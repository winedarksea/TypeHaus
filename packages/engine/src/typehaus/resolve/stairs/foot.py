"""A flight's foot read off the pour it stands on (``Stair.foot_on``, decision #138).

From the AUTHORED slab, so it needs no resolved solid: slabs and stairs resolve in one
pass. The foot is the first riser line's middle, ``start`` plus half the width across.
"""

from __future__ import annotations

from typehaus.model.floors import Slab
from typehaus.model.spatial import Stair
from typehaus.resolve.slab_fall import slab_top_at


def foot_point(stair: Stair) -> tuple[float, float]:
    x, y = stair.start.xy_m
    half = stair.width.meters / 2
    return (x, y + half) if stair.run_direction == "x" else (x + half, y)


def foot_elevation(plan, stair: Stair) -> float | str:
    """The walking surface under the first riser, or why it cannot be read (a message)."""
    slab = plan.by_tag(stair.foot_on)
    if not isinstance(slab, Slab) or slab.top_elevation is None:
        return f"foot_on {stair.foot_on!r} names no Slab with a top_elevation"
    if stair.start is None:
        return "foot_on needs the flight's start"
    return slab_top_at(slab, *foot_point(stair))
