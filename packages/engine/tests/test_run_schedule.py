"""``takeoff/runs.py`` — the per-run routing schedule, and the price join it shares.

The engine has no router (``model/mep.py`` says so). What it lacked as well was any way to
*score* an authored route, so a run that wandered was indistinguishable from one that could
not do better. These tests pin the four lengths a row reports, the two traps that make the
numbers wrong if they are computed naively, and the single price lookup the schedule shares
with the estimate.
"""

from __future__ import annotations

import math

import pytest

from typehaus.cli.prices import rate_for
from typehaus.quantities import M_PER_IN
from typehaus.takeoff.runs import MIN_STRAIGHT_FT, conduit_schedule, run_schedule

_M_TO_FT = 3.280839895013123


@pytest.fixture(scope="module")
def rows(catlin_model):
    return run_schedule(catlin_model)


@pytest.fixture(scope="module")
def catlin_prices(catlin_model):
    from typehaus.cli.prices import load_prices

    return load_prices(catlin_model.plan.source_root)


@pytest.fixture(scope="module")
def by_tag(rows):
    return {row["tag"]: row for row in rows}


def test_every_resolved_run_gets_exactly_one_row(catlin_model, rows):
    """Pipe, duct and conduit in one schedule — the reader's question is "which run", and
    which of the three families it belongs to is a column, not a separate report."""
    expected = (len(catlin_model.pipe_runs) + len(catlin_model.ducts)
                + len(catlin_model.conduits))
    assert len(rows) == expected
    assert {row["tag"] for row in rows} == {
        *(run.tag for run in catlin_model.pipe_runs),
        *(duct.tag for duct in catlin_model.ducts),
        *(run.tag for run in catlin_model.conduits)}
    assert {row["kind"] for row in rows} == {"pipe", "duct", "conduit"}


def test_developed_length_is_the_resolvers_own_number(catlin_model, by_tag):
    """Not recomputed here. ``length_m`` is what the BOM bills, and a schedule that
    measured the same polyline a second time would eventually disagree with the bill."""
    for run in catlin_model.pipe_runs:
        assert by_tag[run.tag]["developed_ft"] == pytest.approx(
            run.length_m * _M_TO_FT, abs=0.02)
    for duct in catlin_model.ducts:
        assert by_tag[duct.tag]["developed_ft"] == pytest.approx(
            duct.length_m * _M_TO_FT, abs=0.02)


def test_plan_plus_rise_accounts_for_the_developed_length(rows):
    """A run's developed length is bounded by its plan run and its rise: never less than
    either, never more than their sum. This is what lets a reader diagnose a long number as
    "it wanders" (plan-heavy) or "it climbs" (rise-heavy) rather than just "it is long"."""
    for row in rows:
        dev, plan, rise = row["developed_ft"], row["plan_ft"], row["rise_ft"]
        assert dev >= max(plan, rise) - 0.02, row["tag"]
        assert dev <= plan + rise + 0.02, row["tag"]


def test_straight_is_three_dimensional_so_a_riser_is_not_an_offender(catlin_model, by_tag):
    """**The conduit trap.** ``ResolvedConduitRun`` carries a plan polyline and two END
    elevations, and the rise happens at the run's LAST point — so a chase riser is 1'-6" of
    plan and 24'-6" of climb. Grade it against the plan hypotenuse and it scores 5 to 8, and
    every riser in the house reads as a routing offender. Grade it against the 3D distance
    between its endpoints, which is what the run actually is, and it scores about 1.1.

    ``CD-B-ATTIC-RISER``, ``CD-B-DATA-CHASE`` and ``CD-B-SPARE-CHASE`` are the three."""
    risers = [run for run in catlin_model.conduits
              if run.z_start_m is not None and run.z_end_m is not None
              and abs(run.z_end_m - run.z_start_m) > 3 * math.dist(run.path[0], run.path[-1])]
    assert len(risers) >= 3, "no riser-dominant conduit left to pin this against"
    for run in risers:
        row = by_tag[run.tag]
        plan_only = math.dist(run.path[0], run.path[-1]) * _M_TO_FT
        assert row["developed_ft"] / plan_only > 4.0, run.tag  # what plan-grading would say
        assert row["straight_ft"] == pytest.approx(
            math.hypot(math.dist(run.path[0], run.path[-1]),
                       run.z_end_m - run.z_start_m) * _M_TO_FT, abs=0.02)
        assert row["ratio"] < 1.3, run.tag


def test_a_stub_is_ungraded_rather_than_scored(rows):
    """Two vertices nine inches apart make any ratio at all, and the run that produced them
    is not the one to go and shorten. Reported as None, which prints as an em dash — an
    admitted absence, never a zero that reads as "perfectly routed"."""
    short = [row for row in rows if row["straight_ft"] < MIN_STRAIGHT_FT]
    assert short, "no sub-foot run left to pin this against"
    assert all(row["ratio"] is None for row in short)
    assert all(row["ratio"] is not None for row in rows
               if row["straight_ft"] >= MIN_STRAIGHT_FT)


def test_worst_detour_sorts_first_and_ungraded_rows_sort_last(rows):
    graded = [row for row in rows if row["ratio"] is not None]
    assert graded == sorted(graded, key=lambda row: -row["ratio"])
    assert rows[:len(graded)] == graded


def test_elbow_count_matches_the_fitting_takeoffs_own_walk(catlin_model, by_tag):
    """Reused, not restated: ``takeoff/mep.py::duct_fitting_takeoff`` counts the same turns
    to bill the same elbows. If the two ever disagreed, the schedule would be telling a
    reader to remove a bend the BOM never charged for."""
    from typehaus.takeoff.mep import duct_fitting_takeoff

    billed: dict[str, int] = {}
    for row in duct_fitting_takeoff(catlin_model):
        for tag in row["tags"]:
            billed[tag] = billed.get(tag, 0) + 1
    # Per-tag totals, not per-row: the BOM groups by fitting size and a run with two
    # different elbow sizes appears in two rows.
    for duct in catlin_model.ducts:
        if by_tag[duct.tag]["elbows"]:
            assert duct.tag in billed, duct.tag


def test_ratio_ranking_reproduces_the_run_the_hand_analysis_named(by_tag):
    """Validation with a known answer. ``DU-A-ERV-R-BED3``'s 56.2 LF / 2.32 was derived by
    hand before this module existed, and it is the figure ``houses/catlin/CLAUDE.md``
    adjudicated that run's route on. Nothing has touched it since; if this moves, either the
    ratio arithmetic changed or somebody re-opened a decision that was closed on the merits."""
    assert by_tag["DU-A-ERV-R-BED3"]["ratio"] == pytest.approx(2.32, abs=0.03)
    assert by_tag["DU-A-ERV-R-BED3"]["developed_ft"] == pytest.approx(56.2, abs=0.2)


def test_the_reroute_is_visible_in_the_schedule(by_tag):
    """``CD-A-DATA-NE`` is what this module was built to make arguable, and it has now been
    rerouted twice — which is the point worth pinning, because the SECOND reroute is the one
    the schedule could not have told you to make.

    It scored 57.08 LF at ratio 2.26 as a 66-foot dogleg south across the studio and back.
    The 2026-08-29 pass took it through the north gable's stud cavity: 29.58 LF at 1.17, very
    nearly the straight line between its two ends, and by every number in this schedule the
    right answer. It also put the raceway through ``WIN-A-N2``'s rough opening at +23'-3", in
    the same band ``DU-ERV-EA`` was crossing both gable windows in. **A good ratio is not a
    buildable route**, and nothing here grades one; ``mep.run_through_opening`` does.

    On 2026-08-30 it went south down the pocket instead, to an AP wall-mounted on
    ``W-A-STU-N`` — 19.0 LF at 1.46. Shorter than either predecessor and a WORSE ratio than
    the route it replaced, which is exactly why this test asserts both numbers: if someone
    optimises the ratio back down, they are on their way to the gable again."""
    assert by_tag["CD-A-DATA-NE"]["developed_ft"] == pytest.approx(19.0, abs=0.2)
    assert by_tag["CD-A-DATA-NE"]["ratio"] == pytest.approx(1.46, abs=0.03)


# --- the shared price join -----------------------------------------------------------------

def test_duct_rows_price_through_the_material_qualified_key(catlin_model, catlin_prices):
    """``[ducts]`` keys on ``system`` and is qualified by ``material``
    (``prices.QUALIFIED_KEY_FIELD``). A second, hand-rolled ``table.get(system)`` would
    price every 3" semi-rigid radial at the sheet-metal rate — which is the drift
    :func:`rate_for` exists to prevent, so the schedule must resolve the qualified key."""
    priced = run_schedule(catlin_model, catlin_prices)
    semi_rigid = [row for row in priced
                  if row["kind"] == "duct" and ":semi_rigid" in str(row.get("price_key"))]
    assert semi_rigid, "catlin's radials are semi_rigid; the qualifier did not resolve"
    for row in semi_rigid:
        key, rate = rate_for(catlin_prices, "ducts", row["system"], "semi_rigid")
        assert key == row["price_key"]
        assert row["cost_low"] == pytest.approx(
            rate.times(row["developed_ft"]).low, abs=0.02)


def test_an_unpriced_run_says_so_instead_of_costing_nothing(catlin_model, catlin_prices):
    """The estimate's discipline, kept here: a rate that is missing produces ``None``, never
    ``$0``. A zero would sum into a total and read as a free run."""
    priced = run_schedule(catlin_model, catlin_prices)
    for row in priced:
        assert ("cost_low" in row) and ("price_key" in row)
        if row["cost_low"] is None:
            assert row["cost_high"] is None
        else:
            assert row["cost_high"] >= row["cost_low"]


def test_without_prices_the_schedule_carries_lengths_and_no_dollars(rows):
    """Dollars are opt-in (decision #28). A house with no ``prices.toml`` still gets every
    length and every ratio — the routing report does not depend on the money."""
    assert all("cost_low" not in row for row in rows)
    assert all(row["developed_ft"] >= 0 for row in rows)


# --- conduit_schedule ----------------------------------------------------------------------

def test_conduit_schedule_covers_power_and_comms_together(catlin_model):
    """``conduit_takeoff`` bills power, ``data_raceway_takeoff`` bills comms, and each
    deliberately skips the other's runs so no foot of pipe is ordered twice. Neither can
    answer "what is in this raceway and where does it go" — this can, for every run."""
    schedule = conduit_schedule(catlin_model)
    assert {row["tag"] for row in schedule} == {run.tag for run in catlin_model.conduits}
    assert {row["service"] for row in schedule} >= {"data"}
    for row, run in zip(schedule,
                        sorted(catlin_model.conduits, key=lambda item: item.tag),
                        strict=True):
        assert row["length_ft"] == pytest.approx(run.length_m * _M_TO_FT, abs=0.05)
        assert row["trade_size_in"] == pytest.approx(run.trade_size_m / M_PER_IN, abs=0.01)
