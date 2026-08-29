"""R807.1 attic access.

The rule only bites where there is an attic to get into: R807.1 exempts a space with less
than 30 sf at 30" of vertical height, which is most cathedral and low-slope roofs. That
applicability test is the whole difficulty, and it is answerable from the resolved roof.
"""

from __future__ import annotations

from typehaus.checks.code.mn_residential._common import (
    SF_PER_M2,
    _fail,
    _pass,
    _unknown,
)
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.quantities import inch
from typehaus.resolve.roof_geometry import roof_headroom_areas

_MIN_ATTIC_AREA_SF = 30.0  # R807.1 applicability
_MIN_ATTIC_HEIGHT = inch(30)  # R807.1 applicability, and the headroom above the opening
_MIN_HATCH_LONG = inch(30)  # R807.1: rough opening 22" x 30"
_MIN_HATCH_SHORT = inch(22)
_SF_PER_M2 = SF_PER_M2


@check(Tier.CODE, "code.R807_1_attic_access")
def attic_access(ctx: CheckContext) -> list[Finding]:
    """R807.1 — an attic over 30 sf with 30" of headroom needs a 22" x 30" access.

    A stair into the attic satisfies it outright and is the ordinary way a habitable attic
    complies — this house's does — so a stairway serving the attic storey is a PASS naming
    the stair rather than a demand for a scuttle nobody would build.
    """
    cid, code = "code.R807_1_attic_access", "R807.1"
    from typehaus.model.floors import FloorOpening, FloorOpeningPurpose

    if not ctx.plan.storeys:
        return [_unknown(cid, "the plan states no storeys", (), code)]
    top = max(ctx.plan.storeys, key=lambda s: s.elevation.meters)
    roofs = [roof for roof in ctx.model.roofs if roof.footprint]
    if not roofs:
        return [_unknown(cid, f"no roof resolves above storey {top.tag}, so there is no "
                         "attic volume to measure", (top.tag,), code)]

    area_sf = 0.0
    for roof in roofs:
        total, at_height = roof_headroom_areas(
            roof.footprint, roof, top.elevation.meters, _MIN_ATTIC_HEIGHT.meters)
        if total > 1e-9:
            area_sf += at_height * _SF_PER_M2
    if area_sf < _MIN_ATTIC_AREA_SF:
        return [_pass(cid, f"attic has {area_sf:.0f} sf at 30\" of height — under the 30 sf "
                      "R807.1 threshold, so no access is required", code)]

    stair = next((s for s in ctx.model.stairs if s.to_storey == top.tag), None)
    if stair is not None:
        return [_pass(cid, f"attic ({area_sf:.0f} sf at 30\") is reached by stair "
                      f"{stair.tag}", code)]

    hatches = [e for e in ctx.plan.all_elements()
               if isinstance(e, FloorOpening) and e.purpose is FloorOpeningPurpose.HATCH]
    if not hatches:
        return [_fail(cid, f"attic has {area_sf:.0f} sf at 30\" of height with no stair and "
                      "no hatch; R807.1 requires a 22\" x 30\" access", (top.tag,), code)]
    out: list[Finding] = []
    for hatch in hatches:
        verts = [p.xy_m for p in hatch.outline]
        if len(verts) < 3:
            out.append(_unknown(cid, f"{hatch.tag} has no usable outline to measure",
                                (hatch.tag,), code))
            continue
        xs = [v[0] for v in verts]
        ys = [v[1] for v in verts]
        short, long = sorted((max(xs) - min(xs), max(ys) - min(ys)))
        if (short + 1e-9 < _MIN_HATCH_SHORT.meters
                or long + 1e-9 < _MIN_HATCH_LONG.meters):
            out.append(_fail(cid, f"{hatch.tag} is {short / .0254:.0f}\" x "
                             f"{long / .0254:.0f}\"; R807.1 requires 22\" x 30\"",
                             (hatch.tag,), code))
        else:
            out.append(_pass(cid, f"{hatch.tag} is {short / .0254:.0f}\" x "
                             f"{long / .0254:.0f}\" (>= 22\" x 30\")", code))
    return out
