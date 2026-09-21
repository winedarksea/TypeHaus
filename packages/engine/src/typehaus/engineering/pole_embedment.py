"""IBC 2018 §1807.3.2.1's non-constrained embedment, and the same formula on a STEPPED pole.

A cast column doweled into a monolithic pad is one rigid body: shaft from grade to the pad
top, then the pad. The code formula knows one width ``b``. Rather than bolt a second
resisting moment onto its answer (``d`` is a depth, not a moment), the stepped pole is fed
to the UNMODIFIED formula through an effective width, computed in the formula's own
pressure field: a rigid pole pivoting at ``γd`` under a pressure ``k z b(z)``, moments about
the pivot, the pressure below it neglected —

    P (h + γd) = ∫₀^{γd} k z b(z) (γd − z) dz  =  k b_eff γ³d³ / 6   for b(z) ≡ b_eff

so ``b_eff = ∫₀^{γd} z b(z) (γd − z) dz / (γ³d³/6)``. With ``b(z) ≡ b`` that is ``b``
identically, for any γ — :func:`effective_width_ft` returns it exactly and the stepped
solve returns the code's own number bit for bit. γ scales only the credit.

**The band on γ is the code's own inconsistency.** Eq. 18-1 rearranges to
``s b d³ = 7.02 P (d + 1.09 h)``; matching the pivot model's ``d`` coefficient (``6/γ² =
3 × 2.34``) gives γ = 0.92450, matching the ratio of its two terms (``γ = 4/4.36``) gives
0.91743. Both ends are run and a verdict is published only where they agree.

**Oracle.** ``houses/catlin/notes/entry_column_base_fixity.md`` §9, hand-worked separately.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

#: The two pivot ratios Eq. 18-1 implies: its ``4.36`` term, and its ``2.34`` term.
PIVOT_RATIO_BAND = (4.0 / 4.36, math.sqrt(6.0 / (3.0 * 2.34)))


def required_embedment_ft(shear_lb: float, height_ft: float, diameter_ft: float,
                          lateral_psf_per_ft: float) -> float:
    """IBC 2018 §1807.3.2.1, the non-constrained case, solved for ``d``.

    ``A = 2.34 P / (S1 b)`` and ``d = 0.5 A [1 + sqrt(1 + 4.36 h / A)]``, with ``S1`` the
    allowable lateral bearing at ``d/3`` — so the pair is a fixed point, not a closed form.
    ``P`` and ``h`` at ALLOWABLE stress: §1806.2's lateral bearing is an allowable.
    """
    if shear_lb <= 0.0 or diameter_ft <= 0.0 or lateral_psf_per_ft <= 0.0:
        return 0.0
    depth = 1.0
    for _ in range(60):
        s1 = lateral_psf_per_ft * depth / 3.0
        a = 2.34 * shear_lb / (s1 * diameter_ft)
        nxt = 0.5 * a * (1.0 + math.sqrt(1.0 + 4.36 * max(height_ft, 0.0) / a))
        if abs(nxt - depth) < 1e-9:
            return nxt
        depth = nxt
    return depth


def effective_width_ft(depth_ft: float, shaft_ft: float, pad_ft: float, pad_thickness_ft: float,
                       pivot_ratio: float) -> float:
    """``b_eff`` of a pole ``shaft_ft`` wide to ``depth - t`` and ``pad_ft`` wide below.

    Written as ``b + (B − b) F`` so a constant width returns ``b`` exactly — the oracle
    property is algebraic and is tested as equality.
    """
    pivot = pivot_ratio * depth_ft
    top = max(depth_ft - pad_thickness_ft, 0.0)
    if pad_ft == shaft_ft or pivot <= top or pivot <= 0.0:
        return shaft_ft

    def lever(z: float) -> float:        # ∫ z (L − z) dz
        return pivot * z * z / 2.0 - z ** 3 / 3.0

    fraction = (lever(pivot) - lever(top)) / (pivot ** 3 / 6.0)
    return shaft_ft + (pad_ft - shaft_ft) * fraction


def required_embedment_stepped_ft(shear_lb: float, height_ft: float, shaft_ft: float,
                                  pad_ft: float, pad_thickness_ft: float,
                                  lateral_psf_per_ft: float, pivot_ratio: float) -> float:
    """The required TOTAL embedment (grade to pad bottom) of a shaft on a monolithic pad.

    The pad keeps the bottom ``t`` of whatever depth is tried, so ``b_eff`` moves with ``d``
    and the pair is iterated; each pass is the unmodified code formula.
    """
    depth = required_embedment_ft(shear_lb, height_ft, shaft_ft, lateral_psf_per_ft)
    for _ in range(200):
        width = effective_width_ft(depth, shaft_ft, pad_ft, pad_thickness_ft, pivot_ratio)
        nxt = required_embedment_ft(shear_lb, height_ft, width, lateral_psf_per_ft)
        if abs(nxt - depth) < 1e-9:
            return nxt
        depth = nxt
    return depth


@dataclass(frozen=True)
class Pole:
    """A column's buried pole: its shaft, and its pad where the pad is earned as part of it."""

    pad_tag: str
    shaft_ft: float
    thickness_ft: float
    width_ft: float | None
    width_how: str
    #: ``None`` = the pad is credited. Otherwise why it is not, and the shaft stands alone.
    refusal: str | None
    anchorage_ratio: float | None = None

    @property
    def credited(self) -> bool:
        return self.refusal is None

    def needs(self, shear_lb: float, height_ft: float,
              lateral: float) -> tuple[float, ...]:
        """The required embedment at each end of :data:`PIVOT_RATIO_BAND`."""
        if not self.credited or self.width_ft is None:
            one = required_embedment_ft(shear_lb, height_ft, self.shaft_ft, lateral)
            return tuple(one for _ in PIVOT_RATIO_BAND)
        return tuple(required_embedment_stepped_ft(
            shear_lb, height_ft, self.shaft_ft, self.width_ft, self.thickness_ft, lateral, g)
            for g in PIVOT_RATIO_BAND)

    def b_eff(self, depth_ft: float, pivot: float) -> float:
        if not self.credited or self.width_ft is None:
            return self.shaft_ft
        return effective_width_ft(depth_ft, self.shaft_ft, self.width_ft, self.thickness_ft,
                                  pivot)

    def citation(self, depth_ft: float, pivot: float) -> str:
        if not self.credited:
            return ", the shaft alone — the pad is not credited as part of the pole"
        lo, hi = PIVOT_RATIO_BAND
        return (f", with {self.pad_tag} credited as part of the pole to its BOTTOM: b_eff "
                f"{self.b_eff(depth_ft, pivot):.3f}' ({self.width_ft:.2f}' of pad over its "
                f"{self.thickness_ft:.2f}') at pivot ratio {pivot:.5f}, the worse end of "
                f"Eq. 18-1's {lo:.5f}-{hi:.5f}")

    def note(self, grade_ft: float, top_ft: float, shaft_ft: float, total_ft: float,
             depth_ft: float, pivot: float | None) -> str:
        if not self.credited:
            return (f"EMBEDMENT is measured from Site.grade ({grade_ft:+.2f}') to the TOP of "
                    f"{self.pad_tag} ({top_ft:+.2f}'), {shaft_ft:.2f}'. The pad is NOT "
                    f"counted as part of the pole: {self.refusal}.")
        b_eff = self.b_eff(depth_ft, pivot if pivot is not None else PIVOT_RATIO_BAND[0])
        return (
            f"EMBEDMENT runs from Site.grade ({grade_ft:+.2f}') to the BOTTOM of "
            f"{self.pad_tag} ({top_ft - self.thickness_ft:+.2f}'), {total_ft:.2f}': the pad "
            f"is part of the pole — one placement with the shaft, its dowels developed into "
            f"it (`deck_post` dowel anchorage, d/c {self.anchorage_ratio:.2f}) — and enters "
            f"§1807.3.2.1 as an effective width, {self.width_ft:.2f}' ({self.width_how}) "
            f"over its {self.thickness_ft:.2f}'. b_eff is {b_eff:.3f}': the pad's WIDTH is "
            f"worth {100 * (b_eff / self.shaft_ft - 1):.1f}%, and nearly all it adds is its "
            f"DEPTH. `h` is still measured from grade, off the SHAFT's own {shaft_ft:.2f}' "
            f"(grade to pad top). This makes the pad part of the pole; it does not divide "
            f"the base moment between a shaft and a pad — see NOT GRADED.")


def verdict(ends: tuple[float, ...], capacity_ft: float) -> bool | None:
    """``True``/``False`` where every pivot end agrees, ``None`` where the band straddles."""
    passes = {need <= capacity_ft for need in ends}
    return passes.pop() if len(passes) == 1 else None


def band_straddle(ends: tuple[float, ...], capacity_ft: float, where: str) -> str:
    lo, hi = PIVOT_RATIO_BAND
    return (f"a pivot ratio: at {where} the embedment needs {ends[0]:.2f}' at γ {lo:.5f} and "
            f"{ends[1]:.2f}' at γ {hi:.5f} — the two ends of the band Eq. 18-1 itself implies "
            f"— against {capacity_ft:.2f}', so the verdict turns on which reading of the "
            f"code formula is right")
