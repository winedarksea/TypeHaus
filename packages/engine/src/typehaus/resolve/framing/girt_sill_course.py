"""A door's girt sill course blocks (``FramingSpec.sill_course``, owner 2026-11-14).

The course under a door runs at the floor band, so its screws land in the floor's edge
member, not a stud: unlike a window's, its end blocks stand at the course ends. Each block
names its screw count in ``connection``, which the takeoff and the approach grade read.
"""

from __future__ import annotations

import math
from dataclasses import replace

from typehaus.resolve.model import FramedMember

#: ``connection`` prefix on a door sill course block: ``girt-sill-screws:<n>``.
SILL_SCREWS = "girt-sill-screws:"


def sill_block_prefix(tier: str, index: int) -> str:
    """Child-key prefix of the blocks under opening ``index``'s sill course."""
    return f"block-{tier}-sill-{index:03d}-"


def sill_block_screws(member: FramedMember) -> int | None:
    """The screw count a door sill course block carries, or ``None`` for any other block."""
    connection = member.connection or ""
    return int(connection[len(SILL_SCREWS):]) if connection.startswith(SILL_SCREWS) else None


def sill_course_blocks(frame, tier: str, index: int, span: tuple[float, float],
                       z0: float) -> list[FramedMember]:
    """End blocks at ``span``'s ends with ``end_screws`` each, one-screw blocks between."""
    spec = frame.sill_course
    lo, hi = span
    gaps = max(1, math.ceil((hi - lo) / spec.block_spacing.meters - 1e-9))
    out = []
    for count in range(gaps + 1):
        screws = spec.end_screws if count in (0, gaps) else 1
        block = frame._block(tier, lo + count * (hi - lo) / gaps, z0,
                             f"{sill_block_prefix(tier, index)}{count:02d}")
        out.append(replace(block, connection=f"{SILL_SCREWS}{screws}"))
    return out
