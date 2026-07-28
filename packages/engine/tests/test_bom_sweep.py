"""The eight families that were resolved for months and reached no order.

The original TODO item's premise was stale — hangers, connectors, sill anchors and screws
*do* bill, and 15 tests pin them. The real gaps were elsewhere, and this file covers them:
plumbing, ducts, sleeves, footing beddings, openings, non-sheathing envelope layers, floor
finishes and stair treads.

The coverage *gate* lives in ``test_framing_takeoff.py`` beside the section list it extends;
this file is the per-section behaviour behind it.
"""

from __future__ import annotations

import pytest

from typehaus.takeoff.bom import bill_of_materials

_M2_TO_FT2 = 10.7639104


@pytest.fixture(scope="module")
def bom(catlin_model):
    return bill_of_materials(catlin_model)


# --- floor finishes: the half of S3 that makes a finish purchasable ------------------------

def test_floor_finishes_reconcile_against_the_houses_own_floor_area(catlin_model, bom):
    """The summed net finish area must equal the area of the rooms it covers. A row that
    quietly reads zero means the string lookup failed, and that is exactly what an
    area-total reconciliation catches and a per-row assertion does not."""
    field_rows = [row for row in bom["floor_finishes"] if "under" not in row]
    billed = sum(float(row["net_area_sqft"]) for row in field_rows)
    resolved = sum(room.area_m2 for room in catlin_model.rooms) * _M2_TO_FT2
    assert billed == pytest.approx(resolved, rel=1e-3)


def test_every_finish_row_resolved_a_real_material(bom):
    """An UNKNOWN row is the feature — it surfaces a typo'd finish string — but the catlin
    house must not have one, or something is genuinely unbilled."""
    unknown = [row for row in bom["floor_finishes"] if not row["known"]]
    assert unknown == [], unknown
    assert {row["finish"] for row in bom["floor_finishes"] if "under" not in row} == {
        "carpet", "lvp", "oak", "tile", "sealed-concrete", "rubber"}


def test_the_second_storey_lvp_and_carpet_rows_match_what_was_authored(catlin_model, bom):
    """S3 moved five second-storey rooms to LVP and one closet to carpet; S6 has to bill
    exactly those. The two halves are only useful together."""
    lvp = next(row for row in bom["floor_finishes"] if row["finish"] == "lvp")
    assert set(lvp["rooms"]) == {"RM-S-LANDING", "RM-S-HALL", "RM-S-SUITEBATH",
                                 "RM-S-VANITY", "RM-S-BATH1"}
    lvp_area = sum(room.area_m2 for room in catlin_model.rooms
                   if room.floor_finish == "lvp") * _M2_TO_FT2
    # Rows round to a tenth of a square foot, which is the tolerance here.
    assert float(lvp["net_area_sqft"]) == pytest.approx(lvp_area, abs=0.05)
    carpet = next(row for row in bom["floor_finishes"] if row["finish"] == "carpet")
    assert {"RM-S-CLOSET", "RM-S-NCLOSET"} <= set(carpet["rooms"])


def test_a_finish_is_ordered_with_its_waste_not_at_bare_polygon_area(bom):
    """Plank and tile are cut to the room; bare area under-orders every time. Tile carries
    the most — every perimeter cut is scrap — and sealed concrete carries none, because a
    sealer is measured by coverage rate rather than cut to fit."""
    rows = {row["finish"]: row for row in bom["floor_finishes"]}
    assert float(rows["tile"]["waste_pct"]) > float(rows["oak"]["waste_pct"])
    assert float(rows["sealed-concrete"]["waste_pct"]) == 0.0
    for row in bom["floor_finishes"]:
        if row["finish"] is None:
            continue
        expected = float(row["net_area_sqft"]) * (1 + float(row["waste_pct"]) / 100.0)
        assert float(row["order_area_sqft"]) >= expected - 1e-9, row["finish"]


def test_a_finish_brings_the_layer_it_implies(bom):
    """Carpet needs pad and LVP needs underlayment; a schedule that bills the covering alone
    is not orderable."""
    companions = {row["finish"]: row for row in bom["floor_finishes"] if "under" in row}
    assert set(companions) == {"carpet-pad", "lvp-underlayment"}
    assert companions["carpet-pad"]["under"] == "carpet"
    assert companions["lvp-underlayment"]["under"] == "lvp"
    for row in companions.values():
        assert row["known"], row
        assert float(row["order_area_sqft"]) > 0


def test_an_unknown_finish_bills_as_unknown_rather_than_as_nothing(catlin_model):
    """The behaviour the whole UNKNOWN path exists for. Point a room at a finish string no
    material answers to: it must appear, named, not silently vanish."""
    from dataclasses import replace

    from typehaus.takeoff.finishes import floor_finish_rows

    patched = replace(
        catlin_model,
        rooms=[replace(room, floor_finish="oka") if room.tag == "RM-M-LIVING" else room
               for room in catlin_model.rooms])
    rows = {row["finish"]: row for row in floor_finish_rows(patched)}
    assert "oka" in rows
    assert rows["oka"]["known"] is False
    assert rows["oka"]["material"] == "UNKNOWN"
    assert float(rows["oka"]["net_area_sqft"]) > 0


# --- the MEP families ---------------------------------------------------------------------

def test_pipe_runs_bill_by_system_and_diameter(catlin_model, bom):
    """3" DWV and 3/4" copper are different orders, so diameter is part of the key. Length
    is the resolver's developed length, so a drop through a floor is not billed as the zero
    plan length it projects to."""
    rows = bom["pipe_runs"]
    assert {row["system"] for row in rows} == {"drain", "vent", "water_cold"}
    billed = {tag for row in rows for tag in row["tags"]}
    assert billed == {run.tag for run in catlin_model.pipe_runs}
    total = sum(float(row["length_ft"]) for row in rows)
    assert total == pytest.approx(
        sum(run.length_m for run in catlin_model.pipe_runs) * 3.280839895, rel=1e-3)


def test_ducts_and_sleeves_bill_every_resolved_record(catlin_model, bom):
    assert ({tag for row in bom["ducts"] for tag in row["tags"]}
            == {duct.tag for duct in catlin_model.ducts})
    assert ({tag for row in bom["sleeves"] for tag in row["tags"]}
            == {sleeve.tag for sleeve in catlin_model.sleeves})
    assert sum(int(row["count"]) for row in bom["sleeves"]) == len(catlin_model.sleeves)


def test_footing_bedding_bills_stone_fabric_and_tile(catlin_model, bom):
    """The browser BOM billed these and the engine did not, so `haus takeoff` and the viewer
    disagreed about whether the stone under every footing was part of the order."""
    rows = bom["footing_bedding"]
    assert ({tag for row in rows for tag in row["tags"]}
            == {bedding.tag for bedding in catlin_model.footing_beddings})
    row = rows[0]
    assert float(row["volume_cubic_yards"]) > 0
    assert float(row["geotextile_sqft"]) > 0
    assert float(row["drain_tile_ft"]) > 0


# --- openings, envelope, stairs -----------------------------------------------------------

def test_openings_bill_by_type_and_cover_every_opening(catlin_model, bom):
    """A-601 drew this schedule all along; it just never reached the BOM."""
    rows = bom["openings"]
    assert sum(int(row["count"]) for row in rows) == len(catlin_model.openings)
    assert {tag for row in rows for tag in row["tags"]} == {
        opening.tag for opening in catlin_model.openings}
    assert {"door", "window"} <= {row["kind"] for row in rows}


def test_envelope_bills_more_than_the_sheathing(bom):
    """`sheet_goods` bills exactly one layer function. Insulation, drywall, cladding and the
    WRB are most of the envelope by area and were reaching no order at all."""
    functions = {row["function"] for row in bom["envelope_layers"]}
    assert {"insulation", "cladding", "membrane"} <= functions
    assert "sheathing" in functions
    # The overlap with sheet_goods is flagged, so a caller summing both cannot double-count.
    sheathing = [row for row in bom["envelope_layers"] if row["function"] == "sheathing"]
    assert sheathing and all(row["also_in_sheet_goods"] for row in sheathing)
    assert not any(row["also_in_sheet_goods"] for row in bom["envelope_layers"]
                   if row["function"] != "sheathing")


def test_stair_finish_bills_treads_risers_and_landings(catlin_model, bom):
    """Stringers bill as lumber through `framing`; a milled tread is a different order from
    a different supplier, counted by the piece."""
    rows = {row["stair"]: row for row in bom["stair_finish"]}
    assert set(rows) == {stair.tag for stair in catlin_model.stairs}
    for stair in catlin_model.stairs:
        row = rows[stair.tag]
        surfaces = len([m for m in stair.members if m.category in ("tread", "winder")])
        assert int(row["treads"]) == surfaces
        # One riser board per tread — the face below it. The model has no riser member.
        assert int(row["risers"]) == int(row["treads"])
    # The U-stairs have landing decks; the winder stair's boxes are winder treads instead.
    assert int(rows["ST-B2M"]["landing_decks"]) == 2
    assert int(rows["ST-S2A"]["landing_decks"]) == 0


def test_a_ceiling_below_bills_with_the_subfloor_it_shares_a_deck_with(catlin_model):
    """``FloorSystem.ceiling_below`` was read by nothing — a whole storey of ceiling drywall
    absent from the order. catlin authors none, so this hangs one on a real deck and checks
    it bills at the same area as the subfloor it shares that deck with."""
    from typehaus.model import DeckLayer, inch
    from typehaus.resolve import resolve
    from typehaus.takeoff.framing import sheet_goods_takeoff

    plan = catlin_model.plan
    storey, system = next(
        (storey.tag, element)
        for storey in plan.storeys
        for element in plan.storey_elements(storey.tag)
        if element.element_kind == "FloorSystem" and element.subfloor is not None)
    lidded = system.model_copy(update={
        "ceiling_below": DeckLayer(material_ref="gwb", thickness=inch(0.625))})
    patched = plan.with_elements(
        storey, [lidded if element.tag == system.tag else element
                 for element in plan.storey_elements(storey)])
    model, _findings = resolve(patched)

    before = {row["scope"] for row in sheet_goods_takeoff(catlin_model)}
    assert "ceiling" not in before, "the fixture is supposed to have no ceiling_below"
    rows = sheet_goods_takeoff(model)
    ceiling = [row for row in rows if row["scope"] == "ceiling"]
    assert ceiling, "ceiling_below reached no order"
    assert ceiling[0]["material"] == "gwb"
    # It covers the deck the subfloor covers, so their areas agree to the row's rounding.
    subfloor_area = sum(float(row["net_area_sqft"]) for row in rows
                        if row["scope"] == "subfloor")
    assert float(ceiling[0]["net_area_sqft"]) < subfloor_area  # one deck of several
    assert float(ceiling[0]["net_area_sqft"]) > 0


def test_conductors_bill_beside_the_raceway_they_pull_through(bom):
    """`conduit_takeoff` bills the pipe and none of the wire, so an estimate built on it
    buys half an electrical rough-in. Labelled an estimate, because a conduit run carries no
    circuit assignment in the model."""
    rows = bom["conductors"]
    assert rows and all(float(row["length_ft"]) > 0 for row in rows)
    assert all("estimate" in str(row["basis"]) for row in rows)
    assert {int(row["poles"]) for row in rows} == {1, 2}


# --- rainscreen base closure ---------------------------------------------------------------

def test_bug_screens_bill_the_exterior_perimeter_once_not_once_per_storey(catlin_model, bom):
    """The screen closes the *bottom* of a rainscreen cavity. The cladding runs past every
    floor line uninterrupted, so a house with three storeys of the same wall still has one
    screened base — billing per wall would order three times the strip that is installed.

    Reconciled against the walls themselves: the total is the run of exactly the walls whose
    cavity starts at their own base, which on catlin is the main-storey perimeter plus the
    garage's.
    """
    from typehaus.resolve.accessories import screens_rainscreen_base
    from typehaus.resolve.geometry import length, sub

    rows = bom["bug_screens"]
    assert rows, "a rainscreen house must order its base closure"
    billed = sum(float(row["length_ft"]) for row in rows)
    screened = [wall for wall in catlin_model.walls
                if screens_rainscreen_base(catlin_model, wall)]
    expected = sum(length(sub(wall.axis[1], wall.axis[0])) for wall in screened) * 3.280839895
    assert billed == pytest.approx(expected, abs=0.2)
    # Every screened wall is a ground-tier one; nothing stacked on a rainscreen qualifies.
    assert {wall.storey for wall in screened} == {"main", "garage"}
    assert all(row["material"] == "corrugated-vent-strip" for row in rows)


def test_bug_screen_rows_are_grouped_by_the_cavity_they_are_cut_to(bom):
    """The strip is bought in the section that fills the cavity, so a house with two
    different batten depths is two different orders — catlin's 1/2" house battens and the
    garage's 3/8" ones."""
    depths = {float(row["cavity_depth_in"]) for row in bom["bug_screens"]}
    assert len(depths) == len(bom["bug_screens"]) > 1
    assert all(depth > 0 for depth in depths)


def test_the_bom_is_json_and_its_section_keys_are_the_uis_contract(bom):
    """The browser renders this payload directly (``/bom``, ``OfflineEngine.bom_json``, and
    ``ui/src/model/engineBom.ts``) — it no longer computes a bill of its own. Two things it
    depends on, neither of which anything else pins:

    * the payload survives ``json.dumps`` unchanged, because that is literally the transport;
    * the section keys are exactly this set, because ``engineBom.ts``'s SECTION_GROUPS
      arranges them by name. A renamed section would silently fall into its "Other" bucket
      and a dropped one would vanish from the view.
    """
    import json

    round_tripped = json.loads(json.dumps(bom))
    assert round_tripped == bom, "the BOM must survive its own transport"

    assert set(bom) == {
        # Structure
        "framing", "framing_by_size", "structural_solids", "sheet_goods",
        "construction_returns", "hardware", "footing_bedding",
        # Envelope & openings
        "envelope_layers", "glazing_panels", "glazing_trim", "bug_screens", "openings",
        "floor_finishes", "stair_finish", "railings",
        # Mechanical & plumbing
        "pipe_runs", "ducts", "sleeves", "floor_heat",
        # Electrical
        "electrical_devices", "panel_schedule", "service_load", "conduit", "conductors",
        "solar", "backup_components",
        # Lighting
        "luminaire_schedule", "lighting_controls", "light_runs", "lighting_load",
        # Placeables
        "placeables",
    }, "add the new section to ui/src/model/engineBom.ts SECTION_GROUPS in the same change"
