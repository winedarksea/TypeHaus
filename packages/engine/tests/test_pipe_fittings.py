"""``fitting_takeoff``: elbows and wyes counted off geometry, not estimated off a heuristic.

What it replaced said so in its own row labels — "elbow (estimated)", "tee (estimated)":

* an elbow was any interior vertex whose **plan** turn cleared a flat 20°, with a hard-coded
  ``return 90.0`` standing in wherever a leg had no plan direction at all. A vertical stack
  meeting a horizontal branch was therefore *assumed* to be 90°, and a rolled 45° offset in
  the vertical plane was invisible.
* a tee was any pair of runs on one system sharing a vertex within 20 mm, found by comparing
  every run against every other — no direction, no diameters, no invert.

Both are now read off the run's own 3D polyline (``resolve/sweep.py``) and the drainage graph
``drain_tie_ins`` already derives for ``mep.pipe_sizing``.
"""

from __future__ import annotations

import pytest

from typehaus.quantities import inch
from typehaus.resolve.model import ResolvedModel, ResolvedPipeRun
from typehaus.takeoff.plumbing import fitting_takeoff


class _Plan:
    storeys = ()

    def storey_elements(self, _tag):
        return []

    def by_tag(self, _tag):
        return None


def _model(*runs: ResolvedPipeRun) -> ResolvedModel:
    model = ResolvedModel(plan=_Plan())
    model.pipe_runs.extend(runs)
    return model


def _run(tag: str, path, z, diameter_in: float, system: str = "drain") -> ResolvedPipeRun:
    return ResolvedPipeRun(
        uid=tag, tag=tag, storey="basement", system=system, path=list(path),
        diameter_m=inch(diameter_in).meters, z_start_m=z[0], z_end_m=z[-1],
        length_m=1.0, z_m=tuple(z))


def _counts(model) -> dict[str, int]:
    return {row["fitting"]: row["count"] for row in fitting_takeoff(model)}


# --- elbows ------------------------------------------------------------------------------

def test_a_vertical_meeting_a_horizontal_is_a_measured_90_not_an_assumed_one() -> None:
    """The old code returned a hard-coded 90 here because plan geometry said nothing."""
    model = _model(_run("PR-A", [(0, 0), (0, 0), (3, 0)], [2.0, 0.0, 0.0], 4))
    assert _counts(model) == {"elbow-90-4in": 1}


def test_a_pitched_branch_off_a_stack_is_still_the_quarter_bend_it_is_bought_as() -> None:
    """A 1/4 bend into a 2"/ft branch measures 80.5°. That is the fitting, not a made bend."""
    fall = 3.0 * 2.0 * inch(1).meters / 0.3048
    model = _model(_run("PR-A", [(0, 0), (0, 0), (3, 0)], [2.0, 0.0, -fall], 3))
    assert _counts(model) == {"elbow-90-3in": 1}


def test_a_branch_dropping_far_steeper_than_stock_is_named_a_bend() -> None:
    model = _model(_run("PR-A", [(0, 0), (0, 0), (2, 0)], [2.0, 0.0, -1.2], 2))
    assert _counts(model) == {"bend-2in": 1}


def test_a_plan_offset_snaps_to_the_eighth_bend() -> None:
    model = _model(_run("PR-A", [(0, 0), (2, 0), (3, 1)], [0.0, 0.0, 0.0], 2, "vent"))
    assert _counts(model) == {"elbow-45-2in": 1}


def test_a_sixteenth_bend_is_its_own_row() -> None:
    import math

    model = _model(_run("PR-A", [(0, 0), (2, 0), (2 + math.cos(math.radians(22.5)),
                                                  math.sin(math.radians(22.5)))],
                        [0.0, 0.0, 0.0], 0.75, "water_cold"))
    assert _counts(model) == {"elbow-22.5-0.75in": 1}


def test_a_grade_change_is_not_a_fitting() -> None:
    """Two lengths glued straight at a slightly different pitch buy nothing."""
    model = _model(_run("PR-A", [(0, 0), (3, 0), (6, 0)], [0.0, -0.02, -0.05], 3))
    assert _counts(model) == {}


def test_a_straight_run_buys_nothing() -> None:
    assert _counts(_model(_run("PR-A", [(0, 0), (5, 0)], [0.0, -0.05], 3))) == {}


def test_a_run_with_no_inverts_is_skipped_rather_than_guessed() -> None:
    run = ResolvedPipeRun(uid="PR-A", tag="PR-A", storey="basement", system="drain",
                          path=[(0, 0), (2, 0), (2, 2)], diameter_m=inch(3).meters,
                          z_start_m=None, z_end_m=None, length_m=1.0, z_m=None)
    assert _counts(_model(run)) == {}


# --- wyes --------------------------------------------------------------------------------

def test_a_wye_carries_both_diameters_and_is_filed_on_the_receiving_main() -> None:
    """The old estimate keyed on ``max(diameter)`` and could not name the branch at all."""
    main = _run("PR-MAIN", [(0, 0), (10, 0)], [0.0, -0.08], 4)
    branch = _run("PR-BR", [(5, 3), (5, 0)], [0.02, -0.03], 2)
    counts = _counts(_model(main, branch))
    assert counts["wye-4x2in"] == 1


def test_a_branch_arriving_below_the_main_is_not_a_tie_in() -> None:
    """It would not flow, so there is no fitting there — the same test the rollup makes."""
    main = _run("PR-MAIN", [(0, 0), (10, 0)], [0.0, -0.08], 4)
    branch = _run("PR-BR", [(5, 3), (5, 0)], [0.0, -0.5], 2)
    assert "wye-4x2in" not in _counts(_model(main, branch))


def test_supply_tees_are_absent_rather_than_guessed() -> None:
    """No parent inference exists for a pressurised system; their cost is in [pipe_runs]."""
    a = _run("PR-A", [(0, 0), (10, 0)], [0.0, 0.0], 0.75, "water_cold")
    b = _run("PR-B", [(5, 0), (5, 3)], [0.0, 0.0], 0.5, "water_cold")
    assert not [key for key in _counts(_model(a, b)) if key.startswith("wye")]


# --- the reference house -----------------------------------------------------------------

def test_catlin_bills_the_fittings_its_drains_actually_turn_through(catlin_model) -> None:
    rows = fitting_takeoff(catlin_model)
    assert rows
    counts = {(row["system"], row["fitting"]): row["count"] for row in rows}
    # The 4" main collects the three stacks and the two slab branches.
    assert counts[("drain", "wye-4x2in")] >= 4
    assert counts[("drain", "elbow-90-4in")] >= 1
    # Every row names the runs it came off, so a reader can find the fitting in the plan.
    assert all(row["tags"] for row in rows)
    # Stock parts dominate; a house full of "bend" rows would mean the snap window is wrong.
    stock = sum(row["count"] for row in rows if not row["fitting"].startswith("bend"))
    made = sum(row["count"] for row in rows if row["fitting"].startswith("bend"))
    assert stock > 8 * made


def test_the_fitting_rows_are_priced_by_the_piece(catlin_model) -> None:
    """``pipe_fittings`` joins prices.toml on the fitting key and the count (ESTIMATE_PLANS)."""
    from typehaus.cli.prices import ESTIMATE_PLANS

    plan = next(p for p in ESTIMATE_PLANS if p[0] == "pipe_fittings")
    assert plan == ("pipe_fittings", "pipe_fittings", "fitting", "count", "ea")
    for row in fitting_takeoff(catlin_model):
        assert isinstance(row["fitting"], str) and isinstance(row["count"], int)


def test_the_catlin_estimate_does_not_double_bill_a_fitting(catlin_model) -> None:
    """The [pipe_runs] drain/vent rates were re-based to BARE PIPE when this table arrived.

    Restoring the old "includes a share of fittings" adder there would charge for every elbow
    twice, which is the one thing the re-base must not be undone into. Pinned as the *rate*
    rather than as a subtotal so it names the number that would have to change.
    """
    from _helpers import CATLIN

    from typehaus.cli.prices import load_prices

    prices = load_prices(CATLIN)
    assert prices is not None
    assert prices.pipe_fittings, "the fittings table has to be there for the re-base to hold"
    assert prices.pipe_runs["drain"].material.high == pytest.approx(2.6), (
        "bare 4\" PVC DWV at retail; the 4.5 it used to be carried the fitting adder")
    assert prices.pipe_runs["vent"].material.high == pytest.approx(2.0)
