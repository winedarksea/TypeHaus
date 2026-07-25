"""Resolve authored stairs into framed geometry: flights, landings, winder turns.

Split out of ``resolve/envelope.py`` (which had grown past the 500-line guideline) so the
stair generator — layout selection, the raked-stringer geometry, landing platforms, the
winder fan, and the bearing pass that hangs a flight on the walls beside it — has one
home. ``resolve_envelope_geometry`` is the only caller.
"""

from __future__ import annotations

import math
from dataclasses import replace

from typehaus.findings import Finding, element_error as _error
from typehaus.model.enums import StructuralRole
from typehaus.model.floors import FloorOpening, FloorSystem, Slab
from typehaus.model.spatial import Stair
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import FramedMember, ResolvedModel, ResolvedStair

_MAX_RISER_M = 7.75 * 0.0254  # IRC R311.7
_MIN_TREAD_M = 10.0 * 0.0254
_TREAD_THICKNESS_M = 0.0381  # 1.5" tread/deck board
_LANDING_JOIST_PROFILE = "2x8"
_FRAMING_SPACING_M = 0.4064  # 16" o.c.
# Below this a stair member only clips a wall's end; it does not bear on it.
_MIN_SHARED_RUN_M = 0.10


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
    along_x = stair.run_direction == "x"
    start_x, start_y = stair.start.xy_m if stair.start is not None else (minx, miny)
    width = stair.width.meters
    sign = -1 if stair.run_reversed else 1
    if along_x:
        end_x, end_y = start_x + sign * tread * (risers - 1), start_y
        strings = (((start_x, start_y), (end_x, end_y)),
                   ((start_x, start_y + width), (end_x, end_y + width)))
    else:
        end_x, end_y = start_x, start_y + sign * tread * (risers - 1)
        strings = (((start_x, start_y), (end_x, end_y)),
                   ((start_x + width, start_y), (end_x + width, end_y)))
    stringer_depth = cross_section("2x12").depth_m
    spring_top = z0 + riser + 0.0381  # top of the first tread at the springing end
    arrival = z0 + riser * risers
    out = [
        FramedMember(stair.uid, f"stringer-{index}", "stringer", "2x12", a, b,
                     spring_top - stringer_depth, spring_top,
                     math.hypot(tread * (risers - 1), riser * risers),
                     z0_end_m=arrival - stringer_depth, z1_end_m=arrival)
        for index, (a, b) in enumerate(strings)
    ]
    for index in range(risers - 1):
        if along_x:
            a = (start_x + sign * tread * index, start_y)
            b = (start_x + sign * tread * index, start_y + width)
        else:
            a = (start_x, start_y + sign * tread * index)
            b = (start_x + width, start_y + sign * tread * index)
        z = z0 + riser * (index + 1)
        out.append(FramedMember(stair.uid, f"tread-{index:03d}", "tread", "2x12", a, b,
                                 z, z + 0.0381, stair.width.meters))
    return tuple(out)


def _grid_positions(span: float, spacing: float) -> list[float]:
    """Deduplicated on-center positions ``{0, s, 2s, …, span}`` including both edges.

    Replaces the old ``ceil``/``range``/``min``-clamp pattern whose last two positions
    were coincident whenever ``span`` was an exact multiple of ``spacing``.
    """
    if span <= 1e-9:
        return [0.0]
    positions = [spacing * index for index in range(math.ceil(span / spacing - 1e-9))]
    positions.append(span)
    out: list[float] = []
    for position in positions:
        if not out or position - out[-1] > 1e-9:
            out.append(position)
    return out


def _u_split_landing_members(stair: Stair, minx: float, miny: float, z0: float,
                             risers: int, riser: float, tread: float,
                             landing_depth_m: float) -> tuple[FramedMember, ...]:
    """Generate two parallel flights joined by two half-width landings one riser apart.

    Riser budget (split-landing semantics): ``lower`` treads, the lower landing, the
    upper landing one riser above it (that riser IS the "step" between the landings),
    ``upper`` treads, then the arrival deck — ``lower + upper + 3 == risers``. Both
    landings sit in the landing zone beyond the flight ends, ``landing_depth_m`` deep.
    """
    width = stair.width.meters
    flight_treads = max(0, risers - 3)
    lower_treads = (flight_treads + 1) // 2  # odd extra tread goes to the lower flight
    upper_treads = flight_treads - lower_treads
    sign = -1 if stair.run_reversed else 1
    along_x = stair.run_direction == "x"
    start = minx if along_x else miny
    lane0 = miny if along_x else minx
    lane1 = lane0 + width

    def at(s: float, cross: float) -> tuple[float, float]:
        """Plan point ``s`` metres along the run (signed from the start edge) at the
        absolute cross-run coordinate ``cross``."""
        return (start + sign * s, cross) if along_x else (cross, start + sign * s)

    stringer_depth = cross_section("2x12").depth_m
    flight_len = tread * lower_treads  # the longer (lower) flight bounds the flight zone
    lower_landing_z = z0 + riser * (lower_treads + 1)
    upper_landing_z = lower_landing_z + riser
    arrival = z0 + riser * risers
    out: list[FramedMember] = []
    # Stringers, raked: at the springing end the top meets the first tread's top; at the
    # far end it meets the flight's bearing (lower flight → the lower landing, upper
    # flight → the arrival deck). The subfloor clip clamps the springing dip.
    for prefix, lane_lo, s_lo, s_hi, spring_z, bear_z, count in (
        ("lower", lane0, 0.0, flight_len, z0, lower_landing_z, lower_treads),
        ("upper", lane1, flight_len, flight_len - tread * upper_treads,
         upper_landing_z, arrival, upper_treads),
    ):
        if not count:
            continue
        spring_top = spring_z + riser + _TREAD_THICKNESS_M
        for index, cross in enumerate((lane_lo, lane_lo + width)):
            out.append(FramedMember(
                stair.uid, f"stringer-{prefix}-{index}", "stringer", "2x12",
                at(s_lo, cross), at(s_hi, cross),
                spring_top - stringer_depth, spring_top,
                math.hypot(tread * count, bear_z - spring_z),
                z0_end_m=bear_z - stringer_depth, z1_end_m=bear_z))
    for index in range(lower_treads):
        z = z0 + riser * (index + 1)
        out.append(FramedMember(stair.uid, f"tread-lower-{index:03d}", "tread", "2x12",
                                at(tread * index, lane0), at(tread * index, lane0 + width),
                                z, z + _TREAD_THICKNESS_M, width))
    # Upper flight climbs back toward the start edge; its first tread leaves the upper
    # landing, and its top tread ends one riser below the arrival deck.
    for index in range(upper_treads):
        z = z0 + riser * (lower_treads + 3 + index)
        s = flight_len - tread * (index + 1)
        out.append(FramedMember(stair.uid, f"tread-upper-{index:03d}", "tread", "2x12",
                                at(s, lane1), at(s, lane1 + width),
                                z, z + _TREAD_THICKNESS_M, width))
    # Two real half-width landing platforms in the landing zone beyond the flight ends.
    out.extend(_landing_platform(stair, "lower", at, flight_len, landing_depth_m,
                                 lane0, width, lower_landing_z))
    out.extend(_landing_platform(stair, "upper", at, flight_len, landing_depth_m,
                                 lane1, width, upper_landing_z))
    # Well partition between the up and down flights: generated stud framing (not an
    # authored Wall) on the lane boundary, bearing on the subfloor the stair springs
    # from and rising to the arrival deck — never past the subfloor into the foundation
    # (the flight-clip guard is the backstop). Both flights' inner stringers bear on it.
    # It stops at the flight end; the landing platforms take over beyond. The 0.20 m
    # inset holds its ends off the opening perimeter framing.
    inset = 0.20
    lo_s, hi_s = inset, flight_len - inset
    if hi_s > lo_s:
        plate = 0.0381  # a 2x4 plate laid flat
        pa, pb = at(lo_s, lane1), at(hi_s, lane1)
        out.append(FramedMember(stair.uid, "well-partition-plate-bottom", "partition",
                                "2x4", pa, pb, z0, z0 + plate, hi_s - lo_s))
        out.append(FramedMember(stair.uid, "well-partition-plate-top", "partition",
                                "2x4", pa, pb, arrival - plate, arrival, hi_s - lo_s))
        orient = (float(sign), 0.0) if along_x else (0.0, float(sign))
        for index, offset in enumerate(_grid_positions(hi_s - lo_s, _FRAMING_SPACING_M)):
            point = at(lo_s + offset, lane1)
            out.append(FramedMember(stair.uid, f"well-partition-stud-{index:03d}",
                                    "partition", "2x4", point, point,
                                    z0 + plate, arrival - plate,
                                    arrival - z0 - 2 * plate, orient=orient))
    return tuple(out)


def _landing_platform(stair: Stair, name: str, at, s0: float, depth: float,
                      lane_lo: float, width: float,
                      landing_z: float) -> list[FramedMember]:
    """One half-width landing platform: full-width deck + joists + perimeter rims.

    The deck is a single ``deck WxT`` member (a parseable profile, so it renders at the
    platform's true width instead of a 1.5" strip). Joists run across the lane on the
    deduplicated 16" grid — edge joists land exactly at 0 and ``depth`` — and the two
    rims cap the joist ends along the run direction.
    """
    joist_depth = cross_section(_LANDING_JOIST_PROFILE).depth_m
    z_top, z_bot = landing_z, landing_z - joist_depth
    mid = lane_lo + width / 2.0
    out = [FramedMember(stair.uid, f"landing-{name}", "landing",
                        f"deck {width / 0.0254:g}x1.5",
                        at(s0, mid), at(s0 + depth, mid),
                        landing_z, landing_z + _TREAD_THICKNESS_M, depth)]
    for index, offset in enumerate(_grid_positions(depth, _FRAMING_SPACING_M)):
        out.append(FramedMember(stair.uid, f"landing-joist-{name}-{index:03d}", "landing",
                                _LANDING_JOIST_PROFILE, at(s0 + offset, lane_lo),
                                at(s0 + offset, lane_lo + width), z_bot, z_top, width))
    for index, cross in enumerate((lane_lo, lane_lo + width)):
        out.append(FramedMember(stair.uid, f"landing-rim-{name}-{index}", "landing",
                                _LANDING_JOIST_PROFILE, at(s0, cross),
                                at(s0 + depth, cross), z_bot, z_top, depth))
    return out


def _winder_stair_members(stair: Stair, minx: float, miny: float, z0: float,
                          risers: int, riser: float, tread: float) -> tuple[FramedMember, ...]:
    """Generate a lower quarter-turn with consistently fanned winder treads.

    ``start`` is the lower outside corner of the winder square.  The straight flight leaves
    that square in ``run_direction``; ``run_reversed`` selects west/south rather than the
    conventional east/north direction. Each tread edge shares the inside corner and fans
    across the outside of the turn, preventing the opposed-diagonal geometry two winders
    produced.
    """
    start_x, start_y = stair.start.xy_m if stair.start is not None else (minx, miny)
    width = stair.width.meters
    straight_treads = risers - 1 - stair.winder_count
    step_z = lambda index: z0 + riser * (index + 1)
    out: list[FramedMember] = []
    sign = -1 if stair.run_reversed else 1
    turn_sign = 1 if stair.turn_direction != "right" else -1
    along_x = stair.run_direction == "x"
    # One parametrization for all four sign/turn_sign combinations: `a` runs along the
    # ascent (the straight flight's direction), `b` across it toward the turn. The turn
    # square's corners are then P(0,0) (the entering outer corner, == ``start``),
    # P(width,0) (the inside corner / newel), P(0,width) and P(width,width).
    run_u = (sign, 0.0) if along_x else (0.0, sign)
    cross_u = (0.0, turn_sign) if along_x else (turn_sign, 0.0)

    def offset(point: tuple[float, float], a: float = 0.0,
               b: float = 0.0) -> tuple[float, float]:
        """``point`` moved ``a`` metres along the run and ``b`` metres across it."""
        return (point[0] + run_u[0] * a + cross_u[0] * b,
                point[1] + run_u[1] * a + cross_u[1] * b)

    def P(a: float, b: float) -> tuple[float, float]:
        """Plan point ``a`` metres along the run, ``b`` metres across it, from ``start``."""
        return offset((start_x, start_y), a, b)

    # The straight flight springs off the top of the winder turn; its raked stringers run
    # from one riser above that springing up to the arrival deck.
    stringer_depth = cross_section("2x12").depth_m
    spring_top = z0 + riser * stair.winder_count + riser + 0.0381
    arrival = z0 + riser * risers
    foot = P(0.0, 0.0)  # the entering outer corner of the turn square (== ``start``)
    inside = P(width, 0.0)  # the turn's inside corner: where the straight flight springs
    outer_corner = P(0.0, width)  # the outer corner the turn sweeps around
    turn = P(width, width)  # the departing corner, where the outer stringer takes over
    for index, cross in enumerate((0.0, width)):
        out.append(FramedMember(stair.uid, f"stringer-{index}", "stringer", "2x12",
                                offset(inside, 0.0, cross),
                                offset(inside, tread * straight_treads, cross),
                                spring_top - stringer_depth, spring_top,
                                math.hypot(tread * straight_treads, riser * risers),
                                z0_end_m=arrival - stringer_depth, z1_end_m=arrival))
    for index in range(stair.winder_count):
        # ``winder_count + 1`` because ``fraction == 1`` — the departing edge of the turn
        # square — belongs to the straight flight's first tread. Dividing by the winder
        # count alone put the top winder exactly on top of ``tread-000``: a riser with
        # zero going. It also makes the carriage rake close exactly on the springing.
        fraction = (index + 1) / (stair.winder_count + 1)
        # First half follows the entering outside edge, second half the departing edge.
        nosing = (P(0.0, width * fraction * 2) if fraction <= 0.5
                  else P(width * (fraction * 2 - 1), width))
        a, b = inside, nosing
        out.append(FramedMember(stair.uid, f"winder-{index:03d}", "winder", "tapered tread",
                                a, b, step_z(index), step_z(index) + 0.0381,
                                math.hypot(b[0] - a[0], b[1] - a[1])))
    for index in range(straight_treads):
        out.append(FramedMember(stair.uid, f"tread-{index:03d}", "tread", "2x12",
                                offset(inside, tread * index, 0.0),
                                offset(inside, tread * index, width),
                                step_z(index + stair.winder_count),
                                step_z(index + stair.winder_count) + 0.0381,
                                width))
    out.extend(_winder_turn_framing(stair, z0, riser, width, spring_top, stringer_depth,
                                    foot, inside, outer_corner, turn,
                                    (float(run_u[0]), float(run_u[1]))))
    return tuple(out)


def _winder_turn_framing(stair: Stair, z0: float, riser: float, width: float,
                         spring_top: float, stringer_depth: float,
                         foot: tuple[float, float], inside: tuple[float, float],
                         outer_corner: tuple[float, float], turn: tuple[float, float],
                         orient: tuple[float, float]) -> list[FramedMember]:
    """Frame the quarter-turn itself: newel, two raked carriages, and the turn header.

    Without this the turn is a mathematical fiction — every winder's narrow end converges
    on a bare point and the straight flight springs off nothing.

    - **The newel** carries every winder narrow end, so it must reach the *highest*
      winder's nosing, which is above the header; it therefore runs past the header up to
      the springing and picks up ``stringer-0`` too. That is how a winder newel works.
    - **The carriages** are the outer stringer carried around the turn: one straight rake
      through every winder nosing, ``top(f) = z0 + riser*(winder_count+1)*f + tread``.
      ``top(1) == spring_top``, so the departing carriage runs continuously into
      ``stringer-1`` and must end precisely at ``turn`` — an overshoot would read as a
      real interference against it. They are category ``stringer``, so the bearing pass
      picks them up against a flanking wall for free.
    - **The header** tops out at the springing's underside — exactly the stringers'
      ``z0_m`` at ``p0`` — so the flight seats on it with zero overlap. Its ends are
      carried by the newel at ``inside`` and by a second newel at ``turn``.
    """

    def carriage_top(fraction: float) -> float:
        return z0 + riser * (stair.winder_count + 1) * fraction + _TREAD_THICKNESS_M

    header_top = spring_top - stringer_depth
    out = [
        FramedMember(stair.uid, "newel-000", "newel", "4x4", inside, inside,
                     z0, spring_top, spring_top - z0, orient=orient),
        FramedMember(stair.uid, "newel-001", "newel", "4x4", turn, turn,
                     z0, header_top, header_top - z0, orient=orient),
    ]
    for index, (a, b, f0, f1) in enumerate(((foot, outer_corner, 0.0, 0.5),
                                            (outer_corner, turn, 0.5, 1.0))):
        top_a, top_b = carriage_top(f0), carriage_top(f1)
        out.append(FramedMember(
            stair.uid, f"winder-carriage-{index}", "stringer", "2x12", a, b,
            top_a - stringer_depth, top_a, math.hypot(width, top_b - top_a),
            z0_end_m=top_b - stringer_depth, z1_end_m=top_b))
    out.append(FramedMember(stair.uid, "winder-header", "header", "2-2x12", inside, turn,
                            header_top - cross_section("2-2x12").depth_m, header_top,
                            width))
    return out


def _clip_stair_to_subfloor(members: tuple[FramedMember, ...],
                            subfloor: float) -> tuple[FramedMember, ...]:
    """Clamp generated stair framing to the subfloor the flight springs from.

    The U-stair well partition (and any carriage member) bears on the first framed deck
    and must never drop into the foundation below it. This is the clip guard the audit
    called for; for a flight already sized off that deck it is a no-op backstop.
    """
    out: list[FramedMember] = []
    for member in members:
        z0 = max(member.z0_m, subfloor)
        z1 = max(member.z1_m, subfloor)
        z0e = None if member.z0_end_m is None else max(member.z0_end_m, subfloor)
        z1e = None if member.z1_end_m is None else max(member.z1_end_m, subfloor)
        if (z0, z1, z0e, z1e) == (member.z0_m, member.z1_m, member.z0_end_m, member.z1_end_m):
            out.append(member)
        else:
            out.append(replace(member, z0_m=z0, z1_m=z1, z0_end_m=z0e, z1_end_m=z1e))
    return tuple(out)


def _wall_run_overlap(wall, p0: tuple[float, float], p1: tuple[float, float]
                      ) -> tuple[float, float, tuple[float, float]] | None:
    """Geometry of an axis-aligned member p0→p1 lying along ``wall``'s axis.

    Returns ``(offset, shared_run, (lo, hi))`` — the perpendicular distance from the
    member to the wall axis, the length they share, and the shared interval in the run
    coordinate — or ``None`` when the two are not colinear-parallel at all.
    """
    (wx0, wy0), (wx1, wy1) = wall.axis
    if abs(wx1 - wx0) < 1e-6 and abs(p1[0] - p0[0]) < 1e-6:  # both run in y
        offset = abs(p0[0] - wx0)
        lo, hi = sorted((p0[1], p1[1]))
        wlo, whi = sorted((wy0, wy1))
    elif abs(wy1 - wy0) < 1e-6 and abs(p1[1] - p0[1]) < 1e-6:  # both run in x
        offset = abs(p0[1] - wy0)
        lo, hi = sorted((p0[0], p1[0]))
        wlo, whi = sorted((wx0, wx1))
    else:
        return None
    shared_lo, shared_hi = max(lo, wlo), min(hi, whi)
    return offset, shared_hi - shared_lo, (shared_lo, shared_hi)


def _best_host_wall(model: ResolvedModel, stair: Stair, p0: tuple[float, float],
                    p1: tuple[float, float]):
    """The wall a stair member p0→p1 bears on, or ``(None, None)``.

    Three independent gates, all required:

    1. **Bearing intent** — the wall is foundation concrete, is authored
       ``StructuralRole.BEARING``, or is named in the stair's ``bearing_refs``. A
       non-bearing partition beside a flight carries nothing.
    2. **Geometry** — the member sits within half the wall's own depth (plus a tread
       board) of its axis. An axis is a *centreline*, so this is the wall's real reach;
       the flat 0.20 m it replaces let a 4.75" partition 4" away read as a host.
    3. **Shared run** — they overlap by more than ``_MIN_SHARED_RUN_M``.

    Survivors rank by foundation first (concrete beats framing under the same member),
    then by the longest shared run, then by the closest axis — the old first-match-wins
    ``next()`` picked whichever wall happened to be declared first, which on catlin meant
    a 4" clip of ``W-M-C4B`` beat 5'-8" of ``W-M-C5``.

    Returns ``(wall, shared_interval)`` so the caller can tell which member endpoints the
    host actually reaches.
    """
    ranked = []
    for wall in model.walls:
        if wall.storey != stair.from_storey:
            continue
        if not (wall.is_foundation or wall.tag in stair.bearing_refs
                or _authored_is_bearing(model, wall.tag)):
            continue
        overlap = _wall_run_overlap(wall, p0, p1)
        if overlap is None:
            continue
        offset, shared_run, interval = overlap
        if offset > wall.thickness_m / 2 + _TREAD_THICKNESS_M:
            continue
        if shared_run <= _MIN_SHARED_RUN_M:
            continue
        ranked.append((not wall.is_foundation, -shared_run, offset, wall.tag, wall, interval))
    if not ranked:
        return None, None
    best = min(ranked, key=lambda entry: entry[:4])
    return best[4], best[5]


def _authored_is_bearing(model: ResolvedModel, tag: str) -> bool:
    """``ResolvedWall`` drops the authored structural role, so read it off the plan."""
    authored = model.plan.by_tag(tag)
    return getattr(authored, "structural_role", None) is StructuralRole.BEARING


def _bear_stair_on_walls(model: ResolvedModel, stair: Stair,
                         members: tuple[FramedMember, ...],
                         subfloor: float) -> tuple[FramedMember, ...]:
    """Give the flight a resolvable load path against the walls it runs beside.

    A stair does not float: its outer stringers and its landing rims run against the
    walls flanking the well, and whatever they miss has to be posted down to the deck
    the flight springs from. Two host kinds, deliberately different:

    - **Foundation concrete** — the stringer/rim is carried on a wall-mounted
      (joist-hanger-style) ledger let into the pour. Annotated
      ``concrete-wall-hanger:{tag}`` *and* given a hanger band as connector geometry, so
      the bearing reads structurally. The band tracks the raked stringer top
      (``z1_m``/``z1_end_m``), so a lower-flight hanger bears at the landing and an
      upper-flight hanger at the arrival deck — never at ``max(z0, z1)`` of a full prism.
    - **Framed wall** — annotated ``framed-wall-ledger:{tag}`` and nothing else. A wall
      ``axis`` is its *centreline*, so a band drawn on it would be geometry invented
      inside the stud cavity; the ledger the framer actually installs waits on insetting
      stair members to the host's finished face (see plans/TODO.md D3).

    Any landing corner no host wall reaches gets a vertical 4x4 post to the subfloor.
    """
    hanger_depth = 0.2032  # 8" ledger band

    def corner_key(point: tuple[float, float]) -> tuple[float, float]:
        return (round(point[0], 4), round(point[1], 4))

    def covered_ends(member: FramedMember,
                     interval: tuple[float, float]) -> list[tuple[float, float]]:
        """The member's endpoints the host wall's shared run actually reaches.

        ``interval`` is in the member's run axis — y for a member running in y, x for one
        running in x — matching what ``_wall_run_overlap`` measured.
        """
        axis = 1 if abs(member.p1[0] - member.p0[0]) < 1e-6 else 0
        return [point for point in (member.p0, member.p1)
                if interval[0] - 1e-6 <= point[axis] <= interval[1] + 1e-6]

    out: list[FramedMember] = []
    rims_by_platform: dict[str, list[FramedMember]] = {}
    supported_corners: set[tuple[float, float]] = set()
    for member in members:
        if member.category == "landing" and member.child_key.startswith("landing-rim-"):
            rims_by_platform.setdefault(member.child_key.rsplit("-", 1)[0],
                                        []).append(member)
        bearable = (member.category == "stringer"
                    or (member.category == "landing"
                        and (member.child_key.startswith("landing-rim-")
                             or member.child_key.startswith("landing-joist-"))))
        if bearable and member.p0 != member.p1:
            host, interval = _best_host_wall(model, stair, member.p0, member.p1)
            if host is not None and not host.is_foundation:
                out.append(replace(member, connection=f"framed-wall-ledger:{host.tag}"))
                if member.category == "landing":
                    # Only the endpoints the wall actually runs past are carried; a host
                    # that overlaps half a rim leaves the far corner needing a post.
                    supported_corners.update(
                        corner_key(point) for point in covered_ends(member, interval))
                continue
            if host is not None:
                tag = f"concrete-wall-hanger:{host.tag}"
                out.append(replace(member, connection=tag))
                if member.category == "stringer":
                    top_p0 = member.z1_m
                    top_p1 = member.z1_m if member.z1_end_m is None else member.z1_end_m
                    out.append(FramedMember(
                        stair.uid, f"hanger-{host.tag}-{member.child_key}", "hanger",
                        "hanger", member.p0, member.p1,
                        max(subfloor, top_p0 - hanger_depth), top_p0, member.length_m,
                        z0_end_m=max(subfloor, top_p1 - hanger_depth), z1_end_m=top_p1,
                        connection=tag))
                else:
                    out.append(FramedMember(
                        stair.uid, f"hanger-{host.tag}-{member.child_key}", "hanger",
                        "hanger", member.p0, member.p1,
                        max(subfloor, member.z1_m - hanger_depth), member.z1_m,
                        member.length_m, connection=tag))
                    supported_corners.update(
                        corner_key(point) for point in covered_ends(member, interval))
                continue
        out.append(member)
    # Any platform corner not on a ledgered edge bears on a 4x4 post to the subfloor.
    # The two rims' endpoints are exactly the platform's four corners; the corner shared
    # by both half-width platforms gets one post, sized to the higher platform.
    posts: dict[tuple[float, float], float] = {}
    for rims in rims_by_platform.values():
        z_top = min(rim.z0_m for rim in rims)  # underside of the platform framing
        for rim in rims:
            for point in (rim.p0, rim.p1):
                key = corner_key(point)
                if key in supported_corners:
                    continue
                posts[key] = max(posts.get(key, z_top), z_top)
    orient = (1.0, 0.0) if stair.run_direction == "x" else (0.0, 1.0)
    for index, (key, z_top) in enumerate(sorted(posts.items())):
        if z_top <= subfloor + 1e-9:
            continue
        out.append(FramedMember(stair.uid, f"landing-post-{index:03d}", "landing", "4x4",
                                key, key, subfloor, z_top, z_top - subfloor,
                                orient=orient))
    return tuple(out)


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
        # (longer) lower flight takes the odd extra one.
        lower_treads = (max(0, risers - 3) + 1) // 2
        required_run = landing_depth_m + tread * lower_treads
        if stair.run_direction == "x":
            return (2 * stair.width.meters <= maxy - miny + 1e-9
                    and required_run <= maxx - minx + 1e-9)
        return (2 * stair.width.meters <= maxx - minx + 1e-9
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
