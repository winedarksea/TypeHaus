"""The working for ``column_head_joint``'s rows, and its sheet declaration.

Split out to keep ``column_head_joint`` under 500 lines. Each function returns the
:class:`~typehaus.engineering.item.Step` chain one limit state prints (review E-02); the
numbers come from the caller, the same ones the state is built from.
"""

from __future__ import annotations

from typehaus.engineering.column_head_uplift import UpliftBuild
from typehaus.engineering.item import NotCovered, StatedBasis, Step, num

#: The combination labels the rows carry (decided per row in the module docstring).
WIND_ASD = ("0.6W, ASD against the published allowable (C_D 1.6 in it)", (("W", 0.6),))
GUARD_ASD = ("L: the 200 lb guard load, ASD, C_D 1.0", (("L", 1.0),))
UPLIFT_ASD = ("ASCE 7-16 §2.4.1(7) 0.6D + 0.6W", (("D", 0.6), ("W", 0.6)))
STRENGTH_LATERAL = ("strength: 1.0W (ASD wind / 0.6) or 1.6L (the guard), the larger",
                    (("W", 1.0),))
STRENGTH_GRAVITY = ("strength: 1.2D + 1.6(L or S)", (("D", 1.2), ("L", 1.6)))


def lateral_wind(wind: float, lateral: float, tie: str,
                 bands: tuple[float, float] | None = None) -> tuple[Step, ...]:
    if bands is not None:
        build: tuple[Step, ...] = (
            Step("V_deck", "wind on the deck band (fascia, beams, plank edge), this column's "
                 "share (service, 0.6W)", bands[0], "lb", source="the deck's wind storey shear"),
            Step("V_guard", "wind on the guard, this column's share (service, 0.6W)",
                 bands[1], "lb", source="the guard's height and its own wind area"),
            Step("V_w", "wind shear the head hands the tie (service, 0.6W)", wind, "lb",
                 "V_deck + V_guard", f"{num(bands[0])} + {num(bands[1])}",
                 "the shaft's own wind acts below the head and is not in it"))
    else:
        build = (Step("V_w", "wind shear the head hands the tie (service, 0.6W)", wind, "lb",
                      source="this column's share of the diaphragm or band shear"),)
    return (*build,
            Step("V_allow", f"{tie} lateral allowable, lower of F1/F2", lateral, "lb",
                 source="the connector's published table, C_D 1.6 included"))


def lateral_guard(guard: float, lateral: float, cd: float, tie: str) -> tuple[Step, ...]:
    return (Step("V_g", "guard load at the head", guard, "lb", source="IRC R301.5"),
            Step("V_allow", f"{tie} lateral allowable at C_D 1.0", lateral / cd, "lb",
                 "V_pub / C_D", f"{num(lateral)} / {num(cd)}", "NDS Table 2.3.2"))


def uplift(net: float, allow: float, tie: str, build: UpliftBuild | None = None
           ) -> tuple[Step, ...]:
    head = build.steps() if build is not None else ()
    equation = "U_net x A_trib" if build is not None else ""
    numbers = (f"{num(build.wind_psf - 0.6 * build.dead_psf)} x {num(build.area_ft2)}"
               if build is not None else "")
    return (*head,
            Step("U", "net uplift at the head, 0.6D + 0.6W", net, "lb", equation, numbers,
                 "" if build is not None else "the uplift surrogate and its area"),
            Step("U_allow", f"{tie} uplift allowable", allow, "lb",
                 source="the connector's published table"))


def combined(net: float, share: int, allow_up: float, wind: float, lateral: float,
             unity: float) -> tuple[Step, ...]:
    return (Step("I", "linear interaction, uplift + lateral", unity, "",
                 "(U / n) / U_allow + V_w / V_allow",
                 f"({num(net)} / {share}) / {num(allow_up)} + {num(wind)} / {num(lateral)}",
                 "the connector document's combined-load rule"),
            Step("I_allow", "interaction limit", 1.0, "", source="the same rule"))


def shear(v_u: float, base_wind: float, wind_factor: float, guard: float, guard_factor: float,
          b_w: float, d: float, fc: float, phi: float) -> tuple[Step, ...]:
    v_c = 2.0 * fc ** 0.5 * b_w * d
    return (Step("V_u", "factored head shear", v_u, "lb", "max(V_w x 1/0.6, 1.6 V_g)",
                 f"max({num(base_wind)} x {num(wind_factor)}, {num(guard_factor)} x "
                 f"{num(guard)})", "V_w the larger of the head shear and the recorded base "
                 "shear; ASD wind back to strength"),
            Step("V_c", "concrete shear strength, N_u = 0", v_c, "lb",
                 "2 sqrt(f'c) b_w d", f"2 x sqrt({num(fc)}) x {num(b_w)} x {num(d)}",
                 "ACI 318-19 Table 22.5.5.1(a); b_w, d per §22.5.2.2"),
            Step("phi V_c", "design shear strength", phi * v_c, "lb", "phi V_c",
                 f"{phi} x {num(v_c)}", "ACI 318-19 Table 21.2.1"))


def torsion(force: float, lever: float, t_u: float, fc: float, area: float,
            perimeter: float, t_th: float, phi: float) -> tuple[Step, ...]:
    return (Step("T_u", "factored torque, horizontal force x plan lever", t_u, "lb-ft",
                 "F r / 12", f"{num(force)} x {num(lever)} / 12",
                 "the bound |r x F| over each beam face and tie at the head"),
            Step("T_th", "torsion threshold", t_th, "lb-ft", "sqrt(f'c) A_cp^2 / p_cp / 12",
                 f"sqrt({num(fc)}) x {num(area)}^2 / {num(perimeter)} / 12",
                 "ACI 318-19 §22.7.4.1(a), N_u = 0"),
            Step("phi T_th", "below this torsion may be neglected", phi * t_th, "lb-ft",
                 "phi T_th", f"{phi} x {num(t_th)}", "ACI 318-19 §22.7.1.1"))


def seat(p_u: float, dead: float, live: float, width: float, length: float, k: float,
         cap: float, fc: float, phi: float) -> tuple[Step, ...]:
    a_1 = width * length
    return (Step("P_u", "factored load on the seat", p_u, "lb", "1.2 D + 1.6 L",
                 f"1.2 x {num(dead)} + 1.6 x {num(live)}", "D less the shaft's own weight"),
            Step("A_1", "seat area", a_1, "in^2", "w l", f"{num(width)} x {num(length)}"),
            Step("phi B_n", "design bearing strength", phi * 0.85 * fc * a_1 * min(k, cap),
                 "lb", "phi 0.85 f'c A_1 min(sqrt(A2/A1), 2)",
                 f"{phi} x 0.85 x {num(fc)} x {num(a_1)} x {num(min(k, cap))}",
                 "ACI 318-19 §22.8.3.2"))


LABELS = {
    "head_lateral_wind": "wind shear at the head, service (0.6W)",
    "head_lateral_guard": "guard load at the head (IRC R301.5)",
    "net_uplift": "net uplift at the head, 0.6D + 0.6W",
    "shear_u": "factored head shear V_u",
    "torsion_u": "factored torque T_u",
    "torsion_lever": "plan lever of the governing horizontal force",
    "seat_pu": "factored load on the seat P_u",
    "seat_eccentricity": "seat centroid off the column axis",
    "seat_bending": "bending from the seat eccentricity, P_u e",
    "combined_unity_unverified": "linear interaction, no published rule",
}

NOT_COVERED = (
    NotCovered("the head connector's fastener schedule",
               "the nails are the connector's own published row (`AN-SG-HETA-TRIM`)",
               "the sealing engineer", "checking the drawing note against the catalog row"),
    NotCovered("moment transfer at the head",
               "the column is analysed with a free head (k = 2.1, fixed base); the strap "
               "pair's rotational stiffness is bounded as negligible",
               "the sealing engineer", "accepting the free-head model on deck_post"),
    NotCovered("wood crushing on the seat pack",
               "NDS Fc-perp under the beam belongs to the beam's own bearing row",
               "the sealing engineer", "the glulam_beam sheet"),
    NotCovered("the guard couple returned through the deck bearings",
               "a free head cannot pass it; it returns as an axial pair not graded here",
               "the sealing engineer", "review of the deck bearing reactions"),
)

BASES: tuple[StatedBasis, ...] = ()


def tie_area(a_v_min: float, a_v: float, b_w: float, spacing: float, tie_bar: int,
             bar_area: float, fc: float, fy: float) -> tuple[Step, ...]:
    """The detailing row's working: minimum tie area against what the circular tie gives."""
    return (Step("A_v,min", "least tie area at this spacing", a_v_min, "in^2",
                 "max(0.75 sqrt(f'c), 50) b_w s / f_y",
                 f"max(0.75 x sqrt({num(fc)}), 50) x {num(b_w)} x {num(spacing)} / {num(fy)}",
                 "ACI 318-19 §9.6.3.4"),
            Step("A_v", f"tie area provided: #{tie_bar} counted twice around a circle",
                 a_v, "in^2", "2 A_b", f"2 x {num(bar_area)}", "ACI 318-19 §22.5.10.5.3"))
