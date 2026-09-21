"""The two bases ``base_rotation`` grades a column on, each read off the model as a spring.

* :class:`PoleBase` — a shaft and its pad as one rigid pole in the ground (Winkler).
* :class:`WallBase` — a wall held at its head, on a strip footing rocking on the subgrade.

Each answers ``k_theta(ctx, delta_ref, column)`` in lb-in/rad at the column's base, where
``delta_ref`` is a presumptive band point in inches or ``None`` for the measured modulus.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

from typehaus.engineering import base_spring as spring
from typehaus.engineering.item import Quantity
from typehaus.engineering.pier_basis import _Pier
from typehaus.engineering.registry import EngineeringContext
from typehaus.engineering.soil import MOTION_AT_ALLOWABLE_BAND_IN, presumptive

if TYPE_CHECKING:
    from typehaus.engineering.base_rotation import _Column

#: IBC §1806.3.4: TWICE the tabular lateral bearing is what the code pairs with the motion.
POLE_MOBILISED_FACTOR = 2.0
#: ACI 318-19 Table 6.6.3.1.1(a) — a CRACKED wall.
WALL_CRACKED_INERTIA = 0.35
PCI_PER_LB_FT3 = 1.0 / 1728.0


def measured(ctx: EngineeringContext):  # type: ignore[no-untyped-def]
    site = getattr(ctx.plan.project, "site", None)
    report = getattr(site, "lateral_subgrade_modulus", None)
    # A report stating only k_v (the thermal break's) leaves n_h on the presumptive band.
    return report if getattr(report, "n_h_pci", None) is not None else None


@dataclass(frozen=True)
class PoleBase:
    """A shaft and its pad as one rigid pole in the ground."""

    tags: tuple[str, ...]
    profile: spring.Profile           # least pad width — buckling picks its own axis
    motion_profile: spring.Profile    # pad width normal to the governing motion
    head_above_grade_ft: float
    s1: float
    shear: tuple[float, float] | None  # (P lb ASD, h above grade ft)
    missing: tuple[str, ...]
    notes: tuple[str, ...]

    @classmethod
    def build(cls, ctx: EngineeringContext, pier: _Pier) -> PoleBase:
        from typehaus.engineering import deck_post as dp
        from typehaus.engineering.roof_moment import base_axis_of, base_shear_of

        post = ctx.plan.by_tag(pier.tag)
        pad = ctx.plan.by_tag(getattr(post, "supported_by", "") or "")
        soil = presumptive(getattr(ctx, "soil_class", None))
        grade = getattr(getattr(ctx.plan.project, "site", None), "grade", None)
        bottom = getattr(pad, "bottom_elevation", None)
        thick = getattr(pad, "thickness", None) or getattr(pad, "depth", None)
        extents = _plan_extents(pad)
        missing = tuple(t for ok, t in (
            (soil is not None, "a declared soil class (Site/profile soil_class)"),
            (grade is not None, "Site.grade — the pole is measured from it"),
            (bottom is not None and thick is not None,
             "a bottom elevation and thickness on the pad this column stands on"),
            (extents is not None, "a resolvable plan outline on that pad"),
        ) if not ok)
        tags = tuple(t for t in (pier.tag, getattr(pad, "tag", None)) if t)
        if missing:
            return cls(tags, (), (), 0.0, 0.0, None, missing, ())
        grade_ft = float(grade.inches) / 12.0
        bottom_ft = float(bottom.inches) / 12.0
        shaft = grade_ft - (bottom_ft + float(thick.inches) / 12.0)
        total = grade_ft - bottom_ft
        if shaft <= 0.0:
            # Grade at or below the pad top: no buried shaft for the soil to hold, and the
            # 2x2 pole solve has no profile to integrate. Name it; never grade a guess.
            return cls(tags, (), (), 0.0, 0.0, None,
                       (f"a buried shaft — Site.grade stands {-shaft:.2f}' below the pad top",),
                       ())
        b = pier.diameter_in / 12.0
        axis = base_axis_of(pier.tag)
        normal = {"x": extents[1], "y": extents[0]}.get(axis or "", min(extents))
        cage = dp.cage_for(pier)
        anchor = dp._dowel_anchorage(pier, cage, dp._fc_psi(pier)) if cage else None
        notes = []
        if anchor is not None and anchor.ok:
            profile = ((0.0, shaft, b), (shaft, total, min(extents)))
            motion = ((0.0, shaft, b), (shaft, total, normal))
            notes.append(
                f"THE POLE is the shaft from grade to the pad top ({shaft:.2f}') and the "
                f"pad under it ({total - shaft:.2f}'), one rigid body because deck_post "
                f"grades the dowels developed into the pad (d/c {anchor.ratio:.2f}). "
                f"Buckling takes the pad's LEAST plan width ({min(extents):.2f}') — the "
                f"column picks its own axis; the motion below uses the width normal to "
                f"the governing case ({normal:.2f}').")
        else:
            profile = motion = ((0.0, shaft, b),)
            notes.append(
                f"THE PAD IS NOT COUNTED IN THE POLE: deck_post does not grade the dowels "
                f"into it as developed, so the shaft ({shaft:.2f}') stands alone.")
        shear = base_shear_of(pier.tag)
        return cls(tags, profile, motion, pier.height_in / 12.0 - shaft,
                   soil.lateral_bearing_psf_per_ft,
                   None if shear is None else (shear[0], shear[1] - shaft),
                   (), tuple(notes))

    def n_h(self, ctx: EngineeringContext, delta_in: float | None) -> float:
        """lb/ft⁴ per foot of width."""
        if delta_in is None:
            return float(measured(ctx).n_h_pci) / PCI_PER_LB_FT3  # type: ignore[union-attr]
        return POLE_MOBILISED_FACTOR * self.s1 / (delta_in / 12.0)

    def k_theta(self, ctx: EngineeringContext, delta_in: float | None, column: _Column
                ) -> float:
        pole = spring.winkler_pole(self.n_h(ctx, delta_in), self.profile, 1.0,
                                   self.head_above_grade_ft)
        tip_in = 12.0 * pole.at_height_ft(self.head_above_grade_ft)
        return column.length_in ** 2 / tip_in

    def modulus_pci(self, ctx: EngineeringContext, delta_in: float | None) -> float:
        return self.n_h(ctx, delta_in) * PCI_PER_LB_FT3

    def inputs(self) -> tuple[Quantity, ...]:
        return (Quantity("pole_depth", self.profile[-1][1], "ft", 0.01),
                Quantity("pole_toe_width", self.profile[-1][2], "ft", 0.01),
                Quantity("head_above_grade", self.head_above_grade_ft, "ft", 0.01))

    not_graded = (
        "NOT GRADED, and each is a real question. (1) HOW THE BASE MOMENT SPLITS between "
        "the buried shaft and the pad under it. The pole here carries it wholly in lateral "
        "bearing on its faces; the pad's own bearing on the soil below — a second, PARALLEL "
        "spring — is left out, which is conservative for sway and says nothing about the "
        "split. Counting the pad as part of the pole does not answer it either: that makes "
        "the pad part of one body, it does not divide one moment between two mechanisms, and "
        "the division is a soil-structure interaction problem. (2) The moment-rotation "
        "relationship is a LINEAR SECANT; a real p-y curve is stiffer at small load and "
        "softer near capacity, and a measured profile is what replaces it. (3) THE COUPLING: "
        "a flexible base makes these columns less rigid, so under the IBC §1604.4 "
        "relative-rigidity split they would take LESS of the canopy's shear — conservative "
        "for the column, UNCONSERVATIVE for W-BW-SCREEN and the deck, which `lateral_system` "
        "grades at the share a rigid base assigned them. The split is deliberately not "
        "re-run here. (4) §6.6.4.6.2's storey sum (a column magnified alone, as deck_post "
        "does, is conservative for the weakest one), the sustained modulus under creep, "
        "beta_ds (taken as deck_post's beta_dns, conservative for wind) and group effect.")

    def evidence(self, ctx: EngineeringContext, delta_in: float | None, column: _Column,
                 label: str) -> str:
        """Where the sway comes from, and the motion at grade §1806.3.4 speaks of."""
        if self.shear is None:
            return "No derived base shear resolves for this column, so no motion is printed."
        load, h = self.shear
        pole = spring.winkler_pole(self.n_h(ctx, delta_in), self.motion_profile, load, h)
        above = self.head_above_grade_ft * 12.0
        arm = h * 12.0 - above   # the load's height above the column head
        flex = (load * column.length_in ** 3 / (3.0 * column.ei_lb_in2)
                + load * max(arm, 0.0) * column.length_in ** 2 / (2.0 * column.ei_lb_in2))
        head = 12.0 * pole.at_height_ft(self.head_above_grade_ft)
        ei_ft = column.ei_lb_in2 / 144.0
        t = (ei_ft / (self.n_h(ctx, delta_in) * self.profile[0][2])) ** 0.2
        depth = self.profile[-1][1]
        return (f"MOTION at {label}, under the {load:,.0f} lb ASD case column_base grades "
                f"at {h:.2f}' above grade: {12.0 * pole.u0_ft:.3f}\" at grade (IBC "
                f"§1806.3.4 speaks of 1/2\" — not independent evidence, since the modulus "
                f"is calibrated on that pairing), {head:.3f}\" at the column head from the "
                f"ground turning against {flex:.4f}\" of the column's own flexure. Rigid-pole "
                f"check: D/T = {depth:.2f}/{t:.2f} = {depth / t:.2f}, T = (EI/n_h)^(1/5) "
                f"(Matlock & Reese: rigid below about 2).")


@dataclass(frozen=True)
class WallBase:
    """A wall held at its head, on a strip footing that rocks on the subgrade."""

    tags: tuple[str, ...]
    ei_lb_in2: float
    height_in: float
    strip_ft: float
    footing_ft: float
    q_allow: float
    missing: tuple[str, ...]
    notes: tuple[str, ...]

    @classmethod
    def build(cls, ctx: EngineeringContext, pier: _Pier) -> WallBase:
        from typehaus.engineering.retaining_basis import PRESUMPTIVE_FC_PSI
        from typehaus.model.enums import LayerFunction
        from typehaus.resolve.concrete import concrete_spec_of, fc_psi

        post = ctx.plan.by_tag(pier.tag)
        wall = ctx.plan.by_tag(getattr(post, "supported_by", "") or "")
        footing = ctx.plan.by_tag(pier.footing_tag or "")
        soil = presumptive(getattr(ctx, "soil_class", None))
        assembly = ctx.plan.library.resolve_assembly(getattr(wall, "assembly", "") or "")
        thick = next((ly.thickness.inches for ly in getattr(assembly, "layers", ())
                      if ly.function is LayerFunction.STRUCTURE), None)
        top, bot = getattr(wall, "top_elevation", None), getattr(wall, "bottom_elevation", None)
        width = getattr(footing, "width", None)
        held = getattr(wall, "lateral_support", None) == "top_and_bottom"
        missing = tuple(t for ok, t in (
            (soil is not None, "a declared soil class (Site/profile soil_class)"),
            (thick is not None, "a STRUCTURE layer on the wall's assembly"),
            (top is not None and bot is not None, "top and bottom elevations on the wall"),
            (width is not None, "a width on the wall's strip footing"),
            (held, "a wall held at its head (`lateral_support=\"top_and_bottom\"`) — a "
                   "free-headed wall under a column is a stacked cantilever this model "
                   "does not work"),
        ) if not ok)
        tags = tuple(t for t in (pier.tag, getattr(wall, "tag", None), pier.footing_tag) if t)
        if missing:
            return cls(tags, 0.0, 0.0, 0.0, 0.0, 0.0, missing, ())
        fc = fc_psi(concrete_spec_of(ctx.plan, wall.assembly)) or PRESUMPTIVE_FC_PSI
        strip_in = pier.diameter_in
        ei = WALL_CRACKED_INERTIA * 57_000.0 * math.sqrt(fc) * strip_in * float(thick) ** 3 / 12
        height = float(top.inches) - float(bot.inches)
        notes = (
            f"THE WALL: {wall.tag}, {float(thick):g}\" at f'c {fc:,.0f} psi, {height:.2f}\" "
            f"from footing to head, held at its head by the diaphragm its "
            f"`lateral_support=\"top_and_bottom\"` declares, cracked at "
            f"{WALL_CRACKED_INERTIA} Ig (ACI 318-19 Table 6.6.3.1.1(a)). The strip is the "
            f"column's own {strip_in:g}\" — no spread of the moment into the wall is "
            f"credited, which is the lower bound. {pier.footing_tag} "
            f"({float(width.inches):g}\") rocks on the subgrade as a rigid strip.",)
        return cls(tags, ei, height, strip_in / 12.0, float(width.inches) / 12.0,
                   soil.allowable_bearing_psf, (), notes)

    def k_v(self, ctx: EngineeringContext, delta_in: float | None) -> float:
        """lb/ft³."""
        report = measured(ctx)
        if delta_in is None and report is not None and report.k_v_pci is not None:
            return float(report.k_v_pci) / PCI_PER_LB_FT3
        # A report that gives n_h and no k_v leaves the footing on the band's SOFT end.
        soft = MOTION_AT_ALLOWABLE_BAND_IN[1]
        return self.q_allow / ((delta_in if delta_in is not None else soft) / 12.0)

    def footing_spring(self, ctx: EngineeringContext, delta_in: float | None) -> float:
        """lb-in/rad."""
        return 12.0 * self.k_v(ctx, delta_in) * self.strip_ft * self.footing_ft ** 3 / 12.0

    def k_theta(self, ctx: EngineeringContext, delta_in: float | None, column: _Column
                ) -> float:
        return spring.wall_top_stiffness(self.ei_lb_in2, self.height_in,
                                         self.footing_spring(ctx, delta_in))

    def modulus_pci(self, ctx: EngineeringContext, delta_in: float | None) -> float:
        return self.k_v(ctx, delta_in) * PCI_PER_LB_FT3

    def inputs(self) -> tuple[Quantity, ...]:
        return (Quantity("wall_EI_strip", self.ei_lb_in2, "lb-in2", 1e6),
                Quantity("wall_height", self.height_in, "in", 0.125),
                Quantity("footing_width", self.footing_ft, "ft", 0.01))

    not_graded = (
        "NOT GRADED, and each is a real question. (1) The wall top's own CAPACITY to receive "
        "the moment and the dowels' DEVELOPMENT into the stem are `column_support/<wall>`'s "
        "questions, not this one; this record answers only the foundation's rotational "
        "restraint those base moments assume. (2) The diaphragm that holds the wall's head "
        "is taken as declared, not graded here. (3) Spread of the column's moment into the "
        "wall beyond its own width is not credited — the lower bound. (4) The footing is a "
        "rigid strip on a LINEAR SECANT subgrade; a real contact softens near uplift, and "
        "the retained fill's own restraint is neglected (conservative). (5) §6.6.4.6.2's "
        "storey sum and beta_ds, as for every column here.")

    def evidence(self, ctx: EngineeringContext, delta_in: float | None, column: _Column,
                 label: str) -> str:
        pinned = spring.wall_top_stiffness(self.ei_lb_in2, self.height_in, 0.0)
        r0 = pinned * column.length_in / column.ei_lb_in2
        return (f"THE SOIL BARELY DECIDES IT at {label}: the footing spring is "
                f"{self.footing_spring(ctx, delta_in):,.3g} lb-in/rad against the wall's "
                f"4EI/H {4 * self.ei_lb_in2 / self.height_in:,.3g}; a footing that did not "
                f"resist rotation at all (3EI/H) still gives R {r0:.2f}.")


def _plan_extents(pad) -> tuple[float, float] | None:  # type: ignore[no-untyped-def]
    """``(x extent ft, y extent ft)`` of a pad."""
    outline = getattr(pad, "outline", None)
    if outline:
        xs = [p.xy_m[0] for p in outline]
        ys = [p.xy_m[1] for p in outline]
        dx, dy = (max(xs) - min(xs)) / 0.3048, (max(ys) - min(ys)) / 0.3048
        if dx > 0.0 and dy > 0.0:
            return dx, dy
    width_in = getattr(getattr(pad, "width", None), "inches", None)
    return (float(width_in) / 12.0,) * 2 if width_in else None
