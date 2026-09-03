"""The complete bill of materials: one payload, every section, nothing dropped.

Sections are deliberately parallel rather than merged — a framer orders lumber by size and
type, a concrete sub orders by the yard, and hardware is ordered by part number — but they
are produced together so a caller cannot render half a BOM.
"""

from __future__ import annotations

from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.anchors import sill_gasket_rows
from typehaus.takeoff.backup_calc import backup_runtime_summary
from typehaus.takeoff.data import data_device_schedule, data_raceway_takeoff, poe_budget
from typehaus.takeoff.drainage import drainage_takeoff
from typehaus.takeoff.edge_trim import edge_trim_takeoff
from typehaus.takeoff.electrical import (
    backup_component_rows,
    conductor_takeoff,
    conduit_takeoff,
    electrical_device_takeoff,
    panel_schedule,
    service_load_summary,
    solar_takeoff,
)
from typehaus.takeoff.envelope import bug_screen_takeoff, envelope_layer_takeoff
from typehaus.takeoff.fabrication import fabricated_member_schedule
from typehaus.takeoff.finishes import floor_finish_rows
from typehaus.takeoff.framing import (
    construction_returns_takeoff,
    framing_bom_by_size,
    framing_takeoff,
    sheet_goods_takeoff,
    structural_solids_takeoff,
)
from typehaus.takeoff.glazing import glazing_panel_takeoff, glazing_trim_takeoff
from typehaus.takeoff.hardware import hardware_takeoff
from typehaus.takeoff.hardware_config import (
    DEFAULT_HARDWARE_TAKEOFF_CONFIG,
    HardwareTakeoffConfig,
)
from typehaus.takeoff.hardwood import hardwood_takeoff
from typehaus.takeoff.lighting import (
    connected_lighting_va,
    light_run_materials,
    light_run_takeoff,
    lighting_controls,
    luminaire_schedule,
)
from typehaus.takeoff.member_protection import member_protection_takeoff
from typehaus.takeoff.mep import (
    duct_fitting_takeoff,
    duct_insulation_takeoff,
    duct_takeoff,
    freeze_protection_takeoff,
    pipe_insulation_takeoff,
    pipe_run_takeoff,
    sleeve_takeoff,
)
from typehaus.takeoff.openings import opening_takeoff
from typehaus.takeoff.placeables import floor_heat_takeoff, placeables_takeoff
from typehaus.takeoff.plumbing import fitting_takeoff
from typehaus.takeoff.plumbing_specialties import (
    install_parts_takeoff,
    plumbing_specialties_takeoff,
)
from typehaus.takeoff.railings import railing_takeoff
from typehaus.takeoff.sitework import footing_bedding_takeoff
from typehaus.takeoff.stairs import stair_finish_takeoff
from typehaus.takeoff.wall_structure import wall_structure_takeoff
from typehaus.takeoff.wood_surfaces import wood_surfaces_takeoff


def bill_of_materials(
    model: ResolvedModel,
    hardware_config: HardwareTakeoffConfig = DEFAULT_HARDWARE_TAKEOFF_CONFIG,
) -> dict:
    """Every BOM section for ``model``.

    ``framing`` is the cut list (one row per size *and* member type, reconciling 1:1 with
    ``model.all_members()``); ``framing_by_size`` rolls it up; ``structural_solids`` covers
    the concrete and standalone structure the member list cannot represent;
    ``construction_returns``, ``sheet_goods`` and ``hardware`` complete the order.
    ``glazing`` covers what none of those could: sheet goods bought as panels rather than as
    sheathing, and the aluminium extrusions that cap them, bought by the lineal foot.
    The ``luminaire_*``/``light_runs``/``light_run_materials``/``lighting_load`` sections are
    the lighting order: fixtures by schedule mark, tape by the lineal foot (blended, then
    split into channel/tape/end-cap/corner-connector order lines), and one supply per cove
    area.
    ``placeables`` counts the free-placed and wall-attached products (casework, appliances,
    fixtures — the UI BOM's placeablesSection twin) and ``floor_heat`` bills each radiant
    zone's element length, so no billable record lives only in a CLI patch or the browser.

    ``test_framing_takeoff`` holds a coverage meta-test over ``ResolvedModel``'s own
    collections so anything the IR learns to resolve cannot quietly go unbilled.
    """
    solar = solar_takeoff(model)
    return {
        "framing": framing_takeoff(model),
        "framing_by_size": framing_bom_by_size(model),
        # What a made-to-order member is BUILT to, as opposed to what it is bought as: the
        # overall length, clear span and end bearing a truss fabricator needs. Not a
        # quantity — every piece it lists is already billed in ``framing`` above.
        "fabricated_members": fabricated_member_schedule(model),
        "structural_solids": structural_solids_takeoff(model),
        "construction_returns": construction_returns_takeoff(model),
        # The seal under the sill plates the line above bills the boards of. Its own table
        # because ``construction_returns`` reconciles 1:1 with the resolved returns
        # (→ ``takeoff/anchors.sill_gasket_rows``).
        "sill_gaskets": sill_gasket_rows(model),
        "sheet_goods": sheet_goods_takeoff(model),
        "glazing_panels": glazing_panel_takeoff(model),
        "glazing_trim": glazing_trim_takeoff(model),
        "hardware": hardware_takeoff(model, hardware_config),
        "placeables": placeables_takeoff(model),
        "railings": railing_takeoff(model),
        "floor_heat": floor_heat_takeoff(model),
        "floor_finishes": floor_finish_rows(model),
        "envelope_layers": envelope_layer_takeoff(model),
        # The other half of the wall stack: a STRUCTURE layer that does not frame — a pour,
        # an ICF core, a CMU/SRW course, a brick wythe — produces no members and is not a
        # solid, so no other section can bill it. 43 of catlin's 154 walls, ~131 cy.
        # Partitions the walls with `framing` by the same predicate `frame_wall` branches on
        # (→ takeoff/wall_structure.py).
        "wall_structure": wall_structure_takeoff(model),
        # The species rollup — sauna liner, wainscot/tile-splash panelings, timber posts,
        # species floors — in square feet and board feet. Rows mirroring another section
        # carry ``also_in_envelope_layers`` / ``also_in_structural_solids`` /
        # ``also_in_floor_finishes``; the primary billing stays in those sections.
        "wood_surfaces": wood_surfaces_takeoff(model),
        # The milling schedule: the same wood as a CUT LIST in rough stock — finished
        # T x W x L, nominal quarters, rough board feet, and the glue-up flag. A view of
        # ``wood_surfaces``, ``framing`` and ``stair_finish`` for everything it shares with
        # them (the rows say which, ``also_in_*``); the stools and shelf boards are its own
        # and are unpriced by design — the fabrication labour is a prices.toml allowance and
        # the stock is owner-milled (→ takeoff/hardwood.py, ``haus millwork``).
        "hardwood": hardwood_takeoff(model),
        # The rainscreen's base closure, by the lineal foot — the solids sweep counts the
        # strip, but in cubic feet, which is not how it is bought.
        "bug_screens": bug_screen_takeoff(model),
        "openings": opening_takeoff(model),
        "stair_finish": stair_finish_takeoff(model),
        "footing_bedding": footing_bedding_takeoff(model),
        # Stormwater by the foot and the piece — gutter and leader were billed only as
        # cubic feet of aluminium, which is not how either is bought.
        "drainage": drainage_takeoff(model),
        # The rest of the edge-run family by the foot: fascia, soffit, flashing and the
        # roof's derived formed trim. Same gap as drainage — flashing billed as cubic feet
        # of aluminium is not an order.
        "edge_trim": edge_trim_takeoff(model),
        # Joist/beam tape by the foot of member it covers. Neither `framing` (sticks by
        # profile, house-wide) nor `structural_solids` (beams by the yard) can address
        # "the two garden decks' joists", so nothing could bill the membrane that keeps
        # water out of a built-up beam's ply seams.
        "member_protection": member_protection_takeoff(model),
        "pipe_runs": pipe_run_takeoff(model),
        # Fittings by the piece, counted off the runs' own 3D polylines and the drainage
        # graph — not estimated. Kept separate so [pipe_runs]'s drain/vent $/LF rates
        # price bare pipe only, not a share of fittings (→ #62).
        "pipe_fittings": fitting_takeoff(model),
        # The supply system's protection budget, which no section could see before
        # `PipeAccessory` existed: valves and preventers by the piece, and the loose
        # gasket/bracket/foam kits that go in with them.
        "plumbing_specialties": plumbing_specialties_takeoff(model),
        "install_parts": install_parts_takeoff(model),
        # Hot-water line insulation by the foot (IRC N1103.4.2). A field on the run, so it
        # cannot drift out of length with the pipe it sleeves.
        "pipe_insulation": pipe_insulation_takeoff(model),
        # Heater cable by the foot, the electrical twin of the row above. Kept apart
        # because a traced AND lagged run is the normal outdoor spec in this climate,
        # and one blended row cannot say that.
        "freeze_protection": freeze_protection_takeoff(model),
        "ducts": duct_takeoff(model),
        # Elbows by the piece off the ducts' own 3D polylines, the same derivation
        # [pipe_fittings] uses. Only possible since DuctRun gained elevations: a plan
        # polyline has no riser to turn at, so every one of these was invisible.
        "duct_fittings": duct_fitting_takeoff(model),
        # Duct wrap by the foot. An uninsulated outdoor-air duct through conditioned space
        # sweats, so this is not a finish line — it is why the ceiling below stays dry.
        "duct_insulation": duct_insulation_takeoff(model),
        "sleeves": sleeve_takeoff(model),
        # The electrical program (→ takeoff/electrical.py): devices by type, the panel
        # schedule + NEC 220.82-style service load, raceway LF, the PV array's installed
        # wattage, and the backup subsystem's derived DIN component list.
        "electrical_devices": electrical_device_takeoff(model),
        "panel_schedule": panel_schedule(model),
        "service_load": service_load_summary(model),
        "conduit": conduit_takeoff(model),
        "conductors": conductor_takeoff(model),
        "solar": solar,
        # The priced view of the dict above. Every ``ESTIMATE_PLANS`` entry
        # reads a LIST of rows, and ``solar`` is a dict of summaries — panel and watt
        # totals, the per-string cold-Voc check — so it could not be joined to a price
        # without either flattening it (and losing the string check) or teaching the join
        # about dicts (and inviting every future summary to be priced by accident). A
        # second top-level key costs nothing and leaves the existing ``solar`` contract,
        # which the UI reads, exactly as it was.
        "solar_modules": solar["by_product"],
        # The backup microgrid (→ takeoff/electrical.py + takeoff/backup_calc.py): the
        # placed ESS hardware and shed-tier switching gear, plus the runtime estimate that
        # says whether the system as sized actually carries the house.
        "backup_power": {
            "components": backup_component_rows(model),
            "runtime": backup_runtime_summary(model),
        },
        # The lighting program (→ takeoff/lighting.py): the E-602 schedule by mark, the
        # switch legs, the LED runs with their supplies sized against them, and the real
        # connected load beside the 3 VA/ft2 allowance the service calculation uses.
        "luminaire_schedule": luminaire_schedule(model),
        "lighting_controls": lighting_controls(model),
        "light_runs": light_run_takeoff(model),
        # The cove/LED order sheet: channel and tape by the foot, end caps and corner
        # connectors by the piece — where ``light_runs`` above bills one blended length.
        "light_run_materials": light_run_materials(model),
        "lighting_load": connected_lighting_va(model),
        # The low-voltage program (→ takeoff/data.py): the E-603 device schedule, the data
        # and spare raceways ``conduit`` deliberately excludes, and the PoE draw the panel
        # schedule cannot see because a PoE device names no circuit.
        "data_devices": data_device_schedule(model),
        "data_raceways": data_raceway_takeoff(model),
        "poe_budget": poe_budget(model),
    }
