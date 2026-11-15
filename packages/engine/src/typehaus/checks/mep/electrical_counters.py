"""NEC 210.52(C) wall countertop spaces and 210.52(C)(4), read off resolved countertops.

Graded rules (printed 2026 NEC, read 2026-11-13; paraphrased in docs/code-notes/nec-2026-paraphrase.md):

* (C)(1): a receptacle at each wall countertop space 12" or wider, none of its wall line more
  than 24", measured horizontally, from a receptacle in that space; none directly behind a
  range, counter-mounted cooking unit or sink; those and a refrigerator separate spaces.
* (C)(3): on or above, and not more than 20" above, the countertop.
* (C)(4): below the counter, none on adjacent walls within 24" of the base cabinets and none
  within 24" beneath the countertop; a drawer receptacle is excepted.
* (C)(1) Ex 2: where a required outlet cannot go in the Figure 210.52(C)(1) wall areas (behind
  a range, cooktop or sink), it may go as close as practicable, the count unchanged, each per
  (C)(3). The printed text names no window; the owner keeps reading glass at the counter as
  "cannot be installed" (2026-11-13), and the finding says it needs the AHJ's agreement.
  Only a stretch of 12" or more whose glass
  occupies the whole band a box could use (sill within a plate height of the top) qualifies;
  there the 24" reach is waived for the count rule and outlets beside the glass.

The wall line is the room's floor-line ring where a counter's back touches it, read as an
arc length so it turns inside corners. A counter's end face on a perpendicular wall (one
counter depth, <= ``_END_FACE_M``) is not wall line. Sinks and cooking units break it where
(C)(1) Ex 1 says no receptacle is needed behind them: under 12" off a straight run, 18" in a
corner.
"""

from __future__ import annotations

import math
from collections import defaultdict

from typehaus.checks._authoring import advisory
from typehaus.checks._authoring import not_applicable as _na
from typehaus.checks._authoring import passed as _pass
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.mep.electrical_wall_space import floor_line_ring
from typehaus.checks.registry import CheckContext
from typehaus.findings import Finding, Result
from typehaus.model.enums import Occupancy
from typehaus.model.nec import NEC, mark
from typehaus.resolve import room_perimeter
from typehaus.resolve.geometry import opening_center
from typehaus.resolve.intervals import Interval, merge, subtract
from typehaus.resolve.placeables import placed_xy

_IN = 0.0254
_REACH_M = 24 * _IN  # (C)(1)
_MIN_SPACE_M = 12 * _IN  # (C)(1)
_MAX_ABOVE_M = 20 * _IN  # (C)(3)
_BELOW_M = 24 * _IN  # (C)(4)
_TOL_M = 2 * _IN  # a counter's back sits within this of the wall face
_FACE_M = 2 * _IN  # a box on a wall or end panel projects about this far
_END_FACE_M = 30 * _IN
_PLATE_M = 4.5 * _IN  # a single-gang plate: glass nearer the top than this leaves no room
_BESIDE_M = 12 * _IN  # "as close as practicable": an outlet this near the glass edge
_KIND_ALL = {"receptacle", "gfci", "receptacle_240"}
_STRAIGHT_SETBACK_M = 12 * _IN  # (C)(1) Ex 1, a straight run
_CORNER_SETBACK_M = 18 * _IN  # (C)(1) Ex 1, a corner


def space_gaps(spaces: list[Interval], stations: list[float]) -> list[Interval]:
    """Wall-line stretches of ``spaces`` more than 24" from every receptacle station.

    Spaces under 12" are exempt, and a station serves only the space it stands in (the
    spaces are already cut at sinks and cooking units).
    """
    gaps: list[Interval] = []
    for lo, hi in spaces:
        if hi - lo < _MIN_SPACE_M:
            continue
        mine = [s for s in stations if lo - 1e-6 <= s <= hi + 1e-6]
        gaps += subtract(lo, hi, [(s - _REACH_M, s + _REACH_M) for s in mine])
    return gaps


def obstructed_gaps(space: Interval, stretches: list[Interval], stations: list[float]
                    ) -> tuple[list[Interval], list[str]]:
    """Ex 2 over one space: 24" gaps outside the glass stretches, and what Ex 2 still lacks.

    Needs (a) a count of ceil(length / 48") outlets, the number 24" reach would take, and (c)
    an outlet within 12" of each glass edge that has wall beyond it. Stations are already
    counted by (C)(3), so (b) holds for each.
    """
    lo, hi = space
    mine = [s for s in stations if lo - 1e-6 <= s <= hi + 1e-6]
    gaps = [g for a, b in space_gaps([space], stations) for g in subtract(a, b, stretches)]
    need = math.ceil(round((hi - lo) / (2 * _REACH_M), 9))
    lacks = ([f"{len(mine)} outlet(s) serve it, {need} needed at 24in reach"]
             if len(mine) < need else [])
    for a, b in stretches:
        if a > lo + 1e-6 and not any(a - _BESIDE_M <= s <= a for s in mine):
            lacks.append("no outlet on the wall within 12\" before the glass")
        if b < hi - 1e-6 and not any(b <= s <= b + _BESIDE_M for s in mine):
            lacks.append("no outlet on the wall within 12\" after the glass")
    return gaps, lacks


def _contacts(ring: list, area, perimeter: float) -> list[Interval]:
    """Arc intervals of ``ring`` lying within ``_TOL_M`` of ``area``, ends trimmed back."""
    from shapely.geometry import LineString, Point

    grown = area.buffer(_TOL_M)
    out: list[Interval] = []
    start = 0.0
    for index in range(len(ring)):
        a, b = ring[index], ring[(index + 1) % len(ring)]
        edge = LineString([a, b])
        length = edge.length
        hit = edge.intersection(grown)
        for part in getattr(hit, "geoms", [hit]):
            if part.is_empty or part.length < 1e-6:
                continue
            t = sorted(edge.project(Point(p)) for p in part.coords)
            lo = t[0] + (_TOL_M if t[0] > 1e-6 else 0.0)
            hi = t[-1] - (_TOL_M if t[-1] < length - 1e-6 else 0.0)
            if hi > lo:
                out.append((start + lo, start + hi))
        start += length
    return merge(out)


def _behind(ring: list, body) -> list[Interval]:
    """(C)(1) Ex 1: wall line behind a sink or cooking unit set under 12" off it, 18" in a
    corner (within 18" of two meeting edges). Each such edge loses the unit's projection."""
    from shapely.geometry import LineString, Point

    edges, start = [], 0.0
    for index in range(len(ring)):
        edge = LineString([ring[index], ring[(index + 1) % len(ring)]])
        edges.append((start, edge, body.distance(edge)))
        start += edge.length
    count = len(edges)
    corner = {i for i in range(count) for j in ((i - 1) % count, (i + 1) % count)
              if edges[i][2] <= _CORNER_SETBACK_M and edges[j][2] <= _CORNER_SETBACK_M}
    out: list[Interval] = []
    for index, (offset, edge, gap) in enumerate(edges):
        if gap > _STRAIGHT_SETBACK_M and index not in corner:
            continue
        along = [edge.project(Point(c)) for c in body.exterior.coords]
        lo, hi = max(min(along), 0.0), min(max(along), edge.length)
        if hi > lo:
            out.append((offset + lo, offset + hi))
    return merge(out)


def _wall_line(contacts: list[Interval], ring: list) -> list[Interval]:
    """Contacts with each run's end face on a perpendicular wall dropped."""
    vertices, total = [], 0.0
    for index in range(len(ring)):
        vertices.append(total)
        a, b = ring[index], ring[(index + 1) % len(ring)]
        total += ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
    pieces: list[Interval] = []
    for lo, hi in contacts:  # split at ring vertices: one piece per wall face
        cuts = [v for v in vertices if lo + 1e-6 < v < hi - 1e-6]
        edges = [lo, *cuts, hi]
        pieces += list(zip(edges, edges[1:], strict=False))
    runs: list[list[Interval]] = []
    for piece in pieces:
        if runs and abs(runs[-1][-1][1] - piece[0]) < 1e-6:
            runs[-1].append(piece)
        else:
            runs.append([piece])
    out: list[Interval] = []
    for run in runs:
        if len(run) > 1 and run[0][1] - run[0][0] <= _END_FACE_M:
            run = run[1:]
        if len(run) > 1 and run[-1][1] - run[-1][0] <= _END_FACE_M:
            run = run[:-1]
        out.append((run[0][0], run[-1][1]))
    return out


def _kitchen_rooms(ctx: CheckContext, kinds: dict) -> set[str]:
    """Rooms with kitchen or dining occupancy, a kitchen sink, or a cooking unit in them."""
    rooms = {r.tag for r in ctx.model.rooms
             if r.occupancy in (Occupancy.KITCHEN.value, Occupancy.DINING.value)}
    for obj in ctx.model.canvas_objects:
        kind = kinds.get(obj.type_ref or "")
        if obj.room and kind and kind[0] in ("sink", "cooking") and obj.kind in (
                "Fixture", "Appliance"):
            rooms.add(obj.room)
    return rooms


def _type_kinds(ctx: CheckContext) -> dict:
    """Type tag -> ("sink" | "cooking",) for the placeables that break a wall space."""
    lib = ctx.plan.library
    out = {t.tag: ("sink",) for t in lib.fixture_types
           if (getattr(t, "plan_symbol", None) or "").startswith(("kitchen-sink", "bar-sink"))}
    out.update({t.tag: ("cooking",) for t in lib.appliance_types if t.cooking})
    return out


def counter_findings(ctx: CheckContext, cid: str) -> list[Finding]:
    """NEC 210.52(C)(1), (C)(3) and (C)(4) over every kitchen-area countertop."""
    from shapely.geometry import Point, Polygon

    from typehaus.checks.mep.electrical import _counts_toward_210_52
    from typehaus.resolve.geometry_countertops import countertop_top_z
    from typehaus.resolve.overlay import union_all

    model = ctx.model
    kinds = _type_kinds(ctx)
    rooms = _kitchen_rooms(ctx, kinds)
    if not rooms:
        return [_na(cid, f"no kitchen or dining room, kitchen sink or cooking unit is modeled, "
                         f"so {NEC.COUNTERTOP} has no counter to govern")]
    pieces: dict[str, list] = defaultdict(list)
    for top in model.countertops:
        if top.room in rooms:
            z = countertop_top_z(model, top)
            if z is not None:
                pieces[top.room].append((top, Polygon(top.outline), z))
    if not pieces:
        return [_unknown(cid, f"{NEC.COUNTERTOP}: kitchen area {', '.join(sorted(rooms))} has "
                              "no resolved countertop (or none with a known top height)")]
    elements = {e.tag: e for s in ctx.plan.storeys for e in ctx.plan.storey_elements(s.tag)
                if e.element_kind == "ElectricalDevice"}
    objects = {o.tag: o for o in model.canvas_objects if o.kind == "ElectricalDevice"}
    out: list[Finding] = []
    for room in (r for r in model.rooms if r.tag in pieces):
        ring = floor_line_ring(model, room)
        items = pieces[room.tag]
        if len(ring) < 3:
            out.append(_unknown(cid, f"room {room.tag}: boundary geometry is unresolved "
                                     f"for {NEC.COUNTERTOP}", (room.tag,)))
            continue
        counters = union_all([p.buffer(0.01) for _, p, _ in items])
        perimeter = room_perimeter.perimeter_length(ring)
        line = _wall_line(_contacts(ring, counters, perimeter), ring)
        breaks: list[Interval] = []
        for obj in model.canvas_objects:
            kind = kinds.get(obj.type_ref or "")
            if obj.room == room.tag and kind and len(obj.footprint) >= 3:
                breaks += _behind(ring, Polygon(obj.footprint))
        spaces = [s for lo, hi in line for s in subtract(lo, hi, breaks)]
        glass: list[tuple[Interval, str]] = []  # windows standing at a counter
        walls = {w.tag: w for w in model.walls if w.storey == room.storey}
        for op in model.openings:
            wall = walls.get(op.host_wall)
            if op.kind != "window" or wall is None:
                continue
            centre = opening_center(wall, op)
            c, dist = room_perimeter.perimeter_position(ring, centre)
            if dist > 0.2 or counters.distance(Point(centre)) > 0.25:
                continue
            top = min(items, key=lambda i: i[1].distance(Point(centre)))[2]
            sill = wall.base_ref_z_m + op.sill_m
            if sill + op.height_m > top and sill - top < _PLATE_M \
                    and op.width_m >= _MIN_SPACE_M:
                glass.append(((c - op.width_m / 2, c + op.width_m / 2), op.tag))
        nearby = []  # (obj, s, nearest piece top, piece tag) for devices on a counter
        for tag, element in elements.items():
            obj = objects.get(tag)
            if obj is None or obj.storey != room.storey:
                continue
            xy = placed_xy(model, element)
            point = Point(xy)
            if counters.distance(point) > _FACE_M:
                continue
            piece = min(items, key=lambda i: i[1].distance(point))
            nearby.append((element, obj, room_perimeter.perimeter_position(ring, xy)[0],
                           piece[2], piece[0].tag))
        stations: list[float] = []
        reasons: list[tuple[float, str]] = []
        for element, obj, s, top, _ in nearby:
            if not _counts_toward_210_52(ctx, element):
                continue
            if obj.z_m < top - 1e-3:
                reasons.append((s, f"{obj.tag} is below the counter"))
            elif (obj.body_z1_m or obj.z_m) - top > _MAX_ABOVE_M:
                reasons.append((s, f"{obj.tag} is {((obj.body_z1_m or obj.z_m) - top) / _IN:.0f}\""
                                   " above the counter, past 20\""))
            else:
                stations.append(s)
        for element, obj, _s, top, ctag in nearby:  # (C)(4)
            device_top = obj.body_z1_m or obj.z_m
            if element.kind.value in _KIND_ALL and obj.z_m < top and device_top > top - _BELOW_M:
                out.append(advisory(
                    cid, f"{obj.tag} sits {(top - device_top) / _IN:.0f}\" below {ctag}'s top; "
                         f"NEC {NEC.BELOW_COUNTERTOP} keeps a receptacle 24\" or more below the "
                         "countertop", (obj.tag, ctag), Result.FAIL))
        gaps, lacking, windows = {}, {}, {}
        for space in spaces:
            if space[1] - space[0] < _MIN_SPACE_M:
                continue
            cut = [(max(a, space[0]), min(b, space[1])) for (a, b), _ in glass
                   if min(b, space[1]) - max(a, space[0]) >= _MIN_SPACE_M]
            windows[space] = sorted({t for (a, b), t in glass
                                     if min(b, space[1]) - max(a, space[0]) >= _MIN_SPACE_M})
            gaps[space], lacking[space] = (obstructed_gaps(space, cut, stations) if cut
                                           else (space_gaps([space], stations), []))
        for (lo, hi), found in gaps.items():
            ends = [room_perimeter.point_at(ring, v) for v in (lo, (lo + hi) / 2, hi)]
            names = sorted({t.tag for t, p, _ in items
                            if any(p.distance(Point(e)) <= _TOL_M + 0.05 for e in ends)})
            label = f"{' + '.join(names)} space {(hi - lo) / _IN:.0f}\" long"
            where = ", ".join(f"({x / 0.3048:.1f}', {y / 0.3048:.1f}')" for x, y in ends[::2])
            lacks, glazing = lacking[(lo, hi)], windows[(lo, hi)]
            if glazing and not found and not lacks:
                out.append(_pass(
                    cid, f"{label} ({where}): glass at the counter ({', '.join(glazing)}) "
                         "leaves no wall for a box; graded under (C)(1) Ex 2, 'as close as "
                         "practicable', with the outlet count and an outlet beside each glass "
                         "edge, each per (C)(3). Ex 2 does not name windows: that reading needs "
                         "the AHJ's agreement, and no 2026 text was found "
                         f"({mark(NEC.WALL_COUNTERTOP)})", (*names, *glazing)))
                continue
            if not found and not lacks:
                out.append(_pass(cid, f"{label} ({where}) meets {mark(NEC.WALL_COUNTERTOP)}",
                                 tuple(names)))
                continue
            if not found:
                out.append(advisory(
                    cid, f"{label} ({where}): glass at the counter ({', '.join(glazing)}) but "
                         f"Ex 2 is not met: {'; '.join(lacks)} ({mark(NEC.WALL_COUNTERTOP)})",
                    (*names, *glazing), Result.FAIL))
                continue
            glo, ghi = max(found, key=lambda g: g[1] - g[0])
            gx, gy = room_perimeter.point_at(ring, (glo + ghi) / 2)
            near = [r for s, r in reasons if lo - _REACH_M <= s <= hi + _REACH_M]
            out.append(advisory(
                cid, f"{label} ({where}): {(ghi - glo) / _IN:.0f}\" of wall line near "
                     f"({gx / 0.3048:.1f}', {gy / 0.3048:.1f}') is more than 24\" from a counter "
                     f"receptacle ({mark(NEC.WALL_COUNTERTOP)})"
                     + (f"; not counted: {'; '.join(near)}" if near else ""),
                tuple(names), Result.FAIL))
    if not out:
        out.append(_na(cid, "every kitchen-area counter stands clear of the walls (an island "
                            "or peninsula is electrical.island_receptacle's), so no wall "
                            f"countertop space exists for {NEC.COUNTERTOP}"))
    return out
