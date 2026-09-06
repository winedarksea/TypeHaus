"""The flood step: how far a wall's top stands above a court that ponds.

A sunken garden is a bowl. Catlin's is a court whose floor is flush with the basement slab
and whose only way out is a drain, so heavy rain — or a plugged drain in a thaw — stands in
it. What keeps that water out of the building is a concrete curb under the framed walls on
its north side, and the height of that curb is the whole rule: below the curb top the water
meets concrete, above it there is a bottom plate.

There is no IRC section behind this, which is why the finding is BUILDING_SCIENCE and not
CODE. R311.3.1 grades the same subtraction from the other direction — an exterior landing
may sit at most 1.5" (or one riser) *below* a threshold — and says nothing about a minimum.
No code article states how far a threshold must stand above a surface that holds water,
because the code does not know the surface holds water. That premise is a drainage
judgement, so it is **authored**: ``Wall.min_threshold_step``, the way
``WindowType.fall_protection`` is authored so R312.2 can fail fairly.

Why the wall's top and not a door's threshold. The curb runs the whole length of the court's
north side and only part of it has a door in it — grading D-B-PATIO alone would leave
W-B-S2, the sauna's curb, ungraded, and a sauna's bottom plate drowns exactly as well as a
gym's. The wall top is also the plane every threshold over it is measured from: an opening
in a wall standing on the curb has ``base_ref_z_m`` equal to the curb top, so a curb that
clears the water carries every threshold above it with it.
"""

from __future__ import annotations

from typehaus.checks._authoring import advisory, not_applicable, passed, unknown
from typehaus.checks.code.mn_residential._common import _rooms_by_storey
from typehaus.checks.code.mn_residential.egress import _landing_surfaces
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.quantities import inch
from typehaus.resolve.geometry import wall_frame

_CHECK_ID = "building_science.flood_step_threshold"
# How far out from the wall face a surface is still "the ground outside this wall". Three
# feet, borrowed from R311.3's landing depth: far enough to reach a court floor authored to
# its own finished edge rather than to the wall, near enough not to claim the pad on the
# far side of a walk.
_OUTWARD_REACH_M = inch(36).meters
# Slivers. A surface that only grazes the band with a corner is not the ground at the foot
# of this wall.
_MIN_BAND_OVERLAP_M2 = 0.02


def _outward_band(ctx: CheckContext, wall, rooms_by_storey):
    """The strip of plan just outside this wall, from its exterior face out 36"."""
    from shapely.geometry import Point, Polygon

    (sx, sy), (ux, uy), (nx, ny), run = wall_frame(wall)
    if run <= 1e-9:
        return None
    mid_x, mid_y = sx + ux * run / 2.0, sy + uy * run / 2.0
    # Outward is the side with no room on it — the same test ``_landing_patch`` makes for a
    # door, and for the same reason: nothing on a Wall names its outside.
    reach = wall.thickness_m / 2.0 + 0.15
    sign = 1.0
    if any(poly.covers(Point(mid_x + nx * reach, mid_y + ny * reach))
           for _room, poly in rooms_by_storey.get(wall.storey, ())):
        sign = -1.0
    ox, oy = nx * sign, ny * sign
    face = wall.thickness_m / 2.0
    corners = [
        (sx + ox * face, sy + oy * face),
        (sx + ox * (face + _OUTWARD_REACH_M), sy + oy * (face + _OUTWARD_REACH_M)),
        (sx + ux * run + ox * (face + _OUTWARD_REACH_M),
         sy + uy * run + oy * (face + _OUTWARD_REACH_M)),
        (sx + ux * run + ox * face, sy + uy * run + oy * face),
    ]
    band = Polygon(corners)
    return band if band.is_valid and band.area > 1e-9 else None


@check(Tier.BUILDING_SCIENCE, _CHECK_ID)
def flood_step_threshold(ctx: CheckContext) -> list[Finding]:
    """A wall whose foot ponds stands its declared step above the surface outside it."""
    required = {element.tag: step for element in ctx.plan.all_elements()
                if (step := getattr(element, "min_threshold_step", None)) is not None}
    if not required:
        return [not_applicable(_CHECK_ID, "no wall in this plan declares that the exterior "
                               "surface at its foot ponds, so there is no flood step to "
                               "hold", ())]
    rooms_by_storey = _rooms_by_storey(ctx)
    surfaces = _landing_surfaces(ctx)
    out: list[Finding] = []
    for tag in sorted(required):
        wall = ctx.model.wall(tag)
        if wall is None:
            out.append(unknown(_CHECK_ID, f"{tag} declares a flood step but resolves to no "
                               "wall to measure it on", (tag,)))
            continue
        band = _outward_band(ctx, wall, rooms_by_storey)
        if band is None:
            out.append(unknown(_CHECK_ID, f"{tag} has a degenerate axis, so the ground "
                               "outside it cannot be projected", (tag,)))
            continue
        # Only surfaces BELOW the top: the porch deck flies over this court eight feet up
        # and is not what water stands on. Of those, the HIGHEST is what governs — water
        # rises to the level of the highest thing it can reach, so the smallest step is the
        # real one.
        below = [(name, top) for name, poly, top in surfaces
                 if top < wall.z1_m - 1e-6
                 and poly.intersection(band).area >= _MIN_BAND_OVERLAP_M2]
        if not below:
            out.append(unknown(_CHECK_ID, f"{tag} declares a flood step but the plan models "
                               "no walk, slab or deck at its foot to measure it against",
                               (tag,)))
            continue
        name, top = max(below, key=lambda item: item[1])
        step = wall.z1_m - top
        want = required[tag].meters
        if step + 1e-6 < want:
            # ``advisory`` and not ``failed``: this reports as a FAIL and holds catlin's
            # clean report, but at WARN severity, so a house rule with no code article
            # behind it does not brick the permit gate the way an ERROR does.
            out.append(advisory(_CHECK_ID, f"{tag}'s top stands {step / 0.0254:.2f}\" above "
                                f"{name}, less than the {required[tag].fmt()} flood step it "
                                "declares; standing water in that court reaches whatever is "
                                "built on this wall", (tag, name), Result.FAIL))
        else:
            out.append(passed(_CHECK_ID, f"{tag}'s top stands {step / 0.0254:.2f}\" above "
                              f"{name}, at or over the {required[tag].fmt()} flood step it "
                              "declares"))
    return out
