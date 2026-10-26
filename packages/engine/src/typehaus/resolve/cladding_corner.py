"""Meet unequal-depth claddings at their actual outer-face intersection.

An angular bisector joins equal-depth strips. With a 3/4-inch skin meeting a
1-1/4-inch skin it leaves a triangular gap and extends the thicker wall past the
thinner facade. The cut instead connects the intersections of their two face pairs.
"""

from __future__ import annotations

from dataclasses import replace

CORNER_TOLERANCE_M = 1e-9


def _intersection(first, second, first_offset, second_offset):
    ax, ay = first
    bx, by = second
    determinant = ax * by - ay * bx
    if abs(determinant) < CORNER_TOLERANCE_M:
        raise ValueError("Cladding mitre requires intersecting wall faces")
    return (
        (first_offset * by - ay * second_offset) / determinant,
        (ax * second_offset - first_offset * bx) / determinant,
    )


def _clip(ring, origin, normal, direction):
    sign = 1 if sum(a * b for a, b in zip(normal, direction, strict=True)) > 0 else -1

    def distance(p):
        return sign * sum((p[i] - origin[i]) * normal[i] for i in range(2))

    result = []
    for a, b in zip(ring, ring[1:] + ring[:1], strict=True):
        da, db = distance(a), distance(b)
        if da >= -CORNER_TOLERANCE_M:
            result.append(a)
        if (da < -CORNER_TOLERANCE_M and db > CORNER_TOLERANCE_M) or (
            db < -CORNER_TOLERANCE_M and da > CORNER_TOLERANCE_M
        ):
            t = da / (da - db)
            result.append(tuple(a[i] + t * (b[i] - a[i]) for i in range(2)))
    return result


def meet_cladding_faces(walls, junction, unclipped):
    first, second = junction.incidents
    if first.wall_tag not in walls or second.wall_tag not in walls:
        return
    pairs = []
    for incident in (first, second):
        wall = walls[incident.wall_tag]
        layers = {
            layer.name: (index, layer)
            for index, layer in enumerate(wall.layers)
            if layer.function == "cladding"
        }
        dx, dy = incident.direction
        normal = (-dy, dx)

        def across(p, normal=normal):
            return sum((p[i] - junction.point[i]) * normal[i] for i in range(2))

        inner = sum(across(p) for p in wall.layers[0].polygon) / len(wall.layers[0].polygon)
        outer = sum(across(p) for p in wall.layers[-1].polygon) / len(wall.layers[-1].polygon)
        if outer < inner:
            normal = tuple(-v for v in normal)
        pairs.append((wall, layers, normal))
    (wall_a, layers_a, normal_a), (wall_b, layers_b, normal_b) = pairs
    for name in layers_a.keys() & layers_b.keys():
        index_a, layer_a = layers_a[name]
        index_b, layer_b = layers_b[name]
        if abs(layer_a.thickness_m - layer_b.thickness_m) <= CORNER_TOLERANCE_M:
            continue
        offsets = []
        for wall, index, normal in ((wall_a, index_a, normal_a), (wall_b, index_b, normal_b)):
            values = [
                sum((p[i] - junction.point[i]) * normal[i] for i in range(2))
                for p in unclipped[wall.tag][index]
            ]
            offsets.append((min(values), max(values)))
        inner = _intersection(normal_a, normal_b, offsets[0][0], offsets[1][0])
        outer = _intersection(normal_a, normal_b, offsets[0][1], offsets[1][1])
        origin = tuple(junction.point[i] + inner[i] for i in range(2))
        normal = (inner[1] - outer[1], outer[0] - inner[0])
        for incident, wall, index in ((first, wall_a, index_a), (second, wall_b, index_b)):
            polygon = _clip(unclipped[wall.tag][index], origin, normal, incident.direction)
            if len(polygon) < 3:
                raise ValueError(f"{wall.tag}: cladding mitre removed its layer")
            layers = list(walls[wall.tag].layers)
            layers[index] = replace(layers[index], polygon=polygon)
            walls[wall.tag] = replace(walls[wall.tag], layers=tuple(layers))
