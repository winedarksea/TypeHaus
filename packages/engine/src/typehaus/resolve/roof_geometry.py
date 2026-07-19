"""Shared roof-plane math for ``ToRoof`` walls and ``FollowRoof`` rooms."""

from __future__ import annotations

from shapely.geometry import Polygon

from typehaus.model.refs import ToRoof
from typehaus.resolve.model import ResolvedModel, ResolvedRoof, ResolvedWall


def roof_height_at(roof: ResolvedRoof, point: tuple[float, float]) -> float:
    """Return the exterior roof-plane elevation at a plan-frame point."""
    xs = [item[0] for item in roof.footprint]
    ys = [item[1] for item in roof.footprint]
    coordinate = point[1] if roof.ridge_direction == "x" else point[0]
    low, high = (min(ys), max(ys)) if roof.ridge_direction == "x" else (min(xs), max(xs))
    span = high - low
    if span <= 1e-9:
        return roof.eave_z_m
    if roof.form == "shed":
        return roof.eave_z_m + (coordinate - low) / span * (roof.ridge_z_m - roof.eave_z_m)
    midpoint = (low + high) / 2.0
    ratio = max(0.0, 1.0 - abs(coordinate - midpoint) / (span / 2.0))
    return roof.eave_z_m + ratio * (roof.ridge_z_m - roof.eave_z_m)


def apply_to_roof_wall_tops(model: ResolvedModel) -> None:
    """Resolve raked wall endpoints after roof envelopes have been established."""
    roofs = {roof.tag: roof for roof in model.roofs}
    resolved: list[ResolvedWall] = []
    for wall in model.walls:
        authored = model.plan.by_tag(wall.tag)
        top = getattr(authored, "top", None)
        if not isinstance(top, ToRoof) or top.roof_ref not in roofs:
            resolved.append(wall)
            continue
        roof = roofs[top.roof_ref]
        start_top = roof_height_at(roof, wall.axis[0])
        end_top = roof_height_at(roof, wall.axis[1])
        resolved.append(ResolvedWall(
            uid=wall.uid, tag=wall.tag, storey=wall.storey, assembly=wall.assembly,
            axis=wall.axis, layers=wall.layers, z0_m=wall.z0_m,
            z1_m=max(start_top, end_top), is_foundation=wall.is_foundation,
            members=wall.members, top_z0_m=start_top, top_z1_m=end_top,
        ))
    model.walls = resolved


def roof_headroom_areas(room_ring: list[tuple[float, float]], roof: ResolvedRoof,
                        elevation_m: float, threshold_m: float) -> tuple[float, float]:
    """Return room area and area at/above a headroom threshold.

    Gable roof halves are linear planes.  Clipping each half against the corresponding
    threshold strip keeps the code result exact for arbitrary room polygons rather than
    relying on a display-resolution sample grid.
    """
    room = Polygon(room_ring).intersection(Polygon(roof.footprint))
    if room.is_empty:
        return (0.0, 0.0)
    total = room.area
    required_z = elevation_m + threshold_m
    xs = [item[0] for item in roof.footprint]
    ys = [item[1] for item in roof.footprint]
    low, high = (min(ys), max(ys)) if roof.ridge_direction == "x" else (min(xs), max(xs))
    rise = roof.ridge_z_m - roof.eave_z_m
    if rise <= 1e-9:
        return total, total if roof.eave_z_m >= required_z else 0.0
    ratio = (required_z - roof.eave_z_m) / rise
    if ratio <= 0:
        return total, total
    if ratio > 1:
        return total, 0.0
    midpoint = (low + high) / 2.0
    extent = max(max(xs) - min(xs), max(ys) - min(ys)) + 1.0
    if roof.ridge_direction == "x":
        if roof.form == "shed":
            qualifying = Polygon([(min(xs) - extent, low + ratio * (high - low)),
                                  (max(xs) + extent, low + ratio * (high - low)),
                                  (max(xs) + extent, max(ys) + extent),
                                  (min(xs) - extent, max(ys) + extent)])
        else:
            lo = low + ratio * (midpoint - low)
            hi = high - ratio * (high - midpoint)
            qualifying = Polygon([(min(xs) - extent, lo), (max(xs) + extent, lo),
                                  (max(xs) + extent, hi), (min(xs) - extent, hi)])
    else:
        if roof.form == "shed":
            qualifying = Polygon([(low + ratio * (high - low), min(ys) - extent),
                                  (max(xs) + extent, min(ys) - extent),
                                  (max(xs) + extent, max(ys) + extent),
                                  (low + ratio * (high - low), max(ys) + extent)])
        else:
            lo = low + ratio * (midpoint - low)
            hi = high - ratio * (high - midpoint)
            qualifying = Polygon([(lo, min(ys) - extent), (hi, min(ys) - extent),
                                  (hi, max(ys) + extent), (lo, max(ys) + extent)])
    return total, room.intersection(qualifying).area
