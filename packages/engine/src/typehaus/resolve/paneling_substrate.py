"""Replace finish locally with real substrate solids while preserving the finished plane."""

from dataclasses import replace

from shapely.geometry import Polygon

from typehaus.resolve.geometry import wall_frame
from typehaus.resolve.layer_pockets import subtract_layer_region


def add_paneling_substrates(model, element, panel):
    """Each substrate bills once; removed finish no longer exists behind the band."""
    wall = next(wall for wall in model.walls if wall.tag == panel.wall_tag)
    origin, tangent, normal, _ = wall_frame(wall)
    tx, ty = tangent
    nx, ny = normal
    face_shape = Polygon(panel.outline)
    candidates = [layer for layer in wall.layers if layer.function == "finish" and layer.polygon]
    layer = min(candidates, key=lambda layer: Polygon(layer.polygon).distance(face_shape))
    stations = [(x - origin[0]) * tx + (y - origin[1]) * ty for x, y in panel.outline]
    start, end = min(stations), max(stations)
    # Cut through the complete original layer, including its back, rather than covering wood.
    offsets = [(x - origin[0]) * nx + (y - origin[1]) * ny for x, y in layer.polygon]
    inward, outward = min(offsets), max(offsets)
    def point(u, v):
        return origin[0] + tx * u + nx * v, origin[1] + ty * u + ny * v
    cutter = Polygon([point(start, inward - 1), point(end, inward - 1),
                      point(end, outward + 1), point(start, outward + 1)])
    replacements = subtract_layer_region(wall, layer, cutter, panel.z0_m, panel.z1_m,
                                         element.tag)
    index = wall.layers.index(layer)
    wall = replace(wall, layers=(*wall.layers[:index], *replacements, *wall.layers[index + 1:]))
    model.walls[next(i for i, entry in enumerate(model.walls) if entry.tag == wall.tag)] = wall
    model.panelings[model.panelings.index(panel)] = replace(
        panel, finish_replaced_in_geometry=True)
    # Panel outer face is invariant. Shift every backing solid away from the room.
    cx = sum(x for x, _ in panel.outline) / len(panel.outline)
    cy = sum(y for _, y in panel.outline) / len(panel.outline)
    side = 1 if (cx - origin[0]) * nx + (cy - origin[1]) * ny > 0 else -1
    consumed = panel.thickness_m
    for index, substrate in enumerate(element.substrates):
        thickness = substrate.thickness.meters
        # Map the tile's four corners to a band immediately behind the preceding layer.
        offsets = [(x - origin[0]) * nx + (y - origin[1]) * ny for x, y in panel.outline]
        face_offset = max(offsets) if side > 0 else min(offsets)
        def ring(source, face_offset=face_offset, consumed=consumed, thickness=thickness):
            result = []
            for x, y in source:
                offset = (x - origin[0]) * nx + (y - origin[1]) * ny
                on_face = abs(offset - face_offset) < 1e-7
                target = face_offset - side * (consumed if on_face else consumed + thickness)
                result.append((x + nx * (target - offset), y + ny * (target - offset)))
            return result
        model.panelings.append(replace(
            panel, tag=f"{element.tag}-substrate-{index}", material_ref=substrate.material_ref,
            outline=ring(panel.outline), thickness_m=thickness, replaces_wall_finish=False,
            pieces=tuple((ring(outline), bottom, top) for outline, bottom, top in panel.pieces)))
        consumed += thickness
