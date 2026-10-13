"""Explicit return flanges land flat on a complete wall face at the rail end's height."""

from __future__ import annotations

import math
from types import SimpleNamespace

from shapely.geometry import LineString, Point

from typehaus.model.placeables import Location
from typehaus.resolve.railings.wall_contact import REACH_M
from typehaus.resolve.wall_faces import wall_body
from typehaus.resolve.wall_hosting import resolve_location

_FACE_TOLERANCE_M = 1e-6
_SLICE_HALF_HEIGHT_M = 0.001


def attached_return_face(model, rail, end, z: float, flange_radius: float):
    """Return ``(face point, outward normal)`` or raise for an invalid authored target."""
    attachment = rail.end_return_attachment
    wall = model.wall(attachment.wall_ref)
    if wall is None:
        raise ValueError(f"missing return wall {attachment.wall_ref}")
    if attachment.face not in ("left", "right") or attachment.normal_gap.meters != 0:
        raise ValueError("a return flange needs a left/right wall face with zero normal gap")
    (x0, y0), (x1, y1) = wall.axis
    run = math.hypot(x1 - x0, y1 - y0)
    if run < _FACE_TOLERANCE_M or not 0 <= attachment.distance_from_start.meters <= run:
        raise ValueError("return attachment station lies outside its wall")
    if z - flange_radius < wall.z0_m or z + flange_radius > wall.z1_m:
        raise ValueError("return flange extends beyond its wall's height")
    item = SimpleNamespace(tag=rail.tag, location=Location(attachment=attachment))
    findings = []
    target, _rotation, _wall, _face = resolve_location(
        item, model, findings, [(0.0, 0.0)], band=(z - flange_radius, z + flange_radius))
    if target is None or findings:
        raise ValueError("return attachment cannot resolve its wall face")
    if not _FACE_TOLERANCE_M < math.dist(end, target) <= REACH_M:
        raise ValueError("return attachment is outside the handrail's return reach")
    tangent = ((x1 - x0) / run, (y1 - y0) / run)
    sign = 1 if attachment.face == "left" else -1
    normal = (-tangent[1] * sign, tangent[0] * sign)
    # A flange at a mitred tip can have its centre on the wall while its screws hang
    # in air. Its whole horizontal diameter must meet the same flat face at every height.
    diameter = LineString([(target[0] + direction * tangent[0] * flange_radius,
                            target[1] + direction * tangent[1] * flange_radius)
                           for direction in (-1, 1)])
    for height in (z - flange_radius, z, z + flange_radius):
        body = wall_body(wall, height - _SLICE_HALF_HEIGHT_M,
                         height + _SLICE_HALF_HEIGHT_M)
        if body.boundary.distance(Point(target)) > _FACE_TOLERANCE_M \
                or not body.buffer(_FACE_TOLERANCE_M).covers(diameter):
            raise ValueError("return flange is not completely supported by a flat wall face")
    return target, normal
