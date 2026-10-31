"""Concealed cladding panel screws as counted parts (decision #105).

A clipped or nail-strip panel's screws used to ride inside its $/SF rate; when the coating
is the spec (316 on the walls), that is how it gets cheaped out. A cladding material opts
in with ``Material.panel_fastener_part`` and ``panel_fastener_pitch_in``: one screw per
``fastener_coverage_in`` of panel width per pitch along it, over the layer's net area.
A face-fastened (``exposed_fastener``) panel is billed by ``takeoff/fasteners.py`` instead.
"""

from __future__ import annotations

import math
from collections import Counter

from typehaus.hardware.catalog import hardware_by_model
from typehaus.model.enums import LayerFunction
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.envelope import wall_layer_net_area_m2, wall_net_areas_m2
from typehaus.takeoff.hardware_row import hardware_row

_CLADDING = LayerFunction.CLADDING.value


def panel_screw_count(area_m2: float, coverage_in: float, pitch_in: float) -> int:
    """Screws over ``area_m2``: each one answers for ``coverage x pitch`` of panel."""
    tributary_m2 = coverage_in * pitch_in * M_PER_IN * M_PER_IN
    return math.ceil(area_m2 / tributary_m2 - 1e-9) if area_m2 > 0 else 0


def _counted_material(model: ResolvedModel, material_ref: str):
    """The cladding material, if it bills its concealed screws; refuses a half-authored one."""
    material = model.plan.library.material(material_ref)
    if material is None or material.panel_fastener_part is None:
        return None
    if material.exposed_fastener:
        raise ValueError(f"{material.tag}: panel_fastener_part on an exposed_fastener panel "
                         "bills its screws twice")
    if not material.fastener_coverage_in or not material.panel_fastener_pitch_in:
        raise ValueError(f"{material.tag}: panel_fastener_part needs fastener_coverage_in "
                         "and panel_fastener_pitch_in")
    return material


def _roof_cladding_ref(model: ResolvedModel, roof) -> str | None:
    assembly = model.plan.library.resolve_assembly(roof.assembly)
    if assembly is None:
        return None
    cladding = [layer for layer in assembly.layers if layer.function.value == _CLADDING]
    return cladding[-1].material_ref if cladding else None


def concealed_panel_screw_rows(model: ResolvedModel) -> list:
    """One row per (material, scope): wall net area or roof deck area, per storey."""
    areas: dict[tuple[str, str], Counter] = {}
    net = wall_net_areas_m2(model)
    for wall in model.walls:
        cladding = [layer for layer in wall.layers if layer.function == _CLADDING]
        if cladding and _counted_material(model, cladding[-1].material_ref):
            layer = cladding[-1]
            area = wall_layer_net_area_m2(model, wall, layer, net[wall.tag])
            areas.setdefault((layer.material_ref, "wall"), Counter())[wall.storey] += area
    for roof in model.roofs:
        ref = _roof_cladding_ref(model, roof)
        if ref and _counted_material(model, ref):
            areas.setdefault((ref, "roof"), Counter())[roof.storey] += roof.surface_area_m2

    rows = []
    for (ref, scope), by_storey_m2 in sorted(areas.items()):
        material = model.plan.library.material(ref)
        item = hardware_by_model(material.panel_fastener_part)
        if item is None or item.model != material.panel_fastener_part:
            raise LookupError(f"{ref}: panel_fastener_part {material.panel_fastener_part!r} "
                              "is not a catalogued part")
        coverage, pitch = material.fastener_coverage_in, material.panel_fastener_pitch_in
        by_storey = {storey: panel_screw_count(area, coverage, pitch)
                     for storey, area in sorted(by_storey_m2.items())}
        count = sum(by_storey.values())
        if count <= 0:
            continue
        area_sf = sum(by_storey_m2.values()) / (M_PER_IN * 12) ** 2
        net_note = "net of openings" if scope == "wall" else "sloped deck area"
        rows.append(hardware_row(
            item, scope=f"concealed panel screws, {ref}", count=count, by_storey=by_storey,
            basis=f"{area_sf:,.1f} SF ({scope}, {net_note}) / ({coverage:g} in coverage x "
                  f"{pitch:g} in o.c. along the fastened edge = "
                  f"{coverage * pitch / 144:.2f} SF per screw), per storey"))
    return rows
