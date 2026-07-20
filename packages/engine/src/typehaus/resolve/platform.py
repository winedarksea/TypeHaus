"""Platform framing: exterior/bearing walls span floor-to-floor (#43).

Revit and SketchUp both expect a wall to run from its base level to the level above, with
the floor system butting into it. TypeHaus used to stop every wall at its own ceiling
height and patch the leftover joist band with a separate ``ResolvedEnvelopeBand`` proxy
object — which left a stud-depth void inboard of the sheathing and handed importers a
non-wall object at every storey line.

Here the lower wall simply grows to meet the wall stacked on it. Its *framing* does not:
``plate_top_z_m`` keeps the double top plate at the original ceiling height, so the band
above the plate is rim board and joists, which is what platform framing actually is.
"""

from __future__ import annotations

from dataclasses import replace

from typehaus.quantities import inch
from typehaus.resolve.model import ResolvedModel

# A storey line is a joist band. Anything deeper is a real void (a stairwell, a
# double-height space) and must not be silently absorbed into the wall below.
_MAX_BAND_M = inch(24).meters


def extend_walls_to_platform(model: ResolvedModel) -> None:
    """Grow each stacked lower wall up to the underside of the wall above it.

    The stack is the authored ``Wall.stacks_on`` graph — the same signal the old envelope
    band used — so this never guesses at which walls belong to one wall line.
    """
    lifted: set[str] = set()
    for upper in model.walls:
        authored = model.plan.by_tag(upper.tag)
        lower_tag = getattr(authored, "stacks_on", None)
        if not lower_tag or lower_tag in lifted:
            continue
        lower = model.wall(lower_tag)
        if lower is None or lower.is_foundation:
            continue
        band = upper.z0_m - lower.z1_m
        if band <= 1e-6 or band > _MAX_BAND_M:
            continue
        # A raked top (gable, wall-to-roof) has no flat platform to reach for.
        if lower.top_z0_m is not None or lower.top_z1_m is not None:
            continue
        index = next(i for i, w in enumerate(model.walls) if w is lower)
        model.walls[index] = replace(lower, z1_m=upper.z0_m, plate_top_z_m=lower.z1_m)
        lifted.add(lower.tag)
