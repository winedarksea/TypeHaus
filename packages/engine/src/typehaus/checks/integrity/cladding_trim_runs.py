"""Geometry helpers the cladding trim checks share."""

from __future__ import annotations

from typehaus.model.cladding_trim import TrimCondition
from typehaus.resolve.cladding_trim.openings import opening_cuts_profiled_metal_cladding
from typehaus.resolve.cladding_trim.runs import kit_faces

_TOLERANCE_M = 1e-6
_BAND_REACH_M = 0.1524     # a band within 6 in above the casing top acts as the head drip


def metal_wall_openings(model, kinds):
    for opening in model.openings:
        if opening.kind not in kinds:
            continue
        wall = model.wall(opening.host_wall)
        if wall is not None and opening_cuts_profiled_metal_cladding(model, wall, opening):
            yield opening, wall


def spans_cover(spans, start, end) -> bool:
    cursor = start
    for low, high in sorted(spans):
        if cursor >= end - _TOLERANCE_M:
            break
        if high < cursor - _TOLERANCE_M:
            continue
        if low > cursor + _TOLERANCE_M:
            return False
        cursor = max(cursor, high)
    return cursor >= end - _TOLERANCE_M


def z_extent(pieces):
    return [(min(p[2] for p in piece.body_mesh.positions),
             max(p[2] for p in piece.body_mesh.positions)) for piece in pieces if piece.body_mesh]


def along_extent(pieces, frame):
    def station(point):
        return sum((point[i] - frame.origin[i]) * frame.along[i] for i in range(2))

    return [(min(map(station, piece.body_mesh.positions)),
             max(map(station, piece.body_mesh.positions))) for piece in pieces if piece.body_mesh]


def door_opening_trim(model, wall, opening, pieces):
    """``None`` when the door is off the kit, ``""`` when trimmed, else what is missing."""
    if not any(face.wall.tag == wall.tag
               for face, _ in kit_faces(model, TrimCondition.DOOR_JAMB)):
        return None
    sill = wall.base_ref_z_m + opening.sill_m
    head = sill + opening.height_m
    for side in ("LEFT", "RIGHT"):
        jambs = [p for p in pieces if p.host_ref == opening.tag
                 and f"-TRIM-JAMB-{side}-" in p.tag]
        if not jambs or not spans_cover(z_extent(jambs), max(sill, wall.z0_m), head):
            return f"lacks a full-height {side.lower()} jamb trim"
    if [p for p in pieces if p.host_ref == opening.tag and "-TRIM-HEAD-" in p.tag]:
        return ""
    low = opening.center_along_m - opening.width_m / 2
    bands = [p for p in pieces if p.product == "BBD_TRANSITION" and p.host_ref == wall.tag]
    if any(p.z0_m <= head + _BAND_REACH_M and p.z1_m >= head and wall.tag == p.host_ref
           for p in bands) and low is not None:
        return ""
    return "has neither a head drip nor a band over it"
