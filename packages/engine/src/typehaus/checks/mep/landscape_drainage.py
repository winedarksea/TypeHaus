"""Rain gardens and leader extensions: is the basin big enough, far enough, fed downhill?

ADVISORY like the rest of site drainage. The sizing and setback numbers are the Minnesota
Stormwater Manual's; they are design guidance, not code, so a shortfall is a FAIL or an
UNKNOWN for the owner to answer, never a permit blocker.
"""

from __future__ import annotations

import math

from shapely.geometry import LineString, Point, Polygon

from typehaus.checks._authoring import advisory, not_applicable
from typehaus.checks._authoring import passed as _pass
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.landscape import RainGarden
from typehaus.model.structure import Drywell
from typehaus.model.trim import Downspout
from typehaus.resolve.drainage_network import EdgeKind
from typehaus.resolve.rain_garden import ponding_depth_m, ponding_volume_m3
from typehaus.resolve.roof_catchment import roof_catchments

_MANUAL = "MN Stormwater Manual"
#: Retain this depth of rain off the catchment (Manual, bioretention sizing: 1.0 in).
DESIGN_RAIN_DEPTH_IN = 1.0
#: Manual, minimum setbacks: 10 ft from a building foundation (a basement's is a FAIL) and
#: 10 ft from a property line.
FOUNDATION_SETBACK_FT = 10.0
PROPERTY_LINE_SETBACK_FT = 10.0
#: A foundation wall reaching this far below grade on a dwelling is a basement.
BASEMENT_DEPTH_FT = 4.0
#: Manual: ponded water gone within 48 h.
DRAWDOWN_HOURS = 48.0
#: IRC Table P3005.3: 1/8 in/ft for 3-6 in pipe, used as the floor for a site drain.
MIN_EXTENSION_SLOPE = 1.0 / 96.0
_M_PER_FT = 0.3048
_IN = 0.0254


def _gardens(ctx: CheckContext) -> list[RainGarden]:
    return [e for e in ctx.model.plan.all_elements() if isinstance(e, RainGarden)]


def _leaders(ctx: CheckContext) -> list[Downspout]:
    return [e for e in ctx.model.plan.all_elements() if isinstance(e, Downspout)]


def leader_arrivals(ctx: CheckContext, network) -> tuple[int, list[Finding]]:
    """``(extensions graded, problems)`` for ``drainage.outfall_connection``.

    A leader's extension arrives when its outlet sits no higher than the receiver takes
    water, and its last vertex lies inside a rain garden's rim or a drywell's shaft.
    """
    cid = "drainage.outfall_connection"
    by_tag = {e.tag: e for e in ctx.model.plan.all_elements()}
    out: list[Finding] = []
    count = 0
    for edge in network.edges:
        leader = by_tag.get(edge.source)
        if not isinstance(leader, Downspout) or edge.kind is not EdgeKind.PRIMARY:
            continue
        target = by_tag.get(edge.target)
        if leader.extension is None:
            if target is not None:
                out.append(advisory(
                    cid, f"{leader.tag} discharges to {edge.target} with no extension — "
                         f"nothing carries the water there", (leader.tag,), Result.FAIL))
            continue
        count += 1
        node = network.nodes.get(edge.target)
        if node is not None and node.in_invert_m is not None and edge.out_invert_m is not None:
            above = edge.out_invert_m - node.in_invert_m
            if above > 2 * _IN:
                out.append(advisory(
                    cid, f"{leader.tag}'s extension lets go {above / _IN:.0f}\" above "
                         f"{edge.target}'s rim", (leader.tag, edge.target), Result.FAIL))
        end = Point(leader.extension.path[-1].xy_m)
        inside = True
        if isinstance(target, RainGarden):
            inside = Polygon([p.xy_m for p in target.outline]).buffer(1e-6).contains(end)
        elif isinstance(target, Drywell):
            inside = end.distance(Point(target.position.xy_m)) <= target.diameter.meters / 2
        if not inside:
            out.append(advisory(
                cid, f"{leader.tag}'s extension ends outside {edge.target} — it stops short "
                     f"of the thing it discharges to", (leader.tag, edge.target), Result.FAIL))
    return count, out


def _catchment_m2(ctx: CheckContext, garden: RainGarden) -> float | None:
    catchments = roof_catchments(ctx.model).by_leader
    feeders = [e for e in _leaders(ctx) if e.discharge_ref == garden.tag]
    if not feeders or any(f.tag not in catchments for f in feeders):
        return None
    return sum(catchments[f.tag] for f in feeders)


@check(Tier.ADVISORY, "drainage.rain_garden_capacity")
def rain_garden_capacity(ctx: CheckContext) -> list[Finding]:
    """Ponding volume holds the design rain off every roof the basin is fed from."""
    cid = "drainage.rain_garden_capacity"
    gardens = _gardens(ctx)
    if not gardens:
        return [not_applicable(cid, "this plan authors no rain garden")]
    out: list[Finding] = []
    for garden in gardens:
        held = ponding_volume_m3(garden)
        area = _catchment_m2(ctx, garden)
        if area is None:
            out.append(advisory(
                cid, f"UNKNOWN — no roof catchment derives for every leader feeding "
                     f"{garden.tag}", (garden.tag,), Result.UNKNOWN, code=_MANUAL))
            continue
        need = area * DESIGN_RAIN_DEPTH_IN * _IN
        cf = 35.3146667
        msg = (f"{garden.tag} ponds {held * cf:.1f} cf against {need * cf:.1f} cf "
               f"({DESIGN_RAIN_DEPTH_IN:g}\" off {area / _M_PER_FT ** 2:.0f} sf of roof)")
        result = Result.PASS if held >= need - 1e-9 else Result.FAIL
        out.append(advisory(cid, msg, (garden.tag,), result, code=_MANUAL))
        out.extend(_non_roof_inflow(ctx, garden))
        if garden.infiltration_in_per_hr is None:
            out.append(advisory(
                cid, f"UNKNOWN — {garden.tag} drawdown is ungraded: no infiltration rate is "
                     f"authored (test the soil; ponding must clear in "
                     f"{DRAWDOWN_HOURS:.0f} h)", (garden.tag,), Result.UNKNOWN, code=_MANUAL))
        else:
            hours = ponding_depth_m(garden) / _IN / garden.infiltration_in_per_hr
            out.append(advisory(
                cid, f"{garden.tag} drains in {hours:.1f} h", (garden.tag,),
                Result.PASS if hours <= DRAWDOWN_HOURS else Result.FAIL, code=_MANUAL))
    return out


def _non_roof_inflow(ctx: CheckContext, garden: RainGarden) -> list[Finding]:
    """UNKNOWN for water that reaches a feeding leader from something that is not a roof."""
    from typehaus.resolve.drainage_network import build_network

    feeders = {e.tag for e in _leaders(ctx) if e.discharge_ref == garden.tag}
    network = build_network(ctx.model.plan)
    extra = sorted({(e.source, e.target) for e in network.edges
                    if e.kind is EdgeKind.PRIMARY and e.target in feeders
                    and network.nodes[e.source].kind != "leader"})
    return [advisory(
        "drainage.rain_garden_capacity",
        f"UNKNOWN — {garden.tag} also takes "
        f"{'pumped ' if network.nodes[source].kind == 'sump' else ''}water from {source} "
        f"(via {leader}); it is not in the design volume",
        (garden.tag, source), Result.UNKNOWN, code=_MANUAL)
        for source, leader in extra]


def _foundations(ctx: CheckContext) -> list[tuple[str, LineString, float, bool]]:
    """``(tag, axis, half thickness, is basement)`` for every below-grade building wall."""
    plan = ctx.model.plan
    grade = plan.project.site.grade
    grade_m = grade.meters if grade is not None else 0.0
    kinds = {b.tag: b.kind for b in plan.project.buildings}
    out = []
    for wall in ctx.model.walls:
        if wall.z0_m >= grade_m - 0.05:
            continue
        kind = kinds.get(plan.building_of(wall.storey), "dwelling")
        if kind == "sitework":
            continue
        basement = kind == "dwelling" and grade_m - wall.z0_m >= BASEMENT_DEPTH_FT * _M_PER_FT
        out.append((wall.tag, LineString(wall.axis), wall.thickness_m / 2.0, basement))
    return out


@check(Tier.ADVISORY, "drainage.infiltration_setback")
def infiltration_setback(ctx: CheckContext) -> list[Finding]:
    """A basin infiltrates away from foundations and off the neighbour's lot."""
    cid = "drainage.infiltration_setback"
    gardens = _gardens(ctx)
    if not gardens:
        return [not_applicable(cid, "this plan authors no rain garden")]
    walls = _foundations(ctx)
    parcel = [p.xy_m for p in ctx.model.plan.project.site.parcel]
    out: list[Finding] = []
    for garden in gardens:
        rim = Polygon([p.xy_m for p in garden.outline])
        for basement in (True, False):
            near = [(rim.distance(axis) - half, tag) for tag, axis, half, is_b in walls
                    if is_b is basement]
            if not near:
                continue
            gap, tag = min(near)
            gap_ft = gap / _M_PER_FT
            what = "basement foundation" if basement else "building foundation"
            if gap_ft >= FOUNDATION_SETBACK_FT:
                out.append(_pass(cid, f"{garden.tag} is {gap_ft:.1f} ft from the nearest "
                                      f"{what} ({tag})", (garden.tag,)))
            elif basement:
                out.append(advisory(
                    cid, f"{garden.tag} is {gap_ft:.1f} ft from basement wall {tag}, inside "
                         f"the {FOUNDATION_SETBACK_FT:.0f} ft setback", (garden.tag, tag),
                    Result.FAIL, code=_MANUAL))
            else:
                out.append(advisory(
                    cid, f"UNKNOWN — {garden.tag} is {gap_ft:.1f} ft from {tag}'s foundation "
                         f"against the Manual's recommended {FOUNDATION_SETBACK_FT:.0f} ft "
                         f"(no basement; an owner's call)", (garden.tag, tag),
                    Result.UNKNOWN, code=_MANUAL))
        if len(parcel) >= 3:
            gap_ft = Polygon(parcel).exterior.distance(rim) / _M_PER_FT
            if gap_ft >= PROPERTY_LINE_SETBACK_FT:
                out.append(_pass(cid, f"{garden.tag} is {gap_ft:.1f} ft from the lot line",
                                 (garden.tag,)))
            else:
                out.append(advisory(
                    cid, f"UNKNOWN — {garden.tag} is {gap_ft:.1f} ft from the lot line "
                         f"against the Manual's recommended {PROPERTY_LINE_SETBACK_FT:.0f} ft "
                         f"(confirm with the AHJ and the neighbour)", (garden.tag,),
                    Result.UNKNOWN, code=_MANUAL))
    return out


@check(Tier.ADVISORY, "drainage.leader_extension_fall")
def leader_extension_fall(ctx: CheckContext) -> list[Finding]:
    """A buried leader extension falls at least 1/8 in/ft to its outlet."""
    cid = "drainage.leader_extension_fall"
    leaders = [e for e in _leaders(ctx) if e.extension is not None]
    if not leaders:
        return [not_applicable(cid, "no leader carries a buried extension")]
    out: list[Finding] = []
    for leader in leaders:
        ext = leader.extension
        assert ext is not None
        pts = [p.xy_m for p in ext.path]
        run = sum(math.dist(a, b) for a, b in zip(pts[:-1], pts[1:], strict=True))
        fall = ext.inlet_invert.meters - ext.outlet_invert.meters
        slope = fall / run if run > 0 else 0.0
        msg = (f"{leader.tag} extension falls {fall / _IN:.1f}\" over "
               f"{run / _M_PER_FT:.1f} ft ({slope * 100:.1f}%)")
        out.append(advisory(cid, msg, (leader.tag,),
                            Result.PASS if slope >= MIN_EXTENSION_SLOPE - 1e-9 else Result.FAIL,
                            code="IRC P3005.3"))
    return out
