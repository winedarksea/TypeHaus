"""Catlin's outdoor structures: porch pillars, the exterior junction box, the raised garden.

Three fixes that all live outside the conditioned envelope and share the ``catlin_model``
fixture: the balcony 6x6s embedded in the masonry railing, the NEMA 3R box moved up beside
the vent clamps, and the new 36" raised garden on the sunken-garden retaining wall.
"""

from __future__ import annotations

import pytest

from typehaus.resolve.placeables import resolved_mount_elevation

FT = 0.3048
INCH = 0.0254

RAILING_WALL_TAGS = ("W-SG-RAIL-F", "W-SG-RAIL-W", "W-SG-RAIL-E")
# The five pillars whose bases are grouted into a railing wall, and the one that is not:
# the porch's north edge is open, so the rear-centre pillar still stands on the decking.
EMBEDDED_PILLAR_TAGS = ("PT-SG-BF1", "PT-SG-BF2", "PT-SG-BF3", "PT-SG-BR1", "PT-SG-BR3")
DECK_BORNE_PILLAR_TAG = "PT-SG-BR2"


def _solid(model, tag):
    return next(s for s in model.solids if s.tag == tag)


def _wall(model, tag):
    return next(w for w in model.walls if w.tag == tag)


# --- porch 6x6 pillars embedded in the CMU railing ---------------------------
def test_pillars_start_at_the_top_of_the_railing_they_are_embedded_in(catlin_model) -> None:
    railing_top = _wall(catlin_model, "W-SG-RAIL-F").z1_m
    assert all(abs(_wall(catlin_model, tag).z1_m - railing_top) < 1e-9
               for tag in RAILING_WALL_TAGS)
    for tag in EMBEDDED_PILLAR_TAGS:
        assert abs(_solid(catlin_model, tag).z0_m - railing_top) < 1e-9, tag


def test_the_open_north_edge_pillar_still_bears_on_the_decking(catlin_model) -> None:
    porch_deck_top = _solid(catlin_model, "SL-SG-PORCH").z1_m
    assert abs(_solid(catlin_model, DECK_BORNE_PILLAR_TAG).z0_m - porch_deck_top) < 1e-9


def test_embedded_pillars_are_shorter_by_exactly_the_railing_height(catlin_model) -> None:
    """Same beam soffit above, base raised 42" — so the exposed post loses 42", no more."""
    rear_embedded = _solid(catlin_model, "PT-SG-BR1")
    rear_on_deck = _solid(catlin_model, DECK_BORNE_PILLAR_TAG)
    assert abs(rear_embedded.z1_m - rear_on_deck.z1_m) < 1e-9  # tops still carry one beam
    railing_height = rear_embedded.z0_m - rear_on_deck.z0_m
    assert abs(railing_height - 42 * INCH) < 1e-9
    assert abs((rear_on_deck.z1_m - rear_on_deck.z0_m)
               - (rear_embedded.z1_m - rear_embedded.z0_m) - railing_height) < 1e-9


def test_post_bases_are_abu66ss_at_each_pillar_base(catlin_model) -> None:
    bases = [el for el in catlin_model.plan.all_elements()
             if el.element_kind == "Connector" and el.tag.startswith("CN-SG-BASE-")]
    assert len(bases) == 6
    assert {b.size for b in bases} == {"ABU66SS"}
    for base in bases:
        pillar = _solid(catlin_model, base.connects[0])
        assert abs(base.elevation.meters - pillar.z0_m) < 1e-9, base.tag
    embedded = [b for b in bases if b.connects[1] in RAILING_WALL_TAGS]
    assert len(embedded) == len(EMBEDDED_PILLAR_TAGS)


# --- NEMA 3R weatherproof junction box ---------------------------------------
def test_nema_box_sits_with_the_vent_clamps_not_at_eye_level(catlin_model) -> None:
    box = catlin_model.plan.by_tag("ED-A-NEMA-JB")
    attic = next(s for s in catlin_model.plan.storeys if s.tag == "attic")
    box_z = resolved_mount_elevation(attic, box)
    clamp_z = [c.elevation.meters for c in catlin_model.plan.all_elements()
               if c.element_kind == "Connector" and c.tag.startswith("CN-M-VENT-CLAMP")]
    assert clamp_z, "no vent clamps to place the box against"
    assert min(abs(box_z - z) for z in clamp_z) < 6 * INCH
    assert box_z > 20 * FT  # up on the gable, not on the main-storey wall it used to ride


def test_nema_box_and_its_clamp_ride_the_same_gable_wall_at_the_same_height(catlin_model) -> None:
    clamp = catlin_model.plan.by_tag("CN-A-NEMA-CLAMP")
    box = catlin_model.plan.by_tag("ED-A-NEMA-JB")
    attic = next(s for s in catlin_model.plan.storeys if s.tag == "attic")
    assert clamp.connects == ("ED-A-NEMA-JB", "W-A-N2")
    assert clamp.position.xy_m == box.position.xy_m
    assert abs(clamp.elevation.meters - resolved_mount_elevation(attic, box)) < 1e-9
    # The gable siding must still reach it: the 4:12 rake is highest toward the x=18' ridge.
    gable = _wall(catlin_model, "W-A-N2")
    assert clamp.elevation.meters < gable.z1_m


# --- raised garden ------------------------------------------------------------
def test_raised_garden_is_36_inches_high_off_the_retaining_wall_it_uses(catlin_model) -> None:
    retaining = _wall(catlin_model, "W-SG-S")
    inner = _wall(catlin_model, "W-RG-INNER")
    assert abs(inner.z0_m - retaining.z1_m) < 1e-9, "inner cheek must bear on the wall's top"
    assert abs((inner.z1_m - inner.z0_m) - 36 * INCH) < 1e-9


def test_raised_garden_outer_face_is_retaining_block_topping_out_with_the_bed(catlin_model) -> None:
    inner = _wall(catlin_model, "W-RG-INNER")
    block = _wall(catlin_model, "W-RG-BLOCK")
    assert block.assembly == "RETAINING_BLOCK_12"
    assert abs(block.z1_m - inner.z1_m) < 1e-9  # both cheeks cap the bed at one elevation
    assert block.z0_m < 0.0, "the SRW base course is buried below grade"
    # Whole courses: a dry-stacked wall cannot end mid-unit.
    assert abs((block.z1_m - block.z0_m) % (6 * INCH)) < 1e-9


def test_raised_garden_bed_sits_outside_the_sunken_garden(catlin_model) -> None:
    """Inner cheek on the retaining wall's axis, block wall south of it, soil in between."""
    retaining = _wall(catlin_model, "W-SG-S")
    inner = _wall(catlin_model, "W-RG-INNER")
    block = _wall(catlin_model, "W-RG-BLOCK")
    inner_y = [y for _, y in inner.axis]
    retaining_y = [y for _, y in retaining.axis]
    block_y = [y for _, y in block.axis]
    assert inner_y == pytest.approx(retaining_y)  # shares the wall it builds on
    assert max(block_y) < min(inner_y), "block wall must be south (-Y) of the inner cheek"


def test_raised_garden_is_not_part_of_the_thermal_envelope(catlin_model) -> None:
    """A landscape retaining wall has no prescriptive R-value; it encloses no space."""
    from typehaus.checks.code.mn_energy import evaluate_envelope

    components = {row.component for row in evaluate_envelope(catlin_model, catlin_model.plan)}
    assert "RETAINING_BLOCK_12" not in components
    # The inner cheek reuses the sunken garden's cast section; it must not drag that
    # already-exempt assembly back into the table either.
    assert "SUNKEN_GARDEN_WALL" not in components


# --- porch third pass: sonotube south-offset + gutter at the drip edge -------
def test_sonotube_column_and_bell_tuck_south_of_the_house_gap(catlin_model) -> None:
    """PT-SG-COL stands a SPEC south-offset (15") inside the deck's north edge, so the
    12" tube clears the house cladding and its 30" bell footing's north face lands exactly
    on the north-edge line — the doweled thermal-break joint plane."""
    deck_edge_y = max(p[1] for p in _solid(catlin_model, "SL-SG-PORCH").outline)
    column = _solid(catlin_model, "PT-SG-COL")
    column_y = sum(p[1] for p in column.outline) / len(column.outline)
    assert column_y == pytest.approx(deck_edge_y - 15 * INCH)
    assert max(p[1] for p in column.outline) < deck_edge_y  # tube fully inside the edge
    bell = _solid(catlin_model, "FT-SG-COL")
    assert max(p[1] for p in bell.outline) == pytest.approx(deck_edge_y)
    # The back-beam line (and its midspan node) re-anchors to the same offset, collinear.
    for tag in ("BM-SG-BKW", "BM-SG-BKE"):
        beam = _solid(catlin_model, tag)
        for _, y in beam.outline:
            assert y == pytest.approx(column_y, abs=2 * INCH)  # within the beam half-width


def test_balcony_gutter_rim_meets_the_drip_edge(catlin_model) -> None:
    """Water shedding off the drip flashing lands in the trough: the gutter's top meets
    the drip's lower edge instead of hanging 6" of open air below it."""
    gutter = _solid(catlin_model, "TR-SG-GUTTER-1")
    drip = _solid(catlin_model, "TR-SG-DRIP-1")
    assert gutter.z1_m == pytest.approx(drip.z0_m)
