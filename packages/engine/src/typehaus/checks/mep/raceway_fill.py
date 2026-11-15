"""``mep.raceway_fill`` — conductor fill against Chapter 9 Tables 1, 4 and 5 (2026 NEC).

A run that names ``circuits`` is graded on each circuit's authored ``conductor_awg`` /
``egc_awg`` (in its ``conductor_insulation``'s Table 5 family, else THHN/THWN-2); a circuit
without one falls back to the SMALLEST copper THHN its breaker allows
(``GAUGE_BY_BREAKER_A``, 240.4(D)), a lower bound that holds only while nothing is upsized.
Each circuit counts its current-carrying conductors (the hots, plus a neutral where
``model/circuit_neutral`` finds one: always on a 1-pole, on a 2-pole unless it authors
``neutral=False`` or feeds only straight-240 receptacles) plus one insulated EGC (Note 3;
Table 250.122 where none is authored).
A run's ``cables`` (PV wire, Class 2, data) add their own areas: a cable at its datasheet
diameter as one conductor (Notes (5), (9)), a single conductor at its Table 5 area. Data cable
is held to Table 1 too, conservatively (Table 723.20's body is unread). Everything else says
what is missing. PVC grades at its authored ``pvc_schedule``, Schedule 80 where unstated. N/A
is earned: a protection sleeve (Note 2) and a run authored with no conductors (a capped spare).

**ADVISORY tier**, like ``mep.conduit_bend_total``. Table 2 (bend radius) is recorded in
``model/raceway_fill.py``; the model draws no bend radius, so nothing grades it.
"""

from __future__ import annotations

import contextlib

from typehaus.checks._authoring import advisory, not_applicable, passed, unknown
from typehaus.checks.mep.electrical_boxes import GAUGE_BY_BREAKER_A
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.ampacity import egc_minimum
from typehaus.model.circuit_neutral import conductors_per_circuit, neutral_by_circuit
from typehaus.model.conductor_areas import conductor_area_in2
from typehaus.model.nec import NEC, cite
from typehaus.model.raceway_areas import table_4_row
from typehaus.model.raceway_cables import table_5_family
from typehaus.model.raceway_fill import cable_area_in2, fill_percent
from typehaus.quantities import M_PER_IN

_CID = "mep.raceway_fill"
_CODE = cite(NEC.FILL_PERCENT, NEC.CONDUIT_DIMENSIONS, NEC.CONDUCTOR_DIMENSIONS, NEC.FILL_EGC)
#: ``RacewayMaterial`` -> (Table 4 key, label). Unstated PVC grades at Schedule 80.
_TABLE = {"emt": ("emt", "EMT"), "ent": ("ent", "ENT"),
          "pvc": ("pvc80", "PVC Schedule 80 (assumed: no schedule authored)")}
_PVC = {40: ("pvc40", "PVC Schedule 40"), 80: ("pvc80", "PVC Schedule 80")}


def _circuit_conductors(circuit, has_neutral: bool = True) -> tuple[list[float], bool] | None:
    """(areas in.2 of one circuit's conductors, authored?), or None where neither the circuit
    nor its breaker gives a size. Authored sizes take the circuit's Table 5 family (THHN/THWN-2
    where none is authored); a circuit authoring no EGC is assumed to carry a Table 250.122 one."""
    if circuit.poles not in (1, 2) or circuit.spd:
        return None
    ccc = conductors_per_circuit(circuit, has_neutral)
    if circuit.conductor_awg is not None:
        family = table_5_family(circuit.conductor_insulation) or "thhn"
        egc = circuit.egc_awg or egc_minimum(circuit.breaker_amps, circuit.conductor_material)
        return ([conductor_area_in2(family, circuit.conductor_awg)] * ccc
                + [conductor_area_in2(family, egc)], True)
    gauge = GAUGE_BY_BREAKER_A.get(circuit.breaker_amps)
    if gauge is None or circuit.source:
        return None
    area = conductor_area_in2("thhn", str(gauge))
    egc = conductor_area_in2("thhn", egc_minimum(circuit.breaker_amps, "cu"))
    return [area] * ccc + [egc], False


def _cable_areas(cables) -> list[float]:
    """One area per conductor or cable (Notes (5), (9)); diameter beats a Table 5 lookup."""
    out: list[float] = []
    for cable in cables:
        if cable.outside_diameter is not None:
            area = cable_area_in2(cable.outside_diameter.meters / M_PER_IN)
        else:
            area = conductor_area_in2(table_5_family(cable.insulation), cable.size_awg)
        out += [area] * cable.count
    return out


def _table(run, authored) -> tuple[str, str]:
    if run.material == "pvc" and authored is not None and authored.pvc_schedule:
        return _PVC[authored.pvc_schedule]
    return _TABLE[run.material]


def _grade_named(run, circuits: dict, authored, neutral: dict[str, bool]) -> Finding:
    table, label = _table(run, authored)
    size_in = round(run.trade_size_m / M_PER_IN, 3)
    areas: list[float] = []
    assumed: list[str] = []
    for tag in run.circuits:
        circuit = circuits.get(tag)
        one = _circuit_conductors(circuit, neutral.get(tag, True)) if circuit else None
        if one is None:
            return unknown(
                _CID, f"{run.tag} carries {tag}, which authors no conductor size and whose "
                      "breaker no table maps to one; author Circuit.conductor_awg",
                (run.tag,), code=_CODE)
        areas += one[0]
        if not one[1]:
            assumed.append(tag)
    cables = authored.cables if authored is not None else ()
    areas += _cable_areas(cables)
    try:
        row = table_4_row(table, size_in)
    except KeyError:
        return unknown(_CID, f"{run.tag}: Table 4 has no {label} row at {size_in:g} in.",
                       (run.tag,), code=_CODE)
    percent = fill_percent(len(areas))
    limit, full, total = row.area_in2(percent), row.a100, sum(areas)
    basis = (f"{', '.join(assumed)} at the smallest THHN each breaker allows, so upsizing "
             "could change it" if assumed else "authored sizes and datasheet diameters")
    carried = ", ".join([*run.circuits, *(f"{c.count} x {c.role or c.cable_type or 'cable'}"
                                          for c in cables)])
    egc = "; EGC counted per Note 3" if run.circuits else ""
    msg = (f"{run.tag} {size_in:g}\" {label}: {len(areas)} conductors/cables "
           f"({carried}{egc}) total {total:.4f} in.2 = "
           f"{100 * total / full:.0f}% of {full:.3f} in.2; Table 1 allows {percent}% = "
           f"{limit:.3f} in.2 ({basis})")
    if total <= limit + 1e-9:
        return passed(_CID, msg, (run.tag,), code=_CODE)
    return advisory(_CID, "ADVISORY — " + msg + " — over the limit; go up a trade size or "
                    "split the circuits", (run.tag,), Result.ADVISORY,
                    code=_CODE)


@check(Tier.ADVISORY, _CID)
def raceway_fill(ctx: CheckContext) -> list[Finding]:
    """Conduit fill per Table 1, graded where a run names its circuits."""
    runs = list(ctx.model.conduits)
    if not runs:
        return [not_applicable(_CID, "this model draws no conduit, so nothing is filled",
                               code=_CODE)]
    circuits = {c.tag: c for c in ctx.plan.library.circuits}
    authored = {r.tag: ctx.plan.by_tag(r.tag) for r in runs if r.derived is None}
    has_cables = {t for t, a in authored.items() if a is not None and a.cables}
    out: list[Finding] = []
    sleeves = tuple(r.tag for r in runs if r.derived == "nm_sleeve")
    spares = [r for r in runs if r.derived is None and r.service is None]
    named = [r for r in runs if r.derived is None and (r.circuits or r.tag in has_cables)
             and r.service is not None and r.material in _TABLE]
    unnamed = tuple(r.tag for r in runs if r.derived is None and not r.circuits
                    and r.tag not in has_cables
                    and r.service in ("power_120", "power_240", "power_24", "power_dc"))
    data = tuple(r.tag for r in runs if r.derived is None and r.service == "data"
                 and r.tag not in has_cables)
    heat = tuple(r.tag for r in runs if r.derived in ("fh_sensor", "fh_cold_lead"))
    if sleeves:
        out.append(not_applicable(
            _CID, f"{len(sleeves)} derived EMT sleeves protect exposed NM from physical damage "
                  "(334.15(B)/(C)); Table 1 is for a complete conduit system, not such a "
                  f"section (Notes to Tables (2))", sleeves, code=cite(NEC.SLEEVE_FILL)))
    for run in spares:
        table, label = (_table(run, authored.get(run.tag)) if run.material in _TABLE
                        else (None, run.material))
        size_in = round(run.trade_size_m / M_PER_IN, 3)
        room = ""
        if table:
            with contextlib.suppress(KeyError):
                room = (f"; once filled Table 1 allows {table_4_row(table, size_in).a40:.3f} "
                        "in.2 for three or more conductors")
        out.append(not_applicable(
            _CID, f"{run.tag} is a capped spare authored with no conductors, so it holds "
                  f"0% fill{room} ({size_in:g}\" {label})", (run.tag,), code=_CODE))
    neutral = neutral_by_circuit(ctx.plan)
    out += [_grade_named(r, circuits, authored.get(r.tag), neutral) for r in named]
    if unnamed:
        out.append(unknown(
            _CID, f"{len(unnamed)} power runs name no circuit and author no cables, so their "
                  "conductor count and sizes are unknown",
            unnamed, code=_CODE, fix="author ConduitRun.circuits or ConduitRun.cables"))
    if data:
        out.append(unknown(
            _CID, f"{len(data)} data runs author no cables; each cable counts as one conductor "
                  "at its actual diameter (Notes to Tables (5), (9))", data, code=_CODE,
            fix="author ConduitRun.cables"))
    if heat:
        out.append(unknown(
            _CID, "floor-heat ENT carries a sensor or cold lead whose actual dimension the "
                  "model does not hold (Notes to Tables (5), (9))", heat, code=_CODE))
    return out
