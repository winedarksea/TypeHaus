"""CODE-tier rules for the power sources on the service — NEC 705 and NEC 690.

Kept apart from ``electrical_code.py`` (E3902 GFCI) for the same reason that module was
split out of ``electrical.py``: these are not questions about the branch-circuit layout,
they are questions about back-feeding a busbar and about de-energizing a roof. They fail
differently and they are read by different people.

Two rules:

- **705.12(B)(3)(2)** — the busbar's 120% allowance. The sum of the main breaker and every
  source breaker may not exceed 1.2 x the bus rating.
- **690.12** — rapid shutdown. Inside the array boundary, conductors must drop to a limited
  voltage; a module either carries its own shutdown device or belongs to a group whose
  summed cold Voc stays under the limit.

Both no-op when the house authors no source circuit and no PV, matching the guard in
``supply_protection.py``: a house with no generation is not a house failing generation
rules.
"""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity

# NEC 705.12(B)(3)(2), the "120% rule": bus rating x 1.2 >= main OCPD + Σ source breakers.
_BUS_ALLOWANCE = 1.2

# NEC 690.12(B)(2) — the controlled-conductor limit inside the array boundary. A module
# group whose summed cold Voc stays under this needs no per-module shutdown device; a group
# over it does. 80V is the limit for conductors *inside* the array boundary.
_RAPID_SHUTDOWN_LIMIT_V = 80.0


def _finding(cid: str, result: Result, message: str, tags: tuple[str, ...],
             code: str, fix: str | None = None) -> Finding:
    severity = Severity.ERROR if result is Result.FAIL else Severity.WARN
    text = message if result is not Result.UNKNOWN else f"UNKNOWN — {message}"
    return Finding(severity=severity, check_id=cid, message=text, element_tags=tags,
                   code_ref=code, fix_hint=fix, result=result)


@check(Tier.CODE, "code.NEC_705_12_interconnection")
def interconnection_busbar(ctx: CheckContext) -> list[Finding]:
    """NEC 705.12(B)(3)(2) — the 120% busbar allowance, per panel that carries a source.

    Formalizes what used to be a comment beside a breaker slot. The main breaker term is
    the service size the load summary reports — the same 200A the E-601 sheet prints, so
    the sheet and the finding cannot disagree; source breakers are the circuits flagged
    ``source=True`` on that panel — typed, so a renamed PV circuit cannot silently stop
    counting.

    One documented limit: the model carries no feeder element, so a source landing on a
    *subpanel* has no modeled main OCPD of its own. This check applies the service main to
    every panel carrying a source, which is right for the service panel and conservative
    nowhere else. Putting a second source (V2H) on the backup subpanel is the case that
    makes it wrong, and is called out in notes/backup_power.md as needing a feeder element
    first.

    A source breaker at the *opposite end* of the bus from the main is the other half of
    705.12(B)(3)(2), and it is authored rather than derived: the check reports the slot the
    source circuit occupies so a reviewer can see it, but it does not claim to know which
    physical end of a busbar a slot number lands on.
    """
    cid, code = "code.NEC_705_12_interconnection", "NEC 705.12(B)(3)(2)"
    sources = [c for c in ctx.plan.library.circuits if c.source]
    if not sources:
        return []

    types = {t.tag: t for t in ctx.plan.library.electrical_device_types}
    panels = {element.tag: element for element in ctx.plan.all_elements()
              if element.element_kind == "ElectricalDevice"
              and element.kind.value == "panel"}
    from typehaus.takeoff.electrical import service_load_summary
    service_amps = (service_load_summary(ctx.model)["service_amps"]
                    if ctx.plan.library.circuits else None)

    by_panel: dict[str, list] = {}
    for circuit in sources:
        by_panel.setdefault(circuit.panel_ref, []).append(circuit)

    out: list[Finding] = []
    for panel_ref, group in sorted(by_panel.items()):
        product = types.get(getattr(panels.get(panel_ref), "type_ref", None) or "")
        bus_amps = getattr(product, "bus_amps", None)
        source_amps = sum(c.breaker_amps for c in group)
        tags = tuple([panel_ref] + sorted(c.tag for c in group))
        if bus_amps is None:
            out.append(_finding(
                cid, Result.UNKNOWN,
                f"panel {panel_ref} carries {source_amps}A of source breakers "
                f"({', '.join(sorted(c.tag for c in group))}) but its type declares no "
                "``bus_amps``, so the 120% allowance cannot be computed", tags, code,
                "declare bus_amps on the panel's ElectricalDeviceType"))
            continue
        if service_amps is None:
            out.append(_finding(
                cid, Result.UNKNOWN,
                f"panel {panel_ref} has a {bus_amps}A bus but no service size is "
                "computable, so the main breaker term of 705.12 is unknown", tags, code))
            continue
        allowance = bus_amps * _BUS_ALLOWANCE
        total = float(service_amps) + source_amps
        headroom = allowance - total
        if total > allowance + 1e-9:
            out.append(_finding(
                cid, Result.FAIL,
                f"panel {panel_ref}: {service_amps}A main + {source_amps}A of source "
                f"breakers = {total:g}A exceeds {_BUS_ALLOWANCE:g} x {bus_amps}A bus = "
                f"{allowance:g}A", tags, code,
                f"reduce the source breaker(s) by {total - allowance:g}A, or use a "
                "supply-side connection"))
        else:
            out.append(_finding(
                cid, Result.PASS,
                f"panel {panel_ref}: {service_amps}A main + {source_amps}A source "
                f"({', '.join(sorted(c.tag for c in group))}) = {total:g}A of the "
                f"{allowance:g}A allowed on a {bus_amps}A bus — {headroom:g}A spare",
                tags, code))
    return out


@check(Tier.CODE, "code.NEC_690_12_rapid_shutdown")
def rapid_shutdown(ctx: CheckContext) -> list[Finding]:
    """NEC 690.12 — every PV module is shut down, per module or as a compliant group.

    A module with ``rsd=True`` carries its own SunSpec shutdown device and answers for
    itself. A module without one has to be covered by a group of adjacent modules on its
    string whose summed **cold** Voc stays under 80V — ``voc_cold``, never rated Voc: at a
    Minnesota design low a module puts out meaningfully more than its STC nameplate, and a
    grouping sized on rated Voc is a grouping that is legal in July and not in January.

    A *group* is one shutdown device together with the modules downstream of it that have
    none of their own — the device is inside the group it controls, not outside it. That
    detail is the whole arithmetic: with a transmitter on every other module the groups are
    pairs at 88.8 V cold, not singletons at 44.4 V, and a check that measured only the
    uncontrolled modules would call the every-other scheme compliant when it is not.

    The check does not assume the answer. It walks each string, builds those groups, and
    compares the largest one against the limit — so "every module" and "every other module"
    are both outcomes the model can produce, not postures the check is written around. A
    module reached before any device on its string is in no group at all and reports as
    uncontrolled.
    """
    cid, code = "code.NEC_690_12_rapid_shutdown", "NEC 690.12(B)(2)"
    panels = list(ctx.model.solar_panels)
    if not panels:
        return []

    by_string: dict[str, list] = {}
    for panel in panels:
        by_string.setdefault(panel.string or "(unstrung)", []).append(panel)

    out: list[Finding] = []
    for string_tag, modules in sorted(by_string.items()):
        modules = sorted(modules, key=lambda p: p.tag)
        missing_voc = [p.tag for p in modules if p.voc_cold is None and not p.rsd]
        if missing_voc:
            out.append(_finding(
                cid, Result.UNKNOWN,
                f"string {string_tag}: {len(missing_voc)} module(s) carry no shutdown "
                f"device and declare no ``voc_cold`` ({', '.join(sorted(missing_voc))}), so "
                "the 80V group limit cannot be evaluated", tuple(sorted(missing_voc)), code,
                "author voc_cold from the module datasheet's Voc temperature coefficient "
                "at the site design low"))
            continue
        groups: list[list] = []
        uncontrolled: list = []
        for panel in modules:
            if panel.rsd:
                groups.append([panel])
            elif groups:
                groups[-1].append(panel)
            else:
                uncontrolled.append(panel)
        if uncontrolled:
            tags = tuple(p.tag for p in uncontrolled)
            out.append(_finding(
                cid, Result.FAIL,
                f"string {string_tag}: {len(uncontrolled)} module(s) are reached before any "
                f"shutdown device on the string ({', '.join(tags)}), so nothing controls "
                "them", tags, code,
                "fit a SunSpec transmitter to the first module of the string"))
            continue
        worst = max(groups, key=lambda item: sum(p.voc_cold for p in item), default=[])
        run_v = sum(p.voc_cold for p in worst)
        tags = tuple(p.tag for p in worst)
        if run_v > _RAPID_SHUTDOWN_LIMIT_V + 1e-9:
            out.append(_finding(
                cid, Result.FAIL,
                f"string {string_tag}: the largest shutdown group is {len(worst)} module(s) "
                f"at {run_v:.1f}V cold Voc, over the {_RAPID_SHUTDOWN_LIMIT_V:g}V limit "
                f"({', '.join(tags)})", tags, code,
                "fit a SunSpec transmitter to more modules until no group exceeds "
                f"{_RAPID_SHUTDOWN_LIMIT_V:g}V cold"))
        elif len(worst) == 1:
            out.append(_finding(
                cid, Result.PASS,
                f"string {string_tag}: all {len(modules)} modules carry a rapid-shutdown "
                f"device of their own ({run_v:.1f}V cold each)",
                tuple(p.tag for p in modules), code))
        else:
            out.append(_finding(
                cid, Result.PASS,
                f"string {string_tag}: the largest shutdown group is {len(worst)} module(s) "
                f"at {run_v:.1f}V cold, within the {_RAPID_SHUTDOWN_LIMIT_V:g}V limit",
                tags, code))
    return out
