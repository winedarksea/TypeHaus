"""The working for ``deck_post``'s rows, and its sheet declaration (review E-02).

Split out of ``deck_post`` (file size). The steps read the same numbers the states are built
from: :class:`PMSection` and :class:`SwayDetail` are what ``deck_post`` computes the section
strength and the sway magnifier through, so the sheet cannot differ from the ratio.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from typehaus.engineering.item import EngineeringRecord, Figure, NotCovered, Step, num

#: A row that is a length or a section property: no load combination applies to it.
NO_LOAD = ("none: a length or a section property, independent of the load combination", ())
#: The screening pairing of the rows that carry one moment against the 1.2D + 1.6L axial.
SCREEN_WIND = ("1.2D + 1.6L axial with 1.0W moment (a screening pairing, harsher than "
               "ASCE 7-16 §2.3.1; the envelope row is the §2.3.1 check)",
               (("D", 1.2), ("L", 1.6), ("W", 1.0)))
SCREEN_BOTH = ("the larger of 1.0W and 1.6 x the guard, with the 1.2D + 1.6L axial "
               "(a screening pairing)", (("D", 1.2), ("L", 1.6), ("W", 1.0)))
SCREEN_GUARD = ("1.2D + 1.6L axial with the guard at 1.6L (ASCE 7-16 §2.3.1 combination 2)",
                (("D", 1.2), ("L", 1.6)))


@dataclass(frozen=True)
class PMSection:
    """The round section at neutral-axis depth ``c``: what ``phi P_n`` and ``phi M_n`` add up."""

    force: float        # total axial force, lb
    moment: float       # total moment about the section centre, lb-in
    tension: float      # strain in the extreme tension bar (positive)
    area: float         # compression-block segment area, in^2
    centroid: float     # its centroid above the centre, in
    bars: tuple[tuple[float, float], ...]   # (offset above centre in., net stress psi)
    c: float
    depth: float        # block depth a = beta_1 c, capped at the diameter
    fc: float
    bar_area: float
    concrete_force: float


@dataclass(frozen=True)
class SwayDetail:
    """§6.6.4.5 magnification of a cantilever column, with each intermediate."""

    slenderness: float
    modulus: float
    inertia: float
    sustained: float
    stiffness: float
    effective: float
    critical: float
    axial: float
    magnifier: float
    k: float
    height: float
    radius: float
    dead: float
    factored: float
    fc: float


def terms(parts: list[tuple[str, float]]) -> tuple[str, str]:
    """``("a + b", "1 + 2")`` over the non-zero parts."""
    live = [(n, v) for n, v in parts if abs(v) > 1e-9]
    return " + ".join(n for n, _ in live) or "0", " + ".join(num(v) for _, v in live) or "0"


def load_steps(pier: Any, dead_factor: float, live_factor: float, factored: float
               ) -> tuple[Step, ...]:
    d_eq, d_num = terms([("D_deck", pier.deck_dead_effective_lb),
                         ("D_roof", pier.roof_tributary_ft2 * pier.roof_dead_psf),
                         ("D_shaft", pier.self_weight_lb), ("D_above", pier.carried_dead_lb),
                         ("D_wall", pier.wall_dead_lb), ("D_planter", pier.planter_lb)])
    l_eq, l_num = terms([("L_deck", pier.deck_live_effective_lb),
                         ("S_roof", pier.roof_tributary_ft2 * pier.roof_snow_psf)])
    return (
        Step("D", "dead load on the column, planter on (deck and beam reaction, roof, the "
             "shaft's own weight, load handed down, wall line load, planter)", pier.dead_lb,
             "lb", d_eq, d_num, "the beam's statics reaction; unit weights in the load basis"),
        Step("L", "live load on the column (deck occupancy, roof snow)", pier.live_lb, "lb",
             l_eq, l_num, "IRC Table R301.5 deck live; design roof snow"),
        Step("P_u", "factored axial load, 1.2D + 1.6L", factored, "lb", "1.2 D + 1.6 L",
             f"{num(dead_factor)} x {num(pier.dead_lb)} + {num(live_factor)} x "
             f"{num(pier.live_lb)}", "ASCE 7-16 §2.3.1 combination 2"))


def axial_steps(area: float, steel: float, fc: float, fy: float, po: float, phi: float,
                alpha: float, capacity: float) -> tuple[Step, ...]:
    return (
        Step("A_g", "gross area of the round section", area, "in^2", "pi (D/2)^2"),
        Step("A_st", "longitudinal steel area", steel, "in^2", "n A_b"),
        Step("P_o", "nominal axial strength with no moment", po, "lb",
             "0.85 f'c (A_g - A_st) + f_y A_st",
             f"0.85 x {num(fc)} x ({num(area)} - {num(steel)}) + {num(fy)} x {num(steel)}",
             "ACI 318-19 Eq. 22.4.2.2"),
        Step("phi P_n,max", "design axial strength of a tied column", capacity, "lb",
             "phi alpha P_o", f"{num(phi)} x {num(alpha)} x {num(po)}",
             "ACI 318-19 Table 22.4.2.1; phi Table 21.2.2"))


def moment_steps(symbol: str, meaning: str, asd: float, factor_text: str, strength: float,
                 source_asd: str) -> tuple[Step, ...]:
    """A service base moment taken to strength level, as an explicit step."""
    return (Step(f"{symbol}_ASD", f"{meaning}, service level (ASD)", asd, "lb-ft",
                 source=source_asd),
            Step(symbol, f"{meaning}, strength level", strength, "lb-ft",
                 f"{symbol}_ASD {factor_text}", f"{num(asd)} {factor_text}",
                 "ASCE 7-16 §2.3.1 / §2.4.1"))


def pm_steps(section: PMSection, phi: float, axial: float, phi_mn: float,
             beta: float, radius: float) -> tuple[Step, ...]:
    bars = " + ".join(f"{num(s)} x {num(section.bar_area)} x {num(o)}"
                      for o, s in section.bars) or "0"
    bar_moment = sum(s * section.bar_area * o for o, s in section.bars)
    return (
        Step("c", "neutral-axis depth at which phi P_n equals P_u (found by bisection on "
             "the strain-compatible section)", section.c, "in",
             source="ACI 318-19 §22.2; the point on the P-M curve at this P_u"),
        Step("a", "depth of the compression block, beta_1 c (not past the diameter)",
             section.depth, "in", "min(beta_1 c, D)",
             f"min({num(beta)} x {num(section.c)}, {num(2.0 * radius)})",
             "ACI 318-19 Table 22.2.2.4.3"),
        Step("A_c", "area of the circular segment of depth a", section.area, "in^2",
             "R^2 acos((R - a)/R) - (R - a) sqrt(2 R a - a^2)"),
        Step("y_c", "its centroid above the section centre", section.centroid, "in",
             "(2/3) (half-chord)^3 / A_c"),
        Step("C_c", "compression in the concrete", section.concrete_force, "lb",
             "0.85 f'c A_c", f"0.85 x {num(section.fc)} x {num(section.area)}"),
        Step("M_s", "moment of the bar forces about the centre (stress x area x offset; a "
             "bar inside the block has the displaced concrete taken off; compression +, "
             "tension -, offset above the centre +)", bar_moment,
             "lb-in", "sum(f_s,i A_b y_i)", bars,
             "stress from strain compatibility, capped at f_y, E_s 29,000,000 psi"),
        Step("eps_t", "strain in the extreme tension bar", section.tension, "",
             "0.003 (d_t - c) / c", source="ACI 318-19 §22.2.2.1"),
        Step("phi", "strength reduction factor from that strain", phi, "",
             source="ACI 318-19 Table 21.2.2 (0.65 compression-controlled to 0.90)"),
        Step("phi P_n", "design axial force at that c (equals P_u within the search "
             "tolerance)", phi * section.force, "lb", "phi (C_c + sum f_s A_b)",
             source=f"P_u = {num(axial)} lb"),
        Step("phi M_n", "design moment strength at this axial load", phi_mn, "lb-ft",
             "phi (C_c y_c + M_s) / 12", f"{num(phi)} x ({num(section.concrete_force)} x "
             f"{num(section.centroid)} + {num(bar_moment)}) / 12", "ACI 318-19 §22.4"))


def sway_steps(d: SwayDetail) -> tuple[Step, ...]:
    return (
        Step("kl/r", "slenderness of a column fixed at the base and free at the head",
             d.slenderness, "", "k l_u / r", f"{num(d.k)} x {num(d.height)} / {num(d.radius)}",
             "ACI 318-19 §6.2.5; r = D/4 for a round section"),
        Step("E_c", "concrete modulus", d.modulus, "psi", "57,000 sqrt(f'c)",
             f"57,000 x sqrt({num(d.fc)})", "ACI 318-19 §19.2.2.1"),
        Step("I_g", "gross moment of inertia", d.inertia, "in^4", "pi D^4 / 64"),
        Step("beta_dns", "sustained-load share, 1.2 D / P_u,gravity", d.sustained, "",
             "1.2 D / P_u", f"1.2 x {num(d.dead)} / {num(d.factored)}",
             "ACI 318-19 §6.6.4.4.4"),
        Step("EI", "effective stiffness", d.stiffness, "lb-in^2",
             "0.4 E_c I_g / (1 + beta_dns)",
             f"0.4 x {num(d.modulus)} x {num(d.inertia)} / (1 + {num(d.sustained)})",
             "ACI 318-19 §6.6.4.4.4(a)"),
        Step("P_c", "critical buckling load", d.critical, "lb", "pi^2 EI / (k l_u)^2",
             f"pi^2 x {num(d.stiffness)} / {num(d.effective)}^2", "ACI 318-19 §6.6.4.5.2"),
        Step("delta", "sway moment magnifier", d.magnifier, "",
             "max(1 / (1 - P_u / (0.75 P_c)), 1)",
             f"max(1 / (1 - {num(d.axial)} / (0.75 x {num(d.critical)})), 1)",
             "ACI 318-19 §6.6.4.5.2"))


def lap_steps(dev: tuple[Step, ...], lap: float, available: float, simplified: float,
              authored: bool) -> tuple[Step, ...]:
    return (*dev,
            Step("l_lap", "class B lap splice, every bar at one section", lap, "in",
                 "1.3 l_d", f"1.3 x {num(dev[-1].value)}", "ACI 318-19 §25.5.2.1"),
            Step("l_simple", "for comparison, Table 25.4.2.3's simplified row x 1.3",
                 simplified, "in", source="the bound; the general equation is the shorter"),
            Step("L_avail", "dowel projection above the joint" if authored else
                 "the column's own height, the only bound on the lap available",
                 available, "in", source="the authored dowel projection" if authored else ""))


def detailing_steps(name: str, pier_area: float, steel: float, minimum_steel: float,
                    count: int, bar_area: float, tie_bar: int, required_tie: int,
                    tie_spacing: float, tie_limit: float, bar_db: float, tie_db: float,
                    diameter: float, e_min: float, magnifier: float, embedded: float
                    ) -> tuple[Step, ...]:
    a_s = ("A_s", "longitudinal steel provided", steel, "in^2", "n A_b",
           f"{count} x {num(bar_area)}")
    if name == "longitudinal steel":
        eff = minimum_steel / 0.01
        return (Step("A_eff", "area the 1% floor is taken on (the gross area unless the "
                     "reduced area of ACI §10.3.1.2 is claimed)", eff, "in^2"),
                Step("A_s,min", "least longitudinal steel", minimum_steel, "in^2",
                     "0.01 A_eff", f"0.01 x {num(eff)}", "ACI 318-19 §10.6.1.1"), Step(*a_s))
    if name == "steel ratio ceiling":
        return (Step("A_s,max", "most longitudinal steel", 0.08 * pier_area, "in^2",
                     "0.08 A_g", f"0.08 x {num(pier_area)}", "ACI 318-19 §10.6.1.1"),
                Step(*a_s))
    if name == "bar count":
        return (Step("n_min", "fewest bars within circular ties", 4.0, "bars",
                     source="ACI 318-19 §10.7.3.1(b)"),
                Step("n", "bars provided", float(count), "bars"))
    if name == "tie size":
        return (Step("tie_req", "tie bar number required (#3 for bars #10 and smaller)",
                     float(required_tie), "bar no.", source="ACI 318-19 §25.7.2.1"),
                Step("tie", "tie bar number provided", float(tie_bar), "bar no."))
    if name == "tie spacing":
        return (Step("s_max", "greatest tie spacing: least of 16 d_b, 48 d_t and the column "
                     "dimension", tie_limit, "in", "min(16 d_b, 48 d_t, h)",
                     f"min(16 x {num(bar_db)}, 48 x {num(tie_db)}, {num(diameter)})",
                     "ACI 318-19 §25.7.2.2"),
                Step("s", "tie spacing provided", tie_spacing, "in"))
    return (Step("e_min", "minimum eccentricity, 0.6 + 0.03 h", 0.6 + 0.03 * diameter, "in",
                 "0.6 + 0.03 h", f"0.6 + 0.03 x {num(diameter)}", "ACI 318-19 §6.6.4.5.4"),
            Step("delta_ns", "non-sway magnifier (k = 1)", magnifier, "", source="§6.6.4.5.2"),
            Step("e_req", "magnified minimum eccentricity", e_min, "in", "e_min delta_ns",
                 f"{num(0.6 + 0.03 * diameter)} x {num(magnifier)}"),
            Step("e_cap", "the eccentricity the 0.80 axial cap already carries, 0.10 h",
                 embedded, "in", "0.10 h", f"0.10 x {num(diameter)}",
                 "ACI 318-19 R22.4.2"))


LABELS = {
    "column_diameter": "column diameter D",
    "column_height": "column height above the joint, l_u",
    "gross_area": "gross area of the section A_g",
    "tributary_area": "deck area carried",
    "roof_tributary_area": "roof area carried",
    "roof_snow": "design roof snow",
    "carried_dead": "dead load handed down from posts above",
    "wall_dead": "dead load of a wall bearing on the beam it carries",
    "dead_load": "dead load, no planter",
    "live_load": "live load (deck occupancy, roof snow)",
    "planter_dead": "saturated planter weight, where one stands over the beam",
    "longitudinal_steel": "area of the longitudinal bars A_st",
    "bar_count": "number of longitudinal bars",
    "bar_number": "longitudinal bar size (#)",
    "tie_number": "tie bar size (#)",
    "tie_spacing": "tie spacing",
    "wind_base_moment_Mu": "wind moment at the base, strength level 1.0W "
                           "(the service value divided by 0.6)",
    "guard_base_moment_Mu": "guard-load moment at the base, strength level "
                            "(the 200 lb service load x 1.6)",
    "phi_Mn": "design moment strength phi M_n at the column's own axial load",
    "cover": "clear cover to the ties",
}

NOT_COVERED = (
    NotCovered("the column's base joint on the wall",
               "the dowels' bearing, tension, shear friction and development are graded as "
               "the wall's `column_support` record, not here",
               "the sealing engineer", "the column_support sheet"),
    NotCovered("the base fixity and its rotation",
               "the base is taken as fixed; the foundation's stiffness and the sway it adds "
               "are `base_rotation`'s",
               "the sealing engineer", "the base_rotation sheet"),
    NotCovered("the head joint's shear and torsion",
               "graded as `column_head_joint`, not here",
               "the sealing engineer", "the column_head_joint sheet"),
    NotCovered("the frame shear shared with another lateral line",
               "none is claimed: the whole shear is spent on these columns unless the "
               "structure declares another line",
               "the sealing engineer", "declaring a diaphragm line, if one is relied on"),
)


def figure(record: EngineeringRecord) -> Figure | None:
    from typehaus.engineering import sketch

    by_name = {s.name: s for s in record.limit_states}
    axial = by_name.get("axial, tied column")
    envelope = next((s for s in record.limit_states if s.name.startswith("P-M envelope")),
                    None)
    wind, guard = record.value("wind_base_moment_Mu"), record.value("guard_base_moment_Mu")
    height = record.value("column_height")
    if None in (axial, envelope, wind, guard, height):
        return None
    return sketch.fixed_column(
        title=f"a moment column, {record.key}",
        height_ft=height / 12.0, axial=f"{num(axial.demand)} lb (1.2D + 1.6L)",
        wind=f"{num(wind)} lb-ft at the base", guard=f"{num(guard)} lb-ft at the base",
        base_moment=f"{num(envelope.demand)} lb-ft (governing, magnified)",
        k="2.1", base="fixed: dowelled into the wall top",
        caption="Not to scale. The governing combination is named in the P-M envelope row.")



def anchorage_wall_steps(dev: tuple[Step, ...], simplified: float, stem: float,
                         authored: float, available: float, refused: bool) -> tuple[Step, ...]:
    return (*dev,
            Step("l_simple", "for comparison, Table 25.4.2.3's simplified row", simplified,
                 "in", source="the bound; the general equation is the shorter"),
            Step("L_stem", "stem depth available below the joint, less the wall's cover",
                 stem, "in"),
            Step("L_emb", "embedment authored on the drawing" + (
                " (refused: it runs past the stem, so the stem governs)" if refused else ""),
                 authored, "in"),
            Step("L_avail", "length available, the lesser of the two", available, "in",
                 "min(L_emb, L_stem)", f"min({num(authored)}, {num(stem)})"))


def anchorage_hook_steps(ldh: float, thickness: float, cover: float, bar_db: float,
                         available: float) -> tuple[Step, ...]:
    return (
        Step("l_dh", "standard-hook development length (psi_e, psi_r, psi_o all 1.0)", ldh,
             "in", source="ACI 318-19 §25.4.3.1; ties continue through the joint (§25.4.3.3)"),
        Step("L_avail", "pour depth less its cover and one bar diameter", max(available, 0.0),
             "in", "t - cover - d_b", f"{num(thickness)} - {num(cover)} - {num(bar_db)}",
             "the hook turns at the bottom mat"))
