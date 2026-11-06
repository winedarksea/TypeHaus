"""``mep.open_web_panel`` — how many runs one web opening will actually take.

The engine read a floor truss as a CONTINUOUS 8 7/8" chase until 2026-09-19. Each truss now
carries an ``OpenWebShape`` (``resolve/open_web.py``), worked by hand in
``houses/catlin/notes/open_web_truss_geometry.md`` and pinned in ``test_open_web_shape.py``.
This module pins the check's own helpers and the house's result.
"""

from __future__ import annotations

import pytest

from typehaus.checks.mep.open_web_panel import _obliquity, _tiers, open_web_panel
from typehaus.findings import Result

pytestmark = pytest.mark.slow


def test_width_along_the_member_is_not_diameter() -> None:
    """A cylinder cut obliquely is an ellipse. Square is 1.0, 45° is 1.414, 30° is 2.0."""
    assert _obliquity((0.0, 0.0), (0.0, 1.0), along_x=True) == pytest.approx(1.0)
    assert _obliquity((0.0, 0.0), (1.0, 1.0), along_x=True) == pytest.approx(2 ** 0.5)
    assert _obliquity((0.0, 0.0), (3 ** 0.5, 1.0), along_x=True) == pytest.approx(2.0)
    # A leg running ALONG a bay crosses no member at all.
    assert _obliquity((0.0, 0.0), (1.0, 0.0), along_x=True) is None


def test_a_TIER_is_not_a_sum() -> None:
    """Two 4" ducts at the window's two tiers use 4" of the opening each, not 8" between
    them. Summing them would call a 15" opening full of two ducts that never meet — the
    same error ``resolve/mep_packing`` was written to stop making about a bay."""
    stacked = [("A", 0.1, 0.0, 0.1), ("B", 0.1, 0.12, 0.22)]
    assert [len(tier) for tier in _tiers(stacked)] == [1, 1]
    side_by_side = [("A", 0.1, 0.0, 0.1), ("B", 0.1, 0.05, 0.15)]
    assert [len(tier) for tier in _tiers(side_by_side)] == [2]


def test_catlin_over_subscribed_openings_are_pinned(catlin_ctx) -> None:
    """TrimJoist J12's published openings (a 5" round per pocket, one run each) replaced the
    13" owner-basis rectangle, which reopened the level-2 lanes. The re-route closed every
    pocket but D4, which DU-M-ERV-R-BED holds open on the ERV owner decision (suppressed in
    catlin's preferences, decision #117). Pinned so nothing else joins it."""
    fails = [f for f in open_web_panel(catlin_ctx) if f.result is Result.FAIL]
    assert all("DU-M-ERV-R-BED" in f.element_tags for f in fails), [f.message for f in fails]
    assert len(fails) <= 1
