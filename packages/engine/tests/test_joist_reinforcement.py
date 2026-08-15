"""Sistered joist plies + solid blocking under a concentrated load (WP1).

``PT-SG-BR2`` — the one balcony pillar that misses the masonry railing — bears on the
*cantilevered* north tip of the porch deck, i.e. on the free end of a single PT 2x8. The
answer is a ``JoistReinforcement`` on the FloorSystem: the resolver sisters the nearest
joist line up to the authored ply count and blocks it out to the lines either side.

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


# --- the catlin porch, end to end -----------------------------------------------------
def test_the_porch_deck_resolves_the_cluster_under_its_cantilevered_pillar(catlin_model):
    floor = next(f for f in catlin_model.floors if f.tag == "FS-SG-PORCH")
    post = catlin_model.plan.by_tag("PT-SG-BR2")
    post_x, _post_y = post.position.xy_m
    sisters = [m for m in floor.members if m.category == "sister_joist"]
    blocks = [m for m in floor.members if m.category == "blocking"]
    assert len(sisters) == 2 and len(blocks) == 2
    # Arm (a) of the check contract: sisters within half a joist spacing of the post.
    assert all(abs(m.p0[0] - post_x) < SPACING_M / 2 for m in sisters)
    # Arm (b): blocking within 0.3 m of it.
    assert all(abs(m.p0[1] - _post_y) < 0.3 for m in blocks)


def test_the_sisters_carry_the_cantilever_they_were_added_for(catlin_model):
    """Full joist length: the 7'-3" back span (arch-wall axis to the back-beam line)
    plus the 17" north overhang the post stands on."""
    floor = next(f for f in catlin_model.floors if f.tag == "FS-SG-PORCH")
    joists = [m for m in floor.members if m.category == "joist"]
    sisters = [m for m in floor.members if m.category == "sister_joist"]
    field_lo = min(min(m.p0[1], m.p1[1]) for m in joists)
    field_hi = max(max(m.p0[1], m.p1[1]) for m in joists)
    expected = ft(7, 3).meters + inch(17).meters
    assert all(m.length_m == pytest.approx(expected) for m in sisters)
    assert all(m.length_m == pytest.approx(field_hi - field_lo) for m in sisters)
    # The single-span joists on that line are each shorter than the sister doubling them.
    assert max(m.length_m for m in joists) < expected


def test_the_cluster_bills_itself(catlin_model):
    """No new take-off wiring: ``framing_takeoff`` groups by (profile, category)."""
    rows = {(row["profile"], row["category"]): row for row in framing_takeoff(catlin_model)}
    sisters = rows[("2x8", "sister_joist")]
    assert sisters["pieces"] == 2
    assert sisters["board_feet"] > 0 and sisters["order_length_ft"] > 0
    blocks = rows[("2x8", "blocking")]
    assert blocks["pieces"] == 2
