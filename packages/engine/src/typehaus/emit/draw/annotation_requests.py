"""Helpers that add a visible seed label and a scale-aware placement request."""

from __future__ import annotations

import math

from typehaus.emit.draw.annotate import wrap_label
from typehaus.emit.draw.annotation_layout import AnnotationRequest, Candidate
from typehaus.emit.draw.annotation_layout_config import LINE_OFFSET_PT, POINT_OFFSET_PT
from typehaus.emit.draw.scene import SceneBuilder, Text
from typehaus.emit.draw.typography import TEXT_PT

Pt = tuple[float, float]


def _reading_angle(dx: float, dy: float) -> float:
    angle = math.degrees(math.atan2(dy, dx))
    return angle + 180.0 if angle > 90.0 or angle <= -90.0 else angle


def add_point_label(builder: SceneBuilder, *, key: str, text: str, target: Pt,
                    layer: str, height_pt: float = TEXT_PT, priority: int = 0,
                    preferred_direction: Pt = (1.0, 1.0), leader: bool = True,
                    avoid_obstacles: bool = True) -> None:
    """Add a seed text node and eight paper-offset candidates around a point feature."""
    text = wrap_label(text, 48) if len(text) > 48 else text
    uid = f"layout-label:{key}"
    directions = (preferred_direction, (1.0, 0.0), (1.0, -1.0),
                  (-1.0, 1.0), (-1.0, 0.0), (-1.0, -1.0), (0.0, 1.0), (0.0, -1.0))
    candidates = tuple(Candidate(
        at=target,
        align="left" if dx > 0 else "right" if dx < 0 else "center",
        leader=leader,
        paper_offset=(dx * POINT_OFFSET_PT, dy * POINT_OFFSET_PT),
    ) for dx, dy in dict.fromkeys(directions))
    seed = candidates[0]
    builder.add(Text(anchor=target, content=text, height_pt=height_pt, layer=layer,
                     align=seed.align, uid=uid))
    builder.add_annotation_request(AnnotationRequest(
        key=key, text=text, target=target, candidates=candidates, height_pt=height_pt,
        priority=priority, layer=layer, uid=uid, avoid_obstacles=avoid_obstacles))


def add_line_label(builder: SceneBuilder, *, key: str, text: str, start: Pt, end: Pt,
                   layer: str, height_pt: float = TEXT_PT, priority: int = 0,
                   preferred_side: int = 1) -> None:
    """Add positions at five stations along either side of the associated line."""
    text = wrap_label(text, 48) if len(text) > 48 else text
    dx, dy = end[0] - start[0], end[1] - start[1]
    run = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / run, dx / run
    rotation = _reading_angle(dx, dy)
    candidates = []
    for side in (preferred_side, -preferred_side):
        for fraction in (0.5, 0.3, 0.7, 0.15, 0.85):
            base = (start[0] + dx * fraction, start[1] + dy * fraction)
            candidates.append(Candidate(at=base, align="center", rotation=rotation,
                                        paper_offset=(nx * LINE_OFFSET_PT * side,
                                                      ny * LINE_OFFSET_PT * side)))
    midpoint = ((start[0] + end[0]) / 2.0, (start[1] + end[1]) / 2.0)
    candidates.append(Candidate(at=midpoint, align="left", leader=True,
                                paper_offset=(POINT_OFFSET_PT, POINT_OFFSET_PT)))
    uid = f"layout-label:{key}"
    builder.add(Text(anchor=midpoint, content=text, height_pt=height_pt, rotation=rotation,
                     layer=layer, align="center", uid=uid))
    builder.add_annotation_request(AnnotationRequest(
        key=key, text=text, target=midpoint, candidates=tuple(candidates),
        height_pt=height_pt, priority=priority, layer=layer, uid=uid))
