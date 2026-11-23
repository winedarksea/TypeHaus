"""Frames for authored tension ties across a joint (catlin's landing, G5 2026-11-23).

* an MSTA flat strap between coplanar wall faces: length along ``axis``, width plumb,
  thickness off the face;
* a DTT2Z pair on one horizontal rod across a wall (Simpson's deck lateral detail): each
  body runs AWAY from the wall along ``axis``, width plumb.
"""

from __future__ import annotations

from typing import Any

Vec3 = tuple[float, float, float]


def tie_frame(index: Any, part: str, references: Any, point: Any, axis: str | None,
              tangent: tuple[float, float]) -> tuple[Vec3, Vec3, Vec3] | None:
    if axis not in ("x", "y"):
        return None
    if part.startswith("MSTA"):
        return (0.0, 0.0, 1.0), (*tangent, 0.0), (-tangent[1], tangent[0], 0.0)
    if part == "DTT2Z" and len(references) == 2:
        wall = index.model.wall(references[1])
        if wall is None:
            return None
        xs, ys = zip(*wall.axis, strict=False)
        centre = (sum(xs) / len(xs), sum(ys) / len(ys))
        away = 1.0 if sum((point[i] - centre[i]) * tangent[i] for i in range(2)) > 0 else -1.0
        return (0.0, 0.0, -away), (-tangent[1], tangent[0], 0.0), \
            (away * tangent[0], away * tangent[1], 0.0)
    return None
