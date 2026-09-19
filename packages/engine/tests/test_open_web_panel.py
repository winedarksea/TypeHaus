"""``mep.open_web_panel`` — how many runs one web opening will actually take.

The engine read a floor truss as a CONTINUOUS 8 7/8" chase until 2026-09-19, so thirteen
4" ducts crossing every truss inside a 41" band all passed. A real truss has webs at panel
points, and the arithmetic is worked by hand in
``houses/catlin/notes/mep_duct_routing_basis.md`` §3a.
"""

from __future__ import annotations

import pytest

from typehaus.checks.mep.open_web_panel import _obliquity, _tiers, open_web_panel
from typehaus.findings import Result
from typehaus.quantities import M_PER_IN
from typehaus.resolve.mep_crossings import WebPanels

pytestmark = pytest.mark.slow

#: The note's §3a datum: pitch 24", clear opening 15", offset 12".
_PANELS = WebPanels(pitch_m=24 * M_PER_IN, opening_m=15 * M_PER_IN,
                    offset_m=12 * M_PER_IN)


def _in(metres):
    return metres / M_PER_IN


def test_the_openings_are_the_notes_openings() -> None:
    """§3a, term by term: the web band is (24 − 15)/2 = 4.5" either side of a panel point,
    so opening n runs 12 + 24n + 4.5 to + 19.5."""
    assert _in(_PANELS.web_width_m) == pytest.approx(9.0)
    for n, (low, high) in enumerate([(16.5, 31.5), (40.5, 55.5), (64.5, 79.5)]):
        span = _PANELS.opening_at(_PANELS.offset_m + n * _PANELS.pitch_m
                                  + _PANELS.web_width_m)
        assert _in(span[0]) == pytest.approx(low)
        assert _in(span[1]) == pytest.approx(high)


def test_a_run_is_clear_only_when_its_WHOLE_OUTSIDE_is_inside_one_opening() -> None:
    """The note's table: a 4" duct has 11" of legal centreline in a 15" opening, a 3" DWV
    11.5" and an 8" duct 7"."""
    for outside_in, low_in, high_in in ((4.0, 42.5, 53.5),
                                        (3.5, 42.25, 53.75),
                                        (8.0, 44.5, 51.5)):
        radius = outside_in / 2 * M_PER_IN
        assert _PANELS.clear_at((low_in + 0.01) * M_PER_IN, radius)
        assert _PANELS.clear_at((high_in - 0.01) * M_PER_IN, radius)
        assert not _PANELS.clear_at((low_in - 0.01) * M_PER_IN, radius)
        assert not _PANELS.clear_at((high_in + 0.01) * M_PER_IN, radius)


def test_the_web_bands_are_the_complement_of_the_openings() -> None:
    """What ``routing/obstacles`` turns into ``fixed`` prisms, so a search threads the
    openings by construction instead of being told off by a check afterwards."""
    bands = _PANELS.web_bands(0.0, 80 * M_PER_IN)
    assert [(round(_in(a), 2), round(_in(b), 2)) for a, b in bands[:4]] == [
        (7.5, 16.5), (31.5, 40.5), (55.5, 64.5), (79.5, 80.0)]


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


def test_an_unauthored_pitch_is_UNKNOWN_naming_the_floor(catlin_ctx) -> None:
    """A truss's panel layout is a shop drawing and this engine has no business inventing
    a pitch. FS-S-EAST is I-joist so it is not even in scope; what this pins is the
    sentence a deck with no layout gets."""
    from types import SimpleNamespace

    floor = SimpleNamespace(tag="FS-X", web_panels=None)
    from typehaus.resolve.mep_crossings import web_panels

    assert web_panels(floor) is None


def test_catlin_reports_the_level_two_neck(catlin_ctx) -> None:
    """§3a's arithmetic, as a verdict: nine 4" radials crossing square on one elevation want
    36.00" of a 15.00" opening. This is the finding D1 exists to answer."""
    fails = [f for f in open_web_panel(catlin_ctx) if f.result is Result.FAIL]
    neck = next(f for f in fails if "DU-M-ERV-R-KITCH" in f.element_tags)
    assert "FS-S-WEST" in neck.element_tags
    assert '9 runs share one elevation there and want 36.00" of its 15.00" clear width' \
        in neck.message
    assert "on 12 of its members" in neck.message
