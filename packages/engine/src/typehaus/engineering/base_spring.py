"""The closed-form mechanics behind ``base_rotation`` — pure functions, no model reads.

Three pieces, each a textbook result, kept apart from the record-building so the hand note
(``notes/column_base_rotation.md``) can be checked against them term by term:

1. A RIGID POLE on a Winkler profile ``p(z) = n_h · z · u(z) · b(z)``, ``u = u0 − θ z`` —
   the pole's translation at grade and its rotation under a shear at a height. Two
   equilibrium equations, two unknowns, no iteration.
2. A CANTILEVER on a rotational base spring: ``(μL)·tan(μL) = R``, ``R = k_θ L / EI``,
   ``k = π / (μL)``. ``R → ∞`` returns the rigid 2.0.
3. A WALL TOP's rotational stiffness where the wall is held at its head and stands on a
   footing that rotates on the subgrade: ``4EI/H − (2EI/H)² / (4EI/H + k_f)``, which runs
   from ``3EI/H`` (pinned foot) to ``4EI/H`` (fixed foot).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

#: ``(top ft, bottom ft, width ft)`` bands below grade, top down.
Profile = tuple[tuple[float, float, float], ...]


@dataclass(frozen=True)
class PoleResponse:
    """A rigid pole's motion under one shear: translation AT GRADE and rotation."""

    u0_ft: float
    theta_rad: float

    def at_height_ft(self, height_ft: float) -> float:
        """Displacement ``height_ft`` above grade, ft."""
        return self.u0_ft + self.theta_rad * height_ft


def _moments(profile: Profile) -> tuple[float, float, float]:
    """``∫ b z dz``, ``∫ b z² dz``, ``∫ b z³ dz`` over the profile."""
    i1 = sum(b * (z1 ** 2 - z0 ** 2) / 2.0 for z0, z1, b in profile)
    i2 = sum(b * (z1 ** 3 - z0 ** 3) / 3.0 for z0, z1, b in profile)
    i3 = sum(b * (z1 ** 4 - z0 ** 4) / 4.0 for z0, z1, b in profile)
    return i1, i2, i3


def winkler_pole(n_h_lb_ft4: float, profile: Profile, shear_lb: float,
                 height_ft: float) -> PoleResponse | None:
    """Solve ``Σ H = 0`` and ``Σ M_grade = 0`` for ``(u0, θ)``.

    ``n_h`` is per foot of WIDTH (lb/ft⁴), the IBC §1807.3.2.1 convention: the reaction
    scales with ``b`` exactly as the code formula's does. Force balance
    ``n_h (u0 I1 − θ I2) = H``; moment about grade ``n_h (θ I3 − u0 I2) = H h``.
    """
    i1, i2, i3 = _moments(profile)
    det = i1 * i3 - i2 * i2
    if n_h_lb_ft4 <= 0.0 or det <= 0.0:
        return None
    u0 = shear_lb * (i3 + i2 * height_ft) / (n_h_lb_ft4 * det)
    theta = shear_lb * (i1 * height_ft + i2) / (n_h_lb_ft4 * det)
    return PoleResponse(u0, theta)


def spring_cantilever_k(r: float) -> float:
    """Effective length factor of a free-top cantilever on a base spring of ratio ``R``.

    ``(μL) tan(μL) = R`` has one root on ``(0, π/2)``; ``k = π/(μL)``. Bisection, because
    the left side is monotone there and a Newton step can leave the interval.
    """
    if r <= 0.0:
        return math.inf
    low, high = 0.0, math.pi / 2.0
    for _ in range(200):
        mid = 0.5 * (low + high)
        if mid * math.tan(mid) < r:
            low = mid
        else:
            high = mid
    return math.pi / (0.5 * (low + high))


def series_ratio(r: float) -> float:
    """``Δ_flex / Δ_total`` for a tip load on a cantilever whose base spring has ratio ``R``.

    ``Δ_flex = PL³/3EI`` and the base adds ``PL²/k_θ``, so the ratio is ``1 / (1 + 3/R)``.
    """
    return 0.0 if r <= 0.0 else 1.0 / (1.0 + 3.0 / r)


def magnifier(pu_lb: float, pc_lb: float) -> float | None:
    """ACI 318-19 §6.6.4.5.2's ``1 / (1 − Pu / 0.75 Pc)``, or ``None`` past instability."""
    if pc_lb <= 0.0 or pu_lb >= 0.75 * pc_lb:
        return None
    return max(1.0 / (1.0 - pu_lb / (0.75 * pc_lb)), 1.0)


def wall_top_stiffness(ei_lb_in2: float, height_in: float,
                       footing_spring_lb_in: float) -> float:
    """Rotational stiffness, lb-in/rad, at the head of a wall held against translation there.

    Near-end stiffness of a member whose far end sits on a rotational spring ``k_f``. The
    footing's spring is ``k_v · b · B³/12`` — a rigid strip rocking on the subgrade.
    """
    near = 4.0 * ei_lb_in2 / height_in
    carry = 2.0 * ei_lb_in2 / height_in
    return near - carry * carry / (near + max(footing_spring_lb_in, 0.0))
