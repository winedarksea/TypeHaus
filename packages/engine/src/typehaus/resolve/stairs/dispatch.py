"""Stair validation + layout dispatch — the package's public entry point.

``_resolve_stair`` checks every authored reference and the geometry budget, then hands
member generation to the layout module (straight / u_split / winder) and runs the
structural guard passes from :mod:`typehaus.resolve.stairs.bearing`.
"""

from __future__ import annotations

import math

from typehaus.findings import Finding, element_error as _error
from typehaus.model.floors import FloorOpening, FloorSystem, Slab
from typehaus.model.spatial import Stair
from typehaus.resolve.model import FramedMember, ResolvedModel, ResolvedStair
from typehaus.resolve.stairs.bearing import _bear_stair_on_walls, _clip_stair_to_subfloor
from typehaus.resolve.stairs.common import (
    _MAX_RISER_M,
    _MIN_TREAD_M,
    _WELL_PARTITION_THICKNESS_M,
)
from typehaus.resolve.stairs.straight import _straight_stair_members
from typehaus.resolve.stairs.u_split import _u_split_landing_members
from typehaus.resolve.stairs.winder import _winder_stair_members


def _resolve_stair(
    model: ResolvedModel, stair: Stair, storey: str
) -> tuple[ResolvedStair | None, list[Finding]]:
    """Resolve an authored stair layout inside its explicitly-owned opening."""
    source = model.plan.storey(stair.from_storey)
    target = model.plan.storey(stair.to_storey)
    opening = model.plan.by_tag(stair.floor_opening)
    if source is None or target is None:
        return None, [_error("integrity.stair_storey", f"stair {stair.tag} references an "
                             "unknown storey", stair.tag)]
    if not isinstance(opening, FloorOpening):
        return None, [_error("integrity.stair_opening", f"stair {stair.tag} references "
                             f"missing FloorOpening {stair.floor_opening!r}", stair.tag)]
    if stair.to_storey != _element_storey(model, opening.tag):
        return None, [_error("integrity.stair_opening", f"stair {stair.tag} must use an "
                             "opening on its destination storey", stair.tag)]
    # The destination deck (wood FloorSystem or concrete Slab) must own the opening.
    destination_floor = next(
        (element for element in model.plan.storey_elements(stair.to_storey)
         if isinstance(element, (FloorSystem, Slab))), None)
    if destination_floor is None or opening.tag not in destination_floor.openings:
        return None, [_error("integrity.stair_opening", f"stair {stair.tag} opening must be "
                             "owned by the destination FloorSystem/Slab", stair.tag)]
    rise = target.elevation.meters - source.elevation.meters
    if rise <= 0:
        return None, [_error("integrity.stair_rise", f"stair {stair.tag} does not rise to "
                             "its destination storey", stair.tag)]
    outline = [point.xy_m for point in opening.outline]
    if len(outline) < 3:
        return None, [_error("integrity.stair_opening", f"stair {stair.tag} opening has no "
                             "usable outline", stair.tag)]
    xs, ys = [point[0] for point in outline], [point[1] for point in outline]
    along_x = stair.run_direction == "x"
    run = (max(xs) - min(xs)) if along_x else (max(ys) - min(ys))
    width = (max(ys) - min(ys)) if along_x else (max(xs) - min(xs))
    if width + 1e-9 < stair.width.meters:
        return None, [_error("integrity.stair_width", f"stair {stair.tag} is wider than its "
                             "floor opening", stair.tag)]
    if stair.layout not in {"straight", "u_split_landing", "right_angle_winder"}:
        return None, [_error("integrity.stair_layout", f"stair {stair.tag} has unknown layout "
                             f"{stair.layout!r}", stair.tag)]
    if stair.layout == "right_angle_winder":
        if stair.turn_direction not in {"left", "right"}:
            return None, [_error("integrity.stair_turn", f"stair {stair.tag} needs a left or "
                                 "right turn direction", stair.tag)]
        if stair.winder_count < 3:
            return None, [_error("integrity.stair_winders", f"stair {stair.tag} needs at least "
                                 "three winders for a quarter turn", stair.tag)]
    elif stair.winder_count:
        return None, [_error("integrity.stair_winders", f"stair {stair.tag} only accepts "
                             "winders in right_angle_winder layout", stair.tag)]
    # ``bearing_refs`` grants bearing permission, so a tag naming no wall on the storey the
    # flight springs from would silently grant nothing — that is an authoring error.
    missing_bearing = [tag for tag in stair.bearing_refs
                       if not any(wall.tag == tag and wall.storey == stair.from_storey
                                  for wall in model.walls)]
    if missing_bearing:
        return None, [_error("integrity.stair_bearing", f"stair {stair.tag} references "
                             "missing bearing wall(s) on "
                             f"{stair.from_storey}: {', '.join(missing_bearing)}", stair.tag)]
    risers = math.ceil(rise / _MAX_RISER_M)
    treads = max(0, risers - 1)
    straight_treads = treads - stair.winder_count
    # Turn-landing depth (in the run direction) for the U-stair. Unset reproduces the
    # historical "reserve one stair width" behaviour; an authored value renders a deeper
    # walk-off platform. IRC R311.7.6 floors the landing at the stair width.
    landing_depth_m = (max(stair.landing_depth.meters, stair.width.meters)
                       if stair.landing_depth is not None else stair.width.meters)
    # A winder turn consumes a square whose side is the stair width. The remaining treads
    # must still meet the 10 in. minimum on their straight walking line.
    if stair.layout == "u_split_landing":
        # Split-landing riser budget: lower treads, the lower landing, the upper landing
        # one riser above (that riser IS the "step" between the half-width landings),
        # upper treads, then the arrival deck — so the flights share ``risers - 3``
        # treads, with an odd extra tread going to the lower flight. The parallel
        # flights use the opening length less the landing depth.
        flight_treads = max(0, risers - 3)
        lower_treads = (flight_treads + 1) // 2
        straight_run = run - landing_depth_m
        tread = straight_run / lower_treads if lower_treads else 0.0
    else:
        straight_run = run - stair.width.meters if stair.layout == "right_angle_winder" else run
        tread = straight_run / straight_treads if straight_treads else 0.0
    if tread + 1e-9 < _MIN_TREAD_M:
        return None, [_error("integrity.stair_geometry", f"stair {stair.tag} needs {risers} "
                             f"risers but its opening only permits {tread / 0.0254:.1f}\" treads "
                             "(IRC R311.7 requires 10\")", stair.tag)]
    riser = rise / risers
    if not _stair_fits_opening(stair, min(xs), max(xs), min(ys), max(ys), tread, risers,
                               landing_depth_m):
        return None, [_error("integrity.stair_opening", f"stair {stair.tag} extends outside "
                             f"floor opening {opening.tag!r}", stair.tag)]
    members = _stair_members(stair, min(xs), min(ys), source.elevation.meters, risers, riser,
                             tread, landing_depth_m)
    # Structural guards: the flight never drops below the subfloor it springs from (so a
    # U-stair well partition cannot poke through the foundation), and every flight is
    # borne on the walls beside it — posted down wherever none reaches.
    members = _clip_stair_to_subfloor(members, source.elevation.meters)
    members = _bear_stair_on_walls(model, stair, members, source.elevation.meters)
    # A stair declaration lives with its destination deck so it can own the opening, but
    # its resolved plan-storey identity is the floor it rises *from*.
    return ResolvedStair(stair.uid, stair.tag, stair.from_storey, stair.to_storey, outline, risers, riser,
                         tread, stair.run_direction, stair.run_reversed, stair.layout,
                         stair.turn_direction, stair.winder_count, members), []


def _element_storey(model: ResolvedModel, tag: str) -> str | None:
    for storey, elements in model.plan.elements.items():
        if any(element.tag == tag for element in elements):
            return storey
    return None


def _stair_members(stair: Stair, minx: float, miny: float, z0: float, risers: int,
                   riser: float, tread: float,
                   landing_depth_m: float) -> tuple[FramedMember, ...]:
    if stair.layout == "right_angle_winder":
        return _winder_stair_members(stair, minx, miny, z0, risers, riser, tread)
    if stair.layout == "u_split_landing":
        return _u_split_landing_members(stair, minx, miny, z0, risers, riser, tread,
                                        landing_depth_m)
    return _straight_stair_members(stair, minx, miny, z0, risers, riser, tread)


def _stair_fits_opening(stair: Stair, minx: float, maxx: float, miny: float, maxy: float,
                        tread: float, risers: int, landing_depth_m: float) -> bool:
    """Keep the generated flight entirely within its destination deck opening.

    The opening is the structural headroom contract shared by both storeys.  Resolving a
    flight from a shifted start without checking its cross-flight edge could generate treads
    under intact deck, even when its scalar run and width each fit the opening in isolation.
    """
    start_x, start_y = stair.start.xy_m if stair.start is not None else (minx, miny)
    if stair.layout == "u_split_landing":
        # Mirrors _u_split_landing_members: flights share risers - 3 treads, and the
        # (longer) lower flight takes the odd extra one, and the two lanes are held apart
        # by the well partition — so the cross-run budget is 2 flights *plus* partition.
        lower_treads = (max(0, risers - 3) + 1) // 2
        required_run = landing_depth_m + tread * lower_treads
        required_cross = 2 * stair.width.meters + _WELL_PARTITION_THICKNESS_M
        if stair.run_direction == "x":
            return (required_cross <= maxy - miny + 1e-9
                    and required_run <= maxx - minx + 1e-9)
        return (required_cross <= maxx - minx + 1e-9
                and required_run <= maxy - miny + 1e-9)
    if stair.layout == "right_angle_winder":
        straight_treads = risers - 1 - stair.winder_count
        cross_end = (start_y + (1 if stair.turn_direction != "right" else -1) * stair.width.meters
                     if stair.run_direction == "x" else
                     start_x + (1 if stair.turn_direction != "right" else -1) * stair.width.meters)
        if stair.run_direction == "x":
            end_x = start_x + (-1 if stair.run_reversed else 1) * (
                stair.width.meters + tread * straight_treads)
            return (min(start_x, end_x) >= minx - 1e-9 and max(start_x, end_x) <= maxx + 1e-9
                    and min(start_y, cross_end) >= miny - 1e-9
                    and max(start_y, cross_end) <= maxy + 1e-9)
        end_y = start_y + (-1 if stair.run_reversed else 1) * (
            stair.width.meters + tread * straight_treads)
        return (min(start_y, end_y) >= miny - 1e-9 and max(start_y, end_y) <= maxy + 1e-9
                and min(start_x, cross_end) >= minx - 1e-9
                and max(start_x, cross_end) <= maxx + 1e-9)
    run = (-1 if stair.run_reversed else 1) * tread * max(0, risers - 1)
    if stair.run_direction == "x":
        return (min(start_x, start_x + run) >= minx - 1e-9
                and max(start_x, start_x + run) <= maxx + 1e-9
                and miny - 1e-9 <= start_y
                and start_y + stair.width.meters <= maxy + 1e-9)
    return (min(start_y, start_y + run) >= miny - 1e-9
            and max(start_y, start_y + run) <= maxy + 1e-9
            and minx - 1e-9 <= start_x
            and start_x + stair.width.meters <= maxx + 1e-9)
