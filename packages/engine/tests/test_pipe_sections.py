"""Nominal size vs real outside diameter — the table, and the one thing it must not collapse.

``resolve/pipe_sections.py`` is the sibling of ``LUMBER_ACTUAL``: the author writes the
nominal the code tables are keyed on, the geometry gets the dimension the pipe measures.
"""

from __future__ import annotations

import pytest
from _helpers import check_context

from typehaus.quantities import M_PER_IN, inch
from typehaus.resolve.pipe_sections import (
    IPS_OD_IN,
    RACEWAY_OD_IN,
    TUBE_OD_IN,
    pipe_outside_diameter_m,
    raceway_outside_diameter_m,
)


def _in(meters: float) -> float:
    return meters / M_PER_IN


def _approx(value: float) -> object:
    return pytest.approx(value, abs=1e-9)


def test_ips_drain_sizes_are_the_published_od() -> None:
    """3" DWV is 3.500" — the half inch every clearance in the engine used to give away."""
    assert _in(pipe_outside_diameter_m(inch(3).meters, "pvc")) == _approx(3.500)
    assert _in(pipe_outside_diameter_m(inch(2).meters, "pvc")) == _approx(2.375)
    assert _in(pipe_outside_diameter_m(inch(4).meters, "pvc")) == _approx(4.500)
    assert _in(pipe_outside_diameter_m(inch(1.5).meters, "pvc")) == _approx(1.900)


def test_copper_tube_size_is_not_iron_pipe_size() -> None:
    """**The assertion that pins the three tables apart.**

    A material-blind IPS table reads 1 1/4" copper at 1.660" instead of 1.375" — a quarter
    inch of invented obstruction — and on catlin that alone conjures a
    ``mep.run_in_finished_volume`` finding on ``PR-B-CW-TRUNK``, which is copper. If anyone
    ever "simplifies" these to one table, this is the test that stops them.
    """
    assert _in(pipe_outside_diameter_m(inch(1.25).meters, "copper")) == _approx(1.375)
    assert _in(pipe_outside_diameter_m(inch(1.25).meters, None)) == _approx(1.660)
    assert IPS_OD_IN[1.25] != TUBE_OD_IN[1.25]
    # PEX is built to the copper OD series so it takes the same fittings.
    assert (pipe_outside_diameter_m(inch(0.75).meters, "pex")
            == pipe_outside_diameter_m(inch(0.75).meters, "copper"))


def test_copper_tube_size_is_nominal_plus_an_eighth() -> None:
    for nominal, od in TUBE_OD_IN.items():
        assert abs(od - (nominal + 0.125)) < 1e-9, nominal


def test_raceway_trade_size_is_a_bore_not_an_outside() -> None:
    """3/4" EMT measures 0.922" — the error that put two catlin raceways inside a chord."""
    assert _in(raceway_outside_diameter_m(inch(0.75).meters)) == _approx(0.922)
    assert _in(raceway_outside_diameter_m(inch(0.5).meters)) == _approx(0.706)
    assert RACEWAY_OD_IN[0.75] > 0.75


def test_unstated_material_takes_the_larger_series() -> None:
    """An unstated material must not be the *optimistic* read of a clearance."""
    for nominal in sorted(set(IPS_OD_IN) & set(TUBE_OD_IN)):
        assert IPS_OD_IN[nominal] >= TUBE_OD_IN[nominal], nominal
        assert (pipe_outside_diameter_m(inch(nominal).meters, None)
                == pipe_outside_diameter_m(inch(nominal).meters, "pvc"))


def test_unknown_nominal_returns_itself() -> None:
    """Documented behaviour, and documented as under-reporting rather than safe."""
    assert _in(pipe_outside_diameter_m(inch(7).meters, "pvc")) == _approx(7.0)
    assert pipe_outside_diameter_m(0.0, "pvc") == 0.0
    assert raceway_outside_diameter_m(0.0) == 0.0


def test_run_radii_reads_the_tables(catlin_model_ro, catlin_plan) -> None:
    """The one notion of a run's surface — and it is the real one, per material."""
    from typehaus.checks.mep.routing_geometry import run_radii

    ctx = check_context(plan=catlin_plan, model=catlin_model_ro)

    radii = run_radii(ctx)
    by_tag = {r.tag: r for r in catlin_model_ro.pipe_runs}
    three_inch_pvc = [t for t, r in by_tag.items()
                      if r.material == "pvc" and abs(_in(r.diameter_m or 0) - 3.0) < 1e-6]
    assert three_inch_pvc
    for tag in three_inch_pvc:
        assert abs(_in(radii[tag] * 2) - 3.500) < 1e-9, tag
    for raceway in catlin_model_ro.conduits:
        if abs(_in(raceway.trade_size_m or 0) - 0.75) < 1e-6:
            assert abs(_in(radii[raceway.tag] * 2) - 0.922) < 1e-9, raceway.tag
    # A duct's authored diameter already IS its outside dimension.
    for duct in catlin_model_ro.ducts:
        if duct.diameter_m:
            assert abs(radii[duct.tag] * 2 - duct.diameter_m) < 1e-12, duct.tag
