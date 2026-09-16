"""Deterministic, printed-space placement for annotations on framed drawings.

The solver intentionally stays small: callers supply a bounded set of meaningful candidate
positions and this module chooses among them.  That preserves association with the feature
being described while still providing collision avoidance, viewport containment, leaders,
and explicit diagnostics when a crowded drawing has no clean answer.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from shapely.geometry import LineString, Polygon
from shapely.geometry import box as shapely_box

from typehaus.emit.draw.annotate import model_in_per_pt, text_extent
from typehaus.emit.draw.annotation_layout_config import LABEL_CLEARANCE_PT
from typehaus.emit.draw.typography import TEXT_PT

Pt = tuple[float, float]
Bounds = tuple[float, float, float, float]


@dataclass(frozen=True)
class Candidate:
    at: Pt
    align: str = "left"
    rotation: float = 0.0
    leader: bool = False
    paper_offset: Pt = (0.0, 0.0)


@dataclass(frozen=True)
class AnnotationRequest:
    key: str
    text: str
    target: Pt | None
    candidates: tuple[Candidate, ...]
    height_pt: float = TEXT_PT
    priority: int = 0
    required: bool = True
    layer: str = "A-ANNO-TEXT"
    uid: str | None = None
    avoid_obstacles: bool = True


@dataclass(frozen=True)
class SegmentObstacle:
    start: Pt
    end: Pt
    clearance_pt: float = 0.0
    hard: bool = True


@dataclass(frozen=True)
class BoxObstacle:
    bounds: Bounds
    hard: bool = True


@dataclass(frozen=True)
class Viewport:
    bounds: Bounds


@dataclass(frozen=True)
class Placement:
    request: AnnotationRequest
    candidate: Candidate
    polygon: tuple[Pt, ...]
    box: Bounds


@dataclass(frozen=True)
class LayoutDiagnostic:
    key: str
    reason: str
    conflicts: tuple[str, ...] = ()


@dataclass(frozen=True)
class LayoutResult:
    placements: tuple[Placement, ...]
    diagnostics: tuple[LayoutDiagnostic, ...]


def annotation_polygon(candidate: Candidate, text: str, height_pt: float,
                       scale: float | None) -> Polygon:
    """Rotation-aware model-space polygon occupied by one rendered text block."""
    per_pt = model_in_per_pt(scale)
    width_pt, height_block_pt = text_extent(text, height_pt)
    width, height = width_pt * per_pt, height_block_pt * per_pt
    if candidate.align == "right":
        x0 = -width
    elif candidate.align == "center":
        x0 = -width / 2.0
    else:
        x0 = 0.0
    local = ((x0, -height / 2.0), (x0 + width, -height / 2.0),
             (x0 + width, height / 2.0), (x0, height / 2.0))
    angle = math.radians(candidate.rotation)
    cosine, sine = math.cos(angle), math.sin(angle)
    ax, ay = candidate.at
    return Polygon(tuple((ax + x * cosine - y * sine, ay + x * sine + y * cosine)
                         for x, y in local))


def _at_scale(candidate: Candidate, scale: float | None) -> Candidate:
    per_pt = model_in_per_pt(scale)
    return Candidate(at=(candidate.at[0] + candidate.paper_offset[0] * per_pt,
                         candidate.at[1] + candidate.paper_offset[1] * per_pt),
                     align=candidate.align, rotation=candidate.rotation,
                     leader=candidate.leader)


def point_candidates(target: Pt, *, offset_pt: float, scale: float | None,
                     preferred: Pt | None = None) -> tuple[Candidate, ...]:
    """Eight nearby positions in stable reading order, optionally led by ``preferred``."""
    offset = offset_pt * model_in_per_pt(scale)
    x, y = target
    out = []
    if preferred is not None:
        out.append(Candidate(preferred, "left" if preferred[0] >= x else "right"))
    out.extend((
        Candidate((x + offset, y + offset), "left"),
        Candidate((x + offset, y), "left"),
        Candidate((x + offset, y - offset), "left"),
        Candidate((x - offset, y + offset), "right"),
        Candidate((x - offset, y), "right"),
        Candidate((x - offset, y - offset), "right"),
        Candidate((x, y + offset), "center"),
        Candidate((x, y - offset), "center"),
    ))
    return tuple(dict.fromkeys(out))


def line_candidates(start: Pt, end: Pt, *, offset_pt: float, scale: float | None,
                    outward: int = 1) -> tuple[Candidate, ...]:
    """Positions along a line at three stations and on either normal side."""
    dx, dy = end[0] - start[0], end[1] - start[1]
    run = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / run, dx / run
    angle = math.degrees(math.atan2(dy, dx))
    if angle > 90.0 or angle <= -90.0:
        angle += 180.0
    offset = offset_pt * model_in_per_pt(scale)
    out = []
    for side in (outward, -outward):
        for fraction in (0.5, 0.3, 0.7):
            point = (start[0] + dx * fraction + nx * offset * side,
                     start[1] + dy * fraction + ny * offset * side)
            out.append(Candidate(point, "center", angle))
    return tuple(out)


def resolve_annotations(requests: tuple[AnnotationRequest, ...] | list[AnnotationRequest],
                        viewport: Viewport,
                        obstacles: tuple[SegmentObstacle | BoxObstacle, ...] = (),
                        scale: float | None = None) -> LayoutResult:
    """Choose one candidate per request and report every unavoidable collision.

    The ordering and every tie break are stable.  Required labels are always retained; if
    none of their candidates is clean, the least harmful candidate is selected and named in
    ``diagnostics`` instead of silently hiding or shrinking the annotation.
    """
    per_pt = model_in_per_pt(scale)
    viewport_shape = shapely_box(*viewport.bounds)
    obstacle_shapes = tuple((
        LineString((item.start, item.end)).buffer(
            (item.clearance_pt + LABEL_CLEARANCE_PT) * per_pt)
        if isinstance(item, SegmentObstacle) else shapely_box(*item.bounds), item)
        for item in obstacles)
    placed: list[Placement] = []
    diagnostics: list[LayoutDiagnostic] = []
    targets = [item.target for item in requests if item.target is not None]
    target_x0 = min((item[0] for item in targets), default=viewport.bounds[0])
    target_x1 = max((item[0] for item in targets), default=viewport.bounds[2])

    ordered = sorted(requests, key=lambda item: (-item.priority, item.key))
    for request in ordered:
        candidates = list(request.candidates)
        # Point annotations may fall back to a leadered side column.  The column positions
        # are derived from the final viewport, so ledger and ARCH D resolve independently.
        if request.target is not None and any(item.leader for item in candidates):
            x0, y0, x1, y1 = viewport.bounds
            margin = 10.0 * per_pt
            pitch = 12.0 * per_pt
            width = text_extent(request.text, request.height_pt)[0] * per_pt * 1.08
            left_anchor = max(x0 + margin + width, target_x0 - margin)
            right_anchor = min(x1 - margin - width, target_x1 + margin)
            target_y = min(max(request.target[1], y0 + margin), y1 - margin)
            for step in range(0, 21):
                signed_steps = (0,) if step == 0 else (step, -step)
                for signed_step in signed_steps:
                    y = min(max(target_y + signed_step * pitch, y0 + margin), y1 - margin)
                    candidates.extend((Candidate((left_anchor, y), "right", leader=True),
                                       Candidate((right_anchor, y), "left", leader=True)))
        if not candidates:
            diagnostics.append(LayoutDiagnostic(request.key, "no candidates"))
            continue
        ranked = []
        for index, candidate in enumerate(candidates):
            candidate = _at_scale(candidate, scale)
            polygon = annotation_polygon(candidate, request.text, request.height_pt, scale)
            label_conflicts = tuple(item.request.key for item in placed
                                    if polygon.intersects(Polygon(item.polygon)))
            leader = (LineString((request.target, candidate.at))
                      if candidate.leader and request.target != candidate.at else None)
            leader_crossings = sum(
                1 for item in placed
                if leader is not None and item.candidate.leader
                and item.request.target is not None
                and leader.crosses(LineString((item.request.target, item.candidate.at)))
            )
            hard = (sum(1 for shape, obstacle in obstacle_shapes
                        if obstacle.hard and polygon.intersects(shape))
                    if request.avoid_obstacles else 0)
            soft = (sum(1 for shape, obstacle in obstacle_shapes
                        if not obstacle.hard and polygon.intersects(shape))
                    if request.avoid_obstacles else 0)
            outside = polygon.difference(viewport_shape).area
            distance = math.dist(candidate.at, request.target) if request.target else 0.0
            score = (bool(outside), len(label_conflicts), hard, leader_crossings,
                     soft, distance, index)
            ranked.append((score, candidate, polygon, label_conflicts))
        score, candidate, polygon, conflicts = min(ranked, key=lambda item: item[0])
        placement = Placement(request, candidate,
                              tuple((float(x), float(y)) for x, y in polygon.exterior.coords[:-1]),
                              tuple(float(value) for value in polygon.bounds))
        placed.append(placement)
        reasons = []
        if score[0]:
            reasons.append("outside viewport")
        if score[1]:
            reasons.append("label overlap")
        if score[2]:
            reasons.append("hard-obstacle overlap")
        if reasons:
            conflict_names = list(conflicts)
            if score[2]:
                conflict_names.append("hard obstacle")
            diagnostics.append(LayoutDiagnostic(request.key, ", ".join(reasons),
                                                tuple(conflict_names)))

    original_order = {request.key: index for index, request in enumerate(requests)}
    placed.sort(key=lambda item: original_order[item.request.key])
    return LayoutResult(tuple(placed), tuple(diagnostics))
