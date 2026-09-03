"""Sistered joist plies + solid blocking under a concentrated load (WP1).

The feature: a ``JoistReinforcement`` on a FloorSystem makes the resolver sister the joist
line nearest an authored load point up to the ply count and block it out to the lines either
side.

It was built for a cantilevered balcony pillar bearing on the free end of a single joist —
a condition catlin no longer has. **No house drives the SISTERING half of it**: every
reinforcement the reference house authors is ``plies=1``, which lays blocks and no sisters,
because what those joints need is a bearing or roll block rather than a stiffened joist. The
synthetic fixtures below are the whole coverage for the plies; the two catlin tests at the
bottom pin what the house does author, and that every station of it actually lands.

These lock the three things the geometry has to get right, because each one is a way the
reinforcement can look present and do nothing:

* the plies land on the joist line *nearest the load* and on the side the load is on,
* they run the joist's whole length **including the cantilever** — a sister stopping at the
  support carries nothing where the post actually stands, and
* the blocks sit at the load, cut to the clear gap between member faces (not centre to
  centre, which would read as a clash and bill long).

The categories are also a published contract — ``structural.cantilever_point_load`` reads
``"sister_joist"`` / ``"blocking"`` as its mitigation arms — so they are asserted verbatim.
"""

from __future__ import annotations


import pytest

from typehaus.model.floors import FloorSystem, JoistReinforcement, JoistSpec
from typehaus.quantities import ft, inch, pt
from typehaus.resolve.floors import _reinforcement_members
from typehaus.resolve.framing.profiles import cross_section
from typehaus.takeoff.framing import framing_takeoff


PLY_WIDTH_M = cross_section("2x8").width_m  # 1.5"
SPACING_M = inch(16).meters


def _system(at, **kwargs):
    """A FloorSystem carrying one reinforcement at ``at``; joists run in y."""
    return FloorSystem(
        uid="FS00000001", tag="FS-T", joists=JoistSpec(member="2x8", spacing=inch(16),
                                                       direction="y"),
        reinforcements=(JoistReinforcement(at=at, **kwargs),),
    )


def _lines(count: int) -> list[float]:
    return [index * SPACING_M for index in range(count)]


# --- the plies ------------------------------------------------------------------------
def test_the_plies_double_the_nearest_line_and_run_the_whole_joist() -> None:
    """plies=3 means the authored joist plus *two* sisters, full length."""
    system = _system(pt(inch(18), ft(4)), plies=3)  # 18" — 2" past the 16" line
    members = _reinforcement_members(system, system.joists, _lines(4), False,
                                     axis_lo=0.0, axis_hi=6.0, z0=-0.2, z1=0.0)
    sisters = [m for m in members if m.category == "sister_joist"]
    assert len(sisters) == 2
    assert all(m.profile == "2x8" for m in sisters)
    assert all(m.p0[1] == 0.0 and m.p1[1] == 6.0 for m in sisters), "not the full joist"
    assert all(m.length_m == pytest.approx(6.0) for m in sisters)
    assert all((m.z0_m, m.z1_m) == (-0.2, 0.0) for m in sisters)


def test_the_plies_sit_face_to_face_on_the_side_the_load_is_on() -> None:
    """Face to face, toward the load — so the finished cluster brackets the post.

    Stacked at one offset they would be byte-identical members (the trimmer-pair defect);
    laid away from the load the post would overhang its own reinforcement.
    """
    line = SPACING_M
    system = _system(pt(inch(18), ft(4)), plies=3)
    members = _reinforcement_members(system, system.joists, _lines(4), False,
                                     0.0, 6.0, -0.2, 0.0)
    xs = sorted(m.p0[0] for m in members if m.category == "sister_joist")
    assert xs == pytest.approx([line + PLY_WIDTH_M, line + 2 * PLY_WIDTH_M])
    assert xs[0] > line, "plies went away from the load"


def test_a_load_below_the_line_puts_the_plies_on_that_side() -> None:
    system = _system(pt(inch(14), ft(4)), plies=3)  # 2" *short* of the 16" line
    members = _reinforcement_members(system, system.joists, _lines(4), False,
                                     0.0, 6.0, -0.2, 0.0)
    xs = sorted(m.p0[0] for m in members if m.category == "sister_joist")
    assert xs == pytest.approx([SPACING_M - 2 * PLY_WIDTH_M, SPACING_M - PLY_WIDTH_M])


def test_the_nearest_line_wins_not_the_first_one() -> None:
    system = _system(pt(inch(30), ft(4)), plies=2)  # nearest the 32" line
    members = _reinforcement_members(system, system.joists, _lines(4), False,
                                     0.0, 6.0, -0.2, 0.0)
    sister = next(m for m in members if m.category == "sister_joist")
    assert sister.p0[0] == pytest.approx(2 * SPACING_M - PLY_WIDTH_M)


def test_joists_running_in_x_reinforce_across_the_other_axis() -> None:
    system = FloorSystem(
        uid="FS00000002", tag="FS-TX",
        joists=JoistSpec(member="2x8", spacing=inch(16), direction="x"),
        reinforcements=(JoistReinforcement(at=pt(ft(4), inch(18)), plies=3),),
    )
    members = _reinforcement_members(system, system.joists, _lines(4), True,
                                     0.0, 6.0, -0.2, 0.0)
    sisters = [m for m in members if m.category == "sister_joist"]
    assert all(m.p0[0] == 0.0 and m.p1[0] == 6.0 for m in sisters)
    assert sorted(m.p0[1] for m in sisters) == pytest.approx(
        [SPACING_M + PLY_WIDTH_M, SPACING_M + 2 * PLY_WIDTH_M])
    blocks = [m for m in members if m.category == "blocking"]
    assert all(m.p0[0] == m.p1[0] for m in blocks), "blocking must run across the joists"


# --- the blocking ---------------------------------------------------------------------
def test_blocking_runs_to_the_lines_either_side_cut_to_the_clear_gap() -> None:
    system = _system(pt(inch(18), ft(4)), plies=3)
    members = _reinforcement_members(system, system.joists, _lines(4), False,
                                     0.0, 6.0, -0.2, 0.0)
    blocks = sorted((m for m in members if m.category == "blocking"), key=lambda m: m.p0[0])
    assert len(blocks) == 2
    # 16" o.c. less the cluster's 3 plies and the neighbour's half ply on the load side;
    # the plain 14.5" clear block on the other.
    assert blocks[0].length_m == pytest.approx(SPACING_M - PLY_WIDTH_M)
    assert blocks[1].length_m == pytest.approx(SPACING_M - 3 * PLY_WIDTH_M)
    assert all(m.length_m > 0 for m in blocks)


def test_blocking_sits_at_the_load_not_at_a_bearing_line() -> None:
    """``structural.cantilever_point_load`` looks for blocking within 0.3 m of the post."""
    system = _system(pt(inch(18), ft(4)), plies=3)
    members = _reinforcement_members(system, system.joists, _lines(4), False,
                                     0.0, 6.0, -0.2, 0.0)
    blocks = [m for m in members if m.category == "blocking"]
    assert all(abs(m.p0[1] - ft(4).meters) < 0.3 for m in blocks)


def test_blocking_is_held_inside_the_joist_tips_so_it_clears_the_rim() -> None:
    system = _system(pt(inch(18), ft(20)), plies=3)  # load out past the axis extent
    members = _reinforcement_members(system, system.joists, _lines(4), False,
                                     0.0, 6.0, -0.2, 0.0)
    blocks = [m for m in members if m.category == "blocking"]
    assert all(m.p0[1] == pytest.approx(6.0 - PLY_WIDTH_M) for m in blocks)


def test_blocking_false_emits_plies_only() -> None:
    system = _system(pt(inch(18), ft(4)), plies=3, blocking=False)
    members = _reinforcement_members(system, system.joists, _lines(4), False,
                                     0.0, 6.0, -0.2, 0.0)
    assert {m.category for m in members} == {"sister_joist"}


def test_a_cluster_on_the_field_edge_blocks_only_where_there_is_a_neighbour() -> None:
    system = _system(pt(inch(0), ft(4)), plies=3)
    members = _reinforcement_members(system, system.joists, _lines(4), False,
                                     0.0, 6.0, -0.2, 0.0)
    assert len([m for m in members if m.category == "blocking"]) == 1


def test_one_ply_is_a_no_op_for_the_plies_but_still_blocks() -> None:
    system = _system(pt(inch(18), ft(4)), plies=1)
    members = _reinforcement_members(system, system.joists, _lines(4), False,
                                     0.0, 6.0, -0.2, 0.0)
    assert not [m for m in members if m.category == "sister_joist"]
    assert len([m for m in members if m.category == "blocking"]) == 2


def test_the_member_override_wins_over_the_deck_joist() -> None:
    system = _system(pt(inch(18), ft(4)), plies=3, member="2x10")
    members = _reinforcement_members(system, system.joists, _lines(4), False,
                                     0.0, 6.0, -0.2, 0.0)
    assert {m.profile for m in members} == {"2x10"}


def test_a_deck_with_no_reinforcement_emits_nothing() -> None:
    system = FloorSystem(uid="FS00000003", tag="FS-T0",
                         joists=JoistSpec(member="2x8", direction="y"))
    assert _reinforcement_members(system, system.joists, _lines(4), False,
                                  0.0, 6.0, -0.2, 0.0) == []


# --- the catlin decks, end to end -----------------------------------------------------
def test_no_catlin_deck_sisters_a_joist(catlin_model):
    """No deck in this house stiffens a joist.

    Every DECK reinforcement in this house is ``plies=1`` — a fastener host for the
    heat-pump anchors (see below), not a stiffened joist — and a stray ``plies=3`` would
    quietly add sixteen sisters and their lumber to the BOM. That is what this catches.

    ** ONE SISTER EXISTS, AND IT IS NOT ON A DECK. ** ``FS-M-WEST`` carries a single
    full-span ply under RM-M-BATH2's drop-in bath, which is the built half of
    plans/TODO.md's 60 psf item. It is an INTERIOR floor answering a real concentrated load,
    which is the case ``JoistReinforcement`` was written for; the decks are still the case
    this test was written for. Pinning the count at one keeps both readings true — a second
    sister appearing here means somebody raised a deck's ``plies`` without meaning to.
    """
    decks = {"FS-SG-PORCH", "FS-SG-DECK", "SL-BW-DECK"}
    sisters = []
    for floor in catlin_model.floors:
        found = [m for m in floor.members if m.category == "sister_joist"]
        assert floor.tag not in decks or found == [], floor.tag
        sisters.extend((floor.tag, m) for m in found)
    assert [tag for tag, _ in sisters] == ["FS-M-WEST"]
    # Full span, tip to tip: a sister that stops short carries nothing where the load is
    # (``resolve/floors.py::_reinforcement_members``). 17.9' and not the 18'-0" bearing grid
    # — the joist it doubles stops 1 1/4" inboard of the foundation's framing face, behind
    # the rim board, and the sister is cut to the joist rather than to the grid line
    # (``resolve/floor_ends.py``).
    assert round(sisters[0][1].length_m / 0.3048, 2) == 17.9
    rows = {(row["profile"], row["category"]) for row in framing_takeoff(catlin_model)}
    assert [key for key in rows if key[1] == "sister_joist"] == [
        ("11.875 I-joist", "sister_joist")]


def test_both_garden_decks_block_only_where_something_is_bolted_down(catlin_model):
    """Every block on these two decks answers a named joint, and nothing else does.

    ``FS-SG-DECK`` hosted sixteen sacrificial blocks under two heat-pump stands until
    2026-09-02, when both units moved to a ground pad east of the porch
    (``houses/catlin/notes/heat_pump_ground_pad.md``) and the stands, the blocking and the
    eight through-deck anchors went with them. It carries FOUR now, one under each of
    RL-SG-BALCONY's south-leg guard posts: that guard stays fascia-mounted precisely
    because this plank is the porch roof and carries no penetrations, and a fascia bracket
    through-bolts the rim, which then needs something behind it so it cannot roll under
    R301.5's 200 lb at 42". **The west and east legs get none** — the joists run E-W, so
    those legs stand over the joist TIPS and bolt into the joists themselves.

    ``FS-SG-PORCH`` carries TEN: a pair under each centre balcony pillar (PT-SG-BR2, and
    PT-SG-BF2 since it came north off PT-SG-FCOL's top on 2026-09-03), and a pair under
    each of RL-SG-PORCH's three south-leg guard posts, which is the one leg of that guard
    with no concrete wall top under it.

    ``plies=1`` throughout, so nothing is sistered — what these joints need is a bearing and
    roll block, not a stiffened joist.
    """
    by_tag = {floor.tag: floor for floor in catlin_model.floors}
    deck_blocks = [m for m in by_tag["FS-SG-DECK"].members if m.category == "blocking"]
    assert len(deck_blocks) == 4, len(deck_blocks)
    porch_blocks = [m for m in by_tag["FS-SG-PORCH"].members if m.category == "blocking"]
    assert len(porch_blocks) == 10, len(porch_blocks)
    for tag in ("FS-SG-DECK", "FS-SG-PORCH"):
        assert [m for m in by_tag[tag].members
                if m.category == "sister_joist"] == [], "plies=1 must sister nothing"


def test_a_guard_block_authored_on_the_deck_edge_would_be_dropped(catlin_model):
    """The trap ``_GUARD_BLOCK_INSET_FT`` exists for, pinned so nobody removes the inset.

    A guard's ``path`` is the deck EDGE. A ``JoistReinforcement`` authored exactly there
    falls outside the joist field the resolver lays blocks in and is silently dropped — the
    model would show a guard with backing at some posts and none at others, at 0 FAIL. Every
    authored station must therefore sit strictly inside the joist field's own extent.
    """
    deck = next(f for f in catlin_model.floors if f.tag == "FS-SG-DECK")
    joists = [m for m in deck.members if m.category == "joist"]
    ys = [p[1] for m in joists for p in (m.p0, m.p1)]
    authored = [e for e in catlin_model.plan.all_elements()
                if getattr(e, "tag", "") == "FS-SG-DECK"][0].reinforcements
    assert authored
    for reinforcement in authored:
        assert min(ys) < reinforcement.at.xy_m[1] < max(ys), reinforcement.at.xy_m
