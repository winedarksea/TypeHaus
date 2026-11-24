"""The working for ``retaining_wall``'s rows: Step chains built from the free body's own terms.

A leaf beside ``retaining_basis`` (which calls these where the numbers are computed): each
function takes the values the state is built from and returns the :class:`Step` chain the
sheet prints, so a PE checks every number with a calculator. Nothing here recomputes a
demand or a capacity; an intermediate that is only displayed is shown from the same inputs.
"""

from __future__ import annotations

from typehaus.engineering.item import Step, num

REQUIRED_FS = 1.5

#: Stability rows take unfactored loads; section rows take 1.6 on the earth.
SERVICE = ("D + H, service loads (IBC §1807.2.3: the safety factors take unfactored loads)",
           (("D", 1.0), ("H", 1.0)))
STRENGTH = ("strength: 1.6H on the earth pressure and the soil column it holds (ASCE 7-16 "
            "§2.3.1, IBC 2018 §1605.2)", (("H", 1.6),))


def _thrust(case, geom) -> tuple[Step, ...]:  # type: ignore[no-untyped-def]
    t, h = case.terms, geom.retained_height_ft
    out = [Step("H", "retained height, footing underside to the top of the soil", h, "ft",
                source="the wall's authored unbalanced fill plus the footing depth"),
           Step("K", "equivalent fluid pressure of the retained soil", case.efp_psf_per_ft,
                "psf/ft", source="IBC Table 1610.1 row for the soil class"),
           Step("P_earth", "earth thrust per foot of wall", t["earth"], "plf",
                "K H^2 / 2", f"{num(case.efp_psf_per_ft)} x {num(h)}^2 / 2")]
    if t["lateral"]:
        out.append(Step("P_sur", "lateral surcharge from the raised-garden apron", t["lateral"],
                        "plf", source="IBC 2018 §1610.1, rigid-wall strip load (assumptions)"))
    out.append(Step("T", "total thrust per foot of wall", case.thrust_plf, "plf",
                    "P_earth + P_sur", f"{num(t['earth'])} + {num(t['lateral'])}"))
    return tuple(out)


def _weights(case, geom) -> tuple[Step, ...]:  # type: ignore[no-untyped-def]
    t = case.terms
    stem_h, pcf = geom.stem_height_ft, case.soil_pcf
    out = [
        Step("W_stem", "stem weight per foot", t["stem"], "plf", "t h_s 150",
             f"{num(geom.stem_thickness_ft)} x {num(stem_h)} x 150"),
        Step("W_ftg", "footing weight per foot", t["footing"], "plf", "B d 150",
             f"{num(geom.footing_width_ft)} x {num(geom.footing_depth_ft)} x 150"),
        Step("W_heel", "soil standing on the heel, per foot", t["heel"], "plf",
             "b_heel h_s gamma", f"{num(geom.heel_ft)} x {num(stem_h)} x {num(pcf)}")]
    if t["column"]:
        out.append(Step("W_col", "service axial of the columns on the wall top, per foot",
                        t["column"], "plf", source="the column records (assumptions)"))
    out.append(Step("W", "weight resisting sliding (dead load only)", case.weight_plf, "plf",
                    "W_stem + W_ftg + W_heel + W_col",
                    f"{num(t['stem'])} + {num(t['footing'])} + {num(t['heel'])} + "
                    f"{num(t['column'])}", "IBC Table 1806.2 note a: friction on dead load"))
    return tuple(out)


def sliding(case, geom, base) -> tuple[Step, ...]:  # type: ignore[no-untyped-def]
    mu = base.friction_coefficient
    return (*_thrust(case, geom), *_weights(case, geom),
            Step("mu", "friction between footing and bed", mu, "",
                 source="IBC Table 1806.2 class of the bearing material"),
            Step("F", "sliding resistance (passive neglected)", case.resistance_plf, "plf",
                 "mu W + passive", f"{num(mu)} x {num(case.weight_plf)} + "
                 f"{num(case.terms['passive'])}"),
            Step("FS_req", "safety factor required", REQUIRED_FS, "", source="IRC R404.4"),
            Step("FS", "safety factor against sliding", case.fs_sliding, "", "F / T",
                 f"{num(case.resistance_plf)} / {num(case.thrust_plf)}"))


def base_restraint(system) -> tuple[Step, ...]:  # type: ignore[no-untyped-def]
    """The court's closed-loop free body read back: ``system = (FS, H, F, item)``."""
    fs, demand, capacity, item = system
    return (Step("H_court", "resultant thrust on the whole court body", demand, "lb",
                 source=f"{item}, dry, soil at 110 pcf"),
            Step("F_court", "base friction of the whole court body", capacity, "lb",
                 source=f"{item}"),
            Step("FS_req", "safety factor required", REQUIRED_FS, "", source="IRC R404.4"),
            Step("FS", "safety factor of the court against sliding", fs, "", "F_court / H_court",
                 f"{num(capacity)} / {num(demand)}"))


def _overturning_moments(case, geom) -> tuple[Step, ...]:  # type: ignore[no-untyped-def]
    t, h, b = case.terms, geom.retained_height_ft, geom.footing_width_ft
    arm = geom.toe_ft + geom.stem_thickness_ft / 2.0
    return (
        Step("M_o", "overturning moment about the toe", case.overturning_moment, "ft-lb/ft",
             "P_earth H / 3 + P_sur arm + |M_col|", f"{num(t['earth'])} x {num(h)} / 3 + "
             f"{num(t['m_lateral'])} + {num(t['m_column'])}",
             "the surcharge and column terms at their own arms"),
        Step("M_r", "restoring moment about the toe", case.resisting_moment, "ft-lb/ft",
             "W_ftg B / 2 + W_stem (b_toe + t / 2) + W_heel (B - b_heel / 2) + W_col arm",
             f"{num(t['r_footing'])} + {num(t['r_stem'])} + {num(t['r_heel'])} + "
             f"{num(t['r_column'])}", f"stem arm {num(arm)} ft, footing {num(b)} ft wide"))


def overturning(case, geom) -> tuple[Step, ...]:  # type: ignore[no-untyped-def]
    return (*_thrust(case, geom), *_weights(case, geom), *_overturning_moments(case, geom),
            Step("FS_req", "safety factor required", REQUIRED_FS, "", source="IRC R404.4"),
            Step("FS", "safety factor against overturning", case.fs_overturning, "", "M_r / M_o",
                 f"{num(case.resisting_moment)} / {num(case.overturning_moment)}"))


def _resultant(case, geom) -> tuple[Step, ...]:  # type: ignore[no-untyped-def]
    b = geom.footing_width_ft
    x = ((case.resisting_moment - case.overturning_moment) / case.weight_plf
         if case.weight_plf else 0.0)
    return (*_thrust(case, geom), *_weights(case, geom), *_overturning_moments(case, geom),
            Step("x", "where the resultant meets the footing, from the toe", x, "ft",
                 "(M_r - M_o) / W", f"({num(case.resisting_moment)} - "
                 f"{num(case.overturning_moment)}) / {num(case.weight_plf)}"),
            Step("e", "eccentricity of the resultant from the footing centre",
                 case.eccentricity_ft, "ft", "B / 2 - x", f"{num(b)} / 2 - {num(x)}"))


def bearing(case, geom, allowable: float, ibc_class: str) -> tuple[Step, ...]:  # type: ignore[no-untyped-def]
    b = geom.footing_width_ft
    return (*_resultant(case, geom),
            Step("q_toe", "soil pressure at the toe", case.bearing_psf, "psf",
                 "W / B (1 + 6 e / B)", f"{num(case.weight_plf)} / {num(b)} x (1 + 6 x "
                 f"{num(case.eccentricity_ft)} / {num(b)})", "linear pressure under a rigid base"),
            Step("q_allow", "allowable bearing of the bed", allowable, "psf",
                 source=f"IBC Table 1806.2, class {ibc_class}"))


def eccentricity(case, geom) -> tuple[Step, ...]:  # type: ignore[no-untyped-def]
    b = geom.footing_width_ft
    return (*_resultant(case, geom),
            Step("|e|", "size of the eccentricity", abs(case.eccentricity_ft), "ft",
                 "|e|", num(case.eccentricity_ft)),
            Step("B/6", "edge of the middle third (the heel stays in contact inside it)",
                 b / 6.0, "ft", "B / 6", f"{num(b)} / 6"))


def plain_section(h_in: float, fc_psi: float, capacity: float, note: str) -> tuple[Step, ...]:
    sm = 12.0 * h_in ** 2 / 6.0
    return (Step("S_m", "section modulus of the plain strip, 12 in wide", sm, "in^3",
                 "b h^2 / 6", f"12 x {num(h_in)}^2 / 6"),
            Step("phi Mn", "design moment strength, plain concrete", capacity, "ft-lb/ft",
                 "0.60 x 5 sqrt(f'c) S_m / 12", f"0.60 x 5 x sqrt({num(fc_psi)}) x {num(sm)} / 12",
                 note))


def reinforced_section(h_in: float, fc_psi: float, fy: float, bar: int, spacing: float,
                       area_in2: float, db: float, cover: float, as_ft: float, d: float,
                       a: float, capacity: float) -> tuple[Step, ...]:
    return (
        Step("A_s", f"steel area per foot of wall, #{bar} at {num(spacing)} in",
             as_ft, "in^2/ft", "A_bar 12 / s", f"{num(area_in2)} x 12 / {num(spacing)}",
             "ASTM A615 bar area"),
        Step("d", "effective depth to the bar centre", d, "in", "h - cover - d_b / 2",
             f"{num(h_in)} - {num(cover)} - {num(db)} / 2"),
        Step("a", "depth of the compression block", a, "in", "A_s f_y / (0.85 f'c b)",
             f"{num(as_ft)} x {num(fy)} / (0.85 x {num(fc_psi)} x 12)", "ACI 318-19 §22.3"),
        Step("phi Mn", "design moment strength, tension-controlled", capacity, "ft-lb/ft",
             "0.90 A_s f_y (d - a / 2) / 12",
             f"0.90 x {num(as_ft)} x {num(fy)} x ({num(d)} - {num(a)} / 2) / 12",
             "ACI 318-19 §22.3, phi from Table 21.2.1"))


def stem_moment(case, stem_ft: float, service: float, demand: float, factor: float
                ) -> tuple[Step, ...]:  # type: ignore[no-untyped-def]
    extra = case.surcharge.stem_moment_plf if case.surcharge else 0.0
    return (Step("h_s", "soil height above the footing top", stem_ft, "ft",
                 source="retained height less the footing depth"),
            Step("M", "service moment at the stem base per foot", service, "ft-lb/ft",
                 "K h_s^3 / 6 + M_sur",
                 f"{num(case.efp_psf_per_ft)} x {num(stem_ft)}^3 / 6 + {num(extra)}",
                 "earth pressure on the stem; apron surcharge moment"),
            Step("M_u", "factored moment, 1.6 on the earth", demand, "ft-lb/ft", "1.6 M",
                 f"{num(factor)} x {num(service)}", "IBC 2018 §1605.2 / ASCE 7-16 §2.3.1 on H"))
