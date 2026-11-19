"""Wide outside corners and the C-Closure a kit ends its panel in under one (BBD75 p. 30).

Pure: reads walls and junctions, never solids, so the skin fold (which runs before the
corner trim) and the band trim share the corner's geometry.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass

from typehaus.library.trim.catalog import PROFILES
from typehaus.model.cladding_trim import CORNER_PROFILE_BY_KIT_PAIR, TrimCondition
from typehaus.quantities import M_PER_IN
from typehaus.resolve.cladding_trim.edges import _corner_face
from typehaus.resolve.cladding_trim.runs import cladding_face
from typehaus.resolve.metal_skin_profiles import SHEET_24_GA_M

_TOL = 1e-6
#: The panel's end clear of the C's web.
_PANEL_CLEAR_M = 0.125 * M_PER_IN
WIDE_CORNER_KEY = "WIDE_OUTSIDE_CORNER"


@dataclass(frozen=True)
class CornerClosure:
    """A C-Closure at one end of a wall's cladding layer, in that face's along stations.

    ``inward`` (+1/-1) points from the corner into the panel; the web stands on the other
    face's back plane and the return's lip ``lip_station`` is ``depth_m`` out.
    """

    wall_uid: str
    layer_name: str
    node_tag: str
    web_station: float
    lip_station: float
    depth_m: float
    inward: float


def closure_key(materials, layer) -> str | None:
    material = materials.get(layer.material_ref)
    return material.trim_kit.get(TrimCondition.CORNER_CLOSURE) if material else None


def closure_shape(key: str) -> tuple[float, float]:
    """(depth, web-to-lip) of a closure profile in metres, read off its section."""
    section = PROFILES[key].section_in
    depth = max(y for _, y in section)
    web = max(x for x, _ in section)
    return depth * M_PER_IN, (web - min(x for x, y in section if y == depth)) * M_PER_IN


def _kit(wall, materials):
    for layer in wall.layers:
        material = materials.get(layer.material_ref)
        if layer.function == "cladding" and material:
            key = material.trim_kit.get(TrimCondition.OUTSIDE_CORNER)
            if key:
                return key
    return None


def back_plane(layer, normal) -> float:
    """The layer's back plane offset along its outward ``normal``."""
    return min(x * normal[0] + y * normal[1] for x, y in layer.polygon)


def wide_corner_junctions(model):
    """(junction, walls, faces) for each convex wide-corner point, its lowest junction.

    A face is (layer, outward normal, corner plane offset): the layer's outer face, or its
    back plane plus the closure's depth where its kit ends the panel in a C-Closure.
    """
    materials = {material.tag: material for material in model.plan.library.materials}
    groups = defaultdict(list)
    for junction in model.junctions:
        if junction.kind != "l" or len(junction.incidents) != 2:
            continue
        walls = tuple(model.wall(incident.wall_tag) for incident in junction.incidents)
        if any(wall is None for wall in walls):
            continue
        keys = tuple(_kit(wall, materials) for wall in walls)
        if any(key is None for key in keys):
            continue
        chosen = keys[0] if keys[0] == keys[1] else CORNER_PROFILE_BY_KIT_PAIR.get(frozenset(keys))
        if chosen != WIDE_CORNER_KEY:
            continue
        faces = tuple(_corner_face(wall, incident, materials, key)
                      for wall, incident, key in zip(walls, junction.incidents, keys, strict=True))
        if any(face is None for face in faces):
            continue
        first, second = junction.incidents
        normal_a, normal_b = faces[0][1], faces[1][1]
        if (abs(sum(a * b for a, b in zip(first.direction, second.direction, strict=True))) > _TOL
                or sum(a * b for a, b in zip(normal_a, second.direction, strict=True)) >= -_TOL
                or sum(a * b for a, b in zip(normal_b, first.direction, strict=True)) >= -_TOL):
            continue
        faces = tuple(
            (layer, normal, back_plane(layer, normal) + closure_shape(key)[0])
            if (key := closure_key(materials, layer)) else (layer, normal, offset)
            for layer, normal, offset in faces)
        groups[tuple(round(value, 6) for value in junction.point)].append((junction, walls, faces))
    return [min(records, key=lambda r: min(wall.z0_m for wall in r[1]))
            for records in groups.values()]


def corner_side_walls(model, point, material_ref):
    """(wall, layer) for every wall ending at ``point`` clad in ``material_ref``."""
    out = []
    for wall in model.walls:
        if not any(math.dist(endpoint, point) < _TOL for endpoint in wall.axis):
            continue
        layer = next((layer for layer in wall.layers if layer.function == "cladding"
                      and layer.material_ref == material_ref), None)
        if layer is not None:
            out.append((wall, layer))
    return out


def corner_closures(model) -> list[CornerClosure]:
    materials = {material.tag: material for material in model.plan.library.materials}
    out = []
    for junction, _walls, faces in wide_corner_junctions(model):
        for index, (layer, _normal, _offset) in enumerate(faces):
            key = closure_key(materials, layer)
            if key is None:
                continue
            depth, lip = closure_shape(key)
            other_layer, other_normal, _ = faces[1 - index]
            other_back = back_plane(other_layer, other_normal)
            for wall, side_layer in corner_side_walls(model, junction.point, layer.material_ref):
                face = cladding_face(wall, side_layer)
                if face is None:
                    continue
                along = other_normal[0] * face.d[0] + other_normal[1] * face.d[1]
                if abs(along) < 1 - _TOL:
                    continue
                web, inward = other_back / along, -along
                out.append(CornerClosure(wall.uid, side_layer.name, junction.node_tag,
                                         web, web + inward * lip, depth, inward))
    return out


def closures_for(model, wall, layer_name) -> list[CornerClosure]:
    return [c for c in corner_closures(model)
            if c.wall_uid == wall.uid and c.layer_name == layer_name]


def corner_end_cuts(model, face, gap_m: float) -> list[tuple[float, float]]:
    """Station spans a run along ``face`` leaves to its wall's wide outside corners.

    A side ending in a C-Closure stops ``gap_m`` short of the return's lip, under the corner
    leg that rides the C; the other side stops at the corner trim's own leg edge. Each span
    runs past the face's end, so whatever lay beyond the corner is cut too.
    """
    from typehaus.resolve.cladding_corner import _intersection

    closures = {c.node_tag: c for c in closures_for(model, face.wall, face.layer.name)}
    section = PROFILES[WIDE_CORNER_KEY].section_in
    cuts = []
    for junction, walls, faces in wide_corner_junctions(model):
        if face.wall.uid not in {wall.uid for wall in walls}:
            continue
        closure = closures.get(junction.node_tag)
        if closure is not None:
            cuts.append((min(face.lo, closure.web_station), closure.lip_station + gap_m)
                        if closure.inward > 0 else
                        (closure.lip_station - gap_m, max(face.hi, closure.web_station)))
            continue
        (da, db) = (incident.direction for incident in junction.incidents)
        x, y = _intersection(faces[0][1], faces[1][1], faces[0][2], faces[1][2])
        stations = [(x + u * M_PER_IN * da[0] + v * M_PER_IN * db[0]) * face.d[0]
                    + (y + u * M_PER_IN * da[1] + v * M_PER_IN * db[1]) * face.d[1]
                    for u, v in section]
        apex = x * face.d[0] + y * face.d[1]
        lo, hi = min(stations), max(stations)
        cuts.append((min(face.lo, lo), hi) if apex - lo < hi - apex
                    else (lo, max(face.hi, hi)))
    return cuts


def clear_of_closures(wall, layer, closures):
    """``layer.polygon`` drawn short of each closure's web: the panel stops inside the C."""
    face = cladding_face(wall, layer) if closures else None
    if face is None:
        return layer.polygon
    polygon = list(layer.polygon)
    for c in closures:
        limit = c.web_station + c.inward * (SHEET_24_GA_M + _PANEL_CLEAR_M)
        for i, (x, y) in enumerate(polygon):
            shift = limit - (x * face.d[0] + y * face.d[1])
            if shift * c.inward > 0:
                polygon[i] = (x + shift * face.d[0], y + shift * face.d[1])
    return tuple(polygon)
