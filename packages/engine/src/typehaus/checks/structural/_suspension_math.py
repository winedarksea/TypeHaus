"""The arithmetic of a hung seat's load path, in lb and inches. Oracled by the house's
``notes/hanging_seat_anchor.md``; ``structural.suspension_anchor`` reports it.

C_D = 1.0 throughout: the impact factor is already on the load.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

#: NDS 2018 Table 12.3.3B, ASTM A36 side plate (1.5 F_u = 1.5 x 58 ksi).
FES_A36_PSI = 87_000.0
#: NDS Appendix I / Table 12A footnote: bolt bending yield strength.
FYB_BOLT_PSI = 45_000.0


@dataclass(frozen=True)
class LimitState:
    name: str
    demand: float
    capacity: float
    unit: str

    @property
    def ratio(self) -> float:
        return self.demand / self.capacity

    def text(self) -> str:
        return (f"{self.name} {self.demand:,.{_places(self.unit)}f}/"
                f"{self.capacity:,.{_places(self.unit)}f} {self.unit} ({self.ratio:.2f})")


def _places(unit: str) -> int:
    return 3 if unit == "in" else 0


@dataclass(frozen=True)
class SimpleSpan:
    """A point load ``p`` at ``a`` from the left bearing of span ``span``, plus uniform ``w``,
    and any ``others`` (``(p, a)`` pairs) hung from the same line."""

    p: float      # lb
    a: float      # in
    span: float   # in
    w: float      # lb/in
    others: tuple[tuple[float, float], ...] = ()

    @property
    def loads(self) -> tuple[tuple[float, float], ...]:
        return ((self.p, self.a), *self.others)

    @property
    def reactions(self) -> tuple[float, float]:
        half = self.w * self.span / 2
        return (sum(p * (self.span - a) / self.span for p, a in self.loads) + half,
                sum(p * a / self.span for p, a in self.loads) + half)

    def moment_at(self, x: float) -> float:
        left, _ = self.reactions
        return left * x - self.w * x * x / 2 - sum(p * (x - a) for p, a in self.loads if x > a)

    def shear_at(self, x: float) -> tuple[float, float]:
        """Shear just left and just right of ``x``."""
        left, _ = self.reactions
        before = left - self.w * x - sum(p for p, a in self.loads if a < x - 1e-9)
        return before, before - sum(p for p, a in self.loads if abs(a - x) <= 1e-9)

    @property
    def max_moment(self) -> float:
        stations = [a for _, a in self.loads]
        if self.w > 0:  # each segment's shear zero, where it falls inside that segment
            edges = sorted({0.0, self.span, *stations})
            for lo, hi in zip(edges, edges[1:], strict=False):
                zero = lo + self.shear_at(lo)[1] / self.w
                if lo < zero < hi:
                    stations.append(zero)
        return max(self.moment_at(x) for x in stations)

    @property
    def shear_at_load(self) -> float:
        """The larger shear either side of ``p`` (NDS 3.4.3.3's V)."""
        return max(abs(v) for v in self.shear_at(self.a))


def point_deflection(p: float, a: float, span: float, e: float, b: float, d: float,
                     shear_k: float) -> float:
    """Deflection under ``p`` at its own station: bending P a^2 b^2 / (3 E I L) plus the
    published shear term, whose uniform form k W L^2 / (E b d) fixes kG = 1.5 E / k."""
    return deflection_at(((p, a),), a, span, e, b, d, shear_k)


def deflection_at(loads, x: float, span: float, e: float, b: float, d: float,
                  shear_k: float) -> float:
    """Deflection at ``x`` under every ``(p, a)`` point load, by superposition."""
    i = b * d ** 3 / 12
    total = 0.0
    for p, a in loads:
        near, far = (x, span - a) if x <= a else (span - x, a)
        total += p * far * near * (span * span - far * far - near * near) / (6 * e * i * span)
        total += p * far * near * shear_k / (1.5 * span * e * b * d)
    return total


def bolt_double_shear(diameter: float, main: float, side: float, g: float) -> tuple[float, str]:
    """NDS 2018 §12.3.1 yield limit Z, one bolt, double shear, steel side plates, load
    perpendicular to grain in the main member (theta = 90: K_theta 1.25). Returns (Z, mode)."""
    fem = 6100 * g ** 1.45 / math.sqrt(diameter)  # Table 12.3.3 footnote 2
    re = fem / FES_A36_PSI
    k_theta = 1.25
    k3 = -1 + math.sqrt(2 * (1 + re) / re + 2 * FYB_BOLT_PSI * (2 + re) * diameter ** 2
                        / (3 * fem * side ** 2))
    modes = {
        "Im": diameter * main * fem / (4 * k_theta),
        "Is": 2 * diameter * side * FES_A36_PSI / (4 * k_theta),
        "IIIs": 2 * k3 * diameter * side * fem / ((2 + re) * 3.2 * k_theta),
        "IV": 2 * diameter ** 2 / (3.2 * k_theta)
        * math.sqrt(2 * fem * FYB_BOLT_PSI / (3 * (1 + re))),
    }
    mode = min(modes, key=modes.get)
    return modes[mode], mode


def connection_shear(fv: float, b: float, d: float, bolt_diameter: float,
                     clear_of_ends: bool, top: float | None = None) -> tuple[float, float]:
    """NDS 2018 §3.4.3.3: V_r' = 2/3 F_v b d_e, d_e the depth less the unloaded (top) edge's
    distance to the bolt hole. ``top`` is the bolt row's centre below the top edge; ``None``
    is mid-depth. Returns (V_r', d_e); the (d_e/d)^2 penalty applies within 5d of an end."""
    de = d - ((d / 2 if top is None else top) - bolt_diameter / 2)
    vr = 2 / 3 * fv * b * de
    return (vr if clear_of_ends else vr * (de / d) ** 2), de
