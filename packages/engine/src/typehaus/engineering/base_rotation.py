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
with an ``n_h`` → graded at it, at unit width (Terzaghi); a ``presumed`` one (a published
table row) grades as draft and says so, and the gap register keeps it open for a report.
Absent → ``n_h = 2 S1 / δ_ref`` (IBC §1806.3.4 pairs twice the tabular lateral bearing with
the motion at grade) and ``k_v = q_a / δ_ref``, run at both ends
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
#: 1: the kind as introduced, 2026-09-20. 2: a stated n_h (report or presumed table row)
#: is Terzaghi's, width-independent — the pole is integrated at 1 ft (2026-09-21).
#: 3: 2026-11-23 (review B-04): the flexible-base delta magnifies EVERY §2.3.1 pair
#: ``deck_post`` grades, each against its own phi*Mn, and the worst is reported; before it
#: magnified the larger of the two service moments at the factored axial.
BASIS_VERSION = "3"

#: ACI 318-19 §6.2.5.3 — Mu including second-order effects may not exceed 1.4 Mu first-order.
MOMENT_RATIO_LIMIT = 1.4

oracled_by(KIND, Oracle(note="column_base_rotation.md", test="tests/test_base_rotation_calcs.py"))


def _pole_tags(ctx: EngineeringContext) -> list[str]:
    """``column_base``'s set less the short poles under PINNED posts: a second-order sway
    increment is a moment column's question, and a pier under a post base has no head
    moment for P-delta to magnify (``notes/canopy_garage_diaphragm.md`` §6)."""
    from typehaus.engineering.column_base import enumerate_column_bases

    pinned = {p.tag for p in cast_piers(ctx) if p.pinned_head is not None}
    return [tag for tag in enumerate_column_bases(ctx) if tag not in pinned]


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
class _Case:
    """One ASCE 7-16 §2.3.1 pair ``deck_post`` grades: its axial, first-order moment, phi*Mn."""

    label: str
    pu_lb: float
    mu_lb_ft: float
    phi_mn_lb_ft: float


@dataclass(frozen=True)
class _Column:
    """``deck_post``'s own column, read through its own functions: the rigid-base bound."""

    length_in: float
    ei_lb_in2: float
    pu_lb: float
    mu_lb_ft: float
    phi_mn_lb_ft: float
    pc_rigid_lb: float
    cases: tuple[_Case, ...] = ()

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
        wind_mu = pier.wind_base_moment_lb_ft * dp.STRENGTH_FROM_ASD_WIND
        guard_mu = pier.guard_base_moment_lb_ft * dp.GUARD_LOAD_FACTOR
        cover = dp._cover_in(pier)
        cases = tuple(_Case(c.label, c.axial_lb, c.moment_lb_ft,
                            dp._pm_point(pier, cage, cover, c.axial_lb)[0])
                      for c in dp._combinations(pier, wind_mu, guard_mu) if c.moment_lb_ft > 0.0)
        first = max(cases, key=lambda c: c.mu_lb_ft / c.phi_mn_lb_ft, default=None)
        mu = first.mu_lb_ft if first else max(wind_mu, guard_mu)
        phi_mn = first.phi_mn_lb_ft if first else dp._pm_point(
            pier, cage, cover, pier.factored_lb)[0]
        return cls(pier.height_in, ei, pier.factored_lb, mu, phi_mn,
                   math.pi ** 2 * ei / effective ** 2, cases)


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
            worst = max(column.cases, key=lambda c: self._ratio(c), default=None)
            states += [
                # The INCREMENT over first order, so a column at delta 1.0 reads 0.00, not
                # 0.71 — the limit is "at most 40% more", and that is what is graded.
                LimitState("second-order increment", self.delta - 1.0,
                           MOMENT_RATIO_LIMIT - 1.0, "",
                           f"ACI 318-19 §6.2.5.3 — Mu with second-order effects at most "
                           f"{MOMENT_RATIO_LIMIT} Mu first-order; delta {self.delta:.3f} {where}"),
            ]
            if worst is not None:
                delta = spring.magnifier(worst.pu_lb, self.pc_flex_lb)
                states.append(LimitState(
                    "magnified moment (sway), flexible base",
                    worst.mu_lb_ft * (delta or math.inf), worst.phi_mn_lb_ft, "lb-ft",
                    f"ACI 318-19 §6.6.4.5.2 delta {delta or math.inf:.3f} on EVERY §2.3.1 pair "
                    f"deck_post grades, each against its own phi*Mn, the worst reported: "
                    f"{worst.label} at Pu {worst.pu_lb:,.0f} lb, Mu {worst.mu_lb_ft:,.0f} "
                    f"lb-ft, phi*Mn {worst.phi_mn_lb_ft:,.0f} lb-ft {where}",
                    combination=f"ASCE 7-16 §2.3.1 {worst.label}"))
        return tuple(states)

    def _ratio(self, case: _Case) -> float:
        delta = spring.magnifier(case.pu_lb, self.pc_flex_lb)
        return case.mu_lb_ft * (delta or math.inf) / case.phi_mn_lb_ft

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
    report = measured(ctx)
    if report is not None:
        return [("the presumed n_h" if _presumed(report) else "the measured modulus", None)]
    return [(f"δ_ref {d:g}\"", d) for d in MOTION_AT_ALLOWABLE_BAND_IN]


def _k_theta(ctx: EngineeringContext, base, delta_in,  # type: ignore[no-untyped-def]
             column: _Column) -> float:
    """The base spring. A wall-borne column's stem is NOT held at its head for the E-W wind that
    governs: all four columns push both stems the same way, so the porch cannot prop either
    (`column_support`). The stem is then a FREE-TOP cantilever, ``EI/H`` in series with the
    footing's rocking: ``1 / (H/EI + 1/k_f)``. (`WallBase.k_theta` is the propped stem, 4EI/H and
    3EI/H, which a soil-propped stem has but a wind-loaded one does not.) A pole base is
    unchanged."""
    if not isinstance(base, WallBase):
        return base.k_theta(ctx, delta_in, column)
    return 1.0 / (base.height_in / base.ei_lb_in2 + 1.0 / base.footing_spring(ctx, delta_in))


def flexible_magnifier(ctx: EngineeringContext, pier: _Pier):  # type: ignore[no-untyped-def]
    """``Pu -> delta`` on the wall-borne column's own base spring, at the SOFT end of the
    presumptive band (the measured modulus where a report is on file); ``None`` where the
    spring cannot be formed. ``column_support`` grades its joint on this, not on the rigid
    base's 1.02 (review B-04)."""
    if not (pier.lateral_system and pier.base_kind == "wall"):
        return None
    column, base = _Column.of(pier), WallBase.build(ctx, pier)
    if column is None or base.missing:
        return None
    point = _Point.at("", column, _k_theta(ctx, base, _moduli(ctx)[-1][1], column))
    return lambda pu_lb: spring.magnifier(pu_lb, point.pc_flex_lb) or math.inf


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

    points = [(d, _Point.at(label, column, _k_theta(ctx, base, d, column)))
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
        (_stated_soil(report) if report is not None else
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
                         _k_theta(ctx, base, MOTION_AT_ALLOWABLE_SENSITIVITY_IN, column))
        notes.append(f"SENSITIVITY, never a band end — {sens.says()}. "
                     + (f"The verdict turns at δ_ref ≈ {turn:.2f}\"." if turn else
                        "The verdict does not turn anywhere from 0.05\" to 20\"."))
    if isinstance(base, WallBase):
        notes.append(
            "THE STEM IS FREE AT ITS TOP for the E-W wind that governs (`column_support`: all four "
            "columns push both stems the same way, so the porch cannot prop either): the spring "
            "is EI/H in series with the footing's rocking, 1 / (H/EI + 1/k_f), softer than the "
            "propped stem's 4EI/H and 3EI/H that the wall-top note below describes. The soil's "
            "own prop does not restrain a wind-loaded stem.")
    notes.append(base.not_graded)
    notes += _serviceability_notes(pier, column, graded)

    inputs = (
        Quantity("column_height", column.length_in, "in", 0.125),
        Quantity("column_EI", column.ei_lb_in2, "lb-in2", 1e6),
        Quantity("factored_axial", column.pu_lb, "lb", 1.0),
        Quantity("governing_Mu", column.mu_lb_ft, "lb-ft", 1.0),
        Quantity("phi_Mn", column.phi_mn_lb_ft, "lb-ft", 1.0),
        Quantity("Pc_rigid", column.pc_rigid_lb, "lb", 1.0),
        Quantity("subgrade_modulus_pci", base.modulus_pci(ctx, graded_d), "pci", 0.001),
        Quantity("subgrade_modulus_measured",
                 1.0 if report is not None and not _presumed(report) else 0.0, "-", 0.5),
        Quantity("n_h_presumed", 1.0 if report is not None and _presumed(report) else 0.0,
                 "-", 0.5),
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


def _serviceability_notes(pier: _Pier, column: _Column, graded: _Point) -> list[str]:
    """Head drift and the seismic statement (review B-12), and which Pc is graded (B-11)."""
    length = column.length_in

    def drift_in(shear_lb: float) -> float:
        # A cantilever column on the base spring: P L^3 / 3EI of bending + P L^2 / k_theta of
        # base rotation, the head's lateral movement under a SERVICE shear at the head.
        return (shear_lb * length ** 3 / (3.0 * column.ei_lb_in2)
                + shear_lb * length ** 2 / graded.k_theta_lb_in)

    guard = drift_in(200.0)
    wind_shear = pier.wind_head_shear_lb or (
        pier.wind_base_moment_lb_ft / (length / 12.0) if length else 0.0)
    wind = drift_in(wind_shear)
    return [
        f"HEAD DRIFT, service loads, flexible base: {guard:.3f}\" under the 200 lb guard load "
        f"(H/{length / guard:,.0f}) and {wind:.3f}\" under the {wind_shear:,.0f} lb ASD wind "
        f"shear at the head (H/{length / wind:,.0f}), by P L^3/3EI + P L^2/k_theta on the "
        f"authored EI and the graded spring; the movement gap to the house is in the "
        f"N-S direction, where the base is in-plane and stiffer still. No code drift limit is "
        f"applied: IRC R301 sets none for a deck column.",
        "SEISMIC: the lot is SDC A (`notes/balcony_moment_columns.md` §9), where ASCE 7-16 §11.7 "
        "sends the structure to §1.4's minimum lateral force 0.01 W — about 50 lb per column "
        "(§9 there) — against the wind and guard shears above; wind governs and no seismic "
        "case is graded.",
        "WHICH Pc IS GRADED: the series form Pc = Pc_rigid / (1 + 3/R), which keeps deck_post's "
        "k 2.1 as the rigid end and so counts the real-fixity allowance twice. The exact "
        f"flagpole-on-spring root (k {graded.k_exact:.2f}) is printed beside it and is the less "
        "conservative of the two; the conservative one is graded.",
    ]


def _presumed(report) -> bool:  # type: ignore[no-untyped-def]
    return getattr(report, "provenance", "measured") == "presumed"


def _stated_soil(report) -> str:  # type: ignore[no-untyped-def]
    k_v = "" if report.k_v_pci is None else f", {report.k_v_pci:g} pci k_v"
    head = (f"THE SOIL IS PRESUMED, NOT MEASURED: n_h {report.n_h_pci:g} pci{k_v} is a "
            f"published table row for the presumed soil — {report.source} ({report.basis}). "
            f"It grades this record as draft; a geotechnical report on this parcel confirms "
            f"or replaces it, and the gap register keeps that open."
            if _presumed(report) else
            f"THE SOIL IS MEASURED: {report.n_h_pci:g} pci n_h{k_v} from {report.source} "
            f"({report.basis}). A measured modulus governs, and no band is run.")
    return (head + " A stated n_h is Terzaghi's (k_h = n_h z / B): the reaction per unit "
            "length does not grow with width, so the pole is integrated at 1 ft and the pad "
            "earns no width credit.")


def _turning_point(ctx: EngineeringContext, base, column: _Column) -> float | None:  # type: ignore[no-untyped-def]
    """The δ_ref at which the verdict turns, by bisection, or ``None`` if it never does."""
    def ok(d: float) -> bool:
        return _Point.at("", column, _k_theta(ctx, base, d, column)).ok(column)

    low, high = 0.05, 20.0
    if ok(low) == ok(high):
        return None
    for _ in range(40):
        mid = 0.5 * (low + high)
        low, high = (mid, high) if ok(mid) else (low, mid)
    return 0.5 * (low + high)
