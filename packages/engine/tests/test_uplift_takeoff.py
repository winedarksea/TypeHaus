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

from typehaus.takeoff.hardware_config import DEFAULT_HARDWARE_TAKEOFF_CONFIG as CONFIG
from typehaus.takeoff.hardware_config import UpliftTieRules
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
AUTHORED_POST_BASES = {
    "PT-SG-BR1", "PT-SG-BF1", "PT-SG-BR2", "PT-SG-BF2", "PT-SG-BR3", "PT-SG-BF3",
    "PT-BW-1", "PT-BW-2", "PT-BW-3", "PT-BW-4",
}

#: The four breezeway roof-beam-to-post joints already strapped with a KBS1Z by hand.
AUTHORED_POST_BEAM_STRAPS = {"BM-BW-RW", "BM-BW-RE"}


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


def test_a_truss_roof_is_tied_at_its_heels_not_its_top_chords(catlin_model_ro,
                                                              connections) -> None:
    """The garage bears on its heels; its top chords cross the plate a foot and a half up.

    This is the whole reason ``tied_roof_categories`` names two member categories rather than
    one. A rule that tied ``top_chord`` would find the garage's chords passing over W-G-S on
    their way to the 16" overhang and tie them at the wrong elevation, or — with a tight
    tolerance — miss the garage roof entirely.
    """
    roof = next(roof for roof in catlin_model_ro.roofs if roof.tag == "RF-GARAGE")
    heels = [m for m in roof.members if m.category == "truss_heel"]
    tied = [c for c in connections if c.member_category == "truss_heel"]
    assert len(tied) == len(heels) > 0
    assert {c.support_tag for c in tied} == {"W-G-S", "W-G-N"}
    assert not [c for c in connections if c.member_category == "top_chord"]


def test_a_floor_is_tied_along_its_whole_bearing_line(catlin_model_ro,
                                                      connections) -> None:
    """``FS-S-WEST`` names one wall of a line the resolver split into six.

    Its ``joists.bearing_refs`` is ``('W-M-W2', 'W-M-C2', 'BM-M-HALL')``, but its 28 floor
    trusses land across the whole west line. Billing only the named segment tied four of the
    twenty-eight and reported the order complete — which is what ``_bearing_line`` exists to
    prevent, and this test is what would catch its removal.
    """
    floor = next(f for f in catlin_model_ro.floors if f.tag == "FS-S-WEST")
    joists = [m for m in floor.members if m.category == "joist"]
    trussed = [c for c in connections if c.member_profile == "11.875 floor truss"]
    assert len(trussed) == len(joists) == 28
    assert len({c.support_tag for c in trussed}) > 1, \
        "the west bearing line is more than one wall; a single support means _bearing_line died"


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
    """Ten posts already carry a hand-authored ABU66SS; none may be bought twice.

    Until 2026-08-28 this asserted an EMPTY list, because every 6x6 that declared a bearing
    was authored and the three 4x4s declared none. The stairwell posts now declare theirs
    (``SL-B-FLOOR``), so the rule derives its first real row — and the guard it is here to
    protect is now visible rather than vacuous: the derived row must be the 4x4 ladder rung
    only, and no authored tag may appear in its basis.
    """
    from typehaus.model.enums import ConnectorKind
    from typehaus.model.structure import Post
    from typehaus.takeoff.uplift_joints import tags_covered_by

    authored = tags_covered_by(catlin_model_ro, frozenset({ConnectorKind.POST_BASE}))
    assert authored >= AUTHORED_POST_BASES, "the fixture's authored bases moved"
    rows = post_base_rows(catlin_model_ro, RULES)
    assert [row["part_number"] for row in rows] == ["ABU44"], (
        "an ABU66SS row means the Connector.connects guard stopped matching and the ten "
        "authored bases are being bought a second time")
    assert rows[0]["count"] == 2
    for tag in AUTHORED_POST_BASES:
        assert tag not in rows[0]["basis"]
    # And the twelve really are all of them, so what is NOT in the row above is coverage
    # rather than silence: ten authored, two derived, one squash block.
    wood = {e.tag for e in catlin_model_ro.plan.all_elements()
            if isinstance(e, Post) and e.supported_by and not e.within_wall
            and e.size in {"6x6", "4x4"}}
    assert wood == AUTHORED_POST_BASES | {"P-M-STRWELL-S", "P-M-STRWELL-N",
                                          "P-M-STRLAND-SE"}


def test_a_squash_block_is_not_bought_a_post_base(catlin_model_ro) -> None:
    """P-M-STRLAND-SE is 13 7/16" of blocking in a joist bay, not a column.

    It declares a bearing (``W-B-CN``) and its section is one the catalog stocks a base for,
    so nothing but ``blocking_max_height_ft`` keeps it out of the order — and a base under a
    block is hardware at a joint whose connection is the bearing itself.
    """
    from typehaus.model.structure import Post
    from typehaus.takeoff.uplift_joints import is_squash_block

    posts = {e.tag: e for e in catlin_model_ro.plan.all_elements() if isinstance(e, Post)}
    assert is_squash_block(posts["P-M-STRLAND-SE"], RULES)
    assert not is_squash_block(posts["P-M-STRWELL-S"], RULES), \
        "a 9 ft stairwell post is a column; only the 13 in block is blocking"
    row = post_base_rows(catlin_model_ro, RULES)[0]
    assert "P-M-STRLAND-SE" not in row["basis"]


# --- rule 2b: the bolt under every base ----------------------------------------------


def test_every_post_base_on_concrete_is_bought_its_anchor(catlin_model_ro) -> None:
    """Simpson ship the ABU without the 5/8" bolt its published capacity is taken through.

    Eleven of catlin's twelve bases land on concrete — four breezeway piers, four
    sunken-garden wall tops, two on the basement slab, and since 2026-08-29 PT-SG-BF2 on
    PT-SG-FCOL's top — and each needs one cast-in anchor. Only PT-SG-BR2 is left standing on
    framing.
    """
    from typehaus.takeoff.uplift_joints import post_base_anchor_rows

    row = post_base_anchor_rows(catlin_model_ro, RULES)[0]
    assert row["part_number"] == "AB-058-10-SS"
    assert row["count"] == 11


def test_a_base_standing_on_framing_is_not_bought_a_cast_in_bolt(catlin_model_ro) -> None:
    """PT-SG-BR2 stands on FS-SG-PORCH — a deck, not a pour.

    This is the reason the rule is a derivation over joints and not a
    ``StructuralHardware.requires_role`` on the base: that field is a flat property of the
    PART, so it would bill a cast-in bolt into porch decking. A base on framing is bolted or
    screwed to it, and those fixings are inside the framing rate.

    The four sonotube piers are the same trap from the other side. ``CN-BW-BASE-*`` names
    both members of its joint, so ``tags_covered_by`` returns PR-BW-1..4 as well as the
    posts on them, and a rule that trusted that set bought four bolts for four piers that
    have no base at all.
    """
    from typehaus.takeoff.uplift_joints import post_base_anchor_rows

    basis = post_base_anchor_rows(catlin_model_ro, RULES)[0]["basis"]
    assert "PT-SG-BR2" not in basis, "PT-SG-BR2 stands on the porch deck"
    # Its opposite number left this test on 2026-08-29: PT-SG-BF2 bears on PT-SG-FCOL, a
    # cast column, so it DOES want the cast-in bolt and is counted above.
    assert "PT-SG-BF2" in basis, "PT-SG-BF2 bears on a cast column"
    for pier in ("PR-BW-1", "PR-BW-2", "PR-BW-3", "PR-BW-4"):
        assert pier not in basis, f"{pier} is a cast pier, not a based post"


def test_authored_post_beam_straps_are_not_derived_a_second_time(catlin_model_ro) -> None:
    row = post_beam_strap_rows(catlin_model_ro, RULES)[0]
    for beam in AUTHORED_POST_BEAM_STRAPS:
        assert beam not in row["basis"], f"{beam} is authored a KBS1Z and was derived again"
    # What is left is the sunken garden, which authors none (three balcony beams, each
    # landing on two of the six pillars = 6 — the two E-W brace rails that used to add
    # eight more of these dropped out 2026-08-30: they carry ``bearing_refs=()``, since the
    # "collision" at the centre posts was a bookkeeping fiction and not real beam-on-post
    # bearing), plus the breezeway's two FLOOR beams on four posts (4) — those share their
    # posts with the strapped roof beams, which is exactly why the guard has to key on the
    # tag PAIR and not on the post alone.
    assert row["count"] == 10
    assert row["part_number"] == "KBS1Z"


def test_a_tie_at_a_beam_s_own_bearing_does_not_stand_down_the_joists_above_it(
        catlin_model_ro, connections) -> None:
    """The authored-connector hand-off is PAIRWISE at a support, not tag-wide (2026-08-29).

    ``CN-SG-TIE-COL`` and ``CN-SG-TIE-FCOL`` hold the porch's four beams down to the two cast
    columns UNDER them. That says nothing about the 32 joists bearing on top, and until this
    was fixed a tag-wide reading stood the derived rule down at all four supports — so the
    porch bought no uplift hardware at all and ``structural.uplift_load_path`` reported a
    break in the load path with the hardware for a different joint as its reason. It was
    latent only because the front pair was flush-framed and ``hangers.py`` billed those ends.

    The coarse reading is still right one level up: a tie naming the FLOOR is the plan saying
    it owns that deck's uplift, and nothing here changes that.
    """
    porch = next(f for f in catlin_model_ro.floors if f.tag == "FS-SG-PORCH")
    porch_supports = {"BM-SG-FRW", "BM-SG-FRE", "BM-SG-BKW", "BM-SG-BKE"}
    assert [m for m in porch.members if m.category == "joist"]
    tied = [c for c in connections if c.support_tag in porch_supports]
    assert tied, "the porch joists bear on their beams and must be tied"
    assert {c.assembly_tag for c in tied} == {"FS-SG-PORCH"}


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
