"""The STIFFNESS of a fixed cast-column base, and the sway it adds — ``base_rotation/<post>``.

``column_base`` grades whether the ground can turn a column's shear around (strength).
``deck_post`` magnifies the column's moment for sway at ACI Table R6.2.5's ``k = 2.1`` — a
base that does not rotate. This grades the base that does, as its own record, and cites
``deck_post``'s numbers as the rigid-base bound without touching them.

**Two bases, one column model.** A cast column on a base spring of stiffness ``k_θ``:
``R = k_θ L / EI``; ``P_cr,flex = P_cr,rigid · Δ_flex/Δ_total = P_cr,rigid / (1 + 3/R)``
(graded — it keeps ``deck_post``'s 2.1 as the rigid end); the exact spring root
``(μL) tan(μL) = R`` is printed beside it and is always the less conservative of the two.
Then ACI 318-19 §6.6.4.5.2's ``δ`` and §6.2.5.3's ceiling of 1.4 on second-order moment.

* **A pad-borne column** (``column_base``'s set): the shaft from grade and the pad under it
  are one RIGID POLE on a Winkler profile ``p = n_h z u b`` (``base_spring.winkler_pole``),
  ``k_θ = L² / Δ_base`` at the column head. The pad counts only while ``deck_post`` grades
  the dowels into it as developed — the claim that makes shaft and pad one body.
* **A wall-borne column**: the wall is held at its head by the declared diaphragm and
  stands on a strip footing rocking on the subgrade; ``k_θ`` is the wall top's rotational
  stiffness over a strip no wider than the column (no spread credited).

**The soil is a band unless a report says otherwise.** ``Site.lateral_subgrade_modulus``
present → graded at it. Absent → ``n_h = 2 S1 / δ_ref`` (IBC §1806.3.4 pairs twice the
tabular lateral bearing with the motion at grade) and ``k_v = q_a / δ_ref``, run at both ends
of ``soil.MOTION_AT_ALLOWABLE_BAND_IN``; the verdict publishes only where both agree.

**Oracle.** ``houses/catlin/notes/column_base_rotation.md``, hand-worked in a separate pass;
``tests/test_base_rotation_calcs.py`` reproduces it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.engineering import base_spring as spring
from typehaus.engineering.base_supports import PoleBase, WallBase, measured
from typehaus.engineering.item import (
    EngineeringRecord,
    LimitState,
    Oracle,
    Quantity,
    Status,
    item_id,
)
from typehaus.engineering.pier_basis import _Pier, cast_piers
from typehaus.engineering.registry import EngineeringContext, calc, keys, oracled_by
from typehaus.engineering.soil import (
    MOTION_AT_ALLOWABLE_BAND_IN,
    MOTION_AT_ALLOWABLE_SENSITIVITY_IN,
)

KIND = "base_rotation"
BASIS = ("ACI 318-19 §6.6.4.5.2 and §6.2.5.3 on a base spring; a rigid pole on a Winkler "
         "profile anchored on IBC 2018 §1806.3.4; ACI 318-19 Table 6.6.3.1.1(a) for a wall")
#: 1: the kind as introduced, 2026-09-20.
BASIS_VERSION = "1"

#: ACI 318-19 §6.2.5.3 — Mu including second-order effects may not exceed 1.4 Mu first-order.
MOMENT_RATIO_LIMIT = 1.4

oracled_by(KIND, Oracle(note="column_base_rotation.md", test="tests/test_base_rotation_calcs.py"))


def _pole_tags(ctx: EngineeringContext) -> list[str]:
    from typehaus.engineering.column_base import enumerate_column_bases

    return enumerate_column_bases(ctx)


def _wall_borne(ctx: EngineeringContext) -> list[_Pier]:
    return [p for p in cast_piers(ctx) if p.lateral_system and p.base_kind == "wall"]


@keys(KIND)
def enumerate_base_rotations(ctx: EngineeringContext) -> list[str]:
    """``column_base``'s own set, plus every wall-borne lateral-system column."""
    return sorted(set(_pole_tags(ctx)) | {p.tag for p in _wall_borne(ctx)})


@calc(KIND)
def compute(ctx: EngineeringContext) -> list[EngineeringRecord]:
    poles = set(_pole_tags(ctx))
    out = []
    for pier in sorted(cast_piers(ctx), key=lambda p: p.tag):
        if pier.tag in poles:
            out.append(_record(ctx, pier, PoleBase.build(ctx, pier)))
        elif pier.lateral_system and pier.base_kind == "wall":
            out.append(_record(ctx, pier, WallBase.build(ctx, pier)))
    return out


# --- the column --------------------------------------------------------------------------

@dataclass(frozen=True)
class _Column:
    """``deck_post``'s own column, read through its own functions: the rigid-base bound."""

    length_in: float
    ei_lb_in2: float
    pu_lb: float
    mu_lb_ft: float
    phi_mn_lb_ft: float
    pc_rigid_lb: float

    @classmethod
    def of(cls, pier: _Pier) -> _Column | None:
        from typehaus.engineering import deck_post as dp

        cage = dp.cage_for(pier)
        if cage is None or pier.height_in <= 0.0 or pier.factored_lb <= 0.0:
            return None
        # Verbatim `deck_post._sway_magnifier`'s EI and P_c, so R -> inf returns its delta.
        modulus = 57_000.0 * math.sqrt(dp._fc_psi(pier))
        inertia = math.pi * pier.diameter_in ** 4 / 64.0
        ei = 0.4 * modulus * inertia / (1.0 + 1.2 * pier.dead_lb / pier.factored_lb)
        effective = dp.CANTILEVER_EFFECTIVE_LENGTH_FACTOR * pier.height_in
        mu = max(pier.wind_base_moment_lb_ft * dp.STRENGTH_FROM_ASD_WIND,
                 pier.guard_base_moment_lb_ft * dp.GUARD_LOAD_FACTOR)
        phi_mn = dp._pm_point(pier, cage, dp._cover_in(pier), pier.factored_lb)[0]
        return cls(pier.height_in, ei, pier.factored_lb, mu, phi_mn,
                   math.pi ** 2 * ei / effective ** 2)


@dataclass(frozen=True)
class _Point:
    """The column graded on one base stiffness."""

    label: str
    k_theta_lb_in: float
    r: float
    pc_flex_lb: float
    k_exact: float
    delta: float | None

    @classmethod
    def at(cls, label: str, column: _Column, k_theta: float) -> _Point:
        r = k_theta * column.length_in / column.ei_lb_in2
        k_exact = spring.spring_cantilever_k(r)
        pc_exact = math.pi ** 2 * column.ei_lb_in2 / (k_exact * column.length_in) ** 2
        # The plan's series form is graded; it is the smaller of the two by construction,
        # and `min` keeps that true if either formula is ever changed.
        pc = min(column.pc_rigid_lb * spring.series_ratio(r), pc_exact)
        return cls(label, k_theta, r, pc, k_exact, spring.magnifier(column.pu_lb, pc))

    def states(self, column: _Column) -> tuple[LimitState, ...]:
        where = f"at {self.label}, R = k_θL/EI {self.r:.3f}"
        states = [LimitState(
            "sway stability, flexible base", column.pu_lb, 0.75 * self.pc_flex_lb, "lb",
            f"ACI 318-19 §6.6.4.5.2: Pu < 0.75 Pc, Pc = {column.pc_rigid_lb:,.0f} lb at "
            f"deck_post's k 2.1 x 1/(1 + 3/R) {where}")]
        if self.delta is not None:
            states += [
                # The INCREMENT over first order, so a column at delta 1.0 reads 0.00, not
                # 0.71 — the limit is "at most 40% more", and that is what is graded.
                LimitState("second-order increment", self.delta - 1.0,
                           MOMENT_RATIO_LIMIT - 1.0, "",
                           f"ACI 318-19 §6.2.5.3 — Mu with second-order effects at most "
                           f"{MOMENT_RATIO_LIMIT} Mu first-order; delta {self.delta:.3f} {where}"),
                LimitState("magnified moment (sway), flexible base",
                           column.mu_lb_ft * self.delta, column.phi_mn_lb_ft, "lb-ft",
                           f"ACI 318-19 §6.6.4.5.2 delta {self.delta:.3f} on deck_post's "
                           f"governing Mu {column.mu_lb_ft:,.0f} lb-ft {where}")]
        return tuple(states)

    def ok(self, column: _Column) -> bool:
        return all(s.ok for s in self.states(column))

    def says(self) -> str:
        what = (f"delta {self.delta:.3f}" if self.delta is not None
                else "a MECHANISM (Pu >= 0.75 Pc)")
        return (f"{self.label}: k_θ {self.k_theta_lb_in:,.3g} lb-in/rad, R {self.r:.3f}, "
                f"Pc {self.pc_flex_lb:,.0f} lb (exact spring k {self.k_exact:.2f}), {what}")


# --- the soil ----------------------------------------------------------------------------

def _moduli(ctx: EngineeringContext) -> list[tuple[str, float | None]]:
    """``(label, δ_ref in or None for measured)`` — stiff end first."""
    if measured(ctx) is not None:
        return [("the measured modulus", None)]
    return [(f"δ_ref {d:g}\"", d) for d in MOTION_AT_ALLOWABLE_BAND_IN]


# --- the record --------------------------------------------------------------------------

def _record(ctx: EngineeringContext, pier: _Pier, base) -> EngineeringRecord:  # type: ignore[no-untyped-def]
    ident = item_id(KIND, pier.tag)
    column = _Column.of(pier)
    missing = list(base.missing)
    if column is None:
        missing.append("a column deck_post grades in bending — a cage, a height and a load")
    if missing:
        return EngineeringRecord(
            item_id=ident, kind=KIND, key=pier.tag, basis_version=BASIS_VERSION, basis=BASIS,
            status=Status.INCOMPLETE, summary=f"{pier.tag}: the base spring could not be formed",
            missing=tuple(missing), element_tags=base.tags)

    points = [(d, _Point.at(label, column, base.k_theta(ctx, d, column)))
              for label, d in _moduli(ctx)]
    verdicts = [p.ok(column) for _d, p in points]
    rigid = spring.magnifier(column.pu_lb, column.pc_rigid_lb) or math.inf
    report = measured(ctx)
    # Publish the end that makes the verdict robust: the soft end of a pass, the stiff end
    # of a failure. A straddle publishes neither.
    if all(verdicts) or not any(verdicts):
        graded_d, graded = points[-1] if all(verdicts) else points[0]
    else:
        graded_d, graded = points[-1]
    turn = _turning_point(ctx, base, column) if report is None else None
    notes = list(base.notes) + [
        (f"THE SOIL IS MEASURED: {report.n_h_pci:g} pci n_h"
         f"{'' if report.k_v_pci is None else f', {report.k_v_pci:g} pci k_v'} from "
         f"{report.source} ({report.basis}). A measured modulus governs, and no band "
         f"is run." if report is not None else
         "THE SOIL IS PRESUMPTIVE: no geotechnical report is on file, so the modulus is "
         "anchored on the code — n_h = 2 S1 / δ_ref (IBC §1806.3.4 pairs twice Table "
         "1806.2's lateral bearing with the motion at grade) and k_v = q_a / δ_ref — and "
         f"run at δ_ref {MOTION_AT_ALLOWABLE_BAND_IN[0]:g}\" and "
         f"{MOTION_AT_ALLOWABLE_BAND_IN[1]:g}\". `Site.lateral_subgrade_modulus` is where "
         "a report's value goes, and it re-grades this with no code change."),
        f"THE RIGID-BASE BOUND is deck_post's: Pc {column.pc_rigid_lb:,.0f} lb at k 2.1, "
        f"delta {rigid:.3f}, Mu {column.mu_lb_ft:,.0f} lb-ft on phi*Mn "
        f"{column.phi_mn_lb_ft:,.0f} lb-ft. Those numbers are not changed here.",
        "BOTH BAND ENDS: " + "; ".join(p.says() for _d, p in points) + ".",
        base.evidence(ctx, graded_d, column, graded.label),
    ]
    if report is None:
        sens = _Point.at(f"δ_ref {MOTION_AT_ALLOWABLE_SENSITIVITY_IN:g}\"", column,
                         base.k_theta(ctx, MOTION_AT_ALLOWABLE_SENSITIVITY_IN, column))
        notes.append(f"SENSITIVITY, never a band end — {sens.says()}. "
                     + (f"The verdict turns at δ_ref ≈ {turn:.2f}\"." if turn else
                        "The verdict does not turn anywhere from 0.05\" to 20\"."))
    notes.append(base.not_graded)

    inputs = (
        Quantity("column_height", column.length_in, "in", 0.125),
        Quantity("column_EI", column.ei_lb_in2, "lb-in2", 1e6),
        Quantity("factored_axial", column.pu_lb, "lb", 1.0),
        Quantity("governing_Mu", column.mu_lb_ft, "lb-ft", 1.0),
        Quantity("phi_Mn", column.phi_mn_lb_ft, "lb-ft", 1.0),
        Quantity("Pc_rigid", column.pc_rigid_lb, "lb", 1.0),
        Quantity("subgrade_modulus_pci", base.modulus_pci(ctx, graded_d), "pci", 0.001),
        Quantity("subgrade_modulus_measured", 1.0 if report is not None else 0.0, "-", 0.5),
        Quantity("base_spring", graded.k_theta_lb_in, "lb-in/rad", 1e3),
        Quantity("spring_ratio_R", graded.r, "-", 0.001),
        Quantity("Pc_flexible", graded.pc_flex_lb, "lb", 1.0),
        *base.inputs(),
    )
    common = dict(item_id=ident, kind=KIND, key=pier.tag, basis_version=BASIS_VERSION,
                  basis=BASIS, inputs=inputs, element_tags=base.tags)
    if not (all(verdicts) or not any(verdicts)):
        stiff, soft = points[0][1], points[-1][1]
        return EngineeringRecord(
            **common, status=Status.INCOMPLETE, notes=tuple(notes),
            summary=f"{pier.tag}: the base's stiffness decides the sway verdict, and the "
                    f"presumptive band straddles it",
            missing=(f"a measured subgrade modulus (`Site.lateral_subgrade_modulus`): the "
                     f"sway verdict turns inside the presumptive band — {stiff.says()} "
                     f"passes; {soft.says()} does not"
                     + (f"; it turns at δ_ref ≈ {turn:.2f}\"" if turn else "")
                     + ". A geotechnical report closes it, and so does a stiffer base.",))
    states = graded.states(column)
    worst = max(states, key=lambda s: s.ratio)
    return EngineeringRecord(
        **common, status=Status.OK if all(verdicts) else Status.OVER,
        limit_states=states, notes=tuple(notes),
        summary=(f"{pier.tag}: the fixed base as a SPRING — R {graded.r:.2f} at "
                 f"{graded.label}; {worst.name} governs at {worst.ratio:.2f}"))


def _turning_point(ctx: EngineeringContext, base, column: _Column) -> float | None:  # type: ignore[no-untyped-def]
    """The δ_ref at which the verdict turns, by bisection, or ``None`` if it never does."""
    def ok(d: float) -> bool:
        return _Point.at("", column, base.k_theta(ctx, d, column)).ok(column)

    low, high = 0.05, 20.0
    if ok(low) == ok(high):
        return None
    for _ in range(40):
        mid = 0.5 * (low + high)
        low, high = (mid, high) if ok(mid) else (low, mid)
    return 0.5 * (low + high)
