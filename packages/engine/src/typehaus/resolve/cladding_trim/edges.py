"""Resolve corrugated outside corners at exterior wall junctions."""

from __future__ import annotations

import math

from typehaus.library.trim.metal_sales import CORRUGATED_OUTSIDE_CORNER
from typehaus.model.cladding_trim import TrimCondition
from typehaus.quantities import M_PER_IN
from typehaus.resolve.cladding_corner import _intersection
from typehaus.resolve.cladding_trim.members import split_stock_run
from typehaus.resolve.cladding_trim.section import folded_section_mesh
from typehaus.resolve.metal_skin_profiles import SHEET_24_GA_M
from typehaus.resolve.model import ResolvedSolid

_KEY = "CORRUGATED_OUTSIDE_CORNER"
_TOLERANCE = 1e-7


def _corner_face(wall, incident, materials, expected_key=_KEY):
    """Return the exterior plane and cladding layer for a participating wall."""
    layer = next((layer for layer in wall.layers
                  if layer.function == "cladding" and layer.material_ref in materials
                  and materials[layer.material_ref].trim_kit.get(TrimCondition.OUTSIDE_CORNER)
                  == expected_key), None)
    if layer is None:
        return None
    dx, dy = incident.direction
    normal = (-dy, dx)
    inner = sum(x * normal[0] + y * normal[1] for x, y in wall.layers[0].polygon)
    inner /= len(wall.layers[0].polygon)
    outer = sum(x * normal[0] + y * normal[1] for x, y in layer.polygon)
    outer /= len(layer.polygon)
    if outer < inner:
        normal = (-normal[0], -normal[1])
    offset = max(x * normal[0] + y * normal[1] for x, y in layer.polygon)
    return layer, normal, offset


def resolve_corrugated_corners(model) -> None:
    """Attach one stock-split corner at each convex corrugated wall junction.

    Mixed-profile and stacked multi-storey corners need their own continuous run
    consolidation; this pass only handles two single-storey corrugated faces.
    """
    materials = {material.tag: material for material in model.plan.library.materials}
    profile = CORRUGATED_OUTSIDE_CORNER
    section = tuple((x * M_PER_IN, y * M_PER_IN) for x, y in profile.section_in)
    for junction in model.junctions:
        if junction.kind != "l" or len(junction.incidents) != 2:
            continue
        first, second = junction.incidents
        walls = (model.wall(first.wall_tag), model.wall(second.wall_tag))
        if any(wall is None for wall in walls):
            continue
        faces = tuple(_corner_face(wall, incident, materials)
                      for wall, incident in zip(walls, (first, second), strict=True))
        if any(face is None for face in faces):
            continue
        # A corner that continues through another storey must be procured as one
        # continuous run, not restarted at each storey with extra stock and laps.
        if any(other.storey != junction.storey
               and math.dist(other.point, junction.point) < _TOLERANCE
               and other.kind == "l"
               and len(other.incidents) == 2
               and all((wall := model.wall(incident.wall_tag)) is not None
                       and _corner_face(wall, incident, materials) is not None
                       for incident in other.incidents)
               for other in model.junctions):
            continue
        (layer_a, normal_a, offset_a), (layer_b, normal_b, offset_b) = faces
        direction_a, direction_b = first.direction, second.direction
        if (abs(sum(x * y for x, y in zip(direction_a, direction_b, strict=True))) > _TOLERANCE
                or sum(x * y for x, y in zip(normal_a, direction_b, strict=True)) >= -_TOLERANCE
                or sum(x * y for x, y in zip(normal_b, direction_a, strict=True)) >= -_TOLERANCE):
            continue
        x, y = _intersection(normal_a, normal_b, offset_a, offset_b)
        z0_a, z1_a = layer_a.band(walls[0])
        z0_b, z1_b = layer_b.band(walls[1])
        z0, z1 = max(z0_a, z0_b), min(z1_a, z1_b)
        if z1 - z0 <= _TOLERANCE:
            continue
        for index, (start, end, stock) in enumerate(split_stock_run(
                z1 - z0, tuple(length * M_PER_IN for length in profile.stock_lengths_in),
                profile.min_lap_in * M_PER_IN)):
            mesh = folded_section_mesh(
                section, (x, y, z0 + start), (*direction_a, 0.0), (*direction_b, 0.0),
                (0.0, 0.0, end - start), SHEET_24_GA_M)
            xs, ys, zs = zip(*mesh.positions, strict=True)
            model.solids.append(ResolvedSolid(
                uid=f"{junction.node_tag}-corrugated-corner-{index}",
                tag=f"TRIM-{junction.node_tag}-CORNER-{index + 1}", storey=junction.storey,
                category="cladding_trim", outline=((min(xs), min(ys)), (max(xs), min(ys)),
                                                    (max(xs), max(ys)), (min(xs), max(ys))),
                z0_m=min(zs), z1_m=max(zs), material=layer_a.material_ref, product=_KEY,
                body_mesh=mesh, host_ref=junction.node_tag,
                trim_length_m=end - start, trim_stock_length_in=round(stock / M_PER_IN, 6)))
