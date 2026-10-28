"""R806.2 attic ventilation — net free area against the vented attic floor.

The requirement is an *area* ratio, which is why ``EaveSoffit.vented`` alone could never
answer it: a vented soffit is not a quantity. The net free area printed on the product is,
and R806.2 divides the sum of it by the attic floor it ventilates.

A roof's vented eave is nested: ``Roof.eave_trim.soffit_vented``. The walk therefore starts
at every plan roof, and the run lengths come from that roof's resolved soffit panels and
ridge run, since a nested trim carries no geometry of its own.

The rule's real subtlety is scope. An unvented (conditioned) roof assembly is a different
compliance path entirely — R806.5, insulation against the deck, no ventilation at all — and
demanding a 1/150 ratio of one would be applying the wrong section. So an assembly with no
vented eave anywhere scope-passes naming that, rather than failing.
"""

from __future__ import annotations

import math

from typehaus.checks.code.mn_residential._common import _fail, _pass, _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.spatial import Roof
from typehaus.model.trim import EaveSoffit, EaveTrim
from typehaus.resolve.roof_edge_geometry import roof_ridge_run
from typehaus.resolve.roof_geometry import roof_ceiling_area_m2

_BASE_RATIO = 1 / 150.0   # R806.2 default
_REDUCED_RATIO = 1 / 300.0  # R806.2 exception 2, with balanced upper/lower distribution
_MIN_UPPER_FRACTION = 0.40  # ...40-50% of the area in the upper portion
_MAX_UPPER_FRACTION = 0.50
_IN2_PER_M2 = 1550.0031
_M_PER_FT = 0.3048
_M2_PER_SF = 0.09290304
_VENTED_SOFFIT = "eave-trim:vented-soffit"  # the connection roof_trim stamps on vented panels


@check(Tier.CODE, "code.R806_2_attic_ventilation")
def attic_ventilation(ctx: CheckContext) -> list[Finding]:
    """R806.2 — vented attic net free area is 1/150 of the attic floor, or 1/300 if balanced."""
    cid, code = "code.R806_2_attic_ventilation", "R806.2"
    resolved = {roof.tag: roof for roof in ctx.model.roofs if roof.footprint}
    if not resolved:
        return [_unknown(cid, "no roofs resolve, so there is no attic to ventilate", (), code)]

    soffits = [e for e in ctx.plan.all_elements() if isinstance(e, EaveSoffit) and e.vented]
    vented_pairs = []
    for tag, trim in _vented_roofs(ctx):
        if tag not in resolved:
            return [_unknown(cid, f"the vented eave on {tag} resolves no roof, so there is no "
                             "attic to ventilate", (tag,), code)]
        vented_pairs.append((resolved[tag], trim))
    if not soffits and not vented_pairs:
        return [_pass(cid, "no vented eave is authored — the roof assemblies are unvented "
                      "(R806.5 insulation against the deck), which R806.2 does not govern",
                      code)]

    # A free-standing EaveSoffit names no roof, so it ventilates every roof's attic.
    attic_roofs = [roof for roof, _ in vented_pairs] or list(resolved.values())
    attic_m2 = 0.0
    for roof in attic_roofs:
        area = roof_ceiling_area_m2(ctx.model, roof)
        if area is None:
            return [_unknown(cid, f"the attic floor over {roof.tag} does not resolve (no bearing "
                             "footprint or pitch), so R806.2 has no area to divide", (roof.tag,),
                             code)]
        attic_m2 += area
    if attic_m2 <= 1e-9:
        return [_unknown(cid, "roof footprints resolve no attic floor to ventilate", (), code)]

    intake_in2, exhaust_in2, unrated = _vent_areas(vented_pairs, soffits)
    total_in2 = intake_in2 + exhaust_in2
    attic_sf = attic_m2 / _M2_PER_SF
    required_base = attic_m2 * _IN2_PER_M2 * _BASE_RATIO
    if total_in2 + 1e-6 >= required_base:
        # Unrated runs can only add, so a known total that clears 1/150 is a real PASS.
        return [_pass(cid, f"{total_in2:.0f} in² net free area over {attic_sf:.0f} sf of attic "
                      f"(>= 1/150 = {required_base:.0f} in²)", code)]
    if unrated:
        labels = ", ".join(f"{tag} {what}" for tag, what in unrated)
        tags = tuple(sorted({tag for tag, _ in unrated}))
        return [_unknown(cid, f"{total_in2:.0f} in² known against 1/150 = {required_base:.0f} "
                         f"in²; these runs state no net free area per foot: {labels}", tags, code)]

    required_reduced = attic_m2 * _IN2_PER_M2 * _REDUCED_RATIO
    upper_fraction = exhaust_in2 / total_in2 if total_in2 > 1e-9 else 0.0
    balanced = _MIN_UPPER_FRACTION <= upper_fraction <= _MAX_UPPER_FRACTION
    if total_in2 + 1e-6 >= required_reduced and balanced:
        return [_pass(cid, f"{total_in2:.0f} in² net free area with {upper_fraction:.0%} in "
                      f"the upper portion — R806.2 exception 2's 1/300 = "
                      f"{required_reduced:.0f} in²", code)]
    detail = (f"{total_in2:.0f} in² net free area over {attic_sf:.0f} sf of attic; R806.2 "
              f"requires {required_base:.0f} in² (1/150), or {required_reduced:.0f} in² (1/300) "
              f"with 40-50% of it in the upper portion — this roof has "
              f"{upper_fraction:.0%} up high")
    return [_fail(cid, f"attic ventilation short: {detail}",
                  tuple(sorted({roof.tag for roof in attic_roofs})), code)]


def _vented_roofs(ctx: CheckContext) -> list[tuple[str, EaveTrim]]:
    """Every plan roof whose nested eave trim is vented, as (tag, trim)."""
    return [(element.tag, element.eave_trim) for element in ctx.plan.all_elements()
            if isinstance(element, Roof) and element.eave_trim is not None
            and element.eave_trim.soffit_vented]


def _run_length_m(run) -> float:
    points = [p.xy_m for p in getattr(run, "path", ())]
    # Pairwise along the path: ``points[1:]`` is one shorter on purpose.
    return sum(((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
               for a, b in zip(points, points[1:], strict=False))


def _vent_areas(pairs, soffits) -> tuple[float, float, list[tuple[str, str]]]:
    """Intake and exhaust net free area in in², and every vent run stating no rating.

    Each rating is per foot, so lengths come from the resolved geometry: a roof's vented soffit
    panels (the eave and rake runs its trim closes) and its ridge run, which the ridge vent
    covers end to end. An unrated run is reported, never counted as zero.
    """
    intake, exhaust = 0.0, 0.0
    unrated: list[tuple[str, str]] = []
    for roof, trim in pairs:
        soffit_ft = sum(m.length_m for m in roof.members
                        if m.connection == _VENTED_SOFFIT) / _M_PER_FT
        if soffit_ft > 0:
            if trim.soffit_nfva_in2_per_ft is None:
                unrated.append((roof.tag, "soffit net free area"))
            else:
                intake += trim.soffit_nfva_in2_per_ft * soffit_ft
        ridge = roof_ridge_run(roof)
        if ridge is not None:
            if trim.ridge_vent_nfva_in2_per_ft is None:
                unrated.append((roof.tag, "ridge vent net free area"))
            else:
                ridge_m = math.hypot(ridge.p1[0] - ridge.p0[0], ridge.p1[1] - ridge.p0[1])
                exhaust += trim.ridge_vent_nfva_in2_per_ft * ridge_m / _M_PER_FT
    for soffit in soffits:
        if soffit.net_free_area_in2_per_ft is None:
            unrated.append((soffit.tag, "net free area"))
        else:
            intake += soffit.net_free_area_in2_per_ft * _run_length_m(soffit) / _M_PER_FT
    return intake, exhaust, unrated
