"""Check sourced sill sections against the actual generated pan and its support."""
from dataclasses import replace

from shapely.geometry import LineString, Point, Polygon, box

from typehaus.resolve.doorway import DOORWAY
from typehaus.resolve.flashing_config import FLASHING


def coordinate_doorway_pans(model):
    from typehaus.resolve.opening_flashing import _pan_outlet, opening_flashing_frame

    walls = {w.tag: w for w in model.walls}
    openings = []
    for opening in model.openings:
        assembly = opening.doorway
        if assembly is None:
            openings.append(opening)
            continue
        wall = walls[opening.host_wall]
        frame = opening_flashing_frame(model, wall)
        conflicts, unknown = list(assembly.conflicts), list(assembly.unknown)
        for component in assembly.components:
            if component.specification.role not in ("sill", "track"):
                continue
            if frame is None:
                unknown.append(f"{component.specification.product_ref}: "
                               "pan/support section is missing")
                continue
            cfg = FLASHING
            outlet = _pan_outlet(opening, frame, cfg)
            dam = frame.back + cfg.back_dam_strip_m
            fall = (outlet - dam) * cfg.drainage_slope
            seat = assembly.rough_opening_z_m + frame.buck
            sign = -frame.along[1] * frame.outward[0] + frame.along[0] * frame.outward[1]
            spec = component.specification
            sections = [Polygon([(sign * (component.normal_m + spec.positive_normal_sign * x),
                                  component.base_z_m + z) for x, z in part.polygon_m])
                        for part in spec.parts]
            back_dam = box(frame.back, seat, dam + cfg.sill_membrane_m, seat + cfg.back_dam_m)
            support_edge = min(outlet, frame.mount)
            support = Polygon([(dam, seat), (support_edge, seat),
                               (support_edge, seat + (outlet - support_edge) * cfg.drainage_slope),
                               (dam, seat + fall)])
            membrane = LineString([(dam, seat + fall), (outlet, seat)])
            if any(s.intersection(back_dam).area > DOORWAY.height_tolerance_m ** 2
                   for s in sections):
                conflicts.append(f"{spec.product_ref}: sill intersects pan back dam")
            if any(s.intersection(support).area > DOORWAY.height_tolerance_m ** 2
                   for s in sections):
                conflicts.append(f"{spec.product_ref}: sill penetrates pan support")
            if any(s.intersection(membrane.buffer(cfg.sill_membrane_m / 2)).area
                   > DOORWAY.height_tolerance_m ** 2
                   for s in sections):
                conflicts.append(f"{spec.product_ref}: sill intersects drainage membrane")
            pan_half_width = opening.width_m / 2 - frame.buck - cfg.sill_membrane_m
            if abs(component.along_m) + component.span_m / 2 > pan_half_width:
                conflicts.append(f"{spec.product_ref}: sill exceeds pan clear width")
            lo, hi = component.normal_extent_m
            extents = sorted((sign * lo, sign * hi))
            if extents[1] > outlet:
                conflicts.append(f"{spec.product_ref}: sill extends beyond pan drainage outlet")
            if not spec.bearing_points_m:
                unknown.append(f"{spec.product_ref}: required bearing/shim contacts "
                               "are unspecified")
            for x, z in spec.bearing_points_m:
                point = Point(sign * (component.normal_m + spec.positive_normal_sign * x),
                              component.base_z_m + z)
                if min(s.boundary.distance(point) for s in sections) > DOORWAY.height_tolerance_m:
                    conflicts.append(f"{spec.product_ref}: bearing point lies outside the section")
                elif point.distance(support) > cfg.sill_membrane_m + DOORWAY.height_tolerance_m:
                    conflicts.append(f"{spec.product_ref}: documented bearing "
                                     "lacks modeled support")
        openings.append(replace(opening, doorway=replace(
            assembly, unknown=tuple(unknown), conflicts=tuple(conflicts))))
    model.openings = openings
