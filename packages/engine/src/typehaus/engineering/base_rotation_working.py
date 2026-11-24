"""The working for ``base_rotation``'s three rows, and its sheet declaration.

Split out to keep ``base_rotation`` under 500 lines. Each function returns the
:class:`~typehaus.engineering.item.Step` chain one limit state prints; every number is a
field the column and the base-spring point already carry, so the working cannot drift
from the ratio.
"""

from __future__ import annotations

import math

from typehaus.engineering.item import EngineeringRecord, Figure, NotCovered, Step, num

#: The axial the first two rows use: the factored column load of ``deck_post``.
AXIAL = ("1.2D + 1.6L: the factored axial the column carries (ASCE 7-16 §2.3.1)",
         (("D", 1.2), ("L", 1.6)))


def _stiffness(col) -> tuple[Step, ...]:  # type: ignore[no-untyped-def]
    ec = 57_000.0 * math.sqrt(col.fc_psi)
    ig = math.pi * col.diameter_in ** 4 / 64.0
    return (
        Step("E_c", "concrete modulus of elasticity", ec, "psi", "57,000 sqrt(f'c)",
             f"57,000 x sqrt({num(col.fc_psi)})", "the same value deck_post uses"),
        Step("I_g", "gross moment of inertia of the round column", ig, "in^4",
             "pi D^4 / 64", f"pi x {num(col.diameter_in)}^4 / 64"),
        Step("beta_dns", "sustained-load ratio (dead load over factored axial)", col.beta_dns,
             "", "1.2 D / P_u", "dead load, factored axial from the column's loads"),
        Step("EI", "effective flexural stiffness of the column", col.ei_lb_in2, "lb-in^2",
             "0.4 E_c I_g / (1 + beta_dns)",
             f"0.4 x {num(ec)} x {num(ig)} / (1 + {num(col.beta_dns)})",
             "ACI 318-19 §6.6.4.4.4(a)"),
        Step("P_c,rigid", "buckling load with the base held rigid (effective length factor "
             f"k = {num(col.k_rigid)})", col.pc_rigid_lb, "lb", "pi^2 EI / (k L)^2",
             f"pi^2 x {num(col.ei_lb_in2)} / ({num(col.k_rigid)} x {num(col.length_in)})^2",
             "ACI 318-19 §6.2.5; the rigid-base bound deck_post grades"))


def _spring(col, pt) -> tuple[Step, ...]:  # type: ignore[no-untyped-def]
    return (
        *_stiffness(col),
        Step("k_theta", "rotational stiffness of the base (moment per radian of turn)",
             pt.k_theta_lb_in, "lb-in/rad",
             source="the soil model in the assumptions: a rigid pole on a soil-reaction "
                    "profile, or a wall on a rocking footing"),
        Step("R", "ratio of base stiffness to column stiffness", pt.r, "",
             "k_theta L / EI", f"{num(pt.k_theta_lb_in)} x {num(col.length_in)} / "
             f"{num(col.ei_lb_in2)}"),
        Step("P_c,series", "buckling load, base-spring series form", pt.pc_series_lb, "lb",
             "P_c,rigid / (1 + 3 / R)", f"{num(col.pc_rigid_lb)} / (1 + 3 / {num(pt.r)})"),
        Step("P_c,exact", "buckling load, exact spring root (the less conservative form)",
             pt.pc_exact_lb, "lb", "pi^2 EI / (k_e L)^2, with (mu L) tan(mu L) = R and "
             "k_e = pi / (mu L)", f"pi^2 x {num(col.ei_lb_in2)} / ({num(pt.k_exact)} x "
             f"{num(col.length_in)})^2"),
        Step("P_c", "buckling load graded: the smaller of the two forms", pt.pc_flex_lb, "lb",
             "min(P_c,series, P_c,exact)", f"min({num(pt.pc_series_lb)}, "
             f"{num(pt.pc_exact_lb)})"))


def sway_steps(col, pt) -> tuple[Step, ...]:  # type: ignore[no-untyped-def]
    return (*_spring(col, pt),
            Step("0.75 P_c", "most axial load the sway-stability rule admits",
                 0.75 * pt.pc_flex_lb, "lb", "0.75 P_c", f"0.75 x {num(pt.pc_flex_lb)}",
                 "ACI 318-19 §6.6.4.5.2"),
            Step("P_u", "factored axial load on the column", col.pu_lb, "lb",
                 source="1.2 dead + 1.6 live, as deck_post"))


def increment_steps(col, pt, limit: float) -> tuple[Step, ...]:  # type: ignore[no-untyped-def]
    d = pt.delta or math.inf
    return (*_spring(col, pt),
            Step("delta", "sway moment magnifier", d, "", "1 / (1 - P_u / (0.75 P_c))",
                 f"1 / (1 - {num(col.pu_lb)} / (0.75 x {num(pt.pc_flex_lb)}))",
                 "ACI 318-19 §6.6.4.5.2"),
            Step("delta - 1", "second-order increase over first-order moment", d - 1.0, "",
                 "delta - 1", f"{num(d)} - 1"),
            Step("limit", "most the second-order moment may add", limit - 1.0, "",
                 f"{limit:g} - 1", f"{limit:g} - 1",
                 "ACI 318-19 §6.2.5.3: second-order moment at most 1.4 x first-order"))


def magnified_steps(worst, pt, delta) -> tuple[Step, ...]:  # type: ignore[no-untyped-def]
    d = delta or math.inf
    return (
        Step("P_u", "axial load of the governing load pair", worst.pu_lb, "lb",
             source="ASCE 7-16 §2.3.1, the pair named in the limit state"),
        Step("P_c", "buckling load graded (see the sway row)", pt.pc_flex_lb, "lb"),
        Step("delta", "sway moment magnifier at this pair", d, "",
             "1 / (1 - P_u / (0.75 P_c))",
             f"1 / (1 - {num(worst.pu_lb)} / (0.75 x {num(pt.pc_flex_lb)}))",
             "ACI 318-19 §6.6.4.5.2"),
        Step("M_u", "first-order moment of this pair at the column base", worst.mu_lb_ft,
             "lb-ft", source="from the column's own wind and guard moments, as deck_post"),
        Step("delta M_u", "magnified design moment", worst.mu_lb_ft * d, "lb-ft",
             "delta M_u", f"{num(d)} x {num(worst.mu_lb_ft)}"),
        Step("phi M_n", "design moment strength of the cage at this P_u", worst.phi_mn_lb_ft,
             "lb-ft", source="the column's moment-axial interaction curve, as deck_post"))


LABELS = {
    "column_height": "column height, base to head L",
    "column_EI": "effective flexural stiffness of the column EI",
    "factored_axial": "factored axial load P_u",
    "governing_Mu": "first-order moment of the governing load pair M_u",
    "phi_Mn": "design moment strength of the column phi M_n",
    "Pc_rigid": "buckling load with a rigid base P_c,rigid",
    "subgrade_modulus_pci": "soil modulus the base spring is built on",
    "subgrade_modulus_measured": "soil modulus measured by a report",
    "n_h_presumed": "soil modulus presumed from a published table row",
    "base_spring": "base rotational stiffness k_theta",
    "spring_ratio_R": "base-to-column stiffness ratio R",
    "Pc_flexible": "buckling load on the spring base P_c",
    "wall_EI_strip": "stiffness of the wall strip under the column",
    "wall_height": "wall height, footing to head",
    "pole_depth": "buried depth of the shaft and pad",
    "pole_toe_width": "width of the pad at the bottom",
    "head_above_grade": "column head above grade",
}

NOT_COVERED = (
    NotCovered("storey sum and sustained-load stiffness reduction",
               "each column is magnified alone, as deck_post does, with beta_dns taken for "
               "beta_ds; conservative for the weakest column (ACI 318-19 §6.6.4.6.2)",
               "the sealing engineer", "accepting the single-column magnification"),
    NotCovered("measured soil stiffness",
               "the lateral modulus is presumed from a published table row and run over "
               "the code's motion band; the verdict publishes only where both ends agree",
               "the owner (soil report)",
               "a geotechnical report on this parcel stating the lateral modulus"),
    NotCovered("seismic and a drift limit",
               "the lot is Seismic Design Category A, where wind governs; IRC R301 sets no "
               "drift limit for a deck column, so head drift is reported and not graded",
               "the sealing engineer", "accepting wind as the governing lateral case"),
)

_WALL = (
    NotCovered("the wall top's capacity and the dowels' development",
               "they are the column_support sheet's questions; this sheet answers only the "
               "foundation's rotational restraint those base moments assume",
               "the sealing engineer", "the column_support sheet"),
    NotCovered("the diaphragm that holds the wall's head",
               "taken as declared (a wall braced top and bottom), not graded here",
               "the sealing engineer", "the floor diaphragm's own calculation"),
    NotCovered("spread of the column's moment into the wall",
               "the strip is the column's own width: the lower bound",
               "the sealing engineer", "accepting the narrow strip"),
    NotCovered("footing contact softening near uplift",
               "the footing is a rigid strip on a linear secant subgrade; the retained "
               "fill's own restraint is neglected (conservative)",
               "the sealing engineer", "accepting the linear subgrade"),
)

_POLE = (
    NotCovered("how the base moment splits between the buried shaft and its pad",
               "the pole carries it wholly in lateral bearing on its faces; the pad's own "
               "bearing is a parallel spring left out (conservative for sway)",
               "the sealing engineer", "a soil-structure analysis or a report"),
    NotCovered("the share of the canopy's shear a flexible base releases",
               "a flexible base takes less shear than the rigid split lateral_system "
               "grades; the split is not re-run here",
               "the sealing engineer", "re-running the lateral split on the spring base"),
)


def base_not_covered(base) -> tuple[NotCovered, ...]:  # type: ignore[no-untyped-def]
    """The rows true of this member's base type only."""
    return _WALL if hasattr(base, "footing_ft") else _POLE


def figure(record: EngineeringRecord) -> Figure | None:
    from typehaus.engineering.sketch import column_on_spring

    length, pu, k_th = (record.value("column_height"), record.value("factored_axial"),
                        record.value("base_spring"))
    if length is None or pu is None or k_th is None:
        return None
    return column_on_spring(
        title=f"{record.key}, a fixed-base column on its base spring",
        length_in=length, axial=f"P_u = {num(pu)} lb",
        moment=f"M_u = {num(record.value('governing_Mu') or 0.0)} lb-ft (first order)",
        spring=f"k_theta = {num(k_th)} lb-in/rad, R = {num(record.value('spring_ratio_R') or 0)}",
        stiffness=f"EI = {num(record.value('column_EI') or 0.0)} lb-in^2",
        caption="The base turns on its spring; the column's sway load P_u is graded "
                "against 0.75 P_c of that spring.")
