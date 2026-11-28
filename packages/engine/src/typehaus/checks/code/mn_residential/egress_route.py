"""R310.1 / R310.3.2.1: where an escape DOOR opens, can you get from that floor to grade?

An exterior door satisfies R310.1 only if it opens "into a public way, yard or court" and, when
that floor is an area well deeper than 44", the well has a permanently affixed ladder or steps
(R310.3.2.1; Minn. R. 1309.0310 amends R310.1's "yard or court that opens to a public way").
The door's own floor is not enough: the sunken garden's door opens 75" below grade into a court
closed by walls on every side. This follows the chain from that floor: a stair that reaches
grade, or a ladder graded on its rung rules whose exit surface is joined by stairs to grade.
Paraphrase only (IRC 2018 R310.3.2.1; the text read on UpCodes 2026-11-27).
"""

from __future__ import annotations

from shapely.geometry import LineString, Polygon

from typehaus.model.structure import Railing
from typehaus.quantities import inch

_MAX_DEPTH_WITHOUT_ROUTE = inch(44).meters
_MIN_RUNG_WIDTH = inch(12).meters
_MIN_RUNG_PROJECTION = inch(3).meters
_MAX_RUNG_SPACING = inch(18).meters
_MAX_RISER = inch(7.75).meters  # R311.7.5.1: the most a step at grade may rise
#: A ladder base stands on the floor it climbs from: within this of that floor, in z and plan.
_ON_FLOOR_TOL_M = 0.15
#: How far from the ladder an exit surface or a guard may lie and still be its side step.
_EXIT_REACH_M = 0.6
#: A wall-top threshold between a deck edge and the stair head it joins (12 1/4" wall).
_JOIN_REACH_M = 0.4


def well_route_verdict(ctx, opening, landing_top_m: float, landing_poly: Polygon,
                       surfaces) -> tuple[str, str]:
    """``(result, text)`` with result ``pass``/``fail``/``unknown``.

    ``surfaces`` is ``(name, polygon, top_m)`` for every walkable plane the plan models. Pass
    only on a complete chain; FAIL only when the floor is deep and no stair or ladder starts on
    it, or a chain element is positively wrong; UNKNOWN where an input is not resolved.
    """
    grade = ctx.plan.project.site.grade.meters
    depth = grade - landing_top_m
    where = f"{opening.tag} opens {depth / .0254:.0f}\" below grade"
    if depth <= _MAX_DEPTH_WITHOUT_ROUTE + 1e-6:
        return "pass", f"{where}, within R310.3.2.1's 44\""
    stairs = [s for s in ctx.model.stairs if _stair_on_floor(s, landing_top_m, landing_poly)]
    for stair in stairs:
        if stair.arrival_elevation_m >= grade - _MAX_RISER - 1e-6:
            return "pass", f"{where}; {stair.tag} climbs from that floor to grade"
    ladders = [o for o in ctx.model.canvas_objects if _ladder_spec(ctx, o) is not None
               and _on_floor(o, landing_top_m, landing_poly)]
    if not ladders:
        return "fail", (f"{where} onto a floor with no stair or ladder leaving it; "
                        "R310.1 needs the opening to reach a yard or court that opens to a "
                        "public way, and R310.3.2.1 a permanently affixed ladder or steps "
                        "in an area well deeper than 44\"")
    notes: list[str] = []
    for obj in ladders:
        result, text = _ladder_chain(ctx, opening, obj, grade, surfaces)
        if result == "pass":
            return "pass", f"{where}; {text}"
        notes.append(f"{obj.tag}: {text}")
        if result == "unknown":
            return "unknown", f"{where}; " + "; ".join(notes)
    return "fail", f"{where}; " + "; ".join(notes)


def door_well_verdict(ctx, opening, wall, rooms_by_storey) -> tuple[str, str]:
    """Find the floor ``opening`` lands on (R311.3's patch and coverage test), then grade its
    route. UNKNOWN where the threshold or the landing cannot be resolved."""
    # Lazy: egress.py imports this module, and these helpers live there.
    from typehaus.checks.code.mn_residential.egress import _landing_patch, _landing_surfaces
    from typehaus.resolve.doorway_heights import installed_threshold_elevation

    surfaces = _landing_surfaces(ctx, union=True)
    patch = _landing_patch(ctx, wall, opening, rooms_by_storey)
    threshold, basis = installed_threshold_elevation(opening, wall)
    if patch is None or threshold is None:
        return "unknown", f"{opening.tag}: no landing patch or threshold ({basis})"
    covered = [(name, poly, top) for name, poly, top in surfaces
               if poly.intersection(patch).area >= patch.area * 0.85
               and threshold - _MAX_RISER - 1e-6 <= top <= threshold + 0.05]
    if not covered:
        return "unknown", f"{opening.tag}: no modelled surface at its threshold to land on"
    name, poly, top = max(covered, key=lambda item: item[2])
    return well_route_verdict(ctx, opening, top, poly, surfaces)


def _stair_on_floor(stair, floor_top_m: float, floor_poly: Polygon) -> bool:
    if (stair.base_elevation_m is None or stair.arrival_elevation_m is None
            or abs(stair.base_elevation_m - floor_top_m) > _ON_FLOOR_TOL_M
            or len(stair.outline) < 3):
        return False
    ring = Polygon(stair.outline)
    return ring.is_valid and ring.distance(floor_poly) <= _ON_FLOOR_TOL_M


def _ladder_spec(ctx, obj):
    for furniture in ctx.plan.library.furniture_types:
        if furniture.tag == obj.type_ref:
            return furniture.ladder
    return None


def _on_floor(obj, floor_top_m: float, floor_poly: Polygon) -> bool:
    return (abs(obj.z_m - floor_top_m) <= _ON_FLOOR_TOL_M and len(obj.footprint) >= 3
            and Polygon(obj.footprint).distance(floor_poly) <= _ON_FLOOR_TOL_M)


def _ladder_chain(ctx, opening, obj, grade: float, surfaces) -> tuple[str, str]:
    spec = _ladder_spec(ctx, obj)
    foot = Polygon(obj.footprint)
    # The rung rules of R310.3.2.1, read off the spec; a failing figure is positive evidence.
    problems = []
    if spec.rung_inside_width.meters + 1e-9 < _MIN_RUNG_WIDTH:
        problems.append(f"rungs {spec.rung_inside_width.inches:.0f}\" inside, 12\" required")
    if spec.rung_projection.meters + 1e-9 < _MIN_RUNG_PROJECTION:
        problems.append(f"rungs project {spec.rung_projection.inches:.1f}\", 3\" required")
    if spec.rung_spacing.meters > _MAX_RUNG_SPACING + 1e-9:
        problems.append(f"rungs {spec.rung_spacing.inches:.0f}\" o.c., 18\" allowed")
    if spec.first_rung_height.meters > _MAX_RUNG_SPACING + 1e-9:
        problems.append(f"first rung {spec.first_rung_height.inches:.0f}\" up, 18\" allowed")
    if problems:
        return "fail", "; ".join(problems)
    sweep = getattr(opening, "swing_clearance", None)
    if sweep and len(sweep) >= 3:
        leaf = Polygon(sweep)
        if leaf.is_valid and leaf.intersection(foot).area > 1e-6:
            return "fail", "the ladder stands in the door's swing"
    top_rung = obj.z_m + spec.top_rung_height.meters
    # The exit surface: a walkable plane beside the ladder's top, within one rung spacing above
    # the top rung (or a hair below), and standing at or above grade less one riser.
    exits = [(name, poly, top) for name, poly, top in surfaces
             if poly.distance(foot) <= _EXIT_REACH_M
             and top_rung - 0.05 <= top <= top_rung + _MAX_RUNG_SPACING
             and top >= grade - _MAX_RISER]
    if not exits:
        return "fail", (f"its top rung ({(top_rung - grade) / .0254:+.0f}\" to grade) meets no "
                        "walkable surface beside it within 18\"")
    name, poly, top = max(exits, key=lambda item: item[2])
    gap = (top - top_rung) / .0254
    if spec.exit == "side_step":
        guards = [r for r in ctx.plan.all_elements() if isinstance(r, Railing)
                  and _near(r, foot, _EXIT_REACH_M)]
        if guards and not any(r.gate for r in guards):
            return "fail", (f"its exit crosses guard {guards[0].tag} with no gate leaf "
                            "(Railing.gate) in it")
    onward = _onward(ctx, poly, top, grade)
    if onward is None:
        return "unknown" if not ctx.model.stairs else "fail", (
            f"exits onto {name} ({gap:.1f}\" above the top rung) but no stair joins it to "
            "grade")
    return "pass", (f"{obj.tag} ({spec.rung_count} rungs at {spec.rung_spacing.inches:.0f}\", "
                    f"{spec.rung_inside_width.inches:.0f}\" wide, {spec.rung_projection.inches:.0f}"
                    f"\" proud) exits onto {name}, then {onward} to grade")


def _near(railing, foot: Polygon, reach_m: float) -> bool:
    pts = [p.xy_m for p in railing.path]
    return len(pts) >= 2 and LineString(pts).distance(foot) <= reach_m


def _onward(ctx, poly: Polygon, top: float, grade: float) -> str | None:
    """The stair that joins ``poly`` (at ``top``) down to grade, by tag, or ``None``."""
    for stair in ctx.model.stairs:
        if (stair.base_elevation_m is None or stair.arrival_elevation_m is None
                or len(stair.outline) < 3
                or abs(stair.arrival_elevation_m - top) > _ON_FLOOR_TOL_M):
            continue
        ring = Polygon(stair.outline)
        if not ring.is_valid or ring.distance(poly) > _JOIN_REACH_M:
            continue
        if stair.base_elevation_m - grade <= _MAX_RISER + 1e-6:
            return stair.tag
    return None
