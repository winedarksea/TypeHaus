"""The working for ``column_support``'s joint rows, and its sheet declaration (review E-02).

Split out of ``column_support`` (file size). :class:`CaseParams` holds the very numbers the
governing combination's states were graded on, so the steps cannot differ from the ratios.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, NamedTuple

from typehaus.engineering.deck_post_working import moment_steps
from typehaus.engineering.item import EngineeringRecord, Figure, NotCovered, Step, num


class Couple(NamedTuple):
    """The dowel couple that balances (P_u, M_u): compression, tension and its pieces."""

    compression: float
    pull: float
    bars: int
    lever: float
    ybar: float
    area: float


@dataclass(frozen=True)
class CaseParams:
    case: Any
    rigid: float
    flexible: float
    delta: float
    mu_in: float
    c: float
    block: float
    couples: tuple[Couple, ...]
    wind_v: float
    guard_v: float
    vu: float
    wind_asd_mu: float
    guard_asd_mu: float
    wind_mu: float
    guard_mu: float


def _loads(p: CaseParams) -> tuple[Step, ...]:
    case = p.case
    return (
        *moment_steps("M_w", "wind moment at the column base", p.wind_asd_mu, "/ 0.6",
                      p.wind_mu, "deck_post: this column's share of the deck wind"),
        *moment_steps("M_g", "guard-load moment at the column base", p.guard_asd_mu, "x 1.6",
                      p.guard_mu, "IRC R301.5's 200 lb at the top of the guard"),
        Step("P_u", f"factored axial load, {case.label}", case.axial_lb, "lb", case.axial_eq,
             case.axial_numbers, "ASCE 7-16 §2.3.1; D, L, S as on the deck_post sheet"),
        Step("M_0", "base moment before magnification", case.moment_lb_ft, "lb-ft",
             case.moment_eq, case.moment_numbers),
        Step("delta", "moment magnifier: the larger of the rigid-base (k 2.1) value and the "
             "flexible-base value", p.delta, "", "max(delta_rigid, delta_flex)",
             f"max({num(p.rigid)}, {num(p.flexible)})",
             "ACI 318-19 §6.6.4.5.2; the flexible base is the base_rotation sheet's"),
        Step("M_u", "magnified base moment at the joint", p.mu_in / 12.0, "lb-ft",
             "delta M_0", f"{num(p.delta)} x {num(p.case.moment_lb_ft)}"))


def _couple_steps(couple: Couple, p: CaseParams, fc: float, radius: float) -> tuple[Step, ...]:
    pu = p.case.axial_lb
    if couple.pull <= 0.0:
        return (Step("C", "compression on the wall top: no dowel tension is needed, so it "
                     "is all of P_u", couple.compression, "lb", "P_u"),
                Step("T", "dowel tension", 0.0, "lb"))
    return (
        Step("l_T", "lever: centroid of the dowels below the centre, taken in tension",
             couple.lever, "in", source="dowels on a ring one bar inside the verticals; "
             "compression dowels are not credited"),
        Step("y_C", "centroid of the bearing segment of area C / (0.85 f'c), above the "
             "centre", couple.ybar, "in", source=f"segment area {num(couple.area)} in^2, "
             f"f'c {num(fc)} psi, R {num(radius)} in"),
        Step("C", "compression on the wall top (found by iteration: C and its segment "
             "depend on each other)", couple.compression, "lb",
             "(M_u 12 + P_u l_T) / (y_C + l_T)",
             f"({num(p.mu_in)} + {num(pu)} x {num(couple.lever)}) / "
             f"({num(couple.ybar)} + {num(couple.lever)})",
             "free body: the couple of C and T balances P_u and M_u"),
        Step("T", "dowel tension that balances it", couple.pull, "lb", "C - P_u",
             f"{num(couple.compression)} - {num(pu)}"))


def bearing(p: CaseParams, couple: Couple, wall_fc: float, root: float, clear: float,
            radius: float, phi: float, capacity: float, col_fc: float) -> tuple[Step, ...]:
    return (
        *_loads(p), *_couple_steps(couple, p, col_fc, radius),
        Step("c", "neutral-axis depth of the column's own P-M point at this P_u", p.c, "in",
             source="the deck_post sheet's P-M working at this axial load"),
        Step("A_c", "area of the column's compression block, a circular segment", p.block,
             "in^2", "segment of depth beta_1 c", source="the deck_post sheet"),
        Step("k_A", "confinement of the wall top, sqrt(A2 / A1): the clear wall each side "
             "of the column centre over its radius, between 1 and 2", root, "",
             "min(2, max(1, clear / R))", f"min(2, max(1, {num(clear)} / {num(radius)}))",
             "ACI 318-19 §22.8.3.2; a round as wide as the stem gets no credit"),
        Step("phi B_n", "design bearing strength on the block", capacity, "lb",
             "phi 0.85 f'c A_c k_A", f"{num(phi)} x 0.85 x {num(wall_fc)} x {num(p.block)} x "
             f"{num(root)}", "ACI 318-19 §22.8.3.2; f'c of the wall. " + _bearing_scope(
                 couple, p, wall_fc, phi)))


def _bearing_scope(couple: Couple, p: CaseParams, wall_fc: float, phi: float) -> str:
    """What this row bounds, and what a reviewer holding the interface to phi 0.85 f'c finds."""
    need = couple.compression / (phi * 0.85 * wall_fc)
    fits = ("still fits within" if need <= p.block else "does NOT fit within")
    return (f"This row bounds the compression C spread on the column's compression block "
            f"A_c at this axial load; the joint's flexure is graded by the dowel-tension "
            f"row. A reviewer holding the interface to phi 0.85 f'c needs "
            f"C / (phi 0.85 f'c) = {num(need)} in^2 of bearing, which {fits} A_c "
            f"{num(p.block)} in^2.")


def tension(p: CaseParams, couple: Couple, col_fc: float, radius: float, per_bar: float,
            bar: int, area: float, phi: float, fy: float, capacity: float
            ) -> tuple[Step, ...]:
    return (
        *_loads(p), *_couple_steps(couple, p, col_fc, radius),
        Step("T_bar", "tension per dowel in tension", per_bar, "lb", "T / n_T",
             f"{num(couple.pull)} / {couple.bars}",
             "the worse of the ring's two orientations"),
        Step("phi T_n", f"design tension strength of one #{bar} dowel", capacity, "lb",
             "phi A_b f_y", f"{num(phi)} x {num(area)} x {num(fy)}",
             "ACI 318-19 Table 21.2.2, tension-controlled"))


def _shear_couple(p: CaseParams, couple: Couple, col_fc: float, radius: float
                  ) -> tuple[Step, ...]:
    """The couple friction deducts: the larger total T of the ring's two orientations, which
    is not always the orientation the tension row grades (the larger T per dowel)."""
    from dataclasses import replace

    steps = _couple_steps(couple, p, col_fc, radius)
    per_dowel = max(p.couples, key=lambda k: k.pull / k.bars)
    if per_dowel.pull == couple.pull or couple.pull <= 0.0:
        return steps
    why = (f"dowel tension of the ring orientation with {couple.bars} dowels in tension, "
           f"the larger total T of the ring's two orientations, so the larger deduction from "
           f"A_vf f_y; the tension row grades the other orientation, the larger per dowel "
           f"({num(per_dowel.pull)} lb on {per_dowel.bars} dowel)")
    return (*steps[:-1], replace(steps[-1], meaning=why))


def shear(p: CaseParams, couple: Couple, count: int, area: float, mu: float, rough: bool,
          phi: float, fy: float, vn_max: float, capacity: float,
          w_factor: float, l_factor: float, col_fc: float, radius: float
          ) -> tuple[Step, ...]:
    friction = mu * (phi * count * area * fy - couple.pull)
    return (
        *_shear_couple(p, couple, col_fc, radius),
        Step("V_w", "wind shear at the head, service", p.wind_v, "lb",
             source="deck_post: the bands' total, shaft included"),
        Step("V_g", "guard load", p.guard_v, "lb", source="IRC R301.5"),
        Step("V_u", "factored shear across the joint", p.vu, "lb",
             "(f_W / 0.6) V_w + f_L V_g",
             f"({num(w_factor)} / 0.6) x {num(p.wind_v)} + {num(l_factor)} x "
             f"{num(p.guard_v)}", f"the combination's own factors, {p.case.label}"),
        Step("A_vf", "dowel steel across the joint", count * area, "in^2", "n A_b",
             f"{count} x {num(area)}"),
        Step("mu", "shear-friction coefficient" + (
            " (surface roughened 1/4 in., authored)" if rough else
            " (not intentionally roughened)"), mu, "", source="ACI 318-19 Table 22.9.4.2"),
        Step("phi mu(...)", "friction strength: the dowels' yield force less the couple's "
             "tension (compression is not credited)", friction, "lb",
             "mu (phi A_vf f_y - T)",
             f"{num(mu)} x ({num(phi)} x {num(count * area)} x {num(fy)} - "
             f"{num(couple.pull)})", "ACI 318-19 §22.9.4.2"),
        Step("phi V_max", "upper limit on shear strength", phi * vn_max, "lb",
             "phi V_n,max", f"{num(phi)} x {num(vn_max)}", "ACI 318-19 §22.9.4.4"),
        Step("phi V_n", "design shear strength, the lesser", capacity, "lb",
             "min(friction, upper limit)", f"min({num(friction)}, {num(phi * vn_max)})"))


def footprint(radius: float, clear: float) -> tuple[Step, ...]:
    return (Step("R", "column radius", radius, "in", "D / 2"),
            Step("clear", "least clear wall top from the column centre to a stem face",
                 clear, "in", source="the wall's resolved structure layer"))


LABELS = {
    "bed_friction": "base friction of the footing's bed, design value",
    "restraint_friction": "base friction of the footing's bed, upper value (restraint)",
    "native_friction": "friction of the native soil",
    "soil_confirmed": "soil parameters confirmed by an investigation",
}

#: Plain words for the inputs a member carries under ``<tag>.<name>``.
_SUFFIX = {
    "sqrt_A2_A1": "bearing confinement sqrt(A2/A1) of the wall top",
    "shear_friction_mu": "shear-friction coefficient mu at the joint",
    "dowel_embedment": "dowel embedment into the stem",
    "wall_fc": "concrete strength f'c of the wall",
    "column_fc": "concrete strength f'c of the column",
    "column_cover": "clear cover to the column's ties",
    "wall_cover": "clear cover in the wall",
    "stem_height": "stem height under the column, joint to footing",
    "dowel_bar": "dowel bar size (#)",
    "dowel_count": "number of dowels",
    "wind_base_moment": "wind moment at the column base, service level",
    "guard_base_moment": "guard moment at the column base, service level",
    "factored_axial": "factored axial load, 1.2D + 1.6L",
    "stem_thickness": "stem thickness",
    "stem_fc": "concrete strength f'c of the stem",
    "spread_below_dowels": "width the moment spreads over below the dowels",
    "ew_base_moment": "sum of the columns' E-W base moments M + V H, strength level",
    "ew_spread_ft": "length of stem the columns' moments spread over",
    "soil_moment_per_ft": "retained-soil moment at the stem base, per foot, factored",
    "soil_prop_per_ft": "retained-soil top reaction, per foot, factored",
    "prop_per_joist": "soil prop each porch joist carries, service",
    "joist_span": "porch joist span",
}


def labelled(inputs: list) -> list:
    """The inputs with their plain-word meanings set (labels are not hashed)."""
    from dataclasses import replace

    return [replace(q, label=_SUFFIX[q.name.split(".")[-1]])
            if not q.label and "." in q.name and q.name.split(".")[-1] in _SUFFIX else q
            for q in inputs]


NOT_COVERED = (
    NotCovered("rotational restraint of the foundation",
               "the column's base fixity is graded as `base_rotation` for each column",
               "the sealing engineer", "the base_rotation sheet"),
    NotCovered("the stem's in-plane (N-S) wind",
               "it runs along the wall's strong axis and is not graded here",
               "the sealing engineer", "accepting the strong-axis bound"),
    NotCovered("the joint's torsion",
               "about 3% of the cracking threshold on the column_head_joint sheet; it rides "
               "the same shear-friction dowels",
               "the sealing engineer", "the column_head_joint sheet"),
    NotCovered("the ledger's Titen HD anchors against the dowels",
               "kept apart by a drawing note, not graded",
               "the contractor at excavation", "following drawing note AN-SG-LEDGER-DOWELS"),
    NotCovered("one-sided backfill",
               "the soil's prop assumes the porch is framed before backfill and both sides "
               "are backfilled together; a one-sided stage would load the far stem through "
               "the porch struts",
               "the contractor at excavation", "following drawing note AN-SG-BACKFILL"),
)


def figure(record: EngineeringRecord) -> Figure | None:
    """The first column's governing bearing row: loads, couple and stem, off its own steps."""
    from typehaus.engineering import sketch

    state = next((s for s in record.limit_states
                  if s.name.endswith("bearing on the wall top")), None)
    if state is None or not state.working:
        return None
    by = {step.symbol: step for step in state.working}
    if not {"P_u", "M_u", "C", "T"} <= by.keys():
        return None
    tag = state.name.split(":")[0]
    shear_state = next((s for s in record.limit_states
                        if s.name.startswith(tag) and "shear friction" in s.name), None)
    foot = next((s for s in record.limit_states
                 if s.name.startswith(tag) and s.name.endswith("footprint on the wall top")),
                None)
    vu = next((x.value for x in (shear_state.working if shear_state else ())
               if x.symbol == "V_u"), 0.0)
    return sketch.wall_top_joint(
        title=f"the joint of {tag} on its wall top",
        axial=f"{num(by['P_u'].value)} lb", moment=f"{num(by['M_u'].value)} lb-ft",
        shear=f"{num(vu)} lb", round_in=2.0 * next((x.value for x in (foot.working if foot else ())
                             if x.symbol == "R"), 0.0),
        couple=f"C {num(by['C'].value)} lb, T {num(by['T'].value)} lb",
        base="stem width (the round is flush)",
        caption="Not to scale. The governing combination is named in each row.")
