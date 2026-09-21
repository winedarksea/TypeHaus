"""The GFRP bars' rows for ``thermal_break`` — free body §11e-§11h.

Every rupture value is ACI CODE-440.11-22's DESIGN value, ``C_E f*_fu`` with §20.2.2.3's
0.85 for concrete exposed or not exposed to earth. A bar spans the CLEAR gap between the two
concretes, which at a wall end includes the house's own foundation insulation.
"""

from __future__ import annotations

import math

from typehaus.engineering.item import LimitState, Quantity
from typehaus.engineering.retaining_basis import EARTH_PRESSURE_LOAD_FACTOR
from typehaus.engineering.thermal_break_board import ALPHA_C_PER_F, CONCRETE_PCF

#: ACI 440.11-22 Table 21.2.1: shear; moment/rupture (tension-controlled).
PHI_SHEAR = 0.75
PHI_RUPTURE = 0.55
#: ACI 440.11-22 §20.2.2.3 — one value, exposed or not.
ENVIRONMENTAL_FACTOR = 0.85
#: ACI 440.11-22 §24.6.2: sustained stress ≤ 0.30 f_fu (creep rupture).
SUSTAINED_FRACTION = 0.30
#: ACI 440.11-22 §25.4.2.1 minima and §25.4.2.4's c_b/d_b cap; §25.4.2.5 casting position.
DEV_MIN_DIAMETERS, DEV_MIN_IN, CB_RATIO_CAP = 20.0, 12.0, 3.5
TOP_BAR_CONCRETE_BELOW_IN, TOP_BAR_FACTOR = 12.0, 1.5

SETTLEMENT_MISSING = (
    "`Site.lateral_subgrade_modulus.k_v_pci` — a vertical subgrade modulus "
    "(SubgradeModulus.k_v_pci, a strip footing at its real width), measured or a presumed "
    "published row; differential settlement across the break has no demand without it")


def _section(d):
    inertia = math.pi * d.diameter.inches ** 4 / 64.0
    t_d = ENVIRONMENTAL_FACTOR * d.bar_tensile_lb
    return inertia, t_d, PHI_RUPTURE * t_d * d.diameter.inches / 8.0


def drift_capacity(d, gap: float) -> float:
    inertia, _t_d, m_cap = _section(d)
    return m_cap * gap ** 2 / (6.0 * d.bar_modulus_psi * inertia)


def reserve(d, ref, by_pcf, total_bars, gap, states, inputs, notes) -> None:
    pcf, source, shortfall = max(((p, tag, lb) for p, row in by_pcf.items()
                                  for tag, lb in row.items()), key=lambda r: r[2])
    share = d.count / total_bars
    demand = EARTH_PRESSURE_LOAD_FACTOR * shortfall * share
    _inertia, t_d, _m = _section(d)
    bend = PHI_RUPTURE * t_d * d.diameter.inches / (4.0 * gap)
    per_bar = min(PHI_SHEAR * d.bar_shear_lb, bend)
    inputs += [Quantity("loop_shortfall", shortfall, "lb", 1.0),
               Quantity("bar_share", share, "", 0.0001)]
    states.append(LimitState(
        "dowel shear reserve", demand, d.count * per_bar, "lb",
        f"1.6 x {shortfall:,.0f} lb ({source} at {pcf:.0f} pcf, loop {ref}) x "
        f"{d.count}/{total_bars} bars; per bar min(0.75 x {d.bar_shear_lb:,.0f}, 0.55 x "
        f"C_E {ENVIRONMENTAL_FACTOR} T_u d/4g = {bend:,.0f}) lb over the {gap:.3f}\" clear gap "
        f"— {d.bar_source}",
        combination="1.6H", combination_factors=(("H", EARTH_PRESSURE_LOAD_FACTOR),)))
    inertia = math.pi * d.diameter.inches ** 4 / 64.0
    slip = (shortfall * share / d.count) * gap ** 3 / (12.0 * d.bar_modulus_psi * inertia)
    notes.append(f"Slip across the gap at the service reserve share: {slip:.4f}\".")


def stem_settlement(ctx, board) -> tuple[str, float, float] | None:
    """``(wall, stem plf, footing width in)`` — the court wall at this joint and its strip."""
    from typehaus.model.enums import LayerFunction
    from typehaus.model.structure import Footing

    for tag in board.dowel.connects:
        el = ctx.plan.by_tag(tag)
        wall = ctx.plan.by_tag(el.under) if isinstance(el, Footing) else el
        if wall is None or wall.tag not in board.structure:
            continue
        footing = el if isinstance(el, Footing) else next(
            (f for f in ctx.plan.all_elements()
             if isinstance(f, Footing) and f.under == wall.tag), None)
        assembly = ctx.plan.library.resolve_assembly(getattr(wall, "assembly", "") or "")
        thick = sum(ly.thickness.inches for ly in getattr(assembly, "layers", ())
                    if ly.function is LayerFunction.STRUCTURE)
        top, bot = getattr(wall, "top_elevation", None), getattr(wall, "bottom_elevation", None)
        if footing is None or not thick or top is None or bot is None:
            return None
        plf = CONCRETE_PCF * (thick / 12.0) * (top.inches - bot.inches) / 12.0
        return wall.tag, plf, footing.width.inches
    return None


def settlement(ctx, board, gap, states, missing, inputs, notes) -> float | None:
    """The court stem's bearing over k_v against the bar's rupture drift; returns Δ."""
    report = getattr(ctx.plan.project.site, "lateral_subgrade_modulus", None)
    k_v = getattr(report, "k_v_pci", None)
    if k_v is None:
        missing.append(SETTLEMENT_MISSING)
        return None
    presumed = getattr(report, "provenance", "measured") == "presumed"
    inputs += [Quantity("k_v", k_v, "pci", 0.1),
               Quantity("k_v_presumed", 1.0 if presumed else 0.0, "-", 0.5)]
    stem = stem_settlement(ctx, board)
    if stem is None:
        missing.append(f"the court wall {board.tag} ties, with a STRUCTURE layer, top and "
                       f"bottom elevations and a Footing under it — the settlement demand")
        return None
    wall_tag, plf, width_in = stem
    q_psi = plf / (width_in / 12.0) / 144.0
    cap = drift_capacity(board.dowel, gap)
    inputs.append(Quantity("stem_bearing", q_psi * 144.0, "psf", 0.1))
    label = "PRESUMED" if presumed else "measured"
    states.append(LimitState(
        "differential settlement", q_psi / k_v, cap, "in",
        f"{wall_tag}'s stem {plf:,.0f} plf over {width_in / 12:.2f}' of footing = "
        f"{q_psi * 144:.1f} psf / k_v {k_v:g} pci ({label}: {report.source}); vs the bar's "
        f"rupture drift fixed-fixed over the {gap:.3f}\" clear gap, 0.55 C_E T_u d/8 x g^2/6EI"))
    notes.append(
        f"SETTLEMENT, BOUNDED: the stem alone is a LOWER bound on the court's added bearing and "
        f"the house is credited none of its own; the bars tolerate "
        f"{k_v * cap * 144.0:.0f} psf of bearing mismatch at this k_v."
        + (" k_v IS PRESUMED, a published table row and not a report on this parcel — a "
           "geotechnical report confirms or replaces it." if presumed else ""))
    return q_psi / k_v


def racking(d, gap, offset_in, opening_f, settle, states, inputs) -> None:
    """E-W growth about the court's centreline, combined with the settlement offset."""
    rack = ALPHA_C_PER_F * opening_f * offset_in
    total = math.hypot(rack, settle or 0.0)
    inputs.append(Quantity("court_offset", offset_in, "in", 0.1))
    states.append(LimitState(
        "racking drift", total, drift_capacity(d, gap), "in",
        f"{ALPHA_C_PER_F:g}/F x {opening_f:.0f} F x {offset_in:.1f}\" off the court's centreline "
        f"= {rack:.5f}\", with settlement {settle or 0:.5f}\" as a vector; vs the bar's rupture "
        f"drift over {gap:.3f}\""))


def bond_length(d, stress, fc_psi, cb_in, concrete_below_in) -> float:
    """ACI 440.11-22 Eq. 25.4.2.4 WITHOUT the §25.4.2.1 minima — the length a stress decays
    over, not a detailing length."""
    ratio = min(cb_in / d.diameter.inches, CB_RATIO_CAP)
    psi_t = TOP_BAR_FACTOR if concrete_below_in > TOP_BAR_CONCRETE_BELOW_IN else 1.0
    root = min(math.sqrt(fc_psi), 100.0)
    return max(0.0, d.diameter.inches * psi_t * (stress / root - 340.0) / (13.6 + ratio))


def opening(d, gap, delta_open, fc_psi, cb_in, below_in, states, inputs) -> None:
    f_sus = SUSTAINED_FRACTION * ENVIRONMENTAL_FACTOR * d.bar_tensile_lb / (
        math.pi * d.diameter.inches ** 2 / 4.0)
    bond = bond_length(d, f_sus, fc_psi, cb_in, below_in)
    capacity = f_sus / d.bar_modulus_psi * (gap + bond)
    inputs.append(Quantity("delta_open", delta_open, "in", 1e-5))
    states.append(LimitState(
        "joint opening", delta_open, capacity, "in",
        f"court contraction over its full run; vs the bonded bar at ACI 440.11-22 §24.6.2's "
        f"sustained {f_sus:,.0f} psi (0.30 x 0.85 f*_fu) stretching over the {gap:.3f}\" gap + "
        f"{bond:.3f}\" of Eq. 25.4.2.4 bond (c_b {cb_in:.2f}\", concrete below "
        f"{below_in:.1f}\")"))


def development(d, court_embed, house_embed, post_installed, states) -> None:
    need = max(DEV_MIN_DIAMETERS * d.diameter.inches, DEV_MIN_IN)
    have = min(court_embed, house_embed)
    side = "house" if house_embed <= court_embed else "court"
    states.append(LimitState(
        "bar development", need, have, "in",
        f"ACI 440.11-22 §25.4.2.1: l_d >= max(Eq. 25.4.2.4, 20 d_b, 12\") = {need:.2f}\"; "
        f"embedment court {court_embed:.3f}\", house {house_embed:.3f}\" ({side} governs)"
        + ("; the house side is drilled and epoxied, which ACI 440.11-22 Ch. 17 does not "
           "address" if post_installed else ""),
        is_detailing=True))
