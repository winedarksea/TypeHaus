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
    # One wall top, not two — and since 2026-09-10 that is literally true of all FIVE court
    # walls, not just of the two a pillar lands on. The retaining run used to stand +0'-6"
    # and then +0'-2"; it is on the porch datum now, `SPEC.retaining_top_ft` being
    # `porch_top_ft` rather than a figure derived off grade. One form height, one
    # strip-and-set, one continuous top line, and no 2-inch jog at the porch corner.
    #
    # **There is no step left to assert, so this asserts its absence.** A reader who finds
    # this failing with a non-zero value has reintroduced a jog in the top line, which is
    # the thing the flush tops were bought to remove.
    tops = {round(_wall(catlin_model, w).z1_m, 9) for w in PILLAR_BEARING_WALL.values()}
    assert tops == {0.0}
    court = {round(_wall(catlin_model, w).z1_m, 9)
             for w in ("W-SG-W2", "W-SG-E2", "W-SG-S", *PILLAR_BEARING_WALL.values())}
    assert court == {0.0}, court


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


def test_only_the_two_wood_pillars_take_a_base_and_it_is_a_tension_tie(catlin_model) -> None:
    """Six ABU66SS until 2026-09-03, then two, and now a five-part strap-and-angle tie.

    A 12" cast column standing on a 12" cast wall is joined by a lapped doweled splice made
    in the pour. Authoring a standoff base there would bill four stainless bases that do not
    exist AND claim a pinned joint, which is the opposite of the fixed one the whole
    braceless design turns on. That is why there are two and not six.

    ** WHY THE REMAINING TWO ARE NOT ABUs. ** Every published value an ABU has is measured
    with the stirrup bearing on CONCRETE through a 5/8" cast-in anchor, and ESR-1622 §5.6
    puts even that anchor outside its own scope. Both these pillars bear on the porch
    FRAMING, where there is no pour, no cast-in bolt and no basis for the table — and the
    R317.1.4 standoff the 1" gap was cited to governs wood on CONCRETE, which this is not.
    ** AND WHY THEY ARE NOT DTT2Zs EITHER. ** A DTT2 is a joint Simpson do publish for a
    post on framing, and it stood here for part of 2026-09-03. It is one-sided: eccentric on
    a 6x6, needing a 1/2" rod through the joist pack, and worth nothing laterally at a base
    that is pinned by design. The deeper objection was that ESR-2330 §3.2.2 wants SG >= 0.50
    and the house framed in SPF at 0.42 — and ESR-2604 §3.2.2 says the same of every cap and
    base in it, so NOTHING at this joint had a published number, the CCQ46SDS2.5 cap on top
    of these same posts included. The pillars are specified DF-L for that reason alone
    (POST_WHITE_PAINT_DF), and the clause is family-wide — ESR-2105 §3.5.2 and ESR-3096
    §3.2.2 word it identically — so that reason survives every part change at this joint.
    ** AND WHY THE BASE IS FIVE PARTS AND NOT AN INVERTED CCQ. ** A CCQ4.62-5.50SDS
    inverted stood here for the rest of that day and CANNOT BE BUILT at either pillar: at
    PT-SG-BF2 the rim, joist tips, beam axis and post centre are one line, and at PT-SG-BR2
    the squash blocks occupy the bays its side plates would hang in. What replaces it is
    mixed by what each face has beside it — an MSTA12Z strap on the one flush vertical pair
    (both west faces at x = 213.25"), plus an L50Z angle wherever there is joist pack to
    screw into: north at both pillars, south at BR2 alone. Five elements for two pillars,
    and no angle on the E/W faces, where 1-1/2" of block would make it fiction.

    The kind moves with the part, and it has to: ``ConnectorKind.TENSION_TIE`` is what
    ``takeoff/uplift_joints.py`` and ``checks/structural/uplift_path.py`` read to know this
    joint is made. Leaving it POST_BASE would have kept two rows of the wrong part number in
    the BOM; dropping it without adding the new kind to those two rules would have derived
    two phantom ABU66 and reported both pillars UNKNOWN.
    """
    from typehaus.model.enums import ConnectorKind
    from typehaus.quantities import inch

    bases = [el for el in catlin_model.plan.all_elements()
             if el.element_kind == "Connector" and el.tag.startswith("CN-SG-BASE-")]
    assert len(bases) == 5
    assert {b.size for b in bases} == {"MSTA12Z", "L50Z"}
    assert {b.kind for b in bases} == {ConnectorKind.TENSION_TIE}
    by_tag = {b.tag: b for b in bases}
    # One strap per pillar on the west face; angles only where there is pack beside it.
    assert {t for t, b in by_tag.items() if b.size == "MSTA12Z"} == {
        "CN-SG-BASE-R2-W", "CN-SG-BASE-F2-W"}
    assert {t for t, b in by_tag.items() if b.size == "L50Z"} == {
        "CN-SG-BASE-R2-N", "CN-SG-BASE-R2-S", "CN-SG-BASE-F2-N"}
    # BF2's joist field ENDS on the front beam, so there is nothing south of it to angle to.
    assert "CN-SG-BASE-F2-S" not in by_tag
    for base in bases:
        pillar = _solid(catlin_model, base.connects[0])
        assert abs(base.elevation.meters - pillar.z0_m) < 1e-9, base.tag
        # Each marker sits on the face it fastens, so five parts do not co-locate.
        centre = [(min(c[i] for c in pillar.outline) + max(c[i] for c in pillar.outline)) / 2.0
                  for i in (0, 1)]
        offset = max(abs(base.position.xy_m[i] - centre[i]) for i in (0, 1))
        assert offset == pytest.approx(inch(2.75).meters, abs=1e-6), base.tag
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

    Both stand over a BEARING rather than over a joist tip — BR2 3" south of the back-beam
    line, BF2 on the front-beam axis — so neither is on a cantilever and
    ``structural.cantilever_point_load`` is silent about them honestly.

    ** WHAT THEY BEAR THROUGH IS THREE PLIES, NOT ONE. ** Each is a 6x6 crossing the grain
    of a 2x8, and ``engineering/post_bearing.py`` computes what that costs: through ONE ply,
    BM-SG-BLC's real reactions bear at 311 and 380 psi against a WET Fc-perp of 285 — not
    the dry 425 this docstring used to quote at the same joint whose glulam has been graded
    wet all along. Two sisters take it to 107 and 131 psi. The blocks are still here and
    still answer rollover; what changed is that bearing is now answered too, by a member
    rather than by a hope.

    ** BF2 IS ON THE AXIS AND THAT COSTS IT HALF ITS BASE. ** The porch outline ends on the
    front beam axis, so half its 5-1/2" footprint is over the deck edge with no joist under
    it — which is why ``_post_on_field_in`` clips the bearing length to the joist field
    instead of crediting the whole section, and why that state comes back at d/c 0.62 rather
    than 0.29. The move is what puts the pillar over the beam its joists END on (2-1/4" of
    bearing, the porch's tightest plane) and what makes it the RL-SG-PORCH guard post at
    x = 18'-0".
    """
    floor = _floor(catlin_model, "FS-SG-PORCH")
    # Two sisters, from ONE shared cluster: both pillars are on the same joist line and both
    # ask for plies=3, and ``_reinforcement_members`` tops the line up rather than laying a
    # second coincident pair. See test_joist_reinforcement.py, which owns both counts.
    assert len([m for m in floor.members if m.category == "sister_joist"]) == 2
    blocks = [m for m in floor.members if m.category == "blocking"]
    assert len(blocks) == 8, len(blocks)

    porch_deck_top = _porch_deck_top(catlin_model)
    for tag in DECK_BORNE_PILLAR_TAGS:
        assert _solid(catlin_model, tag).z0_m == pytest.approx(porch_deck_top), tag
    joist_tip = max(max(m.p0[1], m.p1[1]) for m in floor.members if m.category == "joist")
    back_beam_y = max(p[1] for p in _solid(catlin_model, "BM-SG-BKW").outline)
    br2_y = catlin_model.plan.by_tag("PT-SG-BR2").position.xy_m[1]
    assert br2_y < back_beam_y < joist_tip

    # BR2 is 3" south of the back-beam line; BF2 is ON the front one, over PT-SG-FCOL.
    column_y = catlin_model.plan.by_tag("PT-SG-COL").position.xy_m[1]
    assert (column_y - br2_y) == pytest.approx(3 * INCH, abs=1e-9)
    fcol_y = catlin_model.plan.by_tag("PT-SG-FCOL").position.xy_m[1]
    bf2_y = catlin_model.plan.by_tag("PT-SG-BF2").position.xy_m[1]
    assert bf2_y == pytest.approx(fcol_y, abs=1e-9)


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
    # -33.3333 until the court shortened 28'-0" -> 26'-0" on 2026-09-10. The apron follows
    # the wall it measures off: 3'-0" clear of FT-SG-S's outboard edge, which is itself
    # W-SG-S's axis less half the 7'-0" strip. Both moved 2'-0" north together.
    assert {round(y / FT, 4) for _, y in south.axis} == {-31.3333}
    # The legs run north from those corners to the arch wall's own axis plane, at -10.5: the
    # apron closes against RL-SG-BALCONY (``BALCONY_FRONT_AXIS_Y_FT``), not -9.5.
    for leg in (west, east):
        assert {round(y / FT, 4) for _, y in leg.axis} == {-10.5, -31.3333}
    assert {round(x / FT, 4) for _, x in ((0, west.axis[0][0]), (0, west.axis[1][0]))} == {4.0}
    assert {round(x / FT, 4) for _, x in ((0, east.axis[0][0]), (0, east.axis[1][0]))} == {32.0}


def test_the_raised_garden_returns_close_on_the_court_walls(catlin_model) -> None:
    """The returns retain the terrace corner to corner, and the leader stands over one.

    Each return ends on the OUTER face of the court wall it meets — x 7'-6" and 28'-6", the
    sunken-garden axes less and plus half of a 12" wall — so there is no notch between block
    and concrete for the terrace fill to escape through. They were 2'-9" and stopped 6"
    short of the balcony deck edge until 2026-09-12, holding a slot open for
    ``TR-SG-LEADER-SE``; the hole that left in a retaining wall outranked the pipe's
    clearance. What the change costs is asserted below and it is a drawing detail, not a
    collision: the block runs under the leader with its crest 6" below the outlet, so the
    outlet needs a shoe carrying the discharge south past the cap.
    """
    returns = {tag: _wall(catlin_model, tag) for tag in _APRON_TAGS[3:]}
    for tag, wall in returns.items():
        length = ((wall.axis[1][0] - wall.axis[0][0]) ** 2
                  + (wall.axis[1][1] - wall.axis[0][1]) ** 2) ** 0.5
        assert length == pytest.approx(3.5 * FT, abs=1e-9), tag
        assert {round(y / FT, 4) for _, y in wall.axis} == {-10.5}, tag
    west = returns["W-RG-WEST-BALCONY"]
    east = returns["W-RG-EAST-BALCONY"]
    assert {round(x / FT, 4) for x, _ in west.axis} == {4.0, 7.5}
    assert {round(x / FT, 4) for x, _ in east.axis} == {28.5, 32.0}
    # Read off the court walls rather than typed: their outer faces ARE the return ends.
    for return_wall, court_tag, sign in ((west, "W-SG-W1", -1), (east, "W-SG-E1", 1)):
        court = _wall(catlin_model, court_tag)
        face = court.axis[0][0] + sign * court.thickness_m / 2.0
        ends = [x for x, _ in return_wall.axis]
        assert min(abs(x - face) for x in ends) == pytest.approx(0.0, abs=1e-9), court_tag

    # And the cost: the leader now hangs over the east return, 6" above its crest.
    leader = next(s for s in catlin_model.solids if s.tag == "TR-SG-LEADER-SE")
    pipe_x = [point[0] for point in leader.outline]
    assert min(x for x, _ in east.axis) <= min(pipe_x)
    assert max(pipe_x) <= max(x for x, _ in east.axis)
    assert east.z1_m < leader.z0_m, "the solids never touch, so no check reports this"


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


def test_the_apron_tops_out_level_with_the_wall_it_wraps_and_buries_its_base_course(
        catlin_model) -> None:
    """The drop is 4'-0" since 2026-09-10, and the last 8" of it is embedment.

    It was 3'-0" while the apron top stood at +0'-6" and the yard was an assumed flat plane
    at the -2'-10" datum, which left the base course **4" clear of the ground** — a
    dry-stacked segmental run retaining three feet of fill with nothing holding its toe,
    at 0 FAIL, for two revisions. Both ends have since moved: the top came down to the
    porch datum with the four court walls, and `plan/site.py` now authors the south yard as
    three stations at -3'-4" rather than leaving it to the global plane. A 3'-0" drop off
    the new top would have reproduced the same negative embedment from the other side.

    The embedment assertion is the one that matters and is new. Nothing in the engine
    grades a freestanding wall's base against the ground, so this is the only thing
    watching it; the level-top and whole-course assertions were always here.
    """
    retaining = _wall(catlin_model, "W-SG-S")
    yard_m = min(spot.elevation.meters
                 for spot in catlin_model.plan.project.site.spot_elevations
                 if spot.kind == "grade")
    for tag in _APRON_TAGS:
        leg = _wall(catlin_model, tag)
        assert abs(leg.z1_m - retaining.z1_m) < 1e-9, f"{tag} must cap level with W-SG-S"
        assert abs((leg.z1_m - leg.z0_m) - 4 * FT) < 1e-9, tag
        # Whole courses: a dry-stacked wall cannot end mid-unit.
        assert abs((leg.z1_m - leg.z0_m) % (6 * INCH)) < 1e-9, tag
        # The base course is BURIED, and by at least the ~6" an SRW this tall wants. 3'-10"
        # would give exactly 6" and is not buildable in whole 6" courses.
        embedment_in = (yard_m - leg.z0_m) / INCH
        assert embedment_in == pytest.approx(8.0, abs=0.01), (tag, embedment_in)


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
    the house cladding and its bell footing stops short of the house's own footing.

    How far short is not a free number: FT-B-S2's south face already lands on the deck's
    north-edge line, and the bell's north face sits back 2" from it. Everything here is
    read off the model — the offset itself included — so the assertion tracks
    ``SPEC.column_south_offset_in`` instead of restating it.

    The bell is augered to frost depth, so the two footings do not meet at one elevation and
    there is no joint to dowel or bridge to break. **The clearance grew twice on 2026-09-05
    and the bell did not move for either.** It was 17" of column offset less the bell's own
    15" reach, i.e. 2"; then FT-B-S2/S3 gave up 2" of south toe so W-SG-BRKBM's isolation
    board could sit at -8"..-10", making it 4"; then all four south strips went to a 6" trim
    so the sunken garden's closure board could have its full 2" across an 84" joint, making
    it 8".

    ** THEN THE BELL MOVED, FOR THE FIRST TIME, AND IT SPENT 3" OF THAT. ** On 2026-09-10
    both pier bells were standardised at 36" — the 36" was a fossil from a 20" column and
    this one's 30" was set by nothing — so the reach went 15" to 18" and the clearance
    8" -> **5"**. That is the one direction this number had never gone, and it is why the
    docstring above says "if this ever tightens, something has moved the bell": something
    did, deliberately, and the trade was a width, an under-reamer setting and a schedule row
    against 3" of a gap that has 5" left in it.

    **5" in plan is not the constraint to watch; the 22" of section between them is.** The
    bell's TOP is at -11'-7 7/16" and the house strip bottoms at -9'-9 7/16" (the bell
    bears another 12" down, at -12'-7 7/16"). A 1:1 influence line down and out from the
    strip's south bottom edge reaches y = -2'-2" at the bell's top and the bell's north
    face is inside it — as it was at 30" too. These two never touch,
    and the real constraint is SEQUENCING: auger both shafts with the open basement
    excavation. `AN-SG-PLACEMENTS` says so on the drawing.
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
    assert house_footing_s - bell_north == pytest.approx(5 * INCH)
    # And they never meet in section, which is why 5" of plan gap is comfortable.
    assert (_solid(catlin_model, "FT-B-S2").z0_m - bell.z1_m) == pytest.approx(22 * INCH)
    assert catlin_model.plan.by_tag("DW-SG-COL") is None
    assert {d.tag for d in catlin_model.plan.all_elements()
            if d.element_kind == "Dowel"} == {"DW-SG-W1", "DW-SG-E1",
                                              "DW-SG-W1-STEM", "DW-SG-E1-STEM"}
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
    from typehaus.checks.code.mn_residential.profile import MN_2020

    frost_m = MN_2020.frost_depth_in * INCH
    floor_top = _solid(catlin_model, "SL-SG-FLOOR").z1_m

    for bell_tag, post_tag, beam_tag in (("FT-SG-COL", "PT-SG-COL", "BM-SG-BKW"),
                                         ("FT-SG-FCOL", "PT-SG-FCOL", "BM-SG-FRW")):
        bell = _solid(catlin_model, bell_tag)
        post = _solid(catlin_model, post_tag)
        beam = _solid(catlin_model, beam_tag)
        # The bell bears AT LEAST a full frost depth under the court floor its cover is
        # measured from — which is the whole point: ``structural.frost_depth`` grades these
        # two on COVER, in its plain "at least 42 inches below their lowest adjacent grade"
        # bucket, not on the soil replacement the five wall footings still rely on.
        #
        # ** EXACTLY 42", AND IT WENT THE LONG WAY ROUND. ** `_pier_bell_bottom_ft` derives
        # off `_court_top_in`, so the bells track the court. When the court came back up
        # 7 1/4" that expression was PINNED for a day instead of followed, on the argument
        # that 49 1/4" of cover is more conservative and that re-opening every hand-worked
        # term in notes/sunken_garden_piers.md was not worth 0.1 cy of shaft. Owner's call
        # reverses it: the rule is the rule, and a pinned literal is what silently drifts the
        # next time the court moves. Both bounds are asserted — the inequality says which
        # direction is the failure, the equality says the constant is derived and not held.
        assert bell.z0_m <= floor_top - frost_m + 1e-9, bell_tag
        assert (floor_top - bell.z0_m) / INCH == pytest.approx(42.0, abs=0.05), bell_tag
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

    South: 2-3/4" past the front beam's axis — enough to CROSS the 4-1/2" beam rather than
    die on its centreline, which is what a joist should do and what takes both bearing
    planes at PT-SG-BF2 out of NDS §3.10.4's END case (d/c 0.76 -> 0.35). It was 0" until
    2026-09-03. North: the joists run the column's south-offset past the back-beam line,
    all the way to the deck's north edge, which is the overhang the porch actually has.

    **The sheet follows the framing and the guard does not.** ``resolve/floors.py`` takes
    the subfloor's along-span extent from the joist ends, so the composite plank grew south
    with them and now ends 2-3/4" outboard of RL-SG-PORCH's guard line. That is a deliberate
    setback, not a landing: the guard blocking sits in the bay NORTH of the beam, and a
    guard chased out to the new edge would bolt into cantilevered joist tips.
    """
    from typehaus.quantities import inch

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
    # 2-3/4" PAST the front beam axis: the beam is 4-1/2" wide, so its far face is 2-1/4"
    # south of the axis and the joists clear it by 1/2". Comfortably inside the 8"
    # ``bearing_plan_tolerance_in`` past which the uplift check finds neither a derived tie
    # nor a hanger and FAILs every joist in the deck.
    oversail_in = (front_axis_y - min(heels)) / inch(1).meters
    assert oversail_in == pytest.approx(2.75)
    assert oversail_in < 8.0
    # The authored ``outline`` scopes the x extent only; the SHEET's south edge is derived
    # from the joist ends, so it moved with them while the outline tuple did not.
    assert south == pytest.approx(front_axis_y)
    sheet = [p[1] for p in _floor(catlin_model, "FS-SG-PORCH").deck_outline]
    assert min(sheet) == pytest.approx(min(heels))
    # Which is the whole R312 consequence, taken deliberately: the guard stays on the beam
    # axis and 2-3/4" of walking surface is now outboard of it.
    guard_y = min(p.xy_m[1] for p in catlin_model.plan.by_tag("RL-SG-PORCH").path)
    assert (guard_y - min(sheet)) / inch(1).meters == pytest.approx(2.75)
    # The balcony keeps its own symmetric 9" — the per-end split must not have leaked.
    # 9", not 6", since 2026-09-03: the deck edge used to land exactly on the outer face of
    # the 12" rounds, so the plank shed its water down the columns. The step is 3" because
    # the AridDek main board is 6" and a deck width not divisible by 6 costs a ripped board.
    balcony = catlin_model.plan.by_tag("FS-SG-DECK").joists
    assert balcony.cantilever.inches == pytest.approx(9.0)
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
#: ** ONE UNIT IN THE POCKET SINCE 2026-09-04. ** EQ-M-HP1-OD crossed to the north face
#: with its air handler (params/hp1_north_pad.py); its own pad, stand and anchors are
#: asserted in their own section at the foot of this file. What is left here is HP2 alone.
_HP_UNITS = ("EQ-M-HP2-OD",)


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


def test_the_four_stand_legs_stand_UP_from_the_pad_top(catlin_model) -> None:
    """``supported_by="SL-SG-HPPAD"`` is what makes a post rise from a support.

    ``_resolve_post`` (resolve/envelope.py) bears a post on any tag in ``solid_top``, which
    holds every resolved solid, so a Slab is a legal support. Without it the legs would hang
    their height BELOW the `main` datum — tops at 0'-0", bottoms at -1'-6", floating a foot
    above a pad they are supposed to be bolted to.
    """
    legs = [s for s in catlin_model.solids if s.tag.startswith("PT-SG-HP")]
    assert len(legs) == 4, [s.tag for s in legs]
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
    assert len(anchors) == 4, [e.tag for e in anchors]
    legs = {s.tag for s in catlin_model.solids if s.tag.startswith("PT-SG-HP")}
    for anchor in anchors:
        assert anchor.kind.value == "equipment_anchor", anchor.tag
        assert anchor.size == "SS316-WEDGE-38x3", anchor.tag
        assert "SL-SG-HPPAD" in anchor.connects, anchor.tag
        assert legs & set(anchor.connects), anchor.tag
        assert anchor.elevation.meters / FT == pytest.approx(_HP_PAD_TOP_FT), anchor.tag


def test_the_pocket_condenser_sits_on_its_stand_rather_than_beside_it(catlin_model) -> None:
    """The cabinet's base and the legs' tops are one plane written in two files.

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
    25" x 15 19/32" for the MUL30, width x depth. The cabinet sits SQUARE to the plan since
    2026-09-03 (`rotation=deg(0)`, discharge facing south), so the width pitch runs in **x**
    and the depth pitch in **y** — the transpose of the arrangement that faced east, and the
    reason this test asserts the mapping rather than assuming it. (HP1's 29 3/4 x 15 9/16
    pattern left with it on 2026-09-04; it is asserted on its own pad below.)

    And every leg's full 2" section must land ON the pad.
    """
    from shapely.geometry import Polygon

    pattern = {"EQ-M-HP2-OD": ("B", 25.0, 15.59375)}
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
_PAD_X = (29.0, 32.583333)
_PAD_Y = (-3.333333, -0.833333)
_STAIR_PAD_X = (28.5, 35.25)
_STAIR_PAD_Y = (-9.0, -6.0)


def test_the_pad_carries_the_row_and_nothing_else(catlin_model) -> None:
    """8.96 sf / 0.11 cy, x 29'-0"..32'-7" by y -3'-4"..-0'-10".

    ** IT SHRANK ON 2026-09-04. ** It was 19.6 sf carrying a two-cabinet row that oversailed
    the pocket's SE corner by 7 1/6"; EQ-M-HP1-OD then crossed to the north face with its air
    handler and the east edge came back to 2 3/4" past HP2's cabinet — the same rule that set
    the old one. There is no oversail left: HP2 alone stops 3'-7 27/32" short of x 36'-0".

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
    assert area_sf == pytest.approx(8.958, abs=0.05)
    assert area_sf * (4.0 / 12.0) / 27.0 == pytest.approx(0.1106, abs=0.005)


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


def test_the_pocket_condenser_faces_south_square_to_the_plan(catlin_model) -> None:
    """`rotation=deg(0)`, and its extent is the row this pocket is laid out from.

    The rotation is not cosmetic: it is what turns the discharge out of the pocket's own
    reflecting faces into open yard, and what transposes the stand leg pattern in
    params/sunken_garden.py.

    ** THE 12" SERVICE GAP AND THE 7 1/5" OVERSAIL ARE GONE WITH HP1 (2026-09-04). ** They
    were the two tightest facts about this row and both were assertions about a cabinet that
    no longer stands here. What is asserted now is the west end, which did not move, and the
    fact that this unit ends WELL short of the house's SE corner — the thing the move bought.
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
    hp2 = extents["EQ-M-HP2-OD"]
    # HP2's west end holds 6" off W-SG-E1's east face at x 28'-6".
    assert (hp2[0] / FT - 28.5) * 12.0 == pytest.approx(6.0, abs=0.05)
    # And its east end stops 3'-7 27/32" short of the house's SE corner at x 36'-0".
    assert (36.0 - hp2[1] / FT) * 12.0 == pytest.approx(43.84, abs=0.05)


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


# ---------------------------------------------------------------------------------------
# EQ-M-HP3-OD's pad and stand, north side (params/hp3_pad.py, added 2026-09-04)
# ---------------------------------------------------------------------------------------
# System 3's condenser has stood at grade since it was authored, and had nothing to stand
# ON: no pad, no stand, and no ``mount.elevation``, so a FLOOR mount put its base on the
# `main` datum — 2'-10" over bare soil. Nothing reported it, and that is the point of these
# tests: ``mep.deck_equipment_support_coverage`` sees no deck equipment in this house any
# more, and no check asks what a FLOOR-mounted exterior machine bears on. The coupling is
# the same one SL-SG-HPPAD has, written across two modules that cannot import each other.
_HP3_PAD = "SL-M-HP3PAD"
_HP3_CAB_W_IN, _HP3_CAB_D_IN = 34.375, 14.796875
_HP3_CLADDING_Y_IN = 36 * 12 + 7.25   # params/roof_trim.py::_WALL_OUTBOARD_IN off y=36'
_HP3_GARAGE_CLADDING_Y_IN = 40 * 12 + 7.75  # params/north_entry_frame.py::GARAGE_CLADDING_Y_FT


def test_hp3_stands_on_a_pad_at_the_same_top_and_height_as_the_pocket_pair(catlin_model
                                                                          ) -> None:
    """One pad top and one stand height across all three outdoor units.

    -2'-8" + 18" = -1'-2", and every cabinet carries ``inch(-14)``. A third pad poured to
    some other top would be invisible in the model and obvious on site.
    """
    pad = _solid(catlin_model, _HP3_PAD)
    assert pad.category == "slab"
    assert pad.z1_m / FT == pytest.approx(_HP_PAD_TOP_FT)
    assert (pad.z1_m - pad.z0_m) / INCH == pytest.approx(4.0)
    site_grade = catlin_model.plan.project.site.grade.meters
    assert (pad.z1_m - site_grade) / INCH == pytest.approx(2.0)

    legs = [s for s in catlin_model.solids if s.tag.startswith("PT-M-HP3-L")]
    assert len(legs) == 4, [s.tag for s in legs]
    for leg in legs:
        assert leg.z0_m == pytest.approx(pad.z1_m), leg.tag
        assert (leg.z1_m - leg.z0_m) / INCH == pytest.approx(_HP_STAND_IN), leg.tag
        assert leg.assembly == "EQUIP_STAND_ALUM", leg.tag

    storeys = {s.tag: s for s in catlin_model.plan.storeys}
    unit = next(e for s in catlin_model.plan.storeys
                for e in catlin_model.plan.storey_elements(s.tag)
                if getattr(e, "tag", "") == "EQ-M-HP3-OD")
    base = resolved_mount_elevation(storeys["main"], unit)
    assert base == pytest.approx(max(leg.z1_m for leg in legs))
    assert base / FT == pytest.approx(-1 - 2 / 12.0)
    # Grade units drip onto their own pad, like the pocket pair.
    assert not getattr(unit, "drain_pan", False)
    assert getattr(unit, "pan_drain_ref", None) is None


def test_hp3s_four_anchors_name_their_leg_and_the_pad(catlin_model) -> None:
    """Same part and the same pairing as the eight in the pocket: an anchor naming a leg
    but not the slab it is set into describes a fastener into nothing."""
    anchors = [e for s in catlin_model.plan.storeys
               for e in catlin_model.plan.storey_elements(s.tag)
               if getattr(e, "tag", "").startswith("CN-M-HP3-A")]
    assert len(anchors) == 4, [e.tag for e in anchors]
    legs = {s.tag for s in catlin_model.solids if s.tag.startswith("PT-M-HP3-L")}
    for anchor in anchors:
        assert anchor.kind.value == "equipment_anchor", anchor.tag
        assert anchor.size == "SS316-WEDGE-38x3", anchor.tag
        assert _HP3_PAD in anchor.connects, anchor.tag
        assert legs & set(anchor.connects), anchor.tag
        assert anchor.elevation.meters / FT == pytest.approx(_HP_PAD_TOP_FT), anchor.tag


def test_hp3s_stand_is_a_rail_pair_that_lands_wholly_on_its_pad(catlin_model) -> None:
    """The one departure from SL-SG-HPPAD, and it is deliberate.

    The pocket stands put a leg under each PUBLISHED foot hole, because Gree gives a foot
    pattern for the FXU24 and the MUL30. No mounting-hole drawing for the SAP09 chassis
    could be sourced, so this stand is specified the way it is bought: two 17 1/2" rails
    running the DEPTH way at 26" centres, the cabinet's own feet bolting to them wherever
    its pitch puts them. 17 1/2" is set against the two patterns that ARE published — both
    ~15 9/16" across the depth, an inch wider than the FXU24's own casing — so a rail sized
    to this cabinet's 14 51/64" could have missed its feet outboard on both sides.

    What is asserted here is the geometry that has to hold whatever the pitch is: four legs
    on one symmetric rectangle centred on the cabinet, longer across the depth than the
    cabinet is deep, and every leg's full 2" section ON the pad.
    """
    from shapely.geometry import Polygon

    unit = next(e for s in catlin_model.plan.storeys
                for e in catlin_model.plan.storey_elements(s.tag)
                if getattr(e, "tag", "") == "EQ-M-HP3-OD")
    cx, cy = unit.position.xy_m
    pad = Polygon(_solid(catlin_model, _HP3_PAD).outline)
    legs = {s.tag: Polygon(s.outline) for s in catlin_model.solids
            if s.tag.startswith("PT-M-HP3-L")}
    want = {(cx + sx * 26.0 * INCH / 2.0, cy + sy * 17.5 * INCH / 2.0)
            for sx in (-1, 1) for sy in (-1, 1)}
    tol = 0.001 * INCH
    for tag, ring in legs.items():
        assert pad.contains(ring), f"{tag} overhangs the pad"
        got = (ring.centroid.x, ring.centroid.y)
        assert any(abs(got[0] - w[0]) < tol and abs(got[1] - w[1]) < tol for w in want), tag
    assert len(legs) == len(want)
    # The rails span more than the cabinet's own depth, which is the whole reason for them.
    assert 17.5 > _HP3_CAB_D_IN


def test_hp3_has_open_yard_airflow_and_its_coordinated_pad(catlin_model):
    from shapely.geometry import Polygon, box

    unit = catlin_model.plan.by_tag("EQ-M-HP3-OD")
    assert unit.rotation.degrees == pytest.approx(180)
    cx, cy = (v / INCH for v in unit.position.xy_m)
    west, east = cx - _HP3_CAB_W_IN / 2, cx + _HP3_CAB_W_IN / 2
    rear, front = cy - _HP3_CAB_D_IN / 2, cy + _HP3_CAB_D_IN / 2
    assert rear - _HP3_CLADDING_Y_IN >= 12 - 1e-7
    assert west == pytest.approx(0)
    # Reserve 24in both sides and 80in of unobstructed north discharge.
    clearance = box((west - 24) * INCH, rear * INCH,
                    (east + 24) * INCH, (front + 80) * INCH)
    for wall in catlin_model.walls:
        if wall.tag.startswith("W-G"):
            assert not clearance.intersects(Polygon(wall.layers[0].polygon))
    screen_west = min(p[0] / INCH for s in catlin_model.solids
                      if s.tag.startswith("SC-BW-WEST") for p in s.outline)
    assert screen_west - east >= 24
    pad = Polygon(_solid(catlin_model, _HP3_PAD).outline)
    assert pad.contains(box(west * INCH, rear * INCH, east * INCH, front * INCH))


# ---------------------------------------------------------------------------------------
# EQ-M-HP1-OD's pad and stand, north face east of the garage
# (params/hp1_north_pad.py, added 2026-09-04)
# ---------------------------------------------------------------------------------------
# System 1's condenser left the pocket the day its air handler left RM-S-STUDY2's ceiling
# for RM-S-NCLOSET's: with the machine at the north end of the second storey, the short
# lineset is up the north wall. The same coupling as the other two pads has to hold across
# two modules that cannot import each other, and no check asks what a FLOOR-mounted exterior
# machine bears on.
_HP1_PAD = "SL-M-HP1PAD"
_HP1_CAB_W_IN, _HP1_CAB_D_IN = 39.0, 14.5625
_HP1_CLADDING_Y_IN = 36 * 12 + 7.25   # params/roof_trim.py::_WALL_OUTBOARD_IN off y=36'
#: The garage's plan extent, and it is the ROOF's, not the wall's. The discharge argument
#: turns on the cabinet standing EAST of it: the 48 1/2" slot could never give a 24k unit
#: 40" of throw.
#:
#: ** 31'-10" SINCE 2026-09-07 (was 24'-0"). ** Two things moved it. The garage went 6'-0"
#: east onto the house ridge, and its own ridge turned north-south — so the edge facing this
#: cabinet stopped being a rake at the wall line and became an EAVE carrying a gutter, whose
#: outer face stands 1'-10" proud of the 30'-0" wall. Asserting the wall line here would let
#: the cabinet sit under the trough and still pass. See notes/garage_orientation_lot.md.
_GARAGE_EAST_X_FT = 31.0 + 10.0 / 12.0


def test_hp1_stands_on_a_pad_at_the_same_top_and_height_as_the_other_two(catlin_model
                                                                        ) -> None:
    """One pad top and one stand height across all three outdoor units, still.

    -2'-8" + 18" = -1'-2", and every cabinet carries ``inch(-14)``. ``mount.elevation`` did
    NOT change when this unit moved, and that is the point: the new pad was poured to the
    old pad's top so the authored -14" stayed true. A pad at some other top would be
    invisible in the model and obvious on site.
    """
    pad = _solid(catlin_model, _HP1_PAD)
    assert pad.category == "slab"
    assert pad.z1_m / FT == pytest.approx(_HP_PAD_TOP_FT)
    assert (pad.z1_m - pad.z0_m) / INCH == pytest.approx(4.0)
    site_grade = catlin_model.plan.project.site.grade.meters
    assert (pad.z1_m - site_grade) / INCH == pytest.approx(2.0)

    legs = [s for s in catlin_model.solids if s.tag.startswith("PT-M-HP1-L")]
    assert len(legs) == 4, [s.tag for s in legs]
    for leg in legs:
        assert leg.z0_m == pytest.approx(pad.z1_m), leg.tag
        assert (leg.z1_m - leg.z0_m) / INCH == pytest.approx(_HP_STAND_IN), leg.tag
        assert leg.assembly == "EQUIP_STAND_ALUM", leg.tag

    storeys = {s.tag: s for s in catlin_model.plan.storeys}
    unit = next(e for s in catlin_model.plan.storeys
                for e in catlin_model.plan.storey_elements(s.tag)
                if getattr(e, "tag", "") == "EQ-M-HP1-OD")
    base = resolved_mount_elevation(storeys["main"], unit)
    assert base == pytest.approx(max(leg.z1_m for leg in legs))
    assert base / FT == pytest.approx(-1 - 2 / 12.0)
    assert not getattr(unit, "drain_pan", False)
    assert getattr(unit, "pan_drain_ref", None) is None


def test_hp1s_four_anchors_name_their_leg_and_the_pad(catlin_model) -> None:
    """Same part and the same pairing as the other two stands: an anchor naming a leg but
    not the slab it is set into describes a fastener into nothing."""
    anchors = [e for s in catlin_model.plan.storeys
               for e in catlin_model.plan.storey_elements(s.tag)
               if getattr(e, "tag", "").startswith("CN-M-HP1-A")]
    assert len(anchors) == 4, [e.tag for e in anchors]
    legs = {s.tag for s in catlin_model.solids if s.tag.startswith("PT-M-HP1-L")}
    for anchor in anchors:
        assert anchor.kind.value == "equipment_anchor", anchor.tag
        assert anchor.size == "SS316-WEDGE-38x3", anchor.tag
        assert _HP1_PAD in anchor.connects, anchor.tag
        assert legs & set(anchor.connects), anchor.tag
        assert anchor.elevation.meters / FT == pytest.approx(_HP_PAD_TOP_FT), anchor.tag


def test_hp1_faces_north_off_its_own_pad(catlin_model) -> None:
    """The siting, in the four numbers that decide it.

    ``rotation=deg(180)`` faces the discharge NORTH, away from the wall — the opposite of the
    deg(0) this unit carried in the pocket, where it discharged south into open yard. 6" of
    back clearance against a published 4", 14" to the garage's east gutter face, and 40" of
    throw.

    ** THE 40" IS ONLY LEGAL BECAUSE THE CABINET STANDS EAST OF THE GARAGE. ** Since
    2026-09-07 the garage occupies x 6'..30' with its roof to 31'-4" and its gutter to
    31'-10"; this cabinet is at x 33'-0"..36'-3", past its plan extent, throwing into open
    front yard. Assert that, not the 40", because the 40" is a consequence.

    ** IT OVERSAILS THE HOUSE'S NE CORNER BY 3", DELIBERATELY. ** 31'-10" to 36'-0" is 50"
    and the cabinet plus its 14" clearance is 53". The alternative was to sit flush and give
    the far end 11" — trading a published-unknown airflow clearance for a mounting cosmetic.
    Airflow won, and that is why this test does NOT assert the cabinet stays inside x=36'.

    And the price, asserted so nobody discovers it on site: the cabinet laps a kitchen
    window's rough opening in plan. There is no window-free band 39" wide on this wall — the
    widest is 34 1/2" — so a north-face siting laps one wherever it goes. It used to be
    WIN-M-KITCH over the sink; since the move east it is WIN-M-KITCH-N, and by less.
    """
    from shapely.geometry import Polygon

    unit = next(e for s in catlin_model.plan.storeys
                for e in catlin_model.plan.storey_elements(s.tag)
                if getattr(e, "tag", "") == "EQ-M-HP1-OD")
    assert unit.rotation.degrees == pytest.approx(180.0)
    assert unit.footprint[0].inches == pytest.approx(_HP1_CAB_W_IN)
    assert unit.footprint[1].inches == pytest.approx(_HP1_CAB_D_IN)
    cx_in, cy_in = (v / INCH for v in unit.position.xy_m)
    # 6" of back clearance to the house cladding, against Gree's published 4".
    assert (cy_in - _HP1_CAB_D_IN / 2.0) - _HP1_CLADDING_Y_IN == pytest.approx(6.0)
    # East of the garage's plan extent, which is what gives the discharge somewhere to go.
    assert cx_in - _HP1_CAB_W_IN / 2.0 > _GARAGE_EAST_X_FT * 12.0
    # It laps the kitchen sink window. Unavoidable, and stated rather than discovered.
    # W-M-N1 runs EAST to WEST, so the opening's `center_along_m` is subtracted from the
    # wall's start x rather than added to it.
    wall = _wall(catlin_model, "W-M-N1")
    lapped = []
    for tag in ("WIN-M-KITCH", "WIN-M-KITCH-N"):
        window = next(o for o in catlin_model.openings if o.tag == tag)
        assert window.host_wall == "W-M-N1"
        wx_in = (wall.axis[0][0] - window.center_along_m) / INCH
        ro_half = (window.width_m / INCH) / 2.0
        if abs(wx_in - cx_in) < _HP1_CAB_W_IN / 2.0 + ro_half:
            lapped.append(tag)
    assert lapped, "a 39\" cabinet cannot miss both windows on this wall"

    # Every leg's full 2" section lands on the pad, and on a published foot hole.
    pad = Polygon(_solid(catlin_model, _HP1_PAD).outline)
    legs = {s.tag: Polygon(s.outline) for s in catlin_model.solids
            if s.tag.startswith("PT-M-HP1-L")}
    cx, cy = unit.position.xy_m
    want = [(cx + sx * 29.75 * INCH / 2.0, cy + sy * 15.5625 * INCH / 2.0)
            for sx in (-1, 1) for sy in (-1, 1)]
    tol = 0.001 * INCH
    for tag, ring in legs.items():
        assert pad.contains(ring), f"{tag} overhangs the pad"
        got = (ring.centroid.x, ring.centroid.y)
        assert any(abs(got[0] - w[0]) < tol and abs(got[1] - w[1]) < tol
                   for w in want), tag
    assert len(legs) == len(want)
