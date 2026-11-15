"""CODE-tier rules for the power sources on the service — NEC 705 and NEC 690.

Kept apart from ``electrical_code.py`` (210.8 GFCI) for the same reason that module was
split out of ``electrical.py``: these are not questions about the branch-circuit layout,
they are questions about back-feeding a busbar and about de-energizing a roof. They fail
differently and they are read by different people.

Rules here: **705.30(B)** (the source OCPD) and **690.12** (rapid shutdown). The 705.12(B)
busbar paths live in ``interconnection.py``, which reads ``source_term`` from here.

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

_OUTPUT_FACTOR = 1.25  # 705.12(B), 705.28(B)(1), 705.30(B): 125% of the 705.28(A) current


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


def source_term(ctx: CheckContext, circuit) -> tuple[float, str]:
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


@check(Tier.CODE, "code.NEC_705_30_source_ocpd")
def source_ocpd(ctx: CheckContext) -> list[Finding]:
    """NEC 705.30(B) — a source circuit's OCPD is at least 125% of its 705.28(A) current.

    The floor is graded: 125% of the inverter's rated output, rounded to the ampere first
    (705.28(A)), may be set to the next standard size (240.4(B)). The ceiling is a second
    finding: the conductor (``Circuit.conductor_awg`` at its 110.14(C)(1) column) carries
    705.28(B)(1)'s 125% and protects under 240.4, and the breaker is no larger than the
    inverter type's ``max_overcurrent_a``. 705.30(D) and (E) (breaker marking, the 408.36(D)
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
        out.append(_source_ceiling(ctx, circuit, floor))
    return out


def _source_ceiling(ctx: CheckContext, circuit, floor: float) -> Finding:
    """240.4 / 705.28(B)(1) on the authored conductor, and the inverter's maximum OCPD."""
    from typehaus.model.ampacity import ampacity, max_ocpd, termination_column
    cid, code = "code.NEC_705_30_source_ocpd", cite(NEC.SOURCE_OCPD, NEC.SOURCE_CONDUCTOR)
    types = {t.tag: t for t in ctx.plan.library.equipment_types}
    maxima = [(e.tag, getattr(types.get(e.type_ref or ""), "max_overcurrent_a", None))
              for e in ctx.plan.all_elements()
              if e.element_kind == "Equipment" and getattr(e, "circuit", None) == circuit.tag
              and getattr(types.get(e.type_ref or ""), "inverter_kw_continuous", None)]
    tags = (circuit.tag, *(tag for tag, _ in maxima))
    size, metal = circuit.conductor_awg, circuit.conductor_material
    gaps = [] if size else ["no conductor size"]
    gaps += [f"{tag} states no maximum OCPD" for tag, top in maxima if top is None]
    if gaps:
        return by_result(cid, Result.UNKNOWN, f"{circuit.tag}'s {circuit.breaker_amps}A breaker's "
                         f"ceiling is not checked: {'; '.join(gaps)}", tags, code,
                         "author the circuit's conductor_awg and the inverter's max_overcurrent_a")
    column = termination_column(circuit.breaker_amps, size, circuit.termination_temp_c)
    amps = ampacity(metal, size, column)
    protect = max_ocpd(metal, size, column, next_size_up=circuit.breaker_amps <= 800)
    unit = min(top for _, top in maxima) if maxima else None
    faults = []
    if amps + 1e-9 < floor:
        faults.append(f"{amps}A is under 705.28(B)(1)'s {floor:g}A")
    if protect is not None and circuit.breaker_amps > protect:
        faults.append(f"the breaker exceeds the {protect}A this conductor may take (240.4)")
    if unit is not None and circuit.breaker_amps > unit:
        faults.append(f"the breaker exceeds the inverter's {unit}A maximum OCPD")
    head = (f"{circuit.tag}: #{size} {metal.capitalize()} at {column} °C = {amps}A against "
            f"125% = {floor:g}A, a {circuit.breaker_amps}A breaker"
            + (f", inverter maximum OCPD {unit}A" if unit is not None else ""))
    if faults:
        return by_result(cid, Result.FAIL, f"{head}: {'; '.join(faults)}", tags, code,
                         "upsize the conductor or use a smaller breaker within both limits")
    return by_result(cid, Result.PASS, f"{head}: the conductor carries 125% and the breaker "
                     "is within both the conductor's and the inverter's limits", tags, code)


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
    PVHCS alternative and (A)(2) inverter outputs. See ``docs/code-notes/nec-2026-paraphrase-690-705-710.md``.
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
