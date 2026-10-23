"""Extend resolved finish polygons into reveals; existing exports and takeoff share them."""
from dataclasses import replace

from shapely.geometry import Polygon

from typehaus.resolve.doorway import DOORWAY
from typehaus.resolve.geometry import opening_center, wall_frame
from typehaus.resolve.geometry_door_products import finish_faces
from typehaus.resolve.overlay import union_all
from typehaus.resolve.room_finish import finish_parts


def _geometry(parts):
    return union_all([Polygon(outline, holes=list(holes)) for outline, holes in parts])


def extend_doorway_finishes(model):
    rooms = {room.tag: room for room in model.rooms}
    walls = {wall.tag: wall for wall in model.walls}
    for opening in model.openings:
        assembly = opening.doorway
        if assembly is None or any(f is None or f.surface_m is None
                                   for f in assembly.adjacent_floors):
            continue
        if assembly.conflicts:
            continue
        # A raised access opening does not pull the floor up to its rough sill.
        if assembly.rough_opening_z_m > min(f.surface_m for f in assembly.adjacent_floors
                                           ) + DOORWAY.height_tolerance_m:
            continue
        wall = walls[opening.host_wall]
        faces = finish_faces(wall)
        if faces is None:
            continue
        center = opening_center(wall, opening)
        _, tangent, normal, _ = wall_frame(wall)
        half = opening.width_m / 2
        if opening.cased_product:
            half -= opening.cased_product.jamb_allowance_m
        bounds = [assembly.joint_normal_m, assembly.joint_normal_m]
        for component in assembly.components:
            if component.specification.role not in ("sill", "track", "transition"):
                continue
            lo, hi = component.finish_extent_m
            gaps = component.specification.expansion_gap_m
            if component.specification.positive_normal_sign < 0:
                gaps = gaps[::-1]
            bounds[0] = min(bounds[0], lo - gaps[0])
            bounds[1] = max(bounds[1], hi + gaps[1])
        for index, floor in enumerate(assembly.adjacent_floors):
            room = rooms.get(floor.room_tag)
            if room is None or floor.finish_ref is None:
                continue
            lo, hi = (faces[0], bounds[0]) if index == 0 else (bounds[1], faces[1])
            if hi <= lo:
                continue
            ring = [(center[0] + tangent[0] * along + normal[0] * offset,
                     center[1] + tangent[1] * along + normal[1] * offset)
                    for along, offset in ((-half, lo), (half, lo), (half, hi), (-half, hi))]
            patch = Polygon(ring)
            zones = list(room.finish_zones)
            zone_index = next((i for i, z in enumerate(zones)
                               if z.material_ref == floor.finish_ref
                               and Polygon(z.outline).distance(patch)
                               <= DOORWAY.floor_probe_m), None)
            if zone_index is not None:
                zone = zones[zone_index]
                combined = union_all([_geometry(zone.parts), patch])
                zones[zone_index] = replace(zone, parts=finish_parts(combined),
                                            area_m2=combined.area)
                room = replace(room, finish_zones=tuple(zones))
            elif floor.finish_ref == room.floor_finish:
                combined = union_all([_geometry(room.field_finish), patch])
                room = replace(room, field_finish=finish_parts(combined),
                               field_area_m2=combined.area)
            rooms[room.tag] = room
    model.rooms = [rooms[r.tag] for r in model.rooms]
