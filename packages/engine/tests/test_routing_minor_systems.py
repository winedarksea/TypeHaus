"""Condensate, radon and sump routes (houses/catlin/notes/mep_condensate_routing_basis.md).

Hand-worked oracle values from the note: PR-B-COND's y=108 leg falls 1.170" over 54" from
z -20.276" at x=216", so an indirect line landing at x=210" lands at -20.406" (§3).
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from typehaus.cli.route_cleanouts import place_cleanouts
from typehaus.cli.route_roots import _landing, sleeve_hold, sump_endpoints
from typehaus.quantities import inch
from typehaus.routing.campaign import order_targets
from typehaus.routing.gravity import CONDENSATE_SLOPE_IN_PER_FT, minimum_slope


def _in(*values: float) -> list[float]:
    return [inch(v).meters for v in values]


def test_a_condensate_run_lands_where_it_was_authored_not_at_the_chains_end() -> None:
    parent = SimpleNamespace(path=[(inch(216).meters, inch(108).meters),
                                   (inch(162).meters, inch(108).meters)])
    run = SimpleNamespace(path=[(inch(210).meters, inch(12).meters),
                                (inch(210).meters, inch(108).meters)])
    x, y, z = _landing(run, parent, _in(-20.276, -21.446))
    assert (x, y) == pytest.approx((inch(210).meters, inch(108).meters))
    assert z == pytest.approx(inch(-20.406).meters, abs=inch(0.001).meters)


def test_condensate_grade_is_the_engines_own_drain_grade() -> None:
    """Pinned so the cited constant cannot drift from what ``mep.drain_slope`` grades."""
    assert minimum_slope(inch(0.75).meters) == CONDENSATE_SLOPE_IN_PER_FT
    assert minimum_slope(inch(0.75).meters, sanitary=False) == CONDENSATE_SLOPE_IN_PER_FT


def test_no_cleanouts_on_a_run_that_is_not_sanitary() -> None:
    proposal = SimpleNamespace(echo={"sanitary": False})
    assert place_cleanouts(None, None, proposal) == ((), 0.0, [])


def test_radon_and_sump_have_trades_and_only_gas_goes_unassigned() -> None:
    runs = [SimpleNamespace(tag=f"PR-{system}", system=system, storey="basement",
                            diameter_m=0.05, z_m=[0.0])
            for system in ("radon", "sump_discharge", "gas")]
    model = SimpleNamespace(pipe_runs=runs, ducts=[], conduits=[])
    trades = {t.tag: t.trade for t in order_targets(model)}
    assert trades == {"PR-radon": "vent", "PR-sump_discharge": "supply", "PR-gas": ""}


def test_sump_discharge_roots_on_the_leaders_riser(catlin_model_ro) -> None:
    run = next(r for r in catlin_model_ro.pipe_runs if r.tag == "PR-B-SUMP-DISCH")
    problems: list[str] = []
    root, riser = sump_endpoints(catlin_model_ro, run, problems)
    assert riser == "TR-RF-LEADER-W-EXT-RISER" and not problems
    assert root[2] == pytest.approx(run.z_m[-1])  # the authored wye is on the column


def test_a_sump_line_nothing_names_refuses_with_the_fix(catlin_model_ro) -> None:
    stray = SimpleNamespace(tag="PR-NOBODY", z_m=[0.0])
    problems: list[str] = []
    assert sump_endpoints(catlin_model_ro, stray, problems) is None
    assert "discharge_line_ref" in problems[0] and "PR-NOBODY" in problems[0]


def test_the_sump_line_is_held_through_the_cast_sleeve_it_is_authored_through(
        catlin_model_ro) -> None:
    run = next(r for r in catlin_model_ro.pipe_runs if r.tag == "PR-B-SUMP-DISCH")
    vertex, tag, _ = sleeve_hold(catlin_model_ro, run)
    assert (vertex, tag) == (2, "SP-B-N4-SUMP")  # the tail starts past the wall
