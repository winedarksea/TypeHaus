"""The rebar back-out's oracle — ``houses/catlin/notes/rebar_backout.md``, pinned.

Reinforcing steel used to ride invisibly inside the ``[concrete]`` and ``[wall_structure]``
$/cy rates: roughly five tons of it, worth $10,000-18,000, and the standing condition that
those rates be cut the day it became a line of its own was written down in three places and
enforced in none.

It is enforced now, and this module pins the two halves of that:

* :func:`test_the_billed_tonnage_reproduces_the_note` — §1's schedule, term by term.
* :func:`test_the_backout_gate_is_still_CLOSED` — **the important one.** Since 2026-09-17
  the gate is closed BY DECISION (decision #75 D14, note §3): a constant, the empty
  ``[reinforcement]`` table and the inclusive $/cy rates, so authoring more steel cannot open
  it by crossing a dollar line. Opening it is §5's one-commit rate cut.

Uses catlin's real ``prices.toml``; there is precedent for house-specific price tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.takeoff.reinforcement import reinforcement_takeoff

_CATLIN = Path(__file__).resolve().parents[3] / "houses" / "catlin"

#: §1 of the note, as laid out (decision #75, 2026-09-17): (pieces, weight lb), keyed
#: (scope, bar, coating). Cut lengths — placed + laps + hooks — by counted piece. Three of the
#: hosts in these rows are laid out bar for bar in notes/rebar_layout_basis.md and pinned by
#: test_rebar_layout_oracle.py; this pins the house-wide sum they sit inside.
#:
#: Eleven rows, not seven: §4's gaps are authored (basement horizontals, the garage ICF stems,
#: W-SG-BRKBM's cage, SL-M-DECK's BuildDeck schedule, dowels), and the deck cap is the one
#: BLACK pour because DECK_CAP_MIX says so — a new scope, not a second coating in an old one.
_SCHEDULE = {
    ("column", "#3", "hdg-a767"): (144, 176.6),
    ("column", "#5", "hdg-a767"): (88, 632.5),
    ("footing", "#4", "hdg-a767"): (30, 272.1),
    ("footing", "#5", "hdg-a767"): (154, 989.8),
    ("foundation wall", "#3", "hdg-a767"): (49, 78.6),
    ("foundation wall", "#4", "hdg-a767"): (307, 1723.8),
    ("foundation wall", "#5", "hdg-a767"): (139, 1440.4),
    ("foundation wall", "#6", "hdg-a767"): (10, 129.5),
    ("slab", "#3", "black"): (220, 237.3),
    ("slab", "#4", "black"): (43, 576.9),
    ("slab", "#5", "black"): (22, 410.1),
}
# +3,215.6 lb on 2026-09-17 over the area/spacing era's 3,514.7 (newly authored steel, laps and
# hooks out of [waste], the fencepost), then −122.3 the same day after the detailing review:
# the court stems continuous at #5 @ 7", corner/splice bars, one mat per overlap, A767 bends.
# Note §1 works both out row by row. +27.1 lb on 2026-09-20: the two canopy columns' bases
# went to a common -10'-2" plane (notes/entry_column_base_fixity.md §6a), which is 5'-5 9/16"
# more 12" round shaft between them — five more #3 ties and 21 lb on the #5 verticals.
# +32.5 lb the same day, and it is 8 PIECES not a length: `PT-BW-W` and `PT-BW-GW` joined
# `north_entry_frame._MOMENT_PIERS`, so each takes ENTRY_MOMENT_CAGE's base dowel at every
# vertical — four #5 apiece — where it had the plain cage and none. They had carried the
# same base moment as their east twins since `_base_moments` started splitting it over four
# fixed columns; nothing had made them dowel it. (The 12" pads that develop those dowels are
# concrete, not steel, and are 0.073 cy — they move no row here.)
_TOTAL_LB = 6667.6
_TOTAL_PIECES = 1206

#: §3, decision #75 D14. The back-out gate is CLOSED BY DECISION, not by a dollar comparison:
#: authoring steel may lift the tonnage into the register's band without opening it. Opening
#: it is §5's one-commit rate cut, and flipping this constant is part of that commit.
_BACKOUT_GATE_CLOSED_BY_DECISION = True


@pytest.fixture(scope="module")
def rows(catlin_model):
    return reinforcement_takeoff(catlin_model)


def test_the_billed_tonnage_reproduces_the_note(rows) -> None:
    """§1, row for row. A total that happens to match while two rows are wrong is not a
    reconciliation, which is why the schedule is pinned and not just its sum."""
    got = {(r["scope"], r["bar"], r["coating"]): (r["pieces"], r["weight_lb"]) for r in rows}
    assert set(got) == set(_SCHEDULE), (
        f"the schedule changed shape: extra {sorted(set(got) - set(_SCHEDULE))}, "
        f"missing {sorted(set(_SCHEDULE) - set(got))}. Update notes/rebar_backout.md §1.")
    for key, (pieces, weight) in _SCHEDULE.items():
        assert got[key][0] == pieces, key
        assert got[key][1] == pytest.approx(weight, rel=0.002), key
    assert sum(w for _p, w in got.values()) == pytest.approx(_TOTAL_LB, rel=0.002)
    assert sum(p for p, _w in got.values()) == _TOTAL_PIECES


def test_the_backout_gate_is_still_CLOSED(rows) -> None:
    """**Closed by decision (§3, decision #75 D14), and asserted as that.**

    Until 2026-09-17 this compared the billed steel's dollars against the register's
    $10,000-18,000. The layout lifted the tonnage to 6,608 lb ($6,938-8,921), and further
    authoring could lift it into the band — which must not open the gate by itself. So the
    gate is a constant tied to the note, and this test holds the three things that make it
    true: the constant, the empty ``[reinforcement]`` table and the inclusive $/cy rates.

    When the rate cut is taken (§5), flip the constant in the same commit.
    """
    import tomllib

    from typehaus.cli.price_file import load_prices, rebar_is_inclusive

    note = (_CATLIN / "notes" / "rebar_backout.md").read_text()
    assert "## 3. The test, and the gate is CLOSED BY DECISION" in note
    assert _BACKOUT_GATE_CLOSED_BY_DECISION, (
        "the gate is open by decision: the [reinforcement] rates and the "
        "[rebar_inclusive] flip belong in this same commit — see §5")
    data = tomllib.loads((_CATLIN / "prices.toml").read_text())
    assert rebar_is_inclusive(data, "concrete") and rebar_is_inclusive(data, "wall_structure")
    prices = load_prices(_CATLIN)
    assert prices is not None and prices.reinforcement == {}
    assert sum(r["weight_lb"] for r in rows) > 0


def test_the_rates_still_declare_themselves_rebar_inclusive() -> None:
    """The other half of the same invariant, from the price file's side.

    While the gate is shut these two must stay `true` and `[reinforcement]` must stay empty.
    The loader refuses the combination that would double-bill, so this is really asserting
    that nobody has half-done the cut.
    """
    import tomllib

    from typehaus.cli.price_file import load_prices, rebar_is_inclusive

    data = tomllib.loads((_CATLIN / "prices.toml").read_text())
    assert rebar_is_inclusive(data, "concrete")
    assert rebar_is_inclusive(data, "wall_structure")

    prices = load_prices(_CATLIN)
    assert prices is not None and prices.reinforcement == {}, (
        "reinforcement is priced while the $/cy rates still contain their rebar. "
        "load_prices should have refused this; if it did not, the guard is broken.")


def test_the_concrete_the_steel_sits_in_is_the_note_s_volume(catlin_model) -> None:
    """§2 — the denominator of the lb/cy figure §3 turns on.

    Pinned loosely (2%) on purpose: this moves whenever the building moves, and the point is
    that a REBAR RATIO computed against it stays meaningful, not that the volume is frozen.
    """
    from typehaus.takeoff.framing import structural_solids_takeoff
    from typehaus.takeoff.wall_structure import wall_structure_takeoff

    # "beam" is W-SG-ARCH, the cast grade beam; wood beams fall out on structure_material.
    pour_categories = {"footing", "slab", "pad", "column", "beam"}
    concrete_cy = sum(
        row["volume_cubic_yards"] for row in structural_solids_takeoff(catlin_model)
        if row["category"] in pour_categories and row["structure_material"] == "concrete")
    walls_cy = sum(row["volume_cubic_yards"] for row in wall_structure_takeoff(catlin_model)
                   if row.get("material") == "concrete")
    total_cy = concrete_cy + walls_cy
    assert total_cy == pytest.approx(143.58, rel=0.02), (
        f"the concrete volume moved to {total_cy:.2f} cy; notes/rebar_backout.md §2 and the "
        f"lb/cy figure in §3 both need re-working")

    total_lb = sum(r["weight_lb"] for r in reinforcement_takeoff(catlin_model))
    # ** 26.85 -> 25.74 -> 28.0 -> 27.0 -> 31.2, AND 25.74 IS STILL THE INTERESTING ONE. **
    # The north entry put 3.18 cy of concrete in the ground -- thirteen 12" cast piers and
    # their footings -- and at first not one billed pound of steel with it, because those
    # cages were authored as free-text ``vertical_reinforcement`` and carry no structured
    # ``ReinforcementSpec``, which is the only spelling ``reinforcement_takeoff`` can read.
    # This gate is what caught that: the ratio SAGGING is the signal, not the ratio moving.
    # The cages are now authored both ways and the ratio recovers past where it started.
    # It came back to 27.0 later the same day when eight of the thirteen piers were deleted
    # outright and four cast stair tiers (plain, unreinforced) took their place — steel out
    # AND concrete out, which is why the ratio barely moved for a change that removed about
    # a third of the north entry's pour.
    #
    # Keep both spellings on every new cast column. A drawing string nobody bills and a
    # takeoff row nobody draws are the two halves of the same mistake.
    #
    # 27.0 -> 31.6 on 2026-09-10, and that one was a DESIGN change rather than a bookkeeping
    # one: FT-SG-W1/E1 gained the retaining set's mat, because their 3'-0" PLAIN heel is
    # 2.35x over and nothing in the engine was grading it. +680 lb of #6 and #4 against
    # +1.2 cy. **A ratio RISING on a reinforcement finding is the right direction** — the
    # sag at 25.74 was steel that existed and was not billed; that was steel that did not
    # exist and now does.
    #
    # ** THEN 31.6 -> 23.8, LATER THE SAME DAY, AND THIS SAG IS NOT THE 25.74 KIND. **
    # The court shortened 28'-0" -> 26'-0" and all five strips narrowed 96" -> 84", and the
    # mat came down with them, #6 @ 10" -> #5 @ 12". -1,313 lb against only -5.05 cy, so the
    # ratio falls hard: a bar-size cut removes steel and NO concrete at all, which is the
    # one move that can drop this figure without anything being hidden from it. The sag at
    # 25.74 was steel the takeoff could not SEE; this is steel that is not there, because
    # sunken_garden_court_free_body.md §7e re-ran the toe at its new length and found the
    # bigger bar was carrying 43% of unused capacity.
    #
    # ** 23.8 lb/cy IS LOW AND §3 SAYS SO. ** A lightly reinforced residential foundation
    # runs 40-80. The gap is still the unauthored steel §3 lists, not this cut — but the cut
    # has eaten into the margin this figure had, and a further DESIGN reduction in steel is
    # now the thing to look at twice.
    #
    # ** 24.5 -> 46.9 ON 2026-09-17, AND THIS RISE IS THE GAP CLOSING. ** Laid out (decision
    # #75), with §4's steel authored: +2,899.9 lb of steel that existed and was stated
    # nowhere, laps and hooks out of [waste], the fencepost. No concrete moved. 46.9 is inside
    # the 40-80 a lightly reinforced residential foundation runs. 46.0 after the same day's
    # detailing review (note §1): the stems continuous at #5 @ 7", one mat per overlap.
    assert total_lb / total_cy == pytest.approx(45.98, rel=0.03)
