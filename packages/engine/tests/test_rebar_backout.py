"""The rebar back-out's oracle — ``houses/catlin/notes/rebar_backout.md``, pinned.

Reinforcing steel used to ride invisibly inside the ``[concrete]`` and ``[wall_structure]``
$/cy rates: roughly five tons of it, worth $10,000-18,000, and the standing condition that
those rates be cut the day it became a line of its own was written down in three places and
enforced in none.

It is enforced now, and this module pins the two halves of that:

* :func:`test_the_billed_tonnage_reproduces_the_note` — §1's schedule, term by term.
* :func:`test_the_backout_gate_is_still_CLOSED` — **the important one.** The plan's
  acceptance condition is that the billed subtotal must land inside the register's
  $10,000-18,000 before any rate is cut. It lands at less than half, because the model does
  not yet carry the basement walls' horizontal steel, the garage ICF stems' bar size, or the
  deck cap's schedule. This test asserts the gate is CLOSED and is expected to fail the day
  that changes — which is the point. When it does, read §5 of the note and cut the rates.

Uses catlin's real ``prices.toml``; there is precedent for house-specific price tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.takeoff.reinforcement import reinforcement_takeoff

_CATLIN = Path(__file__).resolve().parents[3] / "houses" / "catlin"

#: §1 of the note. Weight in lb, keyed (scope, bar, coating).
_SCHEDULE = {
    ("column", "#3", ""): 27.8,
    ("column", "#3", "hdg-a767"): 42.8,
    ("column", "#5", ""): 121.0,
    ("column", "#5", "hdg-a767"): 183.7,
    ("footing", "#4", "hdg-a767"): 201.9,
    ("footing", "#6", "hdg-a767"): 1634.2,
    ("foundation wall", "#4", "hdg-a767"): 588.8,
    ("foundation wall", "#5", "hdg-a767"): 216.9,
    ("foundation wall", "#6", "hdg-a767"): 1153.5,
}
_TOTAL_LB = 4170.6

#: §3. The allowance register's figure, and the black-bar material price bracketing it.
_REGISTER_LOW, _REGISTER_HIGH = 10_000.0, 18_000.0
_BLACK_BAR_LOW, _BLACK_BAR_HIGH = 1.05, 1.35


@pytest.fixture(scope="module")
def rows(catlin_model):
    return reinforcement_takeoff(catlin_model)


def test_the_billed_tonnage_reproduces_the_note(rows) -> None:
    """§1, row for row. A total that happens to match while two rows are wrong is not a
    reconciliation, which is why the schedule is pinned and not just its sum."""
    got = {(r["scope"], r["bar"], r["coating"]): r["weight_lb"] for r in rows}
    assert set(got) == set(_SCHEDULE), (
        f"the schedule changed shape: extra {sorted(set(got) - set(_SCHEDULE))}, "
        f"missing {sorted(set(_SCHEDULE) - set(got))}. Update notes/rebar_backout.md §1.")
    for key, want in _SCHEDULE.items():
        assert got[key] == pytest.approx(want, rel=0.002), key
    assert sum(got.values()) == pytest.approx(_TOTAL_LB, rel=0.002)


def test_the_backout_gate_is_still_CLOSED(rows) -> None:
    """**This test is expected to fail one day, and that is what it is for.**

    The rate cut is authorised only when the billed steel's material value lands inside the
    allowance register's $10,000-18,000. It does not: the model carries 2.09 of roughly 5
    tons, because the basement walls' horizontal steel is authored nowhere, `GARAGE_ICF_6`
    states a spacing with no bar size, and `SL-M-DECK`'s cap schedule cannot be derived from
    a form whose rib spacing the model does not carry.

    Cutting the full embedded rebar out of the $/cy rates while billing 42% of it would make
    the estimate FALL by about $6,000 and read as a saving. So the gate stays shut, and this
    asserts that it is shut for the reason the note gives rather than by accident.

    When this fails: re-run §3 of `notes/rebar_backout.md`, and if the number is now inside
    the band, follow §5 and cut the rates.
    """
    total_lb = sum(r["weight_lb"] for r in rows)
    low = total_lb * _BLACK_BAR_LOW
    high = total_lb * _BLACK_BAR_HIGH
    assert high < _REGISTER_LOW, (
        f"THE BACK-OUT GATE HAS OPENED: {total_lb:,.0f} lb is ${low:,.0f}-{high:,.0f}, which "
        f"now reaches the register's ${_REGISTER_LOW:,.0f}-{_REGISTER_HIGH:,.0f}. This is "
        f"good news, not a regression — read notes/rebar_backout.md §5 and cut the "
        f"[concrete]/[wall_structure] rates, then delete this assertion.")


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

    pour_categories = {"footing", "slab", "pad", "column"}
    concrete_cy = sum(
        row["volume_cubic_yards"] for row in structural_solids_takeoff(catlin_model)
        if row["category"] in pour_categories and row["structure_material"] == "concrete")
    walls_cy = sum(row["volume_cubic_yards"] for row in wall_structure_takeoff(catlin_model)
                   if row.get("material") == "concrete")
    total_cy = concrete_cy + walls_cy
    assert total_cy == pytest.approx(147.81, rel=0.02), (
        f"the concrete volume moved to {total_cy:.2f} cy; notes/rebar_backout.md §2 and the "
        f"lb/cy figure in §3 both need re-working")

    total_lb = sum(r["weight_lb"] for r in reinforcement_takeoff(catlin_model))
    assert total_lb / total_cy == pytest.approx(28.2, rel=0.03)
