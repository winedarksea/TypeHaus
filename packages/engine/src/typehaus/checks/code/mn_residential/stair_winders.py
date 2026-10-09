"""R311.7.4 / R311.7.5.2.1 measured from complete resolved winder geometry."""

from __future__ import annotations

from shapely.geometry import Polygon

from typehaus.checks.code.mn_residential._common import _fail, _pass, _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, not_applicable
from typehaus.quantities import inch
from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.stairs.winder_geometry import (
    GEOMETRY_TOLERANCE_M,
    WinderMeasurements,
    measure_winders,
    physical_nosing_line,
)

CHECK_ID = "code.R311_7_5_2_1_winder_treads"
MINIMUM_WALKLINE_DEPTH_M = inch(10).meters
MINIMUM_NARROW_DEPTH_M = inch(6).meters
MAXIMUM_WALKLINE_VARIATION_M = inch(.375).meters


def winder_measurements(stair) -> WinderMeasurements:
    layout = stair.winder_turn
    if layout is None:
        raise ValueError("clear winder inner boundary is missing")
    winders = sorted((m for m in stair.members if m.category == "winder"),
                     key=lambda member: member.z1_m)
    if len(winders) != stair.winder_count:
        raise ValueError("resolved winder count differs from the stair's tread budget")
    if any(member.riser_line is None or member.nosing_line is None for member in winders):
        raise ValueError("winder riser or finished nosing geometry is missing")
    next_tread = min((m for m in stair.members if m.category == "tread"),
                     key=lambda member: member.z1_m, default=None)
    if next_tread is not None:
        if next_tread.riser_line is None:
            raise ValueError("straight-flight transition riser is missing")
        # Read the physical board edge so moving a tread without moving its metadata fails.
        nose = physical_nosing_line(Polygon(member_footprint(next_tread)[0]), layout.normals[-1])
        terminal_riser = next_tread.riser_line
    else:
        head = next((p for p in stair.finish_parts if p.key == "stairhead:nosing"), None)
        if head is None:
            raise ValueError("arrival nosing at the last winder is missing")
        nx, ny = layout.normals[-1]
        nose = tuple(sorted(head.outline, key=lambda p: p[0] * nx + p[1] * ny)[:2])
        terminal_riser = layout.riser_lines[-1]
    return measure_winders(layout.inner_boundary,
                           tuple(m.riser_line for m in winders) + (terminal_riser,),
                           tuple(physical_nosing_line(Polygon(m.plan_outline), normal)
                                 for m, normal in zip(winders, layout.normals, strict=False))
                           + (nose,))


@check(Tier.CODE, CHECK_ID)
def winder_treads(ctx: CheckContext) -> list[Finding]:
    out = []
    for stair in ctx.model.stairs:
        if stair.layout != "right_angle_winder":
            continue
        tags = (stair.tag,)
        try:
            measured = winder_measurements(stair)
        except ValueError as exc:
            out.append(_unknown(CHECK_ID, f"{stair.tag}: {exc}", tags, "R311.7.5.2.1"))
            continue
        walk = measured.walkline_depths_m
        narrow = measured.narrow_depths_m
        spread = max(walk) - min(walk)
        problems = []
        if min(walk) < MINIMUM_WALKLINE_DEPTH_M - GEOMETRY_TOLERANCE_M:
            problems.append("walkline depth below 10 inches")
        if min(narrow) < MINIMUM_NARROW_DEPTH_M - GEOMETRY_TOLERANCE_M:
            problems.append("depth within clear width below 6 inches")
        if spread > MAXIMUM_WALKLINE_VARIATION_M + GEOMETRY_TOLERANCE_M:
            problems.append("walkline depth variation exceeds 3/8 inch")
        label = (f"{stair.tag}: {len(walk)} winder depths at the 12-inch walkline "
                 + ", ".join(f'{depth / .0254:.3f}"' for depth in walk)
                 + f'; narrow depths {", ".join(f"{depth / .0254:.3f}" for depth in narrow)}"'
                 + f'; walkline spread {spread / .0254:.3f}"')
        out.append(_fail(CHECK_ID, label + "; " + "; ".join(problems), tags, "R311.7.5.2.1")
                   if problems else _pass(CHECK_ID, label, "R311.7.5.2.1"))
    return out or [not_applicable(CHECK_ID, "no winder stairs", (), "R311.7.5.2.1")]
