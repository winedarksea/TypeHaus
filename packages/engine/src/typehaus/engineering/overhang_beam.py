"""Statics of a two-support beam with an overhang at either end, under patterned uniform load.

Pure arithmetic; no model types. ``glulam_beam`` reads it. The beam is three segments —
overhang ``a``, back span ``s``, overhang ``b`` — with dead load on all three and live load
on every one of the eight subsets of them (ASCE 7-16 §4.3.3 partial loading): live on the
back span alone is what maximises its sag and positive moment, live on one overhang and the
span what maximises that support's reaction. Oracle: ``notes/balcony_moment_columns.md`` §5b.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product

_STEPS = 4000  # grid intervals over the whole length; the O(h^2) error is < 1e-6 relative


@dataclass(frozen=True)
class Envelope:
    """Worst values over every live pattern. Forces lb, moments lb-ft, deflections in."""

    reactions_lb: tuple[float, float]   # max downward reaction at each support
    min_reaction_lb: float              # < 0 is uplift at a support
    moment_lb_ft: float                 # max |M|
    shear_at_d_lb: float                # max |V| at d from a support face (NDS §3.4.3.1(a))
    span_deflection_in: float           # live only, max sag between the supports
    tip_deflection_in: tuple[float, float]  # live only, max downward at each overhang tip


def _state(loads: tuple[float, float, float], a: float, s: float, b: float):  # type: ignore[no-untyped-def]
    """``(R1, R2, V(x), M(x))`` for one pattern; x from the ``a`` tip, supports at a, a+s."""
    x1, x2, length = a, a + s, a + s + b
    segs = ((0.0, x1, loads[0]), (x1, x2, loads[1]), (x2, length, loads[2]))
    total = sum(w * (hi - lo) for lo, hi, w in segs)
    moment_x1 = sum(w * (hi - lo) * ((lo + hi) / 2.0 - x1) for lo, hi, w in segs)
    r2 = moment_x1 / s
    r1 = total - r2

    def shear(x: float) -> float:
        v = (r1 if x > x1 else 0.0) + (r2 if x > x2 else 0.0)
        return v - sum(w * (min(x, hi) - lo) for lo, hi, w in segs if x > lo)

    def moment(x: float) -> float:
        m = (r1 * (x - x1) if x > x1 else 0.0) + (r2 * (x - x2) if x > x2 else 0.0)
        return m - sum(w * ((x - lo) ** 2 - (x - min(x, hi)) ** 2) / 2.0
                       for lo, hi, w in segs if x > lo)

    return r1, r2, shear, moment


def _deflections(loads: tuple[float, float, float], a: float, s: float, b: float,
                 ei_lb_in2: float) -> tuple[float, float, float]:
    """``(max span sag, tip a, tip b)`` in inches, downward positive, by double integration."""
    _r1, _r2, _v, moment = _state(loads, a, s, b)
    length = a + s + b
    h = length / _STEPS
    xs = [i * h for i in range(_STEPS + 1)]
    # EI y_up'' = M (sagging positive), in inches; flipped to downward below
    curv = [moment(x) * 12.0 / ei_lb_in2 for x in xs]
    h_in = h * 12.0
    slope, y = [0.0], [0.0]
    for i in range(1, len(xs)):
        slope.append(slope[-1] + (curv[i - 1] + curv[i]) * h_in / 2.0)
        y.append(y[-1] + (slope[i - 1] + slope[i]) * h_in / 2.0)
    i1, i2 = round(a / h), round((a + s) / h)
    # add c0 + c1 x so y = 0 at both supports
    c1 = -(y[i2] - y[i1]) / ((xs[i2] - xs[i1]) * 12.0)
    c0 = -y[i1] - c1 * xs[i1] * 12.0

    def fixed(i: int) -> float:
        return -(y[i] + c0 + c1 * xs[i] * 12.0)   # flip so downward is positive

    sag = max(fixed(i) for i in range(i1, i2 + 1))
    return sag, fixed(0), fixed(_STEPS)


def envelope(a_ft: float, s_ft: float, b_ft: float, dead_plf: float, live_plf: float,
             ei_lb_in2: float, d_ft: float) -> Envelope:
    """Envelope over the eight live patterns. ``a``/``b`` may be 0 (a simple span)."""
    x1, x2, length = a_ft, a_ft + s_ft, a_ft + s_ft + b_ft
    grid = [length * i / _STEPS for i in range(_STEPS + 1)]
    faces = [x for x in (x1 - d_ft, x1 + d_ft, x2 - d_ft, x2 + d_ft) if 0.0 < x < length]
    r_max = [0.0, 0.0]
    r_min = float("inf")
    m_max = v_max = sag = 0.0
    tips = [0.0, 0.0]
    for pattern in product((0.0, 1.0), repeat=3):
        loads = tuple(dead_plf + live_plf * on for on in pattern)
        r1, r2, shear, moment = _state(loads, a_ft, s_ft, b_ft)  # type: ignore[arg-type]
        r_max = [max(r_max[0], r1), max(r_max[1], r2)]
        r_min = min(r_min, r1, r2)
        m_max = max(m_max, max(abs(moment(x)) for x in grid))
        v_max = max([v_max, *(abs(shear(x)) for x in faces)])
        live = tuple(live_plf * on for on in pattern)
        if any(live):
            span, tip_a, tip_b = _deflections(live, a_ft, s_ft, b_ft, ei_lb_in2)  # type: ignore[arg-type]
            sag = max(sag, span)
            tips = [max(tips[0], tip_a), max(tips[1], tip_b)]
    return Envelope(reactions_lb=(r_max[0], r_max[1]), min_reaction_lb=r_min,
                    moment_lb_ft=m_max, shear_at_d_lb=v_max, span_deflection_in=sag,
                    tip_deflection_in=(tips[0], tips[1]))
