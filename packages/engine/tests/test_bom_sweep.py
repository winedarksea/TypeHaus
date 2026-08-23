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


# --- railings: the run, the frame, and what fills it ---------------------------------------

def test_railing_rows_still_bill_every_guard_by_its_run(bom):
    """``length_ft`` is what prices a railing and none of the new columns may disturb it:
    ten authored railings, grouped by product and storey, at their plan run.

    The tenth is RL-SG-PORCH (2026-08-18), which replaced the porch's masonry parapet — so
    the fascia-mount product now bills two guards, 36.3 LF of porch under 38.3 LF of
    balcony, and the ``style == "masonry"`` group this test used to exclude is empty."""
    rows = [row for row in bom["railings"] if row["style"] != "masonry"]
    # Eleven since 2026-08-22: RL-G-SERVICE, the handrail on the garage service stair. It is
    # new because the *stair* is new — five concrete slabs until `Stair` could express a
    # step-down within one storey, and R311.7.8 asks for a handrail on any flight of four or
    # more risers the moment one is a flight at all.
    assert sum(int(row["count"]) for row in rows) == 11
    assert not [row for row in bom["railings"] if row["style"] == "masonry"]
    by_type = {}
    for row in rows:
        by_type[row["type"]] = by_type.get(row["type"], 0.0) + float(row["length_ft"])
    assert by_type["RAILING-EXT-ALUMINUM-FASCIA"] == pytest.approx(74.6, abs=0.1)
    assert by_type["RAILING-INT-STAIR-GUARD"] == pytest.approx(23.0, abs=0.1)
    # 36.7, not 30.0, since 2026-08-22, in two parts: RL-A-HANDRAIL gained 3'-0" at its east
    # end so it runs beside ST-S2A's winder fan as well as its straight flight (which is what
    # R311.7.8.2 asks of it, and what `code.R311_7_8_handrail` started measuring rather than
    # reading off `continuous=True`), and RL-G-SERVICE added 3'-8" on the new garage stair.
    assert by_type["(untyped railing)"] == pytest.approx(36.7, abs=0.1)


def test_the_untyped_group_key_is_also_what_gets_emitted(bom):
    """The defect: the group *key* was ``"(untyped railing)"`` and the emitted ``type`` was
    a raw ``None``, so the estimator matched on ``"None"`` and prices.toml carried a
    placeholder rate to work around it. The reader's key and the estimator's key are now
    the same string."""
    untyped = [row for row in bom["railings"] if row["type"] == "(untyped railing)"]
    assert untyped, "the handrails carry no type_ref and must still group"
    assert not [row for row in bom["railings"] if row["type"] is None]


def test_railing_infill_counts_reconcile_against_the_models_own_solids(catlin_model, bom):
    """The bill's picket count is the model's picket count. Summed rather than asserted per
    row, because a per-row number can be right while a whole railing is missing from the
    grouping."""
    billed = sum(int(row.get("baluster_count") or 0) for row in bom["railings"])
    drawn = len([s for s in catlin_model.solids if s.category == "railing_infill"])
    assert billed == drawn


def test_railing_post_counts_reconcile_against_the_models_own_posts(catlin_model, bom):
    billed = sum(int(row["post_count"]) for row in bom["railings"])
    drawn = len([s for s in catlin_model.solids
                 if s.category == "railing" and "POST" in s.tag])
    assert billed == drawn


def test_a_wall_mounted_rail_bills_brackets_rather_than_posts(catlin_model, bom):
    """The five handrails have no posts at all — they are screwed to a wall — and the box of
    brackets that carries them is what an order for one contains."""
    billed = sum(int(row["bracket_count"]) for row in bom["railings"])
    drawn = len([s for s in catlin_model.solids
                 if s.category == "railing" and "BRACKET" in s.tag])
    assert billed == drawn > 0


def test_a_raking_guards_top_rail_is_longer_than_its_plan_run(bom):
    """``length_ft`` is a plan projection by design; the cap stock a rake consumes is not.
    The untyped handrails are the five ``serves_stair`` railings, so every one of their rows
    must show the slope.

    All five are ``mount="wall"``, so the station walk this is read off is their *brackets*.
    It was their posts until the resolver stopped drawing posts under a rail that is screwed
    to a wall, at which point this quantity silently went to zero — a rake's worth of cap
    stock dropping out of the order."""
    for row in bom["railings"]:
        if row["type"] != "(untyped railing)":
            continue
        assert float(row["top_rail_length_ft"]) > float(row["length_ft"]) * 1.15, row


def test_the_railing_frame_row_in_structural_solids_is_still_the_frame_alone(bom):
    """Infill landing back on ``category="railing"`` would inflate this row and the plan
    sheet at once.

    Not pinned to a solid count any more: a raking rail is now banded finely enough to draw
    as one continuous bar and a round one is faceted on top of that, so the count is a
    function of stair slope and rail diameter. What has to hold is that there is exactly one
    frame row and that the infill is still filed in its own categories beside it."""
    frame = [row for row in bom["structural_solids"]
             if row["category"] == "railing" and row["assembly"] == "RAILING_DARK_METAL"]
    assert len(frame) == 1 and int(frame[0]["count"]) > 0
    assert [row for row in bom["structural_solids"]
            if row["category"] in ("railing_infill", "railing_glass")]


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
        "carpet", "lvp", "oak", "tile", "sealed-concrete", "polished-concrete", "rubber",
        "vinyl-sheet"}


def test_the_second_storey_lvp_and_carpet_rows_match_what_was_authored(catlin_model, bom):
    """S3 moved five second-storey rooms to LVP and one closet to carpet; S6 has to bill
    exactly those. The two halves are only useful together."""
    lvp = next(row for row in bom["floor_finishes"] if row["finish"] == "lvp")
    # RM-S-LANDING was folded into RM-S-HALL when the centre line opened up under
    # BM-S-HALL, so the one hall row now bills what used to be two. The two main-floor
    # rooms joined on 2026-08-02 when solid oak retreated to the studies (§Hardwood).
    assert set(lvp["rooms"]) == {"RM-S-HALL", "RM-S-SUITEBATH",
                                 "RM-S-VANITY", "RM-S-BATH1",
                                 "RM-M-LIVING", "RM-M-STUDY"}
    # NET of in-room finish zones. RM-M-LIVING is the reason: 411 SF of it sits on
    # SL-M-DECK, whose polished cap is the finished floor there, so the plank stops at the
    # band. Summing room areas alone would order LVP for a floor nobody covers.
    lvp_area = sum(room.area_m2 - sum(zone.area_m2 for zone in room.finish_zones)
                   for room in catlin_model.rooms
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
    # water_hot joined the other three when the plumbing pass authored the hot trunks and
    # branches off the water heaters — before that the only supply modelled was the cold
    # feed to the hydrant.
    assert {row["system"] for row in rows} == {"drain", "vent", "water_cold", "water_hot"}
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
    # An aggregate bedding, not FB-B-BRICK: the veneer plinth's "bedding" is a 2" XPS sheet
    # on the house footing's toe, so it bills no stone, fabric or tile by design.
    row = next(r for r in rows if float(r["geotextile_sqft"]) > 0)
    assert float(row["volume_cubic_yards"]) > 0
    assert float(row["drain_tile_ft"]) > 0
    # Tile rows group on the product, not just on "there is tile": a row that says only a
    # footage cannot be priced or bought.
    tile_rows = [r for r in rows if r["drain_tile"]]
    assert tile_rows
    for tile_row in tile_rows:
        assert float(tile_row["drain_tile_diameter_in"]) == pytest.approx(4.0, abs=0.01)
        assert tile_row["drain_tile_sock"] is True
        assert "HDPE" in str(tile_row["drain_tile_material"])
    # And where a run discharges is part of the key, not a note: the house tile daylights,
    # the sunken garden's cannot — its floor is 9' down — so it falls to DRW-SG-MAIN. Those
    # are two different runs of the same pipe and the take-off has to keep them apart.
    assert {r["drain_tile_discharge"] for r in tile_rows} == {"daylight", "DRW-SG-MAIN"}
    garden = next(r for r in tile_rows if r["drain_tile_discharge"] == "DRW-SG-MAIN")
    assert all(tag.startswith("FB-SG-") for tag in garden["tags"]), garden["tags"]


def test_drainage_bills_the_whole_storm_run_by_the_foot(catlin_model, bom):
    """Gutter and leader were billed only as solids — cubic feet of aluminium, which is not
    how either is bought. Every authored run belongs on the order, and so does the channel a
    roof derives along its own eave: an estimator buying gutter does not care which."""
    from typehaus.model.trim import Downspout, Gutter

    rows = bom["drainage"]
    billed = {tag for row in rows for tag in row["tags"]}
    authored = {element.tag for storey in catlin_model.plan.storeys
                for element in catlin_model.plan.storey_elements(storey.tag)
                if isinstance(element, (Gutter, Downspout))}
    assert authored <= billed, sorted(authored - billed)
    assert any(tag.startswith("RF-GARAGE:") for tag in billed), \
        "the garage's derived eave gutter is aluminium somebody has to buy"

    for row in rows:
        assert float(row["length_ft"]) > 0 or float(row["aggregate_cubic_yards"]) > 0, row
    leaders = [row for row in rows if row["category"] == "downspout"]
    assert leaders
    # A leader is billed by its drop; its plan run is a point.
    assert all(float(row["length_ft"]) > 0 for row in leaders)
    wells = [row for row in rows if row["category"] == "drywell"]
    assert wells and all(float(row["aggregate_cubic_yards"]) > 0 for row in wells)


def test_edge_trim_bills_the_authored_runs_and_the_derived_roof_trim_by_the_foot(
        catlin_model, bom):
    """Fascia, soffit and flashing were billed only as solids/members — cubic feet of PVC,
    which is not how a fascia board is bought. Every authored edge run reaches the order,
    and so does the trim a roof derives along its own edges."""
    from typehaus.model.trim import EaveSoffit, Fascia, Flashing

    rows = bom["edge_trim"]
    billed = {tag for row in rows for tag in row["tags"]}
    authored = {element.tag for storey in catlin_model.plan.storeys
                for element in catlin_model.plan.storey_elements(storey.tag)
                if isinstance(element, (Fascia, EaveSoffit, Flashing))}
    assert authored, "fixture regression: the Catlin house lost its edge trim"
    assert authored <= billed, sorted(authored - billed)
    for row in rows:
        assert float(row["length_ft"]) > 0, row
    # The balcony's PVC fascia bills its authored path, mirrored (not primary) in solids.
    fascia = next(row for row in rows
                  if row["category"] == "fascia" and "TR-SG-FASCIA" in row["tags"])
    assert fascia["also_in_structural_solids"] and not fascia["also_in_framing"]
    # The garage roof's derived fascia boards bill too, mirrored in the framing cut list.
    derived = [row for row in rows if row["also_in_framing"]]
    assert any(tag.startswith("RF-GARAGE:") for row in derived for tag in row["tags"]), \
        "the garage's derived fascia/soffit is trim somebody has to buy"
    # A derived gutter must NOT appear here: `drainage` bills it, and one channel on two
    # orders is double-billing.
    assert not any(row["category"] == "gutter" for row in rows)
    # The house's formed corner trim is composed of three bands sharing one span; billing
    # every band would treble the order, so each run counts once.
    corner = [row for row in rows if row["category"] == "corner_trim"]
    if corner:
        member_lf = sum(m.length_m for roof in catlin_model.roofs for m in roof.members
                        if m.category == "corner_trim") * 3.280839895
        billed_lf = sum(float(row["length_ft"]) for row in corner)
        assert billed_lf < member_lf * 0.5, "banded corner trim must bill one band per run"


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
    # The overlap with sheet_goods is flagged, so a caller summing both cannot double-count —
    # and only where there IS one. `sheet_goods_takeoff` walks walls, roofs and floor systems
    # and has never walked a slab, so the 4" capillary break under CATLIN_SLAB_FLOOR (a
    # SHEATHING layer, and #57 stone rather than a sheet good at all) bills here and nowhere
    # else. Flagging it would point a reader at a row that does not exist.
    sheathing = [row for row in bom["envelope_layers"] if row["function"] == "sheathing"]
    assert sheathing
    assert all(row["also_in_sheet_goods"] for row in sheathing if row["scope"] != "slab")
    assert not any(row["also_in_sheet_goods"] for row in sheathing
                   if row["scope"] == "slab")
    assert not any(row["also_in_sheet_goods"] for row in bom["envelope_layers"]
                   if row["function"] != "sheathing")


def test_a_roof_ceiling_bills_off_the_bearing_plane_not_the_deck(catlin_model, bom):
    """A roof's ``default_lining`` and its layers' ``CavityFill`` were read by nothing.

    The roof loop walked bare ``assembly.layers``, so the gypsum ceiling under CATLIN_ROOF's
    rafters, its 5.5" cavity batts, and the garage attic's blown fill all reached no order —
    the same class of miss as ``ceiling_below`` above, one plane further up.

    The plane matters as much as the fact. ``surface_area_m2`` is sloped AND runs out to the
    fascia; a ceiling stops at the bearing wall, and on a truss it lies flat. The garage is
    the clean case: 24'-0" square inside its bearings, 26'-8" square once the 1'-4" eaves are
    on, so billing the ceiling off the deck would order 30% too much of it."""
    from typehaus.resolve.roof_geometry import roof_ceiling_area_m2

    rows = [row for row in bom["envelope_layers"] if row["scope"] == "roof ceiling"]
    assert rows, "roof default_lining and cavity fill reached no order"

    garage = next(roof for roof in catlin_model.roofs if roof.tag == "RF-GARAGE")
    # Trussed: flat bottom chord, so the pitch never enters the ceiling area.
    assert roof_ceiling_area_m2(catlin_model, garage) * 10.7639 == pytest.approx(576.0, abs=0.5)
    assert garage.surface_area_m2 > roof_ceiling_area_m2(catlin_model, garage)

    blown = [row for row in rows if row["material"] == "blown-fiberglass"]
    assert len(blown) == 1, "the garage attic fill is a cavity, not a layer"
    assert blown[0]["function"] == "insulation (cavity)", "must read as the wall path does"
    assert float(blown[0]["net_area_sqft"]) == pytest.approx(576.0, abs=0.5)

    house = next(roof for roof in catlin_model.roofs if roof.tag == "RF-HOUSE")
    # Rafter-framed: the lining follows the slope, so the same bearing rectangle is lifted
    # by the slope factor — but it still stops short of the deck's overhung area.
    house_ceiling = roof_ceiling_area_m2(catlin_model, house)
    assert house_ceiling > 0.0
    assert house_ceiling < house.surface_area_m2

    # A ceiling is never billed as sheet goods: that scope belongs to FloorSystem decks.
    assert not any(row["also_in_sheet_goods"] for row in rows)


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
    absent from the order. The second floor authors 5/8" gypsum under its deck (that deck's
    underside *is* the main storey's ceiling), and it has to bill over exactly the surface
    its own subfloor covers: the same gross rectangle, less any stair opening.

    Four decks author one since 2026-08-21 (FS-M-WEST/FS-M-EAST when the basement got a
    framed ceiling; FS-S-WEST/FS-S-EAST when the second floor split truss/I-joist), and
    they group into one ``ceiling`` row because they are the same board at the same
    thickness. So the deck-by-deck arithmetic is checked against each deck's *share* of
    that row, not against the whole of it."""
    from typehaus.resolve.geometry import polygon_area
    from typehaus.takeoff.framing import sheet_goods_takeoff

    rows = sheet_goods_takeoff(catlin_model)
    ceiling = [row for row in rows if row["scope"] == "ceiling"]
    assert len(ceiling) == 1, "ceiling_below reached no order"
    assert ceiling[0]["material"] == "gwb"
    assert float(ceiling[0]["thickness_in"]) == 0.625

    def _gross_sqft(tag: str) -> float:
        floor = next(item for item in catlin_model.floors if item.tag == tag)
        points = [point for member in floor.members for point in (member.p0, member.p1)]
        return ((max(p[0] for p in points) - min(p[0] for p in points))
                * (max(p[1] for p in points) - min(p[1] for p in points))) * 10.7639

    def _opening_sqft(tag: str) -> float:
        opening = next(element for element in catlin_model.plan.all_elements()
                       if getattr(element, "tag", None) == tag)
        return abs(polygon_area([p.xy_m for p in opening.outline])) * 10.7639

    west_second_net = _gross_sqft("FS-S-WEST") - _opening_sqft("FO-S-STAIR")
    east_second_net = _gross_sqft("FS-S-EAST")
    assert float(ceiling[0]["net_area_sqft"]) > west_second_net + east_second_net

    others = _gross_sqft("FS-M-WEST") - _opening_sqft("FO-M-STAIR") + _gross_sqft("FS-M-EAST")
    total = west_second_net + east_second_net + others
    assert float(ceiling[0]["net_area_sqft"]) == pytest.approx(total, abs=0.5)

    # Several decks of several: the house's subfloor area is larger than this one ceiling.
    subfloor_area = sum(float(row["net_area_sqft"]) for row in rows
                        if row["scope"] == "subfloor")
    assert 0 < float(ceiling[0]["net_area_sqft"]) < subfloor_area


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
    cavity starts at their own base, which on catlin is the main-storey perimeter. The garage
    dropped out on 2026-08-20 when GARAGE_WALL_2X6 lost its rainscreen furring — nail strip
    face-fastens straight to the Zip-R, so there is no cavity there to close.
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
    assert {wall.storey for wall in screened} == {"main"}
    assert all(row["material"] == "corrugated-vent-strip" for row in rows)


def test_bug_screen_rows_are_grouped_by_the_cavity_they_are_cut_to(bom):
    """The strip is bought in the section that fills the cavity, so a house with two
    different batten depths is two different orders.

    Catlin is down to ONE depth since 2026-08-20 — the garage's 3/8" battens went with its
    rainscreen, leaving only the house's 1/2" — so what this can still prove is the grouping
    itself: one row per distinct depth, never one row per wall.
    """
    rows = bom["bug_screens"]
    depths = {float(row["cavity_depth_in"]) for row in rows}
    assert rows and len(depths) == len(rows)
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
        # Monolithic wall structure (2026-08-03): the concrete/masonry wall cores that
        # frame no members and are not solids, so no other section could see them.
        "wall_structure",
        # Envelope & openings
        "envelope_layers", "wood_surfaces", "glazing_panels", "glazing_trim", "edge_trim",
        "bug_screens", "openings", "floor_finishes", "stair_finish", "railings",
        # Mechanical & plumbing
        "pipe_runs", "plumbing_specialties", "install_parts", "pipe_insulation",
        "ducts", "sleeves", "floor_heat", "drainage",
        # Electrical
        "electrical_devices", "panel_schedule", "service_load", "conduit", "conductors",
        "solar", "backup_power",
        # Lighting
        "luminaire_schedule", "lighting_controls", "light_runs", "light_run_materials",
        "lighting_load",
        # Data & low-voltage
        "data_devices", "data_raceways", "poe_budget",
        # Placeables
        "placeables",
    }, "add the new section to ui/src/model/engineBom.ts SECTION_GROUPS in the same change"
