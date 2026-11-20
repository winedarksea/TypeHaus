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
box up. A luminaire takes no yoke allowance (it is not a device on a strap); an alarm head
counts three insulated conductors per cable (the interconnect), through-fed; fixture leads are
not counted (314.16(B)(1) exception). A gang bank is one box: each member counts its own
cables and yokes at its own circuit's gauge, and the grounds, clamps, fittings and blocks
count once, at the largest gauge present (314.16(B)(2), (5)); the deepest requirement of any
member sets the depth.
Hand-worked oracle:
``houses/catlin/notes/basement_surface_wiring.md`` §Box fill.

``electrical.nm_sleeve_reach`` reports a derived NM sleeve that stops short of the ceiling.
"""

from __future__ import annotations

from typing import Any, NamedTuple

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
from typehaus.resolve.box_members import box_members
from typehaus.resolve.device_boxes import AIR_SEALED, boxes_by_device, gang_count, takes_box

_CID = "electrical.box_fill"
_CODE = cite(NEC.BOX_FILL)
#: Copper branch-circuit gauge by breaker rating (NEC 240.4(D), 310.16 at 60 °C; checked
#: against the printed 2026 Table 310.16, whose 14-8 AWG values are 15/20/30/40 A).
GAUGE_BY_BREAKER_A = {15: 14, 20: 12, 30: 10, 40: 8, 50: 6}
_RECEPTACLES = frozenset({"receptacle", "gfci", "receptacle_240"})
_NO_YOKE = frozenset({"light", "alarm"})
_ALARM_CONDUCTORS = 3  # hot, neutral and the interconnect per 14/3 cable
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


def conductor_volume_in3(gauge: int, poles: int, has_neutral: bool, gangs: int,
                         cables: int = 2) -> float:
    """One device's insulated conductors and two per yoke, at its own circuit's gauge."""
    return (cables * insulated_per_cable(poles, has_neutral) + 2 * gangs) \
        * VOLUME_PER_CONDUCTOR_IN3[gauge]


def shared_volume_in3(gauge: int, cables: int, *, clamps: bool = False,
                      support_fittings: int = 0, terminal_blocks: int = 0) -> float:
    """The once-per-box allowances at the box's largest gauge: one ground allowance for the
    cables' EGCs (B)(5), clamps (B)(2), support fittings (B)(3), terminal blocks (B)(6)."""
    count = (egc_allowance(cables) + (1 if clamps else 0) + support_fittings + terminal_blocks)
    return count * VOLUME_PER_CONDUCTOR_IN3[gauge]


def required_volume_in3(gauge: int, poles: int, has_neutral: bool, gangs: int,
                        cables: int = 2, *, clamps: bool = False,
                        support_fittings: int = 0, terminal_blocks: int = 0) -> float:
    """A one-device box: its conductors and yokes plus the shared allowances, one gauge."""
    return (conductor_volume_in3(gauge, poles, has_neutral, gangs, cables)
            + shared_volume_in3(gauge, cables, clamps=clamps,
                                support_fittings=support_fittings,
                                terminal_blocks=terminal_blocks))


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


class _Load(NamedTuple):
    """One bank member's wiring: its circuit, gauge, type and cables."""

    tag: str
    circuit: Any
    gauge: int | None
    product_type: Any
    gangs: int
    cables: int
    per_cable: int | None = None  # insulated conductors per cable, over the circuit's own


def _loads(box: Any, circuits: dict[str, Any], types: dict[str, Any],
           type_refs: dict[str, str | None], loads: dict[str, int]
           ) -> tuple[list[_Load], str | None]:
    """Each wired member (data outlets are Class 2), and the tag of one with no circuit."""
    members = [m for m in box_members(box) if m.kind != "data_outlet"]
    out: list[_Load] = []
    for member in members:
        circuit = circuits.get(member.circuit or "")
        if circuit is None:
            return out, member.tag
        product_type = types.get(type_refs.get(member.tag) or "")
        gangs = box.gangs if len(members) == 1 else gang_count(product_type)
        if member.kind in _NO_YOKE:  # a luminaire or alarm hangs on the box, not a strap
            gangs = 0
        end_fed = member.kind in _RECEPTACLES and loads.get(circuit.tag, 0) <= 1
        out.append(_Load(member.tag, circuit, GAUGE_BY_BREAKER_A.get(circuit.breaker_amps),
                         product_type, gangs, 1 if end_fed else 2,
                         _ALARM_CONDUCTORS if member.kind == "alarm" else None))
    return out, None


def _grade(box: Any, circuits: dict[str, Any], types: dict[str, Any],
           type_refs: dict[str, str | None], loads: dict[str, int]) -> Finding:
    tags = tuple(box.device_tags or (box.device_tag,))
    names = "+".join(tags)
    if box.device_kind == "data_outlet" and all(
            m.kind == "data_outlet" for m in box_members(box)):
        return not_applicable(_CID, f"{names} is a data outlet: Class 2 / comms "
                                    f"cabling is outside {NEC.BOX_FILL_AND_VOLUME}", tags,
                                    code=_CODE)
    where = f"{names}'s {box.mounting} {box.gangs}-gang box ({box.box_product})"
    if box.cavity_m is not None and box.depth_m > box.cavity_m + 1e-4:
        return failed(_CID, f"{where} is {box.depth_m / M_PER_IN:.2f}\" deep in a "
                            f"{box.cavity_m / M_PER_IN:.2f}\" cavity", tags,
                      code=cite(NEC.BOX_FLUSH_SETBACK),
                      fix="a shallower box row in the BoxStandard, or a deeper cavity")
    if box.air_barrier and not (box.box_use or "").startswith(AIR_SEALED):
        return failed(_CID, f"{where} breaches an air-control membrane on "
                            f"{box.wall_tag or box.host_layer}, and "
                            f"the BoxStandard has no {AIR_SEALED!r} {box.mounting} "
                            f"{box.gangs}-gang row", tags,
                      fix="add an air-sealed row: a flanged, gasketed box whose flange is "
                          "taped to the membrane")
    wired, missing = _loads(box, circuits, types, type_refs, loads)
    if missing is not None:
        return unknown(_CID, f"{where} names no circuit for {missing}, so its conductors are "
                             "unknown", tags, code=_CODE, fix="name the device's circuit")
    ungauged = next((w for w in wired if w.gauge is None), wired[0])
    if ungauged.gauge is None or box.volume_in3 is None:
        return unknown(_CID, f"{where}: no gauge for a {ungauged.circuit.breaker_amps} A "
                             "breaker or no box volume", tags, code=_CODE)
    # The deepest member sets the depth (314.24(B)).
    depths = []
    for w in wired:
        projection = getattr(w.product_type, "rear_projection", None)
        projection_in = None if projection is None else projection.meters / M_PER_IN
        depths.append((min_depth_in(w.gauge, projection_in), w.gauge, projection_in))
    min_depth, gauge_d, projection_in = max(depths, key=lambda d: d[0])
    if box.depth_m / M_PER_IN < min_depth - 1e-4:
        why = (f"a device projecting {projection_in:.2f}\" needs"
               if min_depth > MIN_DEPTH_IN[gauge_d] else f"{gauge_d} AWG to a device needs")
        return failed(_CID, f"{where} is {box.depth_m / M_PER_IN:.2f}\" deep; {why} "
                            f"{min_depth:.3f}\" internal depth", tags,
                      code=cite(NEC.BOX_DEPTH), fix="a deeper box row in the BoxStandard")
    clamps = box.internal_clamps is not False
    gauge = min(w.gauge for w in wired)  # the largest conductor is the lowest AWG
    required = shared_volume_in3(gauge, sum(w.cables for w in wired), clamps=clamps,
                                 support_fittings=box.support_fittings,
                                 terminal_blocks=box.terminal_blocks)
    for w in wired:
        neutral = (w.circuit.neutral if w.circuit.neutral is not None
                   else device_has_neutral(w.product_type))
        if w.per_cable is not None:
            required += (w.cables * w.per_cable + 2 * w.gangs) * VOLUME_PER_CONDUCTOR_IN3[w.gauge]
            continue
        required += conductor_volume_in3(w.gauge, w.circuit.poles, neutral, w.gangs, w.cables)
    feed = "+".join(sorted({"through-fed" if w.cables == 2 else "end-fed" for w in wired}))
    gauges = "/".join(str(g) for g in sorted({w.gauge for w in wired}, reverse=True))
    note = (f" ({mark(NEC.BOX_FILL_CLAMPS)} clamps not stated, so counted)"
            if box.internal_clamps is None else "")
    if required > box.volume_in3 + 1e-6:
        return failed(_CID, f"{where} holds {box.volume_in3:g} in³; {feed} {gauges} AWG "
                            f"needs {required:.2f} in³{note}", tags, code=_CODE,
                      fix=f"step up to {next_box_up(required)}")
    return passed(_CID, f"{where}: {required:.2f} in³ of {feed} {gauges} AWG in "
                        f"{box.volume_in3:g} in³{note}", tags, code=_CODE)


@check(Tier.ADVISORY, _CID)
def box_fill(ctx: CheckContext) -> list[Finding]:
    """Each derived device box against its through-fed fill and its cavity depth."""
    boxes = list(ctx.model.device_boxes)
    types = {t.tag: t for t in ctx.plan.library.electrical_device_types}
    declared = any(el.element_kind == "BoxStandard" for el in ctx.plan.all_elements())
    if not boxes:
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
    type_refs.update({head.tag: head.type_ref for head in ctx.model.alarm_heads})
    loads = _circuit_loads(ctx)
    out = [_grade(box, circuits, types, type_refs, loads) for box in boxes]
    unboxed = _unboxed_ceiling(ctx, types, {t for b in boxes for t in (b.device_tags or ())})
    if declared and unboxed:
        out.append(unknown(_CID, f"{len(unboxed)} ceiling fixture(s) take a box but no lined, "
                                 f"framed face is over them: {', '.join(unboxed)}",
                           tuple(unboxed), code=_CODE,
                           fix="model the ceiling or soffit they mount to (decision #140)"))
    return out


def _unboxed_ceiling(ctx: CheckContext, types: dict[str, Any], boxed: set[str]) -> list[str]:
    """Ceiling objects and hardwired alarm heads that take a box but got none."""
    wants = [obj.tag for obj in ctx.model.canvas_objects
             if obj.kind == "ElectricalDevice" and obj.mount is not None
             and obj.mount.kind.value == "ceiling"
             and takes_box(ctx.plan.by_tag(obj.tag), types.get(obj.type_ref or ""))]
    wants += [head.tag for head in ctx.model.alarm_heads if head.mount == "ceiling"
              and takes_box(ctx.plan.by_tag(head.tag), types.get(head.type_ref or ""))]
    return sorted(tag for tag in wants if tag not in boxed)


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
    boxes = boxes_by_device(ctx.model)
    circuits = {circuit.tag: circuit for circuit in ctx.plan.library.circuits}
    loads = _circuit_loads(ctx)
    out = []
    for run in sleeves:
        box = boxes.get(run.to_ref or "")
        members = box_members(box) if box is not None else []
        # One sleeve carries every member's cables; each member's breaker is its own.
        found = [(m, circuits.get(m.circuit or "")) for m in members]
        tags = (run.tag, run.to_ref) if run.to_ref else (run.tag,)
        if not found or any(c is None or GAUGE_BY_BREAKER_A.get(c.breaker_amps) is None
                            for _m, c in found):
            out.append(unknown(_AMPS, f"{run.tag}: no circuit or no copper gauge for its "
                                      "breaker", tags, code=_AMPS_CODE))
            continue
        cables = sum(1 if m.kind in _RECEPTACLES and loads.get(c.tag, 0) <= 1 else 2
                     for m, c in found)
        ccc = 2 * cables
        gauges = [GAUGE_BY_BREAKER_A[c.breaker_amps] for _m, c in found]
        on = ", ".join(dict.fromkeys(f"{c.tag} ({c.breaker_amps} A)" for _m, c in found))
        where = (f"{run.tag}: {run.length_m / M_PER_IN:.0f}\" sleeve, {ccc} current-carrying "
                 f"{'/'.join(str(g) for g in sorted(set(gauges), reverse=True))} AWG "
                 f"conductors on {on}")
        factor = adjustment_factor(ccc)
        if ccc <= 3 or run.length_m <= _EXEMPT_M:
            why = "three or fewer conductors" if ccc <= 3 else "a sleeve of 24 in. or less"
            out.append(passed(_AMPS, f"{where}: no adjustment applies ({why})", tags,
                              code=_AMPS_CODE))
            continue
        # The tightest margin governs: each member's gauge against its own breaker.
        ratings = [nm_ampacity(str(g), ccc) for g in gauges]
        rating = min(ratings)
        under = any(r < c.breaker_amps for r, (_m, c) in zip(ratings, found, strict=True))
        if not under:
            out.append(passed(_AMPS, f"{where}: {factor:.0%} gives {rating} A "
                                     f"(90 °C value, capped at 60 °C), covers the breaker",
                              tags, code=_AMPS_CODE))
        else:
            out.append(failed(_AMPS, f"{where}: {factor:.0%} gives {rating} A, under the "
                                     "breaker", tags, code=_AMPS_CODE,
                              fix="a larger conductor, a smaller breaker, or fewer cables in "
                                  "the sleeve"))
    return out
