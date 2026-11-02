"""``mep.run_in_slab`` — a run buried in a pour nobody cast a void for.

The hole ``preferences.toml`` named and nothing graded: ``mep.run_in_finished_volume``
measures hang below a ceiling, ``mep.run_member_crossing`` reads framed members, and
``mep.sleeve_coverage`` asks about passing THROUGH. None of the three answers "this run is
inside it".
"""

from __future__ import annotations

import pytest

from typehaus.checks.mep.run_in_slab import MIN_EMBEDDED_M, run_in_slab
from typehaus.findings import Result
from typehaus.quantities import M_PER_IN

pytestmark = pytest.mark.slow


def _fails(ctx):
    return [f for f in run_in_slab(ctx) if f.result is Result.FAIL]


def _synthetic_fails(*runs):
    from _helpers import check_context
    from _mixed_deck_plan import resolved_with

    model = resolved_with(basement=runs)
    return model, _fails(check_context(model=model))


def test_a_run_in_the_EPS_FORM_is_not_in_the_pour() -> None:
    """``_mixed_deck_plan``'s deck (catlin's retired ``SL-M-DECK``) is 10" of
    ``eps-deck-form`` under a 4 3/16" cap — foam a plumber cuts a channel in with a hot
    knife. Carrying services without a cast void is what an EPS deck is SOLD for, and a check
    that reported it would say the opposite of what is true. Raised until its envelope breaks
    the cap's soffit (106"), the same 5' leg is along the pour, so the band reading
    (``resolve/mep_concrete.concrete_bands``, shared with ``mep.sleeve_coverage``) is what
    excuses it, not the prism."""
    from _mixed_deck_plan import DECK, drain

    def leg(z_in):
        return drain("PRFOAM00e1", "PR-FOAM", ((3, 18), (8, 18)), (z_in, z_in))

    _model, in_foam = _synthetic_fails(leg(100))
    assert not in_foam, [f.message for f in in_foam]
    _model, at_cap = _synthetic_fails(leg(105.5))
    assert [f.element_tags for f in at_cap] == [("PR-FOAM", DECK)]


def test_a_through_crossing_reports_ONCE() -> None:
    """A run passing THROUGH a 12" foundation wall is ``mep.sleeve_coverage``'s crossing.
    Without the dedupe it would report here too, and a reader could not tell which finding
    to act on. It falls through the wall's mid-height, which ``concrete_crossings`` once
    read as a slab crossing outside the footprint and dropped."""
    from _mixed_deck_plan import drain

    from typehaus.resolve.mep_concrete import concrete_crossings

    run = drain("PRWALL00e1", "PR-WALL", ((9, 3), (9, -3)), (48, 47.5))
    model, fails = _synthetic_fails(run)
    owned = {(row["run"], row["host"]) for row in concrete_crossings(model)}
    assert ("PR-WALL", "W-S") in owned
    assert not fails, [f.message for f in fails]


def test_the_band_is_read_over_the_CLIPPED_length_not_the_whole_leg(catlin_ctx) -> None:
    """The banding error ``mep.run_interference`` shed the same day.
    ``PR-B-KITCH-DRAIN``'s third leg leaves the centre wall at -10.8" and falls to -12.9"
    eight feet later; read over the whole leg it dips under the wall's -13.4" top and the
    run appeared to be buried in a wall it only starts at."""
    assert all("PR-B-KITCH-DRAIN" not in f.element_tags for f in _fails(catlin_ctx))


def test_clipped_band_interpolates_z_at_the_clip() -> None:
    from shapely.geometry import LineString

    from typehaus.checks.mep.run_in_slab import _clipped_band

    line = LineString(((0.0, 0.0), (10.0, 0.0)))
    inside = LineString(((2.0, 0.0), (4.0, 0.0)))
    low, high = _clipped_band(line, inside, 0.0, 10.0, grow=0.5)
    # z is affine in arc length: 2.0 and 4.0 along a 10 m leg rising 0..10.
    assert low == pytest.approx(2.0 - 0.5)
    assert high == pytest.approx(4.0 + 0.5)


def test_a_duct_through_a_concrete_wall_is_now_a_crossing(catlin_ctx) -> None:
    """This check found ``DU-B-ERV-R-PLAY`` through catlin's 12" centre wall while
    ``concrete_crossings`` walked no duct (1.0 ft of leg 3, 4.0" of cover). It walks ducts
    since B5, so the crossing is ``mep.sleeve_coverage``'s and the dedupe drops it here."""
    assert all("DU-B-ERV-R-PLAY" not in f.element_tags for f in _fails(catlin_ctx))


def test_a_clip_is_not_a_length_of_pipe_in_a_pour() -> None:
    """A vertex landing on a face, or a corner clipped by a turn. Half a foot."""
    assert MIN_EMBEDDED_M / M_PER_IN == pytest.approx(6.0)


def test_catlin_reports_exactly_the_one_it_has(catlin_ctx) -> None:
    """Pinned so a campaign that fixes one, or a geometry move that adds one, is visible."""
    # PR-SG-ARCH-OVERFLOW, the last, retired with the overflow's move to W1's heel (2026-09-23).
    assert sorted(tuple(f.element_tags) for f in _fails(catlin_ctx)) == []


def test_a_run_lying_ALONG_a_face_is_not_a_crossing() -> None:
    """CD-B-KITCHEN's 1" jog ran on W-B-E2's concrete face; overlap with the CLOSED polygon
    read as 1" embedded and a wall sleeve was authored to a 12" bore that served nothing."""
    from shapely.geometry import LineString, Point, Polygon

    from typehaus.resolve.mep_concrete import _segment_concrete_hit

    wall = Polygon([(0.0, 0.0), (0.3, 0.0), (0.3, 3.0), (0.0, 3.0)])
    along = _segment_concrete_hit((0.0, 1.0), (0.0, 1.1), -0.4, -0.4, wall, -2.0, 0.0,
                                  LineString, Point)
    inside = _segment_concrete_hit((0.01, 1.0), (0.01, 1.1), -0.4, -0.4, wall, -2.0, 0.0,
                                   LineString, Point)
    assert along is None
    assert inside is not None
