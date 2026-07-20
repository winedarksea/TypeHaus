"""Sheet-good takeoffs derived from resolved framing and authored assemblies."""

from __future__ import annotations

import math
from collections import defaultdict

from typehaus.model.enums import LayerFunction
from typehaus.model.floors import FloorOpening, FloorSystem
from typehaus.resolve.geometry import length, polygon_area, sub
from typehaus.resolve.model import ResolvedModel

_M2_TO_FT2 = 10.7639104167
_SHEET_AREA_FT2 = 32.0


def sheet_goods_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Return net-area and whole-sheet quantities for wall, roof, and subfloor sheathing.

    Every row is explicitly tied to its material and thickness; this makes a 4x8-sheet
    estimate auditable instead of silently grouping unlike panel products.
    """
    areas: dict[tuple[str, str, float], float] = defaultdict(float)
    openings_by_wall: dict[str, float] = defaultdict(float)
    for opening in model.openings:
        openings_by_wall[opening.host_wall] += opening.width_m * opening.height_m

    for wall in model.walls:
        exterior = any(layer.function == "cladding" for layer in wall.layers)
        if not exterior:
            continue
        wall_area = length(sub(wall.axis[1], wall.axis[0])) * (
            ((wall.top_z0_m or wall.z1_m) + (wall.top_z1_m or wall.z1_m)) / 2 - wall.z0_m
        ) - openings_by_wall[wall.tag]
        for layer in wall.layers:
            if layer.function == "sheathing":
                areas[("exterior wall", layer.material_ref, layer.thickness_m)] += max(0.0, wall_area)

    for roof in model.roofs:
        assembly = model.plan.library.resolve_assembly(roof.assembly)
        if assembly is None:
            continue
        for layer in assembly.layers:
            if layer.function is LayerFunction.SHEATHING:
                areas[("roof", layer.material_ref, layer.thickness.meters)] += roof.surface_area_m2

    for storey in model.plan.storeys:
        for system in model.plan.storey_elements(storey.tag):
            if not isinstance(system, FloorSystem) or system.subfloor is None:
                continue
            floor = next((item for item in model.floors if item.tag == system.tag), None)
            if floor is None or not floor.members:
                continue
            points = [point for member in floor.members for point in (member.p0, member.p1)]
            gross = (max(point[0] for point in points) - min(point[0] for point in points)) * (
                max(point[1] for point in points) - min(point[1] for point in points)
            )
            openings = sum(abs(polygon_area([point.xy_m for point in opening.outline]))
                           for opening in model.plan.storey_elements(storey.tag)
                           if isinstance(opening, FloorOpening) and opening.tag in system.openings)
            areas[("subfloor", system.subfloor.material_ref, system.subfloor.thickness.meters)] += gross - openings

    return [
        {"scope": scope, "material": material, "thickness_in": round(thickness / 0.0254, 3),
         "net_area_sqft": round(area * _M2_TO_FT2, 1),
         "sheets_4x8": math.ceil(area * _M2_TO_FT2 / _SHEET_AREA_FT2)}
        for (scope, material, thickness), area in sorted(areas.items())
    ]
