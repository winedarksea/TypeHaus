"""Catlin's outdoor structures: porch pillars, the exterior junction box, the raised garden.

Three fixes that all live outside the conditioned envelope and share the ``catlin_model``
fixture: the balcony 6x6s embedded in the masonry railing, the NEMA 3R box moved up beside
the vent clamps, and the raised garden's SRW apron around the sunken garden.
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


def _floor(model, tag):
    return next(f for f in model.floors if f.tag == tag)


def _porch_deck_top(model):
    """Top of the composite boards over FS-SG-PORCH — the porch walking surface.

    There is no SL-SG-PORCH slab standing in for the porch floor any more; the floor system
    *is* the floor, so the surface underfoot is its joist tops plus the plank on them."""
    joists = [m for m in _floor(model, "FS-SG-PORCH").members if m.category == "joist"]
    assert joists, "FS-SG-PORCH must resolve joists to stand on"
    return max(m.z1_m for m in joists) + 1 * INCH  # SPEC.porch_deck_thickness_in


def _porch_outline(model):
    return [p.xy_m for p in model.plan.by_tag("FS-SG-PORCH").outline]


# --- porch 6x6 pillars embedded in the CMU railing ---------------------------
def test_pillars_start_at_the_top_of_the_railing_they_are_embedded_in(catlin_model) -> None:
    railing_top = _wall(catlin_model, "W-SG-RAIL-F").z1_m
    assert all(abs(_wall(catlin_model, tag).z1_m - railing_top) < 1e-9
               for tag in RAILING_WALL_TAGS)
    for tag in EMBEDDED_PILLAR_TAGS:
        assert abs(_solid(catlin_model, tag).z0_m - railing_top) < 1e-9, tag


def test_the_open_north_edge_pillar_still_bears_on_the_decking(catlin_model) -> None:
    porch_deck_top = _porch_deck_top(catlin_model)
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
#
# Rewritten 2026-07-25 with the structure itself. Until then the raised garden was a 36"
# planter bed: two parallel cheeks (a cast W-RG-INNER continuing W-SG-S upward, and the SRW
# W-RG-BLOCK south of it) holding soil between them, standing 3'-6" proud of grade. It is now
# a retaining apron wrapping the sunken garden on three sides, level with the retaining wall
# top and running 3' down. W-RG-INNER is deleted — W-SG-W2/E2/S are the apron's inner face.
_APRON_TAGS = ("W-RG-BLOCK", "W-RG-WEST", "W-RG-EAST",
               "W-RG-WEST-BALCONY", "W-RG-EAST-BALCONY")


def test_the_raised_garden_wraps_the_sunken_garden_as_a_u(catlin_model) -> None:
    """Three legs, with short returns closing each north end against the balcony."""
    assert not [w for w in catlin_model.walls if w.tag == "W-RG-INNER"], (
        "W-RG-INNER's job was to be the bed's inner cheek; the SG walls are that face now")
    walls = {tag: _wall(catlin_model, tag) for tag in _APRON_TAGS}
    assert {w.assembly for w in walls.values()} == {"RETAINING_BLOCK_12"}

    south, west, east = (walls[t] for t in _APRON_TAGS[:3])
    # The south leg runs corner to corner — 28', not the 20' it spanned as a bed cheek.
    assert abs(south.axis[1][0] - south.axis[0][0]) == pytest.approx(28 * FT, abs=1e-9)
    assert {round(y / FT, 4) for _, y in south.axis} == {-33.3333}
    # The legs run north from those corners to the arch wall's own axis plane.
    for leg in (west, east):
        assert {round(y / FT, 4) for _, y in leg.axis} == {-9.5, -33.3333}
    assert {round(x / FT, 4) for _, x in ((0, west.axis[0][0]), (0, west.axis[1][0]))} == {4.0}
    assert {round(x / FT, 4) for _, x in ((0, east.axis[0][0]), (0, east.axis[1][0]))} == {32.0}


def test_the_raised_garden_returns_three_feet_to_the_balcony(catlin_model) -> None:
    returns = {tag: _wall(catlin_model, tag) for tag in _APRON_TAGS[3:]}
    for tag, wall in returns.items():
        length = ((wall.axis[1][0] - wall.axis[0][0]) ** 2
                  + (wall.axis[1][1] - wall.axis[0][1]) ** 2) ** 0.5
        assert length == pytest.approx(3 * FT, abs=1e-9), tag
        assert {round(y / FT, 4) for _, y in wall.axis} == {-9.5}, tag
    west = returns["W-RG-WEST-BALCONY"]
    east = returns["W-RG-EAST-BALCONY"]
    assert {round(x / FT, 4) for x, _ in west.axis} == {4.0, 7.0}
    assert {round(x / FT, 4) for x, _ in east.axis} == {29.0, 32.0}


def test_the_apron_north_limit_is_the_arch_walls_own_plane(catlin_model) -> None:
    """Consumed from sunken_garden.py's exported contract, not re-derived — W-SG-RAIL-F and
    RL-SG-BALCONY sit on the same plane, and the legs stop there."""
    rail = _wall(catlin_model, "W-SG-RAIL-F")
    rail_y = sum(y for _, y in rail.axis) / 2.0
    for leg in ("W-RG-WEST", "W-RG-EAST"):
        assert max(y for _, y in _wall(catlin_model, leg).axis) == pytest.approx(rail_y)


def test_the_apron_tops_out_level_with_the_wall_it_wraps_and_runs_three_feet_down(
        catlin_model) -> None:
    retaining = _wall(catlin_model, "W-SG-S")
    for tag in _APRON_TAGS:
        leg = _wall(catlin_model, tag)
        assert abs(leg.z1_m - retaining.z1_m) < 1e-9, f"{tag} must cap level with W-SG-S"
        assert abs((leg.z1_m - leg.z0_m) - 3 * FT) < 1e-9, tag
        # Whole courses: a dry-stacked wall cannot end mid-unit. (Kept from the bed's own
        # test — it holds for the apron for exactly the same reason.)
        assert abs((leg.z1_m - leg.z0_m) % (6 * INCH)) < 1e-9, tag
        # Mostly below grade, which the user accepted explicitly. (Also kept.)
        assert leg.z0_m < 0.0, tag


def test_the_apron_clears_the_sunken_gardens_strip_footings(catlin_model) -> None:
    """"3' wider" reads from the SG walls' *outer faces*, not their axes. Measuring from the
    axis would put the legs inside FT-SG-W2/FT-SG-E2, which span x = [4.5, 11.5] and
    [24.5, 31.5] — the legs' inner faces land tangent to those, at 4.5 and 31.5."""
    for footing, leg, sign in (("FT-SG-W2", "W-RG-WEST", -1), ("FT-SG-E2", "W-RG-EAST", 1)):
        pad = _solid(catlin_model, footing)
        xs = [x for x, _ in pad.outline]
        wall = _wall(catlin_model, leg)
        axis_x = wall.axis[0][0]
        inner_face = axis_x - sign * 6 * INCH   # half the 12" SRW unit, toward the garden
        edge = min(xs) if sign < 0 else max(xs)
        assert inner_face == pytest.approx(edge, abs=1e-9), leg
        # Tangent, not overlapping: no part of the leg sits over the footing.
        assert (axis_x < min(xs)) if sign < 0 else (axis_x > max(xs)), leg


def test_the_south_leg_keeps_w_rg_blocks_identity_across_the_rewrite(catlin_model) -> None:
    """The IFC GlobalId is uuid5 over the uid, so preserving the uid is what keeps the wall
    the *same* wall to a downstream consumer rather than a delete plus an add."""
    block = catlin_model.plan.by_tag("W-RG-BLOCK")
    assert block.uid == "RGW102AAAA"
    # ...and the tag prefix the energy and grading exemptions match on is intact on all three.
    assert all(tag.startswith("W-RG-") for tag in _APRON_TAGS)


def test_raised_garden_is_not_part_of_the_thermal_envelope(catlin_model) -> None:
    """A landscape retaining wall has no prescriptive R-value; it encloses no space."""
    from typehaus.checks.code.mn_energy import evaluate_envelope

    components = {row.component for row in evaluate_envelope(catlin_model, catlin_model.plan)}
    assert "RETAINING_BLOCK_12" not in components
    # The sunken garden's own cast section stays out too — it always did, and deleting
    # W-RG-INNER must not have been the only thing keeping it out.
    assert "SUNKEN_GARDEN_WALL" not in components


# --- porch third pass: sonotube south-offset + gutter at the drip edge -------
def test_sonotube_column_and_bell_tuck_south_of_the_house_gap(catlin_model) -> None:
    """PT-SG-COL stands a south-offset inside the deck's north edge, so the 12" tube clears
    the house cladding and its 30" bell footing stops short of the house's own footing.

    How far short is not a free number: FT-B-S2's south face already lands on the deck's
    north-edge line, and the dowels cross a 40 psi XPS block between the two footings, so
    the bell's north face has to sit back by exactly that block's thickness. Everything
    here is read off the model — the offset itself included — so the assertion tracks
    ``SPEC.column_south_offset_in`` instead of restating it.
    """
    deck_edge_y = max(y for _, y in _porch_outline(catlin_model))
    column = _solid(catlin_model, "PT-SG-COL")
    column_y = sum(p[1] for p in column.outline) / len(column.outline)
    # The authored back-beam line is the offset's single source of truth.
    beam_line_y = catlin_model.plan.by_tag("N-SGM-COL").position.xy_m[1]
    assert column_y == pytest.approx(beam_line_y)
    assert column_y < deck_edge_y - 6 * INCH  # a real tuck, not "on the line"
    assert max(p[1] for p in column.outline) < deck_edge_y  # tube fully inside the edge

    bell = _solid(catlin_model, "FT-SG-COL")
    house_footing_s = min(y for _, y in _solid(catlin_model, "FT-B-S2").outline)
    foam = catlin_model.plan.by_tag("DW-SG-COL").foam_thickness.meters
    assert max(p[1] for p in bell.outline) == pytest.approx(house_footing_s - foam)
    # The back-beam line (and its midspan node) re-anchors to the same offset, collinear.
    for tag in ("BM-SG-BKW", "BM-SG-BKE"):
        beam = _solid(catlin_model, tag)
        for _, y in beam.outline:
            assert y == pytest.approx(column_y, abs=2 * INCH)  # within the beam half-width


def test_porch_joists_reach_the_deck_edge_without_oversailing_the_front_wall(
        catlin_model) -> None:
    """The porch's two joist ends are different, which one symmetric cantilever cannot say.

    South: the joists stop at the arched front wall — nothing runs out over 16" of concrete.
    North: they run the column's south-offset past the back-beam line, all the way to the
    deck's north edge, which is the overhang the porch actually has.
    """
    outline = _porch_outline(catlin_model)
    north, south = max(y for _, y in outline), min(y for _, y in outline)
    joists = [m for m in _floor(catlin_model, "FS-SG-PORCH").members if m.category == "joist"]
    assert joists
    tips = [max(m.p0[1], m.p1[1]) for m in joists]
    heels = [min(m.p0[1], m.p1[1]) for m in joists]
    assert max(tips) == pytest.approx(north)
    beam_line_y = catlin_model.plan.by_tag("N-SGM-COL").position.xy_m[1]
    assert max(tips) > beam_line_y  # it is a cantilever, not a flush end
    arch_axis_y = sum(y for _, y in _wall(catlin_model, "W-SG-ARCH").axis) / 2.0
    assert min(heels) == pytest.approx(arch_axis_y)  # flush at the bearing, no oversail
    # The balcony keeps its own symmetric 6" — the per-end split must not have leaked.
    balcony = catlin_model.plan.by_tag("FS-SG-DECK").joists
    assert balcony.cantilever.inches == pytest.approx(6.0)
    assert balcony.cantilever_start is None and balcony.cantilever_end is None


def test_balcony_gutter_rim_meets_the_drip_edge(catlin_model) -> None:
    """Water shedding off the drip flashing lands in the trough: the gutter's top meets
    the drip's lower edge instead of hanging 6" of open air below it."""
    bands = [s for s in catlin_model.solids if s.tag.startswith("TR-SG-GUTTER-1-")]
    assert {s.tag.rsplit("-", 1)[1] for s in bands} == {"BACK", "BOTTOM", "FRONT"}
    drip = _solid(catlin_model, "TR-SG-DRIP-1")
    # The channel is an open-top U, so its rim is the top of its tallest band.
    assert max(s.z1_m for s in bands) == pytest.approx(drip.z0_m)
