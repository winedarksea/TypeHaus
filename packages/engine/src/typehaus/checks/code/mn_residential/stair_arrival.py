"""R311.7.6 at the head of a flight: is there a FLOOR there, or the hole it is cut in?

Its own module, not a third rule in ``stairs.py`` — that file is already 667 lines against
``AGENTS.md``'s 500 — and the separation is real: every rule there measures a DIMENSION of
the stairway, and this one asks a question about the deck beside it.

The gap it closes is stated in :func:`stair_arrival_floor`. In short: the two R311.7.5.1
rules between them grade a flight's interior and its two end RISERS, and both read the
arrival deck through the well the flight is cut in — so a flight that stops a going short of
its own opening edge arrives at exactly the right height over open air, and passes.
"""

from __future__ import annotations

import math

from shapely.geometry import Point, Polygon

from typehaus.checks.code.mn_residential._common import _fail, _pass, _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, not_applicable, passed

#: How far past the top nosing, as a fraction of a going, the first footfall off a flight
#: lands. Half a going is inside the arrival tread's own depth, so the probe is never a
#: question about the *next* surface along; and it is far enough off the opening ring that
#: containment is never decided on a boundary coincidence.
_ARRIVAL_PROBE_GOINGS = 0.5


@check(Tier.CODE, "code.R311_7_6_stair_arrival_floor")
def stair_arrival_floor(ctx: CheckContext) -> list[Finding]:
    """R311.7.6: there is a floor, not a hole, where the top nosing puts a foot down.

    ``code.R311_7_5_1_stair_end_risers`` asks how far the last step is; this asks whether
    there is anything to step onto at all. They are not the same question and the first
    cannot answer the second: it compares *elevations*, reading the arrival deck through
    ``deck_owning_opening`` — the deck the well is cut in — whatever the flight's plan
    position inside that well happens to be. A flight that stops a going short of its own
    opening edge arrives at the right height over open air, and passes.

    That is not hypothetical. It is what ``resolve/stairs/u_split.py`` built until
    2026-09-15 on any U-stair with an odd tread split: the upper flight was laid out
    backwards from the *lower* flight's line, so ST-M2S's head stood 10" out into
    ``FO-S-STAIR`` — a 10" x 3'-6 3/8" strip of open floor opening across the whole width of
    the stair. Nothing in the engine saw it. See ``notes/u_stair_split_landing.md``.

    So: step half a going off the top nosing along the walking route's own direction, and
    ask what is there. Inside the stair's own floor opening with nothing standing at the
    arrival elevation is a **FAIL**. Nothing found anywhere is UNKNOWN, not a pass — a floor
    nobody drew is exactly the ambiguity the end-riser rule already refuses to guess at
    (ST-SG-PORCH heads onto 12" of wall top that is deliberately not modelled). A stair that
    perforates no deck has no opening edge to fall short of, and that absence is positive:
    NOT_APPLICABLE.
    """
    from typehaus.resolve.stairs.walkline import stair_walk_stations
    from typehaus.resolve.walking_surface import surfaces_at as _surfaces_at

    cid, code = "code.R311_7_6_stair_arrival_floor", "R311.7.6"
    if not ctx.model.stairs:
        return [_unknown(cid, "no resolved stairs", (), code)]
    out: list[Finding] = []
    for stair in ctx.model.stairs:
        route = stair_walk_stations(stair)
        if len(route) < 2:
            out.append(not_applicable(cid, f"{stair.tag} resolves fewer than two walking "
                                      "stations, so it has no arrival nosing",
                                      (stair.tag,), code))
            continue
        opening_tag = getattr(ctx.plan.by_tag(stair.tag), "floor_opening", None)
        opening = ctx.plan.by_tag(opening_tag) if opening_tag else None
        ring = [point.xy_m for point in getattr(opening, "outline", ())]
        if len(ring) < 3:
            out.append(not_applicable(cid, f"{stair.tag} perforates no floor opening, so "
                                      "its head has no opening edge to fall short of",
                                      (stair.tag,), code))
            continue
        (ax, ay), (bx, by), arrival_z = route[-1]
        (px, py), (qx, qy), _ = route[-2]
        nose = ((ax + bx) / 2.0, (ay + by) / 2.0)
        back = ((px + qx) / 2.0, (py + qy) / 2.0)
        dx, dy = nose[0] - back[0], nose[1] - back[1]
        span = math.hypot(dx, dy)
        if span < 1e-9:
            out.append(_unknown(cid, f"{stair.tag}'s arrival station has no travel "
                                "direction to step off along", (stair.tag,), code))
            continue
        step = _ARRIVAL_PROBE_GOINGS * stair.going_depth_m
        probe = (nose[0] + dx / span * step, nose[1] + dy / span * step)
        band = stair.riser_height_m / 2.0
        surfaces = _surfaces_at(ctx.model, probe)
        standing = [s for s in surfaces
                    if abs((s.surface_m if s.surface_m is not None else s.deck_top_m)
                           - arrival_z) <= band]
        inside = Polygon(ring).contains(Point(*probe))
        if standing:
            out.append(_pass(cid, f"{stair.tag} steps off its top nosing onto "
                             f"{standing[0].deck_tag}", code))
        elif inside:
            short = math.hypot(*_nearest_edge_offset(ring, nose))
            out.append(_fail(cid, f"{stair.tag}'s top nosing stands {short / .0254:.2f}\" "
                             f"inside {opening_tag} with no surface at the arrival "
                             "elevation — the flight ends over the hole it is cut in; "
                             "R311.7.6 requires a floor or landing at the top of a "
                             "stairway", (stair.tag, opening_tag), code))
        else:
            out.append(_unknown(cid, f"{stair.tag} steps off its top nosing outside "
                                f"{opening_tag} onto no modelled surface, so the floor it "
                                "arrives at is undrawn", (stair.tag,), code))
    return out


def _nearest_edge_offset(ring: list[tuple[float, float]],
                         point: tuple[float, float]) -> tuple[float, float]:
    """Vector from ``point`` to the nearest point on ``ring``'s boundary — how far short."""
    best = (float("inf"), (0.0, 0.0))
    px, py = point
    for (x0, y0), (x1, y1) in zip(ring, [*ring[1:], ring[0]], strict=True):
        dx, dy = x1 - x0, y1 - y0
        run2 = dx * dx + dy * dy
        t = 0.0 if run2 < 1e-18 else max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy)
                                                 / run2))
        cx, cy = x0 + dx * t, y0 + dy * t
        gap = math.hypot(px - cx, py - cy)
        if gap < best[0]:
            best = (gap, (cx - px, cy - py))
    return best[1]


#: R311.7.6: a landing at the top of each stairway, at least as wide as the stairway and 36"
#: in the direction of travel.
_HEAD_LANDING_M = 36 * 0.0254
_SAMPLE_STEP_M = 3 * 0.0254
_EDGE_INSET_M = 1 * 0.0254


@check(Tier.CODE, "code.R311_7_6_stair_head_landing")
def stair_head_landing(ctx: CheckContext) -> list[Finding]:
    """R311.7.6 at the head: 36" of floor past the top nosing, the full stair width.

    ``stair_arrival_floor`` asks whether a foot lands on something; this asks whether the
    whole landing is there — a floor at the arrival elevation under every sample of the
    36" x width rectangle past the top nosing, and no wall standing in it. A header moved
    back to seat the head riser board eats into exactly this rectangle. Scope is the same
    as the sibling rule: a flight through a floor opening.
    """
    from typehaus.resolve.stairs.walkline import stair_walk_stations
    from typehaus.resolve.walking_surface import surfaces_at as _surfaces_at

    cid, code = "code.R311_7_6_stair_head_landing", "R311.7.6"
    if not ctx.model.stairs:
        return [_unknown(cid, "no resolved stairs", (), code)]
    out: list[Finding] = []
    for stair in ctx.model.stairs:
        tags = (stair.tag,)
        route = stair_walk_stations(stair)
        if not getattr(ctx.plan.by_tag(stair.tag), "floor_opening", None) or len(route) < 2:
            out.append(not_applicable(cid, f"{stair.tag} perforates no floor opening, so "
                                      "its head is not a floor landing", tags, code))
            continue
        (ax, ay), (bx, by), arrival_z = route[-1]
        (px, py), (qx, qy), _ = route[-2]
        dx = (ax + bx - px - qx) / 2.0
        dy = (ay + by - py - qy) / 2.0
        span = math.hypot(dx, dy)
        width = math.hypot(bx - ax, by - ay)
        if span < 1e-9 or width < 1e-9:
            out.append(_unknown(cid, f"{stair.tag}'s arrival station has no direction",
                                tags, code))
            continue
        ux, uy = dx / span, dy / span
        cx, cy = (bx - ax) / width, (by - ay) / width
        rect = Polygon([(ax, ay), (bx, by), (bx + ux * _HEAD_LANDING_M,
                                             by + uy * _HEAD_LANDING_M),
                        (ax + ux * _HEAD_LANDING_M, ay + uy * _HEAD_LANDING_M)])
        band = stair.riser_height_m / 2.0
        missing = []
        depth = _SAMPLE_STEP_M
        while depth <= _HEAD_LANDING_M + 1e-9:
            for across in (_EDGE_INSET_M, width / 2.0, width - _EDGE_INSET_M):
                point = (ax + cx * across + ux * depth, ay + cy * across + uy * depth)
                if not any(abs((s.surface_m if s.surface_m is not None else s.deck_top_m)
                               - arrival_z) <= band for s in _surfaces_at(ctx.model, point)):
                    missing.append(depth)
            depth += _SAMPLE_STEP_M
        inside = rect.buffer(-_EDGE_INSET_M)
        walls = sorted(wall.tag for wall in ctx.model.walls
                       if wall.z0_m < arrival_z + 0.05 < wall.z1_m
                       and _wall_polygon(wall) is not None
                       and _wall_polygon(wall).intersects(inside))
        if walls:
            out.append(_fail(cid, f"{stair.tag}'s head landing is not 36\" deep x "
                             f"{width / .0254:.2f}\" clear: {', '.join(walls)} stands in it",
                             (stair.tag, *walls), code))
        elif missing:
            out.append(_fail(cid, f"{stair.tag}'s head landing has no floor at the arrival "
                             f"elevation {min(missing) / .0254:.1f}\" past the top nosing, "
                             "inside R311.7.6's 36\"", tags, code))
        else:
            out.append(_pass(cid, f"{stair.tag} heads onto 36\" x {width / .0254:.2f}\" of "
                             "clear floor past its top nosing", code))
    return out


def _wall_polygon(wall) -> Polygon | None:
    points = [point for layer in wall.layers for point in layer.polygon]
    return Polygon(points).convex_hull if len(points) >= 3 else None


#: A door "at the head" stands within a going past the top nosing plus its own wall's depth.
_HEAD_DOOR_REACH_GOINGS = 1.0
#: Its host wall crosses the walking line: within 45 degrees of square to the travel.
_CROSSING_COS = math.cos(math.radians(45))
#: Plan area of a sweep over the flight that counts as swinging over it (1 sq in).
_SWEEP_TOL_M2 = 0.0254 ** 2


@check(Tier.CODE, "code.R311_7_6_door_at_stair_head")
def door_at_stair_head(ctx: CheckContext) -> list[Finding]:
    """R311.7.6 exception: no top landing where a flight rises to a door that swings clear.

    "A floor or landing is not required at the top of an interior flight of stairs,
    including stairs in an enclosed garage, provided that a door does not swing over the
    stairs" (IRC 2018, adopted by MN 1309). The two rules above grade a flight through a
    floor opening; one that rises inside a storey straight to a door threshold — catlin's
    ST-G-SERVICE since 2026-10-13 — leaves both N/A, and this is the question it raises.

    Scope: a flight with no floor opening and a door at its head — threshold within one
    riser of the arrival elevation, in a wall crossing the walking line, overlapping the
    flight's width, within a going past the top nosing plus the wall's depth. PASS: the
    flight stands in an enclosed room and the leaf's ``swing_clearance`` misses its plan
    footprint. FAIL: the leaf swings over the stairs. UNKNOWN: no swing is resolved, or the
    flight is not interior and the exception does not reach it. N/A: no door at the head.
    """
    from shapely.geometry import Polygon

    from typehaus.resolve.room_lookup import room_owning
    from typehaus.resolve.stairs.walkline import stair_walk_stations

    cid, code = "code.R311_7_6_door_at_stair_head", "R311.7.6"
    if not ctx.model.stairs:
        return [_unknown(cid, "no resolved stairs", (), code)]
    out: list[Finding] = []
    for stair in ctx.model.stairs:
        tags = (stair.tag,)
        route = stair_walk_stations(stair)
        if getattr(ctx.plan.by_tag(stair.tag), "floor_opening", None) or len(route) < 2:
            out.append(not_applicable(cid, f"{stair.tag} heads onto a floor through its "
                                      "opening (code.R311_7_6_stair_head_landing)",
                                      tags, code))
            continue
        door = _door_at_head(ctx.model, stair, route)
        if door is None:
            out.append(not_applicable(cid, f"{stair.tag} has no door at its head", tags,
                                      code))
            continue
        tags = (stair.tag, door.tag)
        flight = Polygon(stair.outline)
        if len(door.swing_clearance) < 3:
            out.append(_unknown(cid, f"{door.tag} stands at {stair.tag}'s head with no "
                                "resolved swing, so whether it swings over the stairs is "
                                "unknown", tags, code))
            continue
        over = Polygon(door.swing_clearance).intersection(flight).area
        if over > _SWEEP_TOL_M2:
            out.append(_fail(cid, f"{door.tag}'s leaf swings over {stair.tag} "
                             f"({over / 0.0254 ** 2:.0f} sq in of its sweep over the flight) "
                             "and the flight has no top landing; R311.7.6's exception holds "
                             "only where a door does not swing over the stairs", tags, code))
            continue
        cx, cy = flight.representative_point().coords[0]
        room = room_owning(ctx.model, stair.storey, (cx, cy))
        if room is None:
            out.append(_unknown(cid, f"{stair.tag} rises to {door.tag} with no top landing, "
                                "but stands in no room: the exception covers an INTERIOR "
                                "flight", tags, code))
            continue
        out.append(passed(cid, f"{stair.tag} rises to {door.tag}'s threshold with no top "
                          f"landing, inside {room.tag}, and {door.tag}'s leaf swings clear "
                          "of the stairs (R311.7.6 exception)", tags, code=code))
    return out


def _door_at_head(model, stair, route):
    """The door whose threshold the flight's top nosing reaches, or ``None``."""
    (ax, ay), (bx, by), arrival_z = route[-1]
    (px, py), (qx, qy), _ = route[-2]
    nose = ((ax + bx) / 2.0, (ay + by) / 2.0)
    dx, dy = nose[0] - (px + qx) / 2.0, nose[1] - (py + qy) / 2.0
    span = math.hypot(dx, dy)
    width = math.hypot(bx - ax, by - ay)
    if span < 1e-9 or width < 1e-9:
        return None
    ux, uy = dx / span, dy / span
    best = None
    for opening in model.openings:
        wall = model.wall(opening.host_wall) if opening.is_door else None
        if wall is None or getattr(wall, "axis", None) is None:
            continue
        (sx, sy), (ex, ey) = wall.axis
        run = math.hypot(ex - sx, ey - sy) or 1.0
        tx, ty = (ex - sx) / run, (ey - sy) / run
        if abs(tx * ux + ty * uy) > _CROSSING_COS:
            continue  # the wall runs with the walking line; nobody walks through it
        threshold = getattr(wall, "base_ref_z_m", wall.z0_m) + opening.sill_m
        if abs(threshold - arrival_z) > stair.riser_height_m:
            continue
        cx, cy = sx + tx * opening.center_along_m, sy + ty * opening.center_along_m
        along = (cx - nose[0]) * ux + (cy - nose[1]) * uy
        lateral = abs((cx - nose[0]) * -uy + (cy - nose[1]) * ux)
        reach = _HEAD_DOOR_REACH_GOINGS * stair.going_depth_m + wall.thickness_m
        if (-1e-6 <= along <= reach and lateral < (width + opening.width_m) / 2.0
                and (best is None or along < best[0])):
            best = (along, opening)
    return None if best is None else best[1]
