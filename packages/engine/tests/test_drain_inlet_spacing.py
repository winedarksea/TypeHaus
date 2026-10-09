"""``mep.drain_inlet_spacing`` — two inlets on one barrel, graded on published fittings.

catlin's ``mep_drainage.py`` claims the attic branch and the suite WC branch are "two inlets
on one barrel, not a double fitting at one point". They land 3 1/2" apart: a combo (501)
with a street sanitary tee (403) in its top hub, the tightest sanitary stack Charlotte Pipe
SUB-PAC-PVC-DWV publishes. These pin that the pair is found and PASSes on those two parts,
and that a spacing below the published minimum FAILs.
"""

from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

import pytest

from typehaus.checks.mep.drain_inlet_spacing import (
    INLET_SCREEN_DIAMETERS,
    drain_inlet_spacing,
)
from typehaus.hardware.fittings import fitting_catalog
from typehaus.resolve.model import ResolvedPipeRun

pytestmark = pytest.mark.slow

_IN = 0.0254


def _drain(tag, pts, diameter_in=3.0) -> ResolvedPipeRun:
    return ResolvedPipeRun(
        uid=tag, tag=tag, storey="S", system="drain",
        path=tuple((x * _IN, y * _IN) for x, y, _ in pts), diameter_m=diameter_in * _IN,
        z_start_m=pts[0][2] * _IN, z_end_m=pts[-1][2] * _IN, length_m=1.0,
        z_m=tuple(z * _IN for *_, z in pts))


def _stack(gap_in, *, rise_in=0.25):
    """A 3" barrel with two level-ish 3" branches ending on it ``gap_in`` apart."""
    barrel = _drain("BARREL", [(0, 0, 120), (0, 0, 0)])
    low = _drain("LOW", [(48, 0, 60 + rise_in * 4), (0, 0, 60)])
    high = _drain("HIGH", [(0, 48, 60 + gap_in + rise_in * 4), (0, 0, 60 + gap_in)])
    return SimpleNamespace(model=SimpleNamespace(pipe_runs=[barrel, low, high]))


def test_catlin_suite_stack_has_one_inlet_in_the_truss_band(catlin_ctx) -> None:
    """The combo + street tee pair is gone (2026-10-08): PR-A-STUBATH-DRAIN now ties into
    PR-M-S-SUITE-WC-DRAIN's horizontal leg, so the suite stack head takes one branch."""
    findings = drain_inlet_spacing(catlin_ctx)
    assert not [f for f in findings
                if "PR-A-STUBATH-DRAIN" in f.message and "PR-M-S-SUITE-WC-DRAIN" in f.message]


def test_catlin_carries_no_inlet_spacing_fail_or_unknown(catlin_ctx) -> None:
    assert {f.result.value for f in drain_inlet_spacing(catlin_ctx)} == {"pass"}


def test_it_fails_below_the_published_minimum() -> None:
    findings = drain_inlet_spacing(_stack(2.5))
    assert [f.result.value for f in findings] == ["fail"]
    assert 'closer than 3.50"' in findings[0].message
    assert findings[0].element_tags == ("BARREL", "LOW", "HIGH")


def test_it_passes_at_the_published_minimum() -> None:
    findings = drain_inlet_spacing(_stack(3.5))
    assert [f.result.value for f in findings] == ["pass"]
    assert "combo 501 + street sanitary tee 403" in findings[0].message


def test_a_45_degree_inlet_is_graded_as_a_wye() -> None:
    """Two branches arriving at 45 degrees stack as wyes: 5 + 3 1/8 with a street wye."""
    ctx = _stack(6.0, rise_in=12.0)  # 48" run, 48" rise: 45 degrees
    findings = drain_inlet_spacing(ctx)
    assert [f.result.value for f in findings] == ["fail"]
    assert 'closer than 8.12"' in findings[0].message


def test_a_reducing_pair_stays_unknown() -> None:
    ctx = _stack(2.5)
    low = ctx.model.pipe_runs[1]
    ctx.model.pipe_runs[1] = replace(low, diameter_m=2 * _IN)
    assert [f.result.value for f in drain_inlet_spacing(ctx)] == ["unknown"]


def test_every_stack_row_cites_a_part_and_page() -> None:
    """A stack station is a submittal measurement: name the part number and its page."""
    import re

    rows = [f for f in fitting_catalog()
            if f.branch_to_top_in is not None or f.branch_to_bottom_in is not None]
    assert rows, "the Charlotte stack rows are gone"
    for row in rows:
        assert re.search(r"part \d{3}, p\. \d+", row.source or ""), row.tag
        assert row.branch_to_top_in is not None and row.branch_to_bottom_in is not None


def test_the_screen_is_a_stated_convention_not_a_read_dimension() -> None:
    """Three barrel diameters clears a full-sweep fitting body on the larger pipe — the same
    convention ``run_interference.JOINT_REACH_FACTOR`` states, and for the same reason."""
    from typehaus.checks.mep.run_interference import JOINT_REACH_FACTOR

    assert INLET_SCREEN_DIAMETERS == JOINT_REACH_FACTOR == 3.0


def test_inlets_further_apart_than_the_screen_raise_no_question(catlin_ctx) -> None:
    """A stack with branches a foot apart is ordinary work and must not be reported."""
    from typehaus.checks.mep.drain_inlet_spacing import _barrels, _inlets_on

    for tag, point, z0_m, z1_m, diameter_m in _barrels(catlin_ctx):
        inlets = sorted(_inlets_on(catlin_ctx, tag, point, z0_m, z1_m))
        wide = [(a, b) for a, b in zip(inlets[:-1], inlets[1:], strict=False)
                if b[0] - a[0] > INLET_SCREEN_DIAMETERS * diameter_m]
        for (_low_z, low_tag), (_high_z, high_tag) in wide:
            assert not [f for f in drain_inlet_spacing(catlin_ctx)
                        if low_tag in f.element_tags and high_tag in f.element_tags]
