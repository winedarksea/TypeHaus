"""Check declared mounting-post centres against emitted wood on the mounting face."""

import math

from shapely.geometry import Point, Polygon

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, advisory, not_applicable, passed
from typehaus.model.enums import LayerFunction
from typehaus.model.placeable_symbols import place_local
from typehaus.model.placeables import MountKind
from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.model import FramedMember, ResolvedWall

_EPSILON_M = 1e-7
_WOOD_CATEGORIES = frozenset({"stud", "corner", "king", "jack", "cripple", "blocking"})


def fixing_support(wall: ResolvedWall, face: str, fixing_xy: tuple[float, float],
                   fixing_z: float) -> list[FramedMember]:
    """Members containing the post's projection just inside the selected stud face.

    Casting to the selected face keeps a block in the opposite staggered row from
    claiming support. There is no one-inch coverage tolerance for a discrete fixing.
    """
    start, end = wall.axis
    length = math.dist(start, end)
    if length <= _EPSILON_M:
        return []
    tangent = ((end[0] - start[0]) / length, (end[1] - start[1]) / length)
    normal = (-tangent[1], tangent[0])
    structure = next((layer for layer in wall.layers
                      if layer.function == LayerFunction.STRUCTURE.value
                      and not layer.is_cavity and layer.polygon), None)
    if structure is None:
        return []
    offsets = [(point[0] - start[0]) * normal[0] + (point[1] - start[1]) * normal[1]
               for point in structure.polygon]
    offset = (max(offsets) - _EPSILON_M if face == "left"
              else min(offsets) + _EPSILON_M)
    station = ((fixing_xy[0] - start[0]) * tangent[0]
               + (fixing_xy[1] - start[1]) * tangent[1])
    point = Point(start[0] + tangent[0] * station + normal[0] * offset,
                  start[1] + tangent[1] * station + normal[1] * offset)
    supported = []
    for member in wall.members:
        if member.category not in _WOOD_CATEGORIES:
            continue
        outline, bottom, top = member_footprint(member)
        if (bottom - _EPSILON_M <= fixing_z <= top + _EPSILON_M
                and Polygon(outline).buffer(_EPSILON_M).covers(point)):
            supported.append(member)
    return supported


@check(Tier.ADVISORY, "advisory.wall_fixing_support")
def wall_fixing_support(ctx: CheckContext) -> list[Finding]:
    types = {item.tag: item for item in ctx.plan.library.furniture_types
             if item.wall_fixing_points}
    walls = {wall.tag: wall for wall in ctx.model.walls}
    out = []
    for obj in ctx.model.canvas_objects:
        product = types.get(obj.type_ref or "")
        if (product is None or obj.kind != "Furniture" or obj.host_fixture_ref is not None
                or obj.mount is None or obj.mount.kind is not MountKind.WALL):
            continue
        wall = walls.get(obj.attachment_wall or "")
        if wall is None or obj.attachment_face not in {"left", "right"}:
            out.append(advisory("advisory.wall_fixing_support",
                                f"{obj.tag} declares post centres but no resolved wall face",
                                (obj.tag,), Result.UNKNOWN))
            continue
        depth = product.footprint[1].meters
        for index, (width_offset, height_offset) in enumerate(product.wall_fixing_points, 1):
            xy = place_local([(width_offset.meters, depth / 2)],
                             obj.position, obj.rotation_degrees)[0]
            support = fixing_support(wall, obj.attachment_face, xy,
                                      obj.z_m + height_offset.meters)
            tags = (obj.tag, wall.tag)
            if support:
                out.append(passed("advisory.wall_fixing_support",
                                  f"{obj.tag} post {index} lands on "
                                  + ", ".join(member.child_key for member in support), tags))
            else:
                out.append(advisory("advisory.wall_fixing_support",
                                    f"{obj.tag} post {index} misses studs and backing on "
                                    f"the {obj.attachment_face} face of {wall.tag}",
                                    tags, Result.FAIL))
    return out or [not_applicable("advisory.wall_fixing_support",
                                  "no wall-mounted furnishings declare mounting-post centres")]
