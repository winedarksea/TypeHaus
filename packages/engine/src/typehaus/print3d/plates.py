"""A furniture piece's thin horizontal plates fused into the parts they rest on.

A tabletop on its legs, a desk's apron under its top: a flat prism thinner than a feature
whose bottom sits on another of the piece's primitives (or whose top hangs from one) grows
to ``min_feature_mm`` toward that host, its exposed face fixed. Growth goes into the host or
the open space under the plate, so the top surface stays true. Every other primitive is
printed as drawn, and the piece is then graded as before.
"""

from __future__ import annotations

from dataclasses import replace

from typehaus.print3d.collect import PrintItem
from typehaus.print3d.policy import PrintSettings
from typehaus.resolve.geometry_ir import GPrism
from typehaus.solids3d.convert import to_manifold, union
from typehaus.solids3d.recorder import Primitive

#: Faces this close are in contact, metres.
CONTACT_M = 1e-4


def fuse_resting_plates(item: PrintItem, mm_per_m: float,
                        settings: PrintSettings) -> tuple[PrintItem, int]:
    """The item with its thin resting plates grown, and how many grew."""
    target_m = settings.feature_mm / mm_per_m
    boxes = [_box(primitive) for primitive in item.primitives]
    grown: list[Primitive] = []
    count = 0
    for index, primitive in enumerate(item.primitives):
        solid = primitive.solid
        if not _thin_flat_plate(primitive, target_m):
            grown.append(primitive)
            continue
        others = [box for other, box in enumerate(boxes) if other != index]
        z0, z1 = solid.z0_m, solid.z1_m
        if any(_touches(boxes[index], box, box[5], z0) for box in others):
            solid = replace(solid, z0_m=z1 - target_m)  # rests on its host: top fixed
        elif any(_touches(boxes[index], box, box[2], z1) for box in others):
            solid = replace(solid, z1_m=z0 + target_m)  # hangs from its host: bottom fixed
        else:
            grown.append(primitive)
            continue
        dims = (*primitive.dims_m[1:], target_m)
        grown.append(Primitive(solid, primitive.color, tuple(sorted(dims))))
        count += 1
    if not count:
        return item, 0
    return replace(item, solid=union(to_manifold(p.solid) for p in grown),
                   primitives=grown), count


def _thin_flat_plate(primitive: Primitive, target_m: float) -> bool:
    solid = primitive.solid
    if not isinstance(solid, GPrism) or solid.top is not None:
        return False
    height = solid.z1_m - solid.z0_m
    return height < target_m and abs(height - primitive.dims_m[0]) < 1e-9


def _touches(plate, other, face_z: float, plate_z: float) -> bool:
    """``other``'s face at ``face_z`` meets the plate's face at ``plate_z``, overlapping
    it in plan."""
    return (abs(face_z - plate_z) <= CONTACT_M and plate[0] < other[3] and other[0] < plate[3]
            and plate[1] < other[4] and other[1] < plate[4])


def _box(primitive: Primitive) -> tuple[float, ...]:
    solid = primitive.solid
    if isinstance(solid, GPrism):
        xs = [x for x, _ in solid.ring]
        ys = [y for _, y in solid.ring]
        top = max(solid.top) if solid.top is not None else solid.z1_m
        return (min(xs), min(ys), solid.z0_m, max(xs), max(ys), top)
    return tuple(to_manifold(solid).bounding_box())
