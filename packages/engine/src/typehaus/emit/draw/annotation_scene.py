"""Apply scale-aware annotation requests to immutable drawing scenes."""

from __future__ import annotations

from typehaus.emit.draw.annotation_layout import (
    AnnotationRequest,
    BoxObstacle,
    Candidate,
    SegmentObstacle,
    Viewport,
    annotation_polygon,
    resolve_annotations,
)
from typehaus.emit.draw.annotation_layout_config import HARD_OBSTACLE_CLEARANCE_PT
from typehaus.emit.draw.scene import ArchDimension, Frame, Leader, NamedPoint, Polyline, Scene, Text


def _model_viewport(frame: Frame) -> Viewport:
    width = frame.viewport[2] * 12.0 / frame.scale
    height = frame.viewport[3] * 12.0 / frame.scale
    cx, cy = frame.center
    return Viewport((cx - width / 2.0, cy - height / 2.0,
                     cx + width / 2.0, cy + height / 2.0))


def _obstacles(scene: Scene, request_uids: set[str], frame: Frame,
               ) -> tuple[SegmentObstacle | BoxObstacle, ...]:
    out: list[SegmentObstacle | BoxObstacle] = []
    table_bounds = []
    for node in scene.nodes:
        if getattr(node, "uid", None) in request_uids:
            continue
        if isinstance(node, Polyline):
            points = list(node.points)
            if node.closed and points:
                points.append(points[0])
            out.extend(SegmentObstacle(start, end, HARD_OBSTACLE_CLEARANCE_PT,
                                       hard=node.lineweight >= 0.35)
                       for start, end in zip(points, points[1:], strict=False))
        elif isinstance(node, ArchDimension):
            out.append(SegmentObstacle(node.p0, node.p1, HARD_OBSTACLE_CLEARANCE_PT, True))
        elif isinstance(node, Text) and node.space == "model":
            height_pt = node.height_pt or node.height / (12.0 / frame.scale / 72.0)
            bounds = annotation_polygon(Candidate(node.anchor, node.align, node.rotation),
                                        node.content, height_pt, frame.scale).bounds
            obstacle = BoxObstacle(tuple(float(value) for value in bounds), True)
            out.append(obstacle)
            if node.layer == "C-ANNO-TABL":
                table_bounds.append(bounds)
    if table_bounds:
        out.append(BoxObstacle((min(item[0] for item in table_bounds),
                                min(item[1] for item in table_bounds),
                                max(item[2] for item in table_bounds),
                                max(item[3] for item in table_bounds)), True))
    return tuple(out)


def resolve_scene_annotations(scene: Scene, frame: Frame) -> Scene:
    """Resolve requests once at the chosen sheet scale and replace their seed text nodes."""
    requests = tuple(item for item in scene.annotation_requests
                     if isinstance(item, AnnotationRequest))
    if not requests:
        return scene
    request_uids = {item.uid for item in requests if item.uid is not None}
    result = resolve_annotations(requests, _model_viewport(frame),
                                 _obstacles(scene, request_uids, frame), frame.scale)
    placements = {item.request.uid: item for item in result.placements
                  if item.request.uid is not None}
    nodes = []
    for node in scene.nodes:
        uid = getattr(node, "uid", None)
        placed = placements.get(uid)
        if placed is None:
            nodes.append(node)
            continue
        request, candidate = placed.request, placed.candidate
        if candidate.leader and request.target is not None:
            nodes.append(Leader(anchor=NamedPoint(xy=request.target, name=request.key),
                                at=candidate.at, to=request.target, text=request.text,
                                height_pt=request.height_pt, layer=request.layer, uid=request.uid))
        else:
            nodes.append(Text(anchor=candidate.at, content=request.text,
                              height_pt=request.height_pt, rotation=candidate.rotation,
                              layer=request.layer, align=candidate.align, uid=request.uid))
    return scene.model_copy(update={"nodes": tuple(nodes), "frame": frame,
                                    "annotation_diagnostics": result.diagnostics})
