"""Stair validation + layout dispatch — the package's public entry point.

``_resolve_stair`` checks every authored reference and the geometry budget, then hands
member generation to the layout module (straight / u_split / winder) and runs the
structural guard passes from :mod:`typehaus.resolve.stairs.bearing`.
"""

from __future__ import annotations

import math
from dataclasses import replace

from typehaus.findings import Finding, element_error as _error
from typehaus.model.floors import FloorOpening, FloorSystem, Slab
from typehaus.model.spatial import Stair
from typehaus.quantities import inch
from typehaus.resolve.model import FramedMember, ResolvedModel, ResolvedStair
from typehaus.resolve.stairs.bearing import _bear_stair_on_walls, _clip_stair_to_subfloor
from typehaus.resolve.stairs.common import (
    _MAX_RISER_M,
    _DEFAULT_NOSING_DEPTH_M,
    _DEFAULT_TREAD_DEPTH_M,
    _MAX_NOSING_DEPTH_M,
    _MIN_NOSING_DEPTH_M,
    _MIN_LANDING_DEPTH_M,
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
    if source is None or target is None:
        return None, [_error("integrity.stair_storey", f"stair {stair.tag} references an "
                             "unknown storey", stair.tag)]
    if (stair.base_elevation is None) != (stair.top_elevation is None):
        return None, [_error("integrity.stair_rise", f"stair {stair.tag} authors only one of "
                             "base_elevation/top_elevation; a flight that states its own "
                             "rise must state both ends of it", stair.tag)]
    base, top = stair.base_elevation, stair.top_elevation
    explicit = base is not None and top is not None
    z0 = base.meters if base is not None else source.elevation.meters
    z_top = top.meters if top is not None else target.elevation.meters
    rise = z_top - z0
    if rise <= 0:
        return None, [_error("integrity.stair_rise", f"stair {stair.tag} does not rise to "
                             "its destination", stair.tag)]

    if stair.floor_opening is None:
        # A run that passes through no floor — a step-down within one storey. There is no
        # hole to bound it, so the flight bounds itself: its footprint is derived below,
        # once the riser count is known, and it must state where it starts.
        if stair.start is None:
            return None, [_error("integrity.stair_opening", f"stair {stair.tag} has no "
                                 "floor_opening, so it must author start", stair.tag)]
        if not explicit:
            return None, [_error("integrity.stair_rise", f"stair {stair.tag} has no "
                                 "floor_opening, so its rise cannot come from a pair of "
                                 "storey elevations: author base_elevation/top_elevation",
                                 stair.tag)]
        if stair.layout != "straight":
            return None, [_error("integrity.stair_layout", f"stair {stair.tag} has no "
                                 "floor_opening; only a straight flight is bounded without "
                                 "one", stair.tag)]
        opening = None
        outline: list[tuple[float, float]] = []
        xs = ys = []
    else:
        opening = model.plan.by_tag(stair.floor_opening)
        if not isinstance(opening, FloorOpening):
            return None, [_error("integrity.stair_opening", f"stair {stair.tag} references "
                                 f"missing FloorOpening {stair.floor_opening!r}", stair.tag)]
        if stair.to_storey != _element_storey(model, opening.tag):
            return None, [_error("integrity.stair_opening", f"stair {stair.tag} must use an "
                                 "opening on its destination storey", stair.tag)]
        # The destination deck (wood FloorSystem or concrete Slab) must own the opening.
        # Asked of *any* deck on that storey, not of the first one found: a storey may carry
        # several — catlin's main floor is two I-joist bays and a concrete band since
        # 2026-08-21, and its breezeway deck is filed there too — and "the first element
        # that is a FloorSystem or a Slab" then depends on authoring order rather than on
        # which deck the hole is in.
        if not any(isinstance(element, (FloorSystem, Slab))
                   and opening.tag in element.openings
                   for element in model.plan.storey_elements(stair.to_storey)):
            return None, [_error("integrity.stair_opening", f"stair {stair.tag} opening must "
                                 "be owned by the destination FloorSystem/Slab", stair.tag)]
        outline = [point.xy_m for point in opening.outline]
        if len(outline) < 3:
            return None, [_error("integrity.stair_opening", f"stair {stair.tag} opening has "
                                 "no usable outline", stair.tag)]
        xs, ys = [point[0] for point in outline], [point[1] for point in outline]
        along_x = stair.run_direction == "x"
        width = (max(ys) - min(ys)) if along_x else (max(xs) - min(xs))
        if width + 1e-9 < stair.width.meters:
            return None, [_error("integrity.stair_width", f"stair {stair.tag} is wider than "
                                 "its floor opening", stair.tag)]
    along_x = stair.run_direction == "x"
    run = (0.0 if opening is None else
           ((max(xs) - min(xs)) if along_x else (max(ys) - min(ys))))
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
    if (stair.layout == "u_split_landing" and stair.turn_direction is not None
            and stair.turn_direction not in {"left", "right"}):
        return None, [_error("integrity.stair_turn", f"stair {stair.tag} has unknown turn "
                             f"direction {stair.turn_direction!r}", stair.tag)]
    # ``bearing_refs`` grants bearing permission, so a tag naming no wall on the storey the
    # flight springs from would silently grant nothing — that is an authoring error.
    missing_bearing = [tag for tag in stair.bearing_refs
                       if not any(wall.tag == tag and wall.storey == stair.from_storey
                                  for wall in model.walls)]
    if missing_bearing:
        return None, [_error("integrity.stair_bearing", f"stair {stair.tag} references "
                             "missing bearing wall(s) on "
                             f"{stair.from_storey}: {', '.join(missing_bearing)}", stair.tag)]
    physical_tread_m = (stair.tread_depth.meters if stair.tread_depth is not None
                        else _DEFAULT_TREAD_DEPTH_M)
    nosing_m = (stair.nosing_depth.meters if stair.nosing_depth is not None
                else _DEFAULT_NOSING_DEPTH_M)
    going_m = physical_tread_m - nosing_m
    if nosing_m < -1e-9 or (nosing_m > 1e-9 and not
                            _MIN_NOSING_DEPTH_M - 1e-9 <= nosing_m <= _MAX_NOSING_DEPTH_M + 1e-9):
        return None, [_error("integrity.stair_nosing", f"stair {stair.tag} nosing must be "
                             "0 or 3/4\"–1 1/4\"", stair.tag)]
    if physical_tread_m + 1e-9 < inch(11).meters and nosing_m <= 1e-9:
        return None, [_error("integrity.stair_nosing", f"stair {stair.tag} needs a nosing "
                             "when its physical tread is under 11\"", stair.tag)]
    if going_m + 1e-9 < _MIN_TREAD_M:
        return None, [_error("integrity.stair_geometry", f"stair {stair.tag} has "
                             f"{going_m / 0.0254:.1f}\" going; IRC R311.7 requires 10\"", stair.tag)]
    risers = math.ceil(rise / _MAX_RISER_M)
    treads = max(0, risers - 1)
    straight_treads = treads - stair.winder_count
    # Turn-landing depth (in the run direction) for the U-stair. Unset reproduces the
    # historical "reserve one stair width" behaviour; an authored value is honoured down to
    # the IRC R311.7.6 direction-of-travel minimum (see ``_MIN_LANDING_DEPTH_M``), which is
    # 36" and *not* the stair width.
    landing_depth_m = (max(stair.landing_depth.meters, _MIN_LANDING_DEPTH_M)
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
        available_going = straight_run / lower_treads if lower_treads else 0.0
    else:
        straight_run = run - stair.width.meters if stair.layout == "right_angle_winder" else run
        available_going = straight_run / straight_treads if straight_treads else 0.0
    # A flight with no opening has no run budget to blow: nothing bounds it overhead, so its
    # footprint is whatever its own risers and going come to, derived below.
    if opening is not None and available_going + 1e-9 < going_m:
        return None, [_error("integrity.stair_geometry", f"stair {stair.tag} needs {risers} "
                             f"risers but its opening only permits {available_going / 0.0254:.1f}\" "
                             f"going (needs {going_m / 0.0254:.1f}\")", stair.tag)]
    riser = rise / risers
    if opening is not None and not _stair_fits_opening(
            stair, min(xs), max(xs), min(ys), max(ys), going_m, risers, landing_depth_m):
        return None, [_error("integrity.stair_opening", f"stair {stair.tag} extends outside "
                             f"floor opening {opening.tag!r}", stair.tag)]
    if opening is not None:
        origin_x, origin_y = min(xs), min(ys)
    else:
        # ``start`` is required without an opening — the guard above returns an integrity
        # error when it is missing — but that is two branches back from here.
        assert stair.start is not None
        origin_x, origin_y = stair.start.xy_m
    members = _stair_members(stair, origin_x, origin_y, z0, risers, riser,
                             going_m, physical_tread_m, nosing_m, landing_depth_m)
    if opening is None:
        outline = _flight_footprint(stair, going_m, risers)
    # Structural guards: the flight never drops below the subfloor it springs from (so a
    # U-stair well partition cannot poke through the foundation), and every flight is
    # borne on the walls beside it — posted down wherever none reaches.
    members = _clip_stair_to_subfloor(members, z0)
    members = _bear_stair_on_walls(model, stair, members, z0)
    members = _in_stair_material(stair, members)
    # A stair declaration lives with its destination deck so it can own the opening, but
    # its resolved plan-storey identity is the floor it rises *from*.
    return ResolvedStair(stair.uid, stair.tag, stair.from_storey, stair.to_storey, outline, risers, riser,
                         physical_tread_m, stair.run_direction, stair.run_reversed, stair.layout,
                         stair.turn_direction, stair.winder_count, members,
                         going_depth_m=going_m, nosing_depth_m=nosing_m,
                         base_elevation_m=z0, arrival_elevation_m=z_top), []


def _in_stair_material(stair: Stair, members: tuple[FramedMember, ...]
                       ) -> tuple[FramedMember, ...]:
    """Stamp the flight's material onto every member it generated.

    Applied here, once, rather than threaded through twenty ``FramedMember`` constructions
    across ``straight`` / ``u_split`` / ``winder`` / ``bearing``: the material is a property
    of the flight, not of any one stringer, and a member the *bearing* pass posts down under
    a PT flight is PT for the same reason its stringers are. A generator that has already
    named a material for a member keeps it — nothing here overrides a more specific answer.
    """
    if stair.material is None:
        return members
    return tuple(member if member.material is not None
                 else replace(member, material=stair.material)
                 for member in members)


def _flight_footprint(stair: Stair, going_m: float, risers: int) -> list[tuple[float, float]]:
    """The plan rectangle a flight with no floor opening occupies.

    Every consumer of ``ResolvedStair.outline`` — the plan drawing, the room-area deduction,
    the UI's stair pick — reads the *opening* outline, because until a flight could exist
    without one that was the only footprint there was. A within-storey run bounds itself
    instead: ``start``, the authored width across, and ``going x treads`` along the run.
    """
    assert stair.start is not None  # only reached for a flight that authored one
    start_x, start_y = stair.start.xy_m
    sign = -1 if stair.run_reversed else 1
    span = sign * going_m * (risers - 1)
    width = stair.width.meters
    if stair.run_direction == "x":
        x0, x1 = sorted((start_x, start_x + span))
        y0, y1 = start_y, start_y + width
    else:
        x0, x1 = start_x, start_x + width
        y0, y1 = sorted((start_y, start_y + span))
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _element_storey(model: ResolvedModel, tag: str) -> str | None:
    for storey, elements in model.plan.elements.items():
        if any(element.tag == tag for element in elements):
            return storey
    return None


def _stair_members(stair: Stair, minx: float, miny: float, z0: float, risers: int,
                   riser: float, going: float, tread_depth: float, nosing: float,
                   landing_depth_m: float) -> tuple[FramedMember, ...]:
    if stair.layout == "right_angle_winder":
        return _winder_stair_members(stair, minx, miny, z0, risers, riser, going,
                                     tread_depth, nosing)
    if stair.layout == "u_split_landing":
        return _u_split_landing_members(stair, minx, miny, z0, risers, riser, going,
                                        tread_depth, nosing,
                                        landing_depth_m)
    return _straight_stair_members(stair, minx, miny, z0, risers, riser, going,
                                  tread_depth, nosing)


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
