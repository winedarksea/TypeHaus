"""Bearing on the native soil under the washed-stone bed (review A1-09).

The bearing row grades the footing on the stone (IBC Table 1806.2 class 3). The load then
passes through the bed to the native at its bottom, which is the weaker material (class 4 for
the site's GM). The footing's pressure is spread through the bed at 2:1 (vertical:horizontal),
the strip growing by half the bed's thickness each side, and the stone's own weight is added.
The 2:1 spread is a standard engineering approximation, not a code row. The bed is read off
the resolved model; the worse end of the soil-unit-weight band governs.
"""

from __future__ import annotations

from typehaus.engineering import retaining_working as W
from typehaus.engineering.item import LimitState, Quantity, Step, num
from typehaus.engineering.retaining_system_body import STONE_PCF

_M_PER_FT = 0.3048
NAME = "bearing on the native under the stone"


def bed_thickness_ft(ctx, wall) -> float | None:  # type: ignore[no-untyped-def]
    """Thickness of the stone bed under the wall's footing, off the resolved bedding."""
    from typehaus.model.structure import Footing

    footing = next((f for f in ctx.plan.all_elements()
                    if isinstance(f, Footing) and f.under == wall.tag), None)
    bed = next((b for b in ctx.model.footing_beddings
                if footing is not None and b.host == footing.tag), None)
    return None if bed is None else (bed.z1_m - bed.z0_m) / _M_PER_FT


def native_bearing(ctx, wall, geometry, cases, soil):  # type: ignore[no-untyped-def]
    """``(LimitState, inputs)`` for the worse of ``cases``, or ``(None, ())`` without a bed."""
    z = bed_thickness_ft(ctx, wall)
    if not z or z <= 0.0:
        return None, ()
    b = geometry.footing_width_ft
    spread = b + z

    def pressure(case) -> float:  # type: ignore[no-untyped-def]
        e = abs(case.eccentricity_ft)
        return case.weight_plf / spread * (1.0 + 6.0 * e / spread) + STONE_PCF * z

    case = max(cases, key=pressure)
    e = abs(case.eccentricity_ft)
    footing_q = case.weight_plf / spread * (1.0 + 6.0 * e / spread)
    stone_q = STONE_PCF * z
    q = pressure(case)
    allowed = soil.allowable_bearing_psf
    steps = (
        Step("z", "thickness of the washed-stone bed under the footing", z * 12.0, "in",
             source="the model's bedding under this footing"),
        Step("B", "footing width", b, "ft"),
        Step("B_z", "width the footing's load has spread to at the bed's bottom, 2:1",
             spread, "ft", "B + z", f"{num(b)} + {num(z)}",
             "2 vertical : 1 horizontal each side (an engineering approximation)"),
        Step("W", f"weight per foot at the footing, soil at {num(case.soil_pcf)} pcf "
             "(the worse end of the band)", case.weight_plf, "plf",
             source="the sliding row's weight"),
        Step("e", "eccentricity of the resultant, kept as at the footing", e, "ft",
             source="the bearing row"),
        Step("q_f", "footing load's pressure on the native", footing_q, "psf",
             "W / B_z (1 + 6 e / B_z)",
             f"{num(case.weight_plf)} / {num(spread)} x (1 + 6 x {num(e)} / {num(spread)})"),
        Step("q_s", "weight of the stone above the native", stone_q, "psf", "100 pcf x z",
             f"{num(STONE_PCF)} x {num(z)}", "the library's #57 density"),
        Step("q", "pressure on the native at the bed's bottom", q, "psf", "q_f + q_s",
             f"{num(footing_q)} + {num(stone_q)}"),
        Step("q_allow", "allowable bearing of the native", allowed, "psf",
             source=f"IBC Table 1806.2, class {soil.ibc_class}, presumed"))
    state = LimitState(
        NAME, q, allowed, "psf",
        f"IBC Table 1806.2 class {soil.ibc_class} on the native at the bed bottom: the "
        f"footing's pressure spread through {z * 12:.0f}\" of stone at 2:1 plus the stone's "
        f"weight, soil at {case.soil_pcf:.0f} pcf",
        combination=W.SERVICE[0], combination_factors=W.SERVICE[1], working=steps)
    return state, (Quantity("bed_thickness", z * 12.0, "in", 0.01),
                   Quantity("stone_unit_weight", STONE_PCF, "pcf", 1.0),
                   Quantity("native_allowable_bearing", allowed, "psf", 1.0))
