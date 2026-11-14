"""``mep.raceway_fill`` — conductor fill against Chapter 9 Tables 1, 4 and 5 (2026 NEC).

The model authors no conductor, so a run that names ``circuits`` is graded on the SMALLEST
copper THHN/THWN-2 each breaker allows (``GAUGE_BY_BREAKER_A``, 240.4(D)): the circuit's
current-carrying conductors (hot and neutral: 2 on a 1-pole, 3 on a 2-pole, the takeoff's
convention) plus one insulated EGC per circuit at its Table 250.122 size (Note 3). That is a
lower bound: an over-limit result is real, a PASS holds only while nothing is upsized.
Everything else says what is missing. PVC grades at Schedule 80 (the model holds ``pvc``
only; 300.7(D) already wants Schedule 80 where it rises). N/A is earned: a protection
sleeve (Note 2) and a run authored with no conductors (a capped spare).

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
from typehaus.model.conductor_areas import conductor_area_in2
from typehaus.model.nec import NEC, cite
from typehaus.model.raceway_areas import table_4_row
from typehaus.model.raceway_fill import fill_percent
from typehaus.quantities import M_PER_IN

_CID = "mep.raceway_fill"
_CODE = cite(NEC.FILL_PERCENT, NEC.CONDUIT_DIMENSIONS, NEC.CONDUCTOR_DIMENSIONS, NEC.FILL_EGC)
#: ``RacewayMaterial`` -> (Table 4 key, label). PVC is graded at Schedule 80, said in the text.
_TABLE = {"emt": ("emt", "EMT"), "ent": ("ent", "ENT"),
          "pvc": ("pvc80", "PVC Schedule 80 (assumed: the model holds no schedule)")}
_CONDUCTORS_PER_POLE_COUNT = {1: 2, 2: 3}  # hot + neutral, as takeoff/raceways.py


def _circuit_conductors(circuit) -> list[float] | None:
    """Areas (in.2) of one circuit's conductors, or None where the breaker has no known gauge."""
    gauge = GAUGE_BY_BREAKER_A.get(circuit.breaker_amps)
    ccc = _CONDUCTORS_PER_POLE_COUNT.get(circuit.poles)
    if gauge is None or ccc is None or circuit.source or circuit.spd:
        return None
    area = conductor_area_in2("thhn", str(gauge))
    egc = conductor_area_in2("thhn", egc_minimum(circuit.breaker_amps, "cu"))
    return [area] * ccc + [egc]


def _grade_named(run, circuits: dict) -> Finding:
    table, label = _TABLE[run.material]
    size_in = round(run.trade_size_m / M_PER_IN, 3)
    areas: list[float] = []
    for tag in run.circuits:
        circuit = circuits.get(tag)
        one = _circuit_conductors(circuit) if circuit else None
        if one is None:
            return unknown(
                _CID, f"{run.tag} carries {tag}, whose conductor size no table can derive "
                      "(not a 15/20/30/40/50 A branch breaker); author the conductors",
                (run.tag,), code=_CODE)
        areas += one
    try:
        row = table_4_row(table, size_in)
    except KeyError:
        return unknown(_CID, f"{run.tag}: Table 4 has no {label} row at {size_in:g} in.",
                       (run.tag,), code=_CODE)
    percent = fill_percent(len(areas))
    limit, full, total = row.area_in2(percent), row.a100, sum(areas)
    msg = (f"{run.tag} {size_in:g}\" {label}: {len(areas)} conductors "
           f"({', '.join(run.circuits)} at the smallest THHN each breaker allows, EGC counted "
           f"per Note 3) total {total:.4f} in.2 = {100 * total / full:.0f}% of {full:.3f} in.2; "
           f"Table 1 allows {percent}% = {limit:.3f} in.2. Sizes are assumed, so upsizing "
           "(voltage drop) could change it")
    if total <= limit + 1e-9:
        return passed(_CID, msg, (run.tag,), code=_CODE)
    return advisory(_CID, "ADVISORY — " + msg + " — over the limit even at minimum size; "
                    "go up a trade size or split the circuits", (run.tag,), Result.ADVISORY,
                    code=_CODE)


@check(Tier.ADVISORY, _CID)
def raceway_fill(ctx: CheckContext) -> list[Finding]:
    """Conduit fill per Table 1, graded where a run names its circuits."""
    runs = list(ctx.model.conduits)
    if not runs:
        return [not_applicable(_CID, "this model draws no conduit, so nothing is filled",
                               code=_CODE)]
    circuits = {c.tag: c for c in ctx.plan.library.circuits}
    out: list[Finding] = []
    sleeves = tuple(r.tag for r in runs if r.derived == "nm_sleeve")
    spares = [r for r in runs if r.derived is None and r.service is None]
    named = [r for r in runs if r.derived is None and r.circuits and r.service is not None
             and r.material in _TABLE]
    unnamed = tuple(r.tag for r in runs if r.derived is None and not r.circuits
                    and r.service in ("power_120", "power_240", "power_24", "power_dc"))
    data = tuple(r.tag for r in runs if r.derived is None and r.service == "data")
    heat = tuple(r.tag for r in runs if r.derived in ("fh_sensor", "fh_cold_lead"))
    if sleeves:
        out.append(not_applicable(
            _CID, f"{len(sleeves)} derived EMT sleeves protect exposed NM from physical damage "
                  "(334.15(B)/(C)); Table 1 is for a complete conduit system, not such a "
                  f"section (Notes to Tables (2))", sleeves, code=cite(NEC.SLEEVE_FILL)))
    for run in spares:
        table, label = _TABLE.get(run.material, (None, run.material))
        size_in = round(run.trade_size_m / M_PER_IN, 3)
        room = ""
        if table:
            with contextlib.suppress(KeyError):
                room = (f"; once filled Table 1 allows {table_4_row(table, size_in).a40:.3f} "
                        "in.2 for three or more conductors")
        out.append(not_applicable(
            _CID, f"{run.tag} is a capped spare authored with no conductors, so it holds "
                  f"0% fill{room} ({size_in:g}\" {label})", (run.tag,), code=_CODE))
    out += [_grade_named(r, circuits) for r in named]
    if unnamed:
        out.append(unknown(
            _CID, f"{len(unnamed)} power runs name no circuit, so their conductor count and "
                  "sizes are unknown; name the circuits pulled through each",
            unnamed, code=_CODE, fix="author ConduitRun.circuits"))
    if data:
        out.append(unknown(
            _CID, f"{len(data)} data runs author no cables; each cable counts as one conductor "
                  "at its actual diameter (Notes to Tables (5), (9))", data, code=_CODE))
    if heat:
        out.append(unknown(
            _CID, "floor-heat ENT carries a sensor or cold lead whose actual dimension the "
                  "model does not hold (Notes to Tables (5), (9))", heat, code=_CODE))
    return out
