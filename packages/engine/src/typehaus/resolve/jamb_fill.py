"""Local door-jamb backing and cavity replacements, derived from actual stud bays.

The first clear bay outside each jamb pack ends at real framing, including corner
and tee studs. Solid packs at a wall end have no cavity to foam or block.
"""
from dataclasses import dataclass, replace

from shapely.geometry import Polygon, box

from typehaus.model.door_hardware import HARDWARE_BLOCKING_ANCHOR_ROLES
from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.geometry import add, pocket_centerline_offset, scale, wall_frame
from typehaus.resolve.geometry_walls import wall_top_at
from typehaus.resolve.model import FramedMember
from typehaus.resolve.overlay import difference, union_all

_EPS = 1e-8
_SEAM_PROBE_M = .001


@dataclass(frozen=True)
class ResolvedJambFill:
    opening_tag: str
    host_wall: str
    bay_polygon: tuple[tuple[float, float], ...]  # station / elevation, metres
    depth_m: float
    material_ref: str
    replaced_material_ref: str
    replaced_layer: str
    voids: tuple[tuple[tuple[float, float], ...], ...] = ()

    @property
    def area_m2(self):
        return Polygon(self.bay_polygon, self.voids).area


def _member_band(member, origin, tangent):
    ring, bottom, top = member_footprint(member)
    stations = [sum((point[i] - origin[i]) * tangent[i] for i in (0, 1))
                for point in ring]
    return box(min(stations), bottom, max(stations), top)


def _remove_replaced_tee_backing(model):
    """Full-height doubled kings replace intersecting finish-only ladder rungs."""
    types = {item.tag: item for item in model.plan.library.door_types}
    hardened_tags = {opening.tag for opening in model.openings
                      if opening.is_door and opening.type_ref in types
                      and types[opening.type_ref].jamb_framing}
    kings = [(Polygon(ring), low, high) for wall in model.walls
             for member in wall.members
             if member.category == "king" and member.opening_tag in hardened_tags
             for ring, low, high in [member_footprint(member)]]
    for index, wall in enumerate(model.walls):
        retained = []
        for member in wall.members:
            if member.category == "door_blocking" and member.opening_tag in hardened_tags:
                continue
            if member.category == "blocking" and member.child_key.startswith("tee-"):
                ring, low, high = member_footprint(member)
                if any(min(high, top) > max(low, bottom) + _EPS
                       and Polygon(ring).intersection(polygon).area > _EPS
                       for polygon, bottom, top in kings):
                    continue
            retained.append(member)
        model.walls[index] = replace(wall, members=tuple(retained))


def _bay_host(model, wall, station, side):
    """Continue across a collinear authored seam, never across a corner or a gap."""
    origin, tangent, normal, run = wall_frame(wall)
    if _EPS < station < run - _EPS:
        return wall, station, side
    point = add(origin, scale(tangent, station))
    for neighbor in model.walls:
        if neighbor.tag == wall.tag or neighbor.storey != wall.storey:
            continue
        if neighbor.assembly != wall.assembly:
            continue
        other_origin, other_tangent, _other_normal, other_run = wall_frame(neighbor)
        parallel = sum(a*b for a, b in zip(tangent, other_tangent, strict=True))
        if abs(abs(parallel)-1) > _EPS:
            continue
        offset = sum((other_origin[i]-origin[i])*normal[i] for i in (0, 1))
        if abs(offset) > _EPS:
            continue
        other_station = sum((point[i]-other_origin[i])*other_tangent[i] for i in (0, 1))
        other_side = side * (1 if parallel > 0 else -1)
        if (-_EPS <= other_station <= other_run + _EPS
                and _EPS < other_station + other_side * _SEAM_PROBE_M < other_run - _EPS):
            return neighbor, other_station, other_side
    return wall, station, side


def resolve_jamb_fills(model):
    """Frame hardware backing first, then deduct its solid area from the foam bays."""
    types = {item.tag: item for item in model.plan.library.door_types}
    model.jamb_fills = []
    _remove_replaced_tee_backing(model)
    for index, wall in enumerate(model.walls):
        openings = [(opening, types.get(opening.type_ref)) for opening in model.openings
                    if opening.host_wall == wall.tag and opening.is_door]
        openings = [(opening, spec) for opening, spec in openings
                    if spec and spec.jamb_framing]
        if not openings:
            continue
        structure = next((layer for layer in wall.layers
                          if layer.function == "structure" and not layer.is_cavity), None)
        if structure is None:
            continue  # The integrity rule reports an incompatible host.
        origin, tangent, _normal, run = wall_frame(wall)
        members = list(wall.members)
        vertical = [(_member_band(member, origin, tangent), member)
                    for member in members if member.category in
                    {"stud", "king", "jack", "corner"}]
        for opening, spec in openings:
            framing = spec.jamb_framing
            king = next((member for _, member in vertical
                         if member.category == "king"), None)
            profile = king.profile if king else None
            if profile is None:
                continue
            section = cross_section(profile)
            thickness = section.width_m
            bottom = wall.base_ref_z_m + opening.sill_m
            top = bottom + opening.height_m
            leaf_bottom = (opening.doorway.leaf_bottom_z_m if opening.doorway
                           and opening.doorway.leaf_bottom_z_m is not None else bottom)
            for side in (-1, 1):
                edge = opening.center_along_m + side * (
                    opening.width_m / 2 + (framing.kings + framing.jacks) * thickness)
                bay_wall, edge, bay_side = _bay_host(model, wall, edge, side)
                bay_origin, bay_tangent, bay_normal, bay_run = wall_frame(bay_wall)
                bay_members = members if bay_wall.tag == wall.tag else list(bay_wall.members)
                bay_vertical = [(_member_band(member, bay_origin, bay_tangent), member)
                                for member in bay_members if member.category in
                                {"stud", "king", "jack", "corner"}]
                candidates = [band.bounds[2 if bay_side < 0 else 0]
                              for band, _member in bay_vertical
                              if band.bounds[1] < top and band.bounds[3] > bottom
                              and (band.bounds[2] <= edge + _EPS if bay_side < 0
                                   else band.bounds[0] >= edge - _EPS)]
                far = (max(candidates, default=0) if bay_side < 0
                       else min(candidates, default=bay_run))
                low, high = sorted((max(0, min(edge, bay_run)), far))
                if high - low <= _EPS:
                    continue
                if any(band.bounds[0] < edge - _EPS and band.bounds[2] > edge + _EPS
                       for band, _member in bay_vertical):
                    continue
                if framing.blocking:
                    heights = sorted({item.height.meters for item in spec.hardware
                                      if item.height is not None
                                      and item.role in HARDWARE_BLOCKING_ANCHOR_ROLES})
                    for number, height in enumerate(heights):
                        z = leaf_bottom + height
                        offset_origin = add(bay_origin, scale(bay_normal,
                                            pocket_centerline_offset(bay_wall)))
                        p0, p1 = (add(offset_origin, scale(bay_tangent, station))
                                  for station in (low, high))
                        bay_members.append(FramedMember(
                            bay_wall.uid, f"door-block-{opening.tag}-{side}-{number}",
                            "door_blocking", profile, p0, p1,
                            z - thickness / 2, z + thickness / 2, high - low,
                            opening_tag=opening.tag, material=king.material))
                if bay_wall.tag == wall.tag:
                    members = bay_members
                else:
                    bay_index = next(i for i, item in enumerate(model.walls)
                                     if item.tag == bay_wall.tag)
                    model.walls[bay_index] = replace(bay_wall, members=tuple(bay_members))
                bay_cavity = next((layer for layer in bay_wall.layers if layer.is_cavity), None)
                if not framing.bay_fill_ref or bay_cavity is None:
                    continue
                occupied = union_all([_member_band(member, bay_origin, bay_tangent)
                                        for member in bay_members])
                occupied = union_all([occupied, *(Polygon(fill.bay_polygon, fill.voids)
                                       for fill in model.jamb_fills
                                       if fill.host_wall == bay_wall.tag)])
                bay_base = bay_wall.base_ref_z_m
                p_low, p_high = (add(bay_origin, scale(bay_tangent, station))
                                 for station in (low, high))
                bay = Polygon([(low, bay_base), (high, bay_base),
                               (high, wall_top_at(bay_wall, *p_high)),
                               (low, wall_top_at(bay_wall, *p_low))])
                clear = difference(bay, occupied)
                polygons = [clear] if clear.geom_type == "Polygon" else list(clear.geoms)
                for polygon in polygons:
                    if polygon.area > _EPS:
                        model.jamb_fills.append(ResolvedJambFill(
                            opening.tag, bay_wall.tag, tuple(polygon.exterior.coords[:-1]),
                            bay_cavity.thickness_m, framing.bay_fill_ref,
                            bay_cavity.material_ref, bay_cavity.name,
                            tuple(tuple(ring.coords[:-1]) for ring in polygon.interiors)))
        model.walls[index] = replace(wall, members=tuple(members))
