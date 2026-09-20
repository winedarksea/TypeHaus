"""E5: the one collinear-overlap arithmetic the four wall-line matchers share.

The helper answers *geometry only* — where two segments share a line and a run. Every
caller keeps its own tolerance and its own minimum, because ``layout_lines`` measures on
the datum face and ``stacking`` on the raw node axis (43.8 mm apart at catlin's basement).
"""

from __future__ import annotations

import math

from typehaus.resolve.layout_lines import collinear_overlap

A = ((0.0, 0.0), (10.0, 0.0))


def _run(seg_b, tol=0.05, **kw):
    out = collinear_overlap(A, seg_b, tol, **kw)
    return None if out is None else out[1] - out[0]


def test_full_and_partial_overlap():
    assert _run(((0.0, 0.0), (10.0, 0.0))) == 10.0
    assert _run(((4.0, 0.0), (12.0, 0.0))) == 6.0
    assert _run(((-3.0, 0.0), (2.0, 0.0))) == 2.0


def test_result_is_an_interval_in_a_s_own_parameter():
    assert collinear_overlap(A, ((4.0, 0.0), (12.0, 0.0)), 0.05) == (4.0, 10.0)


def test_reversed_b_is_the_same_line():
    assert _run(((12.0, 0.0), (4.0, 0.0))) == 6.0


def test_disjoint_returns_a_negative_or_empty_run():
    lo, hi = collinear_overlap(A, ((14.0, 0.0), (18.0, 0.0)), 0.05)
    assert hi - lo <= 0.0  # the caller's minimum rejects it; the helper does not judge


def test_off_line_beyond_tolerance_is_not_the_same_line():
    assert collinear_overlap(A, ((0.0, 0.2), (10.0, 0.2)), 0.05) is None
    assert _run(((0.0, 0.02), (10.0, 0.02))) == 10.0  # within tolerance


def test_tolerance_is_the_caller_s_and_is_honoured_as_given():
    b = ((0.0, 0.1), (10.0, 0.1))
    assert collinear_overlap(A, b, 0.05) is None
    assert collinear_overlap(A, b, 0.2) is not None


def test_not_parallel_is_rejected():
    assert collinear_overlap(A, ((0.0, 0.0), (7.0, 7.0)), 0.05) is None


def test_degenerate_segments():
    assert collinear_overlap(((1.0, 1.0), (1.0, 1.0)), A, 0.05) is None
    assert collinear_overlap(A, ((2.0, 0.0), (2.0, 0.0)), 0.05) is None


def test_both_ends_gates_the_far_endpoint_too():
    """platform's formulation: no cross-product test, both of b's ends held to the tol."""
    splayed = ((0.0, 0.0), (10.0, 0.5))
    assert collinear_overlap(A, splayed, 0.05) is None
    assert collinear_overlap(A, splayed, 0.05, both_ends=True) is None
    # a degenerate b on the line passes both_ends (no direction to test) but not the default
    assert collinear_overlap(A, ((2.0, 0.0), (2.0, 0.0)), 0.05, both_ends=True) == (2.0, 2.0)


def test_diagonal_line_projects_by_arc_length():
    a = ((0.0, 0.0), (3.0, 4.0))  # span 5
    lo, hi = collinear_overlap(a, ((1.5, 2.0), (6.0, 8.0)), 0.05)
    assert math.isclose(lo, 2.5) and math.isclose(hi, 5.0)
