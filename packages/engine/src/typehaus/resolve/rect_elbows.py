"""The rectangular duct elbow the ``DuctStandard`` has shop-made (``RectElbowRow``).

A rectangular elbow is fabricated to the duct's own section, so it has no catalog row: its
centreline radius is the standard's r/W times the section side lying in the plane of the
turn, read off the sweep's own leg frame (``resolve/sweep.leg_frame``: width across the leg,
depth through it). Without a row the turn stays the coverage gap below.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from typehaus.hardware.fittings import KIND_ELBOW, SERVICE_DUCT, FittingSpec
from typehaus.model.ducts import duct_size_text
from typehaus.quantities import M_PER_IN
from typehaus.resolve.duct_standard import ELBOW_SNAP_DEG
from typehaus.resolve.sweep import leg_frame

Vec3 = tuple[float, float, float]

RECTANGULAR_DUCT_GAP = ("a rectangular duct elbow is fabricated to the duct, not ordered "
                        "from a pattern catalog — its throat radius comes off a shop "
                        "drawing and nothing here can stand in for one")


def plane_side_m(path: Sequence[Vec3], index: int, width_m: float, depth_m: float) -> float:
    """The section side in the plane of the turn at ``index``: ``width_m`` for a turn in
    plan, ``depth_m`` for one into or out of a rise. Framed on a non-vertical leg."""
    a, b, c = path[index - 1], path[index], path[index + 1]
    before = tuple(q - p for p, q in zip(a, b, strict=True))
    after = tuple(q - p for p, q in zip(b, c, strict=True))
    normal = (before[1] * after[2] - before[2] * after[1],
              before[2] * after[0] - before[0] * after[2],
              before[0] * after[1] - before[1] * after[0])
    ref = before if math.hypot(before[0], before[1]) > 1e-9 else after
    right, up = leg_frame(ref)
    across = abs(sum(r * n for r, n in zip(right, normal, strict=True)))
    through = abs(sum(u * n for u, n in zip(up, normal, strict=True)))
    return width_m if across <= through else depth_m


def rect_elbow_spec(standard: Any, path: Sequence[Vec3], index: int, angle_deg: float,
                    width_m: float, depth_m: float) -> tuple[FittingSpec | None, str | None,
                                                             float | None]:
    """``(spec, gap, in-plane side in inches)`` for one rectangular turn."""
    row = getattr(standard, "rect_elbow", None)
    if row is None or not width_m or not depth_m:
        return None, RECTANGULAR_DUCT_GAP, None
    side_in = plane_side_m(path, index, width_m, depth_m) / M_PER_IN
    if angle_deg > row.max_angle + ELBOW_SNAP_DEG:
        return None, (f"a {angle_deg:.1f} degree turn is past the {row.max_angle:g} degrees "
                      "one shop-made rectangular elbow makes — two elbows with a straight "
                      "between, or re-draw the turn"), side_in
    radius_in = row.radius_ratio * side_in
    section = duct_size_text(None, width_m, depth_m)
    return FittingSpec(
        tag=f"FIT-DUCT-RECT-R{row.radius_ratio:g}-{section}",
        name=(f"{angle_deg:.0f} degree rectangular radius elbow, {section}, r/W "
              f"{row.radius_ratio:g} ({radius_in:.2f}\" centreline), shop-fabricated"),
        service=SERVICE_DUCT, kind=KIND_ELBOW, nominal_in=round(max(width_m, depth_m)
                                                                / M_PER_IN, 3),
        angle_deg=round(angle_deg, 1), bend_radius_in=radius_in, source=row.source,
        data_note="fabricated to the duct's section; no catalog row"), None, side_in
