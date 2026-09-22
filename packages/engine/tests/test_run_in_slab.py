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


def test_a_run_in_the_EPS_FORM_is_not_in_the_pour(catlin_ctx) -> None:
    """``SL-M-DECK`` is 14 3/8" tall and 10" of that is ``eps-deck-form`` — a material a
    plumber cuts a channel in with a hot knife. Carrying services without a cast void is
    what an EPS deck is SOLD for, and a check that reported it would say the opposite of
    what is true.

    The band reading is ``resolve/mep_concrete.concrete_bands``, shared with
    ``mep.sleeve_coverage``; this pins that this check consumes it rather than the prism."""
    from typehaus.resolve.mep_concrete import concrete_bands

    deck = next(s for s in catlin_ctx.model.solids if s.tag == "SL-M-DECK")
    (bottom, top), = concrete_bands(catlin_ctx.model, deck)
    assert top == pytest.approx(deck.z1_m)
    # Ten inches of foam under 4 3/8" of topping, and only the topping is a pour.
    assert (bottom - deck.z0_m) / M_PER_IN == pytest.approx(10.0, abs=0.05)
    assert all("SL-M-DECK" not in f.element_tags for f in _fails(catlin_ctx)), \
        "nothing on catlin lies in the deck's topping today"


def test_a_through_crossing_reports_ONCE(catlin_ctx) -> None:
    """``PR-B-CW-TRUNK`` and ``PR-B-HW-KITCH`` pass through ``SL-M-DECK`` and
    ``mep.sleeve_coverage`` owns them. Without the dedupe every one of those would report
    here too, and a reader could not tell which finding to act on."""
    from typehaus.resolve.mep_concrete import concrete_crossings

    owned = {(row["run"], row["host"]) for row in concrete_crossings(catlin_ctx.model)}
    assert ("PR-B-CW-TRUNK", "SL-M-DECK") in owned
    assert ("PR-B-HW-KITCH", "SL-M-DECK") in owned
    reported = {tuple(f.element_tags) for f in _fails(catlin_ctx)}
    assert not (owned & reported)


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
    assert sorted(tuple(f.element_tags) for f in _fails(catlin_ctx)) == [
        ("PR-SG-ARCH-OVERFLOW", "SL-SG-FIELD"),
    ]
