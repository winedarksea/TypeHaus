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

# Pillar -> the concrete wall top it bears on. `SunkenGardenSpec.side_wall_south_extension_in`
# runs the two porch side walls 6" past the front pillar line, so all four outer pillars bear
# on those two walls, at one elevation. The *pair* of centre pillars miss every wall and bear
# on the decking instead.
PILLAR_BEARING_WALL = {"PT-SG-BR1": "W-SG-W1", "PT-SG-BR3": "W-SG-E1",
                       "PT-SG-BF1": "W-SG-W1", "PT-SG-BF3": "W-SG-E1"}
# Both CENTRE pillars bear on the porch decking, 3" inside their own beam line, and take
# squash blocks. PT-SG-BF2 stood on PT-SG-FCOL's top from 2026-08-29 to 2026-09-03; moving
# it north made all six pillars one member and let that column shrink from 20" round to 12".
DECK_BORNE_PILLAR_TAGS = ("PT-SG-BR2", "PT-SG-BF2")
#: The four CORNER pillars became 12" round cast concrete columns on 2026-09-03, fixed at
#: their bases and doweled into the wall tops they stand on. They are the balcony's entire
#: lateral system, and they take no post base at all — concrete on concrete is a lapped
#: splice made in the pour, not a connector.
CORNER_COLUMN_TAGS = ("PT-SG-BR1", "PT-SG-BR3", "PT-SG-BF1", "PT-SG-BF3")
#: Half a 12" round.
COLUMN_RADIUS_IN = 6.0
#: The cage's bar circle: 6" less 2" cover, a #3 tie and half a #5 bar.
DOWEL_CIRCLE_RADIUS_IN = 3.3125


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
    # floor. The +0'-6" retaining step is what W-SG-W2/E2 stand at, begins 6" south of the
    # front pillar line, and runs out over the side walls' own tops at the front corners.
    tops = {round(_wall(catlin_model, w).z1_m, 9) for w in PILLAR_BEARING_WALL.values()}
    assert tops == {0.0}
    step = {round(_wall(catlin_model, w).z1_m, 9) for w in ("W-SG-W2", "W-SG-E2")}
    assert len(step) == 1
    assert abs(step.pop() - 6 * INCH) < 1e-9


def test_the_side_walls_run_past_the_front_pillars_they_carry(catlin_model) -> None:
    """The reason the map above can name one wall per side.

    A pillar centred on the porch's front edge overhangs a wall that stops on that same line
    by half its width. Both side walls end south of the pillar's own south face, so the
    bearing is real and not a rounding of which side of a node the post sits on.

    **What "enough" means changed with the pillar.** While these were 5 1/2" 6x6s on square
    post bases, the rule was the 3" of side cover a base wants past its plate. They are 12"
    cast columns now, doweled into the wall top, and nothing is bolted to that top at all —
    so what has to clear is the CAGE. The southernmost #5 dowel sits on a 6 5/8" bar circle,
    3 5/16" off the column axis, and it is that bar's cover to the end of the wall that is
    the real edge distance. The column face itself lands 2 3/4" inside the wall end, which
    is thin to look at and carries nothing: a 12" column delivering under 4 kip onto a 12"
    wall spreads into it long before the end matters.
    """
    for wall_tag, pillar_tag in (("W-SG-W1", "PT-SG-BF1"), ("W-SG-E1", "PT-SG-BF3")):
        wall_y = [p[1] for p in _wall(catlin_model, wall_tag).axis]
        pillar_y = [p[1] for p in _solid(catlin_model, pillar_tag).outline]
        assert min(wall_y) < min(pillar_y), wall_tag
        # The whole column is on the wall, cage and all, with cover to spare on the bars.
        axis_y = catlin_model.plan.by_tag(pillar_tag).position.xy_m[1]
        dowel_south = axis_y - DOWEL_CIRCLE_RADIUS_IN * INCH
        assert dowel_south - min(wall_y) > 4 * INCH, wall_tag


def test_the_centre_pillars_bear_on_the_decking(catlin_model) -> None:
    """Neither centre line has a wall under it — the porch's north edge is the house gap and
    its south edge is now a column and two beams — so both stand on the composite plank."""
    porch_deck_top = _porch_deck_top(catlin_model)
    for tag in DECK_BORNE_PILLAR_TAGS:
        assert abs(_solid(catlin_model, tag).z0_m - porch_deck_top) < 1e-9, tag


def test_every_pillar_top_lands_on_the_same_beam_soffit(catlin_model) -> None:
    """The invariant that survived retiring the masonry guard, and the real contract here.

    ``height`` is authored as ``beam_soffit - base (+ drainage rise)``, so lowering a base
    lengthens the post and leaves its top exactly where it was.
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


def test_only_the_two_wood_pillars_take_a_post_base(catlin_model) -> None:
    """Six ABU66SS until 2026-09-03, two now — and the four that went are the point.

    A 12" cast column standing on a 12" cast wall is joined by a lapped doweled splice made
    in the pour. Authoring a standoff base there would bill four stainless bases that do not
    exist AND claim a pinned joint, which is the opposite of the fixed one the whole
    braceless design turns on.
    """
    bases = [el for el in catlin_model.plan.all_elements()
             if el.element_kind == "Connector" and el.tag.startswith("CN-SG-BASE-")]
    assert len(bases) == 2
    assert {b.size for b in bases} == {"ABU66SS"}
    for base in bases:
        pillar = _solid(catlin_model, base.connects[0])
        assert abs(base.elevation.meters - pillar.z0_m) < 1e-9, base.tag
    bears_on = {b.connects[0]: b.connects[1] for b in bases}
    assert bears_on == {t: "FS-SG-PORCH" for t in DECK_BORNE_PILLAR_TAGS}


def test_the_corner_columns_are_cast_concrete_with_a_cage(catlin_model) -> None:
    """The four members that replaced the knee braces, asserted at the model level.

    ``size`` must be the ROUND spelling: a nominal-looking "12x12" matches ``_RE_NOMINAL``
    in ``resolve/framing/profiles.py``, misses LUMBER_ACTUAL and silently resolves to
    1.5x5.5 — a 12" column drawn as a 2x6, at 0 FAIL. And ``vertical_reinforcement`` must be
    stated: ACI 318-19 §14.1.5 does not permit a plain concrete COLUMN at any stress, so
    without it ``deck_post/<tag>`` reports INCOMPLETE however well the section does.
    """
    from typehaus.resolve.assembly_material import assembly_structure_material

    for tag in CORNER_COLUMN_TAGS:
        post = catlin_model.plan.by_tag(tag)
        assert post.size == "12 round", tag
        assert post.assembly == "SUNKEN_GARDEN_COLUMN_12", tag
        assert assembly_structure_material(catlin_model.plan, post.assembly) == "concrete"
        assert post.vertical_reinforcement, tag
        # The round really is 12" on the ground, not a 2x6 the size string was misread as.
        outline = _solid(catlin_model, tag).outline
        xs = [p[0] for p in outline]
        assert max(xs) - min(xs) == pytest.approx(2 * COLUMN_RADIUS_IN * INCH, abs=1e-3), tag


def test_the_corner_columns_are_flush_with_both_faces_of_the_wall_they_stand_on(
        catlin_model) -> None:
    """12" round on a 12" wall, centred on its axis: no ledge on either side to pond on.

    This is one of the two things that made 12" the right diameter rather than the 10" first
    drafted (the other is the 2" of cover a #5 cage needs). It also keeps BF3's east leader
    clear — a 3" pipe dropping outside the east wall's outer face at x 28.625 has 1 1/2" to
    the column, which a 20" round would have eaten.
    """
    for tag, wall_tag in PILLAR_BEARING_WALL.items():
        # A ResolvedWall carries an axis and a thickness, not a plan outline, so the two
        # faces are the axis +/- half the wall.
        wall = _wall(catlin_model, wall_tag)
        axis_x = wall.axis[0][0]
        half = wall.thickness_m / 2.0
        column_xs = [p[0] for p in _solid(catlin_model, tag).outline]
        assert min(column_xs) == pytest.approx(axis_x - half, abs=1e-3), tag
        assert max(column_xs) == pytest.approx(axis_x + half, abs=1e-3), tag


def test_the_deck_borne_pillars_stand_over_a_bearing_not_a_joist_tip(catlin_model) -> None:
    """The load path the two CENTRE pillars actually stand on, asserted directly.

    Each sits 3" inside its own beam line, over the beams that run to their cast columns —
    no cantilever. Each still bears CROSS-GRAIN: a 6x6 on one 1 1/2" ply is ~315 psi against
    an Fc-perp of 425, so squash blocks are here — but with ``plies=1``, which lays
    ``range(plies - 1)`` sisters, i.e. NONE. Blocking without sistering is the whole
    distinction, and it is what keeps ``test_no_catlin_deck_sisters_a_joist`` green.

    The 3" is not slop either. The band in ``checks/structural/cantilever.py`` is closed at
    the bearing line, so a pillar landed exactly on it still reads as inside the overhang
    and reports a 0" one — a finding about a joint that does not exist. It is also the
    minimum that keeps BF2's 5 1/2" post on the deck, whose outline ends on the front beam
    axis, and what keeps its base off TR-SG-CAP-FRW/FRE and the butyl under it.
    """
    floor = _floor(catlin_model, "FS-SG-PORCH")
    assert [m for m in floor.members if m.category == "sister_joist"] == []
    blocks = [m for m in floor.members if m.category == "blocking"]
    # Two under each centre pillar, plus two under each of the porch guard's three
    # south-leg posts — see test_joist_reinforcement.py, which owns that count.
    assert len(blocks) == 10, len(blocks)

    porch_deck_top = _porch_deck_top(catlin_model)
    for tag in DECK_BORNE_PILLAR_TAGS:
        assert _solid(catlin_model, tag).z0_m == pytest.approx(porch_deck_top), tag
    joist_tip = max(max(m.p0[1], m.p1[1]) for m in floor.members if m.category == "joist")
    back_beam_y = max(p[1] for p in _solid(catlin_model, "BM-SG-BKW").outline)
    br2_y = catlin_model.plan.by_tag("PT-SG-BR2").position.xy_m[1]
    assert br2_y < back_beam_y < joist_tip

    # 3" inside each beam line, mirrored about the deck.
    column_y = catlin_model.plan.by_tag("PT-SG-COL").position.xy_m[1]
    assert (column_y - br2_y) == pytest.approx(3 * INCH, abs=1e-9)
    fcol_y = catlin_model.plan.by_tag("PT-SG-FCOL").position.xy_m[1]
    bf2_y = catlin_model.plan.by_tag("PT-SG-BF2").position.xy_m[1]
    assert (bf2_y - fcol_y) == pytest.approx(3 * INCH, abs=1e-9)


def test_the_front_pillar_tops_are_roofed_by_the_beams_that_land_on_them(
        catlin_model) -> None:
    """The balcony's front posts sit half a post NORTH of the beam ends they carry.

    BM-SG-BLW/BLC/BLE *terminate* on the front pillar line — those are their south nodes.
    A beam stopped on its post's AXIS covers the north half of that post's top and leaves
    the south 2 3/4", full width, open to the sky, with a re-entrant corner against the beam
    face for water to sit in. Nobody frames it that way; the beam is pushed out flush with
    the post's south face so the member roofs the end grain it bears on.

    Modelled by moving the POSTS north rather than the beam ends south, because the beam
    ends are also the deck edge, the fascia line, the drip, the gutter, and
    ``BALCONY_FRONT_AXIS_Y_FT``, which raised_garden.py consumes — none of those should
    shift for a bearing detail.

    Only a post at a beam's END has the problem, which is why the REAR row is exempt and
    asserted so here: at ``_y_rear_pillar`` the beams run 20" further north, so BR1/2/3 are
    mid-span under a continuous member and already covered.

    **The row DID move when the corners became 12" columns — 5 1/4" north, and the offset
    is the round's radius now, not half a 6x6.** For one day it stayed on the wood post's
    2 3/4", which put a 6" radius 3 1/4" PAST the beam end: the beam roofed nothing and sat
    on the north half of a concrete shelf that collected water against its own end grain
    and against the HGAM10 seat. The offset is ``radius + 2"`` instead, so the glulam
    cantilevers 2" past the column's south face and drips into air.

    The 2" is a weather number, and what it costs is written down at ``_y_front_pillar``:
    RL-SG-PORCH's two front corner posts lose their baseplates and land on the columns, and
    the beams' 20" north overhang now sits against an R507.5.1 limit of 22" rather than 24".
    """
    # PT-SG-BF2 is exempt now for the REAR row's reason rather than the front row's: it
    # moved 15" north onto the porch deck on 2026-09-03, so BM-SG-BLC runs past it to the
    # deck edge and it is mid-span under a continuous member, exactly like BR2.
    bf2 = _solid(catlin_model, "PT-SG-BF2")
    blc = _solid(catlin_model, "BM-SG-BLC")
    assert min(p[1] for p in blc.outline) < min(p[1] for p in bf2.outline)
    # The two front CORNERS are 12" rounds, and their beams cantilever 2" past them.
    for tag, beam_tag in (("PT-SG-BF1", "BM-SG-BLW"), ("PT-SG-BF3", "BM-SG-BLE")):
        column_south = min(p[1] for p in _solid(catlin_model, tag).outline)
        beam_south = min(p[1] for p in _solid(catlin_model, beam_tag).outline)
        assert beam_south < column_south, tag
        assert column_south - beam_south == pytest.approx(2.0 * INCH, abs=1e-3), tag
    # The rear row is exempt: the beams run 20" further north past it.
    for tag, beam_tag in (("PT-SG-BR1", "BM-SG-BLW"), ("PT-SG-BR3", "BM-SG-BLE")):
        post = _solid(catlin_model, tag)
        beam = _solid(catlin_model, beam_tag)
        assert min(p[1] for p in beam.outline) < min(p[1] for p in post.outline), tag


def test_no_balcony_pillar_top_carries_more_than_one_member(catlin_model) -> None:
    """Every balcony pillar top carries exactly one bearing member — its own N-S beam.

    The two E-W brace rails that used to run through all six posts carried
    ``bearing_refs=()`` on purpose: a rail claiming a post would bill a strap at a joint
    that is not real beam-on-post bearing (``takeoff/uplift_joints.py``). Both rails were
    deleted with the knee braces on 2026-09-03, so what this now guards is the other half —
    no post may ever gain a second bearing member, and nothing but a beam may claim one.
    """
    pillar_tags = ("PT-SG-BR1", "PT-SG-BR2", "PT-SG-BR3",
                   "PT-SG-BF1", "PT-SG-BF2", "PT-SG-BF3")
    beams = [el for el in catlin_model.plan.all_elements()
             if getattr(el, "tag", "").startswith("BM-SG-")]
    for tag in pillar_tags:
        bearing = [b.tag for b in beams if tag in getattr(b, "bearing_refs", ())]
        assert len(bearing) == 1, (tag, bearing)
    for beam in beams:
        if beam.tag.startswith("BM-SG-RAIL-"):
            assert beam.bearing_refs == (), beam.tag


def test_the_front_column_is_centred_on_the_span_its_top_has_to_reach(
        catlin_model) -> None:
    """PT-SG-FCOL sits ON the beam axis, and the 20" sizing essay it used to carry is gone.

    It was a 20" round centred 4 7/8" SOUTH of the beam axis, sized to span from the front
    beams' north face to PT-SG-BF2's south face because that pillar stood on its top. BF2
    moved north onto the porch deck on 2026-09-03, so this column seats two collinear beam
    ends and nothing else — and a column carrying two collinear beam ends belongs on their
    axis.

    12" and not 10", for the reason the four balcony corners are 12": it leaves 3 3/4" of
    concrete beside each beam end for the HGAM10's Titen Turbo screws, against Simpson's
    1 1/2" minimum, where a 10" round would leave 2 3/4".
    """
    column = _solid(catlin_model, "PT-SG-FCOL")
    ys = [p[1] for p in column.outline]
    assert max(ys) - min(ys) == pytest.approx(12 * INCH, abs=1e-3)

    beam_axis = catlin_model.plan.by_tag("N-SGM-FCOL").position.xy_m[1]
    axis = catlin_model.plan.by_tag("PT-SG-FCOL").position.xy_m[1]
    assert axis == pytest.approx(beam_axis, abs=1e-9), "the column drifted off the beam axis"

    # 3 3/4" of concrete beside a 4 1/2" beam end centred on the same axis.
    beam = _solid(catlin_model, "BM-SG-FRW")
    beam_ys = [p[1] for p in beam.outline]
    beam_half = (max(beam_ys) - min(beam_ys)) / 2.0
    assert COLUMN_RADIUS_IN * INCH - beam_half == pytest.approx(3.75 * INCH, abs=1e-3)


def test_the_two_beam_on_column_ties_reach_concrete(catlin_model) -> None:
    """CN-SG-TIE-COL and CN-SG-TIE-FCOL hold two beam ends down to a cast column top.

    Both are HGAM10 masonry gusset angles: #14 screws into the wood leg, Titen Turbo into
    the concrete — an H2.5A's published values are nails into lumber on BOTH legs, which
    would splice the two beam ends across the pour instead of holding either down to it.
    The ``ConnectorKind`` is unchanged on purpose — ``takeoff/uplift.py`` keys the
    beam-to-post link on the kind and never on the size, so this moves the BOM and no
    finding. No authored H2.5A is left in the house.
    """
    for tag, column in (("CN-SG-TIE-COL", "PT-SG-COL"), ("CN-SG-TIE-FCOL", "PT-SG-FCOL")):
        tie = catlin_model.plan.by_tag(tag)
        assert tie.kind.value == "hurricane_tie", tag
        assert tie.size == "HGAM10", tag
        assert column in tie.connects, tag

    authored = [el for el in catlin_model.plan.all_elements()
                if el.element_kind == "Connector" and getattr(el, "size", None) == "H2.5A"]
    assert authored == []
    assert not any(el.tag == "CN-SG-TIE-BR2"
                   for el in catlin_model.plan.all_elements())


# --- NEMA 3R weatherproof junction box ---------------------------------------
def test_nema_box_sits_with_the_vent_clamps_not_at_eye_level(catlin_model) -> None:
    box = catlin_model.plan.by_tag("ED-A-NEMA-JB")
    attic = next(s for s in catlin_model.plan.storeys if s.tag == "attic")
    box_z = resolved_mount_elevation(attic, box)
    clamp_z = [c.elevation.meters for c in catlin_model.plan.all_elements()
               if c.element_kind == "Connector" and c.tag.startswith("CN-M-VENT-CLAMP")]
    assert clamp_z, "no vent clamps to place the box against"
    assert min(abs(box_z - z) for z in clamp_z) < 6 * INCH
    assert box_z > 20 * FT  # up on the gable, not the main-storey wall


def test_the_gable_enclosures_carry_no_seam_clamp_on_an_exposed_fastener_wall(
    catlin_model,
) -> None:
    """The NEMA box and the PV junction box keep their gable perch; their clamps do not.

    An S-5! seam clamp closes on a standing-seam leg, and `pbr-panel-26` has no leg — the
    fixing is uninstallable on this wall, so neither clamp exists. Neither box sits on the
    roof: the 4:12 rake at x=4' and x=9' is well above their ~25'-6" elevation, so what has
    to hold is that the boxes ride W-A-N2's gable, below its rake.
    """
    attic = next(s for s in catlin_model.plan.storeys if s.tag == "attic")
    gable = _wall(catlin_model, "W-A-N2")
    for tag in ("CN-A-NEMA-CLAMP", "CN-A-PV-CLAMP"):
        assert catlin_model.plan.by_tag(tag) is None, (
            f"{tag} clamps a seam the wall no longer has; see plan/wind_clamps.py")
    for tag in ("ED-A-NEMA-JB", "ED-A-PV-JB"):
        box = catlin_model.plan.by_tag(tag)
        assert box is not None, f"{tag} is the enclosure itself and must survive the swap"
        # The gable siding must still reach it: the 4:12 rake is highest toward the x=18' ridge.
        assert resolved_mount_elevation(attic, box) < gable.z1_m


# --- raised garden ------------------------------------------------------------
#
# A retaining apron wrapping the sunken garden on three sides, level with the retaining wall
# top and running 3' down. W-SG-W2/E2/S are the apron's inner face; there is no W-RG-INNER.
_APRON_TAGS = ("W-RG-BLOCK", "W-RG-WEST", "W-RG-EAST",
               "W-RG-WEST-BALCONY", "W-RG-EAST-BALCONY")


def test_the_raised_garden_wraps_the_sunken_garden_as_a_u(catlin_model) -> None:
    """Three legs, with short returns closing each north end against the balcony."""
    assert not [w for w in catlin_model.walls if w.tag == "W-RG-INNER"], (
        "W-RG-INNER's job was to be the bed's inner cheek; the SG walls are that face now")
    walls = {tag: _wall(catlin_model, tag) for tag in _APRON_TAGS}
    assert {w.assembly for w in walls.values()} == {"RETAINING_BLOCK_12"}

    south, west, east = (walls[t] for t in _APRON_TAGS[:3])
    # The south leg runs corner to corner, 28'.
    assert abs(south.axis[1][0] - south.axis[0][0]) == pytest.approx(28 * FT, abs=1e-9)
    assert {round(y / FT, 4) for _, y in south.axis} == {-33.3333}
    # The legs run north from those corners to the arch wall's own axis plane, at -10.5: the
    # apron closes against RL-SG-BALCONY (``BALCONY_FRONT_AXIS_Y_FT``), not -9.5.
    for leg in (west, east):
        assert {round(y / FT, 4) for _, y in leg.axis} == {-10.5, -33.3333}
    assert {round(x / FT, 4) for _, x in ((0, west.axis[0][0]), (0, west.axis[1][0]))} == {4.0}
    assert {round(x / FT, 4) for _, x in ((0, east.axis[0][0]), (0, east.axis[1][0]))} == {32.0}


def test_the_raised_garden_returns_three_feet_to_the_balcony(catlin_model) -> None:
    returns = {tag: _wall(catlin_model, tag) for tag in _APRON_TAGS[3:]}
    for tag, wall in returns.items():
        length = ((wall.axis[1][0] - wall.axis[0][0]) ** 2
                  + (wall.axis[1][1] - wall.axis[0][1]) ** 2) ** 0.5
        assert length == pytest.approx(3 * FT, abs=1e-9), tag
        assert {round(y / FT, 4) for _, y in wall.axis} == {-10.5}, tag
    west = returns["W-RG-WEST-BALCONY"]
    east = returns["W-RG-EAST-BALCONY"]
    assert {round(x / FT, 4) for x, _ in west.axis} == {4.0, 7.0}
    assert {round(x / FT, 4) for x, _ in east.axis} == {29.0, 32.0}


def test_the_apron_north_limit_is_the_balcony_front_plane(catlin_model) -> None:
    """Consumed from sunken_garden.py's exported ``BALCONY_FRONT_AXIS_Y_FT``, not re-derived.

    ``PORCH_FRONT_AXIS_Y_FT`` and ``BALCONY_FRONT_AXIS_Y_FT`` are 12" apart, and the apron
    closes against the balcony RAILING, so it follows the balcony. Read off that guard's own
    south run rather than off the front column, which is on neither plane — it sits 4 7/8"
    south of the porch's, centred on the 14 1/4" its top has to span between the two beams'
    north face and PT-SG-BF2's south face.
    """
    guard = catlin_model.plan.by_tag("RL-SG-BALCONY")
    front_y = min(p.xy_m[1] for p in guard.path)
    for leg in ("W-RG-WEST", "W-RG-EAST"):
        assert max(y for _, y in _wall(catlin_model, leg).axis) == pytest.approx(front_y)


def test_the_apron_tops_out_level_with_the_wall_it_wraps_and_runs_three_feet_down(
        catlin_model) -> None:
    retaining = _wall(catlin_model, "W-SG-S")
    for tag in _APRON_TAGS:
        leg = _wall(catlin_model, tag)
        assert abs(leg.z1_m - retaining.z1_m) < 1e-9, f"{tag} must cap level with W-SG-S"
        assert abs((leg.z1_m - leg.z0_m) - 3 * FT) < 1e-9, tag
        # Whole courses: a dry-stacked wall cannot end mid-unit.
        assert abs((leg.z1_m - leg.z0_m) % (6 * INCH)) < 1e-9, tag
        assert leg.z0_m < 0.0, tag  # mostly below grade, user-accepted


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
    # The sunken garden's own cast section stays out too.
    assert "SUNKEN_GARDEN_WALL" not in components


# --- porch third pass: sonotube south-offset + gutter at the drip edge -------
def test_sonotube_column_and_bell_tuck_south_of_the_house_gap(catlin_model) -> None:
    """PT-SG-COL stands a south-offset inside the deck's north edge, so the 12" tube clears
    the house cladding and its 30" bell footing stops short of the house's own footing.

    How far short is not a free number: FT-B-S2's south face already lands on the deck's
    north-edge line, and the bell's north face sits back 2" from it. Everything here is
    read off the model — the offset itself included — so the assertion tracks
    ``SPEC.column_south_offset_in`` instead of restating it.

    The bell is augered to frost depth, so the two footings do not meet at one elevation and
    there is no joint to dowel or bridge to break. The 2" clearance is 17" of column offset
    less the bell's own 15" reach.
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
    bell_north = max(p[1] for p in bell.outline)
    assert bell_north < house_footing_s, "the bell stops short of the house's own footing"
    assert house_footing_s - bell_north == pytest.approx(2 * INCH)
    assert catlin_model.plan.by_tag("DW-SG-COL") is None
    assert {d.tag for d in catlin_model.plan.all_elements()
            if d.element_kind == "Dowel"} == {"DW-SG-W1", "DW-SG-E1"}
    # The back-beam line (and its midspan node) re-anchors to the same offset, collinear.
    # The tolerance IS the beam's own half-width, READ off the member (a 4 1/2" three-ply
    # KDAT 2x12) rather than written out as a hardcoded number.
    from typehaus.resolve.framing.profiles import cross_section

    half_width = cross_section(catlin_model.plan.by_tag("BM-SG-BKW").size).width_m / 2
    for tag in ("BM-SG-BKW", "BM-SG-BKE"):
        beam = _solid(catlin_model, tag)
        for _, y in beam.outline:
            assert y == pytest.approx(column_y, abs=half_width + 1e-9)


def test_the_two_porch_piers_are_belled_to_frost_depth_without_moving_a_beam_soffit(
        catlin_model) -> None:
    """The bell sits at frost depth and the shaft grew to suit.

    The owner's call was to auger these two to 42" rather than lean on the aggregate
    section the wall footings lean on ("bell bottom piers as part of the sonotube
    installation"). What makes that a two-element change rather than a one-number change is
    that a ``Footing`` under a ``Post`` tops out on its storey datum unless it authors a
    ``bottom_elevation``, and a ``Post`` starts at whatever its support's top is. Move the
    bell without growing the shaft and both columns drop 2'-6" off their beams; grow the
    ``Footing.depth`` instead of moving it and the model bills a 30"x30"x42" prism of
    concrete for a 12" auger hole. So this asserts both ends: the bells bear at frost
    depth, AND the two soffits they carry did not move by so much as a hair.
    """
    from typehaus.checks.code.mn_residential.profile import MN_2024

    frost_m = MN_2024.frost_depth_in * INCH
    floor_top = _solid(catlin_model, "SL-SG-FLOOR").z1_m

    for bell_tag, post_tag, beam_tag in (("FT-SG-COL", "PT-SG-COL", "BM-SG-BKW"),
                                         ("FT-SG-FCOL", "PT-SG-FCOL", "BM-SG-FRW")):
        bell = _solid(catlin_model, bell_tag)
        post = _solid(catlin_model, post_tag)
        beam = _solid(catlin_model, beam_tag)
        # The bell bears a full frost depth under the court floor its cover is measured
        # from — which is the whole point: ``structural.frost_depth`` grades these two on
        # COVER now, in its plain "at least 42 inches below their lowest adjacent grade"
        # bucket, not on the soil replacement the five wall footings still rely on.
        assert bell.z0_m == pytest.approx(floor_top - frost_m)
        assert bell.z1_m - bell.z0_m == pytest.approx(12 * INCH), "12\" bell, not 42\""
        # The shaft picks up exactly where the bell stops...
        assert post.z0_m == pytest.approx(bell.z1_m)
        # ...and still dies on its beam's soffit. Both porch beam pairs carry a joist drop,
        # so there is ONE soffit and the whole porch frame hangs off -1'-6 1/2". Nothing
        # here is free to slide.
        assert post.z1_m == pytest.approx(beam.z0_m)

    assert _solid(catlin_model, "PT-SG-COL").z1_m == pytest.approx(-18.5 * INCH)
    # ``_bearing_stack_drops`` propagates the joists' 7 1/4" through to this post, which is
    # what puts PT-SG-BF2 on concrete. The authored height must not be "corrected" to match.
    assert _solid(catlin_model, "PT-SG-FCOL").z1_m == pytest.approx(-18.5 * INCH)

    # A bell bearing on undisturbed soil at frost depth takes a levelling course, not a
    # 42" replacement section. 42" under the NEW underside would bottom the excavation
    # 1'-9" below the soakaway it is meant to stack on top of.
    beds = {b.host: b for b in catlin_model.footing_beddings}
    well_top = _solid(catlin_model, "DRW-SG-MAIN").z1_m
    for host in ("FT-SG-COL", "FT-SG-FCOL"):
        bed = beds[host]
        assert bed.z1_m - bed.z0_m == pytest.approx(7 * INCH)
        assert bed.z0_m > well_top, "the levelling course clears the drywell's stone"
        # The claim and the outlet both survive the section shrinking.
        assert bed.non_frost_susceptible is True
        assert bed.drain_tile_spec.discharge == "DRW-SG-MAIN"


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


# --- the heat-pump ground pad, east of the porch --------------------------------------
#
# Both condensers stood on FS-SG-DECK at +10' until 2026-09-02 and now stand on a poured pad
# in the yard pocket east of the porch (houses/catlin/notes/heat_pump_ground_pad.md). What
# used to hold this together was ``mep.deck_equipment_support_coverage``, which read the
# stand and the cabinets and reconciled a dimension written in two modules that cannot import
# each other. Nothing stands on a deck now, so that check grades an empty population here and
# these tests take over the coupling: the pad's top, the legs' bearing on it, the anchors'
# host, and the cabinets' own base all have to agree, and they are authored in two files.
_HP_PAD_TOP_FT = -2 - 8 / 12.0
_HP_STAND_IN = 18.0
_HP_UNITS = ("EQ-M-HP1-OD", "EQ-M-HP2-OD")


def test_the_heat_pump_pad_tops_out_two_inches_proud_of_grade(catlin_model) -> None:
    """``SL-SG-HPPAD`` is a 4" pour whose top is ABOVE the site plane, not level with it.

    -2'-8" against a -2'-10" grade. The two inches are Gree's own instruction ("install 2 in
    above the expected snow line") and they are the first two of the ~20" the 18" stands then
    make up. A pad authored without ``top_elevation`` would hang its thickness below the
    `main` datum instead — 0'-0" to -0'-4", nearly three feet in the air.
    """
    pad = _solid(catlin_model, "SL-SG-HPPAD")
    assert pad.category == "slab"
    assert pad.z1_m / FT == pytest.approx(_HP_PAD_TOP_FT)
    assert (pad.z1_m - pad.z0_m) / INCH == pytest.approx(4.0)
    site_grade = catlin_model.plan.project.site.grade.meters
    assert pad.z1_m > site_grade
    assert (pad.z1_m - site_grade) / INCH == pytest.approx(2.0)


def test_the_eight_stand_legs_stand_UP_from_the_pad_top(catlin_model) -> None:
    """``supported_by="SL-SG-HPPAD"`` is what makes a post rise from a support.

    ``_resolve_post`` (resolve/envelope.py) bears a post on any tag in ``solid_top``, which
    holds every resolved solid, so a Slab is a legal support. Without it the legs would hang
    their height BELOW the `main` datum — tops at 0'-0", bottoms at -1'-6", floating a foot
    above a pad they are supposed to be bolted to.
    """
    legs = [s for s in catlin_model.solids if s.tag.startswith("PT-SG-HP")]
    assert len(legs) == 8, [s.tag for s in legs]
    pad_top = _solid(catlin_model, "SL-SG-HPPAD").z1_m
    for leg in legs:
        assert leg.z0_m == pytest.approx(pad_top), leg.tag
        assert (leg.z1_m - leg.z0_m) / INCH == pytest.approx(_HP_STAND_IN), leg.tag
        assert leg.assembly == "EQUIP_STAND_ALUM", leg.tag


def test_every_stand_anchor_names_the_pad_and_sits_on_its_top(catlin_model) -> None:
    """One wedge anchor per leg, connecting that leg to the slab it is set into.

    The pair matters as much as the count: an anchor naming a leg but not the pad describes a
    fastener into nothing, and the plan (not the resolved model) is where that claim lives.
    """
    anchors = [e for s in catlin_model.plan.storeys
               for e in catlin_model.plan.storey_elements(s.tag)
               if getattr(e, "tag", "").startswith("CN-SG-HP")]
    assert len(anchors) == 8, [e.tag for e in anchors]
    legs = {s.tag for s in catlin_model.solids if s.tag.startswith("PT-SG-HP")}
    for anchor in anchors:
        assert anchor.kind.value == "equipment_anchor", anchor.tag
        assert anchor.size == "SS316-WEDGE-38x3", anchor.tag
        assert "SL-SG-HPPAD" in anchor.connects, anchor.tag
        assert legs & set(anchor.connects), anchor.tag
        assert anchor.elevation.meters / FT == pytest.approx(_HP_PAD_TOP_FT), anchor.tag


def test_both_condensers_sit_on_the_stands_rather_than_beside_them(catlin_model) -> None:
    """The cabinets' base and the legs' tops are one plane written in two files.

    ``mount.elevation`` is authored in plan/electrical.py and measures from the `main` datum;
    the pad top and the stand height are authored in params/sunken_garden.py. -2'-8" + 18"
    = -1'-2", and the units carry inch(-14). Nothing but this reconciles them — the two
    modules cannot import each other, and the check that used to do it sees no deck
    equipment any more.
    """
    storeys = {s.tag: s for s in catlin_model.plan.storeys}
    units = {e.tag: (s, e) for s in catlin_model.plan.storeys
             for e in catlin_model.plan.storey_elements(s.tag)
             if getattr(e, "tag", "") in _HP_UNITS}
    assert set(units) == set(_HP_UNITS), sorted(units)
    leg_top = max(s.z1_m for s in catlin_model.solids if s.tag.startswith("PT-SG-HP"))
    for tag, (storey, unit) in units.items():
        assert storey.tag == "main", (tag, storey.tag)
        base = resolved_mount_elevation(storeys[storey.tag], unit)
        assert base == pytest.approx(leg_top), tag
        assert base / FT == pytest.approx(-1 - 2 / 12.0), tag
        # Ground units drip onto their own pad: no pan, no piped condensate, no heat trace.
        assert not getattr(unit, "drain_pan", False), tag
        assert getattr(unit, "pan_drain_ref", None) is None, tag


def test_each_stand_leg_stands_under_a_published_foot_hole_and_on_the_pad(catlin_model
                                                                          ) -> None:
    """On a pad the legs ARE the feet, which is the whole simplification the move bought.

    On the balcony the legs answered to the deck (bay centres, six inches off a beam axis)
    and the feet to the cabinet, and the two could not coincide — decision #64. A flat slab
    has no grid, so each leg sits directly under a published foot hole: Gree's patterns are
    29 3/4" x 15 9/16" (FXU24, HP1) and 25" x 15 19/32" (MUL30, HP2), width x depth. Both
    cabinets sit SQUARE to the plan since 2026-09-03 (`rotation=deg(0)`, discharge facing
    south), so the width pitch runs in **x** and the depth pitch in **y** — the transpose of
    the arrangement that faced east, and the reason this test asserts the mapping rather
    than assuming it.

    And every leg's full 2" section must land ON the pad. HP1's depth pattern is an inch
    WIDER than its cabinet, so its leg lines sit outboard of the cabinet's own faces on that
    axis.
    """
    from shapely.geometry import Polygon

    pattern = {"EQ-M-HP1-OD": ("A", 29.75, 15.5625), "EQ-M-HP2-OD": ("B", 25.0, 15.59375)}
    units = {e.tag: e for s in catlin_model.plan.storeys
             for e in catlin_model.plan.storey_elements(s.tag)
             if getattr(e, "tag", "") in _HP_UNITS}
    pad = Polygon(_solid(catlin_model, "SL-SG-HPPAD").outline)
    legs = {s.tag: s for s in catlin_model.solids if s.tag.startswith("PT-SG-HP")}
    for tag, (key, width_in, depth_in) in pattern.items():
        cx, cy = units[tag].position.xy_m
        # Matched within a thousandth of an inch rather than by rounding both sides to six
        # decimal places and comparing sets: a leg centre that lands on a half-microm etre
        # boundary (HP1's south pair does, at -2.359375') flips that rounding and fails a
        # test about foot patterns for reasons that have nothing to do with foot patterns.
        want = [(cx + sx * width_in * INCH / 2.0, cy + sy * depth_in * INCH / 2.0)
                for sx in (-1, 1) for sy in (-1, 1)]
        got = []
        for index in range(1, 5):
            leg = legs[f"PT-SG-HP{key}{index}"]
            ring = Polygon(leg.outline)
            got.append((ring.centroid.x, ring.centroid.y))
            assert pad.contains(ring), f"PT-SG-HP{key}{index} overhangs the pad"
        tol = 0.001 * INCH
        for hole in want:
            assert any(abs(g[0] - hole[0]) < tol and abs(g[1] - hole[1]) < tol
                       for g in got), (tag, hole)
        assert len(got) == len(want)


# ---------------------------------------------------------------------------------------
# The 2026-09-03 turn, and the 2026-09-04 swap.
#
# Both cabinets face SOUTH (`rotation=deg(0)`), side by side in one east-west row. The row
# ran across the pocket's SOUTH half for a day, with ST-SG-PORCH in the north strip; on
# 2026-09-04 the two swapped halves, because the flight springs from W-SG-E1's top and that
# top is walkable only between its two 12" round columns — y -9'-9"..-3'-0", which is exactly
# where the row stood. Nothing reported it: the threshold board is trim rather than an
# element, and PT-SG-BR3's east face is EXACTLY tangent to the stair's head at x 28'-6", so
# no solid overlapped. notes/porch_stair.md and notes/heat_pump_ground_pad.md.
#
# The row's x is unchanged by the swap and asserted below at both ends — tucked as far west
# as 40 5/32" + 12" + 39" allows.
# ---------------------------------------------------------------------------------------
_PAD_X = (29.0, 36.833333)
_PAD_Y = (-3.333333, -0.833333)
_STAIR_PAD_X = (28.5, 35.25)
_STAIR_PAD_Y = (-9.0, -6.0)


def test_the_pad_carries_the_row_and_nothing_else(catlin_model) -> None:
    """19.6 sf / 0.24 cy, x 29'-0"..36'-10" by y -3'-4"..-0'-10".

    It was 56.9 sf / 0.70 cy for a day, when one pour had to reach both the cabinets and a
    flight in the same band. They are 2'-8" apart in y now, and a rectangle spanning both
    would be 94 sf of concrete to serve 40 — so the flight took its own pour (SL-SG-STAIRPAD)
    and this one shrank to the row. `prices.toml`'s qualified `slab:HP_PAD_ON_GRADE` row is
    keyed to the pair's 0.49 cy.

    The north edge stops 3" short of the cladding rather than butting it: no isolation joint
    to detail, and the wall's runoff lands in gravel instead of against a lip.
    """
    from shapely.geometry import Polygon

    pad = Polygon(_solid(catlin_model, "SL-SG-HPPAD").outline)
    x0, y0, x1, y1 = pad.bounds
    assert (x0 / FT, x1 / FT) == pytest.approx(_PAD_X)
    assert (y0 / FT, y1 / FT) == pytest.approx(_PAD_Y)
    area_sf = pad.area / (FT * FT)
    assert area_sf == pytest.approx(19.583, abs=0.05)
    assert area_sf * (4.0 / 12.0) / 27.0 == pytest.approx(0.242, abs=0.005)


def test_the_flight_has_its_own_pad_with_a_code_landing_on_it(catlin_model) -> None:
    """SL-SG-STAIRPAD, 20.3 sf / 0.25 cy, x 28'-6"..35'-3" by y -9'-0"..-6'-0".

    Its west edge is W-SG-E1's east face where the stringers foot; the flight covers x
    28'-6"..32'-2"; and what is left east of that is R311.7.6's bottom landing, which wants
    36" in the direction of travel. The two pads must not touch — a single pour spanning the
    2'-8" between them is 94 sf to serve 40 — and they must share a top, or the flight's
    authored base is not the surface it lands on.
    """
    from shapely.geometry import Polygon

    pad = Polygon(_solid(catlin_model, "SL-SG-STAIRPAD").outline)
    x0, y0, x1, y1 = pad.bounds
    assert (x0 / FT, x1 / FT) == pytest.approx(_STAIR_PAD_X)
    assert (y0 / FT, y1 / FT) == pytest.approx(_STAIR_PAD_Y)
    area_sf = pad.area / (FT * FT)
    assert area_sf == pytest.approx(20.25, abs=0.05)
    # 37" of landing east of the bottom riser, against R311.7.6's 36".
    assert (_STAIR_PAD_X[1] - (28.5 + 4 * 11.0 / 12.0)) * 12.0 >= 36.0
    # Separate pours, and the gap is the point.
    equipment = Polygon(_solid(catlin_model, "SL-SG-HPPAD").outline)
    assert not pad.intersects(equipment)
    assert equipment.distance(pad) / FT == pytest.approx(2.667, abs=0.01)
    slabs = {e.tag: e for st in catlin_model.plan.storeys
             for e in catlin_model.plan.storey_elements(st.tag)
             if getattr(e, "tag", "") in ("SL-SG-STAIRPAD", "SL-SG-HPPAD")}
    assert (slabs["SL-SG-STAIRPAD"].top_elevation.meters
            == slabs["SL-SG-HPPAD"].top_elevation.meters)


def test_both_condensers_face_south_square_to_the_plan(catlin_model) -> None:
    """`rotation=deg(0)` on both, and their extents are the row this house is laid out from.

    The rotation is not cosmetic: it is what turns the discharge out of the pocket's own
    reflecting faces into open yard, and what transposes the stand leg patterns in
    params/sunken_garden.py. The 12" service gap between them is the one clearance still at
    its published minimum, so it is asserted rather than described.
    """
    units = {e.tag: e for s in catlin_model.plan.storeys
             for e in catlin_model.plan.storey_elements(s.tag)
             if getattr(e, "tag", "") in _HP_UNITS}
    extents = {}
    for tag, unit in units.items():
        assert unit.rotation.degrees == pytest.approx(0.0), tag
        cx, cy = unit.position.xy_m
        w, d = (q.meters for q in unit.footprint)
        extents[tag] = (cx - w / 2.0, cx + w / 2.0, cy - d / 2.0, cy + d / 2.0)
    hp2, hp1 = extents["EQ-M-HP2-OD"], extents["EQ-M-HP1-OD"]
    # HP2 west, HP1 east, 12" of service gap between them.
    assert (hp1[0] - hp2[1]) / INCH == pytest.approx(12.0, abs=0.05)
    # HP2's west end holds 6" off W-SG-E1's east face at x 28'-6".
    assert (hp2[0] / FT - 28.5) * 12.0 == pytest.approx(6.0, abs=0.05)
    # HP1 stands 7 1/5" past the house's SE corner at x 36'-0", into open side yard.
    assert (hp1[1] / FT - 36.0) * 12.0 == pytest.approx(7.2, abs=0.05)


def test_the_porch_stair_climbs_five_risers_from_the_pad_to_the_plank(catlin_model) -> None:
    """ST-SG-PORCH: 5 risers, 4 treads, 36" wide, -2'-8" to +0'-1".

    Both elevations are authored because neither is a storey datum — this is a step-down
    within `main`. The top is the porch's WALKING surface (the composite plank), not the 0'-0"
    joist top, which is the inch that makes the wall top a threshold rather than a tread.
    """
    stair = next(s for s in catlin_model.stairs if s.tag == "ST-SG-PORCH")
    assert stair.riser_count == 5
    assert stair.riser_height_m / INCH == pytest.approx(6.6)
    assert stair.going_depth_m / INCH == pytest.approx(11.0)
    assert stair.base_elevation_m / FT == pytest.approx(_HP_PAD_TOP_FT)
    treads = [m for m in stair.members if m.category == "tread"]
    assert len(treads) == 4
    for tread in treads:
        assert tread.length_m / FT == pytest.approx(3.0)
    stringers = [m for m in stair.members if m.category == "stringer"]
    assert len(stringers) == 2
    # It lands on its own pad, not beside it — and not on the condensers', which since
    # 2026-09-04 is a separate pour 2'-8" north.
    from shapely.geometry import Polygon

    pad = Polygon(_solid(catlin_model, "SL-SG-STAIRPAD").outline)
    assert pad.contains(Polygon(stair.outline).buffer(-0.01))
    assert not Polygon(_solid(catlin_model, "SL-SG-HPPAD").outline).intersects(
        Polygon(stair.outline))


def test_the_flight_is_guarded_both_sides_and_the_porch_guard_opened_for_it(catlin_model
                                                                            ) -> None:
    """Two raked guard-handrails on the flight, two level cheeks on the threshold, and
    RL-SG-PORCH's east leg opened 3'-0" in its MIDDLE with RL-SG-PORCH-NE carrying the stub.

    Nothing in the engine asks for the threshold pair — R312.1.1 measures the FLIGHT, whose
    top tread is only 26.4" over the pad, and `code.R312_1_guard_height` cannot see a guard
    opening in a deck edge at all, at the end or in the middle (plans/TODO.md). They are the
    author's guard return, so they are asserted here or they are nothing.
    """
    rails = {e.tag: e for s in catlin_model.plan.storeys
             for e in catlin_model.plan.storey_elements(s.tag)
             if getattr(e, "element_kind", "") == "Railing"}
    for tag in ("RL-SG-PSTAIR-S", "RL-SG-PSTAIR-N"):
        rail = rails[tag]
        assert rail.serves_stair == "ST-SG-PORCH", tag
        assert rail.role == "guard_and_handrail", tag
        assert rail.height.inches == pytest.approx(36.0), tag
        assert rail.top_height is not None and rail.top_height.inches == pytest.approx(36.0)
        assert rail.graspable_profile is not None, tag
    for tag in ("RL-SG-PTHRESH-S", "RL-SG-PTHRESH-N"):
        rail = rails[tag]
        assert rail.serves_stair is None, tag  # level on the wall top, never raked
        assert [round(p.xy_m[0] / FT, 4) for p in rail.path] == [27.5, 28.5], tag
    # ** THE OPENING IS IN THE MIDDLE OF THE EAST LEG, SO IT TAKES TWO ELEMENTS. ** A `path`
    # cannot carry a hole. RL-SG-PORCH runs up the east edge and stops at the flight's south
    # side; RL-SG-PORCH-NE picks up at its north side and runs to the porch's north edge.
    porch = rails["RL-SG-PORCH"]
    assert porch.path[-1].xy_m[1] / FT == pytest.approx(-9.0, abs=1e-3)
    assert porch.path[-1].xy_m[0] / FT == pytest.approx(27.5)
    stub = rails["RL-SG-PORCH-NE"]
    assert [round(p.xy_m[0] / FT, 4) for p in stub.path] == [27.5, 27.5]
    assert stub.path[0].xy_m[1] / FT == pytest.approx(-6.0, abs=1e-3)
    # Same product, same mount, same height — it is one run of guard with a doorway in it.
    assert stub.type_ref == porch.type_ref and stub.mount == porch.mount
    assert stub.height.inches == pytest.approx(porch.height.inches)
    # The doorway is exactly the flight's 36", and the two pieces do not overlap it.
    assert (stub.path[0].xy_m[1] - porch.path[-1].xy_m[1]) / FT == pytest.approx(3.0,
                                                                                abs=1e-3)
