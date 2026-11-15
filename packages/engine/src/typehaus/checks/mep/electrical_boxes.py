"""``electrical.box_fill`` — NEC 314.16(B) fill, 314.24(B) depth, a flush box against its cavity.

A box is graded **through-fed** — the worst ordinary case — except a receptacle that is its
circuit's only load, which is end-fed (one cable); a switch or thermostat always has a line
and a load cable. Counted: cables of the
insulated conductors (a 1-pole circuit's hot and neutral; a 2-pole's two hots, plus a neutral
where ``Circuit.neutral`` says so, else where the device has a 120 V half or a 14-
configuration), two volumes per yoke
(314.16(B)(4)), one for up to four equipment grounds and a quarter per ground past four
(314.16(B)(5)), one for internal clamps unless the row states none (B)(2), and one per kind
of support fitting (B)(3), and one per terminal block (B)(6) the row states. The unit
volume is Table 314.16(B)(4)'s, at the gauge the breaker implies — 15 A 14 AWG, 20 A 12 AWG,
30 A 10 AWG. Box volume is the standard's row: Table 314.16(A) or the marked volume, plus a
marked raised cover or ring. Depth is 314.24(B)'s by gauge, or a device's datasheet
``rear_projection`` plus 1/4 in. past 1-7/8 in. (1 in. on 12/10 AWG). A FAIL names the next
box up. Hand-worked oracle:
``houses/catlin/notes/basement_surface_wiring.md`` §Box fill.

``electrical.nm_sleeve_reach`` reports a derived NM sleeve that stops short of the ceiling.
"""

from __future__ import annotations

from typing import Any

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import (
    Finding,
    Result,
    advisory,
    failed,
    not_applicable,
    passed,
    unknown,
)
from typehaus.model.ampacity import adjustment_factor, nm_ampacity
from typehaus.model.circuit_neutral import device_has_neutral
from typehaus.model.electrical import METAL_BOX_VOLUME_IN3
from typehaus.model.nec import NEC, cite, mark
from typehaus.quantities import M_PER_IN
from typehaus.resolve.device_boxes import AIR_SEALED, takes_box

_CID = "electrical.box_fill"
_CODE = cite(NEC.BOX_FILL)
#: Copper branch-circuit gauge by breaker rating (NEC 240.4(D), 310.16 at 60 °C; checked
#: against the printed 2026 Table 310.16, whose 14-8 AWG values are 15/20/30/40 A).
GAUGE_BY_BREAKER_A = {15: 14, 20: 12, 30: 10, 40: 8, 50: 6}
_RECEPTACLES = frozenset({"receptacle", "gfci", "receptacle_240"})
#: Table 314.16(B)(4), in³ per conductor by AWG (printed 2026-11-14; 18 and 16 AWG omitted).
VOLUME_PER_CONDUCTOR_IN3 = {14: 2.0, 12: 2.25, 10: 2.5, 8: 3.0, 6: 5.0}
#: 314.24(B) minimum internal depth with a device, in, by conductor size. The listed-with-box
#: exception and the 1/2 in. rear-entry clearance are not read.
MIN_DEPTH_IN = {14: 15 / 16, 12: 1 + 3 / 16, 10: 1 + 3 / 16, 8: 2 + 1 / 16, 6: 2 + 1 / 16}
_PROJECTION_ADDER_IN = 0.25
_DEEP_PROJECTION_IN = 1 + 7 / 8  # any gauge
_SMALL_GAUGE_PROJECTION_IN = 1.0  # 12 and 10 AWG


def insulated_per_cable(poles: int, has_neutral: bool) -> int:
    return 2 if poles == 1 else (3 if has_neutral else 2)


def egc_allowance(egcs: int) -> float:
    """314.16(B)(5): one allowance covers up to four EGCs, each past four a quarter more."""
    return 0.0 if egcs <= 0 else 1.0 + 0.25 * max(0, egcs - 4)


def required_volume_in3(gauge: int, poles: int, has_neutral: bool, gangs: int,
                        cables: int = 2, *, clamps: bool = False,
                        support_fittings: int = 0, terminal_blocks: int = 0) -> float:
    """Cables × insulated conductors + 2 per yoke + the grounds (one per cable), clamps,
    support fittings and terminal blocks (314.16(B)(6), one each), all at the circuit's gauge
    (the largest conductor in the box)."""
    count = (cables * insulated_per_cable(poles, has_neutral) + 2 * gangs
             + egc_allowance(cables) + (1 if clamps else 0) + support_fittings
             + terminal_blocks)
    return count * VOLUME_PER_CONDUCTOR_IN3[gauge]


def min_depth_in(gauge: int, rear_projection_in: float | None) -> float:
    """314.24(B): the gauge's depth, or the device's rear projection plus 1/4 in. past the
    threshold (1-7/8 in., or 1 in. for 12 and 10 AWG)."""
    base = MIN_DEPTH_IN[gauge]
    if rear_projection_in is None:
        return base
    limit = _SMALL_GAUGE_PROJECTION_IN if gauge in (12, 10) else _DEEP_PROJECTION_IN
    if rear_projection_in > min(limit, _DEEP_PROJECTION_IN) + 1e-9:
        return max(base, rear_projection_in + _PROJECTION_ADDER_IN)
    return base


def next_box_up(required_in3: float) -> str:
    fits = sorted((volume, name) for name, volume in METAL_BOX_VOLUME_IN3.items()
                  if volume >= required_in3)
    if not fits:
        return f"no {NEC.BOX_VOLUME_TABLE} box holds {required_in3:.1f} in³ — split the splice"
    volume, name = fits[0]
    return f"a {name} box ({volume:g} in³) or a listed box marked ≥ {required_in3:.1f} in³"


def _grade(box: Any, circuits: dict[str, Any], types: dict[str, Any],
           type_ref: str | None, loads: dict[str, int]) -> Finding:
    tags = (box.device_tag,)
    if box.device_kind == "data_outlet":
        return not_applicable(_CID, f"{box.device_tag} is a data outlet: Class 2 / comms "
                                    f"cabling is outside {NEC.BOX_FILL_AND_VOLUME}", tags,
                                    code=_CODE)
    where = f"{box.device_tag}'s {box.mounting} {box.gangs}-gang box ({box.box_product})"
    if box.cavity_m is not None and box.depth_m > box.cavity_m + 1e-4:
        return failed(_CID, f"{where} is {box.depth_m / M_PER_IN:.2f}\" deep in a "
                            f"{box.cavity_m / M_PER_IN:.2f}\" cavity", tags,
                      code=cite(NEC.BOX_FLUSH_SETBACK),
                      fix="a shallower box row in the BoxStandard, or a deeper cavity")
    if box.air_barrier and not (box.box_use or "").startswith(AIR_SEALED):
        return failed(_CID, f"{where} breaches an air-control membrane on {box.wall_tag}, and "
                            f"the BoxStandard has no {AIR_SEALED!r} {box.mounting} "
                            f"{box.gangs}-gang row", tags,
                      fix="add an air-sealed row: a flanged, gasketed box whose flange is "
                          "taped to the membrane")
    circuit = circuits.get(box.circuit or "")
    if circuit is None:
        return unknown(_CID, f"{where} names no circuit, so its conductors are unknown",
                       tags, code=_CODE, fix="name the device's circuit")
    gauge = GAUGE_BY_BREAKER_A.get(circuit.breaker_amps)
    if gauge is None or box.volume_in3 is None:
        return unknown(_CID, f"{where}: no gauge for a {circuit.breaker_amps} A breaker or no "
                             "box volume", tags, code=_CODE)
    product_type = types.get(type_ref or "")
    projection = getattr(product_type, "rear_projection", None)
    projection_in = None if projection is None else projection.meters / M_PER_IN
    min_depth = min_depth_in(gauge, projection_in)
    if box.depth_m / M_PER_IN < min_depth - 1e-4:
        why = (f"a device projecting {projection_in:.2f}\" needs"
               if min_depth > MIN_DEPTH_IN[gauge] else f"{gauge} AWG to a device needs")
        return failed(_CID, f"{where} is {box.depth_m / M_PER_IN:.2f}\" deep; {why} "
                            f"{min_depth:.3f}\" internal depth", tags,
                      code=cite(NEC.BOX_DEPTH), fix="a deeper box row in the BoxStandard")
    end_fed = box.device_kind in _RECEPTACLES and loads.get(circuit.tag, 0) <= 1
    cables = 1 if end_fed else 2
    feed = "through-fed" if cables == 2 else "end-fed"
    clamps = box.internal_clamps is not False
    neutral = (circuit.neutral if circuit.neutral is not None
               else device_has_neutral(product_type))
    required = required_volume_in3(gauge, circuit.poles, neutral, box.gangs,
                                   cables, clamps=clamps,
                                   support_fittings=box.support_fittings,
                                   terminal_blocks=box.terminal_blocks)
    note = (f" ({mark(NEC.BOX_FILL_CLAMPS)} clamps not stated, so counted)"
            if box.internal_clamps is None else "")
    if required > box.volume_in3 + 1e-6:
        return failed(_CID, f"{where} holds {box.volume_in3:g} in³; {feed} {gauge} AWG "
                            f"needs {required:.2f} in³{note}", tags, code=_CODE,
                      fix=f"step up to {next_box_up(required)}")
    return passed(_CID, f"{where}: {required:.2f} in³ of {feed} {gauge} AWG in "
                        f"{box.volume_in3:g} in³{note}", tags, code=_CODE)


@check(Tier.ADVISORY, _CID)
def box_fill(ctx: CheckContext) -> list[Finding]:
    """Each derived device box against its through-fed fill and its cavity depth."""
    boxes = list(ctx.model.device_boxes)
    types = {t.tag: t for t in ctx.plan.library.electrical_device_types}
    if not boxes:
        declared = any(el.element_kind == "BoxStandard" for el in ctx.plan.all_elements())
        wants = [obj.tag for obj in ctx.model.canvas_objects
                 if obj.kind == "ElectricalDevice" and obj.attachment_wall is not None
                 and takes_box(ctx.plan.by_tag(obj.tag), types.get(obj.type_ref or ""))]
        if declared or not wants:
            return [not_applicable(_CID, "no wall device takes a derived box", code=_CODE)]
        return [unknown(_CID, f"{len(wants)} wall device(s) but no BoxStandard, so no box is "
                              "modeled", code=_CODE,
                        fix="declare one BoxStandard (decision #93)")]
    circuits = {circuit.tag: circuit for circuit in ctx.plan.library.circuits}
    type_refs = {obj.tag: obj.type_ref for obj in ctx.model.canvas_objects}
    loads = _circuit_loads(ctx)
    return [_grade(box, circuits, types, type_refs.get(box.device_tag), loads)
            for box in boxes]


def _circuit_loads(ctx: CheckContext) -> dict[str, int]:
    loads: dict[str, int] = {}
    for element in ctx.plan.all_elements():
        circuit = getattr(element, "circuit", None)
        if circuit and element.element_kind in ("ElectricalDevice", "Equipment"):
            loads[circuit] = loads.get(circuit, 0) + 1
    return loads


_REACH = "electrical.nm_sleeve_reach"
_REACH_CODE = cite(NEC.NM_PROTECTION, NEC.NM_BASEMENT)


@check(Tier.ADVISORY, _REACH)
def nm_sleeve_reach(ctx: CheckContext) -> list[Finding]:
    """Each derived NM sleeve against the ceiling it was meant to reach.

    A sleeve that stops under a run leaves the NM above it off the sleeve, on the wall. How
    far is reported, never graded: whether the run shields it or the sleeve offsets around
    the run is the electrician's call and the inspector's.
    """
    sleeves = [run for run in ctx.model.conduits if run.derived == "nm_sleeve"]
    if not sleeves:
        return [not_applicable(_REACH, "no surface box takes a derived NM sleeve",
                               code=_REACH_CODE)]
    out = []
    for run in sleeves:
        tags = (run.tag, run.to_ref) if run.to_ref else (run.tag,)
        if run.stops_under is None:
            out.append(passed(_REACH, f"{run.tag} sleeves the NM from the box to the ceiling",
                              tags, code=_REACH_CODE))
            continue
        out.append(advisory(
            _REACH, f"{run.tag} stops under {run.stops_under}, "
                    f"{run.unsleeved_m / M_PER_IN:.1f}\" short of the ceiling: the NM above is "
                    "off the sleeve", (*tags, run.stops_under), Result.ADVISORY,
            code=_REACH_CODE, fix=f"offset the sleeve around {run.stops_under}, or confirm on "
                                  "site that the run shields the NM"))
    return out


_AMPS = "electrical.nm_sleeve_ampacity"
_AMPS_CODE = cite(NEC.ADJUSTMENT_FACTORS, NEC.NM_AMPACITY)
_EXEMPT_M = 24 * M_PER_IN


@check(Tier.ADVISORY, _AMPS)
def nm_sleeve_ampacity(ctx: CheckContext) -> list[Finding]:
    """310.15(C)(1) / 334.80(A): NM in a derived sleeve, adjusted, against its breaker.

    Cables per sleeve follow ``box_fill`` (two through-fed, one end-fed); each 2-wire or
    single-phase 3-wire cable carries two current-carrying conductors (310.15(E): the hot-
    neutral pair counts, a single-phase neutral carrying only the unbalance does not; the EGC
    never does). A sleeve of 24 in. or less is exempt (310.15(C)(1)(b)). Otherwise the 90 °C
    value times the Table 310.15(C)(1) factor, capped at the 60 °C value, must cover the
    breaker. Only the sleeve is counted: overhead NM bundles are not modelled.
    """
    sleeves = [run for run in ctx.model.conduits if run.derived == "nm_sleeve"]
    if not sleeves:
        return [not_applicable(_AMPS, "no surface box takes a derived NM sleeve",
                               code=_AMPS_CODE)]
    boxes = {box.device_tag: box for box in ctx.model.device_boxes}
    circuits = {circuit.tag: circuit for circuit in ctx.plan.library.circuits}
    loads = _circuit_loads(ctx)
    out = []
    for run in sleeves:
        box = boxes.get(run.to_ref or "")
        circuit = circuits.get(box.circuit or "") if box is not None else None
        tags = (run.tag, run.to_ref) if run.to_ref else (run.tag,)
        gauge = GAUGE_BY_BREAKER_A.get(circuit.breaker_amps) if circuit else None
        if circuit is None or gauge is None:
            out.append(unknown(_AMPS, f"{run.tag}: no circuit or no copper gauge for its "
                                      "breaker", tags, code=_AMPS_CODE))
            continue
        end_fed = box.device_kind in _RECEPTACLES and loads.get(circuit.tag, 0) <= 1
        ccc = 2 * (1 if end_fed else 2)
        where = (f"{run.tag}: {run.length_m / M_PER_IN:.0f}\" sleeve, {ccc} current-carrying "
                 f"{gauge} AWG conductors on {circuit.tag} ({circuit.breaker_amps} A)")
        factor = adjustment_factor(ccc)
        if ccc <= 3 or run.length_m <= _EXEMPT_M:
            why = "three or fewer conductors" if ccc <= 3 else "a sleeve of 24 in. or less"
            out.append(passed(_AMPS, f"{where}: no adjustment applies ({why})", tags,
                              code=_AMPS_CODE))
            continue
        rating = nm_ampacity(str(gauge), ccc)
        if rating >= circuit.breaker_amps:
            out.append(passed(_AMPS, f"{where}: {factor:.0%} gives {rating} A "
                                     f"(90 °C value, capped at 60 °C), covers the breaker",
                              tags, code=_AMPS_CODE))
        else:
            out.append(failed(_AMPS, f"{where}: {factor:.0%} gives {rating} A, under the "
                                     "breaker", tags, code=_AMPS_CODE,
                              fix="a larger conductor, a smaller breaker, or fewer cables in "
                                  "the sleeve"))
    return out
