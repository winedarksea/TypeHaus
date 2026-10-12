"""Armless bench-top recliner and its three-section mattress, in one local frame.

The back is +y. Both symbols mount on the platform, not one on the other's bounding
box: the mattress follows the slats, whose bounding height is the back's height.
"""

from __future__ import annotations

import math

from typehaus.model.placeable_symbols._families import Geometry
from typehaus.model.placeable_symbols._frame import box, line, rect
from typehaus.model.placeable_symbols._mesh import mesh_part
from typehaus.quantities import M_PER_IN

REFERENCE_WIDTH_IN = 26.0
REFERENCE_DEPTH_IN = 57.5
BACK_LENGTH_IN = 36.0
SEAT_LENGTH_IN = 22.0
LEG_LENGTH_IN = 22.0
MATTRESS_FLAT_LENGTH_IN = BACK_LENGTH_IN + SEAT_LENGTH_IN + LEG_LENGTH_IN
READING_BACK_ANGLE_DEG = 110.0
LOCKING_BACK_ANGLES_DEG = (105.0, 110.0, 112.0)
WOOD_THICKNESS_IN = 1.5
MATTRESS_THICKNESS_IN = 4.0
SLAT_WIDTH_IN = 3.0
SLAT_GAP_IN = 0.25
SUPPORT_WIDTH_IN = 1.5
BOLSTER_THICKNESS_IN = 2.0
BOLSTER_WIDTH_SHARE = 0.7
# Distances down from the back's top; both cushions can be moved during the fit trial.
BOLSTER_BACK_RANGES_IN = ((4.0, 12.0), (24.0, 32.0))


def profile_height_in(*, mattress: bool = False,
                      angle_degrees: float = READING_BACK_ANGLE_DEG) -> float:
    angle = math.radians(180.0 - angle_degrees)
    thickness = WOOD_THICKNESS_IN + (MATTRESS_THICKNESS_IN if mattress else 0.0)
    return BACK_LENGTH_IN * math.sin(angle) + thickness * math.cos(angle)


def reclining_profile(depth_m: float, angle_degrees: float = READING_BACK_ANGLE_DEG):
    """Back top, hip, knee and heel on the wood's underside; (local y, local z)."""
    scale = depth_m / (REFERENCE_DEPTH_IN * M_PER_IN)
    angle = math.radians(180.0 - angle_degrees)
    back_projection = BACK_LENGTH_IN * M_PER_IN * scale * math.cos(angle)
    seat_length = SEAT_LENGTH_IN * M_PER_IN * scale
    leg_length = LEG_LENGTH_IN * M_PER_IN * scale
    half_run = (back_projection + seat_length + leg_length) / 2
    hip = half_run - back_projection
    return ((half_run, BACK_LENGTH_IN * M_PER_IN * scale * math.sin(angle)),
            (hip, 0.0), (hip - seat_length, 0.0), (-half_run, 0.0))


def _offset_vectors(profile):
    """Miter adjacent offsets so thick back/seat pads meet without overlapping filling."""
    normals = []
    for start, end in zip(profile, profile[1:], strict=False):
        dy, dz = end[0] - start[0], end[1] - start[1]
        length = math.hypot(dy, dz)
        normals.append((dz / length, -dy / length))
    vectors = [normals[0]]
    for previous, following in zip(normals, normals[1:], strict=False):
        denominator = 1 + sum(a * b for a, b in zip(previous, following, strict=True))
        vectors.append(tuple((a + b) / denominator
                             for a, b in zip(previous, following, strict=True)))
    return (*vectors, normals[-1])


def _ribbon(width, start, end, offset_lo, offset_hi, vertical_scale, color,
            offset_vectors=None, *, center_x=0.0):
    """Closed extrusion across the width, with optional miter vectors at profile joints."""
    if offset_vectors is None:
        dy, dz = end[0] - start[0], end[1] - start[1]
        length = math.hypot(dy, dz)
        offset_vectors = ((dz / length, -dy / length),) * 2
    first, last = offset_vectors
    ring = [(point[0] + normal[0] * offset,
             (point[1] + normal[1] * offset) * vertical_scale)
            for point, normal, offset in ((start, first, offset_lo), (end, last, offset_lo),
                                          (end, last, offset_hi), (start, first, offset_hi))]
    positions = [(center_x + x, y, z) for x in (-width / 2, width / 2) for y, z in ring]
    triangles = [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7)]
    for index in range(4):
        following = (index + 1) % 4
        triangles.extend(((index, following, following + 4),
                          (index, following + 4, index + 4)))
    # The y/z ring runs clockwise; reverse winding so visible faces point outward.
    return mesh_part(positions, [(a, c, b) for a, b, c in triangles], color)


def _projection(part):
    center, size = part["center"], part["size"]
    return rect(center[0], center[1], size[0], size[1], fill=part["color"])


def _geometry(width: float, depth: float, height: float, *, mattress: bool,
              angle_degrees: float = READING_BACK_ANGLE_DEG) -> Geometry:
    profile = reclining_profile(depth, angle_degrees)
    vectors = _offset_vectors(profile)
    scale = depth / (REFERENCE_DEPTH_IN * M_PER_IN)
    wood = WOOD_THICKNESS_IN * M_PER_IN * scale
    padding = MATTRESS_THICKNESS_IN * M_PER_IN * scale
    vertical_scale = height / (profile_height_in(mattress=mattress,
                                                angle_degrees=angle_degrees) * M_PER_IN * scale)
    parts = []
    support = min(SUPPORT_WIDTH_IN * M_PER_IN * scale, width / 8)
    strokes = [] if mattress else [rect(0, 0, width, depth, fill="sauna-wood")]
    for segment, (start, end) in enumerate(zip(profile, profile[1:], strict=False)):
        if mattress:
            part = _ribbon(width, start, end, wood, wood + padding,
                           vertical_scale, "mattress", vectors[segment:segment + 2])
            parts.append(part)
            strokes.append(_projection(part))
            continue
        joint_y = end[0] + vectors[segment + 1][0] * wood
        strokes.append(line((-width / 2, joint_y), (width / 2, joint_y)))
        length = math.dist(start, end)
        pitch = (SLAT_WIDTH_IN + SLAT_GAP_IN) * M_PER_IN * scale
        slat_count = max(1, math.ceil(length / pitch))
        gap_share = SLAT_GAP_IN / (SLAT_WIDTH_IN + SLAT_GAP_IN)
        for index in range(slat_count):
            a = (index + gap_share / 2) / slat_count
            b = (index + 1 - gap_share / 2) / slat_count
            lo = tuple(start[i] + (end[i] - start[i]) * a for i in range(2))
            hi = tuple(start[i] + (end[i] - start[i]) * b for i in range(2))
            offset_vectors = tuple(tuple(vectors[segment][i] + fraction *
                                         (vectors[segment + 1][i] - vectors[segment][i])
                                         for i in range(2)) for fraction in (a, b))
            parts.append(_ribbon(width - 2 * support, lo, hi, 0, wood,
                                 vertical_scale, "sauna-wood",
                                 offset_vectors))
    if mattress:
        start, end = profile[:2]
        for first, last in BOLSTER_BACK_RANGES_IN:
            lo = tuple(start[i] + (end[i] - start[i]) * first / BACK_LENGTH_IN
                       for i in range(2))
            hi = tuple(start[i] + (end[i] - start[i]) * last / BACK_LENGTH_IN
                       for i in range(2))
            part = _ribbon(width * BOLSTER_WIDTH_SHARE, lo, hi, wood + padding,
                           wood + padding + BOLSTER_THICKNESS_IN * M_PER_IN * scale,
                           vertical_scale, "pillow")
            parts.append(part)
            strokes.append(_projection(part))
    if not mattress:
        back_y, back_z = profile[0]
        # Slats join inclined side stringers; rear uprights carry these into the base.
        for sign in (-1, 1):
            x = sign * (width / 2 - support / 2)
            parts.append(_ribbon(support, *profile[:2], 0, wood, vertical_scale,
                                 "sauna-wood-dark", vectors[:2], center_x=x))
            parts.append(box(x, back_y - support / 2, 0, back_z * vertical_scale,
                             support, support, "sauna-wood-dark"))
            parts.append(box(x, 0, 0, wood * vertical_scale,
                             support, depth, "sauna-wood-dark"))
    return tuple(strokes), tuple(parts)


def sauna_recliner(width: float, depth: float, height: float) -> Geometry:
    return _geometry(width, depth, height, mattress=False)


def sauna_recliner_mattress(width: float, depth: float, height: float) -> Geometry:
    return _geometry(width, depth, height, mattress=True)
