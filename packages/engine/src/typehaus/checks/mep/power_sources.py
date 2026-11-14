"""CODE-tier rules for the power sources on the service — NEC 705 and NEC 690.

Kept apart from ``electrical_code.py`` (210.8 GFCI) for the same reason that module was
split out of ``electrical.py``: these are not questions about the branch-circuit layout,
they are questions about back-feeding a busbar and about de-energizing a roof. They fail
differently and they are read by different people.

Two rules:

- **705.12(B)** — busbar sizing: 125% of each source's output current plus the busbar's
  OCPD, against 100% of the bus ((B)(1)) or, source at the far end, 120% ((B)(2)(a)).
- **690.12** — rapid shutdown. Inside the array boundary, conductors must drop to a limited
  voltage; a module either carries its own shutdown device or belongs to a group whose
  summed cold Voc stays under the limit.

Both no-op when the house authors no source circuit and no PV, matching the guard in
``supply_protection.py``: a house with no generation is not a house failing generation
rules.
"""

from __future__ import annotations

import math

from typehaus.checks._authoring import by_result, not_applicable
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.nec import NEC, cite

# NEC 705.12(B): 125% of source output current + busbar OCPD <= bus x 1.0 ((B)(1)) or x 1.2
# with the source at the opposite end ((B)(2)(a)).
_BUS_ALLOWANCE = 1.2
_OUTPUT_FACTOR = 1.25


def _inverter_output(ctx: CheckContext, circuit) -> tuple[float, float] | None:
    """(exact, rounded) rated output current of the inverter on ``circuit``, or ``None``.
    705.28(A) rounds a source current to the nearest ampere, dropping fractions under 0.5."""
    types = {t.tag: t for t in ctx.plan.library.equipment_types}
    volts = 240.0 if circuit.poles >= 2 else 120.0
    kw = sum(float(getattr(types.get(e.type_ref or ""), "inverter_kw_continuous", None) or 0.0)
             for e in ctx.plan.all_elements()
             if e.element_kind == "Equipment" and getattr(e, "circuit", None) == circuit.tag)
    if kw <= 0:
        return None
    exact = kw * 1000.0 / volts
    return exact, float(math.floor(exact + 0.5))


def _source_term(ctx: CheckContext, circuit) -> tuple[float, str]:
    """(amps, how) for one source circuit: 125% of the inverter's rated output current, or
    the breaker rating where no inverter on it declares ``inverter_kw_continuous``."""
    found = _inverter_output(ctx, circuit)
    if found:
        exact, output = found
        note = (f", {exact:.1f}A rounded per {NEC.SOURCE_OUTPUT_CURRENT}"
                if abs(exact - output) > 1e-9 else "")
        return _OUTPUT_FACTOR * output, f"125% of {output:g}A output on {circuit.tag}{note}"
    return float(circuit.breaker_amps), f"{circuit.tag}'s breaker for 125% of output"


# NEC 690.12(B)(2) — the controlled-conductor limit inside the array boundary. A module
# group whose summed cold Voc stays under this needs no per-module shutdown device; a group
# over it does. 80V is the limit for conductors *inside* the array boundary.
_RAPID_SHUTDOWN_LIMIT_V = 80.0


@check(Tier.CODE, "code.NEC_705_12_interconnection")
def interconnection_busbar(ctx: CheckContext) -> list[Finding]:
    """NEC 705.12(B) — busbar sizing per panel that carries a source.

    The source term is 125% of each source's rated output current (705.12(B)), read off the
    inverter on the circuit; a circuit with none falls back to its breaker rating, which
    240.4 sizing keeps at or above that 125%. (B)(1) is tried first and has no placement
    condition; (B)(2)(a)'s 120% needs the source at the far end of the bus from the main
    and the (B)(2)(b) label, neither of which the model can show, so the PASS says so.
    (B)(3) (sum of all OCPDs), (B)(4)-(6) and (A) feeders are not tried. Printed text read
    2026-11-14: the arithmetic here is (B)(1)/(B)(2)(a) as printed.

    The main breaker term is the panel's OWN ``service_amps`` where its type states one —
    705.12 measures a backfeed against the main ahead of the bus, and on a Class 320
    service the meter-main's 320 A is not any one panel's main. The service size the load
    summary reports is the fallback for a panel that states none. Source breakers are the
    circuits flagged ``source=True`` on that panel — typed, so a renamed PV circuit cannot
    silently stop counting.

    One documented limit: the model carries no feeder element, so a source landing on a
    *subpanel* has no modeled main OCPD of its own. This check applies the service main to
    every panel carrying a source, which is right for the service panel and conservative
    nowhere else. Putting a second source (V2H) on the backup subpanel is the case that
    makes it wrong, and is called out in notes/backup_power.md as needing a feeder element
    first.

    A source breaker at the *opposite end* of the bus from the main is the other half of
    705.12(B)(2)(a), and it is authored rather than derived: the check reports the slot the
    source circuit occupies so a reviewer can see it, but it does not claim to know which
    physical end of a busbar a slot number lands on.
    """
    cid, code = "code.NEC_705_12_interconnection", cite(NEC.INTERCONNECTION_120PCT)
    sources = [c for c in ctx.plan.library.circuits if c.source]
    if not sources:
        # N/A, not silence: the circuit schedule was read and declares no source circuit,
        # so there is no interconnection for the 120% rule to size. Returning nothing left
        # the permit item with no matched findings, which resolves to UNKNOWN — the same
        # answer as "nobody looked" — and kept the line out of the gate for it.
        return [not_applicable(cid, "no circuit in the schedule is a power source, so this "
                                    "house has no interconnected PV or generator for "
                                    f"{NEC.INTERCONNECTION} to size", (), code)]

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
        # The panel's own main outranks the service size: see the docstring.
        main_amps = float(getattr(product, "service_amps", None) or service_amps or 0.0) or None
        terms = [_source_term(ctx, c) for c in group]
        source_amps = round(sum(amps for amps, _ in terms), 2)
        basis = "; ".join(how for _, how in terms)
        tags = tuple([panel_ref] + sorted(c.tag for c in group))
        if bus_amps is None:
            out.append(by_result(
                cid, Result.UNKNOWN,
                f"panel {panel_ref} carries {source_amps}A of source breakers "
                f"({', '.join(sorted(c.tag for c in group))}) but its type declares no "
                "``bus_amps``, so the 120% allowance cannot be computed", tags, code,
                "declare bus_amps on the panel's ElectricalDeviceType"))
            continue
        if main_amps is None:
            out.append(by_result(
                cid, Result.UNKNOWN,
                f"panel {panel_ref} has a {bus_amps}A bus but neither its type nor the "
                f"service states a main breaker, so the main term of {NEC.INTERCONNECTION} "
                "is unknown",
                tags, code))
            continue
        allowance = bus_amps * _BUS_ALLOWANCE
        spaces = getattr(product, "spaces", None)
        slots = ", ".join(str(c.slot) for c in sorted(group, key=lambda c: c.tag) if c.slot)
        where = f" (slot {slots} of {spaces} spaces)" \
            if slots and spaces else ""
        total = round(float(main_amps) + source_amps, 2)
        head = f"panel {panel_ref}: {main_amps:g}A main + {source_amps:g}A source ({basis})"
        if total <= bus_amps + 1e-9:
            out.append(by_result(
                cid, Result.PASS,
                f"{head} = {total:g}A within the {bus_amps}A bus "
                f"({NEC.INTERCONNECTION_100PCT}, any position)", tags, code))
        elif total <= allowance + 1e-9:
            out.append(by_result(
                cid, Result.PASS,
                f"{head} = {total:g}A of the {allowance:g}A allowed on a {bus_amps}A bus "
                f"({NEC.INTERCONNECTION_120PCT}) — {allowance - total:g}A spare; holds only "
                f"with the source breaker at the opposite end from the main{where} and the "
                f"{NEC.INTERCONNECTION_LABEL} label, neither modeled", tags, code))
        else:
            out.append(by_result(
                cid, Result.FAIL,
                f"{head} = {total:g}A exceeds {_BUS_ALLOWANCE:g} x {bus_amps}A bus = "
                f"{allowance:g}A", tags, code,
                f"reduce the source by {total - allowance:g}A, or use a supply-side "
                "connection"))
    return out


@check(Tier.CODE, "code.NEC_705_30_source_ocpd")
def source_ocpd(ctx: CheckContext) -> list[Finding]:
    """NEC 705.30(B) — a source circuit's OCPD is at least 125% of its 705.28(A) current.

    The floor is graded: 125% of the inverter's rated output, rounded to the ampere first
    (705.28(A)), may be set to the next standard size (240.4(B)). The ceiling, that the
    breaker does not exceed the conductor's ampacity or the inverter's maximum OCPD, needs a
    conductor size on the circuit and a maximum on the equipment type; neither is authored,
    so a second finding says UNKNOWN. 705.30(D) and (E) (breaker marking, the 408.36(D)
    hold-down) are not modeled.
    """
    cid, code = "code.NEC_705_30_source_ocpd", cite(NEC.SOURCE_OCPD)
    sources = sorted((c for c in ctx.plan.library.circuits if c.source), key=lambda c: c.tag)
    if not sources:
        return [not_applicable(cid, "no circuit in the schedule is a power source, so there "
                                    "is no source OCPD to size", (), code)]
    from typehaus.model.ampacity import next_standard_rating
    out: list[Finding] = []
    for circuit in sources:
        found = _inverter_output(ctx, circuit)
        tags = (circuit.tag,)
        if found is None:
            out.append(by_result(
                cid, Result.UNKNOWN, f"{circuit.tag} is a source but no inverter on it declares "
                f"inverter_kw_continuous, so its {NEC.SOURCE_OUTPUT_CURRENT} current is unknown",
                tags, code, "declare inverter_kw_continuous on the inverter's type"))
            continue
        exact, rounded = found
        floor = _OUTPUT_FACTOR * rounded
        standard = next_standard_rating(floor)
        head = (f"{circuit.tag}: {circuit.breaker_amps}A breaker against 125% x {rounded:g}A "
                f"({exact:.1f}A rounded) = {floor:g}A, standard size {standard}A")
        if circuit.breaker_amps + 1e-9 < floor:
            out.append(by_result(cid, Result.FAIL, f"{head}; the breaker is under the floor",
                                 tags, code, f"use at least a {standard}A breaker"))
        else:
            out.append(by_result(cid, Result.PASS, f"{head}; meets the floor", tags, code))
        out.append(by_result(
            cid, Result.UNKNOWN, f"{circuit.tag}'s {circuit.breaker_amps}A breaker is not "
            "checked against the conductor's ampacity (240.4) or the inverter's maximum OCPD: "
            "no conductor size or maximum OCPD is authored", tags, code,
            "author the circuit's conductor size and the inverter type's maximum OCPD"))
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
    detail is the whole arithmetic: with a receiver on every other module the groups are
    pairs at 87.9 V cold, not singletons at 44.0 V, and a check that measured only the
    uncontrolled modules would call the every-other scheme compliant when it is not.

    The check does not assume the answer. It walks each string, builds those groups, and
    compares the largest one against the limit — so "every module" and "every other module"
    are both outcomes the model can produce, not postures the check is written around. A
    module reached before any device on its string is in no group at all and reports as
    uncontrolled.

    Read against the printed 690.12(B)(2): the 80 V limit is right. Not graded: (B)(1)'s 30 V
    within 30 s outside the array boundary (no field for a shut-down module's output), the
    PVHCS alternative and (A)(2) inverter outputs. See ``docs/nec-2026-paraphrase-690-705-710.md``.
    """
    cid, code = "code.NEC_690_12_rapid_shutdown", cite(NEC.RAPID_SHUTDOWN_ARRAY)
    panels = list(ctx.model.solar_panels)
    if not panels:
        return [not_applicable(cid, "no PV module is modeled, so there is no array for "
                                    f"{NEC.RAPID_SHUTDOWN} rapid shutdown to govern", (), code)]

    by_string: dict[str, list] = {}
    for panel in panels:
        by_string.setdefault(panel.string or "(unstrung)", []).append(panel)

    out: list[Finding] = []
    for string_tag, modules in sorted(by_string.items()):
        modules = sorted(modules, key=lambda p: p.tag)
        missing_voc = [p.tag for p in modules if p.voc_cold is None and not p.rsd]
        if missing_voc:
            out.append(by_result(
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
            out.append(by_result(
                cid, Result.FAIL,
                f"string {string_tag}: {len(uncontrolled)} module(s) are reached before any "
                f"shutdown device on the string ({', '.join(tags)}), so nothing controls "
                "them", tags, code,
                "fit a SunSpec receiver to the first module of the string"))
            continue
        worst = max(groups, key=lambda item: sum(p.voc_cold for p in item), default=[])
        run_v = sum(p.voc_cold for p in worst)
        tags = tuple(p.tag for p in worst)
        if run_v > _RAPID_SHUTDOWN_LIMIT_V + 1e-9:
            out.append(by_result(
                cid, Result.FAIL,
                f"string {string_tag}: the largest shutdown group is {len(worst)} module(s) "
                f"at {run_v:.1f}V cold Voc, over the {_RAPID_SHUTDOWN_LIMIT_V:g}V limit "
                f"({', '.join(tags)})", tags, code,
                "fit a SunSpec receiver to more modules until no group exceeds "
                f"{_RAPID_SHUTDOWN_LIMIT_V:g}V cold"))
        elif len(worst) == 1:
            out.append(by_result(
                cid, Result.PASS,
                f"string {string_tag}: all {len(modules)} modules carry a rapid-shutdown "
                f"device of their own ({run_v:.1f}V cold each)",
                tuple(p.tag for p in modules), code))
        else:
            out.append(by_result(
                cid, Result.PASS,
                f"string {string_tag}: the largest shutdown group is {len(worst)} module(s) "
                f"at {run_v:.1f}V cold, within the {_RAPID_SHUTDOWN_LIMIT_V:g}V limit",
                tags, code))
    return out
