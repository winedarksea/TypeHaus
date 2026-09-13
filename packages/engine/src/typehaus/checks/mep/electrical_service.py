"""Service and feeder load checks — NEC 220.82 against what the gear is rated for.

Split out of ``checks/mep/electrical.py`` (which is a symbols-and-spacing module and was
already past the file-size guidance): these two read the same
``takeoff/electrical.service_load_summary``, one over the whole house against the service,
one per panel against that panel's own main.
"""

from __future__ import annotations

from typehaus.checks._authoring import advisory
from typehaus.checks._authoring import not_applicable as _na
from typehaus.checks._authoring import passed as _pass
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result


# WARN severity + FAIL result, deliberately: the permit integrity gate only blocks on ERROR
# severity, and these findings are advisory estimates, not hard blockers.
def _warn_fail(cid: str, msg: str, tags: tuple[str, ...]) -> Finding:
    return advisory(cid, msg, tags, Result.FAIL)


# How each credited basis reads in a finding — the code section or the listing, never just
# the strategy word.
def _basis(credit: dict) -> str:
    strategy = str(credit["strategy"])
    if strategy == "hvac_interlock":
        return "220.82(C) interlock"
    if strategy == "noncoincident":
        return "220.60 noncoincident, AHJ judgement"
    return f"PCS, {credit['listing'] or 'listed'}"


@check(Tier.ADVISORY, "electrical.service_load")
def service_load(ctx: CheckContext) -> list[Finding]:
    """The 220.82 demand estimate vs. the authored service, with load management credited.

    A ``LoadManagement`` caps what its managed circuits can draw together, so the group's
    connected excess over ``max_simultaneous_va`` comes off the demand — *in the 220.82
    term the load was counted in*. It comes off only where the basis holds: a 220.82(C)
    HVAC interlock, a 220.60 noncoincident pair with a stated source, or a PCS listed
    under 2026 NEC Article 130 Part II. A group that earns none of those is a FAIL naming
    what it is missing, and its excess stays in the demand.
    """
    from typehaus.takeoff.electrical import service_load_summary

    cid = "electrical.service_load"
    if not ctx.plan.library.circuits:
        return [_unknown(cid, "no circuits authored")]

    summary = service_load_summary(ctx.model)
    demand_va = float(summary["demand_va"])  # type: ignore[arg-type]
    service_amps = float(summary["service_amps"])  # type: ignore[arg-type]
    credit_va = float(summary["load_management_credit_va"])  # type: ignore[arg-type]

    out: list[Finding] = []
    for credit in summary["load_management"]:  # type: ignore[union-attr]
        tag = str(credit["tag"])
        missing = list(credit["missing_circuits"])  # type: ignore[arg-type]
        if missing:
            out.append(_warn_fail(
                cid, f"{tag} manages unknown circuits: {', '.join(sorted(missing))}", (tag,)))
            continue
        managed_tags = ", ".join(credit["managed_circuits"])  # type: ignore[arg-type]
        if not credit["credited"]:
            out.append(_warn_fail(
                cid, f"{tag} ({credit['strategy']}) claims {float(credit['excess_va']):.0f} "
                     f"VA off {managed_tags} but earns no credit — {credit['refusal']}",
                (tag,)))
            continue
        if float(credit["excess_va"]):  # type: ignore[arg-type]
            out.append(_pass(
                cid, f"{tag} ({_basis(credit)}) caps {managed_tags} at "  # type: ignore[arg-type]
                     f"{float(credit['cap_va']):.0f} VA — "
                     f"{float(credit['excess_va']):.0f} VA of connected load never reaches "
                     "the service", (tag,)))

    managed_amps = demand_va / 240.0
    where = ("" if summary["service_amps_source"] == "default"
             else f" ({summary['service_amps_source']})")
    credit_text = ("no load-management credit" if credit_va <= 0
                   else f"after a {credit_va:.0f} VA load-management credit")
    if managed_amps <= service_amps:
        out.append(_pass(
            cid, f"demand {managed_amps:.1f}A ({credit_text}) fits the "
                 f"{service_amps:.0f}A service{where}"))
    else:
        out.append(_warn_fail(
            cid, f"estimated demand {managed_amps:.1f}A exceeds the {service_amps:.0f}A "
                 f"service{where} — options: a listed PCS (2026 NEC 120.7/130), a 220.82(C) "
                 f"HVAC interlock, or a service upgrade", ()))
    return out


@check(Tier.ADVISORY, "electrical.panel_feeder_load")
def panel_feeder_load(ctx: CheckContext) -> list[Finding]:
    """Each panel's own circuits vs. the main OCPD its type states — the feeder estimate.

    With the load split across two mains, the per-panel feeder is the binding constraint
    and the service total no longer proves anything about either half. This runs the same
    220.82 term structure over one panel's circuits and compares it to that panel's
    ``service_amps`` (which on a PANEL type means the main breaker, not the service size).

    **An estimate, and conservative.** A feeder to a subpanel is properly a Part III
    calculation; applying 220.82(B)'s first-10-kVA-at-100% step to each panel separately
    over-counts, because the step is a whole-dwelling one. The general-lighting allowance
    goes only to the panel(s) hosting ``general`` circuits — it is not split by area,
    which the model has no basis to do.
    """
    from typehaus.takeoff.electrical import service_load_summary

    cid = "electrical.panel_feeder_load"
    types = {t.tag: t for t in ctx.plan.library.electrical_device_types}
    panels = {e.tag: e for e in ctx.plan.all_elements()
              if e.element_kind == "ElectricalDevice" and e.kind.value == "panel"}
    by_panel: dict[str, list] = {}
    for circuit in ctx.plan.library.circuits:
        by_panel.setdefault(circuit.panel_ref, []).append(circuit)

    graded = [tag for tag in sorted(by_panel)
              if getattr(types.get(getattr(panels.get(tag), "type_ref", "") or ""),
                         "service_amps", None) is not None]
    if not graded:
        # Earned N/A: the panel schedule was read and no panel type states a main OCPD, so
        # there is no feeder rating in this model for 220.82 to be compared against.
        return [_na(cid, "no panel type in this house states a main OCPD "
                         "(``service_amps``), so no feeder has a rating to grade against")]

    out: list[Finding] = []
    for panel_ref in graded:
        main = float(types[panels[panel_ref].type_ref].service_amps)
        tags = frozenset(c.tag for c in by_panel[panel_ref])
        summary = service_load_summary(ctx.model, circuit_tags=tags)
        amps = float(summary["demand_va"]) / 240.0  # type: ignore[arg-type]
        if amps > main:
            out.append(_warn_fail(
                cid, f"panel {panel_ref}: {amps:.1f}A of 220.82 feeder demand over "
                     f"{len(tags)} circuits exceeds its {main:.0f}A main — move load to "
                     "another feeder or raise the main (estimate: a subpanel feeder is "
                     "properly NEC 220 Part III)", (panel_ref,)))
        else:
            out.append(_pass(
                cid, f"panel {panel_ref}: {amps:.1f}A of 220.82 feeder demand over "
                     f"{len(tags)} circuits fits its {main:.0f}A main (estimate)",
                (panel_ref,)))
    return out
