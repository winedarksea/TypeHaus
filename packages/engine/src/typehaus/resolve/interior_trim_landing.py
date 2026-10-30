"""Base on a skirted stair's landing: the ordinary base, at the landing's own floor (#85).

Base runs are derived per room at the room's floor, so a mid-height landing had none. Each
landing (its decks grouped by walking height) becomes a ring, each side snapped to the
finish face of the wall beside it, as a room's clear face is; its wall-backed edges take the
room's base, cut and cornered as ``interior_trim_base`` cuts a room's, broken at the skirts.
"""

from __future__ import annotations

from dataclasses import replace

from typehaus.resolve import room_perimeter as rp
from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.interior_trim_base import (
    _AGAINST_M,
    _butting,
    _cut,
    _runs,
    _subtract,
    finish_arcs,
    stair_skirt_footprints,
)
from typehaus.resolve.interior_trim_scope import TrimScope, base_kind
from typehaus.resolve.model import ResolvedModel, ResolvedStair
from typehaus.resolve.model_trim import ResolvedBaseRun
from typehaus.resolve.overlay import union_all
from typehaus.resolve.room_lookup import room_owning
from typehaus.resolve.room_walls import bounding_wall_arcs

# A deck edge this close to a wall's finish face is snapped to it: catlin's landing deck
# stops 7/8" short of W-M-N2's face, and the base belongs on the wall.
_SNAP_TO_WALL_M = 1.0 * 0.0254


def resolve_landing_base_runs(model: ResolvedModel, scope: TrimScope) -> None:
    skirt = scope.standard.stair_skirt
    if skirt is None:
        return
    for stair in sorted(model.stairs, key=lambda s: s.uid):
        if stair.tag not in skirt.stair_refs:
            continue
        for ring, floor_z in _landing_rings(model, stair):
            xs, ys = [p[0] for p in ring], [p[1] for p in ring]
            room = room_owning(model, stair.storey, ((min(xs) + max(xs)) / 2.0,
                                                     (min(ys) + max(ys)) / 2.0))
            if room is None or room.tag not in scope.rooms:
                continue
            kind = base_kind(scope, room)
            if kind != "none":
                model.base_runs.extend(
                    _landing_runs(model, scope, stair, room, ring, floor_z, kind))


def _landing_rings(model: ResolvedModel, stair: ResolvedStair) -> list[tuple[list, float]]:
    """``(ccw ring, walking z)`` per landing height."""
    by_height: dict[float, list] = {}
    for member in stair.members:
        if member.category == "landing":
            z = round(member.z1_m + stair.finish_thickness_m, 6)
            by_height.setdefault(z, []).append(member_footprint(member)[0])
    from shapely.geometry import Polygon

    out = []
    for z, rings in sorted(by_height.items()):
        x0, y0, x1, y1 = union_all([Polygon(r) for r in rings]).bounds
        x0, x1 = (_wall_face(model, stair.storey, 0, edge, outward, (y0, y1))
                  for edge, outward in ((x0, -1), (x1, 1)))
        y0, y1 = (_wall_face(model, stair.storey, 1, edge, outward, (x0, x1))
                  for edge, outward in ((y0, -1), (y1, 1)))
        out.append(([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z))
    return out


def _wall_face(model: ResolvedModel, storey: str, cross_axis: int, edge: float,
               outward: int, span: tuple[float, float]) -> float:
    """The finish face of the wall that most overlaps a landing side near ``edge``, else
    ``edge``. ``outward`` points from the landing toward the wall on ``cross_axis``."""
    best = None
    for wall in model.walls:
        a, b = wall.axis
        if wall.storey != storey or abs(a[cross_axis] - b[cross_axis]) > 1e-6:
            continue
        points = [p for layer in wall.depth_layers() for p in layer.polygon]
        if not points:
            continue
        face = outward * min(outward * p[cross_axis] for p in points)
        run = [p[1 - cross_axis] for p in points]
        overlap = min(max(run), span[1]) - max(min(run), span[0])
        if abs(face - edge) <= _SNAP_TO_WALL_M and overlap > 0 and (
                best is None or overlap > best[0]):
            best = (overlap, face)
    return edge if best is None else best[1]


def _landing_runs(model: ResolvedModel, scope: TrimScope, stair: ResolvedStair, room,
                  ring: list, floor_z: float, kind: str) -> list[ResolvedBaseRun]:
    from shapely.geometry import LineString

    landing = replace(room, clear_face=tuple(ring))
    perimeter = rp.perimeter_length(ring)
    height = scope.standard.base_height.meters
    arcs = bounding_wall_arcs(model, landing, ring, scope.body)
    finish, bare, owned = finish_arcs(ring, perimeter, arcs, floor_z, height)
    breaks = [(a, b, "bare face") for a, b in bare]
    sides = [LineString([ring[i], ring[(i + 1) % len(ring)]]) for i in range(len(ring))]
    for tag, polygon in stair_skirt_footprints(model, stair.storey):
        if tag == stair.tag:
            breaks.extend((a, b, tag) for a, b in _butting(sides, polygon, _AGAINST_M))
    kept = _subtract(rp.merged_intervals(finish, perimeter),
                     rp.merged_intervals([(a, b) for a, b, _ in breaks], perimeter))
    runs = _runs(landing, kind, scope, ring, perimeter, _cut(ring, kept, [], owned), owned,
                 breaks, floor_z, height)
    # Distinct from the room's own runs on the same walls.
    return [replace(run, uid=run.uid.replace(f"{room.uid}-base-",
                                             f"{stair.uid}-landing-base-", 1),
                    tag=run.tag.replace(f"BASE-{room.tag}-", f"BASE-{stair.tag}-LANDING-", 1))
            for run in runs]
