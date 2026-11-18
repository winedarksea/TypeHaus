"""A door's girt sill course (``FramingSpec.sill_course``): blocks or an end-seated beam.

The course under a door runs at the floor band, so its screws land in the floor's edge
member, not a stud. ``blocks``: end blocks at the course ends and one-screw blocks between
(owner 2026-11-14). ``end_seats``: a beam on edge outboard of the girt band, its face at the
sill extender's nose, on one block stack back to the sheathing at each end (owner
2026-11-17). Each block or seat names its screw count in ``connection``, which the takeoff
and the approach grade read.
"""

from __future__ import annotations

import math
from dataclasses import replace

from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.framing.truss_common import BLOCK_CATEGORY, LADDER_CATEGORY
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


def end_seat_sill_course(frame, tier: str, index: int, band: str,
                         jambs: tuple[float, float], top: float, seat_top: float
                         ) -> list[FramedMember]:
    """The beam, back on the girt band's outer face, top at the rough sill (``top``), RO edge
    to RO edge; one seat stack per end, sheathing to the beam, under the buck (``seat_top``)."""
    spec = frame.sill_course
    beam = cross_section(spec.course_stock)
    girt_face = frame.sheathing_face + frame.buck_depth
    lo, hi = jambs
    axis = girt_face + beam.width_m / 2
    out = [FramedMember(
        frame.wall.uid, f"ladder-sill-{band}-{index:03d}", LADDER_CATEGORY, spec.course_stock,
        frame.point(lo, axis), frame.point(hi, axis), top - beam.depth_m, top, hi - lo,
        material=frame.band_materials[tier])]
    plies = max(1, round(frame.buck_depth / frame.stock_thickness))
    depth = frame.sheathing_face + frame.buck_depth / 2
    width = spec.seat_width.meters
    for side, (s0, s1) in enumerate(((lo, lo + width), (hi - width, hi))):
        out.append(FramedMember(
            frame.wall.uid, f"{sill_block_prefix(tier, index)}seat-{side}", BLOCK_CATEGORY,
            f"{plies}-{spec.course_stock}", frame.point(s0, depth), frame.point(s1, depth),
            seat_top - beam.depth_m, seat_top, width, material=frame.block_materials[tier],
            connection=f"{SILL_SCREWS}{spec.seat_rows * spec.screws_per_row}"))
    return out
