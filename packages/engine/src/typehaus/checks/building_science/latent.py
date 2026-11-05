"""The air-side latent cooling load: infiltration and ventilation moisture.

``q = 0.68 · CFM · Δgr`` (Manual J / ASHRAE Fundamentals Ch. 17), with Δgr the outdoor
design humidity ratio less the indoor one, in grains per lb of dry air. The outdoor ratio
comes off ``Site.design_wet_bulb_cooling`` (the coincident wet bulb a code table prints
beside the dry bulb), the indoor one off ``Preferences.cooling_relative_humidity`` at the
cooling setpoint, both at the site's barometric pressure. Psychrometrics per ASHRAE
Fundamentals Ch. 1 (Hyland-Wexler saturation pressure, Eq. 35 for W from wet bulb).

Hand-worked for catlin in ``houses/catlin/notes/block_load_basis.md`` §9.
"""

from __future__ import annotations

import math

from typehaus.resolve.model import ResolvedModel

# 0.075 lb/ft³ × 60 min/h × 1,061 Btu/lb ÷ 7,000 gr/lb, at sea level.
LATENT_BTU_PER_CFM_GR = 0.68
_SEA_LEVEL_PSIA = 14.696
_GRAINS_PER_LB = 7000.0


def saturation_pressure_psia(temp_f: float) -> float:
    """Saturation vapour pressure over liquid water (ASHRAE Fundamentals Ch. 1 Eq. 6)."""
    t = temp_f + 459.67
    return math.exp(-1.0440397e4 / t - 1.1294650e1 - 2.7022355e-2 * t + 1.2890360e-5 * t * t
                    - 2.4780681e-9 * t ** 3 + 6.5459673 * math.log(t))


def humidity_ratio_from_rh(temp_f: float, rh: float, pressure_psia: float) -> float:
    pw = rh * saturation_pressure_psia(temp_f)
    return 0.621945 * pw / (pressure_psia - pw)


def humidity_ratio_from_wet_bulb(db_f: float, wb_f: float, pressure_psia: float) -> float:
    """ASHRAE Fundamentals Ch. 1 Eq. 35 (IP)."""
    ws = humidity_ratio_from_rh(wb_f, 1.0, pressure_psia)
    return ((1093 - 0.556 * wb_f) * ws - 0.240 * (db_f - wb_f)) / (1093 + 0.444 * db_f - wb_f)


def design_grains_difference(site, preferences, pressure_ratio: float) -> float | None:
    """Outdoor less indoor humidity ratio at the cooling design hour, gr/lb; ``None`` with no
    coincident wet bulb authored. Never negative: dry outdoor air is no latent credit."""
    if site.design_temp_cooling is None or site.design_wet_bulb_cooling is None:
        return None
    pressure = _SEA_LEVEL_PSIA * pressure_ratio
    outdoor = humidity_ratio_from_wet_bulb(site.design_temp_cooling.fahrenheit,
                                           site.design_wet_bulb_cooling.fahrenheit, pressure)
    indoor = humidity_ratio_from_rh(preferences.cooling_setpoint_f,
                                    preferences.cooling_relative_humidity, pressure)
    return max(0.0, outdoor - indoor) * _GRAINS_PER_LB


def ventilation_latent_cfm(model: ResolvedModel, caveats: list[str]) -> float:
    """``Σ cfm × (1 − latent recovery)`` over the authored ERV/HRVs.

    An ERV with no ``latent_recovery_effectiveness`` is charged with none — the upper bound,
    stated in ``caveats``. A missing ``ventilation_cfm`` is already named by the sensible
    ventilation term and is skipped here.
    """
    types = {item.tag: item for item in model.plan.library.equipment_types}
    total = 0.0
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if element.element_kind != "Equipment" or element.kind.value != "erv":
                continue
            product = types.get(element.type_ref)
            cfm = getattr(product, "ventilation_cfm", None)
            if cfm is None:
                continue
            recovery = getattr(product, "latent_recovery_effectiveness", None)
            if recovery is None:
                caveats.append(f"{element.tag} states no latent_recovery_effectiveness, so its "
                               "ventilation latent is charged with no recovery (upper bound)")
                recovery = 0.0
            total += cfm * (1.0 - recovery)
    return total
