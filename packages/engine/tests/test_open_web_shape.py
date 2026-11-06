"""``OpenWebShape``: the geometry of ``houses/catlin/notes/open_web_truss_geometry.md``.

One 18' truss and one stair-clipped truss on FS-S-WEST (TrimJoist J12), pinned to the note's
hand-worked numbers, plus the per-opening grade rules.
"""

from __future__ import annotations

import pytest

from typehaus.quantities import M_PER_IN
from typehaus.resolve.open_web import RunSize, grade_crossing

_TOL = 0.01  # inches


def _in(metres: float) -> float:
    return metres / M_PER_IN


def _truss(model, length_in: float):
    floor = next(f for f in model.floors if f.tag == "FS-S-WEST")
    return next(m for m in floor.members
                if m.web is not None and abs(_in(m.length_m) - length_in) < 0.01)


def _pocket(shape, run_in: float):
    return next(o for o in shape.openings
                if o.kind == "D" and abs(_in(o.run0_m) - run_in) < 0.02)


def test_the_18_foot_truss_is_the_notes_s1(catlin_model_ro) -> None:
    member = _truss(catlin_model_ro, 215.0)
    shape = member.web
    assert _in(shape.stock_m) == pytest.approx(216.0)
    assert _in(shape.trim_lo_m) == pytest.approx(0.5) and _in(shape.trim_hi_m) == pytest.approx(0.5)
    assert _in(shape.chase_run_m) == pytest.approx(107.5)
    trims = [o for o in shape.openings if o.kind == "trim_end"]
    assert sorted((round(_in(o.run0_m), 3), round(_in(o.run1_m), 3)) for o in trims) == [
        (0.0, 11.5), (203.5, 215.0)]
    r1 = next(o for o in shape.openings if o.kind == "R1")
    assert (_in(r1.run0_m), _in(r1.run1_m)) == pytest.approx((99.5, 115.5), abs=_TOL)
    # Pockets: right of the chase, and the end pocket against the TrimEnd.
    for start, end in ((118.0, 128.74), (119.26, 140.74), (131.26, 152.74), (179.26, 202.13),
                       (191.37, 203.5)):
        pocket = _pocket(shape, start)
        assert _in(pocket.run1_m) == pytest.approx(end, abs=_TOL)
    assert _in(_pocket(shape, 86.26).run1_m) == pytest.approx(97.0, abs=_TOL)
    # Plan: p0 stands at x = 1.75", so the chase is at x = 109.25".
    assert _in(member.p0[0]) + _in(shape.chase_run_m) == pytest.approx(109.25, abs=_TOL)


def test_the_stair_clipped_truss_is_the_notes_s2(catlin_model_ro) -> None:
    member = _truss(catlin_model_ro, 120.75)
    shape = member.web
    assert _in(shape.stock_m) == pytest.approx(144.0)
    assert _in(shape.trim_lo_m) == pytest.approx(11.625)
    assert _in(shape.trim_lo_m) <= 12.0 and not shape.issues
    assert _in(shape.chase_run_m) == pytest.approx(60.375)
    assert _in(member.p0[0]) + _in(shape.chase_run_m) == pytest.approx(62.125, abs=_TOL)
    assert _in(_pocket(shape, 0.375).run1_m) == pytest.approx(12.51, abs=_TOL)


def test_each_opening_grades_what_it_publishes(catlin_model_ro) -> None:
    shape = _truss(catlin_model_ro, 215.0).web
    chase = _in(shape.chase_run_m)
    mid = shape.window_z_m[0] / 2 + shape.window_z_m[1] / 2

    def grade(run_in, z_m, round_in, along_in=None):
        size = RunSize((along_in or round_in) * M_PER_IN, round_in * M_PER_IN, True)
        return grade_crossing(shape, run_in * M_PER_IN, z_m, size)

    assert grade(chase, mid, 8.0).ok  # R1 takes an 8" round
    assert not grade(chase, mid, 9.0).ok
    assert grade(5.0, mid, 4.0).opening.kind == "trim_end"  # a TrimEnd passes nothing
    assert not grade(5.0, mid, 1.0).ok
    # A web pocket: the 5" round of the row, centred on the bottom-chord pocket 131.26..152.74.
    z_low = 4.0 * M_PER_IN  # 4" up: a 4" round clears the bottom chord (1.5")
    assert grade(142.0, z_low, 4.0).ok
    assert not grade(142.0, z_low, 5.5).ok  # over the published round
    assert not grade(131.5, z_low, 4.0).ok  # against the diagonal: outline reaches it
    assert grade(142.0, z_low, 4.0).opening.kind == "D"
