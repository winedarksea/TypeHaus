"""The working for ``wood_roof_post``'s rows, and its sheet declaration (calc-sheet pattern).

Split from ``wood_roof_post`` to keep it under 500 lines. Each function returns the
:class:`~typehaus.engineering.item.Step` chain one limit state prints; the demand chains
(``demand_steps``) are built in ``wood_roof_post._one``, where the numbers are computed, and
reach the joint rows through ``EndDemands.steps``.
"""

from __future__ import annotations

from typehaus.engineering.item import Figure, NotCovered, Step, num
from typehaus.engineering.lateral_working import GEOMETRY, NET_UPLIFT, WIND_ASD, cw  # noqa: F401
from typehaus.engineering.sketch import pinned_post

SNOW_GRAVITY = ("D + S: dead plus the design snow, unfactored (ASD), C_D 1.15 for snow",
                (("D", 1.0), ("S", 1.0)))
WIND_COMBINED = ("D + S axial with 0.6W bending, the NDS combined-stress screen; wind at "
                 "C_D 1.6", (("D", 1.0), ("S", 1.0), ("W", 0.6)))
WIND_UPLIFT = NET_UPLIFT


def axial(trib: float, dead: float, snow: float, weight_plf: float, length_ft: float,
          load: float, fc_table: float, cd: float, length_in: float, side: float, emin: float,
          sawn_c: float, fce: float, cp: float, fc_prime: float, area: float
          ) -> tuple[Step, ...]:
    fc_star = fc_table * cd
    term = (1.0 + fce / fc_star) / (2.0 * sawn_c)
    return (Step("A_t", "roof area the post carries", trib, "ft^2"),
            Step("w_D", "roof dead load", dead, "psf"),
            Step("w_S", "design roof snow, drift included", snow, "psf",
                 source="the house's authored design snow; see Stated bases"),
            Step("W_p", "weight of the post itself", weight_plf * length_ft, "lb",
                 "plf x L", f"{num(weight_plf)} x {num(length_ft)}"),
            Step("P", "axial load on the post", load, "lb", "A_t (w_D + w_S) + W_p",
                 f"{num(trib)} x ({num(dead)} + {num(snow)}) + {num(weight_plf * length_ft)}"),
            Step("Fc*", "compression strength before stability, wet row, snow duration",
                 fc_star, "psi", "Fc C_D", f"{num(fc_table)} x {num(cd)}",
                 "NDS 2018 Supplement Table 4D, SP No. 2 timbers, wet row"),
            Step("FcE", "elastic buckling stress, pinned both ends (K = 1)", fce, "psi",
                 "0.822 E_min / (L / d)^2",
                 f"0.822 x {num(emin)} / ({num(length_in)} / {num(side)})^2", "NDS 2018 §3.7.1.5"),
            Step("r", "ratio of buckling stress to compression strength", fce / fc_star, "",
                 "FcE / Fc*", f"{num(fce)} / {num(fc_star)}"),
            Step("C_P", "column stability factor, sawn lumber c = 0.8", cp, "",
                 "(1 + r)/(2c) - sqrt(((1 + r)/(2c))^2 - r/c)",
                 f"{num(term)} - sqrt({num(term)}^2 - {num(fce / fc_star)}/{num(sawn_c)})",
                 "NDS 2018 §3.7.1.5"),
            Step("Fc'", "compression allowable", fc_prime, "psi", "Fc* C_P",
                 f"{num(fc_star)} x {num(cp)}"),
            Step("A", "section area, 5.5 in square", area, "in^2"),
            Step("P_allow", "allowable axial load", fc_prime * area, "lb", "Fc' A",
                 f"{num(fc_prime)} x {num(area)}"))


def combined(fc_actual: float, fc_prime: float, fb_actual: float, fb_allow: float,
             fce: float, interaction: float, moment: float, moment_basis: str,
             modulus: float, drag_plf: float, length_ft: float, m_drag: float,
             m_plate: float, m_push: float, load: float, area: float, fb_table: float,
             cd: float, plate: tuple[float, float, float], push: tuple[float, float]
             ) -> tuple[Step, ...]:
    steps = [Step("w", "wind drag per foot on the post's face", drag_plf, "plf",
                  source="wind pressure x face width the wind sees"),
             Step("M_w", "bending moment from the post's own drag", m_drag, "lb-ft", "w L^2 / 8",
                  f"{num(drag_plf)} x {num(length_ft)}^2 / 8")]
    if m_plate:
        steps.append(Step("M_pl", "added by the framed panel's top-plate reaction", m_plate,
                          "lb-ft", "P_pl a b / L",
                          f"{num(plate[0])} x {num(plate[1])} x {num(plate[2])} / "
                          f"{num(length_ft)}", "point load on the post"))
    if m_push:
        steps.append(Step("M_N-S", "N-S case: own drag plus the slat band's push", m_push,
                          "lb-ft", "w L^2 / 8 + P_b a_p (L - a_p) / L",
                          f"{num(m_drag)} + {num(push[0])} x {num(push[1])} x "
                          f"{num(length_ft - push[1])} / {num(length_ft)}",
                          "the push acts at the centroid of its brace landings"))
    return (*steps,
            Step("M", f"design moment, the larger case ({moment_basis})", moment, "lb-ft",
                 "max(M_w + M_pl, M_N-S)" if m_push else "M_w + M_pl" if m_plate else "M_w"),
            Step("f_c", "axial stress", fc_actual, "psi", "P / A", f"{num(load)} / {num(area)}"),
            Step("f_b", "bending stress", fb_actual, "psi", "12 M / S",
                 f"12 x {num(moment)} / {num(modulus)}"),
            Step("Fb'", "bending allowable, wet row, wind duration", fb_allow, "psi",
                 "Fb C_D", f"{num(fb_table)} x {num(cd)}",
                 "NDS 2018 Supplement Table 4D, SP No. 2 timbers, wet row"),
            Step("I", "combined axial and bending, second-order amplified", interaction, "",
                 "(f_c / Fc' + f_b / Fb') / (1 - f_c / FcE)",
                 f"({num(fc_actual)} / {num(fc_prime)} + {num(fb_actual)} / {num(fb_allow)}) / "
                 f"(1 - {num(fc_actual)} / {num(fce)})",
                 "NDS 2018 §3.9, a conservative uniaxial screen"),
            Step("I_allow", "interaction limit", 1.0, "", source="NDS 2018 §3.9"))


def drag_half(drag_plf: float, length_ft: float, own_half: float) -> tuple[Step, ...]:
    return (Step("w", "wind drag per foot on the post's face", drag_plf, "plf"),
            Step("R_w", "half the post's own drag to each end", own_half, "lb", "w L / 2",
                 f"{num(drag_plf)} x {num(length_ft)} / 2"))


def demand_steps(trib: float, pressure: float, dead: float, uplift: float, head_uplift: float,
                 couple: float, lever: float, own: tuple[Step, ...], plate: float, a_ft: float,
                 b_ft: float, length_ft: float, push: float, a_p: float, push_head: float,
                 push_base: float, head_along: float, base_along: float, head_across: float,
                 base_across: float) -> dict[str, tuple[Step, ...]]:
    """Each end demand's chain, keyed as ``EndDemands.steps`` reads them."""
    up = Step("U", "net roof uplift on the post, 0.6D + 0.6W", uplift, "lb",
              "max(A_t (p - 0.6 w_D), 0)", f"{num(trib)} x ({num(pressure)} - 0.6 x {num(dead)})")
    head_up: tuple[Step, ...] = (up,)
    if couple:
        head_up += (Step("M_c", "couple the band puts on the header", couple, "lb-ft"),
                    Step("d_c", "lever between the two chords", lever, "ft"))
    head_up += (Step("U_h", "uplift at the head", head_uplift, "lb",
                     "U + M_c / d_c" if couple else "U",
                     f"{num(uplift)} + {num(couple)} / {num(lever)}" if couple else ""),)
    plate_steps = (Step("P_pl", "framed panel's top-plate reaction", plate, "lb",
                        source="the panel's wind over its height and the band above"),
                   Step("a", "height of the plate above the base", a_ft, "ft"))
    push_steps = ((Step("P_b", "outward push of the slat band on this chord", push, "lb"),
                   Step("a_p", "height of the push above the base", a_p, "ft"))
                  if push else ())
    out = {
        "uplift_head": head_up,
        "uplift_base": (up,),
        "head_along": (*own, *push_steps,
                       Step("V_ha", "lateral at the head, along the beam", head_along, "lb",
                            "R_w + P_b (L - a_p) / L" if push else "R_w",
                            f"{num(own[-1].value)} + {num(push_head)}" if push else "")),
        "base_along": (*own, *push_steps,
                       Step("V_ba", "lateral at the base, along the beam", base_along, "lb",
                            "R_w + P_b a_p / L" if push else "R_w",
                            f"{num(own[-1].value)} + {num(push_base)}" if push else "")),
        "head_across": (*own, *((*plate_steps,) if plate else ()),
                        Step("V_hx", "lateral at the head, across the beam", head_across, "lb",
                             "R_w + P_pl a / L" if plate else "R_w",
                             f"{num(own[-1].value)} + {num(plate * a_ft / length_ft)}"
                             if plate else "")),
        "base_across": (*own, *((*plate_steps,) if plate else ()),
                        Step("V_bx", "lateral at the base, across the beam", base_across, "lb",
                             "R_w + P_pl b / L" if plate else "R_w",
                             f"{num(own[-1].value)} + {num(plate * b_ft / length_ft)}"
                             if plate else "")),
        "plate": (*plate_steps,),
    }
    return out


def slenderness(length_in: float, side: float, limit: float) -> tuple[Step, ...]:
    return (Step("L", "post length between pins", length_in, "in"),
            Step("d", "post width, 5.5 in dressed", side, "in"),
            Step("L/d", "slenderness", length_in / side, "", "L / d",
                 f"{num(length_in)} / {num(side)}"),
            Step("(L/d)_max", "largest slenderness allowed, pinned K = 1", limit, "",
                 source="NDS 2018 §3.7.1.4"))


def height_cross_check(length_ft: float, limit: float) -> tuple[Step, ...]:
    return (Step("H", "post height", length_ft, "ft"),
            Step("H_max", "tallest 6x6 the prescriptive table lists", limit, "ft",
                 source="2018 IRC Table R507.4"))


# -- joint rows ---------------------------------------------------------------------------

def cap_uplift(demand: tuple[Step, ...], rated: float, cm: float, cap: float, size: str
               ) -> tuple[Step, ...]:
    return (*demand,
            Step("U_pub", f"{size} published allowable uplift, dry", rated, "lb",
                 source="the connector's evaluation-report table, see References"),
            Step("C_M", "wet-service factor on the dry row", cm, "",
                 source="NDS 2018 Table 11.3.3"),
            Step("U_allow", "allowable uplift, wet", cap, "lb", "U_pub C_M",
                 f"{num(rated)} x {num(cm)}"))


def cap_combined(up: tuple[Step, ...], head_along: tuple[Step, ...], rated: float,
                 lateral: float, cm: float, u_h: float, v: float, unity: float, size: str
                 ) -> tuple[Step, ...]:
    cap_up, cap_lat = rated * cm, lateral * cm
    return (*up, *head_along,
            Step("U_allow", "allowable uplift, wet", cap_up, "lb", "U_pub C_M",
                 f"{num(rated)} x {num(cm)}", "the connector's evaluation-report table"),
            Step("V_allow", f"{size} lateral allowable parallel to the beam, wet", cap_lat,
                 "lb", "V_pub C_M", f"{num(lateral)} x {num(cm)}", "ESR-2604 Table 3 fn. 6"),
            Step("I", "linear interaction, uplift + lateral", unity, "",
                 "U_h / U_allow + V_ha / V_allow",
                 f"{num(u_h)} / {num(cap_up)} + {num(v)} / {num(cap_lat)}"),
            Step("I_allow", "interaction limit", 1.0, "", source="the connector's linear rule"))


def angle(demand: tuple[Step, ...], total: float, n: int, per: float, values_min: float,
          cm: float, cap: float, size: str) -> tuple[Step, ...]:
    return (*demand,
            Step("n_a", f"{size} angles", n, ""),
            Step("F_a", "load on one angle", per, "lb", "demand / n_a", f"{num(total)} / {n}"),
            Step("F_pub", f"{size} lateral allowable, the lower of F1 and F2, dry", values_min,
                 "lb", source="ESR-3096 Table 5"),
            Step("F_allow", "allowable on one angle, wet", cap, "lb", "F_pub C_M",
                 f"{num(values_min)} x {num(cm)}", "NDS 2018 Table 11.3.3"))


def base_combined(up: tuple[Step, ...], lat: tuple[Step, ...], base_up: float, lateral: float,
                  allow: float, unity: float, label: str, size: str, u: float, v: float
                  ) -> tuple[Step, ...]:
    return (*up, *lat,
            Step("U_allow", f"{size} allowable uplift, cracked concrete, wet", base_up, "lb",
                 source="ESR-3050 Table 2 x C_M"),
            Step("V_allow", f"{size} lateral allowable {label}, wet", allow, "lb",
                 source="ESR-3050 Table 2 x C_M; F2 along the base's axis, F1 across it"),
            Step("I", "linear unity, uplift + lateral", unity, "",
                 "U / U_allow + V / V_allow",
                 f"{num(u)} / {num(base_up)} + {num(v)} / {num(allow)}"),
            Step("I_allow", "interaction limit", 1.0, "", source="the maker's unity rule"))


# -- sheet declaration --------------------------------------------------------------------

def figure(record) -> Figure | None:  # type: ignore[no-untyped-def]
    head, base = record.value("head_uplift_lb"), record.value("uplift_lb")
    axial_lb = record.value("axial_lb")
    if head is None or axial_lb is None or base is None:
        return None
    length = (record.value("post_length_in") or 0.0) / 12.0
    return pinned_post(
        title=f"{record.key}, a 6x6 pinned post under its header",
        length_ft=length, axial=f"P = {num(axial_lb)} lb (D + S)",
        lateral="wind drag across the post's face",
        head=f"cap + angles, U_h = {num(head)} lb up",
        base=f"cast-in base, U = {num(base)} lb up",
        caption="Pinned at head and foot: each end takes half the post's own drag, and the "
                "panel plate and slat band loads divide between the ends by their height.")


NOT_COVERED = (
    NotCovered("wind from both directions at once on the post",
               "the design moment is the larger of the along-beam and across-beam cases, "
               "not their vector sum",
               "the sealing engineer", "accepting the one-direction-at-a-time reading"),
    NotCovered("the connectors' wet-service values",
               "the caps, angles and base are graded with C_M 0.70 on their dry rows; their "
               "evaluation reports cover moisture content of 19% or less only, so the wet "
               "values are a reading outside the report",
               "the sealing engineer",
               "accepting the C_M 0.70 reading, or keeping the parts dry (KDAT at 19% or "
               "less, checked with a moisture meter)"),
    NotCovered("anchorage of the cast-in post base",
               "the base's published uplift row is measured through the concrete, so no "
               "separate anchor-bolt row is graded",
               "the sealing engineer", "accepting the published row as the anchor check"),
)

LABELS = {
    "roof_tributary_ft2": "roof area carried by the post",
    "post_length_in": "post length, base to head",
    "pier_fc_psi": "concrete strength of the pier under the base",
    "axial_lb": "axial load, D + S plus the post's weight",
    "uplift_lb": "net roof uplift at the base, 0.6D + 0.6W",
    "head_uplift_lb": "uplift at the head (adds the band's couple where there is one)",
    "plate_load_lb": "framed panel's top-plate reaction on the post",
    "band_push_lb": "outward push of the slat band on this chord",
    "band_push_base_lb": "share of that push reaching the base",
    "band_push_height_ft": "height of the push's centroid above the base",
}
