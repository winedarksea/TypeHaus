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
def test_no_deck_sisters_a_joist_and_one_floor_does(catlin_model):
    """Which decks stiffen a joist — and, since 2026-09-14, that none of them does.

    ** THE PORCH WAS THE ONE EXCEPTION, AND IT HAS GONE BACK. ** Until 2026-09-03 this test
    asserted that no deck in the house sistered anything: every deck reinforcement was
    ``plies=1``, a fastener host rather than a stiffened joist. That stopped being true when
    ``engineering/post_bearing.py`` computed what the two centre balcony pillars did to the
    joist they stood on — through one 1-1/2" ply, ``BM-SG-BLC``'s reactions bore at 311 and
    380 psi against a WET Fc-perp of 285, and no block fixes bearing. Two sisters took it to
    107 and 131 psi, and ``FS-SG-PORCH`` carried a 3-ply pack for eleven days.

    On 2026-09-14 both pillars came off this deck and onto the cast column tops (PT-SG-BF2 on
    PT-SG-FCOL, PT-SG-BR2 on PT-SG-COL), with the four porch beams hung off their faces on
    HU212-3 hangers rather than seated beside them on the pour. **A pillar that does not bear
    on a deck poses no cross-grain question**, which is exactly why the two ``post_bearing``
    records left the engineering register — so the packs went with them, kept as
    ``_DECK_BORNE_PILLAR_REINFORCEMENTS`` in ``params/sunken_garden.py``.

    So the original assertion is restored, for the original reason and with one more deck in
    it: **no deck in this house sisters a joist**, and a stray ``plies=3`` on any of them
    would quietly add sisters and their lumber to the BOM.

    ** AND ONE MORE, NOT ON A DECK AT ALL. ** ``FS-M-WEST`` carries a single full-span ply
    under RM-M-BATH2's drop-in bath, the built half of plans/TODO.md's 60 psf item. It is the
    only sister left in the house, which is what the exact list below says.
    """
    unsistered = {"FS-SG-DECK", "FS-SG-PORCH", "SL-BW-DECK"}
    sisters = []
    for floor in catlin_model.floors:
        found = [m for m in floor.members if m.category == "sister_joist"]
        assert floor.tag not in unsistered or found == [], floor.tag
        sisters.extend((floor.tag, m) for m in found)
    assert sorted(tag for tag, _ in sisters) == ["FS-M-WEST"]
    # Full span, tip to tip: a sister that stops short carries nothing where the load is
    # (``resolve/floors.py::_reinforcement_members``). 17.9' and not the 18'-0" bearing grid
    # — the joist it doubles stops 1 1/4" inboard of the foundation's framing face, behind
    # the rim board, and the sister is cut to the joist rather than to the grid line
    # (``resolve/floor_ends.py``).
    full_span = next(m for tag, m in sisters if tag == "FS-M-WEST")
    assert round(full_span.length_m / 0.3048, 2) == 17.9
    # And the BOM follows: the 2x8 sister rows the porch pack bought are gone with it, and
    # the I-joist ply under the bath is the only sistered stock this house orders.
    rows = {(row["profile"], row["category"]) for row in framing_takeoff(catlin_model)}
    assert sorted(key for key in rows if key[1] == "sister_joist") == [
        ("11.875 I-joist", "sister_joist")]


def test_both_garden_decks_block_only_where_something_is_bolted_down(catlin_model):
    """Every block on these two decks answers a named joint, and nothing else does.

    ``FS-SG-DECK`` carries TWENTY-THREE, and they answer two different joints.

    THREE are structural: one under each of RL-SG-BALCONY's south-leg guard posts (19'-6"
    of front edge at <= 60" o.c. is four bays, three interior posts; the 21'-6" deck before
    the 17'-0" court had four). That guard stays fascia-mounted because this plank is the
    porch roof and carries no penetrations, and a fascia bracket through-bolts the rim,
    which then needs something behind it so it cannot roll under R301.5's 200 lb at 42".
    **The west and east legs get none** — the joists run E-W, so those legs stand over the
    joist TIPS and bolt into the joists themselves.

    TWENTY answer an **envelope** joint. The porch enclosure's two flank tracks run N-S at
    x = 10'-0"/26'-0", PERPENDICULAR to these joists, so the curtain plane crosses every bay
    (``houses/catlin/notes/porch_enclosure.md``). Five entries per flank — the front track's
    spare joist at -9'-0" and every second line north of it (-7'-6" .. -1'-6"), since one
    entry blocks the bay on EACH side of its line — for ten blocks a flank. Authoring every
    line would put two blocks in every bay, a real ``structural.member_interference`` FAIL.

    ``FS-SG-PORCH`` carries THREE: one 2" inside the south edge joist under each of
    RL-SG-PORCH's three south-leg guard posts (17'-0" at <= 60" o.c.), the balcony's inset
    pattern, since the porch joists run E-W with that leg too. (The centre pillars' packs,
    and the station they collapsed into a guard post, retired with the centre line, 2026-09.)

    Every entry on both decks is ``plies=1``: blocks and plies answer different limit
    states — rollover and cross-grain bearing — and nothing in this house has the second one
    (see ``test_no_catlin_deck_sisters_a_joist``). A stray ``plies=3`` anywhere here would
    silently sister a joist and buy its lumber; the assertion below is what catches it.
    """
    by_tag = {floor.tag: floor for floor in catlin_model.floors}
    deck_blocks = [m for m in by_tag["FS-SG-DECK"].members if m.category == "blocking"]
    assert len(deck_blocks) == 23, len(deck_blocks)
    porch_blocks = [m for m in by_tag["FS-SG-PORCH"].members if m.category == "blocking"]
    assert len(porch_blocks) == 3, len(porch_blocks)
    for tag in ("FS-SG-DECK", "FS-SG-PORCH"):
        assert [m for m in by_tag[tag].members
                if m.category == "sister_joist"] == [], f"plies=1 must sister nothing ({tag})"


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
