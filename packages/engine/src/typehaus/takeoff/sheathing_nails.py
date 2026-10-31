"""Sheathing nails off an authored ``Layer.nailing`` schedule (decision #105).

A FORTIFIED deck (RSRS-01 ring-shank at 4" o.c.) or a shear panel's edge nailing is the
spec a framer substitutes first. The count is a per-sheet density, read with the host's
OWN support spacing (its ``FramingSpec``, never a constant), times the layer's area.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict

from typehaus.hardware.catalog import hardware_by_model
from typehaus.model.enums import LayerFunction
from typehaus.quantities import M_PER_IN
from typehaus.resolve.framing.tables import DEFAULT_SPACING
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.sheet_stock import (
    SHEET_WIDTH_IN,
    order_sheet_length_in,
    wall_layer,
)
from typehaus.takeoff.envelope import wall_layer_net_area_m2, wall_net_areas_m2
from typehaus.takeoff.hardware_row import hardware_row

_M2_PER_SF = (12 * M_PER_IN) ** 2


def nails_per_sheet(sheet_w_in: float, sheet_l_in: float, support_oc_in: float,
                    edge_oc_in: float, field_oc_in: float, blocked: bool = False) -> int:
    """Nails in one sheet whose supports cross ``sheet_l_in``, each support ``sheet_w_in`` long.

    The two end supports are panel edges at ``edge_oc_in``; the ones between are field at
    ``field_oc_in``. ``blocked`` also nails the two edges between the supports at
    ``edge_oc_in`` (a shear panel), less the points the support lines already hold.
    4x8 across 24" supports at 4"/4": 5 lines x 13 = 65.
    """
    lines = math.floor(sheet_l_in / support_oc_in + 1e-9) + 1
    along_edge = math.ceil(sheet_w_in / edge_oc_in - 1e-9) + 1
    along_field = math.ceil(sheet_w_in / field_oc_in - 1e-9) + 1
    nails = 2 * along_edge + max(0, lines - 2) * along_field
    if blocked:
        on_edge = math.ceil(sheet_l_in / edge_oc_in - 1e-9) + 1
        shared = lines if support_oc_in % edge_oc_in < 1e-9 else 2
        nails += 2 * max(0, on_edge - shared)
    return nails


def _support_oc_in(assembly) -> float:
    for layer in assembly.layers:
        if layer.function == LayerFunction.STRUCTURE and layer.framing is not None:
            return (layer.framing.spacing or DEFAULT_SPACING).inches
    return DEFAULT_SPACING.inches


def _density_per_sf(layer, support_oc_in: float, vertical: bool) -> tuple[float, str]:
    """Nails per SF of this layer, and the sheet arithmetic behind it."""
    length_in = order_sheet_length_in(layer.sheet_length.inches if layer.sheet_length else None)
    # A wall sheet stands with its long side up the studs; a deck sheet spans across them.
    line_in, across_in = (length_in, SHEET_WIDTH_IN) if vertical else (SHEET_WIDTH_IN, length_in)
    spec = layer.nailing
    per_sheet = nails_per_sheet(line_in, across_in, support_oc_in, spec.edge_oc_in,
                                spec.field_oc_in, spec.blocked)
    note = (f"{per_sheet} per 4x{length_in / 12:g} sheet over {support_oc_in:g} in o.c. "
            f"supports at {spec.edge_oc_in:g} in edges / {spec.field_oc_in:g} in field"
            f"{', all edges blocked' if spec.blocked else ''}")
    return per_sheet / (SHEET_WIDTH_IN * length_in / 144.0), note


def sheathing_nail_rows(model: ResolvedModel) -> list:
    """One row per nail model, per storey, with each host's sheet arithmetic in the basis."""
    by_part: dict[str, Counter] = defaultdict(Counter)
    notes: dict[str, set] = defaultdict(set)

    def add(layer, area_m2: float, storey: str, support_oc: float, vertical: bool, host: str):
        density, note = _density_per_sf(layer, support_oc, vertical)
        by_part[layer.nailing.part][storey] += density * area_m2 / _M2_PER_SF
        notes[layer.nailing.part].add(f"{host} {layer.material_ref}: {note}")

    net = wall_net_areas_m2(model)
    for wall in model.walls:
        assembly = model.plan.library.resolve_assembly(wall.assembly)
        for resolved in wall.layers:
            layer = wall_layer(model.plan, wall, resolved.name)
            if layer is None or layer.nailing is None:
                continue
            area = wall_layer_net_area_m2(model, wall, resolved, net[wall.tag])
            add(layer, area, wall.storey, _support_oc_in(assembly), True, wall.tag)
    for roof in model.roofs:
        assembly = model.plan.library.resolve_assembly(roof.assembly)
        for layer in assembly.layers if assembly else ():
            if layer.nailing is not None:
                add(layer, roof.surface_area_m2, roof.storey, _support_oc_in(assembly), False,
                    roof.tag)

    rows = []
    for part, storeys in sorted(by_part.items()):
        item = hardware_by_model(part)
        if item is None or item.model != part:
            raise LookupError(f"Layer.nailing names {part!r}, which is not catalogued")
        counts = {storey: math.ceil(n - 1e-9) for storey, n in sorted(storeys.items())}
        rows.append(hardware_row(
            item, scope="sheathing nails", count=sum(counts.values()), part_number=part,
            by_storey=counts,
            basis="nails per sheet / sheet area x layer area: " + "; ".join(sorted(notes[part]))))
    return rows
