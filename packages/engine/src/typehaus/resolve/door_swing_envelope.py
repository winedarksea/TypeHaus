"""Conservative continuous leaf and hardware sweeps for a documented installation.

This is coordination geometry, not certification of a prehung assembly or its fit.
All elevations and distances are in project-frame metres.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from shapely.affinity import affine_transform, rotate
from shapely.geometry import MultiPoint, box
from shapely.ops import unary_union

from typehaus.emit.draw.elevation_project import solid_faces
from typehaus.resolve.geometry import opening_center, wall_frame


@dataclass(frozen=True)
class SwingComponent:
    name: str
    closed: object
    bottom_z_m: float
    top_z_m: float


@dataclass(frozen=True)
class ClearanceResult:
    component: str
    obstacle: str
    part: str
    clearance_m: float
    angle_interval_degrees: tuple[float, float]


def assembly_components(wall, opening):
    """Resolve the independent hinge, leaf faces and hardware from the authored section."""
    spec = opening.swing_assembly
    if spec is None:
        raise ValueError(f"{opening.tag} has no authored swing assembly")
    center = opening_center(wall, opening)
    if center is None:
        raise ValueError("a swing assembly requires a nondegenerate wall")
    _, tangent, normal, _ = wall_frame(wall)
    toward_latch = 1 if opening.flip_hinge else -1
    placement = opening.doorway.exterior_placement if opening.doorway else None
    if spec.hinge_normal_datum == "exterior_placement" and placement is None:
        raise ValueError("swing assembly requires an exterior placement datum")
    normal_offset = spec.hinge_normal_offset.meters
    if spec.hinge_normal_datum == "exterior_placement":
        normal_offset += placement.leaf_normal_m
    hinge = tuple(center[i] - tangent[i] * toward_latch * opening.width_m / 2
                  + tangent[i] * toward_latch * spec.hinge_inset.meters
                  + normal[i] * normal_offset for i in range(2))
    closed_axis = (tangent[0] * toward_latch, tangent[1] * toward_latch)
    cross_axis = (-closed_axis[1], closed_axis[0])
    matrix = [closed_axis[0], cross_axis[0], closed_axis[1], cross_axis[1], *hinge]
    leaf = box(spec.leaf_start.meters, spec.leaf_face_min.meters,
               spec.leaf_end.meters, spec.leaf_face_max.meters)
    spindle = spec.leaf_end.meters - spec.lever_backset.meters
    lever_start = spindle - spec.lever_hingeward_extent.meters
    lever = unary_union([
        box(lever_start, spec.leaf_face_min.meters - spec.lever_projection.meters,
            spindle, spec.leaf_face_min.meters),
        box(lever_start, spec.leaf_face_max.meters,
            spindle, spec.leaf_face_max.meters + spec.lever_projection.meters),
    ])
    sill_z = wall.base_ref_z_m + opening.sill_m
    return hinge, (
        SwingComponent("leaf", affine_transform(leaf, matrix),
                       sill_z + spec.leaf_bottom.meters, sill_z + spec.leaf_top.meters),
        SwingComponent("lever", affine_transform(lever, matrix),
                       sill_z + spec.lever_bottom.meters, sill_z + spec.lever_top.meters),
    )


def swept_intervals(component, hinge, opening, stop_degrees, step_degrees=1.0):
    """Enclose the full rotation with chord hulls plus a vertex-arc sagitta."""
    limit = stop_degrees + opening.swing_assembly.stop_tolerance_degrees
    count = max(1, math.ceil(limit / step_degrees))
    step = limit / count
    hinge_sign = -1 if opening.flip_hinge else 1
    swing_sign = -1 if opening.flip_swing else 1
    direction = -hinge_sign * swing_sign
    bounds = component.closed.bounds
    radius = max(math.hypot(x - hinge[0], y - hinge[1])
                 for x in (bounds[0], bounds[2]) for y in (bounds[1], bounds[3]))
    sagitta = radius * (1 - math.cos(math.radians(step / 2)))
    poses = [rotate(component.closed, direction * step * i, origin=hinge)
             for i in range(count + 1)]
    return tuple((i * step, (i + 1) * step,
                  poses[i].union(poses[i + 1]).convex_hull.buffer(sagitta))
                 for i in range(count))


def installed_swing_sector(wall, opening, stop_degrees):
    """A conservative symbolic sector using the sourced installation's hinge and leaf."""
    from shapely.geometry import Point

    hinge, _ = assembly_components(wall, opening)
    _, tangent, _, _ = wall_frame(wall)
    toward_latch = 1 if opening.flip_hinge else -1
    direction = -(-1 if opening.flip_hinge else 1) * (-1 if opening.flip_swing else 1)
    radius = opening.swing_assembly.leaf_end.meters
    closed_tip = Point(hinge[0] + tangent[0] * toward_latch * radius,
                       hinge[1] + tangent[1] * toward_latch * radius)
    return [hinge, *(tuple(rotate(closed_tip, direction * stop_degrees * i / 8,
                                  origin=hinge).coords[0]) for i in range(9))]


def _clip_face(face, lower, upper):
    clipped = list(face)
    for height, sign in ((lower, 1), (upper, -1)):
        if not clipped:
            break
        result = []
        for start, end in zip(clipped, clipped[1:] + clipped[:1], strict=True):
            inside_start = sign * (start[2] - height) >= 0
            inside_end = sign * (end[2] - height) >= 0
            if inside_start:
                result.append(start)
            if inside_start != inside_end:
                fraction = (height - start[2]) / (end[2] - start[2])
                result.append(tuple(start[k] + fraction * (end[k] - start[k]) for k in range(3)))
        clipped = result
    return clipped


def clearance_results(model, opening, stop_degrees):
    """Return every nearby component/obstacle clearance, including below-leaf obstacles."""
    wall = model.wall(opening.host_wall)
    hinge, components = assembly_components(wall, opening)
    spec = opening.swing_assembly
    margin = spec.minimum_clearance.meters + spec.installation_allowance.meters
    sweeps = {c.name: swept_intervals(c, hinge, opening, stop_degrees) for c in components}
    envelopes = {name: unary_union([interval[2] for interval in intervals])
                 for name, intervals in sweeps.items()}
    tags = {element.uid: element.tag for element in model.plan.all_elements()}
    tags.update({solid.uid: solid.tag for solid in model.solids})
    results = []
    for element in model.geometry.elements:
        tag = tags.get(element.uid, tags.get(element.uid.split("::")[0],
                       tags.get(element.uid[:10], element.uid)))
        if tag == opening.host_wall or tag.startswith(opening.tag):
            continue
        for part in element.parts:
            for solid in part.solids:
                faces = list(solid_faces(solid))
                vertices = [point for face in faces for point in face]
                if not vertices:
                    continue
                z_min, z_max = min(p[2] for p in vertices), max(p[2] for p in vertices)
                for component in components:
                    if z_max < component.bottom_z_m - margin or z_min > component.top_z_m + margin:
                        continue
                    # Include the nearby part below/above the component, then use its true
                    # vertical gap. Intersecting faces are clipped before plan projection.
                    lower = max(z_min, component.bottom_z_m - margin)
                    upper = min(z_max, component.top_z_m + margin)
                    points = [p for face in faces for p in _clip_face(face, lower, upper)]
                    if not points:
                        continue
                    footprint = MultiPoint([(p[0], p[1]) for p in points]).convex_hull
                    if footprint.distance(envelopes[component.name]) > 12 * 0.0254:
                        continue
                    vertical_gap = max(0, component.bottom_z_m - z_max,
                                       z_min - component.top_z_m)
                    candidates = [(math.hypot(shape.distance(footprint), vertical_gap), a, b)
                                  for a, b, shape in sweeps[component.name]]
                    distance, start, end = min(candidates)
                    results.append(ClearanceResult(component.name, tag, part.key,
                                                   distance - spec.installation_allowance.meters,
                                                   (start, end)))
    return tuple(sorted(results, key=lambda result: result.clearance_m))
