"""Catlin's outdoor structures: porch pillars, the exterior junction box, the raised garden.

Three fixes that all live outside the conditioned envelope and share the ``catlin_model``
fixture: the balcony 6x6s and where they bear, the NEMA 3R box moved up beside the vent
clamps, and the raised garden's SRW apron around the sunken garden.
"""

from __future__ import annotations

import pytest

from typehaus.resolve.placeables import resolved_mount_elevation

FT = 0.3048
INCH = 0.0254

# Pillar -> the concrete wall top it bears on. Until 2026-08-18 five of the six were
# grouted into a 42"-tall masonry parapet; retiring that guard dropped each of them onto
# whatever concrete it was standing over. That left the two front outer pillars on the
# retaining walls' +0'-6" step — but only because the W1/W2 junction node sat on their own
# axis, so each of them straddled the joint and the bearing map had to pick a side. Since
# 2026-08-21 `SunkenGardenSpec.side_wall_south_extension_in` runs the two porch side walls
# 6" past the front pillar line, so all four outer pillars bear on those two walls, at one
# elevation. What is left over is the *pair* of centre pillars, which miss every wall and
# bear on the decking.
PILLAR_BEARING_WALL = {"PT-SG-BR1": "W-SG-W1", "PT-SG-BR3": "W-SG-E1",
                       "PT-SG-BF1": "W-SG-W1", "PT-SG-BF3": "W-SG-E1"}
DECK_BORNE_PILLAR_TAGS = ("PT-SG-BR2", "PT-SG-BF2")
DECK_BORNE_PILLAR_TAG = "PT-SG-BR2"  # the one on the *cantilever*, not merely on the deck


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


# --- porch 6x6 pillars and what they bear on ---------------------------------
def test_pillars_start_at_the_top_of_the_wall_they_bear_on(catlin_model) -> None:
    for tag, wall_tag in PILLAR_BEARING_WALL.items():
        wall_top = _wall(catlin_model, wall_tag).z1_m
        assert abs(_solid(catlin_model, tag).z0_m - wall_top) < 1e-9, tag
    # One wall top, not two: every outer pillar lands on a porch side wall at the porch
    # floor. The +0'-6" retaining step still exists — it is what W-SG-W2/E2 stand at — but
    # it now begins 6" south of the front pillar line rather than under it, so the guard
    # runs out over the side walls' own tops at the front corners instead of returning
    # against a curb there.
    tops = {round(_wall(catlin_model, w).z1_m, 9) for w in PILLAR_BEARING_WALL.values()}
    assert tops == {0.0}
    step = {round(_wall(catlin_model, w).z1_m, 9) for w in ("W-SG-W2", "W-SG-E2")}
    assert len(step) == 1
    assert abs(step.pop() - 6 * INCH) < 1e-9


def test_the_side_walls_run_past_the_front_pillars_they_carry(catlin_model) -> None:
    """The reason the map above can name one wall per side.

    A 6x6 centred on the porch's front edge overhangs a wall that stops on that same line by
    half its width. Both side walls now end south of the pillar's own south face, so the
    bearing is real and not a rounding of which side of a node the post sits on.
    """
    for wall_tag, pillar_tag in (("W-SG-W1", "PT-SG-BF1"), ("W-SG-E1", "PT-SG-BF3")):
        wall_y = [p[1] for p in _wall(catlin_model, wall_tag).axis]
        pillar_y = [p[1] for p in _solid(catlin_model, pillar_tag).outline]
        assert min(wall_y) < min(pillar_y), wall_tag
        # 6" of extension past a 5 1/2" post centred on the edge leaves 3 1/4" of concrete
        # beyond its face — the side cover a square post base wants.
        assert min(pillar_y) - min(wall_y) > 3 * INCH, wall_tag


def test_the_centre_pillars_bear_on_the_decking(catlin_model) -> None:
    """Neither centre line has a wall under it — the porch's north edge is the house gap and
    its south edge is now a column and two beams — so both stand on the composite plank."""
    porch_deck_top = _porch_deck_top(catlin_model)
    for tag in DECK_BORNE_PILLAR_TAGS:
        assert abs(_solid(catlin_model, tag).z0_m - porch_deck_top) < 1e-9, tag


def test_every_pillar_top_lands_on_the_same_beam_soffit(catlin_model) -> None:
    """The invariant that survived retiring the masonry guard, and the real contract here.

    ``height`` is authored as ``beam_soffit - base (+ drainage rise)``, so lowering a base
    lengthens the post and leaves its top exactly where it was. Five of the six pillars
    dropped between 37" and 42" on 2026-08-18 and not one balcony elevation moved with them.
    """
    rear = {t: _solid(catlin_model, t) for t in ("PT-SG-BR1", "PT-SG-BR2", "PT-SG-BR3")}
    front = {t: _solid(catlin_model, t) for t in ("PT-SG-BF1", "PT-SG-BF2", "PT-SG-BF3")}
    for row in (rear, front):
        tops = [s.z1_m for s in row.values()]
        assert max(tops) - min(tops) < 1e-9
    # The rear row rides 2" proud of the front so the balcony drains south, away from the
    # house — the one deliberate difference between the two.
    assert abs(next(iter(rear.values())).z1_m
               - next(iter(front.values())).z1_m - 2 * INCH) < 1e-9


def test_post_bases_are_abu66ss_at_each_pillar_base(catlin_model) -> None:
    bases = [el for el in catlin_model.plan.all_elements()
             if el.element_kind == "Connector" and el.tag.startswith("CN-SG-BASE-")]
    assert len(bases) == 6
    assert {b.size for b in bases} == {"ABU66SS"}
    for base in bases:
        pillar = _solid(catlin_model, base.connects[0])
        assert abs(base.elevation.meters - pillar.z0_m) < 1e-9, base.tag
    bears_on = {b.connects[0]: b.connects[1] for b in bases}
    assert bears_on == {**PILLAR_BEARING_WALL,
                        **{t: "FS-SG-PORCH" for t in DECK_BORNE_PILLAR_TAGS}}


def test_the_deck_borne_pillar_stands_on_a_sistered_and_blocked_joist_line(catlin_model) -> None:
    """PT-SG-BR2 is the only pillar landing on framing, and it lands on the *cantilever*.

    A 6x6 on the free tip of one PT 2x8 is the load path that reinforcement answers, so
    the cluster is asserted where the post is, not merely somewhere on the deck: three
    plies (the authored joist plus two sisters) inside half a joist spacing of it, and
    solid blocking out to the neighbouring lines. ``structural.cantilever_point_load``
    reads exactly these two categories.
    """
    floor = _floor(catlin_model, "FS-SG-PORCH")
    post_x, post_y = catlin_model.plan.by_tag(DECK_BORNE_PILLAR_TAG).position.xy_m
    spacing = 16 * INCH
    sisters = [m for m in floor.members if m.category == "sister_joist"]
    blocks = [m for m in floor.members if m.category == "blocking"]
    assert len(sisters) == 2, "3-ply cluster = the joist + two sisters"
    assert all(abs(m.p0[0] - post_x) < spacing / 2 for m in sisters)
    assert len(blocks) == 2
    assert all(abs(m.p0[1] - post_y) < 0.3 for m in blocks)
    # The sisters run past the back-beam line the joists are split at, out to the tip the
    # post stands on — a ply stopping at the support would carry nothing under the load.
    joist_tip = max(max(m.p0[1], m.p1[1]) for m in floor.members if m.category == "joist")
    assert all(max(m.p0[1], m.p1[1]) == pytest.approx(joist_tip) for m in sisters)


def test_the_reinforced_line_is_tied_down_at_its_back_span_bearing(catlin_model) -> None:
    """Loading a cantilever tip pries the far end of that joist off its bearing; H2.5A
    (~455 lb) answers the ~0.45 kip of uplift, in the front-beam hangers the back span
    lands in. It named W-SG-ARCH until 2026-08-18, when that wall became two flush beams —
    the bearing is the same joint, held by the same part, in a different member."""
    tie = catlin_model.plan.by_tag("CN-SG-TIE-BR2")
    assert tie.kind.value == "hurricane_tie"
    assert tie.size == "H2.5A"
    assert set(tie.connects) == {"FS-SG-PORCH", "BM-SG-FRW", "BM-SG-FRE"}
    post_x, post_y = catlin_model.plan.by_tag(DECK_BORNE_PILLAR_TAG).position.xy_m
    tie_x, tie_y = tie.position.xy_m
    assert abs(tie_x - post_x) < 16 * INCH / 2, "not on the reinforced joist line"
    assert tie_y < post_y, "the tie belongs at the back-span bearing, not the loaded tip"


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


def test_the_apron_north_limit_is_the_porch_front_plane(catlin_model) -> None:
    """Consumed from sunken_garden.py's exported ``PORCH_FRONT_AXIS_Y_FT``, not re-derived.

    The plane was the arched cross-wall's axis and is the front column's now; the number did
    not move, which is the point of publishing it rather than letting two modules each do
    the arithmetic.
    """
    column_y = _solid(catlin_model, "PT-SG-FCOL").outline
    front_y = sum(y for _, y in column_y) / len(column_y)
    for leg in ("W-RG-WEST", "W-RG-EAST"):
        assert max(y for _, y in _wall(catlin_model, leg).axis) == pytest.approx(front_y)


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


def test_every_apron_leg_beds_on_a_levelling_pad_under_its_own_footprint(
        catlin_model) -> None:
    """A dry-stacked SRW wall has no footing; the compacted pad *is* what it stands on.

    So the bed hosts the wall directly (``FootingBedding.host_ref`` takes either), tops out
    at the wall underside, and runs 6" past each block face — 24" of band under a 12" block.
    """
    beds = {b.host: b for b in catlin_model.footing_beddings
            if b.host.startswith("W-RG-")}
    assert set(beds) == set(_APRON_TAGS)
    for tag in _APRON_TAGS:
        bed, wall = beds[tag], next(w for w in catlin_model.walls if w.tag == tag)
        assert bed.z1_m == pytest.approx(wall.z0_m), "the pad tops out at the block underside"
        assert (bed.z1_m - bed.z0_m) == pytest.approx(6 * INCH)
        assert _band_width(bed.outline) == pytest.approx(24 * INCH, abs=1e-6)
        # Bearing prep, not drainage: no tile, but fabric, or the clay silts the voids shut.
        assert not bed.drain_tile
        assert bed.geotextile


def test_the_apron_pads_butt_at_the_corners_rather_than_overlapping(catlin_model) -> None:
    """The stone at a corner is billed once. ``rect_between`` is not extended past an axis
    end (the convention ``_resolve_footing`` follows), so two legs meet at the shared node
    instead of double-counting a 2' x 2' square of excavation three times over."""
    beds = [b for b in catlin_model.footing_beddings if b.host.startswith("W-RG-")]
    south = next(b for b in beds if b.host == "W-RG-BLOCK")
    west = next(b for b in beds if b.host == "W-RG-WEST")
    south_y = {round(y, 6) for _, y in south.outline}
    west_y = {round(y, 6) for _, y in west.outline}
    # The south leg's band is the only one occupying its own y-range; the west leg stops on
    # the south leg's axis, which is the middle of that range and not its far edge.
    assert min(west_y) == pytest.approx((min(south_y) + max(south_y)) / 2.0)


def _band_width(outline) -> float:
    """Short side of a four-point band, in metres."""
    edges = [((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
             for (x0, y0), (x1, y1) in zip(outline, list(outline[1:]) + [outline[0]])]
    return min(edges)


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
    # The tolerance IS the beam's own half-width, and it is READ off the member rather than
    # written out: the pair went from a 3 1/2" two-ply LVL to a 4 1/2" three-ply KDAT 2x12
    # on 2026-08-23, and a hardcoded 2" quietly became a quarter-inch too tight for a beam
    # that had not moved at all.
    from typehaus.resolve.framing.profiles import cross_section

    half_width = cross_section(catlin_model.plan.by_tag("BM-SG-BKW").size).width_m / 2
    for tag in ("BM-SG-BKW", "BM-SG-BKE"):
        beam = _solid(catlin_model, tag)
        for _, y in beam.outline:
            assert y == pytest.approx(column_y, abs=half_width + 1e-9)


def test_porch_joists_reach_the_deck_edge_without_oversailing_the_front_wall(
        catlin_model) -> None:
    """The porch's two joist ends are different, which one symmetric cantilever cannot say.

    South: the joists stop dead on the front beam line — they hang *in* those beams, in
    hangers, so there is nothing to oversail. North: they run the column's south-offset past
    the back-beam line, all the way to the deck's north edge, which is the overhang the
    porch actually has.
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
    front_axis_y = catlin_model.plan.by_tag("N-SGM-FCOL").position.xy_m[1]
    assert min(heels) == pytest.approx(front_axis_y)  # flush at the bearing, no oversail
    assert min(heels) == pytest.approx(south)         # ... which is the deck's own edge
    # The balcony keeps its own symmetric 6" — the per-end split must not have leaked.
    balcony = catlin_model.plan.by_tag("FS-SG-DECK").joists
    assert balcony.cantilever.inches == pytest.approx(6.0)
    assert balcony.cantilever_start is None and balcony.cantilever_end is None


def test_balcony_gutter_rim_meets_the_drip_edge(catlin_model) -> None:
    """Water shedding off the drip flashing lands in the trough: the gutter's top meets
    the drip's lower edge instead of hanging 6" of open air below it.

    Both runs are formed metal composed out of bands — the gutter an open-top U, the drip a
    bent angle whose turn-down hangs off its outboard end (resolve/trim_bands.py). The
    turn-down is the piece that has to reach the rim, and it has to reach it *over the
    channel*: a drip that clears the rim outboard of the front sheet misses the trough.
    """
    bands = [s for s in catlin_model.solids if s.tag.startswith("TR-SG-GUTTER-1-")]
    assert {s.tag.rsplit("-", 1)[1] for s in bands} == {"BACK", "BOTTOM", "FRONT"}
    drip = [s for s in catlin_model.solids if s.tag.startswith("TR-SG-DRIP-1-")]
    assert {s.tag.rsplit("-", 1)[1] for s in drip} == {"LAP", "DRIP"}
    turn_down = _solid(catlin_model, "TR-SG-DRIP-1-DRIP")
    # The channel is an open-top U, so its rim is the top of its tallest band.
    assert max(s.z1_m for s in bands) == pytest.approx(turn_down.z0_m)
    # And the turn-down hangs between the two sheets, not past either of them.
    trough = _solid(catlin_model, "TR-SG-GUTTER-1-BOTTOM")
    span = [p[1] for p in trough.outline]
    drop = [p[1] for p in turn_down.outline]
    assert min(span) < min(drop) and max(drop) < max(span)
