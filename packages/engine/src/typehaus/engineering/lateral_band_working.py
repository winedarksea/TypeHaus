"""The working for ``lateral_band`` and ``lateral_band_slats`` rows (calc-sheet pattern).

Each function returns the :class:`~typehaus.engineering.item.Step` chain one limit state
prints, from the very numbers the state is built from. The chains for the slat band share
their first steps (the force one slat carries), which the sheet prints once.
"""

from __future__ import annotations

import math

from typehaus.engineering.item import Step, num
from typehaus.engineering.lateral_working import (  # noqa: F401
    NET_UPLIFT,
    WIND_ASD,
    WIND_NO_DEAD,
    cw,
)

_SHARE = ("the two bays mirror each other, so they share the wind equally; one slat crosses "
          "mid-band, where the verticals carry no shear, and takes its bay's half")


def slat_force(sb) -> tuple[Step, ...]:  # type: ignore[no-untyped-def]
    slope = sb.layout.braces(0)[0].slope
    return (Step("V", "wind shear the band carries (the panel's shear)", sb.shear_lb, "lb",
                 source="the deck's wind shear delivered to this wall; see the Independent "
                        "check note"),
            Step("n_slat", "braced slats crossing mid-band in one bay", sb.crossing, ""),
            Step("h", "horizontal force at each end of one slat", sb.per_end_lb, "lb",
                 "V / 2 / n_slat", f"{num(sb.shear_lb)} / 2 / {sb.crossing}", _SHARE),
            Step("theta", "angle of the braced slats above the plates", sb.angle_degrees, "deg",
                 "atan(slope)", f"atan({num(slope)})"),
            Step("P", "force along one slat, tension or compression", sb.slat_lb, "lb",
                 "h sqrt(1 + slope^2)", f"{num(sb.per_end_lb)} x sqrt(1 + {num(slope)}^2)"))


def slat_end(sb, capacity: float, allow, connector: str, source: str  # type: ignore[no-untyped-def]
             ) -> tuple[Step, ...]:
    f45, f3060 = allow.lateral_f1_lb, allow.lateral_f1_30_60_lb
    off = abs(sb.angle_degrees - 45.0)
    if off < 1e-9:
        tail: tuple[Step, ...] = (Step(
            "F1", f"{connector} allowable along the brace at 45 deg, one connection at each "
            "end", capacity, "lb", source=source),)
    else:
        tail = (Step("F1_45", f"{connector} allowable at 45 deg", f45, "lb", source=source),
                Step("F1_30/60", f"{connector} allowable at 30 or 60 deg", f3060, "lb",
                     source=source),
                Step("F1", f"{connector} allowable at the slats' own angle, interpolated",
                     capacity, "lb", "F1_45 - (F1_45 - F1_30/60) |theta - 45| / 15",
                     f"{num(f45)} - ({num(f45)} - {num(f3060)}) x {num(off)} / 15",
                     "the maker's footnote: interpolate between the angles"))
    return (*slat_force(sb), *tail)


def slat_buckling(sb, p, length_in, d_in, b_in, fc, fc_cm, cd, emin, emin_cm, row  # type: ignore
                  ) -> tuple[Step, ...]:
    fc_star = fc * fc_cm * cd
    slender = length_in / d_in
    fce = 0.822 * emin * emin_cm / slender ** 2
    ratio = fce / fc_star
    term = (1.0 + ratio) / 1.6
    cp = term - math.sqrt(term ** 2 - ratio / 0.8)
    return (*slat_force(sb),
            Step("l/d", "slenderness of the longest braced slat", slender, "", "l / d",
                 f"{num(length_in)} / {num(d_in)}", "NDS 2018 §3.7"),
            Step("Fc*", "compression strength before stability, wet, wind duration", fc_star,
                 "psi", "Fc C_M C_D", f"{num(fc)} x {num(fc_cm)} x {num(cd)}", row),
            Step("FcE", "elastic buckling stress", fce, "psi", "0.822 E_min' / (l/d)^2",
                 f"0.822 x {num(emin * emin_cm)} / {num(slender)}^2", "NDS 2018 §3.7.1.5"),
            Step("r", "ratio of buckling stress to compression strength", ratio, "",
                 "FcE / Fc*", f"{num(fce)} / {num(fc_star)}"),
            Step("C_P", "column stability factor, sawn lumber c = 0.8", cp, "",
                 "(1 + r)/1.6 - sqrt(((1 + r)/1.6)^2 - r/0.8)",
                 f"{num(term)} - sqrt({num(term)}^2 - {num(ratio)}/0.8)", "NDS 2018 §3.7.1.5"),
            Step("P_allow", "allowable axial force on the slat", fc_star * cp * d_in * b_in,
                 "lb", "Fc* C_P d b", f"{num(fc_star)} x {num(cp)} x {num(d_in)} x {num(b_in)}"))


def clipped_bearing(sb, label, force, contact, depth, grain_deg, fc_star, fc_perp,  # type: ignore
                    f_theta, capacity) -> tuple[Step, ...]:
    area = contact * depth
    return (*slat_force(sb),
            Step("F", f"component of the slat's end force square to the {label}", force, "lb",
                 "h" if label == "post" else "h tan(theta)",
                 "" if label == "post" else
                 f"{num(sb.per_end_lb)} x tan({num(sb.angle_degrees)})"),
            Step("A", "contact area of the clipped end", area, "in^2", "c x d",
                 f"{num(contact)} x {num(depth)}"),
            Step("f_c", "bearing stress", force / area, "psi", "F / A",
                 f"{num(force)} / {num(area)}"),
            Step("F'_theta", "bearing allowable at the slat's angle to its own grain "
                 "(Hankinson)", f_theta, "psi",
                 "Fc* Fc_perp / (Fc* sin^2 a + Fc_perp cos^2 a)",
                 f"{num(fc_star)} x {num(fc_perp)} / ({num(fc_star)} x sin^2({num(grain_deg)}) "
                 f"+ {num(fc_perp)} x cos^2({num(grain_deg)}))",
                 "NDS 2018 §3.10.3"),
            Step("F_allow", f"allowable: lesser of that and the {label}'s Fc_perp", capacity,
                 "psi", "min(F'_theta, Fc_perp)", f"min({num(f_theta)}, {num(fc_perp)})"))


def centre_post_bending(sb, force, span_ft, m_uniform, point, a_ft, m_point, moment, fb, fb_allow,
                        fb_table, cd) -> tuple[Step, ...]:  # type: ignore[no-untyped-def]
    steps = [*slat_force(sb),
             Step("W_c", "load on the centre post, both bays pushing the same way", force, "lb",
                  "2 x landings x h", f"2 x {sb.landings('centre')} x {num(sb.per_end_lb)}",
                  "uniform over the post's clear height"),
             Step("L", "clear height of the post", span_ft, "ft"),
             Step("M_u", "bending moment from the uniform load", m_uniform, "lb-ft", "W_c L / 8",
                  f"{num(force)} x {num(span_ft)} / 8")]
    if point:
        steps += [Step("M_p", "bending moment from the compression bay's clipped end", m_point,
                       "lb-ft", "h a b / L",
                       f"{num(point)} x {num(a_ft)} x {num(span_ft - a_ft)} / {num(span_ft)}",
                       "the clipped end bears h just under the top plate")]
    steps += [Step("M", "design bending moment on the post", moment, "lb-ft",
                   "M_u + M_p" if point else "M_u"),
              Step("S", "section modulus of the 6x6 (5.5 in square)", 5.5 ** 3 / 6.0, "in^3",
                   "b^3 / 6", "5.5^3 / 6"),
              Step("f_b", "bending stress", fb, "psi", "12 M / S",
                   f"12 x {num(moment)} / {num(5.5 ** 3 / 6.0)}"),
              Step("F_b'", "bending allowable, wet, wind duration", fb_allow, "psi",
                   "Fb C_M C_D", f"{num(fb_table)} x 1.0 x {num(cd)}",
                   "NDS 2018 Supplement Table 4D, SP No. 2 timbers")]
    return tuple(steps)


def centre_post_ties(sb, half: float, point_part: float, reaction: float, n: int, row: float,
                     capacity: float, tie: str) -> tuple[Step, ...]:  # type: ignore[no-untyped-def]
    return (*slat_force(sb),
            Step("R", "larger end reaction of the centre post", reaction, "lb",
                 "W_c / 2 + h b / L" if point_part else "W_c / 2",
                 f"{num(half)} + {num(point_part)}" if point_part else f"{num(half)}"),
            Step("n_tie", f"{tie} connectors at each end of the post", n, ""),
            Step("F_row", f"{tie} lateral allowable, the lower of its two directions", row, "lb",
                 source="the connector's published table, see References"),
            Step("R_allow", "allowable end reaction", capacity, "lb", "n_tie F_row",
                 f"{n} x {num(row)}"))


def plate_screws(sb, label, n_fast, fastener, lateral, landings, vertical, half, withdrawal,
                 resultant, alpha_deg, z_prime, w_prime, cd, cm, z_alpha,  # type: ignore
                 row) -> tuple[Step, ...]:
    z, _side, w_per_in, thread, w_max = row
    return (*slat_force(sb),
            Step("V_s", "lateral force on each screw", lateral, "lb", "V / n",
                 f"{num(sb.shear_lb)} / {n_fast}", f"{n_fast} {fastener} in the {label}"),
            Step("W_s", "withdrawal on each screw of the tension bay", withdrawal, "lb",
                 "landings x h tan(theta) / (n/2)",
                 f"{landings} x {num(vertical)} / {num(half)}",
                 "the compression bay's end bears on the plate: no withdrawal"),
            Step("R_s", "resultant on a screw", resultant, "lb", "sqrt(V_s^2 + W_s^2)",
                 f"sqrt({num(lateral)}^2 + {num(withdrawal)}^2)"),
            Step("Z'", "lateral design value, wet, wind duration", z_prime, "lb",
                 "Z C_D C_M", f"{num(z)} x {num(cd)} x {num(cm)}",
                 "ICC-ES ER-192 row, see References"),
            Step("W'p", "withdrawal design value, wet, wind duration", w_prime, "lb",
                 "min(W x thread, W_max) C_D C_M",
                 f"min({num(w_per_in)} x {num(thread)}, {num(w_max)}) x {num(cd)} x {num(cm)}",
                 "ICC-ES ER-192 row, see References"),
            Step("Z'_a", f"allowable at {num(alpha_deg)} deg to the screw's axis", z_alpha, "lb",
                 "W'p Z' / (W'p cos^2 a + Z' sin^2 a)",
                 f"{num(w_prime)} x {num(z_prime)} / ({num(w_prime)} x cos^2({num(alpha_deg)}) "
                 f"+ {num(z_prime)} x sin^2({num(alpha_deg)}))", "NDS 2018 §12.4.1"))


def end_bearing(shear: float, area: float, fc_perp: float, post: float, cm: float
                ) -> tuple[Step, ...]:
    return (Step("V", "wind shear the panel's plates hand a chord", shear, "lb",
                 source="the deck's shear delivered to this wall; compression only, so it "
                        "serves either direction"),
            Step("A", "end grain of the plates bearing on one chord face", area, "in^2"),
            Step("f_c", "bearing stress on the chord's face", shear / area, "psi", "V / A",
                 f"{num(shear)} / {num(area)}"),
            Step("F_c-perp", "bearing allowable across the chord's grain, wet", fc_perp, "psi",
                 "Fc_perp C_M", f"{num(post)} x {num(cm)}",
                 "NDS 2018 Supplement Table 4D, SP No. 2 timbers; Table 4.3.8 wet factor"))


def collector_clips(shear: float, n: int, each: float, row: float, size: str
                    ) -> tuple[Step, ...]:
    return (Step("V", "wind shear the collector beam drags to the wall", shear, "lb",
                 source="the deck's shear delivered to this wall"),
            Step("n_clip", f"{size} clips along the collector", n, ""),
            Step("F_clip", "load on one clip", each, "lb", "V / n_clip", f"{num(shear)} / {n}"),
            Step("F_clip,allow", f"{size} lateral allowable, the lower of its two directions", row,
                 "lb", source="the connector's published table, see References"))


def strap_tension(shear: float, theta_deg: float, n: int, tension: float, steel: float,
                  per_nail: float, nails: int, capacity: float) -> tuple[Step, ...]:
    return (Step("V", "wind shear the band's straps carry", shear, "lb"),
            Step("theta", "angle of the straps above the plates", theta_deg, "deg"),
            Step("T", "tension in one strap", tension, "lb", "V / cos(theta) / n",
                 f"{num(shear)} / cos({num(theta_deg)}) / {n}"),
            Step("T_steel", "strap steel strength", steel, "lb",
                 source="the coil-strap table, see References"),
            Step("T_nails", "nails at the post end, the row pro-rated by its own nails",
                 per_nail * nails, "lb", "n_nail x per-nail",
                 f"{nails} x {num(per_nail)}"),
            Step("T_allow", "allowable: the lesser", capacity, "lb", "min(T_steel, T_nails)",
                 f"min({num(steel)}, {num(per_nail * nails)})"))


def holdown_full_height(shear: float, height: float, lever: float, uplift: float,
                        tension: float, capacity: float, holdown: str) -> tuple[Step, ...]:
    return (Step("V", "wind shear on the panel", shear, "lb"),
            Step("H", "height from the collector's top to the chord bases", height, "ft"),
            Step("d", "lever arm between the two chords", lever, "ft"),
            Step("U", "net roof uplift at the column, 0.6D + 0.6W", uplift, "lb"),
            Step("T", "tension in the chord, no wall dead load credited", tension, "lb",
                 "V H / d + U",
                 f"{num(shear)} x {num(height)} / {num(lever)} + {num(uplift)}"),
            Step("T_allow", f"{holdown} published allowable uplift", capacity, "lb",
                 source="the hold-down's published table, see References"))


def base_shear(shear: float, lateral: float, holdown: str, along: bool) -> tuple[Step, ...]:
    return (Step("V", "in-plane shear on ONE base (the plates bear on one chord)", shear, "lb"),
            Step("V_allow", f"{holdown} lateral allowable"
                 + (", oriented along the panel" if along else ", the lower direction"),
                 lateral, "lb", source="the hold-down's published table, see References"))


def pullout(tension: float, shaft: float, pad_lb: float, prism_lb: float, post: float,
            wall: float, held: float) -> tuple[Step, ...]:
    return (Step("T", "tension in the chord", tension, "lb"),
            Step("W", "weight holding the pier down: shaft + doweled pad + soil over the pad "
                 "+ post + wall", held, "lb", "sum",
                 f"{num(shaft)} + {num(pad_lb)} + {num(prism_lb)} + {num(post)} + {num(wall)}",
                 "no deck or roof dead credited"),
            Step("0.6W_D", "resisting weight at 0.6D", 0.6 * held, "lb", "0.6 W",
                 f"0.6 x {num(held)}", "ASCE 7-16 §2.4.1"))


def pad_bearing(dead: float, pad_lb: float, live: float, overturning: float, area: float,
                load_psf: float, allowable: float) -> tuple[Step, ...]:
    load = dead + pad_lb + 0.75 * live + 0.75 * overturning
    return (Step("P", "load on the pad: D + pad + 0.75 (L + S) + 0.75 overturning", load, "lb",
                 "D + pad + 0.75 L + 0.75 M_o",
                 f"{num(dead)} + {num(pad_lb)} + 0.75 x {num(live)} + 0.75 x {num(overturning)}",
                 "ASCE 7-16 §2.4.1"),
            Step("A", "plan area of the pad", area, "ft^2"),
            Step("q", "bearing pressure on the soil", load_psf, "psf", "P / A",
                 f"{num(load)} / {num(area)}"),
            Step("q_allow", "allowable soil bearing, presumptive", allowable, "psf",
                 source="IBC 2018 Table 1806.2"))
