"""The CONCRETE under a shear panel's hold-down — ACI 318-19 Ch. 17 on the cast-in bolt.

ICC-ES ESR-1622 §5.6, verbatim: "The design of anchor bolts and the concrete footings is
outside the scope of this report." So an ``ABU66SS`` standing on a pier top publishes 2,190 lb
of uplift **through** a 5/8" anchor whose own capacity the report declines to state, and the
link is a design. This is it, in the ``deck_tie_anchor.py`` idiom: a headed cast-in anchor,
cracked concrete, condition B (no supplementary reinforcement credited).

** THE EDGE DISTANCE IS THE WHOLE CALCULATION. ** A bolt at the centre of a 12" round pier is
6" from the face in EVERY direction at once, so tension breakout is edge-limited on all sides
and shear breakout has a 6" edge whichever way the panel pushes. Two readings of §17.6.2 are
computed and the **lower** is graded:

* §17.6.2.1.2's reduced ``h_ef`` (three or more edges under ``1.5 h_ef``), which is the code's
  own correction for a narrow member and gives the LARGER capacity here;
* the unreduced ``h_ef`` with the projected area clipped to the pier, which is the
  conservative bound.

Taking the lower is the same move ``roof_moment``'s solid-sign wind surrogate makes: a bound,
not a reading, and cheap while it clears by a factor of four.

** WHAT IS NOT CREDITED. ** No supplementary reinforcement (the (4) #5 cage is not developed
as anchor reinforcement), no uncracked concrete, no dead load against the overturning couple,
and no shear friction from the base plate's bearing.

**Oracle.** ``houses/catlin/notes/north_entry_canopy_lateral.md`` §8f;
``tests/test_lateral_system_calcs.py`` reproduces it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.engineering.item import LimitState

#: ACI 318-19 Table 17.5.3(b), cast-in headed anchor, condition B (no supplementary
#: reinforcement): concrete-governed tension and shear. Steel is Table 17.5.3(a), ductile.
PHI_CONCRETE = 0.70
PHI_STEEL_TENSION = 0.75
PHI_STEEL_SHEAR = 0.65

#: §17.6.2.2.1, cast-in anchor in CRACKED concrete.
K_C_CRACKED = 24.0
#: §17.7.3.1, pryout, for ``h_ef >= 2.5"``.
K_CP = 2.0

#: ASD wind to strength level: the demands here are 0.6W (ASCE 7-16 §2.4.1), the capacities
#: are φ-factored strengths, so the load returns to 1.0W.
STRENGTH_FROM_ASD_WIND = 1.0 / 0.6


@dataclass(frozen=True)
class Anchor:
    """One cast-in headed anchor in a round pier, and the pier it stands in."""

    joint: str
    #: Nominal bolt diameter, inches.
    diameter_in: float
    #: Tensile stress area, in² (5/8"-11 UNC: 0.226).
    area_in2: float
    #: Specified tensile strength, psi, already capped at ``1.9 f_ya`` by the caller.
    f_uta_psi: float
    #: Effective embedment to the head's bearing face, inches.
    h_ef_in: float
    #: Bearing area of the head (a heavy hex nut here), in².
    bearing_in2: float
    #: Edge distance, inches — the pier's radius, the same in every direction.
    c_a_in: float
    fc_psi: float


def round_pier_anchor(joint: str, pier_diameter_in: float, fc_psi: float,
                      bolt_length_in: float = 10.0, diameter_in: float = 0.625,
                      projection_in: float = 1.5) -> Anchor:
    """The anchor a 5/8" x ``bolt_length_in`` cast-in bolt makes at a round pier's centre.

    ``h_ef`` is DERIVED rather than assumed: the bolt's length less what stands above the
    pour (base plate, washer, nut and a couple of threads — ``projection_in``) and less the
    embedded nut's own thickness, which is where the head bears.
    """
    across_flats_in = 1.70 * diameter_in      # a heavy hex nut, ANSI B18.2.2
    nut_thickness_in = 0.975 * diameter_in
    bearing = (math.sqrt(3.0) / 2.0 * across_flats_in ** 2
               - math.pi / 4.0 * diameter_in ** 2)
    return Anchor(
        joint=joint, diameter_in=diameter_in,
        # 5/8"-11 UNC: A_se = pi/4 (d - 0.9743/n)^2.
        area_in2=math.pi / 4.0 * (diameter_in - 0.9743 / 11.0) ** 2,
        # ASTM A193 Gr. B8 Cl. 1 (the conservative read of "304 stainless"): f_u 75 ksi,
        # f_y 30 ksi, and §17.6.1.2 caps f_uta at 1.9 f_ya.
        f_uta_psi=min(75_000.0, 1.9 * 30_000.0),
        h_ef_in=bolt_length_in - projection_in - nut_thickness_in,
        bearing_in2=bearing, c_a_in=pier_diameter_in / 2.0, fc_psi=fc_psi)


def breakout_tension(anchor: Anchor) -> tuple[float, float, str]:
    """``(φN_cb lb, A_Nc/A_Nco of the graded reading, how)`` — the lower of the two readings."""
    root = math.sqrt(anchor.fc_psi)
    c = anchor.c_a_in

    # §17.6.2.1.2: three or more edges closer than 1.5 h_ef, so h_ef is limited.
    limited = c / 1.5
    out = []
    for h_ef, label in ((limited, "§17.6.2.1.2 h_ef'"), (anchor.h_ef_in, "unreduced h_ef")):
        a_nco = 9.0 * h_ef ** 2
        # The projected area is clipped by the pier itself: a circle of radius min(1.5 h_ef, c).
        a_nc = math.pi * min(1.5 * h_ef, c) ** 2
        psi_ed = min(1.0, 0.7 + 0.3 * c / (1.5 * h_ef))
        n_b = K_C_CRACKED * root * h_ef ** 1.5
        out.append((PHI_CONCRETE * a_nc / a_nco * psi_ed * n_b, a_nc / a_nco, psi_ed, h_ef,
                    label))
    capacity, ratio, psi_ed, h_ef, label = min(out, key=lambda row: row[0])
    other = max(out, key=lambda row: row[0])
    how = (f"ACI 318-19 §17.6.2, cracked concrete (k_c {K_C_CRACKED:g}), condition B "
           f"(φ {PHI_CONCRETE:g}), c_a {c:.2f}\" on EVERY side of a "
           f"{2.0 * c:.0f}\" round pier: {label} {h_ef:.3f}\", A_Nc/A_Nco {ratio:.3f}, "
           f"ψ_ed,N {psi_ed:.3f}, f'c {anchor.fc_psi:,.0f} psi — the LOWER of the two "
           f"readings is graded ({other[4]} would give {other[0]:,.0f} lb)")
    return capacity, ratio, how


def pullout_tension(anchor: Anchor) -> float:
    """φN_pn, §17.6.3.2 — ``8 A_brg f'c``, ψ_c,P 1.0 for cracked concrete."""
    return PHI_CONCRETE * 8.0 * anchor.bearing_in2 * anchor.fc_psi


def steel_tension(anchor: Anchor) -> float:
    return PHI_STEEL_TENSION * anchor.area_in2 * anchor.f_uta_psi


def steel_shear(anchor: Anchor) -> float:
    """φV_sa, §17.7.1.2 — ``0.6 A_se f_uta`` for a cast-in headed bolt."""
    return PHI_STEEL_SHEAR * 0.6 * anchor.area_in2 * anchor.f_uta_psi


def breakout_shear(anchor: Anchor) -> tuple[float, str]:
    """φV_cb toward the pier face, §17.7.2, with the pier's own width limiting ``A_Vc``."""
    c = anchor.c_a_in
    root = math.sqrt(anchor.fc_psi)
    l_e = min(anchor.h_ef_in, 8.0 * anchor.diameter_in)
    v_b = min(7.0 * (l_e / anchor.diameter_in) ** 0.2 * math.sqrt(anchor.diameter_in)
              * root * c ** 1.5,
              9.0 * root * c ** 1.5)
    # The pier is 2c wide and deep, so the half-pyramid is clipped sideways and not by depth.
    a_vc = 2.0 * c * 1.5 * c
    a_vco = 4.5 * c ** 2
    psi_ed = min(1.0, 0.7 + 0.3 * c / (1.5 * c))
    capacity = PHI_CONCRETE * a_vc / a_vco * psi_ed * v_b
    how = (f"ACI 318-19 §17.7.2 toward the pier face, c_a1 {c:.2f}\": l_e {l_e:.3f}\", "
           f"V_b {v_b:,.0f} lb, A_Vc/A_Vco {a_vc / a_vco:.3f} (the pier is only "
           f"{2.0 * c:.0f}\" wide), ψ_ed,V {psi_ed:.2f}, φ {PHI_CONCRETE:g}")
    return capacity, how


def pryout_shear(anchor: Anchor) -> float:
    """φV_cp, §17.7.3 — ``k_cp N_cb``, on the same breakout the tension row grades."""
    return K_CP * breakout_tension(anchor)[0]


def side_face_blowout_applies(anchor: Anchor) -> bool:
    """§17.6.4.1 engages only for a DEEP anchor near an edge, ``h_ef > 2.5 c_a1``."""
    return anchor.h_ef_in > 2.5 * anchor.c_a_in


def states(anchor: Anchor, tension_asd_lb: float, shear_asd_lb: float,
           tension_how: str, shear_how: str) -> list[LimitState]:
    """The three graded rows: tension, shear, and §17.8.3's interaction."""
    tension_u = tension_asd_lb * STRENGTH_FROM_ASD_WIND
    shear_u = shear_asd_lb * STRENGTH_FROM_ASD_WIND
    breakout_t, _ratio, breakout_how = breakout_tension(anchor)
    capacity_t = min(breakout_t, pullout_tension(anchor), steel_tension(anchor))
    breakout_v, shear_breakout_how = breakout_shear(anchor)
    capacity_v = min(breakout_v, pryout_shear(anchor), steel_shear(anchor))
    blowout = ("side-face blowout §17.6.4 does NOT apply (it engages at "
               f"h_ef > 2.5 c_a1, {anchor.h_ef_in:.2f}\" against "
               f"{2.5 * anchor.c_a_in:.2f}\")" if not side_face_blowout_applies(anchor)
               else "side-face blowout §17.6.4 APPLIES and is NOT computed here")
    tension_ratio = tension_u / capacity_t if capacity_t > 0.0 else float("inf")
    shear_ratio = shear_u / capacity_v if capacity_v > 0.0 else float("inf")
    both = (max(tension_ratio, shear_ratio)
            if tension_ratio <= 0.2 or shear_ratio <= 0.2
            else (tension_ratio + shear_ratio) / 1.2)
    return [
        LimitState(
            f"{anchor.joint} anchor tension (breakout / pullout / steel)",
            tension_u, capacity_t, "lb",
            f"{breakout_how}; pullout φN_pn {pullout_tension(anchor):,.0f} lb (A_brg "
            f"{anchor.bearing_in2:.3f} in2), steel φN_sa {steel_tension(anchor):,.0f} lb "
            f"(f_uta {anchor.f_uta_psi:,.0f} psi, the conservative 304 read); {blowout}. "
            f"Demand {tension_asd_lb:,.0f} lb ASD / 0.6 — {tension_how}",
            combination="ASCE 7-16 §2.4.1(7) 0.6D + 0.6W, taken to 1.0W for strength design",
            combination_factors=(("W", 1.0),)),
        LimitState(
            f"{anchor.joint} anchor shear (breakout / pryout / steel)",
            shear_u, capacity_v, "lb",
            f"{shear_breakout_how}; pryout φV_cp {pryout_shear(anchor):,.0f} lb, steel "
            f"φV_sa {steel_shear(anchor):,.0f} lb. Demand {shear_asd_lb:,.0f} lb ASD / 0.6 "
            f"— {shear_how}",
            combination="ASCE 7-16 §2.4.1(7) 0.6D + 0.6W, taken to 1.0W for strength design",
            combination_factors=(("W", 1.0),)),
        LimitState(
            f"{anchor.joint} anchor tension-shear interaction", both, 1.0, "",
            f"ACI 318-19 §17.8: tension {tension_ratio:.3f}, shear {shear_ratio:.3f}; "
            + ("either at or under 0.2 of its strength, so the other governs alone (§17.8.1/"
               "§17.8.2)" if tension_ratio <= 0.2 or shear_ratio <= 0.2
               else "both over 0.2, so §17.8.3's (N/φN + V/φV) <= 1.2 governs")),
    ]
