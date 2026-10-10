"""R311.7.8.2 clearance and ends, R311.7.1 projection, R301.5 support spacing — on drawn rails.

``checks/code/mn_residential/handrail_clearance.py`` and ``handrail_hardware.py``, run over
a synthetic rail resolved by the real resolver beside a one-layer wall.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from _railing_fixtures import railing, railing_type, resolve_railings, wall_along_x

from typehaus.checks.code.mn_residential.handrail_clearance import (
    handrail_projection,
    handrail_wall_clearance,
)
from typehaus.checks.code.mn_residential.handrail_hardware import (
    handrail_ends,
    handrail_support_spacing,
)
from typehaus.findings import Result
from typehaus.model.enums import RailingKind
from typehaus.quantities import ft, inch, mm, pt

# The checks only ask that the model HAS a stair; a tag nothing serves keeps the rail flat.
_STAIR = SimpleNamespace(tag="ST-ELSEWHERE")


def _ctx(y_in=2.375, *, wall=True, types=(), **kw):
    defaults = dict(path=(pt(ft(0), inch(y_in)), pt(ft(10), inch(y_in))), mount="wall",
                    kind=RailingKind.METAL_SURFACE_MOUNT, rail_count=1, height=inch(36),
                    post_spacing=inch(48), role="handrail", serves_stair="ST-T",
                    graspable_profile="1.5in round — Type I")
    defaults.update(kw)
    rail = railing("RL-H", **defaults)
    model = resolve_railings([rail], types=types, stairs=[_STAIR],
                             walls=[wall_along_x("W-T", 0.0)] if wall else [])
    return SimpleNamespace(model=model, plan=model.plan)


def _results(findings):
    return [f.result for f in findings]


@pytest.mark.parametrize(("y_in", "expected"), [(2.0, Result.FAIL), (2.375, Result.PASS)])
def test_wall_clearance_is_measured_off_the_drawn_bar(y_in, expected):
    """2" to the centre of a 1 1/2" bar leaves 1 1/4"; 2 3/8" leaves 1 5/8"."""
    assert _results(handrail_wall_clearance(_ctx(y_in))) == [expected]


def test_a_free_standing_rail_has_no_wall_to_clear():
    assert _results(handrail_wall_clearance(_ctx(wall=False))) == [Result.NOT_APPLICABLE]


def test_projection_counts_the_bar_section():
    """A 42 mm bar at 3 3/4" to its centre reaches 4.58" — over R311.7.1's 4 1/2"."""
    product = railing_type("RT-TI", rail_diameter=mm(42))
    assert _results(handrail_projection(
        _ctx(3.75, types=[product], type_ref="RT-TI"))) == [Result.FAIL]
    assert _results(handrail_projection(
        _ctx(2.75, types=[product], type_ref="RT-TI"))) == [Result.PASS]


@pytest.mark.parametrize(("start", "end", "expected"), [
    (None, None, Result.UNKNOWN),
    ("open", "wall_return", Result.FAIL),
    ("wall_return", "wall_return", Result.PASS),
    ("safety_terminal", "wall_return", Result.PASS),
    ("newel", "wall_return", Result.UNKNOWN),  # no post stands at a wall rail's end
])
def test_ends_return_or_terminate(start, end, expected):
    ctx = _ctx(start_termination=start, end_termination=end)
    assert _results(handrail_ends(ctx)) == [expected]


def test_an_authored_return_that_reached_no_wall_fails():
    ctx = _ctx(wall=False, start_termination="wall_return", end_termination="wall_return")
    assert _results(handrail_ends(ctx)) == [Result.FAIL]


def test_a_post_mounted_handrail_terminates_in_its_own_posts():
    ctx = _ctx(mount="fascia")
    (finding,) = handrail_ends(ctx)
    assert finding.result == Result.PASS and "RL-H-POST1" in finding.message


@pytest.mark.parametrize(("limit_mm", "expected"), [(1100, Result.PASS), (1000, Result.FAIL)])
def test_support_spacing_against_the_products_limit(limit_mm, expected):
    """10' at 48" o.c. is three 40" (1016 mm) bays; the returns are the end supports."""
    product = railing_type("RT-TI", rail_diameter=mm(42), bracket_spacing_max=mm(limit_mm))
    ctx = _ctx(2.75, types=[product], type_ref="RT-TI",
               start_termination="wall_return", end_termination="wall_return")
    assert _results(handrail_support_spacing(ctx)) == [expected]


def test_support_spacing_unknown_without_a_stated_limit_and_na_on_posts():
    assert _results(handrail_support_spacing(_ctx())) == [Result.UNKNOWN]
    assert _results(handrail_support_spacing(_ctx(mount="fascia"))) == [
        Result.NOT_APPLICABLE]


def test_a_stub_bracket_with_no_wall_carries_nothing():
    product = railing_type("RT-TI", bracket_spacing_max=mm(1100))
    ctx = _ctx(types=[product], type_ref="RT-TI", wall=False)
    (finding,) = handrail_support_spacing(ctx)
    assert finding.result == Result.FAIL and "0 support(s)" in finding.message
