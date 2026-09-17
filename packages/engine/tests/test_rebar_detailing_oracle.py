"""``resolve/rebar/detailing.py`` against ``houses/catlin/notes/rebar_layout_basis.md`` §1.

The note's table was worked by hand before the module existed. Every value is reproduced to
the note's printed precision; the delegation from ``engineering/deck_post`` is pinned by
``test_pier_calcs.py`` staying byte-for-byte unchanged.
"""

from __future__ import annotations

import pytest

from typehaus.resolve.rebar import detailing as det

#: bar -> (ld 5,000, class B 5,000, class B top-cast 5,000, ld 4,000, class B 4,000, compression)
_TABLE = {
    3: (12.73, 16.55, 21.51, 14.23, 18.50, 12.00),
    4: (16.97, 22.06, 28.68, 18.97, 24.67, 15.00),
    5: (21.21, 27.58, 35.85, 23.72, 30.83, 18.75),
    6: (25.46, 33.09, 43.02, 28.46, 37.00, 22.50),
}
#: bar -> (standard 90° allowance, tie 135° black, tie 135° A767)
_HOOKS = {3: (5.062, 4.084, 4.5925), 4: (6.749, 4.445, 5.1233), 5: (8.436, 5.557, 6.4042),
          6: (10.123, 7.685, 7.685)}
#: bar -> (IRC-governed wall lap 5,000, ldh 5,000 at every ψ 1.0)
_WALL = {3: (16.55, 6.0), 4: (30.0, 6.0), 5: (38.0, 7.115), 6: (45.0, 9.353)}


@pytest.mark.parametrize("bar", sorted(_TABLE))
def test_development_and_laps_reproduce_the_note(bar: int) -> None:
    ld5, b5, b5_top, ld4, b4, comp = _TABLE[bar]
    assert det.development_length_in(bar, 5000) == pytest.approx(ld5, abs=0.006)
    assert det.tension_lap_in(bar, 5000, "B") == pytest.approx(b5, abs=0.006)
    assert det.tension_lap_in(bar, 5000, None, top_cast=True) == pytest.approx(b5_top, abs=0.006)
    assert det.development_length_in(bar, 4000) == pytest.approx(ld4, abs=0.006)
    assert det.tension_lap_in(bar, 4000, "B") == pytest.approx(b4, abs=0.006)
    assert det.compression_lap_in(bar) == pytest.approx(comp, abs=0.006)


@pytest.mark.parametrize("bar", sorted(_HOOKS))
def test_hook_allowances_reproduce_the_note(bar: int) -> None:
    std, tie, tie_galv = _HOOKS[bar]
    assert det.hook_allowance_in(bar, "std90") == pytest.approx(std, abs=0.0006)
    assert det.hook_allowance_in(bar, "tie135") == pytest.approx(tie, abs=0.0006)
    assert det.hook_allowance_in(bar, "tie135", galvanized=True) == pytest.approx(
        tie_galv, abs=0.0006)
    assert det.hook_allowance_in(bar, "std90", galvanized=True) == pytest.approx(std, abs=0.0006)


@pytest.mark.parametrize("bar", sorted(_WALL))
def test_wall_laps_and_hooked_development_reproduce_the_note(bar: int) -> None:
    lap, ldh = _WALL[bar]
    assert det.wall_lap_in(bar, 5000, "B") == pytest.approx(lap, abs=0.006)
    assert det.hooked_development_in(bar, 5000, confined_spacing=True,
                                     side_cover_ok=True) == pytest.approx(ldh, abs=0.001)


def test_only_a767_bends_at_a767_diameters() -> None:
    assert det.bent_before_galvanizing("hdg-a767")
    assert not det.bent_before_galvanizing("black")
    assert not det.bent_before_galvanizing(None)


def test_class_a_is_ld_and_every_length_has_the_12_inch_floor() -> None:
    assert det.tension_lap_in(3, 5000, "A") == pytest.approx(12.73, abs=0.006)
    assert det.development_length_in(3, 10_000) == 12.0
    assert det.compression_lap_in(3) == 12.0


def test_the_deck_post_lap_is_this_module() -> None:
    """``engineering/deck_post._class_b_lap_in`` returns 1.3 × the unfloored ld."""
    from types import SimpleNamespace

    from typehaus.engineering.deck_post import _class_b_lap_in

    cage = SimpleNamespace(bar_diameter_in=0.625)
    assert _class_b_lap_in(cage, 5000.0) == pytest.approx(27.577, abs=0.001)
