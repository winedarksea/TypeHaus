"""Where a placeable stands: its authored point, or the wall face it is attached to.

A ``location.attachment`` names a wall, a face and a station; the centre is derived from the
resolved layer polygons every build, so a retype that moves the finish face carries the
device with it. The finish face is read only from the layers present over the body's own z
band (a banded layer such as a dimpleboard that stops at grade is not there at 8'), which is
why ``resolve_placeables`` calls this twice: once to find the room and height, once more
with the body band.
"""

from __future__ import annotations

import math

from typehaus.findings import Finding, Severity
from typehaus.resolve.model import ResolvedModel

#: A body band, absolute metres (bottom, top).
Band = tuple[float, float]


def resolve_location(
    item: object, model: ResolvedModel,
    findings: list[Finding], local_footprint: list[tuple[float, float]],
    band: Band | None = None,
) -> tuple[tuple[float, float] | None, float, str | None, str | None]:
    """(centre, rotation, attachment wall, attachment face) for one placeable."""
    location = getattr(item, "location", None)
    attachment = location.attachment if location is not None else None
    rotation = _degrees(getattr(location, "rotation", None) if location is not None else None)
    rotation = _degrees(getattr(item, "rotation", None)) if rotation == 0 else rotation
    if attachment is None:
        point = (location.position
                 if location is not None and location.position is not None
                 else getattr(item, "position", None))
        return (point.xy_m if point is not None else None), rotation, None, None
    wall = model.wall(attachment.wall_ref)
    if wall is None:
        if band is None:
            findings.append(_finding(
                "integrity.orphan_wall_attachment", item.tag,
                f"placeable {item.tag} attaches to missing wall {attachment.wall_ref}"))
        return None, rotation, attachment.wall_ref, attachment.face
    (x0, y0), (x1, y1) = wall.axis
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy)
    if length < 1e-9:
        if band is None:
            findings.append(_finding(
                "integrity.invalid_wall_attachment", item.tag,
                f"placeable {item.tag} cannot attach to a zero-length wall"))
        return None, rotation, wall.tag, attachment.face
    tangent = (dx / length, dy / length)
    left = (-tangent[1], tangent[0])
    sign = 1 if attachment.face == "left" else -1
    distance = max(0.0, min(length, attachment.distance_from_start.meters))
    finish_offset = _finish_offset(wall, (x0, y0), left, sign, band)
    gap = attachment.normal_gap.meters
    resolved_rotation = (math.degrees(math.atan2(tangent[1], tangent[0]))
                         + _degrees(attachment.rotation_offset))
    # Align the *nearest footprint edge*, not its center, to the resolved finish face.
    # Project the rotated local polygon onto the wall's left-normal: left attachments use
    # the minimum (wallward) edge; right attachments use the maximum edge.
    radians = math.radians(resolved_rotation)
    cos, sin = math.cos(radians), math.sin(radians)
    normal_projections = [(px * cos - py * sin) * left[0] + (px * sin + py * cos) * left[1]
                          for px, py in local_footprint]
    wallward_edge = min(normal_projections) if sign > 0 else max(normal_projections)
    center_offset = finish_offset + sign * gap - wallward_edge
    return ((x0 + tangent[0] * distance + left[0] * center_offset,
             y0 + tangent[1] * distance + left[1] * center_offset),
            resolved_rotation, wall.tag, attachment.face)


def hosted_placement(item: object,
                     model: ResolvedModel) -> tuple[tuple[float, float], float] | None:
    """((x, y), degrees) for a placeable, usable BEFORE the placeable stage has run.

    The resolved canvas object when there is one; otherwise the same derivation over every
    layer (the first pass). For the stages that run earlier — drain points, carriers.
    """
    uid = getattr(item, "uid", None)
    obj = next((o for o in model.canvas_objects if o.uid == uid), None)
    if obj is not None:
        return obj.position, obj.rotation_degrees
    from typehaus.resolve.placeables import _TYPE_COLLECTIONS, _local_footprint

    type_ref = getattr(item, "type_ref", None)
    product_type = next((t for collection, _, _ in _TYPE_COLLECTIONS
                         for t in getattr(model.plan.library, collection)
                         if t.tag == type_ref), None)
    center, rotation, _, _ = resolve_location(
        item, model, [], _local_footprint(product_type, item))
    return None if center is None else (center, rotation)


def _finish_offset(wall: object, origin: tuple[float, float], left: tuple[float, float],
                   sign: int, band: Band | None) -> float:
    """Extreme normal offset of the layers present over ``band`` (every layer when None)."""
    x0, y0 = origin
    layers = [layer for layer in wall.layers if band is None or _present(layer, band)]
    if not layers:
        layers = list(wall.layers)
    offsets = [(point[0] - x0) * left[0] + (point[1] - y0) * left[1]
               for layer in layers for point in layer.polygon]
    if not offsets:
        return 0.0
    return max(offsets) if sign > 0 else min(offsets)


def _present(layer: object, band: Band) -> bool:
    """Is a (possibly banded) layer there anywhere over the body band?"""
    z0, z1 = band
    lz0, lz1 = getattr(layer, "z0_m", None), getattr(layer, "z1_m", None)
    return (lz0 is None or lz0 < z1 + 1e-6) and (lz1 is None or lz1 > z0 - 1e-6)


def _degrees(value: object | None) -> float:
    return float(getattr(value, "degrees", 0.0))


def _finding(check_id: str, tag: str, message: str) -> Finding:
    from typehaus.resolve.placeables import _finding as finding

    return finding(check_id, tag, message, Severity.ERROR)
