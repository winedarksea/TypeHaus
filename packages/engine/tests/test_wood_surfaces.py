"""The species-split wood order (plans/TODO.md §Hardwood, 2026-08-02).

``wood_surfaces`` is a rollup, so every quantity here is reconciled against the model's
own geometry rather than hard-coded — and each mirrored row's overlap contract with its
primary section (``envelope_layers`` / ``floor_finishes`` / ``structural_solids``) is
pinned from both sides, so neither section can drift or double-bill unnoticed.
"""

from __future__ import annotations

import dataclasses

import pytest

from typehaus.model.enums import LayerFunction
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.geometry import length, sub
from typehaus.takeoff.bom import bill_of_materials
from typehaus.takeoff.wood_surfaces import wood_surfaces_takeoff

_M2_TO_FT2 = 10.7639104
_M_TO_FT = 3.280839895


@pytest.fixture(scope="module")
def bom(catlin_model):
    return bill_of_materials(catlin_model)


def _wall_net_ft2(catlin_model, wall) -> float:
    """The envelope-layers wall convention: run x mean top, net of openings."""
    openings = sum(o.width_m * o.height_m for o in catlin_model.openings
                   if o.host_wall == wall.tag)
    run = length(sub(wall.axis[1], wall.axis[0]))
    mean_top = ((wall.top_z0_m or wall.z1_m) + (wall.top_z1_m or wall.z1_m)) / 2.0
    return max(0.0, run * (mean_top - wall.z0_m) - openings) * _M2_TO_FT2


# --- the sauna liner and its tile splash ---------------------------------------------------

def test_the_sauna_liner_bills_net_of_the_shower_splash(catlin_model, bom):
    """Basswood = the three liner walls' envelope area minus the two 3' x 7'-6" tile
    bands; the tile bills beside it as an override. Recomputed, not hard-coded."""
    rows = bom["wood_surfaces"]
    basswood = next(row for row in rows if row["material"] == "sauna-tg")
    liner_walls = [w for w in catlin_model.walls
                   if any(ly.function == LayerFunction.FINISH.value
                          and ly.material_ref == "sauna-tg" for ly in w.layers)]
    assert {w.tag for w in liner_walls} == {"W-B-SA-W", "W-B-SA-N", "W-B-CS"}
    gross = sum(_wall_net_ft2(catlin_model, w) for w in liner_walls)
    splash = sum(p.area_m2 for p in catlin_model.panelings
                 if p.replaces_wall_finish) * _M2_TO_FT2
    assert splash == pytest.approx(2 * 3.0 * 7.5, rel=1e-3)  # two 3' bands x 7'-6"
    assert float(basswood["net_area_sqft"]) == pytest.approx(gross - splash, abs=0.05)
    assert basswood["species"] == "basswood"
    assert basswood["also_in_envelope_layers"] is True
    # 5/4 stock: 1.25 bf per ordered square foot.
    assert float(basswood["board_feet"]) == pytest.approx(
        float(basswood["order_area_sqft"]) * 1.25, abs=0.05)

    tile = next(row for row in rows if row["kind"] == "override")
    assert tile["material"] == "tile"
    assert float(tile["net_area_sqft"]) == pytest.approx(45.0, abs=0.05)
    assert float(tile["waste_pct"]) == 15.0
    assert float(tile["order_area_sqft"]) == 52.0


def test_envelope_layers_stays_gross_of_the_splash(catlin_model, bom):
    """The overlap contract from the other side: ``envelope_layers`` keeps billing the
    liner at the full assembly-truth area, and only ``wood_surfaces`` nets the splash —
    the ``also_in_envelope_layers`` flag is what says the two rows overlap on purpose."""
    liner_rows = [row for row in bom["envelope_layers"] if row["material"] == "sauna-tg"]
    assert liner_rows, "the liner must keep its envelope_layers billing"
    liner_walls = [w for w in catlin_model.walls
                   if any(ly.function == LayerFunction.FINISH.value
                          and ly.material_ref == "sauna-tg" for ly in w.layers)]
    gross = sum(_wall_net_ft2(catlin_model, w) for w in liner_walls)
    assert sum(float(r["net_area_sqft"]) for r in liner_rows) == pytest.approx(
        gross, abs=0.1)


# --- the walnut wainscot -------------------------------------------------------------------

def test_the_study_wainscot_reconciles_with_the_rooms_bounding_walls(catlin_model, bom):
    """Walnut = the shared runs of RM-M-STUDY's bounding walls x 36", minus D-M-STUDY's
    punch through the band; 4/4 stock makes board feet equal the ordered square feet."""
    walnut = next(row for row in bom["wood_surfaces"] if row["material"] == "walnut-tg")
    assert walnut["kind"] == "paneling"
    assert walnut["species"] == "walnut"
    resolved = sum(p.area_m2 for p in catlin_model.panelings
                   if p.material_ref == "walnut-tg") * _M2_TO_FT2
    assert float(walnut["net_area_sqft"]) == pytest.approx(resolved, abs=0.05)
    # Sanity-bound against the room's own clear face: perimeter x 3' is the ceiling
    # (nothing subtracted), and the door punch (2'-6" x 3') is the only deduction.
    room = next(r for r in catlin_model.rooms if r.tag == "RM-M-STUDY")
    ring = list(room.clear_face)
    perimeter = sum(length(sub(ring[i], ring[i - 1])) for i in range(len(ring)))
    ceiling = perimeter * _M_TO_FT * 3.0
    assert ceiling - 7.5 - 3.0 < float(walnut["net_area_sqft"]) < ceiling - 7.5 + 3.0
    assert float(walnut["board_feet"]) == pytest.approx(
        float(walnut["order_area_sqft"]), abs=0.05)


# --- the elm tudor posts -------------------------------------------------------------------

def test_the_four_elm_posts_bill_as_ten_foot_sections(catlin_model, bom):
    """Four 6-1/8" square posts, each cut just under 9' and ordered as a 10' section:
    40 LF ordered, board feet off the actual section over the ordered length."""
    elm = next(row for row in bom["wood_surfaces"] if row["material"] == "elm-timber")
    assert elm["kind"] == "timber"
    assert elm["species"] == "elm"
    assert int(elm["count"]) == 4
    assert elm["tags"] == ["P-S-TUDOR1", "P-S-TUDOR2", "P-S-TUDOR3", "P-S-TUDOR4"]
    assert int(elm["order_length_ft"]) == 40
    assert float(elm["board_feet"]) == pytest.approx(6.125 * 6.125 / 12.0 * 40.0, abs=0.05)
    assert elm["also_in_structural_solids"] is True
    # The primary billing: the posts stay in structural_solids under their assembly.
    solids = [row for row in bom["structural_solids"]
              if row["category"] == "column" and row["assembly"] == "ELM_TIMBER"]
    assert len(solids) == 1 and int(solids[0]["count"]) == 4


def test_a_custom_actual_profile_parses_as_stated_dimensions() -> None:
    """"6.125x6.125" is actual (decimal) dimensions, not a LUMBER_ACTUAL nominal — it
    must never fall back to the 1.5x5.5 stud section."""
    cs = cross_section("6.125x6.125")
    assert cs.width_m == pytest.approx(6.125 * 0.0254)
    assert cs.depth_m == pytest.approx(6.125 * 0.0254)


# --- the species floors --------------------------------------------------------------------

def test_the_oak_floor_mirrors_floor_finishes_for_the_two_studies(catlin_model, bom):
    """Solid oak retreated to the studies on 2026-08-02: RM-A-STUDY plus RM-S-STUDY2,
    and the mirror row must equal the floor_finishes oak row to the digit."""
    oak = next(row for row in bom["wood_surfaces"] if row["material"] == "oak")
    assert oak["kind"] == "floor"
    assert oak["tags"] == ["RM-A-STUDY", "RM-S-STUDY2"]
    assert oak["also_in_floor_finishes"] is True
    primary = next(row for row in bom["floor_finishes"] if row["finish"] == "oak")
    assert set(primary["rooms"]) == {"RM-A-STUDY", "RM-S-STUDY2"}
    assert float(oak["net_area_sqft"]) == pytest.approx(
        float(primary["net_area_sqft"]), abs=0.05)


# --- UNKNOWN rows --------------------------------------------------------------------------

def test_an_unresolvable_paneling_material_reports_unknown(catlin_model) -> None:
    """A paneling whose material names nothing must surface as an UNKNOWN row, not bill
    zero — same philosophy as floor_finishes (the resolver also flags it, but the takeoff
    must not depend on someone reading findings)."""
    patched = dataclasses.replace(
        catlin_model,
        panelings=[dataclasses.replace(catlin_model.panelings[0],
                                       material_ref="no-such-wood",
                                       replaces_wall_finish=False)],
    )
    rows = wood_surfaces_takeoff(patched)
    unknown = next(row for row in rows if row["material"] == "UNKNOWN")
    assert unknown["known"] is False
    assert float(unknown["net_area_sqft"]) > 0.0
