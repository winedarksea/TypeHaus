"""A shower's door in world space: entry, leaf sector, the angle it can open, its front zone.

Derived from ``FixtureType.shower_enclosure`` through the same ``_shower_door`` functions the
plan glyph uses (decision #152). Records only; ``shower.door_opening`` grades them. The leaf is
a segment from the hinge to the tip (``swing_radius``, handle included), so a body or room face
blocks it where that segment first touches it. ``free_angle_degrees`` is how far it opens.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from shapely.geometry import LineString, Polygon

from typehaus.model.placeable_symbols import place_local
from typehaus.model.placeable_symbols._shower_door import (
    entry_edge,
    hinge_frame,
    leaf_sector,
)
from typehaus.resolve.model import ResolvedModel, Ring

# Resolution of the opening-angle scan, then bisected to ``_REFINE_STEPS``.
_SCAN_STEP_DEGREES = 0.5
_REFINE_STEPS = 8
# Contact tolerance: a leaf resting on a face, or a pan beside a wall, is not blocked.
_TOUCH_M = 1e-3
ROOM_FACE = "room face"


@dataclass(frozen=True)
class ResolvedShowerEnclosure:
    tag: str
    storey: str
    room: str | None
    type_ref: str
    kind: str
    entry: tuple[tuple[float, float], tuple[float, float]] | None
    entry_normal: tuple[float, float] | None  # out of the compartment
    clear_opening_m: float
    leaf_width_m: float | None = None
    swing_radius_m: float | None = None
    hinge: tuple[float, float] | None = None
    closed_direction: tuple[float, float] | None = None
    max_opening_degrees: float = 0.0
    # The fan the leaf sweeps to ``max_opening_degrees``; empty without a swing.
    sector: Ring = ()
    # Degrees the leaf opens before it meets ``blocker`` (None: not before the maximum).
    free_angle_degrees: float | None = None
    blocker: str | None = None
    front_zone: Ring = ()
    front_blockers: tuple[str, ...] = ()
    product_ref: str | None = None


def _local_ring(product) -> tuple[tuple[float, float], ...]:
    if product.footprint_shape is not None:
        return tuple(p.xy_m for p in product.footprint_shape.points)
    w, d = (v.meters for v in product.footprint)
    return ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2))


def _rotated(vector: tuple[float, float], degrees: float) -> tuple[float, float]:
    c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    return (vector[0] * c - vector[1] * s, vector[0] * s + vector[1] * c)


def free_opening_angle(hinge, closed_dir, normal, radius: float, max_degrees: float,
                       room: Polygon | None, bodies: list[tuple[str, Polygon]],
                       ) -> tuple[float, str | None]:
    """``(degrees, blocker)``: the leaf-segment scan from closed to ``max_degrees``."""
    def blocker_at(degrees: float) -> str | None:
        tip = leaf_sector(hinge, closed_dir, normal, radius, degrees, 1)[-1]
        leaf = LineString([hinge, tip])
        if room is not None and not room.covers(leaf):
            return ROOM_FACE
        return next((tag for tag, shape in bodies if shape.intersects(leaf)), None)

    blocked = blocker_at(0.0)
    if blocked is not None:
        return 0.0, blocked
    lo = 0.0
    while lo < max_degrees:
        hi = min(lo + _SCAN_STEP_DEGREES, max_degrees)
        blocked = blocker_at(hi)
        if blocked is not None:
            for _ in range(_REFINE_STEPS):
                mid = (lo + hi) / 2
                lo, hi = (mid, hi) if blocker_at(mid) is None else (lo, mid)
            return lo, blocker_at(hi)
        lo = hi
    return max_degrees, None


def derive_shower_enclosures(model: ResolvedModel, obstruction_by_uid: dict[str, Any],
                             footprints: dict[str, Polygon]) -> None:
    model.shower_enclosures.clear()
    products = {t.tag: t for t in model.plan.library.fixture_types}
    rooms = {r.tag: r for r in model.rooms}
    for obj in model.canvas_objects:
        product = products.get(obj.type_ref or "")
        spec = getattr(product, "shower_enclosure", None) if obj.kind == "Fixture" else None
        if spec is None:
            continue
        edge = entry_edge(_local_ring(product), spec.entry_edge)
        base = dict(tag=obj.tag, storey=obj.storey, room=obj.room, type_ref=product.tag,
                    kind=spec.kind, clear_opening_m=spec.clear_opening.meters,
                    product_ref=spec.product_ref)
        if edge is None:
            model.shower_enclosures.append(ResolvedShowerEnclosure(
                entry=None, entry_normal=None, **base))
            continue
        p0, p1 = place_local([edge[0], edge[1]], obj.position, obj.rotation_degrees)
        normal = _rotated(edge[2], obj.rotation_degrees)
        room_shape = rooms.get(obj.room or "")
        room_poly = (Polygon(room_shape.clear_face).buffer(_TOUCH_M)
                     if room_shape is not None and len(room_shape.clear_face) >= 3 else None)
        z0 = obj.z_m + (product.flood_rim_height.meters if product.flood_rim_height else 0.0)
        z1 = obj.body_z1_m if obj.body_z1_m is not None else z0
        bodies = []
        for other in model.canvas_objects:
            if (other.uid == obj.uid or other.storey != obj.storey
                    or other.host_fixture_ref == obj.tag
                    or not obstruction_by_uid[other.uid].obstructs
                    or (other.body_z0_m is not None and other.body_z0_m >= z1 - 1e-6)
                    or (other.body_z1_m is not None and other.body_z1_m <= z0 + 1e-6)):
                continue
            shape = footprints[other.uid].buffer(-_TOUCH_M)
            if not shape.is_empty:
                bodies.append((other.tag, shape))
        depth = spec.front_zone_depth.meters
        zone = (p0, p1, (p1[0] + normal[0] * depth, p1[1] + normal[1] * depth),
                (p0[0] + normal[0] * depth, p0[1] + normal[1] * depth))
        front = []
        if depth > 0:
            zone_poly = Polygon(zone).buffer(-_TOUCH_M)
            front = [tag for tag, shape in bodies if shape.intersects(zone_poly)]
            if room_poly is not None and not room_poly.covers(zone_poly):
                front.insert(0, ROOM_FACE)
        swing = {}
        if spec.swings:
            local_hinge, local_closed = hinge_frame(
                edge, spec.hinge, spec.hinge_inset.meters, spec.plane_inset.meters)
            hinge = place_local([local_hinge], obj.position, obj.rotation_degrees)[0]
            closed = _rotated(local_closed, obj.rotation_degrees)
            radius = spec.reach.meters
            free, blocker = free_opening_angle(
                hinge, closed, normal, radius, spec.max_opening_degrees, room_poly, bodies)
            swing = dict(
                leaf_width_m=spec.leaf_width.meters, swing_radius_m=radius, hinge=hinge,
                closed_direction=closed, max_opening_degrees=spec.max_opening_degrees,
                sector=tuple(leaf_sector(hinge, closed, normal, radius,
                                         spec.max_opening_degrees)),
                free_angle_degrees=free, blocker=blocker)
        model.shower_enclosures.append(ResolvedShowerEnclosure(
            entry=(p0, p1), entry_normal=normal, front_zone=zone,
            front_blockers=tuple(front), **swing, **base))
