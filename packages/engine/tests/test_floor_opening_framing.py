"""Floor-opening edge framing (plans/TODO.md "Stair framing follow-ups", defect 1).

Two defects lived side by side in ``resolve/floors.py``:

* the doubled trimmer pair was emitted twice at *identical* endpoints, so the second ply
  was invisible geometry — it rendered, measured and clashed as one member, not two; and
* an opening header was emitted as a single ply of the deck's own ``JoistSpec.member``,
  which is neither doubled nor sized: catlin's 3'-4" attic header and its 11'-0" stair
  header were the same unsized I-joist ply.

These lock the fix, plus the advisory that says so when a header outruns the prescriptive
table rather than letting the drawn member imply a prescriptive answer.
"""

from __future__ import annotations

import pytest
from _helpers import CATLIN as CATLIN_DIR

from typehaus.checks import build_context
from typehaus.checks.structural.checks import floor_opening_header_within_prescriptive
from typehaus.findings import Result
from typehaus.quantities import ft, inch
from typehaus.resolve.floor_openings import opening_header_profile
from typehaus.resolve.framing.profiles import cross_section


def _members(model, category):
    return [member for floor in model.floors for member in floor.members
            if member.category == category]


def _endpoints(member):
    return (round(member.p0[0], 6), round(member.p0[1], 6),
            round(member.p1[0], 6), round(member.p1[1], 6))


# ------------------------------------------------------------------ trimmer plies
def test_trimmer_plies_are_not_coincident(catlin_model):
    trimmers = _members(catlin_model, "trimmer")
    assert trimmers, "catlin frames stair openings in both wood decks"
    assert len({_endpoints(member) for member in trimmers}) == len(trimmers)


def test_an_extended_trimmer_stops_at_a_neighbouring_wells_bearing(catlin_model):
    # FO-S-ERV-CHASE's header-edge trimmers once ran to x=18', across FO-S-STAIR's well,
    # and folded the stair's north pack out to the same 17'-6 3/4".
    members = {m.child_key: m for floor in catlin_model.floors if floor.tag == "FS-S-WEST"
               for m in floor.members if m.category == "trimmer"}
    stair_west = ft(10, 3.375).meters
    for key in ("trimmer-FO-S-ERV-CHASE-0-0", "trimmer-FO-S-ERV-CHASE-1-0"):
        assert members[key].p1[0] == pytest.approx(stair_west), key
    assert members["trimmer-FO-S-STAIR-1-0"].p0[0] == pytest.approx(stair_west)


def test_trimmer_plies_lie_face_to_face_outboard_of_the_opening(catlin_model):
    """Ply 0 keeps the authored opening line (the header ends bear on it); ply 1 steps
    exactly one ply thickness *away* from the hole, which is where the second trimmer of
    a doubled pair goes.

    **Only the DOUBLED edges are in scope.** ``_trimmer_plies`` lays one ply, not two, on an
    edge inside R502.10.1's 4' short-opening allowance on a sawn deck (catlin's porch had
    two such chases until the centre support line was retired, 2026-09). An edge with no
    ply 1 is that rule working, so this asserts the GEOMETRY of a pair wherever there is a
    pair, and :func:`test_a_short_sawn_opening_is_headed_in_single_joist_sized_members`
    asserts that the singles are single.
    """
    trimmers = {member.child_key: member for member in _members(catlin_model, "trimmer")}
    pairs = {key[: -len("-0")] for key in trimmers
             if key.endswith("-0") and f"{key[: -len('-0')]}-1" in trimmers}
    assert pairs
    for prefix in pairs:
        first, second = trimmers[f"{prefix}-0"], trimmers[f"{prefix}-1"]
        thickness = cross_section(first.profile).width_m
        gap = max(abs(second.p0[0] - first.p0[0]), abs(second.p0[1] - first.p0[1]))
        assert gap == pytest.approx(thickness, abs=1e-9), prefix
        # Same run, same z band — a ply, not a different member.
        assert second.length_m == pytest.approx(first.length_m)
        assert (second.z0_m, second.z1_m) == pytest.approx((first.z0_m, first.z1_m))


# ------------------------------------------------------------------ header sizing
def test_opening_headers_are_multi_ply_and_deck_deep(catlin_model):
    """Every header is flush in its joist band, and doubled unless R502.10.1 says otherwise.

    The DEPTH half holds for every header without exception: a header hangs *inside* the
    band so the cut joists land on it at their own depth, and one that is not band-deep is
    drawn wrong whatever its ply count.

    The PLY half is conditional, and the condition is the code's. ``opening_header_profile``
    emits a single member the size of the floor joist for an opening inside R502.10.1's 4'
    allowance on a sawn-lumber deck, and doubles up past it. Catlin has no short SAWN
    opening since its porch pillar chases were retired (2026-09), so the single-member half
    is exercised on a synthetic 2x10 deck in
    :func:`test_a_short_sawn_opening_is_headed_in_single_joist_sized_members`.
    """
    from typehaus.resolve.floor_openings import (
        _SINGLE_MEMBER_SPAN_M,
        _prescriptive_short_opening,
    )

    headers = _members(catlin_model, "header")
    assert headers
    short = 0
    short_span_engineered = 0
    for floor in catlin_model.floors:
        joist = next((member for member in floor.members if member.category == "joist"), None)
        if joist is None:
            continue
        band_depth = cross_section(joist.profile).depth_m
        for header in (m for m in floor.members if m.category == "header"):
            section = cross_section(header.profile)
            # **The span is not the whole condition — the DECK MATERIAL is the other
            # half.** R502.10 is a sawn-lumber table, so ``FO-M-ERV-OA``'s and
            # ``FO-M-ERV-EA``'s headers — 11" and 10 3/4", an order of magnitude inside the
            # 4'-0" allowance — are short by span and still DOUBLED: ``FS-M-MECH`` is framed
            # in I-joists, where "a single member the same size as the floor joist" means a
            # hung I-joist with web stiffeners and backer blocks out of a manufacturer's
            # table this engine cannot grade. Testing on span alone would call them wrong.
            # (``FO-M-FIRE`` was the witness here until 2026-09-19, when it was retired: the
            # fireplace piers stand in joist pockets now and the deck has no hole at all.
            # These two are the better witness anyway — being ten times inside the allowance
            # they flip LOUDLY if the sawn-lumber gate is ever removed.)
            if (header.length_m <= _SINGLE_MEMBER_SPAN_M + 1e-9
                    and not _prescriptive_short_opening(header.length_m, joist.profile)):
                short_span_engineered += 1
            if _prescriptive_short_opening(header.length_m, joist.profile):
                # R502.10.1: a single member the same size as the floor joist.
                assert section.plies == 1, header.child_key
                assert header.profile == joist.profile, header.child_key
                short += 1
            else:
                assert section.plies >= 2, header.child_key
            # Flush in the joist band, so the cut joists hang off it at their own depth.
            assert section.depth_m == pytest.approx(band_depth), header.child_key
    # No short sawn opening is left in catlin (the porch's two 9" pillar chases went with
    # the centre support line, 2026-09); the single-member branch is pinned synthetically.
    assert short == 0
    # The sawn-lumber gate, promoted from the comment above to an assertion. Both ERV riser
    # chases sit far inside R502.10.1's span allowance and are doubled anyway because their
    # deck is I-joist; drop the ``is_sawn_lumber`` half of ``_prescriptive_short_opening``
    # and this count goes to zero.
    assert short_span_engineered >= 2, (
        "expected the ERV riser chases' headers to be short by span and doubled by member")


def test_header_ply_count_tracks_the_span(catlin_model):
    """Ply count must track span, not draw the same single ply for every opening."""
    band = cross_section("11.875 I-joist").depth_m
    short = cross_section(opening_header_profile(ft(3, 4).meters, band))
    long = cross_section(opening_header_profile(ft(11).meters, band))
    assert short.plies == 2
    assert long.plies > short.plies
    assert short.depth_m == pytest.approx(band) and long.depth_m == pytest.approx(band)


def _plan_without_stair_bearing_refs(catlin_plan):
    """Catlin with FO-S-STAIR's ``bearing_refs`` stripped.

    Both of that opening's long edges are carried by bearing wall, so the resolver draws
    no header for it at all — which leaves the advisory nothing to report. Dropping the
    declared bearing restores exactly the condition the rule guards: a 10'-3" opening edge
    with nothing under it, closed by a header past the prescriptive table.
    """
    plan = catlin_plan
    elements = {
        storey: [element.model_copy(update={"bearing_refs": ()})
                 if getattr(element, "tag", None) == "FO-S-STAIR" else element
                 for element in storey_elements]
        for storey, storey_elements in plan.elements.items()
    }
    return plan.model_copy(update={"elements": elements})


def test_no_header_is_drawn_where_bearing_wall_carries_the_edge(catlin_model):
    """FO-S-STAIR is drawn to the finished well, so no edge coincides with a wall axis.

    The bearing test reads each declared wall's plan *footprint*, so both long edges are
    still recognised as wall-borne — a centreline-equality test claimed neither was and
    put a 10'-3" engineered header under both (plans/TODO.md D3).
    """
    headers = [member for member in _members(catlin_model, "header")
               if "FO-S-STAIR" in member.child_key]
    assert headers == []


def test_beyond_prescriptive_header_is_reported(catlin_plan):
    """A 10'-3" floor-opening header is an engineered beam; the drawing set has to say
    so, which ``structural.header_prescriptive`` only ever did for *wall* openings."""
    plan = _plan_without_stair_bearing_refs(catlin_plan)
    ctx, _ = build_context(plan, CATLIN_DIR)
    findings = floor_opening_header_within_prescriptive(ctx)
    failures = [finding for finding in findings if finding.result is Result.FAIL]
    assert failures, "an unsupported FO-S-STAIR edge needs a header spanning 10'-3\""
    assert all(finding.severity.value == "warn" for finding in findings)
    for header in _members(ctx.model, "header"):
        if header.length_m / inch(12).meters <= 8.0 + 1e-9:
            assert not any(header.child_key in finding.message for finding in failures)


# ------------------------------------------------ R502.10.1: the short-opening allowance
# IRC R502.10.1 lets a header joist spanning 4 ft or less be a single member the same size
# as the floor joist, with single trimmers; the doubling starts past that line. The engine
# threw the prescriptive answer away except for its leading ply digit, so 36", 48" and 49"
# all emitted the same 2-ply LVL.
#
# The allowance is deliberately SAWN-LUMBER ONLY. On an I-joist or floor-truss deck "the
# same size as the floor joist" means a single I-joist used as a header, hung on both
# faces — a manufacturer's table, not R502.10's — so the engineered header is kept there.
# Catlin is all-engineered and therefore unchanged by this rule; that is the honest answer.

def test_short_sawn_opening_takes_a_single_joist_sized_header():
    band = cross_section("2x8").depth_m
    assert opening_header_profile(ft(3, 4).meters, band, "2x8") == "2x8"
    assert opening_header_profile(ft(4).meters, band, "2x8") == "2x8"


def test_past_four_feet_a_sawn_opening_is_back_on_the_prescriptive_header():
    band = cross_section("2x8").depth_m
    header = cross_section(opening_header_profile(ft(4, 1).meters, band, "2x8"))
    assert header.plies == 2


def test_engineered_decks_keep_the_engineered_header_at_every_span():
    """The strength guard: R502.10 is a sawn-lumber table and does not reach an I-joist."""
    band = cross_section("11.875 I-joist").depth_m
    for member in ("11.875 I-joist", "11.875 floor truss", "11.875 TJI 230"):
        short = cross_section(opening_header_profile(ft(3).meters, band, member))
        assert short.plies == 2, member
        assert short.depth_m == pytest.approx(band), member


def test_trimmer_plies_follow_the_same_line():
    from typehaus.resolve.floor_openings import _trimmer_plies
    assert _trimmer_plies(ft(3, 4).meters, "2x8") == 1
    assert _trimmer_plies(ft(4, 1).meters, "2x8") == 2
    assert _trimmer_plies(ft(3, 4).meters, "11.875 I-joist") == 2


def test_catlin_is_unchanged_by_the_short_opening_allowance(catlin_model):
    """Every catlin deck is engineered, so every trimmer stays a doubled pair."""
    trimmers = {member.child_key for member in _members(catlin_model, "trimmer")}
    assert trimmers
    assert {key for key in trimmers if key.endswith("-1")}, "doubled pairs survive"
    for key in trimmers:
        assert key.endswith(("-0", "-1")), key


# ------------------------------------------------ bearing-to-bearing trimmers + hangers
# A 24'x12' I-joist deck in x on three bearing lines (x = 0, 12', 24'); the opening sits in
# the east span at y 4'-0"..7'-4", so the y=4'-0" joist line is ON its south edge and the
# 5'-4"/6'-8" lines are inside it.
def _deck_plan(*, east_edge=None, opening_bearing=(), member="11.875 I-joist"):
    import uuid

    from typehaus.model import (
        Assembly,
        Building,
        FloorOpening,
        FloorSystem,
        FramingSpec,
        JoistSpec,
        Layer,
        LayerFunction,
        Library,
        Material,
        Node,
        PlanModel,
        Project,
        Site,
        Storey,
        Wall,
    )
    from typehaus.quantities import degF, pt

    east_edge = east_edge or ft(20)
    stud = Assembly(tag="EXT", layers=(
        Layer(name="stud", material_ref="wood", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6")),))
    project = Project(
        name="Deck", project_uuid=uuid.UUID("00000000-0000-4000-8000-0000000000b1"),
        site=Site(lat=44.9, lon=-93.2, elevation=ft(830), design_temp_heating=degF(-15),
                  design_temp_cooling=degF(90)), building=Building(name="Deck"))
    main = Storey(uid="STMAIN0001", tag="main", elevation=ft(0), default_ceiling_height=ft(9))
    second = Storey(uid="STSEC00001", tag="second", elevation=ft(9),
                    default_ceiling_height=ft(9))
    nodes, walls = [], []
    for index, x in enumerate((0, 12, 24)):
        south, north = f"N-{index}S", f"N-{index}N"
        nodes += [Node(uid=f"N{index:08d}S", tag=south, position=pt(ft(x), ft(0)), open_end=True),
                  Node(uid=f"N{index:08d}N", tag=north, position=pt(ft(x), ft(12)), open_end=True)]
        walls.append(Wall(uid=f"W{index:09d}", tag=f"W-{x}", start_node=south,
                          end_node=north, assembly="EXT", top=ft(9)))
    plan = PlanModel(project=project, library=Library(
        materials=(Material(tag="wood", name="Wood", r_per_inch=1.25),),
        assemblies=(stud,)), storeys=(main, second))
    deck = (
        FloorOpening(uid="FO00000001", tag="FO-1", bearing_refs=opening_bearing, outline=(
            pt(ft(14), ft(4)), pt(east_edge, ft(4)), pt(east_edge, ft(7, 4)),
            pt(ft(14), ft(7, 4)))),
        FloorSystem(uid="FS00000001", tag="FS-1", openings=("FO-1",), joists=JoistSpec(
            member=member, spacing=inch(16), direction="x",
            bearing_refs=("W-0", "W-12", "W-24"))),
    )
    return plan.with_elements("main", (*nodes, *walls)).with_elements("second", deck)


def _deck(**fields):
    from typehaus.resolve import resolve

    model, findings = resolve(_deck_plan(**fields))
    assert not [f for f in findings if f.severity.value == "error"], findings
    return model, {member.child_key: member for member in model.floors[0].members}


def test_trimmers_run_bearing_to_bearing_at_a_header_edge():
    model, members = _deck()
    tip_hi = model.floors[0].ends.tip_hi
    for key in ("trimmer-FO-1-0-0", "trimmer-FO-1-0-1", "trimmer-FO-1-1-0"):
        trimmer = members[key]
        assert trimmer.p0[0] == pytest.approx(ft(12).meters), key  # the x=12' bearing
        assert trimmer.p1[0] == pytest.approx(tip_hi), key
        assert trimmer.length_m == pytest.approx(tip_hi - ft(12).meters), key
    assert {"header-FO-1-0", "header-FO-1-1"} <= members.keys()


def test_trimmers_stop_at_a_declared_bearing_edge():
    edge = ft(23, 9.25)  # inside W-24's 5 1/2" footprint
    _model, members = _deck(east_edge=edge, opening_bearing=("W-24",))
    assert "header-FO-1-1" not in members
    trimmer = members["trimmer-FO-1-0-0"]
    assert trimmer.p0[0] == pytest.approx(ft(12).meters)
    assert trimmer.p1[0] == pytest.approx(edge.meters)


def test_an_absorbed_joist_line_leaves_no_stub_and_inside_lines_keep_tails():
    _model, members = _deck()
    east_span = (ft(12).meters, ft(24).meters)
    on_edge = [m for m in members.values() if m.category == "joist"
               and m.p0[1] == pytest.approx(ft(4).meters)
               and m.p1[0] > east_span[0] + 1e-6]
    assert on_edge == [], "the y=4' line is the trimmer pack across the whole east span"
    tails = sorted((round(m.p0[0] / inch(1).meters, 3), round(m.p1[0] / inch(1).meters, 3))
                   for m in members.values() if m.category == "joist"
                   and m.p0[1] == pytest.approx(ft(5, 4).meters) and m.p1[0] > east_span[0])
    assert tails[0] == (144.0, 168.0) and tails[1][0] == 240.0


def test_i_joist_trimmers_are_band_deep_lvl_and_sawn_decks_keep_their_stock():
    from typehaus.resolve.floor_openings import opening_trimmer_profile

    _model, members = _deck()
    assert members["trimmer-FO-1-0-0"].profile == "1.75x11.875 LVL"
    band = cross_section("11.875 I-joist").depth_m
    assert opening_trimmer_profile("11.875 TJI 230", band) == "1.75x11.875 LVL"
    assert opening_trimmer_profile("2x10", cross_section("2x10").depth_m) == "2x10"
    assert opening_trimmer_profile("11.875 floor truss", band) == "11.875 floor truss"


def test_tails_hang_on_the_header_and_the_header_hangs_on_the_trimmers():
    from typehaus.hardware.config import HangerDetectionRules
    from typehaus.joints.hung import hung_connections

    model, _members = _deck()
    hung = {(c.member_key.split(":")[1], c.carrier_tag.split(":")[1])
            for c in hung_connections(model, HangerDetectionRules())}
    tails = {(member, carrier) for member, carrier in hung if carrier.startswith("header-")}
    assert len(tails) == 4, "two cut lines, each hung at both headers"
    assert {(member, carrier) for member, carrier in hung if member.startswith("header-")} == {
        ("header-FO-1-0", "trimmer-FO-1-0-0"), ("header-FO-1-0", "trimmer-FO-1-1-0"),
        ("header-FO-1-1", "trimmer-FO-1-0-0"), ("header-FO-1-1", "trimmer-FO-1-1-0")}
    assert not any(carrier.startswith("trimmer-") and member.startswith("joist-")
                   for member, carrier in hung)


def test_a_short_sawn_opening_is_headed_in_single_joist_sized_members():
    """R502.10.1 on a sawn deck: a 3'-4" opening in 2x10s takes a single 2x10 header at each
    headed edge and single trimmers. The witness catlin carried until 2026-09 (the porch's
    two 9" pillar chases); named, so removing the allowance fails here loudly."""
    from typehaus.resolve.floor_openings import _prescriptive_short_opening

    _model, members = _deck(member="2x10")
    headers = [m for m in members.values() if m.category == "header"]
    assert len(headers) == 2, "both headed edges of the opening"
    for header in headers:
        assert _prescriptive_short_opening(header.length_m, "2x10"), header.child_key
        assert cross_section(header.profile).plies == 1, header.child_key
        assert header.profile == "2x10", header.child_key
    trimmers = {m.child_key for m in members.values() if m.category == "trimmer"}
    assert trimmers
    assert not {key for key in trimmers if key.endswith("-1")}, "single trimmers"


def test_a_short_sawn_opening_is_end_nailed_not_hung():
    """IRC R502.10: a sawn header takes hangers past a 6' span and a tail past 12'. This
    opening's 3'-4" header and 2' tails are nailed, so no opening joint buys a hanger."""
    from typehaus.hardware.config import HangerDetectionRules
    from typehaus.joints.hung import hung_connections

    model, members = _deck(member="2x10")
    assert "header-FO-1-0" in members
    assert not [c for c in hung_connections(model, HangerDetectionRules())
                if c.carrier_tag.split(":")[1].startswith(("header-", "trimmer-"))]
