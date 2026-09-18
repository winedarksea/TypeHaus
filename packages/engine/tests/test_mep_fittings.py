"""The fitting catalog, and the one reading the take-off, the check and the router share.

Phase 5 of the routing roadmap. Three things are pinned here and each has a failure mode
worth naming:

* **the catalog holds patterns, not guesses** — every row cites a standard, and every
  dimensional field that no submittal in this repo publishes is ``None`` rather than a
  plausible number;
* **the take-off rows did not move** — ``prices.toml`` is keyed on them and a house's price
  list is the house's, so a shared reading that re-keyed the rows would have silently
  unpriced the plumbing;
* **what a turn is billed as and what part it is are two answers** — ``elbow-22.5-1in`` is a
  priced row for a fitting ASME B16.22 does not make, and merging the two would bury that.
"""

from __future__ import annotations

import math

import pytest

from typehaus.hardware.fittings import (
    KIND_ELBOW,
    KIND_WYE,
    SERVICE_DRAIN,
    SERVICE_DUCT,
    SERVICE_SUPPLY,
    catalogued_angles,
    fitting_catalog,
    fitting_for,
)
from typehaus.quantities import inch
from typehaus.resolve.mep_fittings import (
    FAMILY_DUCT,
    FAMILY_PIPE,
    MIN_DWV_SIZE_IN,
    fitting_records,
    order_key,
    polyline_fittings,
    takeoff_rows,
)
from typehaus.resolve.model import ResolvedModel, ResolvedPipeRun


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


# --- the catalog -------------------------------------------------------------------------

def test_every_catalogued_pattern_cites_a_standard() -> None:
    """A row without a source is a number somebody reasoned to, which is the one thing the
    hardware catalog's rules forbid."""
    unsourced = [item.tag for item in fitting_catalog() if not item.source]
    assert unsourced == []


def test_no_laying_length_is_invented() -> None:
    """Every ``center_to_face_in`` is ``None`` and says why.

    This is the field that would let ``resolve/sweep.py`` draw a fitting body instead of a
    mitre, and it is deliberately empty: no manufacturer submittal has been read into this
    repo. If this test starts failing because somebody filled one in, the accompanying
    change must cite the submittal — not a retailer listing.
    """
    for item in fitting_catalog():
        if item.center_to_face_in is None:
            assert item.data_note, f"{item.tag} is undimensioned and does not say why"
        else:
            assert item.source, f"{item.tag} carries a laying length with no source"


def test_a_gored_duct_elbow_carries_the_radius_its_standard_defines() -> None:
    """The one dimensional field that is not ``None``, and it is a construction standard
    rather than one maker's submittal: SMACNA draws a round gored elbow at R = 1.5 D."""
    elbow = fitting_for(SERVICE_DUCT, KIND_ELBOW, 90.0, 6.0)
    assert elbow is not None
    assert elbow.bend_radius_in == pytest.approx(9.0)


def test_there_is_no_22_point_5_degree_copper_elbow() -> None:
    """B16.22 makes 90 and 45. A shallow turn in tube is a bend, not a part."""
    assert catalogued_angles(SERVICE_SUPPLY, KIND_ELBOW) == (45.0, 90.0)
    assert fitting_for(SERVICE_SUPPLY, KIND_ELBOW, 22.5, 1.0) is None


def test_a_pitched_line_may_widen_the_snap_and_a_pressure_line_may_not() -> None:
    """The same 80.5 degree turn: an elbow at the foot of a 2 in/ft fall, or nothing."""
    assert fitting_for(SERVICE_SUPPLY, KIND_ELBOW, 80.5, 0.75) is None
    assert fitting_for(SERVICE_SUPPLY, KIND_ELBOW, 80.5, 0.75, snap_bonus_deg=5.0) is not None


def test_the_dwv_catalog_starts_at_the_smallest_size_the_patterns_are_made_in() -> None:
    assert fitting_for(SERVICE_DRAIN, KIND_ELBOW, 90.0, MIN_DWV_SIZE_IN) is not None
    assert fitting_for(SERVICE_DRAIN, KIND_ELBOW, 90.0, 0.75) is None


# --- the shared reading ------------------------------------------------------------------

def test_a_three_quarter_inch_gravity_line_is_graded_as_TUBE_not_as_DWV() -> None:
    """A condensate drain is copper and turns on a copper elbow.

    Grading it against D3311 reported the absence of a part nobody would have ordered —
    six findings on catlin, every one of them the engine's own category error.
    """
    model = _model(_run("PR-COND", [(0, 0), (0, 0), (3, 0)], [2.0, 0.0, 0.0], 0.75))
    record = fitting_records(model)[0]
    assert record.service == SERVICE_SUPPLY
    assert record.spec is not None and record.spec.tag.startswith("FIT-CU-")


def test_a_turn_no_pattern_makes_is_reported_with_the_angles_that_are_made() -> None:
    """The refusal is an instruction: a reader is told what the catalog does hold."""
    # A vertical drop into a leg falling at 15 degrees: a 75 degree turn, which is 15 off
    # the 1/4 bend and 15 off the 1/6 — the gap between two patterns, not near either.
    drop = 3.0 * math.tan(math.radians(15.0))
    model = _model(_run("PR-A", [(0, 0), (0, 0), (3, 0)], [2.0, 0.0, -drop], 3))
    record = fitting_records(model)[0]
    assert record.spec is None
    assert "the catalogued patterns are" in (record.gap or "")
    assert "22.5, 45, 60, 90" in (record.gap or "")


def test_the_order_key_and_the_catalog_answer_are_allowed_to_disagree() -> None:
    """A 32 degree turn in 1" copper bills as ``elbow-22.5-1in`` and is no such part.

    The take-off row is what ``prices.toml`` joins and the catalog is what a supplier
    stocks; keeping them separate is what makes the disagreement visible instead of
    resolving it by fiat in one direction or the other.
    """
    model = _model(_run("PR-A", [(0, 0), (3, 0), (6, 1.874)], [0.0, 0.0, 0.0], 1.0,
                        system="water_cold"))
    record = fitting_records(model)[0]
    assert record.order_key == "elbow-22.5-1in"
    assert record.spec is None
    assert "BENT TUBE" in (record.gap or "")


def test_a_rectangular_duct_elbow_names_no_pattern_and_says_why() -> None:
    records = polyline_fittings("DU-A", FAMILY_DUCT, "supply",
                                [(0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (2.0, 2.0, 0.0)],
                                inch(10).meters, rectangular=True)
    assert len(records) == 1
    assert records[0].spec is None
    assert "shop drawing" in (records[0].gap or "")


def test_a_grade_change_is_not_a_fitting() -> None:
    """Two lengths glued straight with the pipe flexing: below the threshold, no part."""
    model = _model(_run("PR-A", [(0, 0), (3, 0), (6, 0)], [0.0, -0.05, -0.20], 3))
    assert fitting_records(model) == []


# --- the take-off rows -------------------------------------------------------------------

def test_the_rows_keep_the_keys_prices_toml_is_joined_on() -> None:
    model = _model(_run("PR-A", [(0, 0), (0, 0), (3, 0)], [2.0, 0.0, 0.0], 4))
    rows = takeoff_rows(fitting_records(model))
    assert rows[0]["system"] == "drain"
    assert rows[0]["fitting"] == "elbow-90-4in"
    assert rows[0]["count"] == 1
    assert rows[0]["tags"] == ["PR-A"]


def test_a_row_is_only_a_part_when_every_turn_on_it_is_that_part() -> None:
    """One matched and one unmatched turn at the same order key: the row names no part.

    The conservative reading, and the one an estimator needs — a line item that says "1/4
    bend" for a pair of turns only one of which is one would be ordered wrong.
    """
    def bent(tag: str, degrees: float):
        angle = math.radians(degrees)
        return _run(tag, [(0, 0), (1, 0), (1 + math.cos(angle), math.sin(angle))],
                    [0.0, 0.0, 0.0], 1.0, system="water_cold")

    # Both bill as ``elbow-45-1in`` — the order key's snap is 10 degrees — and only one is
    # a B16.22 part, whose snap is 5 because a pressure line carries no pitch.
    rows = takeoff_rows(fitting_records(_model(bent("PR-A", 45.0), bent("PR-B", 39.0))))
    row = next(r for r in rows if r["fitting"] == "elbow-45-1in")
    assert row["count"] == 2
    assert row["catalog"] is None
    assert row["ungraded"] == 1


def test_order_key_is_the_take_offs_own_spelling_and_rounds_a_made_bend() -> None:
    assert order_key(90.0, inch(3).meters) == "elbow-90-3in"
    assert order_key(71.4, inch(2).meters) == "bend-70-2in"


# --- what a proposal says about its own corners ------------------------------------------

def test_a_proposed_lane_names_the_parts_its_corners_would_take() -> None:
    """The router grades a lane with the derivation that will bill it once pasted."""
    from typehaus.routing.proposal import RouteProposal

    proposal = RouteProposal(
        tag="PR-X", kind="pipe", system="drain", diameter_m=inch(3).meters,
        points=[(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0)])
    records = proposal.fittings()
    assert len(records) == 1
    assert records[0].family == FAMILY_PIPE
    assert records[0].spec is not None
    assert proposal.fitting_lines() == []


def test_a_proposal_whose_corner_is_unmakeable_says_so_without_explain() -> None:
    from typehaus.routing.proposal import RouteProposal

    proposal = RouteProposal(
        tag="PR-X", kind="pipe", system="drain", diameter_m=inch(3).meters,
        # 75 degrees in plan: between the 1/6 bend and the 1/4, and neither reaches it.
        points=[(0.0, 0.0, 0.0), (1.0, 0.0, 0.0),
                (1.0 + math.cos(math.radians(75.0)), math.sin(math.radians(75.0)), 0.0)])
    lines = proposal.fitting_lines()
    assert lines and "no stock drain elbow turns" in lines[0]
    assert any(entry["gap"] for entry in proposal.as_dict()["fittings"])


def test_a_wye_names_both_diameters_or_says_which_branch_is_missing() -> None:
    assert fitting_for(SERVICE_DRAIN, KIND_WYE, 45.0, 3.0, branch_in=2.0) is not None
    assert fitting_for(SERVICE_DRAIN, KIND_WYE, 45.0, 2.0, branch_in=0.75) is None
