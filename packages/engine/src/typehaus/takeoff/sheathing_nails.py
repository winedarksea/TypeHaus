"""Sheathing nails off an authored ``Layer.nailing`` / ``DeckLayer.nailing`` (decisions #105, #147).

A FORTIFIED deck (RSRS-01 ring-shank at 4" o.c.) or a shear panel's edge nailing is the
spec a framer substitutes first. The count is a per-sheet density, read with the host's
OWN support spacing (its ``FramingSpec``, never a constant), times the layer's area. A
subfloor reads its ``JoistSpec.spacing`` over the deck's net area.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict

from typehaus.hardware.catalog import hardware_by_model
from typehaus.model.enums import LayerFunction
from typehaus.model.floors import FloorSystem
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
from typehaus.takeoff.sheet_goods import deck_net_area_m2

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
        # An authored 24" reads back as 23.999...: test the remainder from both sides.
        remainder = support_oc_in % edge_oc_in
        shared = lines if min(remainder, edge_oc_in - remainder) < 1e-6 else 2
        nails += 2 * max(0, on_edge - shared)
    return nails


def _support_oc_in(assembly) -> float:
    for layer in assembly.layers:
        if layer.function == LayerFunction.STRUCTURE and layer.framing is not None:
            return (layer.framing.spacing or DEFAULT_SPACING).inches
    return DEFAULT_SPACING.inches


def _roof_blocked(model: ResolvedModel, roof) -> bool:
    """A roof whose ``DiaphragmSpec`` is blocked AND authors the blocks nails every edge."""
    spec = getattr(model.plan.by_tag(roof.tag), "diaphragm", None)
    return bool(spec and spec.blocked and spec.panel_edge_blocking)


def _density_per_sf(layer, support_oc_in: float, vertical: bool,
                    blocked: bool) -> tuple[float, str]:
    """Nails per SF of this layer, and the sheet arithmetic behind it."""
    stated = getattr(layer, "sheet_length", None)  # a DeckLayer states none: 4x8
    length_in = order_sheet_length_in(stated.inches if stated else None)
    # A wall sheet stands with its long side up the studs; a deck sheet spans across them.
    line_in, across_in = (length_in, SHEET_WIDTH_IN) if vertical else (SHEET_WIDTH_IN, length_in)
    spec = layer.nailing
    per_sheet = nails_per_sheet(line_in, across_in, support_oc_in, spec.edge_oc_in,
                                spec.field_oc_in, blocked)
    note = (f"{per_sheet} per 4x{length_in / 12:g} sheet over {support_oc_in:g} in o.c. "
            f"supports at {spec.edge_oc_in:g} in edges / {spec.field_oc_in:g} in field"
            f"{', all edges blocked' if blocked else ''}")
    return per_sheet / (SHEET_WIDTH_IN * length_in / 144.0), note


def _hosts(hosts: set) -> str:
    """One host by tag; many by count, so a wall-wide schedule stays one clause."""
    return next(iter(hosts)) if len(hosts) == 1 else f"{len(hosts)} hosts"


def sheathing_nail_rows(model: ResolvedModel) -> list:
    """One row per nail model, per storey, with each host's sheet arithmetic in the basis."""
    by_part: dict[str, Counter] = defaultdict(Counter)
    notes: dict[str, dict[tuple, set]] = defaultdict(lambda: defaultdict(set))

    def add(layer, area_m2: float, storey: str, support_oc: float, vertical: bool, host: str,
            blocked: bool = False):
        density, note = _density_per_sf(layer, support_oc, vertical,
                                        blocked or layer.nailing.blocked)
        by_part[layer.nailing.part][storey] += density * area_m2 / _M2_PER_SF
        notes[layer.nailing.part][(layer.material_ref, note)].add(host)

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
                    roof.tag, _roof_blocked(model, roof))

    floors = {floor.tag: floor for floor in model.floors}
    for storey in model.plan.storeys:
        for system in model.plan.storey_elements(storey.tag):
            if not isinstance(system, FloorSystem) or system.subfloor is None \
                    or system.subfloor.nailing is None:
                continue
            floor = floors.get(system.tag)
            if floor is None or not floor.members:
                continue
            spacing = (system.joists.spacing or DEFAULT_SPACING).inches
            add(system.subfloor, deck_net_area_m2(floor), storey.tag, spacing, False,
                system.tag)

    rows = []
    for part, storeys in sorted(by_part.items()):
        item = hardware_by_model(part)
        if item is None or item.model != part:
            raise LookupError(f"Layer.nailing names {part!r}, which is not catalogued")
        counts = {storey: math.ceil(n - 1e-9) for storey, n in sorted(storeys.items())}
        rows.append(hardware_row(
            item, scope="sheathing nails", count=sum(counts.values()), part_number=part,
            by_storey=counts,
            basis="nails per sheet / sheet area x layer area: " + "; ".join(
                f"{_hosts(hosts)} {material}: {note}"
                for (material, note), hosts in sorted(notes[part].items()))))
    return rows
