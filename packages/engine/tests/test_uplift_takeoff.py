"""The uplift load path: bearing ties, post bases, post/beam straps, lateral tie plates.

The trap this file exists to hold is **double billing**. Every rule here derives a joint that
a house may also have authored a ``Connector`` for, and the sunken garden and the breezeway
author twenty of them; a rule that ignored those would buy each one twice and the total would
still look plausible. So the guard gets its own tests, by tag, not just a total.

The second trap is the boundary with ``takeoff/hangers.py``. A member end either hangs in a
carrier's depth or bears on its top; both rules walk the same members, and if their tests
only checked their own counts a member end could be billed a hanger AND a tie without either
file noticing. ``test_a_hung_end_is_never_also_a_bearing`` is that check.
"""

from __future__ import annotations

import pytest

from typehaus.hardware.config import DEFAULT_HARDWARE_TAKEOFF_CONFIG as CONFIG
from typehaus.hardware.config import UpliftTieRules
from typehaus.takeoff.uplift import (
    bearing_connections,
    lateral_tie_plate_rows,
    uplift_rows,
)
from typehaus.takeoff.uplift_joints import post_base_rows, post_beam_strap_rows

RULES = CONFIG.uplift

#: Every wood post the sunken garden and the breezeway already author an ABU66SS base under.
#: They are the whole of catlin's post-base scope, which is why ``post_base_rows`` derives
#: nothing: the derived rule is the guard against the *next* post being forgotten.
#:
#: Six, not ten, since 2026-09-03: the balcony's four CORNER pillars became 12" cast
#: concrete columns fixed at their bases and doweled into the wall tops under them, and
#: concrete-on-concrete takes no post base at all. Then FOUR later the same day, when the
#: two CENTRE pillars went from an ABU66SS to an inverted CCQ column cap — an ABU has no published
#: value bearing on framing, and the R317.1.4 standoff it was cited for governs wood on
#: CONCRETE. See ``houses/catlin/notes/balcony_moment_columns.md``.
# The canopy's two WEST columns, authored as ABU66SS on 2026-09-10 so the order names the
# stainless part the house actually buys rather than the galvanized one the section-based
# derivation reaches for. The east pair is not here because it no longer exists: PT-BW-RE and
# PT-BW-RNE run full height in cast concrete and carry no wood column at all.
# The canopy's two west columns on ABU66SS, and since 2026-09-11 the two interior landing
# posts on ABU44 (CN-BW-IBASE-C/-E): 4x4 KDAT standing 25 3/4" on the garage slab, authored
# so the 1" standoff is on the drawings — and so the base can say `anchored=False`, which no
# derived base can. There is no cast-in bolt under those two; see
# ``test_every_post_base_on_concrete_is_bought_its_anchor``.
#: The two balcony centre pillars joined this set on 2026-09-14, when they came off the porch
#: framing and onto the cast column tops (CN-SG-BASE-R2 / -F2, ABU66SS, ``anchored=True``).
#: They were covered by an authored TENSION_TIE until then, and the kind moved with the joint
#: rather than with the part: ``model/enums.py`` reads TENSION_TIE as "a post on FRAMING" and
#: POST_BASE as "a stirrup on CONCRETE", so a pillar that now stands on a pour takes a base.
AUTHORED_POST_BASES = {"PT-BW-CW", "PT-BW-CNW", "PT-BW-IC", "PT-BW-IE"}

#: **Empty since 2026-09-14, and kept rather than deleted.** ``post_base_rows`` reads BOTH
#: kinds — a post whose joint is already made must not be bought a base — and while the two
#: centre pillars were tied rather than based, this set was the only thing exercising the
#: TENSION_TIE half of that rule in this house. Nothing exercises it now, so the empty set is
#: the statement: a tie reappearing here is a house change, and the rule reading two kinds is
#: still asserted below, where every tag in the union must stay out of the derived basis.
AUTHORED_TENSION_TIES: set[str] = set()

#: The north entry's two canopy-header-to-column joints, authored as CCQ46SDS2.5 column caps
#: (``CN-BW-CAP-W`` / ``CN-BW-CAP-E``) with RF-BW-CANOPY on 2026-09-10. The tags are the ones
#: the retired breezeway roof beams used to carry; they name real members again, and the
#: guard is the same one it always was — a joint an authored connector already makes must not
#: be derived a strap on top.
AUTHORED_POST_BEAM_JOINTS = {frozenset({"BM-BW-RW", "PT-BW-CW"}),
                             frozenset({"BM-BW-RW", "PT-BW-CNW"})}


@pytest.fixture(scope="module")
def rows(catlin_model_ro):
    return uplift_rows(catlin_model_ro, RULES)


@pytest.fixture(scope="module")
def connections(catlin_model_ro):
    return bearing_connections(catlin_model_ro, RULES)


# --- rule 1: bearing ties ------------------------------------------------------------


def test_every_rafter_is_tied_at_its_eave(catlin_model_ro, connections) -> None:
    """One tie per rafter, reconciled against the roof's own bearing-stiffener census.

    ``resolve/framing/roof.py::_bearing_stiffeners`` emits one stiffener per I-joist rafter
    END — at ``rafter.p0`` for the eave bearing, and since 2026-08-28 at the ridge too, where
    the sloped hanger requires it. It is derived by a different rule, from a different field,
    in a different module — so the EAVE half is an independent witness that this count is the
    number of bearings and not the number of something adjacent to them. Filter on the
    connection rather than counting both: only the eave ends are tied here, and a bare
    ``len(stiffeners)`` would have started passing for the wrong reason the day the peak got
    its own.
    """
    roof = next(roof for roof in catlin_model_ro.roofs if roof.tag == "RF-HOUSE")
    rafters = [m for m in roof.members if m.category == "rafter"]
    stiffeners = [m for m in roof.members if m.category == "bearing_stiffener"]
    eave = [m for m in stiffeners if m.connection == "eave:beveled-web-stiffener"]
    ridge = [m for m in stiffeners if m.connection == "ridge:beveled-web-stiffener"]
    assert len(rafters) == len(eave) == len(ridge) > 0
    assert len(stiffeners) == 2 * len(rafters)

    tied = [c for c in connections if c.member_category == "rafter"]
    assert len(tied) == len(rafters)
    # The ridge end is HUNG on RB-HOUSE and billed an LSSR by hangers.py, so only the attic
    # side walls appear here — never the ridge beam. FOUR of them since 2026-08-29: W-A-W1
    # split at N-A-W2 (y=22'-4") when the guest studio walled its storage pocket off, so the
    # west knee wall is W-A-W1 north of that line and W-A-W1B south of it. Same wall, same
    # rafters landing on it, one more tag.
    assert {c.support_tag for c in tied} == {"W-A-W1", "W-A-W1B", "W-A-E1", "W-A-E2"}


def test_a_truss_roof_is_tied_at_both_ends_of_every_truss(catlin_model_ro,
                                                          connections) -> None:
    """A truss is one member with two bearings, and both of them get a tie.

    This used to tie ``truss_heel``, because the multi-stick truss's top chords crossed the
    plate a foot and a half up on their way to the 16" overhang and tying those would have
    tied the wrong member at the wrong elevation. One member per truss removes the problem
    rather than working around it: the member's own ends ARE its bearings, at the plate top.
    It also picks up the two GABLE-END trusses, which carried no heel block and so went
    untied — 26 ties over 13 trusses where there were 22 over 11.

    Scoped per roof since 2026-09-10, when RF-BW-CANOPY became catlin's second trussed roof:
    a house-wide count would read 34 against RF-GARAGE's 13 and say nothing about either.
    The canopy's 3 trusses bear on BEAMS rather than a wall plate — the rule does not care
    which, and this is the case that says so.
    """
    roof = next(roof for roof in catlin_model_ro.roofs if roof.tag == "RF-GARAGE")
    trusses = [m for m in roof.members if m.category == "roof_truss"]
    tied = [c for c in connections
            if c.member_category == "roof_truss" and c.assembly_tag == "RF-GARAGE"]
    assert len(tied) == 2 * len(trusses) == 26
    # W-G-E / W-G-W since 2026-09-07: the overhead door turned north and RF-GARAGE's ridge
    # turned with it, so the trusses span east-west and bear on the other pair. The count is
    # untouched — a square garage under a rotated gable frames the same number of trusses.
    assert {c.support_tag for c in tied} == {"W-G-E", "W-G-W"}

    # RF-BW-CANOPY derives NOTHING since 2026-09-10 and that is the point of it being here.
    # Its three trusses land on treated headers at a salted entry, so the six ties are
    # authored stainless (`CN-BW-TRTIE-*`) rather than commodity H2.5A, and `authored_joints`
    # stands the derived rule down.
    #
    # THREE, not four, since 2026-09-11. The fourth stood on the 8" tail the headers run past
    # their north columns — out of the 24" module and 1 1/2" off the garage wall — because
    # `build_truss_layout` forces a last station onto the end of the bearing so a gable wall
    # never ends up short of one. `RF-BW-CANOPY` authors `gable_ends=()`, neither end of it is
    # a gable line, and an off-module end station that is not a gable line carries no truss.
    #
    # An empty list here with the connectors present is
    # coverage; an empty list with them GONE is a roof tied by nothing, which is why the
    # count of authored ties is asserted alongside it rather than the absence alone.
    canopy = next(r for r in catlin_model_ro.roofs if r.tag == "RF-BW-CANOPY")
    canopy_trusses = [m for m in canopy.members if m.category == "roof_truss"]
    assert len(canopy_trusses) == 3
    # And every one is a FIELD truss. A gable-end frame is supported continuously by the wall
    # under its bottom chord and does not span, so a gable member on a roof with no wall under
    # either end is one no plant can build — which is what `gable_ends` exists to prevent.
    assert not any(m.truss.gable for m in canopy_trusses)
    assert not [c for c in connections if c.assembly_tag == "RF-BW-CANOPY"]
    authored_ties = [e for storey in catlin_model_ro.plan.storeys
                     for e in catlin_model_ro.plan.storey_elements(storey.tag)
                     if getattr(e, "tag", "").startswith("CN-BW-TRTIE-")]
    assert len(authored_ties) == 2 * len(canopy_trusses) == 6
    assert {t.size for t in authored_ties} == {"H2.5ASS"}
    assert not [c for c in connections
                if c.member_category in {"top_chord", "bottom_chord", "truss_heel"}]


def test_a_floor_is_tied_along_its_whole_bearing_line(catlin_model_ro) -> None:
    """``FS-S-WEST`` names one wall of a line the resolver split into six.

    Its ``joists.bearing_refs`` is ``('W-M-W2', 'W-M-C2', 'BM-M-HALL')``, but its 26 floor
    trusses land across the whole west line. Billing only the named segment tied four of the
    twenty-six and reported the order complete — which is what ``_bearing_line`` exists to
    prevent, and this test is what would catch its removal.
    """
    # Floors on walls are untied by default, so the line rule is exercised with them on.
    from dataclasses import replace
    wall_ties = bearing_connections(catlin_model_ro,
                                    replace(RULES, tie_floor_joists_on_walls=True))
    floor = next(f for f in catlin_model_ro.floors if f.tag == "FS-S-WEST")
    joists = [m for m in floor.members if m.category == "joist"]
    trussed = [c for c in wall_ties if c.member_profile == "11.875 floor truss"]
    # Less one tie: the y=34'-5 3/4" truss's west end hangs on FO-S-ERV-CHASE's header.
    assert len(trussed) == len(joists) - 1 == 25
    assert len({c.support_tag for c in trussed}) > 1, \
        "the west bearing line is more than one wall; a single support means _bearing_line died"


def test_a_floor_joist_on_a_wall_takes_no_tie(catlin_model_ro, connections) -> None:
    """Hurricane ties are for the roof. A joist on a wall plate is toe-nailed and held down
    by the wall above; the band's CS16/LTP4 carry uplift storey to storey."""
    walls = {w.tag for w in catlin_model_ro.walls}
    floors = {f.tag for f in catlin_model_ro.floors}
    on_walls = [c for c in connections if c.assembly_tag in floors and c.support_tag in walls]
    assert not on_walls
    assert [c for c in connections if c.assembly_tag in floors], "deck joists on beams stay tied"


def test_a_hung_end_is_never_also_a_bearing(catlin_model_ro, connections) -> None:
    """The one-sided elevation test is the whole boundary with ``hangers.py``.

    Both modules walk ``all_members()`` and both look at member ends. Nothing but the sign of
    ``bottom_z - support_top`` keeps a joist framed into an 11-7/8" LVL out of this list, so
    an LVL a floor declares as a bearing must contribute no ties at all.
    """
    from typehaus.takeoff.hangers import hung_connections

    hung = hung_connections(catlin_model_ro, CONFIG.hanger_detection)
    assert hung, "the fixture must have hung ends for this test to mean anything"
    # BM-M-HALL and BM-S-HALL are declared bearings of three floors AND carriers of hangers.
    # Every joist reaching them drops into their depth, so neither may appear as a bearing.
    carriers = {c.carrier_tag.split(":")[-1] for c in hung}
    assert {"BM-M-HALL", "BM-S-HALL"} <= carriers
    assert not [c for c in connections if c.support_tag in {"BM-M-HALL", "BM-S-HALL"}]


def test_a_tie_row_names_the_bearings_it_came_from(rows) -> None:
    """A hardware count is only auditable if the row carries the rule that produced it.

    Two rules buy the same part and they are told apart by scope, not by part number: ends
    that BEAR take one tie per joint, and a member that bears along its whole length takes
    them at a pitch instead. Asserting one basis string over every H2.5A row would have
    forced the second rule to lie about which rule it was.
    """
    ties = [row for row in rows if row["part_number"] == "H2.5A"]
    assert ties
    per_joint = [row for row in ties if not row["scope"].endswith("continuous bearing")]
    assert per_joint
    for row in per_joint:
        assert row["count"] > 0
        assert "per bearing joint" in row["basis"]
        assert row["by_storey"] and sum(row["by_storey"].values()) == row["count"]
    for row in ties:
        if row["scope"].endswith("continuous bearing"):
            assert row["count"] > 0
            assert "o.c. plus both ends" in row["basis"]


def test_a_beam_that_bears_everywhere_is_tied_at_a_pitch_not_at_its_ends(rows) -> None:
    """RB-HOUSE had no uplift connector at all until 2026-08-28.

    ``bearing_connections`` ties member ENDS, and the ridge does not meaningfully have two —
    it sits on W-A-C1/C1B/C2 for all 36'. ``uplift_path.py`` walks ``Beam.bearing_refs`` but
    skips a ref that resolves to a wall, and ``uplift.py`` walked the roof's own bearing_refs,
    which name the eave line. So the member carrying the whole roof down the centre of
    the house was in neither. Ten is the fencepost count, not 36/4.
    """
    ridge = [row for row in rows
             if row["part_number"] == "H2.5A" and row["scope"].endswith("continuous bearing")]
    assert len(ridge) == 1
    assert ridge[0]["size"] == "2-1.75x16 LVL"  # 14 -> 16 with the 6:12 pitch
    assert ridge[0]["count"] == int(36.0 / 4.0) + 1 == 10


# --- the double-billing guard ---------------------------------------------------------


def test_authored_post_bases_are_not_derived_a_second_time(catlin_model_ro) -> None:
    """Every post whose joint is already made by hand; none may be bought a base twice.

    Until 2026-08-28 this asserted an EMPTY list, because every 6x6 that declared a bearing
    was authored and the three 4x4s declared none. The stairwell posts now declare theirs
    (``SL-B-FLOOR``), so the rule derives its first real row — and the guard it is here to
    protect is now visible rather than vacuous: the derived row must be the 4x4 ladder rung
    only, and no authored tag may appear in its basis.
    """
    from typehaus.model.enums import ConnectorKind
    from typehaus.model.structure import Post
    from typehaus.joints.authored import tags_covered_by

    authored = tags_covered_by(catlin_model_ro, frozenset({ConnectorKind.POST_BASE}))
    assert authored >= AUTHORED_POST_BASES, "the fixture's authored bases moved"
    tied = tags_covered_by(catlin_model_ro, frozenset({ConnectorKind.TENSION_TIE}))
    assert tied >= AUTHORED_TENSION_TIES, "the fixture's authored tension ties moved"
    rows = post_base_rows(catlin_model_ro, RULES)
    # ABU66 joined the order on 2026-09-10 with the canopy's 6x6 KDAT roof columns and left
    # it again the same day: the house buys stainless at every treated post base, and the
    # derived rule names the catalog model for the SECTION, which is the galvanized ABU66.
    # `CN-BW-BASE-W` / `-NW` author those two joints as ABU66SS instead, which stands the
    # derivation down, and `CN-BW-IBASE-C` / `-E` do the same for the two interior landing
    # posts (ABU44, authored for the standoff detail). The 4x4 rung that is left is the
    # stairwell posts on the basement slab — a TRIO since 2026-09-15, when ST-M2S's upper
    # half-landing gained a going of depth and with it a third corner over FO-M-STAIR's
    # hole (P-M-STRWELL-SS, houses/catlin/notes/u_stair_split_landing.md). A PAIR again
    # since 2026-09-24: the landings reach the north wall and P-M-STRWELL-N retired.
    #
    # An ABU66 row reappearing is the failure now, and it means an authored base stopped
    # matching. (The balcony centre pillars' ABU66SS bases retired with them, 2026-09.)
    assert [row["part_number"] for row in rows] == ["ABU44"]
    counts = {row["part_number"]: row["count"] for row in rows}
    assert counts == {"ABU44": 2}
    for row in rows:
        for tag in AUTHORED_POST_BASES | AUTHORED_TENSION_TIES:
            assert tag not in row["basis"]
    # And the eight really are all of them, so what is NOT in the rows above is coverage
    # rather than silence: four authored bases, three derived, one squash block (the centre
    # pillars' two authored bases retired in 2026-09). The four balcony corner columns are
    # absent because they are no longer WOOD —
    # the filter below is on section, and a "12 round" is not a 6x6. PT-BW-IC / PT-BW-IE
    # were squash blocks for one day (2026-09-10: 1'-6 1/2" of 6x6 stopping 7 1/4" SHORT of
    # the carriers they were meant to hold, sized off the pier top); since 2026-09-11 they
    # are 25 3/4" 4x4 posts on authored bases, and they left the squash-block set with the
    # height.
    # No ``within_wall`` filter, and deliberately not: since 2026-09-12 that field is
    # geometric only (the framer cuts the plates around the post), so it says nothing about
    # whether the base joint is made. PT-BW-CW / -CNW now carry it — they stand in
    # W-BW-SCREEN's stud line — and still stand on their own authored ABU66SS bases. The
    # tudor timbers, which also carry it, stay out of this set on their 6.125x6.125 section.
    wood = {e.tag for e in catlin_model_ro.plan.all_elements()
            if isinstance(e, Post) and e.supported_by
            and e.size in {"6x6", "4x4"}}
    assert wood == AUTHORED_POST_BASES | AUTHORED_TENSION_TIES | {
        "P-M-STRWELL-S", "P-M-STRWELL-SS", "P-M-STRLAND-SE",
        "PT-BW-CW", "PT-BW-CNW", "PT-BW-IC", "PT-BW-IE"}


def test_a_squash_block_is_not_bought_a_post_base(catlin_model_ro) -> None:
    """P-M-STRLAND-SE is 13 7/16" of blocking in a joist bay, not a column.

    It declares a bearing (``W-B-CN``) and its section is one the catalog stocks a base for,
    so nothing but ``blocking_max_height_ft`` keeps it out of the order — and a base under a
    block is hardware at a joint whose connection is the bearing itself.
    """
    from typehaus.model.structure import Post
    from typehaus.joints.posts import is_squash_block

    posts = {e.tag: e for e in catlin_model_ro.plan.all_elements() if isinstance(e, Post)}
    assert is_squash_block(posts["P-M-STRLAND-SE"], RULES)
    assert not is_squash_block(posts["P-M-STRWELL-S"], RULES), \
        "a 9 ft stairwell post is a column; only the 13 in block is blocking"
    row = post_base_rows(catlin_model_ro, RULES)[0]
    assert "P-M-STRLAND-SE" not in row["basis"]


# --- rule 2b: the bolt under every base ----------------------------------------------


def test_every_post_base_on_concrete_is_bought_its_anchor(catlin_model_ro) -> None:
    """Simpson ship the ABU without the 5/8" bolt its published capacity is taken through.

    Five of catlin's bases land on concrete AND take a bolt — the canopy's two west columns on
    their 12" piers, and the three stairwell 4x4s on the basement slab. The sunken garden has
    none left: its four balcony corners are cast columns, and its two wood centre pillars
    retired with the centre support line (2026-09).

    ** AND TWO BASES LAND ON CONCRETE AND TAKE NO BOLT, WHICH IS THE INTERESTING HALF. **
    PT-BW-IC / PT-BW-IE stand on the garage slab under the interior landing. Their bases are
    authored ``anchored=False`` (2026-09-11): a 5/8" x 10" cast-in bolt needs something like
    8" of embedment and SL-G-FLOOR is 3-1/2" on 1" of XPS, so the bolt could not live there
    without dragging a slab thickening along to house itself. Both went. Those bases transfer
    download by bearing and claim no uplift and no lateral, which is a real configuration and
    the one thing that must not silently re-acquire a bolt.
    """
    from typehaus.takeoff.uplift_joints import post_base_anchor_rows

    row = post_base_anchor_rows(catlin_model_ro, RULES)[0]
    assert row["part_number"] == "AB-058-10-SS"
    # 2 -> 4 -> 6 -> 4 on 2026-09-10 (the east pair left: PT-BW-RE and PT-BW-RNE became
    # full-height CAST columns, so the two wood columns on them and their bases went), 6 on
    # 2026-09-11 when PT-BW-IC / PT-BW-IE grew from squash blocks into 25 3/4" posts on
    # authored ABU44 standoffs, and 4 again the same day when those two went bearing-only.
    #
    # The population is the union of authored and derived bases, which is why this does not
    # equal the derived rows alone: `CN-BW-BASE-W` / `-NW` (ABU66SS) are authored and each
    # still need their bolt.
    #
    # It stayed 4 on 2026-09-12, when PT-BW-CW / -CNW gained ``within_wall="W-BW-SCREEN"``
    # so the screen panel's plates would be cut around them. That field used to stand this
    # rule down on its own and would have deleted these two bolts; it is now keyed on the
    # JOINT, and a post standing in a stud line on an authored base still buys its part.
    #
    # ** 4 -> 6 ON 2026-09-14, AND IT IS THIS RULE AGREEING WITH A MOVE RATHER THAN DRIFTING. **
    # Both balcony centre pillars came off the porch framing onto the cast column tops
    # (CN-SG-BASE-R2 / -F2, ABU66SS, ``anchored=True``) — see
    # ``test_a_base_on_a_pour_is_bought_its_cast_in_bolt``, which was the test asserting the
    # opposite about these same two posts while they stood on a deck. A base that bears on
    # concrete and says it is anchored buys its bolt; nothing about the rule changed.
    #
    # 6 -> 7 on 2026-09-15: P-M-STRWELL-SS, the third stairwell post, on the same slab.
    #
    # 7 -> 5 in 2026-09: the centre pillars and their anchored CN-SG-BASE-R2 / -F2 retired.
    #
    # 5 -> 4 on 2026-09-24: P-M-STRWELL-N retired once the landings reached the north wall.
    assert row["count"] == 4
    # The population is the union of DERIVED and AUTHORED bases, stated as that sum rather
    # than as one number, because the two halves move independently: the derived rows are the
    # 2 ABU44 ladder rungs, and the authored-and-anchored-on-concrete half is 2 — the
    # canopy's CN-BW-BASE-W / -NW. (The other two
    # authored bases, CN-BW-IBASE-C / -E, are on concrete and ``anchored=False``, so they are
    # in neither half; that is the interesting case above.)
    derived = sum(r["count"] for r in post_base_rows(catlin_model_ro, RULES))
    assert derived == 2
    assert row["count"] == derived + 2
    assert "PT-BW-IC" not in row["basis"] and "PT-BW-IE" not in row["basis"], \
        "a bearing-only base must not be billed a cast-in anchor"


def test_a_base_on_a_pour_is_bought_its_cast_in_bolt_and_a_bare_pier_is_not(
        catlin_model_ro) -> None:
    """What decides the bolt is the JOINT, which is why this rule is a derivation.

    It is not a ``StructuralHardware.requires_role`` on the base, because that field is a
    flat property of the PART: it would bill a cast-in bolt wherever the part appears,
    including into decking. The balcony centre pillars proved it from both sides (on the porch
    deck, no bolt; on the cast columns, one each) until they retired in 2026-09. The canopy's
    PT-BW-CW / -CNW are the positive witness now: authored ABU66SS on their 12" piers,
    anchored, one bolt each.

    The four sonotube piers are the same trap from the other side. ``CN-BW-BASE-*`` names
    both members of its joint, so ``tags_covered_by`` returns PR-BW-1..4 as well as the
    posts on them, and a rule that trusted that set bought four bolts for four piers that
    have no base at all.

    And PT-BW-IC / PT-BW-IE are the third side: their bases DO bear on concrete (the garage
    slab) and are authored ``anchored=False``, so the pour is not sufficient either — the
    joint has to claim the bolt as well.
    """
    from typehaus.takeoff.uplift_joints import post_base_anchor_rows

    basis = post_base_anchor_rows(catlin_model_ro, RULES)[0]["basis"]
    for tag in ("PT-BW-CW", "PT-BW-CNW"):
        assert tag in basis, f"{tag} stands on a cast pier and its base is anchored"
    for pier in ("PR-BW-1", "PR-BW-2", "PR-BW-3", "PR-BW-4"):
        assert pier not in basis, f"{pier} is a cast pier, not a based post"
    for bearing_only in ("PT-BW-IC", "PT-BW-IE"):
        assert bearing_only not in basis, f"{bearing_only}'s base is anchored=False"


def test_an_authored_column_cap_stands_down_the_derived_strap(catlin_model_ro):
    """The canopy's two header-on-column joints are made by hand; only the bare ones derive.

    Catlin billed no strap at all between the breezeway's retirement and 2026-09-10. The
    north entry brought the rule back to life, and the population splits, which is what
    makes the guard readable: BM-BW-RW lands on PT-BW-CW / PT-BW-CNW under an authored
    CCQ46SDS2.5 cap and must NOT be strapped again, while BM-BW-LAND-HDR lands on
    PT-BW-IC/IE — the posts that ended the interior cantilever, with nothing authored at their
    tops — and must be (the carriers themselves hang in the header since 2026-09-24). BM-BW-RE is in neither set as of 2026-09-10: it lands on cast concrete, and a
    beam-on-WOOD-post rule has no business there.
    """
    rows = post_beam_strap_rows(catlin_model_ro, RULES)
    assert len(rows) == 1
    assert rows[0]["part_number"] == "KBS1Z"
    assert rows[0]["count"] == 2
    assert "BM-BW-LAND-HDR->PT-BW-IC" in rows[0]["basis"]
    assert "BM-BW-LAND-HDR->PT-BW-IE" in rows[0]["basis"]
    for joint in AUTHORED_POST_BEAM_JOINTS:
        beam, post = sorted(joint)
        assert f"{beam}->{post}" not in rows[0]["basis"], joint
        assert f"{post}->{beam}" not in rows[0]["basis"], joint


def test_a_tie_at_a_beam_s_own_bearing_does_not_stand_down_the_joists_above_it(
        catlin_model_ro, connections) -> None:
    """The authored-connector hand-off is PAIRWISE at a support, not tag-wide (2026-08-29).

    ``CN-BW-TIE-EA`` / ``-EB`` (HETA20Z) hold BM-BW-HOUSE-SEAT down to PT-BW-E UNDER it, and
    ``-GEA`` / ``-GEB`` do the same for BM-BW-GARAGE-SEAT on PT-BW-GE. That says nothing about
    FS-BW-FLOOR's joists bearing on TOP of those beams, and a tag-wide reading would stand the
    derived rule down at both seats — the deck would buy no uplift hardware and
    ``structural.uplift_path_coverage`` would report a break with the hardware for a different
    joint as its reason. (The porch's four beams and their CN-SG-TIE-COL/-FCOL were the first
    witness; they retired, and the porch now hangs on ledgers, 2026-09.)

    The coarse reading is still right one level up: a tie naming the FLOOR is the plan saying
    it owns that deck's uplift (FS-SG-DECK's authored CN-SG-TIE-*), and nothing here changes
    that.
    """
    from typehaus.model.enums import ConnectorKind

    tagged = {e.tag for e in catlin_model_ro.plan.all_elements()
              if getattr(e, "connects", None)
              and getattr(e, "kind", None) is ConnectorKind.HURRICANE_TIE
              and {"BM-BW-HOUSE-SEAT", "PT-BW-E"} <= set(e.connects)}
    assert tagged, "the fixture's beam-to-column tie moved"
    floor = next(f for f in catlin_model_ro.floors if f.tag == "FS-BW-FLOOR")
    seats = {"BM-BW-HOUSE-SEAT", "BM-BW-GARAGE-SEAT"}
    assert [m for m in floor.members if m.category == "joist"]
    tied = [c for c in connections if c.support_tag in seats]
    assert {c.support_tag for c in tied} == seats, \
        "the entry joists bear on both seats and must be tied at each"
    assert {c.assembly_tag for c in tied} == {"FS-BW-FLOOR"}
    assert not [c for c in connections if c.assembly_tag == "FS-SG-DECK"], \
        "FS-SG-DECK's ties are authored against the floor, so none is derived"


# --- rule 4: lateral tie plates -------------------------------------------------------


def test_tie_plates_skip_a_wall_standing_on_concrete(catlin_model_ro) -> None:
    """A plate on concrete is a sill; its MASA anchors already make that connection.

    Without the foundation exclusion this billed 179 plates across 49 walls, 71 of them on
    the main storey and the garage — every one of those a second anchor at a joint the
    mudsill rule had already paid for.
    """
    row = lateral_tie_plate_rows(catlin_model_ro, RULES)[0]
    assert row["part_number"] == "LTP4"
    assert "garage" not in row["by_storey"], \
        "the garage wall stands on an ICF stem — that is a sill, not a floor band"
    assert set(row["by_storey"]) <= {"main", "second", "attic"}
    assert row["count"] == sum(row["by_storey"].values()) > 0


# --- cross-floor strapping (takeoff/anchors.py, extended 2026-08-28) ------------------


def test_the_wall_runs_are_strapped_not_only_the_corners(catlin_model_ro) -> None:
    """Eight corner straps is two per 36 ft facade; the other thirty-two feet had none.

    The corner term is the older rule and it is still right — a four-stud corner is where two
    facades hand off. But a strap only at the corners leaves the middle of every elevation
    carrying the storey above it on rim-board nailing, which is where uplift is largest on a
    4:12 roof. This pins that the run term exists and that the corners survive it.
    """
    from typehaus.takeoff.anchors import coil_strap_rows

    row = coil_strap_rows(catlin_model_ro, CONFIG.wall_ties)[0]
    assert row["part_number"] == "CS16"
    assert row["unit"] == "coil", "strapping is bought by the coil, not the piece"
    assert "8 at stacked framed-exterior corners" in row["basis"]
    assert "64 along the runs between them at 4 ft o.c." in row["basis"]
    # The purchasable count is coils; the straps they are cut into stay in the basis.
    assert row["count"] == row["coils"] == 2
    assert row["length_ft"] > 0


# --- the negative -------------------------------------------------------------------


def test_a_house_with_no_bearing_declarations_reports_nothing(swinburne_model) -> None:
    """Empty list, never a zero-count row.

    A zero-count row prices as free and disappears into the estimate; an absent row is
    reported as unpriced scope and gets looked at. Same contract as
    ``test_member_protection.py::test_untaped_model_reports_nothing``.
    """
    assert uplift_rows(swinburne_model, RULES) == []


def test_the_rules_are_configurable_without_editing_the_derivation(catlin_model_ro,
                                                                   rows) -> None:
    """The per-bearing multiplier is the main cost lever, so it must live in the config.

    Ties are the largest count in this module by an order of magnitude. A schedule that ties
    each member of a lapped pair separately is a real choice a reviewer may want to price,
    and it must not require touching ``uplift.py`` to do it.
    """
    doubled = uplift_rows(catlin_model_ro, UpliftTieRules(ties_per_bearing=2))
    def ties(source):
        # Per-JOINT rows only. The continuous-bearing rule buys the same part off a pitch,
        # so it does not scale with this lever and folding it in would make the assertion
        # measure two rules at once and pass for neither.
        return sum(row["count"] for row in source
                   if row["part_number"] == "H2.5A"
                   and not row["scope"].endswith("continuous bearing"))
    assert ties(doubled) == 2 * ties(rows) > 0

    # And the pitch IS the other lever: halve it and the continuous run doubles its ties.
    def pitched(source):
        return sum(row["count"] for row in source
                   if row["part_number"] == "H2.5A"
                   and row["scope"].endswith("continuous bearing"))
    tighter = uplift_rows(catlin_model_ro, UpliftTieRules(continuous_bearing_pitch_ft=2.0))
    assert pitched(tighter) == 19 and pitched(rows) == 10
