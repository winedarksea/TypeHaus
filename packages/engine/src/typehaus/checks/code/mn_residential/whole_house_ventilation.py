"""MN 1322 R403.5 whole-house ventilation: the rate off the CFA, against the delivered flow.

Minnesota's own rule, which is NOT ASHRAE 62.2's and not the IRC's N1103.6 either:

    TVR = 0.02 cfm/ft2 x conditioned floor area + 15 cfm x (bedrooms + 1)

and the *continuous* portion must be at least half of that, never below 40 cfm. The area is
``resolve.conditioned_area``'s CFA (structural face, stair wells deducted once), not a room
sum: rooms stop at the finish face and leave every wall out.

The supply side is the ventilator's flow off its fan curve at the static the ducts make
(``mep.erv_static_budget``), where that resolves; otherwise the type's rated
``ventilation_cfm``. A rating is the curve at 0.2 in. w.g., which no real duct system lands
under, so grading the rating alone over-states every house.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from typehaus.checks.code.mn_residential._common import SF_PER_M2, _fail, _pass, _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, unknown
from typehaus.model.enums import EquipmentKind, Occupancy

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.model.plan import PlanModel
    from typehaus.resolve.model import ResolvedModel

_VENT_CFM_PER_FT2 = 0.02
_VENT_CFM_PER_OCCUPANT = 15.0
_CONTINUOUS_FRACTION_OF_TOTAL = 0.5
_MIN_CONTINUOUS_CFM = 40.0
WHOLE_HOUSE_REF = "MN 1322 R403.5"
# Owner's shortfall policy (2026-10-30): a delivered flow this close under the rate is inside
# the static budget's own chart-reading error, so only a commissioning reading settles it.
# UNKNOWN, never suppressed; past it is a FAIL. `notes/erv_static_budget.md` §10.4.
COMMISSIONING_BAND_CFM = 2.0


@dataclass(frozen=True)
class _ModelView:
    """The two fields the static budget reads, for a caller that holds no CheckContext."""

    plan: PlanModel
    model: ResolvedModel


@dataclass(frozen=True)
class WholeHouseVentilation:
    """R403.5's two rates and what the plan provides — what the check grades and G-005 prints.

    ``provided_cfm`` (the rating) is ``None`` when the plan states no rate: no ERV/HRV, or
    one whose type carries no ``ventilation_cfm``; ``reason`` says which. ``delivered_cfm`` is
    the fan-curve flow, ``None`` where the static budget cannot honestly produce one.
    """

    conditioned_area_ft2: float
    storey_areas_ft2: tuple[tuple[str, float], ...]
    area_basis: str
    bedrooms: int
    total_rate_cfm: float  # TVR
    continuous_rate_cfm: float  # CVR
    provided_cfm: float | None
    unit_tags: tuple[str, ...]
    unrated_tags: tuple[str, ...]
    reason: str | None = None
    delivered_cfm: float | None = None
    delivered_static_in_wg: float | None = None

    @property
    def graded_cfm(self) -> float | None:
        return self.delivered_cfm if self.delivered_cfm is not None else self.provided_cfm

    def verdict(self) -> str:
        """``pass`` | ``unknown`` (inside the commissioning band) | ``fail`` | ``unstated``."""
        graded = self.graded_cfm
        if graded is None:
            return "unstated"
        if self.provided_cfm is not None and self.provided_cfm + 1e-6 < self.total_rate_cfm:
            return "fail"
        shortfall = self.total_rate_cfm - graded
        if shortfall <= 1e-6:
            return "pass"
        return "unknown" if shortfall <= COMMISSIONING_BAND_CFM + 1e-6 else "fail"


def _delivered(units: list, ctx) -> tuple[float | None, float | None]:
    """Summed curve flow and the worst static, or ``(None, None)`` if any unit has none."""
    from typehaus.checks.mep.erv_static import delivered_flows

    flows = delivered_flows(ctx)
    readings = [flows.get(unit.tag) for unit in units]
    if not readings or any(reading is None for reading in readings):
        return None, None
    return sum(r[0] for r in readings), max(r[1] for r in readings)


def whole_house_summary(model: ResolvedModel, plan: PlanModel,
                        ctx: CheckContext | None = None) -> WholeHouseVentilation | None:
    """Derive R403.5's TVR and CVR and the rate the modelled equipment provides.

    ``None`` when no conditioned floor area resolves — with no area there is no requirement
    to state, which is a different answer from a requirement nothing meets.
    """
    from typehaus.resolve.conditioned_area import conditioned_floor_area

    cfa = conditioned_floor_area(model)
    area_ft2 = cfa.area_m2 * SF_PER_M2
    if area_ft2 <= 1e-6:
        return None
    storeys = tuple((row.storey, row.area_m2 * SF_PER_M2) for row in cfa.storeys)
    bedrooms = sum(1 for room in model.rooms if room.occupancy == Occupancy.BEDROOM.value)
    total = area_ft2 * _VENT_CFM_PER_FT2 + _VENT_CFM_PER_OCCUPANT * (bedrooms + 1)
    continuous = max(total * _CONTINUOUS_FRACTION_OF_TOTAL, _MIN_CONTINUOUS_CFM)
    base = {"conditioned_area_ft2": area_ft2, "storey_areas_ft2": storeys,
            "area_basis": cfa.basis, "bedrooms": bedrooms, "total_rate_cfm": total,
            "continuous_rate_cfm": continuous}

    units = [e for e in plan.all_elements()
             if e.element_kind == "Equipment" and e.kind is EquipmentKind.ERV]
    unit_tags = tuple(sorted(unit.tag for unit in units))
    if not units:
        return WholeHouseVentilation(**base, provided_cfm=None, unit_tags=(), unrated_tags=(),
                                     reason="no ERV/HRV equipment modeled")
    provided = 0.0
    unrated: list[str] = []
    for unit in units:
        unit_type = next((t for t in plan.library.equipment_types
                          if t.tag == unit.type_ref), None)
        cfm = getattr(unit_type, "ventilation_cfm", None) if unit_type else None
        if cfm is None:
            unrated.append(unit.tag)
        else:
            provided += cfm
    if unrated:
        return WholeHouseVentilation(
            **base, provided_cfm=None, unit_tags=unit_tags, unrated_tags=tuple(sorted(unrated)),
            reason=(f"ventilation unit(s) {', '.join(sorted(unrated))} state no "
                    "ventilation_cfm on their type"))
    delivered, static = _delivered(units, ctx if ctx is not None else _ModelView(plan, model))
    return WholeHouseVentilation(**base, provided_cfm=provided, unit_tags=unit_tags,
                                 unrated_tags=(), delivered_cfm=delivered,
                                 delivered_static_in_wg=static)


def _area_text(summary: WholeHouseVentilation) -> str:
    storeys = " + ".join(f"{tag} {ft2:,.0f}" for tag, ft2 in summary.storey_areas_ft2)
    return (f"{summary.conditioned_area_ft2:,.0f} sf conditioned floor area ({storeys}, "
            f"to the structural face, stair wells deducted once), "
            f"{summary.bedrooms} bedroom(s)")


@check(Tier.CODE, "code.N1103_6_whole_house_ventilation")
def whole_house_ventilation(ctx: CheckContext) -> list[Finding]:
    """MN Rules 1322 R403.5 — the dwelling needs a whole-house ventilation rate.

    ``EquipmentType.ventilation_cfm`` IS a continuous balanced flow, so a unit meeting TVR
    meets CVR by construction; CVR is printed for the certificate posted at the panel. The
    check id keeps its N1103.6 spelling (houses suppress by name); the citation is MN's.
    """
    cid, code = "code.N1103_6_whole_house_ventilation", WHOLE_HOUSE_REF
    summary = whole_house_summary(ctx.model, ctx.plan, ctx)
    if summary is None:
        return [_unknown(cid, "no conditioned floor area resolved", (), code)]
    rates = (f"{summary.total_rate_cfm:.1f} cfm total / "
             f"{summary.continuous_rate_cfm:.0f} cfm continuous")
    if summary.provided_cfm is None:
        return [_unknown(cid, f"{summary.reason}; R403.5 requires {rates} "
                         f"({_area_text(summary)})", summary.unrated_tags, code)]
    if summary.delivered_cfm is None:
        supply = (f"{summary.provided_cfm:.0f} cfm rated (no delivered flow resolves off the "
                  "fan curve, so the rating is graded)")
    else:
        supply = (f"{summary.delivered_cfm:.1f} cfm delivered at "
                  f"{summary.delivered_static_in_wg:.3f} in. w.g. off the fan curve "
                  f"({summary.provided_cfm:.0f} cfm rated)")
    detail = f"{supply} vs {rates} required ({_area_text(summary)})"
    verdict = summary.verdict()
    if verdict == "fail":
        return [_fail(cid, f"whole-house ventilation short: {detail}", summary.unit_tags, code)]
    if verdict == "unknown":
        short = summary.total_rate_cfm - summary.graded_cfm
        return [unknown(cid, f"{detail}: {short:.1f} cfm short, inside the "
                        f"{COMMISSIONING_BAND_CFM:.0f} cfm band only a commissioning reading "
                        "can settle", summary.unit_tags, code=code,
                        fix="measure the balanced flow at commissioning with a low-flow hood")]
    # The rate is only delivered if a ventilator riding an air handler's ducts runs with
    # that blower on — an authored control fact (``mep.erv_blower_interlock``).
    from typehaus.checks.mep.erv_interlock import uninterlocked

    loose = uninterlocked(ctx)
    if loose:
        pairs = "; ".join(f"{c.erv} -> {', '.join(c.missing)}" for c in loose)
        return [_unknown(cid, f"{detail}, but it reaches the rooms through an air handler's "
                         f"ducts with no blower interlock recorded ({pairs}; "
                         "Equipment.blower_interlock_ref)",
                         tuple(sorted({t for c in loose for t in (c.erv, *c.missing)})),
                         code)]
    return [_pass(cid, f"whole-house ventilation ok: {detail}", code)]
