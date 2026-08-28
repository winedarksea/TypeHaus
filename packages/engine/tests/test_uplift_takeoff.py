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
    post_base_rows,
    post_beam_strap_rows,
    uplift_rows,
)

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

    ``resolve/framing/roof.py::_bearing_stiffeners`` emits exactly one stiffener per I-joist
    rafter, at ``rafter.p0``, for the express purpose of making the eave bearing countable.
    It is derived by a different rule, from a different field, in a different module — so it
    is an independent witness that this count is the number of bearings and not the number of
    something adjacent to them.
    """
    roof = next(roof for roof in catlin_model_ro.roofs if roof.tag == "RF-HOUSE")
    rafters = [m for m in roof.members if m.category == "rafter"]
    stiffeners = [m for m in roof.members if m.category == "bearing_stiffener"]
    assert len(rafters) == len(stiffeners) > 0

    tied = [c for c in connections if c.member_category == "rafter"]
    assert len(tied) == len(rafters)
    # The ridge end is HUNG on RB-HOUSE and billed an LSSR by hangers.py, so only the three
    # attic side walls appear here — never the ridge beam.
    assert {c.support_tag for c in tied} == {"W-A-W1", "W-A-E1", "W-A-E2"}


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
    """A hardware count is only auditable if the row carries the rule that produced it."""
    ties = [row for row in rows if row["part_number"] == "H2.5A"]
    assert ties
    for row in ties:
        assert row["count"] > 0
        assert "per bearing joint" in row["basis"]
        assert row["by_storey"] and sum(row["by_storey"].values()) == row["count"]


# --- the double-billing guard ---------------------------------------------------------


def test_authored_post_bases_are_not_derived_a_second_time(catlin_model_ro) -> None:
    """Ten posts already carry a hand-authored ABU66SS; none may be bought twice."""
    from typehaus.model.enums import ConnectorKind
    from typehaus.model.structure import Post
    from typehaus.takeoff.uplift import tags_covered_by

    authored = tags_covered_by(catlin_model_ro, frozenset({ConnectorKind.POST_BASE}))
    assert authored >= AUTHORED_POST_BASES, "the fixture's authored bases moved"
    assert post_base_rows(catlin_model_ro, RULES) == [], (
        "every wood post that declares a bearing is already authored a base — a row here "
        "means the Connector.connects guard stopped matching")
    # And the ten really are all of them, so the empty list above is coverage, not silence.
    wood = {e.tag for e in catlin_model_ro.plan.all_elements()
            if isinstance(e, Post) and e.supported_by and not e.within_wall
            and e.size in {"6x6", "4x4"}}
    assert wood == AUTHORED_POST_BASES


def test_authored_post_beam_straps_are_not_derived_a_second_time(catlin_model_ro) -> None:
    row = post_beam_strap_rows(catlin_model_ro, RULES)[0]
    for beam in AUTHORED_POST_BEAM_STRAPS:
        assert beam not in row["basis"], f"{beam} is authored a KBS1Z and was derived again"
    # What is left is the sunken garden, which authors none (three balcony beams and four
    # girts, each landing on two of the six pillars = 14), plus the breezeway's two FLOOR
    # beams on four posts (4) — those share their posts with the strapped roof beams, which
    # is exactly why the guard has to key on the tag PAIR and not on the post alone.
    assert row["count"] == 18
    assert row["part_number"] == "KBS1Z"


def test_a_floor_system_named_by_an_authored_tie_is_left_alone(catlin_model_ro,
                                                               connections) -> None:
    """``CN-SG-TIE-BR2`` names ``FS-SG-PORCH``, so the plan owns that floor's uplift."""
    porch = next(f for f in catlin_model_ro.floors if f.tag == "FS-SG-PORCH")
    porch_supports = {"BM-SG-FRW", "BM-SG-FRE", "BM-SG-BKW", "BM-SG-BKE"}
    assert [m for m in porch.members if m.category == "joist"]
    assert not [c for c in connections if c.support_tag in porch_supports]


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
        return sum(row["count"] for row in source if row["part_number"] == "H2.5A")
    assert ties(doubled) == 2 * ties(rows) > 0
