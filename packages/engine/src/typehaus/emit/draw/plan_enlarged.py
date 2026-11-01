"""Enlarged plans (NCS 4 series): the level plan cropped to a room group at 1/2" (C7-E8).

The baths and the mechanical rooms are where the plans overprint at 3/32": fixtures,
plenums and labels inches apart. An enlarged plan is the same drawing as the floor plan
(``build_floorplan``), framed on a crop at ``ENLARGED_PLAN_SCALE`` the way
``detail_enlarged`` crops an opening detail. Rooms are chosen by ``Room.occupancy`` and
grouped per level so that each group fits the viewport at that scale.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

from shapely.geometry import Polygon

from typehaus.emit.draw._shared import PLAN_RESERVATION_SCALE
from typehaus.emit.draw.datum import model_at_level
from typehaus.emit.draw.floorplan import build_floorplan
from typehaus.emit.draw.plan_marks import BUBBLE_RADIUS_IN, MARK_LAYER
from typehaus.emit.draw.scene import (
    ArchDimension,
    Frame,
    Hatch,
    Leader,
    Polyline,
    Scene,
    Symbol,
    Text,
)
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel

ENLARGED_PLAN_SCALE = (0.5, "1/2\" = 1'-0\"")

#: Air around a room group, model inches: the walls round it and their tags.
_MARGIN_IN = 12.0

Box = tuple[float, float, float, float]
Build = Callable[[ResolvedModel, str], Scene]


@dataclass(frozen=True)
class RoomGroup:
    """Rooms on one level drawn as one enlarged plan; ``box`` is model inches."""

    level: str
    rooms: tuple[str, ...]
    box: Box


def enlarged_groups(model: ResolvedModel, occupancies: frozenset[str],
                    paper: tuple[float, float]) -> list[RoomGroup]:
    """Rooms of ``occupancies``, grouped per level, first-fit into the 1/2" viewport."""
    from typehaus.emit.draw.sheet_writer import viewport_box

    _x, _y, width, height = viewport_box(paper)
    span = (width * 12.0 / ENLARGED_PLAN_SCALE[0], height * 12.0 / ENLARGED_PLAN_SCALE[0])
    groups: list[RoomGroup] = []
    for primary, here in model.plan.levels():
        storeys = {storey.tag for storey in here}
        found: list[RoomGroup] = []
        for room in model.rooms:
            if room.storey not in storeys or _occupancy(room) not in occupancies:
                continue
            box = _room_box(room)
            if box is None:
                continue
            for index, group in enumerate(found):
                merged = _union(group.box, box)
                if _fits(merged, span):
                    found[index] = RoomGroup(primary.tag, (*group.rooms, room.tag), merged)
                    break
            else:
                found.append(RoomGroup(primary.tag, (room.tag,), box))
        groups += found
    return groups


def enlarged_plan_scene(model: ResolvedModel, group: RoomGroup,
                        paper: tuple[float, float], build: Build | None = None) -> Scene:
    """The level plan cropped to ``group`` and framed at ``ENLARGED_PLAN_SCALE``.

    ``build(level_model, level)`` is the plan being enlarged: the floor plan by default,
    the HVAC plan for a mechanical room (its equipment and ducts are what overprint).
    """
    from typehaus.emit.draw.sheet_writer import viewport_box

    scale, label = ENLARGED_PLAN_SCALE
    level = model_at_level(model, group.level)
    scene = (build(level, group.level) if build is not None
             else build_floorplan(level, group.level, dimension_scale=scale))
    u0, z0, u1, z1 = group.box
    crop = (u0 - _MARGIN_IN, z0 - _MARGIN_IN, u1 + _MARGIN_IN, z1 + _MARGIN_IN)
    nodes = tuple(_rescale_bubble(node, PLAN_RESERVATION_SCALE / scale)
                  for node in scene.nodes if _inside(node, crop))
    kept_uids = {getattr(node, "uid", None) for node in nodes}
    requests = tuple(req for req in scene.annotation_requests
                     if getattr(req, "uid", None) in kept_uids
                     or _point_in(getattr(req, "target", None), crop))
    frame = Frame(paper=paper, viewport=viewport_box(paper, notes_panel=bool(scene.notes)),
                  center=((crop[0] + crop[2]) / 2.0, (crop[1] + crop[3]) / 2.0),
                  scale=scale, scale_label=label)
    return scene.model_copy(update={"nodes": nodes, "annotation_requests": requests,
                                    "frame": frame})


def enlarged_plan_sheet(model: ResolvedModel, group: RoomGroup,
                        build: Build | None = None) -> Scene:
    """The A-4xx ``SceneFn``: :func:`enlarged_plan_scene` on the set's paper."""
    from typehaus.emit.draw.sheet_writer import current_paper

    return enlarged_plan_scene(model, group, current_paper(), build)


def enlarged_title(kind: str, group: RoomGroup) -> str:
    return f"Enlarged {kind} plan — {group.level}: {', '.join(group.rooms)}"


def _rescale_bubble(node, factor: float):
    """A mark bubble is model inches sized for the plan scale; keep its paper size here."""
    if not (isinstance(node, Polyline) and node.closed and node.layer == MARK_LAYER):
        return node
    cx = sum(p[0] for p in node.points) / len(node.points)
    cy = sum(p[1] for p in node.points) / len(node.points)
    if any(abs(math.hypot(p[0] - cx, p[1] - cy) - BUBBLE_RADIUS_IN) > 0.05 * BUBBLE_RADIUS_IN
           for p in node.points):
        return node
    return node.model_copy(update={"points": tuple(
        (cx + (p[0] - cx) * factor, cy + (p[1] - cy) * factor) for p in node.points)})


def _occupancy(room) -> str:
    occupancy = getattr(room, "occupancy", None)
    return str(getattr(occupancy, "value", occupancy) or "")


def _room_box(room) -> Box | None:
    if not room.clear_face or len(room.clear_face) < 3:
        return None
    x0, y0, x1, y1 = Polygon(room.clear_face).bounds
    return (x0 / M_PER_IN, y0 / M_PER_IN, x1 / M_PER_IN, y1 / M_PER_IN)


def _union(a: Box, b: Box) -> Box:
    return (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))


def _fits(box: Box, span: tuple[float, float]) -> bool:
    return (box[2] - box[0] + 2 * _MARGIN_IN <= span[0]
            and box[3] - box[1] + 2 * _MARGIN_IN <= span[1])


def _point_in(point, box: Box) -> bool:
    return (point is not None and box[0] <= point[0] <= box[2]
            and box[1] <= point[1] <= box[3])


def _points(node) -> list:
    if isinstance(node, Polyline):
        return list(node.points)
    if isinstance(node, Hatch):
        return list(node.boundary)
    if isinstance(node, Text):
        return [node.anchor]
    if isinstance(node, ArchDimension):
        return [node.p0, node.p1]
    if isinstance(node, Leader):
        return [node.at, node.to]
    if isinstance(node, Symbol):
        return [node.insert]
    return []


def _inside(node, box: Box) -> bool:
    """A node whose extent meets the crop; text and symbols only when their anchor is in."""
    points = _points(node)
    if not points:
        return False
    if isinstance(node, (Text, Symbol, Leader, ArchDimension)):
        return all(_point_in(point, box) for point in points)
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return not (max(xs) < box[0] or min(xs) > box[2] or max(ys) < box[1] or min(ys) > box[3])
