"""The working for a deck's delivery to its neighbour (calc-sheet pattern).

Joint straps, nailers, plate clips, receiving walls, the open front's chords and couples.
Each function returns the :class:`~typehaus.engineering.item.Step` chain one state prints,
from the very numbers it is built from. A group of members running the same chain (the
fourteen nailers, the receiving walls) calls one function, and the sheet prints a step
once and writes "as above" after it.
"""

from __future__ import annotations

from typehaus.engineering.item import Step, num
from typehaus.engineering.lateral_working import (  # noqa: F401
    GEOMETRY,
    NET_UPLIFT,
    WIND_ASD,
    WIND_NO_DEAD,
    cw,
)

_V = "the deck's wind shear delivered across the joint; see the Independent check note"


def strap_factor(delivery) -> float:  # type: ignore[no-untyped-def]
    """The installed-nail factor ``joint_attachment.installed_strap_capacity`` applies."""
    recipe = delivery.joint_nailing
    if recipe is None:
        return 1.0
    return min(recipe.strap_nails_each_end / recipe.rated_strap_nails_each_end, 1.0)


def strap_allow(delivery, rated: float, capacity: float) -> tuple[Step, ...]:  # type: ignore
    recipe = delivery.joint_nailing
    k = strap_factor(delivery)
    detail = (f"{recipe.strap_nails_each_end} installed / {recipe.rated_strap_nails_each_end} "
              "rated" if recipe is not None else "")
    return (Step("T_rated", "strap's published allowable axial load, full nail schedule", rated,
                 "lb", source="the strap's evaluation-report table, see References"),
            Step("k", "reduction for the installed end nail schedule", k, "",
                 "min(installed / rated, 1)", detail),
            Step("T_allow", "installed allowable of one strap", capacity, "lb", "T_rated k",
                 f"{num(rated)} x {num(k)}"))


def strap_across(v_across: float, n: int, delivery, rated: float, capacity: float
                 ) -> tuple[Step, ...]:  # type: ignore[no-untyped-def]
    return (Step("V_x", "wind shear across the joint, in strap tension", v_across, "lb",
                 source=_V),
            Step("n_strap", "joint straps sharing it", n, ""),
            Step("T_x", "tension in one strap", v_across / n, "lb", "V_x / n_strap",
                 f"{num(v_across)} / {n}"),
            *strap_allow(delivery, rated, capacity))


def strap_rotation(v_along: float, lever: float, couple: float, second: float, arm: float,
                   worst: float, delivery, rated: float, capacity: float
                   ) -> tuple[Step, ...]:  # type: ignore[no-untyped-def]
    return (Step("V_a", "wind shear along the joint", v_along, "lb", source=_V),
            Step("e", "distance from the joint to where the shear resolves", lever, "ft"),
            Step("M", "rotation couple", couple, "lb-ft", "V_a e",
                 f"{num(v_along)} x {num(lever)}"),
            Step("sum x^2", "sum of squared strap distances from the strap line's centre",
                 second, "ft^2"),
            Step("x_max", "distance of the end strap from the centre", arm, "ft"),
            Step("T_rot", "tension in the end strap, linear couple over the stations", worst,
                 "lb", "M x_max / sum x^2", f"{num(couple)} x {num(arm)} / {num(second)}"),
            *strap_allow(delivery, rated, capacity))


def nailer(share: float, worst: float | None, chord_bound: float | None, demand: float,
           usable_in: float, spacing_in: float, nails: int, z: float, mode: str, cd: float,
           capacity: float, tag: str) -> tuple[Step, ...]:
    if worst is None or chord_bound is None:
        top: tuple[Step, ...] = (Step("T_x", "tension in one strap from the across-joint shear",
                                      share, "lb"),
                                 Step("T_d", "load the nailer must pass into the deck", demand,
                                      "lb", "T_x"))
    else:
        top = (Step("T_x", "tension in one strap from the across-joint shear", share, "lb"),
               Step("T_rot", "tension in the end strap from the rotation couple", worst, "lb"),
               Step("T_chd", "the same couple read as chord forces, M / l_j", chord_bound, "lb"),
               Step("T_d", "load the nailer must pass into the deck: the across share plus "
                    "the larger reading of the couple", demand, "lb",
                    "T_x + max(T_rot, T_chd)",
                    f"{num(share)} + max({num(worst)}, {num(chord_bound)})"))
    return (*top,
            Step("l_u", "usable length of the nailing row", usable_in, "in",
                 "block length - 2 x deck edge distance"),
            Step("N", "nails in one row", nails, "", "ceil(l_u / s) + 1",
                 f"ceil({num(usable_in)} / {num(spacing_in)}) + 1"),
            Step("Z", f"single-shear nail value, yield mode {mode}", z, "lb",
                 source="NDS 2018 §12.3.1"),
            Step("C_D", "load duration factor, wind", cd, "", source="NDS 2018 Table 2.3.2"),
            Step(f"F_{tag}", "allowable load on the nailer", capacity, "lb", "N Z C_D",
                 f"{nails} x {num(z)} x {num(cd)}"))


def plate_clips(v_along: float, n: int, size: str, row: float) -> tuple[Step, ...]:
    return (Step("V_a", "wind shear along the joint", v_along, "lb", source=_V),
            Step("n_pc", f"{size} plate clips", n, ""),
            Step("F_pc", "load on one plate clip", v_along / n, "lb", "V_a / n_pc",
                 f"{num(v_along)} / {n}"),
            Step("F_pc,allow", f"{size} lateral allowable, the lower of its two directions", row,
                 "lb", source="the connector's published table, see References"))


def line_shear(force: float, provided: float, required: float, surplus: float, v: float,
               v_allow: float, wall: str) -> tuple[Step, ...]:
    return (Step("F_w", f"wind shear delivered to {wall}", force, "lb", source=_V),
            Step("L_prov", "braced length the line provides", provided, "ft",
                 source="IRC R602.10 braced-wall reading of the line"),
            Step("L_req", "braced length the line needs for its own building", required, "ft",
                 source="IRC R602.10.3"),
            Step("L_sur", "surplus length", surplus, "ft", "L_prov - L_req",
                 f"{num(provided)} - {num(required)}", "IRC R301.1.3"),
            Step("v", "unit shear on the surplus", v, "plf", "F_w / L_sur",
                 f"{num(force)} / {num(surplus)}"),
            Step("v_allow", "allowable unit shear of the wall's authored sheathing", v_allow,
                 "plf", source="the wall's authored SDPWS Table 4.3A row, see References"))


def overturning(force: float, provided: float, height: float, tension: float,
                capacity: float, device: str) -> tuple[Step, ...]:
    return (Step("F_w", "wind shear delivered to the wall", force, "lb"),
            Step("L_prov", "braced length the line provides", provided, "ft"),
            Step("v", "unit shear on that length", force / provided, "plf", "F_w / L_prov",
                 f"{num(force)} / {num(provided)}"),
            Step("h", "wall height", height, "ft"),
            Step("T", "tension at the panel end, no dead load credited", tension, "lb",
                 "v h", f"{num(force / provided)} x {num(height)}"),
            Step("T_allow", f"{device} published allowable uplift", capacity, "lb",
                 source="the hold-down's published table, see References"))


def roof_increment(shear: float, resultant: float, lo: float, hi: float, to_hi: float,
                   to_lo: float, depth: float, v: float, v_allow: float, tag: str
                   ) -> tuple[Step, ...]:
    return (Step("V", "wind shear entering the receiving deck", shear, "lb", source=_V),
            Step("r", "station where it enters, across the wind", resultant, "ft"),
            Step("x_lo", "station of the lower receiving line", lo, "ft"),
            Step("x_hi", "station of the upper receiving line", hi, "ft"),
            Step("F_hi", "share to the upper line (lever rule)", to_hi, "lb",
                 "V (r - x_lo) / (x_hi - x_lo)",
                 f"{num(shear)} x ({num(resultant)} - {num(lo)}) / ({num(hi)} - {num(lo)})"),
            Step("F_lo", "share to the lower line", to_lo, "lb", "V - F_hi",
                 f"{num(shear)} - {num(to_hi)}"),
            Step("d", "depth of the deck along which the shear enters", depth, "ft",
                 source="the receiving walls' own length"),
            Step("v", f"unit shear increment in {tag}", v, "plf", "max(F_lo, F_hi) / d",
                 f"{num(max(to_hi, to_lo))} / {num(depth)}"),
            Step("v_allow", "allowable unit shear of the deck's sheathing and nailing", v_allow,
                 "plf", source="the deck's authored SDPWS Table 4.2A row, see References"))


def chord_tension(couple: float, spacing: float, force: float, area: float, stress: float,
                  allow: float, ft_table: float, cm: float) -> tuple[Step, ...]:
    return (Step("M", "open-front couple", couple, "lb-ft",
                 source="the along-joint shear x its lever to the joint's strap line"),
            Step("W'", "spacing of the deck's two chords", spacing, "ft"),
            Step("T_ch", "chord force", force, "lb", "M / W'", f"{num(couple)} / {num(spacing)}",
                 "SDPWS-2015 §4.2.5.2"),
            Step("A", "section of the glulam chord", area, "in^2"),
            Step("f_t", "tension stress", stress, "psi", "T_ch / A",
                 f"{num(force)} / {num(area)}"),
            Step("F_t'", "tension allowable, wet, wind duration", allow, "psi",
                 "Ft C_M C_D", f"{num(ft_table)} x {num(cm)} x 1.6",
                 "NDS 2018 Supplement Table 5A, 24F-V4 DF"))


def end_strap_chord(force: float, share: float, capacity: float, n: int, delivery, rated: float
                    ) -> tuple[Step, ...]:  # type: ignore[no-untyped-def]
    return (Step("T_ch", "chord force crossing the joint through an end strap", force, "lb",
                 source="M / W' as above"),
            Step("T_x", "that strap's own across-joint tension", share, "lb",
                 "V_x / n_strap", f"V_x / {n}"),
            Step("T_sum", "the two added linearly (a conservative combination of the "
                 "separate wind cases)", force + share, "lb", "T_ch + T_x",
                 f"{num(force)} + {num(share)}"),
            *strap_allow(delivery, rated, capacity))


def chord_block(force: float, n: int, share: float, demand: float, row: float, size: str
                ) -> tuple[Step, ...]:
    return (Step("T_ch", "chord force into the block under the end strap", force, "lb"),
            Step("n_cp", f"{size} plates joining the chord to the block", n, ""),
            Step("T_c", "the plate's own collector share, added linearly", share, "lb"),
            Step("F_cp", "load on one plate", demand, "lb", "T_ch / n_cp + T_c",
                 f"{num(force)} / {n} + {num(share)}"),
            Step("F_cp,allow", f"{size} lateral allowable, the lower of its two directions", row,
                 "lb", source="the connector's published table, see References"))


def couple_line(couple: float, spacing: float, force: float, provided: float,
                required: float, surplus: float, v: float, v_allow: float, wall: str,
                case: str) -> tuple[Step, ...]:
    return (Step(f"M_{case}", f"{case} couple the joint hands on", couple, "lb-ft"),
            Step("d", "spacing of the two far receiving lines", spacing, "ft"),
            Step(f"F_{case}", "force on one far line", force, "lb", "M / d",
                 f"{num(couple)} / {num(spacing)}"),
            Step("L_sur", "surplus braced length of the line", surplus, "ft",
                 "L_prov - L_req", f"{num(provided)} - {num(required)}", "IRC R301.1.3"),
            Step("v", f"unit shear on {wall}'s surplus", v, "plf", f"F_{case} / L_sur",
                 f"{num(force)} / {num(surplus)}"),
            Step("v_allow", "allowable unit shear of the wall's authored sheathing", v_allow,
                 "plf", source="the wall's authored SDPWS Table 4.3A row, see References"))


def end_strap_couple(v: float, lever: float, couple: float, strap_line: float, pair: float,
                     chord_ew: float, capacity: float, delivery, rated: float
                     ) -> tuple[Step, ...]:  # type: ignore[no-untyped-def]
    return (Step("V_y", "N-S wind shear at 100% on the screen", v, "lb", source=_V),
            Step("e", "distance from the screen to where the deck's shear resolves", lever,
                 "ft"),
            Step("M_ns", "N-S couple", couple, "lb-ft", "V_y e", f"{num(v)} x {num(lever)}"),
            Step("l_s", "length of the strap line", strap_line, "ft"),
            Step("F_p", "force on each end strap, a pair of opposite forces", pair, "lb",
                 "M_ns / l_s", f"{num(couple)} / {num(strap_line)}"),
            Step("T_ch", "E-W chord force added linearly", chord_ew, "lb"),
            Step("T_sum", "demand on an end strap", pair + chord_ew, "lb", "F_p + T_ch",
                 f"{num(pair)} + {num(chord_ew)}"),
            *strap_allow(delivery, rated, capacity))


_PART_SYMBOL = {
    "canopy deck share": "F_deck", "N-S couple": "F_cpl,NS", "E-W couple": "F_cpl,EW",
    "landing ties along": "F_tie,al", "landing ties across the E-W wall, by the roof": "F_tie,ac",
    "landing ties across the N-S walls, by the roof": "F_tie,ac",
}


def summed(parts: dict[str, float], total: float, surplus: float, v: float, v_allow: float,
           wall: str, case: str) -> tuple[Step, ...]:
    return (*[Step(_PART_SYMBOL.get(name, f"F_{i}"), name, value, "lb")
              for i, (name, value) in enumerate((p for p in parts.items() if p[1]), 1)],
            Step("F_sum", f"every delivery into {wall} added ({case})", total, "lb",
                 "sum of the deliveries above"),
            Step("L_sur", "surplus braced length of the line", surplus, "ft"),
            Step("v", f"summed unit shear on {wall}'s surplus", v, "plf", "F_sum / L_sur",
                 f"{num(total)} / {num(surplus)}"),
            Step("v_allow", "allowable unit shear of the wall's authored sheathing", v_allow,
                 "plf", source="the wall's authored SDPWS Table 4.3A row, see References"))


def head_collector(uplift: float, share: int, up_allow: float, force: float, direct: float,
                   lateral: float, across: float, perpendicular: float, unity: float,
                   rule: str) -> tuple[Step, ...]:
    return (Step("U", "net uplift at the column head, 0.6D + 0.6W", max(uplift, 0.0), "lb"),
            Step("U_allow", "head tie's published allowable uplift", up_allow, "lb",
                 source="the connector's published table, see References"),
            Step("V_line", "in-plane force on this line: its direct share with its "
                 "torsional increment", force, "lb",
                 source=f"direct share {num(direct)} lb x the torsion multiplier"),
            Step("V_allow", "head tie's published lateral allowable, in the plane", lateral,
                 "lb", source="the connector's published table"),
            Step("V_x", "force across the line from the torsional couple", across, "lb"),
            Step("V_x,allow", "head tie's lateral allowable across the line", perpendicular,
                 "lb"),
            Step("I", "linear interaction of the three", unity, "",
                 "(U / n) / U_allow + V_line / V_allow + V_x / V_x,allow",
                 f"({num(max(uplift, 0.0))} / {share}) / {num(up_allow)} + {num(force)} / "
                 f"{num(lateral)} + {num(across)} / {num(perpendicular)}", rule),
            Step("I_allow", "interaction limit", 1.0, "", source=rule))


def strap_line(force: float, n: int, per_strap: float, capacity: float,
               size: str) -> tuple[Step, ...]:
    return (Step("F_sl", "E-W line reaction collected by the strap line", force, "lb",
                 source="the line's direct share with its torsional increment"),
            Step("n_sl", f"{size} ties in the line", n, ""),
            Step("T_sl", "load on one tie, along the joint", per_strap, "lb", "F_sl / n_sl",
                 f"{num(force)} / {n}"),
            Step("T_sl,allow", f"{size} published allowable, the steel strength", capacity, "lb",
                 source="the connector's published table, see References"))
