"""R806.2 attic ventilation — net free area against the vented attic footprint.

The requirement is an *area* ratio, which is why ``EaveSoffit.vented`` alone could never
answer it: a vented soffit is not a quantity. The net free area printed on the product is,
and R806.2 divides the sum of it by the footprint it ventilates.

The rule's real subtlety is scope. An unvented (conditioned) roof assembly is a different
compliance path entirely — R806.5, insulation against the deck, no ventilation at all — and
demanding a 1/150 ratio of one would be applying the wrong section. So an assembly with no
vented eave anywhere scope-passes naming that, rather than failing.
"""

from __future__ import annotations

from typehaus.checks.code.mn_residential._common import _fail, _pass, _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding

_BASE_RATIO = 1 / 150.0   # R806.2 default
_REDUCED_RATIO = 1 / 300.0  # R806.2 exception 2, with balanced upper/lower distribution
_MIN_UPPER_FRACTION = 0.40  # ...40-50% of the area in the upper portion
_MAX_UPPER_FRACTION = 0.50
_IN2_PER_M2 = 1550.0031


@check(Tier.CODE, "code.R806_2_attic_ventilation")
def attic_ventilation(ctx: CheckContext) -> list[Finding]:
    """R806.2 — vented attic net free area is 1/150 of the space, or 1/300 if balanced."""
    from typehaus.model.trim import EaveSoffit, EaveTrim

    cid, code = "code.R806_2_attic_ventilation", "R806.2"
    roofs = [roof for roof in ctx.model.roofs if roof.footprint]
    if not roofs:
        return [_unknown(cid, "no roofs resolve, so there is no attic to ventilate", (), code)]

    soffits = [e for e in ctx.plan.all_elements() if isinstance(e, EaveSoffit) and e.vented]
    trims = [e for e in ctx.plan.all_elements() if isinstance(e, EaveTrim)]
    vented_trims = [t for t in trims if t.soffit_vented]
    if not soffits and not vented_trims:
        return [_pass(cid, "no vented eave is authored — the roof assemblies are unvented "
                      "(R806.5 insulation against the deck), which R806.2 does not govern",
                      code)]

    footprint_m2 = sum(_ring_area(roof.footprint) for roof in roofs)
    if footprint_m2 <= 1e-9:
        return [_unknown(cid, "roof footprints resolve no area to ventilate", (), code)]

    lower_in2, unrated = _intake_area(soffits, vented_trims)
    upper_in2, unrated_upper = _exhaust_area(vented_trims)
    unrated = unrated + unrated_upper
    if unrated:
        return [_unknown(cid, f"vent run(s) {', '.join(sorted(unrated))} state no net free "
                         "area per foot, so the R806.2 ratio cannot be computed",
                         tuple(sorted(unrated)), code)]

    total_in2 = lower_in2 + upper_in2
    required_base = footprint_m2 * _IN2_PER_M2 * _BASE_RATIO
    if total_in2 + 1e-6 >= required_base:
        return [_pass(cid, f"{total_in2:.0f} in² net free area over {footprint_m2 * 10.7639:.0f} "
                      f"sf of attic (>= 1/150 = {required_base:.0f} in²)", code)]

    required_reduced = footprint_m2 * _IN2_PER_M2 * _REDUCED_RATIO
    upper_fraction = upper_in2 / total_in2 if total_in2 > 1e-9 else 0.0
    balanced = _MIN_UPPER_FRACTION <= upper_fraction <= _MAX_UPPER_FRACTION
    if total_in2 + 1e-6 >= required_reduced and balanced:
        return [_pass(cid, f"{total_in2:.0f} in² net free area with {upper_fraction:.0%} in "
                      f"the upper portion — R806.2 exception 2's 1/300 = "
                      f"{required_reduced:.0f} in²", code)]
    detail = (f"{total_in2:.0f} in² net free area over {footprint_m2 * 10.7639:.0f} sf of "
              f"attic; R806.2 requires {required_base:.0f} in² (1/150), or "
              f"{required_reduced:.0f} in² (1/300) with 40-50% of it in the upper portion "
              f"— this roof has {upper_fraction:.0%} up high")
    return [_fail(cid, f"attic ventilation short: {detail}", (), code)]


def _ring_area(ring) -> float:
    from shapely.geometry import Polygon

    if len(ring) < 3:
        return 0.0
    polygon = Polygon(ring)
    return polygon.area if polygon.is_valid else 0.0


def _run_length_m(run) -> float:
    points = [p.xy_m for p in getattr(run, "path", ())]
    return sum(((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
               for a, b in zip(points, points[1:]))


def _intake_area(soffits, trims) -> tuple[float, list[str]]:
    """Eave-level net free area, in square inches, and any run that states no rating."""
    total, unrated = 0.0, []
    for soffit in soffits:
        if soffit.net_free_area_in2_per_ft is None:
            unrated.append(soffit.tag)
        else:
            total += soffit.net_free_area_in2_per_ft * _run_length_m(soffit) / 0.3048
    for trim in trims:
        if trim.soffit_nfva_in2_per_ft is None:
            unrated.append(trim.tag)
        else:
            total += trim.soffit_nfva_in2_per_ft * _run_length_m(trim) / 0.3048
    return total, unrated


def _exhaust_area(trims) -> tuple[float, list[str]]:
    """Ridge-level net free area. A trim stating no ridge rating contributes zero, not
    UNKNOWN: a vented soffit with no ridge vent is a real (if poor) configuration, and the
    1/150 path does not require any upper-portion area at all."""
    total = 0.0
    for trim in trims:
        if trim.ridge_vent_nfva_in2_per_ft is not None:
            total += trim.ridge_vent_nfva_in2_per_ft * _run_length_m(trim) / 0.3048
    return total, []
