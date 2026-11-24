"""The working for ``thermal_break_transfer``'s rows: Step chains from the rows' own values.

Each function takes the numbers the row's state is built from (the calling module passes
the variables it just computed) and returns the chain the sheet prints; the last steps
arrive at the state's demand and capacity. Combination texts live here once, so the sheet
and the analytical export see one string per kind of load.
"""

from __future__ import annotations

from typehaus.engineering.item import Step, num

#: The break's thrust and the court's movement are self-straining (a temperature effect),
#: load factor 1.0. T has no letter in the analytical export, so these carry no typed factors.
THERMAL = ("1.0T: the court's thermal closure toward the house, self-straining, load factor "
           "1.0 (ACI 318-19 §5.3.6, ASCE 7-16 §2.3.4)", ())
WINTER = ("1.0T: the court's contraction 80 F below its set temperature, self-straining, "
          "load factor 1.0 (ACI 318-19 §5.3.6, ASCE 7-16 §2.3.4)", ())
SOIL_SERVICE = ("service: dead load D, at-rest soil H and the break's thrust T, all at 1.0 "
                "(IBC §1807.2.3: safety factors on unfactored loads)", ())
POUR = ("fresh-concrete pressure during the pour, unfactored (ACI 347R-14)", ())

REQUIRED_FS = 1.5


def pour_pressure(psi: float, head_in: float, concrete_pcf: float, rating: float,
                  how: str) -> tuple[Step, ...]:
    return (Step("h", "head of fresh concrete above the board's bottom", head_in / 12.0, "ft",
                 source=how),
            Step("p", "fresh-concrete pressure", psi, "psi", "w h / 144",
                 f"{num(concrete_pcf)} x {num(head_in / 12.0)} / 144",
                 "ACI 347R-14, capped at w h"),
            Step("p_allow", "the board's compressive rating", rating, "psi",
                 source="the board's datasheet"))


def compliant_strain(alpha: float, closing_f: float, run_in: float, delta: float,
                     at_strain: float, thick_in: float, capacity: float,
                     source: str) -> tuple[Step, ...]:
    return (Step("alpha", "thermal expansion of concrete", alpha, "1/F",
                 source="PCA average, normal-weight concrete"),
            Step("dT", "closing range: service maximum less the set temperature", closing_f,
                 "F", source="the site's concrete service temperature"),
            Step("L", "the whole court's run toward the house", run_in, "in",
                 source="outer face to outer face of the court"),
            Step("delta", "largest closure of the joint (no neutral point, no shrinkage "
                 "credit)", delta, "in", "alpha dT L",
                 f"{num(alpha)} x {num(closing_f)} x {num(run_in)}"),
            Step("delta_allow", "closure at which the compliant layer reaches the strain "
                 "its stress cap is published at", capacity, "in", "strain x thickness",
                 f"{num(at_strain)} x {num(thick_in)}", source))


def board_strain(pour_psi: float, thick_in: float, modulus: float, pour_in: float,
                 closure_in: float, delta: float, rating: float, capacity: float,
                 estimated: bool, via_cap: str) -> tuple[Step, ...]:
    return (Step("p_lock", "locked-in fresh-concrete pressure", pour_psi, "psi",
                 source="zero for a board set into a stripped blockout"),
            Step("E", "board modulus" + (" (ESTIMATED: not published; it cancels in the "
                                         "ratio below)" if estimated else ""), modulus, "psi"),
            Step("pour", "squeeze the pour locks in", pour_in, "in", "p_lock t / E",
                 f"{num(pour_psi)} x {num(thick_in)} / {num(modulus)}"),
            Step("closing", "closing at the stress the board is graded at", closure_in, "in",
                 via_cap),
            Step("delta", "board strain: pour plus closing", delta, "in", "pour + closing",
                 f"{num(pour_in)} + {num(closure_in)}"),
            Step("delta_allow", "recoverable strain of the board", capacity, "in",
                 "t sigma_y / E", f"{num(thick_in)} x {num(rating)} / {num(modulus)}",
                 "the board's rated yield stress over its modulus"))


def insulation_bearing(sigma: float, pour_psi: float, demand: float, rating: float,
                       how: str) -> tuple[Step, ...]:
    return (Step("sigma", "closing stress the board passes to the house foam", sigma, "psi",
                 source="the compliant layer's published cap"),
            Step("p_lock", "locked-in pour pressure", pour_psi, "psi"),
            Step("q", "pressure on the house foam", demand, "psi", "sigma + p_lock",
                 f"{num(sigma)} + {num(pour_psi)}"),
            Step("q_allow", "house foam's compressive rating", rating, "psi", source=how))


def wall_flexure(on_wall: float, span: float, moment: float, length: float, bar: int,
                 spacing: float, area_in2: float, db: float, cover: float, h: float,
                 area: float, d: float, fy: float, fc: float, a: float, phi_mn: float
                 ) -> tuple[Step, ...]:
    return (Step("T", "thrust on the wall panel (closing + locked-in pour)", on_wall, "lb",
                 source="the board's thrust, wall patch integrated over the board"),
            Step("L", "span of the panel, footing to floor", span, "in"),
            Step("M", "largest moment, simply supported, load integrated along the span",
                 moment, "lb-in", source="statics"),
            Step("A_s", f"steel in the whole {num(length)} in panel, #{bar} at {num(spacing)} in",
                 area, "in^2", "A_bar L / s", f"{num(area_in2)} x {num(length)} / {num(spacing)}"),
            Step("d", "effective depth", d, "in", "h - cover - d_b / 2",
                 f"{num(h)} - {num(cover)} - {num(db)} / 2"),
            Step("a", "depth of the compression block", a, "in", "A_s f_y / (0.85 f'c L)",
                 f"{num(area)} x {num(fy)} / (0.85 x {num(fc)} x {num(length)})"),
            Step("phi Mn", "design moment strength of the whole panel", phi_mn, "lb-in",
                 "0.90 A_s f_y (d - a / 2)",
                 f"0.90 x {num(area)} x {num(fy)} x ({num(d)} - {num(a)} / 2)",
                 "ACI 318-19 §22.3; soil left out (generous)"))


def wall_shear(bottom: float, top: float, demand: float, fc: float, length: float, d: float,
               capacity: float) -> tuple[Step, ...]:
    return (Step("V_bot", "reaction at the footing", bottom, "lb", source="statics"),
            Step("V_top", "reaction at the floor line", top, "lb", source="statics"),
            Step("V_u", "larger reaction", demand, "lb", "max(V_bot, V_top)",
                 f"max({num(bottom)}, {num(top)})"),
            Step("phi Vc", "design one-way shear strength of the whole panel", capacity, "lb",
                 "0.75 x 2 sqrt(f'c) L d",
                 f"0.75 x 2 x sqrt({num(fc)}) x {num(length)} x {num(d)}",
                 "ACI 318-19 §22.5.5.1"))


def floor_line(top: float, band: float, demand: float, anchors: list, capacity: float
               ) -> tuple[Step, ...]:
    """``anchors``: ``[(model, F2 allowable lb, citation)]``, one per anchor counted."""
    model, each, citation = anchors[0]
    same = all(a[0] == model and a[1] == each for a in anchors)
    return (Step("R_top", "wall's top reaction", top, "lb"),
            Step("R_band", "board above the wall top", band, "lb"),
            Step("R", "load into the sill anchorage", demand, "lb", "R_top + R_band",
                 f"{num(top)} + {num(band)}"),
            Step("F2", f"one {model}'s allowable load perpendicular to the sill (F2)", each,
                 "lb", source=f"{citation}; at its C_D 1.6 and SG 0.50 lumber, generous for "
                              "an SPF sill"),
            Step("R_allow", f"the {len(anchors)} anchors on this wall's sill", capacity, "lb",
                 "n F2" if same else "sum of each anchor's F2",
                 f"{len(anchors)} x {num(each)}" if same
                 else " + ".join(num(a[1]) for a in anchors)))


def court_sliding(total: float, soil_push: float, friction: float, net: float, pcf: float,
                  fs: float | None, demand: float, capacity: float) -> tuple[Step, ...]:
    steps = [Step("T", "sum of every board's thrust on the loop", total, "lb"),
             Step("H_soil", f"retained soil's push on the court at {num(pcf)} pcf", soil_push,
                  "lb", source="the court's sliding body"),
             Step("net", "thrust left after the soil's push", net, "lb", "T - H_soil",
                  f"{num(total)} - {num(soil_push)}"),
             Step("F", "base friction of the court", friction, "lb",
                  source="the court's sliding body; passive not credited")]
    if fs is not None:
        steps += [Step("FS_req", "safety factor required", REQUIRED_FS, "",
                       source="IRC R404.4"),
                  Step("FS", "safety factor against being pushed away", fs, "", "F / net",
                       f"{num(friction)} / {num(net)}")]
    else:
        steps += [Step("push", "net push, never below zero: the thrust does not overcome "
                       "the soil", demand, "lb", "max(net, 0)", f"max({num(net)}, 0)"),
                  Step("F/1.5", "friction over the required safety factor", capacity, "lb",
                       "F / 1.5", f"{num(friction)} / {REQUIRED_FS:g}")]
    return tuple(steps)


def slab_edge(line: float, total: float, floor: float, depth: float, edge_len: float,
              area: float, psi: float, capacity: float, how: str, label: str
              ) -> tuple[Step, ...]:
    return (Step("T", "thrust of all the boards", total, "lb"),
            Step("R_floor", "share the house walls' floor line takes", floor, "lb"),
            Step("N", "thrust left for the slab edge", line, "lb", "T - R_floor",
                 f"{num(total)} - {num(floor)}"),
            Step("A", "contact area of the slab's perimeter break", area, "in^2",
                 "depth x edge length", f"{num(depth)} x {num(edge_len)}"),
            Step("q_allow", label, psi, "psi", source=how),
            Step("N_allow", "most thrust the break carries", capacity, "lb", "q_allow A",
                 f"{num(psi)} x {num(area)}"))


def slab_strut(line: float, thick: float, edge_len: float, stress: float, fc: float,
               capacity: float) -> tuple[Step, ...]:
    return (Step("N", "thrust through the slab", line, "lb"),
            Step("f", "compressive stress in the slab strut", stress, "psi",
                 "N / (t L)", f"{num(line)} / ({num(thick)} x {num(edge_len)})"),
            Step("phi fc", "plain-concrete bearing stress", capacity, "psi",
                 "0.60 x 0.85 f'c", f"0.60 x 0.85 x {num(fc)}",
                 "ACI 318-19 Table 21.2.1, §14.5.6"))


def global_sliding(mu: float, dead: float, net: float, total: float, fs: float,
                   basis: str, at_rest: float, depth: float, edge_len: float, near: float
                   ) -> tuple[Step, ...]:
    return (Step("D", "dead load of the house, a stated lower bound", dead, "lb", source=basis),
            Step("mu", "friction under the house", mu, "", source="IBC Table 1806.2"),
            Step("P_far", "at-rest soil load on the far wall, per foot", at_rest, "plf",
                 "K d^2 / 2", f"at-rest pressure over d = {num(depth, 6)} ft"),
            Step("net", "net at-rest soil resisting: far wall's length less the near face's "
                 "backfilled length", net, "lb", "P_far (L_far - L_near) / 12",
                 f"{num(at_rest)} x ({num(edge_len)} - {num(near)}) / 12"),
            Step("H", "thrust to be resisted", total, "lb"),
            Step("FS_req", "safety factor required", REQUIRED_FS, "", source="IRC R404.4"),
            Step("FS", "safety factor against sliding of the house", fs, "",
                 "(mu D + net) / H", f"({num(mu)} x {num(dead)} + {num(net)}) / {num(total)}"))


def far_wall(at_rest_load: float, unresisted: float, demand: float, lateral: float,
             depth: float, length_ft: float, capacity: float, friction: float,
             total: float) -> tuple[Step, ...]:
    return (Step("P_rest", "at-rest soil load on the far wall", at_rest_load, "lb",
                 "P_far L", f"{num(at_rest_load / length_ft, 6)} x {num(length_ft)}",
                 "P_far from the sliding row"),
            Step("F_house", "friction under the house", friction, "lb",
                 source="mu D from the sliding row"),
            Step("P_extra", "thrust friction does not take", unresisted, "lb",
                 "max(0, T - F_house)", f"max(0, {num(total)} - {num(friction)})"),
            Step("P", "load on the far wall's soil", demand, "lb", "P_rest + P_extra",
                 f"{num(at_rest_load)} + {num(unresisted)}"),
            Step("P_allow", "lateral bearing of the soil on the far wall", capacity, "lb",
                 "q d^2 L / 2", f"{num(lateral)} x {num(depth, 6)}^2 x {num(length_ft)} / 2",
                 "IBC Table 1806.2, lateral bearing"))


def near_line(result_load: float, moment: float, shear: float, phi_mn: float, phi_vn: float,
              b: float, h: float, root: float, bed: float, kind: str, mesh_in: float,
              ec_per_root_fc: float) -> tuple[Step, ...]:
    solve = Step("solve", "total load on the near footing line, solved as a beam in plan "
                 "on a compression-only bed and struts", result_load, "lb",
                 source=f"finite elements: the line is a plain-concrete beam in plan, EI from "
                        f"E_c {num(ec_per_root_fc)} sqrt(f'c) on its full section; 2-node cubic "
                        f"(Hermite) beam elements at a {num(mesh_in)} in mesh, with nodes also "
                        "at each load edge and strut; the slab break a Winkler bed of "
                        f"{num(bed)} lb/in per in = E x depth / thickness; each "
                        "perpendicular footing chain that reaches the far line a spring "
                        "E_c A / L; bed and springs compression only, solved by an active set "
                        "(springs and bed that open are removed and the line re-solved). "
                        "Checked in the court free body note: §11m.1 sets out the method and "
                        "solves it exactly at the earlier strip size; §11p re-solves it "
                        "independently at this geometry and reproduces M and the peak "
                        "deflection (V is not separately re-checked there)")
    if kind == "flexure":
        return (solve,
                Step("M", "largest moment in the line", moment, "lb-in",
                     source="the finite-element solution above, the largest |M| over the "
                            "elements"),
                Step("phi Mn", "plain-concrete flexural strength of the line", phi_mn, "lb-in",
                     "0.60 x 5 sqrt(f'c) b h^2 / 6",
                     f"0.60 x 5 x {num(root)} x {num(b)} x {num(h)}^2 / 6",
                     "ACI 318-19 §14.5.2.1; thickness less 2 in per §14.5.1.7"))
    return (solve,
            Step("V", "largest shear in the line", shear, "lb",
                 source="the finite-element solution above, the largest |V| over the "
                        "elements"),
            Step("phi Vn", "plain-concrete shear strength of the line", phi_vn, "lb",
                 "0.60 x (4/3) sqrt(f'c) b h",
                 f"0.60 x (4/3) x {num(root)} x {num(b)} x {num(h)}", "ACI 318-19 §14.5.5.1"))


def near_line_peak(edge_e: float, peak_in: float, thick: float, peak: float, cap: float,
                   how: str) -> tuple[Step, ...]:
    return (Step("v", "largest compression of the slab break in the solution", peak_in, "in",
                 source="the near-line finite-element solution (house near-line plan "
                        "flexure, above): the largest nodal deflection into the bed; "
                        "independently re-solved in the court free body note §11p"),
            Step("sigma", "largest stress on the break", peak, "psi", "E v / t",
                 f"{num(edge_e)} x {num(peak_in)} / {num(thick)}"),
            Step("sigma_allow", "stress the break may carry", cap, "psi", source=how))


def winter(total: float, count: int, demand: float, area: float, fy: float, capacity: float,
           friction: float, house: float, far: float, relax: float, soil: float, pcf: float,
           parts: dict, relief: tuple[float, float, float], where: str) -> tuple[Step, ...]:
    mu = parts["mu"]
    factor, ka, k0 = relief
    weight = friction / mu if mu else 0.0
    return (Step("W_conc", "concrete on the house side of the strut: the spliced walls' "
                 "footings and stems", parts["concrete"], "lb",
                 source="read off the resolved solids, 150 pcf"),
            Step("W_soil", "soil on those walls' heels, taken to the stem tops (not grade) at "
                 f"{num(parts['soil_pcf'])} pcf", parts["soil"], "lb",
                 source="the top of the unit-weight band; the height above grade stands in "
                        "for the porch, balcony and veneer dead load those walls carry, so "
                        "the weight is an upper bound"),
            Step("W_cast", "other cast walls bedded on that side and cast with them",
                 parts["extra"], "lb", source="concrete only, 150 pcf"),
            Step("W_house", "weight on the house side of the strut, an upper bound",
                 parts["weight"], "lb", "W_conc + W_soil + W_cast",
                 f"{num(parts['concrete'])} + {num(parts['soil'])} + {num(parts['extra'])}"),
            Step("mu_max", "bed friction for this row: the upper bound, the SPECIFIED MAXIMUM (a "
                 "confirmed report value once one is entered)", mu, "",
                 source="section 6; more friction pulls harder on the side runs, so the upper "
                        "bound is the bounding case for winter tension, the reverse of the "
                        "sliding rows, which take the specified minimum"),
            Step("F_house", "friction mobilised on the house side of the strut", house, "lb",
                 "mu_max W_house", f"{num(mu)} x {num(parts['weight'])}"),
            Step("N'", f"weight of the whole court body at {num(pcf)} pcf", weight, "lb",
                 source="the court's sliding body"),
            Step("relax", "share of the at-rest soil push that still acts on the far side",
                 relax, "", "0.9 x K_a / K_0", f"{num(factor)} x {num(ka)} / {num(k0)}",
                 "the soil relaxes from at-rest toward active as the court moves off it; "
                 "0.9 because that push reduces the tension (H counteracting, ASCE 7-16 "
                 "§2.3.1)"),
            Step("F_far", "far side: its friction less the relaxed soil push", far, "lb",
                 "mu_max N' - F_house - relax H_soil",
                 f"{num(mu)} x {num(weight)} - {num(house)} - {num(relax)} x {num(soil)}",
                 f"H_soil is the dry resultant thrust at {num(pcf)} pcf"),
            Step("T_tot", "tension the court can mobilise: the smaller side", total, "lb",
                 "min(F_house, F_far)", f"min({num(house)}, {num(far)})",
                 "rigid-plastic upper bound"),
            Step("T_u", f"tension in one of the {count} side lines", demand, "lb",
                 "T_tot / n", f"{num(total)} / {count}"),
            Step("A_s", where, area, "in^2", source="bars crossing the section (rebar model)"),
            Step("phi Tn", "design tension strength, concrete not credited", capacity, "lb",
                 "0.90 A_s f_y", f"0.90 x {num(area)} x {num(fy)}",
                 "ACI 318-19 §21.2.2; cracked section"))


def winter_joint(demand: float, width: float, depth: float, fc: float, cap: float,
                 stress: float) -> tuple[Step, ...]:
    return (Step("T_u", "tension across the joint", demand * width * depth, "lb"),
            Step("f_t", "tension stress on the footing alone", stress, "psi",
                 "T_u / (b h)", f"{num(demand)} per section of {num(width)} x {num(depth)} in"),
            Step("phi ft", "plain-concrete tension stress", cap, "psi",
                 "0.60 x 5 sqrt(f'c)", f"0.60 x 5 x sqrt({num(fc)})",
                 "ACI 318-19 §14.5.2.1, read for a direct tension"))


def joint_closure(thermal: float, slide: float, demand: float, moved: float, pcf: float,
                  anchor: float, capacity: float, at_strain: float, thick: float,
                  squeeze: float) -> tuple[Step, ...]:
    return (Step("delta_T", "thermal closure of the whole run", thermal, "in",
                 source="the compliant layer strain row"),
            Step("mu_move", "share of the court's friction mobilised that counts "
                 "(boards set after the backfill: the increment only)", moved, "",
                 source=f"the court's cases at {num(pcf)} pcf"),
            Step("u", "ground motion at which a presumptive lateral value is mobilised",
                 anchor, "in", source="IBC §1806.3.4 (tabular value, the lateral anchor)"),
            Step("delta_s", "sliding of the court toward the house", slide, "in", "mu_move u",
                 f"{num(moved)} x {num(anchor)}"),
            Step("delta", "joint closure the layer must take", demand, "in",
                 "delta_T + delta_s", f"{num(thermal)} + {num(slide)}"),
            Step("delta_allow", "layer thickness x the strain its cap is published at",
                 capacity, "in", "strain x thickness", f"{num(at_strain)} x {num(thick)}"),
            Step("squeeze", "foam board's own squeeze at the cap (reported, not credited)",
                 squeeze, "in"))

