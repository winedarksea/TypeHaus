"""A detail's lettering as ONE obstacle set (C5 escalated #1, option (a)).

Dimension strings, the caption and notes under the drawing, keyed bubbles and any leader
that lands on a ladder were each placed by their own family and never dodged against one
another. Here they go through :func:`annotation_layout.resolve_annotations` in priority
order, every earlier placement an obstacle for the next. Ladder columns keep their order
and stay put: they are the fixed set everything else moves around.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from shapely.geometry import LineString
from shapely.geometry import box as shapely_box

from typehaus.emit.draw.annotate import leader_box, model_in_per_pt, text_extent
from typehaus.emit.draw.annotation_layout import (
    AnnotationRequest,
    BoxObstacle,
    Candidate,
    SegmentObstacle,
    Viewport,
    resolve_annotations,
)
from typehaus.emit.draw.annotation_layout_config import COLUMN_PITCH_PT
from typehaus.emit.draw.scene import ArchDimension, Frame, Leader, Polyline, Scene, Text

#: uid prefix marking a caption or a note printed under the drawing as movable.
CAPTION_UID = "layout-caption:"
_STEPS = 12
#: Bubble stand-offs (radii) and bearings (degrees) tried around the bubble's target.
_BUBBLE_RADII = (2.2, 3.4, 4.6, 6.0, 7.5, 9.0)
_BUBBLE_BEARINGS = (0, 30, -30, 60, -60, 180, 150, -150, 120, -120, 90, -90)


@dataclass(frozen=True)
class DetailLayoutRequest:
    """Asks ``annotation_scene`` to run :func:`layout_detail` once the frame is known."""

    key: str = "detail-layout"


def as_captions(nodes: list) -> list:
    """Mark every ``Text`` in ``nodes`` (notes under the drawing) as movable."""
    return [n.model_copy(update={"uid": f"{CAPTION_UID}{i}"}) if isinstance(n, Text) else n
            for i, n in enumerate(nodes)]


def _dim_label(node: ArchDimension) -> str:
    from typehaus.emit.draw.plan_labels import feet_inches

    return node.text or feet_inches(math.dist(node.p0, node.p1))


def _vertical(node: ArchDimension) -> bool:
    return abs(node.p1[0] - node.p0[0]) < abs(node.p1[1] - node.p0[1])


def _dim_geometry(node: ArchDimension, offset: float, along: float, per_pt: float):
    """``(text centre, rotation, line)`` as ``pdf_writer._draw_dimension`` prints it."""
    from typehaus.emit.draw.annotate import DODGE_GAP_PT

    gap = DODGE_GAP_PT * per_pt
    half = text_extent(_dim_label(node), node.height_pt)[1] * per_pt / 2.0
    if _vertical(node):
        x = node.p0[0] + offset
        z = (node.p0[1] + node.p1[1]) / 2.0 + along
        return (x - gap - half, z), 90.0, ((x, node.p0[1]), (x, node.p1[1]))
    y = node.p0[1] + offset
    u = (node.p0[0] + node.p1[0]) / 2.0 + along
    return (u, y + gap + half), 0.0, ((node.p0[0], y), (node.p1[0], y))


def _dim_options(node: ArchDimension, per_pt: float) -> list[tuple[float, float]]:
    """``(offset, text_along)`` tries: as authored, slid along, outside the ends, stepped off."""
    width = text_extent(_dim_label(node), node.height_pt)[0] * per_pt
    length = math.dist(node.p0, node.p1)
    clear = length / 2.0 + width / 2.0 + 2.0 * per_pt
    alongs = [node.text_along, node.text_along + width * 0.6, node.text_along - width * 0.6,
              clear, -clear, clear + width, -(clear + width)]
    pitch = COLUMN_PITCH_PT * per_pt
    offsets = [node.offset, node.offset - pitch, node.offset + pitch,
               node.offset - 2 * pitch, node.offset + 2 * pitch]
    return list(dict.fromkeys((o, a) for o in offsets for a in alongs))


def _crosses_any(start, end, boxes) -> bool:
    line = LineString((start, end))
    return any(line.intersects(shapely_box(*b).buffer(-1e-6)) for b in boxes)


def _bubbles(scene: Scene) -> dict:
    """``{key: [text node, leader, outline ids]}`` for every keyed bubble with its leader."""
    from typehaus.emit.draw.keyed_notes import KEY_LAYER

    found = {node.content: [node, None, set()] for node in scene.nodes
             if isinstance(node, Text) and node.layer == KEY_LAYER}
    for node in scene.nodes:
        for text, _leader, ids in found.values():
            if (isinstance(node, Polyline) and node.layer == KEY_LAYER and node.points
                    and math.dist(_mean(node.points), text.anchor) < 1e-3):
                ids.add(id(node))
            elif (isinstance(node, Leader) and not node.text
                  and math.dist(node.at, text.anchor) < 1e-3):
                found[text.content][1] = node
    return {key: entry for key, entry in found.items() if entry[1] is not None}


def _mean(points) -> tuple[float, float]:
    return (sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points))


def _movable_leaders(leaders: list[Leader], scale: float) -> set[int]:
    """Leaders that overprint a label in a longer column — the ladder stays, they move."""
    def column(node):
        return (round(node.at[0], 3), node.at[0] < node.to[0])

    size: dict = {}
    for node in leaders:
        size[column(node)] = size.get(column(node), 0) + 1
    boxes = [(node, shapely_box(*leader_box(node, scale))) for node in leaders]
    out: set[int] = set()
    for node, shape in boxes:
        for other, other_shape in boxes:
            if (other is not node and size[column(other)] > size[column(node)]
                    and shape.intersects(other_shape)):
                out.add(id(node))
                break
    return out


def _model_viewport(frame: Frame) -> Viewport:
    """The drawing window, run down to the paper margin: the notes under a drawing print
    there on a sheet, whose bands are not the card's (paper nodes are dropped)."""
    from typehaus.emit.draw.annotation_scene import _model_viewport
    from typehaus.emit.draw.detail_card import MARGIN_IN

    x0, y0, x1, y1 = _model_viewport(frame).bounds
    below = max(0.0, frame.viewport[1] - MARGIN_IN) * 12.0 / frame.scale
    return Viewport((x0, y0 - below, x1, y1))


def layout_detail(scene: Scene, frame: Frame) -> Scene:
    """Re-place the movable lettering of one detail at ``frame``'s printed scale."""
    if frame is None:
        return scene
    from typehaus.emit.draw.keyed_notes import bubble_nodes, bubble_radius_in

    scale = frame.scale
    per_pt = model_in_per_pt(scale)
    pitch = COLUMN_PITCH_PT * per_pt
    viewport = _model_viewport(frame)
    model = [n for n in scene.nodes if getattr(n, "space", "model") == "model"]
    bubbles = _bubbles(scene)
    bubble_texts = {id(entry[0]) for entry in bubbles.values()}
    bubble_ink = set().union(*(entry[2] for entry in bubbles.values()))
    leaders = [n for n in model if isinstance(n, Leader) and n.text]
    movable = _movable_leaders(leaders, scale)
    captions = [n for n in model if isinstance(n, Text)
                and (n.uid or "").startswith(CAPTION_UID)]
    dims = [n for n in model if isinstance(n, ArchDimension)]

    fixed_boxes: list = [leader_box(n, scale) for n in leaders if id(n) not in movable]
    fixed_lines = [(n.at, n.to) for n in leaders if id(n) not in movable]
    fixed_boxes += [leader_box(n, scale) for n in model
                    if isinstance(n, Text) and id(n) not in bubble_texts
                    and not (n.uid or "").startswith(CAPTION_UID)]

    def run(requests, soft=()):
        obstacles = ([BoxObstacle(tuple(b)) for b in fixed_boxes]
                     + [SegmentObstacle(a, b) for a, b in fixed_lines] + list(soft))
        result = resolve_annotations(requests, viewport, tuple(obstacles), scale)
        return {p.request.key: p for p in result.placements}

    replace: dict[int, list] = {}

    # 1. Dimension strings, each kept on its own line.
    options: dict = {}
    requests = []
    for index, node in enumerate(dims):
        key = f"dim:{index}"
        tries = _dim_options(node, per_pt)
        cands = []
        for offset, along in tries:
            at, rotation, _line = _dim_geometry(node, offset, along, per_pt)
            options[(key, round(at[0], 6), round(at[1], 6))] = (offset, along)
            cands.append(Candidate(at, "center", rotation))
        requests.append(AnnotationRequest(key, _dim_label(node), cands[0].at, tuple(cands),
                                          height_pt=node.height_pt, priority=30))
    placements = run(requests) if requests else {}
    for index, node in enumerate(dims):
        placed = placements[f"dim:{index}"]
        at = placed.candidate.at
        offset, along = options[(f"dim:{index}", round(at[0], 6), round(at[1], 6))]
        new = node.model_copy(update={"offset": offset, "text_along": along})
        replace[id(node)] = [new]
        fixed_boxes.append(placed.box)
        fixed_lines.append(_dim_geometry(new, offset, along, per_pt)[2])

    # 2. A leader that overprints a ladder slides up or down its own column.
    requests = []
    for node in leaders:
        if id(node) not in movable:
            continue
        cands = [Candidate(node.at, "right" if node.at[0] < node.to[0] else "left")]
        for step in range(1, _STEPS + 1):
            for sign in (-1, 1):
                at = (node.at[0], node.at[1] + sign * step * pitch)
                if not _crosses_any(at, node.to, fixed_boxes):
                    cands.append(Candidate(at, cands[0].align))
        requests.append(AnnotationRequest(f"leader:{id(node)}", node.text, node.at,
                                          tuple(cands), height_pt=node.height_pt or 7.0,
                                          priority=20))
    for placed in run(requests).values() if requests else ():
        node = next(n for n in leaders if f"leader:{id(n)}" == placed.request.key)
        replace[id(node)] = [node.model_copy(update={"at": placed.candidate.at})]
        fixed_boxes.append(placed.box)
        fixed_lines.append((placed.candidate.at, node.to))

    # Heavy linework: a soft obstacle, so a caption or bubble prefers air to the drawing.
    ink = [SegmentObstacle(a, b, hard=False) for n in model
           if isinstance(n, Polyline) and n.lineweight >= 0.35 and id(n) not in bubble_ink
           for a, b in zip(n.points, (*n.points[1:], n.points[0]) if n.closed
                           else n.points[1:], strict=False)]

    # 3. The caption and notes under the drawing step down clear, top one first.
    requests = []
    for index, node in enumerate(sorted(captions, key=lambda n: -n.anchor[1])):
        cands = [Candidate((node.anchor[0], node.anchor[1] - step * pitch), node.align)
                 for step in range(_STEPS + 1)]
        cands += [Candidate((node.anchor[0], node.anchor[1] + step * pitch), node.align)
                  for step in (1, 2)]
        requests.append(AnnotationRequest(node.uid, node.content, node.anchor, tuple(cands),
                                          height_pt=node.height_pt or 7.0,
                                          priority=10 - index))
    for placed in run(requests, soft=ink).values() if requests else ():
        node = next(n for n in captions if n.uid == placed.request.key)
        replace[id(node)] = [node.model_copy(update={"anchor": placed.candidate.at})]
        fixed_boxes.append(placed.box)

    # 4. Bubbles last, one at a time around their own target: off the linework where they
    #    can be, never with a leader across a label or an earlier bubble.
    radius = bubble_radius_in(scale)
    side_pt = 2.0 * radius / per_pt + 2.0  # the outline and some air
    for key, (text, leader, outline) in sorted(bubbles.items()):
        target = leader.to
        cands = [Candidate(text.anchor, "center")]
        for reach in _BUBBLE_RADII:
            for bearing in _BUBBLE_BEARINGS:
                angle = math.radians(bearing)
                cands.append(Candidate((target[0] + reach * radius * math.cos(angle),
                                        target[1] + reach * radius * math.sin(angle)),
                                       "center"))
        clean = [c for c in cands if not _crosses_any(target, c.at, fixed_boxes)]
        request = AnnotationRequest(f"bubble:{key}", key, target, tuple(clean or cands),
                                    extent_pt=(side_pt, side_pt))
        placed = run([request], ink)[request.key]
        at = placed.candidate.at
        replace[id(text)] = bubble_nodes(key, at, scale)
        replace[id(leader)] = [leader.model_copy(update={"at": at})]
        for node_id in outline:
            replace[node_id] = []
        fixed_boxes.append(placed.box)
        fixed_lines.append((target, at))

    nodes: list = []
    for node in scene.nodes:
        nodes.extend(replace.get(id(node), [node]))
    return scene.model_copy(update={"nodes": tuple(nodes)})
