"""Continuous outside corners where different panel kits meet."""

from __future__ import annotations

import math
from collections import defaultdict

from typehaus.library.trim.metal_sales import WIDE_OUTSIDE_CORNER
from typehaus.model.cladding_trim import CORNER_PROFILE_BY_KIT_PAIR, TrimCondition
from typehaus.quantities import M_PER_IN
from typehaus.resolve.cladding_corner import _intersection
from typehaus.resolve.cladding_trim.edges import _corner_face
from typehaus.resolve.cladding_trim.members import split_stock_run
from typehaus.resolve.cladding_trim.section import folded_section_mesh
from typehaus.resolve.geometry_ir import GMesh
from typehaus.resolve.geometry_walls import wall_top_at
from typehaus.resolve.metal_skin_profiles import SHEET_24_GA_M
from typehaus.resolve.model import ResolvedSolid
from typehaus.resolve.roof_image_ii_eave import LAP_GAP_M, capped_z, roof_head_caps

_TOL = 1e-6
_PROFILE_KEY = "WIDE_OUTSIDE_CORNER"
#: How far outside a gutter's plan box a corner may stand and still sit behind its back.
_NOTCH_REACH_M = 0.25 * M_PER_IN


def _selected_kit(wall, materials):
    for layer in wall.layers:
        material = materials.get(layer.material_ref)
        if layer.function == "cladding" and material:
            key = material.trim_kit.get(TrimCondition.OUTSIDE_CORNER)
            if key:
                return layer, key
    return None


def _closure_top(model, wall, point, direction):
    """Highest roof closure belonging to this wall at the corner station."""
    tops = []
    for roof in model.roofs:
        for member in roof.members:
            if member.parent_uid != wall.uid or member.category != "cladding":
                continue
            a = sum((member.p0[i] - point[i]) * direction[i] for i in range(2))
            b = sum((member.p1[i] - point[i]) * direction[i] for i in range(2))
            if min(a, b) - _TOL <= 0 <= max(a, b) + _TOL and abs(b - a) > _TOL:
                fraction = (0 - a) / (b - a)
                end = member.z1_m if member.z1_end_m is None else member.z1_end_m
                tops.append(member.z1_m + fraction * (end - member.z1_m))
    return max(tops, default=None)


def resolve_mixed_corners(model) -> None:
    materials = {material.tag: material for material in model.plan.library.materials}
    groups = defaultdict(list)
    for junction in model.junctions:
        if junction.kind != "l" or len(junction.incidents) != 2:
            continue
        walls = tuple(model.wall(incident.wall_tag) for incident in junction.incidents)
        if any(wall is None for wall in walls):
            continue
        selected = tuple(_selected_kit(wall, materials) for wall in walls)
        if any(item is None for item in selected):
            continue
        keys = tuple(item[1] for item in selected)
        chosen = keys[0] if keys[0] == keys[1] else CORNER_PROFILE_BY_KIT_PAIR.get(frozenset(keys))
        if chosen != _PROFILE_KEY:
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
        point_key = tuple(round(value, 6) for value in junction.point)
        groups[point_key].append((junction, walls, faces))

    profile = WIDE_OUTSIDE_CORNER
    section = tuple((x * M_PER_IN, y * M_PER_IN) for x, y in profile.section_in)
    for records in groups.values():
        records.sort(key=lambda record: min(wall.z0_m for wall in record[1]))
        junction, walls, faces = records[0]
        directions = tuple(incident.direction for incident in junction.incidents)
        x, y = _intersection(faces[0][1], faces[1][1], faces[0][2], faces[1][2])
        # Walk all cladding at the same corner, including a gable wall without a
        # matching wall on the adjacent eave and the eave's roof closure band.
        lows, highs = [], []
        for face_index, direction in enumerate(directions):
            material_key = faces[face_index][0].material_ref
            side_walls = []
            for wall in model.walls:
                if not any(math.dist(endpoint, junction.point) < _TOL for endpoint in wall.axis):
                    continue
                layer = next((layer for layer in wall.layers if layer.function == "cladding"
                              and layer.material_ref == material_key), None)
                if layer is not None:
                    side_walls.append((wall, layer))
            if not side_walls:
                break
            lows.append(min(layer.band(wall)[0] for wall, layer in side_walls))
            tops = [min(layer.band(wall)[1], wall_top_at(wall, *junction.point))
                    for wall, layer in side_walls]
            if not any(wall.top_z0_m is not None for wall, _ in side_walls):
                tops.extend(
                    top for wall, _ in side_walls
                    if (top := _closure_top(model, wall, junction.point, direction)) is not None
                )
            highs.append(max(tops))
        if len(lows) != 2:
            continue
        # Run to the higher meeting edge: the rake-side gable reaches the roof
        # above the eave closure, and the corner must terminate against that edge.
        z0, z1 = max(lows), max(highs)
        if z1 - z0 <= _TOL:
            continue
        caps = tuple(cap for roof in model.roofs for cap in roof_head_caps(model, roof))
        # Under a wrapped eave the run stops level at the head cap, as the eave wall head does.
        corner_points = [(x + u * directions[0][0] + v * directions[1][0],
                          y + u * directions[0][1] + v * directions[1][1])
                         for u, v in section]
        z1 = min(capped_z(caps, px, py, z1) for px, py in corner_points)
        if z1 - z0 <= _TOL:
            continue
        notch = _gutter_notch(model, (x, y), faces)
        for index, (start, end, stock) in enumerate(split_stock_run(
                z1 - z0, tuple(length * M_PER_IN for length in profile.stock_lengths_in),
                profile.min_lap_in * M_PER_IN)):
            # Upper pieces sit outboard of the lower piece at a shingled lap.
            offset = index * SHEET_24_GA_M
            origin = (x + offset * (faces[0][1][0] + faces[1][1][0]),
                      y + offset * (faces[0][1][1] + faces[1][1][1]))
            mesh = _corner_mesh(section, origin, directions, z0 + start, z0 + end,
                                notch, offset, caps)
            xs, ys, zs = zip(*mesh.positions, strict=True)
            model.solids.append(ResolvedSolid(
                uid=f"{junction.node_tag}-wide-corner-{index}",
                tag=f"TRIM-{junction.node_tag}-WIDE-CORNER-{index + 1}",
                storey=junction.storey, category="cladding_trim",
                outline=((min(xs), min(ys)), (max(xs), min(ys)),
                         (max(xs), max(ys)), (min(xs), max(ys))),
                z0_m=min(zs), z1_m=max(zs), material=faces[0][0].material_ref,
                product=_PROFILE_KEY, body_mesh=mesh, host_ref=junction.node_tag,
                trim_length_m=end - start, trim_stock_length_in=round(stock / M_PER_IN, 6)))


def _gutter_notch(model, point, faces):
    """(z, face index) where a gutter's back stands outboard of one face at this corner:
    that face's leg stops at ``z``, below the trough, and the other leg ends at its plane."""
    for solid in model.solids:
        if solid.category != "gutter":
            continue
        xs = [p[0] for p in solid.outline]
        ys = [p[1] for p in solid.outline]
        if not (min(xs) - _NOTCH_REACH_M <= point[0] <= max(xs) + _NOTCH_REACH_M
                and min(ys) - _NOTCH_REACH_M <= point[1] <= max(ys) + _NOTCH_REACH_M):
            continue
        middle = ((min(xs) + max(xs)) / 2 - point[0], (min(ys) + max(ys)) / 2 - point[1])
        for index, face in enumerate(faces):
            if middle[0] * face[1][0] + middle[1] * face[1][1] > 0:
                return solid.z0_m - LAP_GAP_M, index
    return None


def _corner_mesh(section, origin, directions, bottom, top, notch, offset, caps) -> GMesh:
    """One piece: the full section below a gutter notch, the far leg alone above it, its
    top level under the eave head caps (the rake's face leg drops below the cap inboard)."""
    pieces = [(bottom, top, section)]
    if notch is not None and notch[0] < top:
        z, face = notch
        # Leg ``i`` runs along ``directions[i]`` (section coordinate ``i``) on face ``i``.
        keep = 1 - face
        # The kept leg (its points have coordinate ``face`` zero), its fold moved along it
        # to the notched face's plane.
        leg = tuple(tuple(offset if i == keep and point[keep] == 0.0 else c
                          for i, c in enumerate(point))
                    for point in section if point[face] == 0.0)
        pieces = ([(bottom, z, section)] if z > bottom + _TOL else []) + [
            (max(bottom, z), top, leg)]
    positions, triangles = [], []
    for z0, z1, ring in pieces:
        mesh = folded_section_mesh(ring, (*origin, z0), (*directions[0], 0.0),
                                   (*directions[1], 0.0), (0.0, 0.0, z1 - z0), SHEET_24_GA_M)
        # Level, at the lowest cap any of its top corners stands under.
        cap = min(capped_z(caps, px, py, pz) for px, py, pz in mesh.positions
                  if pz > z1 - _TOL)
        base = len(positions)
        positions.extend((px, py, min(pz, cap)) for px, py, pz in mesh.positions)
        triangles.extend(tuple(i + base for i in tri) for tri in mesh.triangles)
    return GMesh(tuple(positions), tuple(triangles))
