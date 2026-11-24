"""The working for ``retaining_system``'s rows: Step chains from the court's own bodies.

Called by the modules that compute each row (``retaining_system_cases``, ``_rows``,
``_fallback``, ``retaining_system``) with the very values the state is built from, so the
sheet cannot drift from the ratio. Every chain ends on the state's demand and capacity.
"""

from __future__ import annotations

from typehaus.engineering.item import Step, num

REQUIRED_FS = 1.5

_SERVICE = "service loads, no load factors (IBC §1807.2.3: FS 1.5 on unfactored loads)"
#: ``case key -> (combination text, letters)`` for the sliding rows.
COMBINATIONS = {
    "dry": (f"D + H, at-rest earth, {_SERVICE}", (("D", 1.0), ("H", 1.0))),
    "perched": (f"D + H, perched water at H/2 on the retained side, {_SERVICE}",
                (("D", 1.0), ("H", 1.0))),
    "snow": (f"D + H + S, ground snow on the terrace as an earth surcharge, {_SERVICE}",
             (("D", 1.0), ("H", 1.0), ("S", 1.0))),
    "wind": ("D + H + 0.6W, ASD wind on the court (ASCE 7-16 §2.4.1; IBC §1807.2.3 at service)",
             (("D", 1.0), ("H", 1.0), ("W", 0.6))),
    "flooded court": (f"D + H, court flooded to its lowest threshold, water both sides, "
                      f"{_SERVICE}", (("D", 1.0), ("H", 1.0))),
    "deep, soakaway full": (f"D + H, soakaway full to its lip, water both sides, {_SERVICE}",
                            (("D", 1.0), ("H", 1.0))),
}
SERVICE_BACKFILL = (f"D + H, staged backfill, {_SERVICE}", (("D", 1.0), ("H", 1.0)))
STRENGTH = ("strength: 1.6H on the thrust (ASCE 7-16 §2.3.1, IBC 2018 §1605.2)",
            (("H", 1.6),))


def sliding_steps(body, water, fs: float) -> tuple[Step, ...]:  # type: ignore[no-untyped-def]
    """One sliding case: each push's thrust, the body's weight, and ``FS = mu N' / H``."""
    out: list[Step] = []
    forces = []
    for p in body.pushes:
        earth, wat, snow, lat = body.thrust_terms(p, water)
        depth = p.top_ft - body.plane_ft
        t = body.thrust_per_ft(p, water)
        head = 0.0 if water.level_ft is None else min(depth, max(0.0, water.level_ft
                                                                  - body.plane_ft))
        out.append(Step(
            f"T_{p.tag}", f"thrust per foot on {p.tag}'s face", t, "plf",
            "earth + unbalanced water + snow + apron surcharge",
            f"{num(earth)} earth + {num(wat)} water + {num(snow)} snow + {num(lat)} apron; "
            f"K {num(p.efp)} psf/ft, depth d {num(depth)} ft, water head {num(head)} ft",
            "earth K d^2 / 2 when dry; below water K0 x (gamma - 62.4) and the water's own "
            "62.4 h^2 / 2 (retained side only); snow K0 x ground snow x d"))
        forces.append(t * p.width_ft)
        out.append(Step(f"w_{p.tag}", f"width {p.tag}'s push acts over", p.width_ft, "ft",
                        source="the body's projected width, corner squares included"))
    out.append(Step(
        "H", "resultant thrust on the whole body (2-D vector sum)", body.resultant(water),
        "lb", "|sum of T_i w_i along each wall's push direction| (+ wind where the case has it)",
        " ; ".join(f"{num(f)} lb" for f in forces),
        "opposed walls cancel in equilibrium"))
    parts = body.parts(water)
    out.append(Step(
        "N'", "weight on the sliding plane (buoyant below water where both sides are wet)",
        body.weight(water), "lb", "sum of the body's parts",
        " + ".join(f"{k} {num(v)}" for k, v in parts.items()),
        "volumes read off the resolved solids; concrete 150 pcf, stone 100 pcf"))
    out += [Step("mu", f"friction on the {body.label}", body.friction, "",
                 source="the court's soil basis, section 6"),
            Step("F", "base friction", body.friction * body.weight(water), "lb", "mu N'",
                 f"{num(body.friction)} x {num(body.weight(water))}"),
            Step("FS_req", "safety factor required", REQUIRED_FS, "", source="IRC R404.4"),
            Step("FS", "safety factor against sliding", fs, "", "F / H",
                 f"{num(body.friction * body.weight(water))} / {num(body.resultant(water))}")]
    return tuple(out)


def strut_steps(*, w1: float, l1: float, w2: float, l2: float, tag1: str, tag2: str,
                simple: float, moment: float, reaction: float, demand: float, factor: float,
                thickness: float, height: float, fc: float, span: float, slender: float,
                phi: float, coefficient: float, capacity: float) -> tuple[Step, ...]:
    steps = [
        Step("w_1", f"thrust per foot along the strut from {tag1}", w1, "plf",
             source="the sliding row's thrust, resolved along the strut axis"),
        Step("l_1", f"span of {tag1}'s footing", l1, "ft")]
    if l2:
        steps += [
            Step("w_2", f"whole at-rest thrust of {tag2}'s footing", w2, "plf",
                 source="at-rest pressure to the footing underside"),
            Step("l_2", f"span of {tag2}'s footing", l2, "ft")]
    steps += [Step("R_simple", "reaction if each span were simply supported", simple, "lb",
                   "w_1 l_1 / 2 + w_2 l_2 / 2",
                   f"{num(w1)} x {num(l1)} / 2 + {num(w2)} x {num(l2)} / 2")]
    if l2:
        steps.append(Step(
            "M_prop", "continuity moment at the strut over the two spans", moment, "lb-ft",
            "(w_1 l_1^3 + w_2 l_2^3) / (8 (l_1 + l_2))",
            f"({num(w1)} x {num(l1)}^3 + {num(w2)} x {num(l2)}^3) / (8 x ({num(l1)} + "
            f"{num(l2)}))"))
    steps += [
        Step("R", "two-span continuous reaction at the strut", reaction, "lb",
             "R_simple + M_prop / l_1 + M_prop / l_2" if l2 else "R_simple",
             f"{num(simple)} + {num(moment)} / {num(l1)} + {num(moment)} / {num(l2)}" if l2
             else num(simple)),
        Step("P_u", "factored force in the strut, 1.6 on the thrust", demand, "lb", "1.6 R",
             f"{num(factor)} x {num(reaction)}", "IBC 2018 §1605.2 / ASCE 7-16 §2.3.1 on H"),
        Step("lambda", "slenderness reduction of the plain strut", slender, "",
             "1 - (12 l_c / (32 t))^2", f"1 - (12 x {num(span)} / (32 x {num(thickness)}))^2",
             "ACI 318-19 §14.5.4"),
        Step("phi Pn", "design axial strength of the plain strut", capacity, "lb",
             "phi 0.45 f'c t h lambda",
             f"{num(phi)} x {num(coefficient)} x {num(fc)} x {num(thickness)} x "
             f"{num(height)} x {num(slender)}", "ACI 318-19 §14.5.4, phi from Table 21.2.1")]
    return tuple(steps)


def plan_steps(*, side: bool, w: float, width: float, own: float, load: float, span: float,
               factor: float, moment: float, lever: float, demand: float, tie_area: float,
               fy: float, phi: float, capacity: float, tag: str) -> tuple[Step, ...]:
    steps = [Step("w", f"thrust per foot of {tag}'s face", w, "plf",
                  source="the dry sliding row's thrust")]
    if side:
        steps.append(Step("q", "line load on the footing in plan: the whole thrust "
                          "(its base friction is spent north-south)", load, "plf"))
    else:
        steps += [
            Step("F_own", "this footing's own base friction along the thrust", own, "lb",
                 "mu x weight on the footing", "from the sliding body"),
            Step("q", "line load in plan: thrust less its own base friction", load, "plf",
                 "(w x width - F_own) / width",
                 f"({num(w)} x {num(width)} - {num(own)}) / {num(width)}")]
    return (*steps,
            Step("L", "span of the footing in plan", span, "ft"),
            Step("M_u", "factored moment of the plan beam, simple span", moment, "ft-lb",
                 "1.6 q L^2 / 8", f"{num(factor)} x {num(load)} x {num(span)}^2 / 8",
                 "IBC 2018 §1605.2 / ASCE 7-16 §2.3.1 on H; fixed ends would take 2/3"),
            Step("z", "lever arm of the strut-and-tie arch (stem line to toe-edge tie)",
                 lever, "in", source="geometry of the footing and the tie bars"),
            Step("T_u", "factored tie force", demand, "lb", "12 M_u / z",
                 f"12 x {num(moment)} / {num(lever)}", "ACI 318-19 Ch. 23 strut and tie"),
            Step("phi Tn", "design strength of the tie bars", capacity, "lb",
                 "phi A_s f_y", f"{num(phi)} x {num(tie_area)} x {num(fy)}",
                 "ACI 318-19 Ch. 23, phi from Table 21.2.1"))


def staged_steps(body, worst: float, empty: float, loop_only: float, rule: float
                 ) -> tuple[Step, ...]:  # type: ignore[no-untyped-def]
    heights = [(p.tag, p.top_ft - body.plane_ft) for p in body.pushes]
    return (
        Step("mu", "friction on the footing plane", body.friction, ""),
        Step("N'", "completed body's weight, concrete and heel soil", body.weight(), "lb",
             source="the dry sliding row's body"),
        Step("H_i", "full height of each retained side", heights[0][1], "ft",
             numbers="; ".join(f"{t} {num(h)}" for t, h in heights),
             source="top of the retained soil to the footing plane"),
        Step("FS_stage", "worst safety factor over every fill stage the rule allows", worst,
             "", f"min over fill fractions f_i in twelfths of H_i, spread <= {rule:.0%}, of "
             "mu (N'_stage) / |sum of the thrusts K (f_i H_i)^2 w_i / 2|",
             "earth only, spliced walls empty, apron not yet placed",
             "IRC R404.4; the backfill rule on the drawing"),
        Step("FS_empty", "worst with one side empty and two full (not permitted)", empty, "",
             source="reported"),
        Step("FS_loop", "worst under the rule without the spliced walls' concrete",
             loop_only, "", source="reported"),
        Step("FS_req", "safety factor required", REQUIRED_FS, "", source="IRC R404.4"),
        Step("FS", "safety factor in the worst allowed stage", worst, ""))


def fallback_steps(*, passive: float, submerged: float, cap: float, phi_mn: float, arm: float,
                   section: float, width_in: float, fc: float, credit: float, length: float,
                   z1: float, z2: float, lateral: float, friction: float | None,
                   resultant: float | None, fs: float) -> tuple[Step, ...]:
    steps = [
        Step("P_p", "class-3 lateral bearing on the wall's face, per foot", passive, "plf",
             "q (z_2^2 - z_1^2) / 2", f"{num(lateral)} x ({num(z2)}^2 - {num(z1)}^2) / 2",
             "IBC Table 1806.2 presumption, IBC §1806.3.1; depths below the court floor"),
        Step("S", "section modulus of the 12 in plain lean wall", section, "in^3",
             "b h^2 / 6", f"12 x {num(width_in)}^2 / 6"),
        Step("phi Mn", "plain wall's cantilever strength", phi_mn, "ft-lb/ft",
             "0.60 x 5 sqrt(f'c) S / 12", f"0.60 x 5 x sqrt({num(fc)}) x {num(section)} / 12",
             "ACI 318-19 §14.5.2.1, phi 0.60"),
        Step("arm", "height of the passive resultant above the wall's bottom support", arm,
             "ft", "(2/3)(z_2^3 - z_1^3)/(z_2^2 - z_1^2) - z_1",
             f"(2/3) x ({num(z2)}^3 - {num(z1)}^3) / ({num(z2)}^2 - {num(z1)}^2) - {num(z1)}"),
        Step("P_cap", "wall's cantilever credit per foot", cap, "plf", "phi Mn / arm",
             f"{num(phi_mn)} / {num(arm)}"),
        Step("K", "credit along the thrust: the lesser of the two, over the wall's length",
             credit, "lb", "min(P_p x submerged factor, P_cap) x length",
             f"min({num(passive)} x {num(submerged)}, {num(cap)}) x {num(length)}")]
    if friction is not None and resultant is not None:
        steps += [Step("F", "base friction on the presumptive bed", friction, "lb",
                       "mu N'", "mu 0.35 on the washed stone, the body's weight"),
                  Step("H", "resultant thrust on the body", resultant, "lb")]
    steps += [Step("FS_req", "safety factor required", REQUIRED_FS, "", source="IRC R404.4"),
              Step("FS", "safety factor with the lean wall: the root of |FS H - K d| = F "
                   "(wall resists along the unopposed side's push only)", fs, "")]
    return tuple(steps)
