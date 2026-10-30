"""The room decides paint (decision #104): a coating edit on each face a Room bounds.

Applied to a wall's authored stack before it resolves, which moves nothing because a coating
takes no depth (``resolve/coatings.py``). Per stack end, against every Room its face bounds:

* no Room → as authored (an attic hall with no Room keeps what its assembly says);
* every Room ``unpainted`` → the end's coatings are stripped, unless the wall is envelope:
  an exterior wall's room-face paint is its Class III vapour retarder and always stays;
* a used Room (not UNCONDITIONED) on bare gypsum → ``room.paint or DEFAULT_PAINT`` is added;
* an authored coating facing Rooms that agree on ``room.paint`` → swapped to it;
* Rooms on one face that disagree → paint wins, and ``integrity.room_paint_conflict`` warns.

A slotted end row is left as authored. Ceilings, floor-opening linings and the Glaser walk
call :func:`paint_stack_end` with their own room.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from shapely.geometry import Point, Polygon
from shapely.prepared import PreparedGeometry, prep

from typehaus.findings import Finding, Result, Severity
from typehaus.model.assembly import Layer
from typehaus.model.enums import ControlLayer, LayerFunction, Occupancy
from typehaus.quantities import inch
from typehaus.resolve.coatings import coating_tags
from typehaus.resolve.rooms import claimed_room_faces

#: What a used room's bare gypsum is painted with when the room names no paint.
DEFAULT_PAINT = "latex-paint"
#: The added coat's authored film: the library's ``PAINT_FINISH``. It takes no depth.
_PAINT_FILM = inch(0.01)
#: Probe spacing along a face; a short wall still takes three.
_STATION_M = 0.15
#: How far off a face the probe stands, so the room on that side holds it and the room
#: across the wall does not.
FACE_PROBE_M = 0.0254
#: A room counts only where it shares this much height with the wall.
MIN_ROOM_Z_OVERLAP_M = 0.3


@dataclass(frozen=True)
class PaintRoom:
    tag: str
    face: Polygon
    prepared: PreparedGeometry
    z0: float
    z1: float
    used: bool
    unpainted: bool
    paint: str | None


def paint_room(room: Any, face: Polygon, z0: float, z1: float) -> PaintRoom:
    return PaintRoom(room.tag, face, prep(face), z0, z1,
                     room.occupancy != Occupancy.UNCONDITIONED,
                     bool(getattr(room, "unpainted", False)), getattr(room, "paint", None))


def _gypsum(library: Any, layer: Layer) -> bool:
    return getattr(library.material(layer.material_ref), "gypsum_type", None) is not None


def paint_stack_end(stack: list, end: int, rooms: list[PaintRoom], library: Any,
                    envelope: bool) -> tuple[list, bool]:
    """``stack`` with the room rule applied at ``end`` (0 or -1), and whether rooms disagree."""
    if not rooms or not stack or getattr(stack[end], "slot", None) is not None:
        return stack, False
    coatings = coating_tags(library)
    order = stack if end == 0 else stack[::-1]
    depth = next((i for i, layer in enumerate(order) if layer.material_ref not in coatings),
                 len(order))
    painted = [room for room in rooms if not room.unpainted]
    paints = {room.paint for room in painted}
    conflict = (bool(painted) and len(painted) < len(rooms)) or len(paints) > 1
    if not painted:
        if envelope or depth == 0:
            return stack, False
        kept = order[depth:]
    elif depth:
        tag = paints.pop() if len(paints) == 1 else None
        if tag is None or tag == order[0].material_ref:
            return stack, conflict
        kept = [order[0].model_copy(update={"material_ref": tag}), *order[1:]]
    elif depth < len(order) and _gypsum(library, order[0]) and any(r.used for r in painted):
        tag = (paints.pop() if len(paints) == 1 else None) or DEFAULT_PAINT
        coat = Layer(name="room-paint-a" if end == 0 else "room-paint-b", material_ref=tag,
                     thickness=_PAINT_FILM, function=LayerFunction.FINISH,
                     control={ControlLayer.VAPOR})
        kept = [coat, *order]
    else:
        return stack, conflict
    return (list(kept) if end == 0 else list(kept[::-1])), conflict


@dataclass
class RoomPaint:
    """Every claimed Room of the plan, probed by wall faces as the walls resolve."""

    plan: Any
    rooms: list[PaintRoom] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    stripped: set[str] = field(default_factory=set)

    @classmethod
    def of(cls, plan: Any) -> RoomPaint:
        out = cls(plan)
        for storey in plan.storeys:
            z0 = storey.elevation.meters
            z1 = z0 + storey.default_ceiling_height.meters
            for room, face in claimed_room_faces(plan, storey.tag):
                out.rooms.append(paint_room(room, face, z0, z1))
        return out

    def edit_wall(self, wall: Any, stack: list, axis: tuple, sign: float, faces: tuple,
                  z_range: tuple[float, float], envelope: bool) -> list:
        """The wall's stack with both ends painted by the rooms their faces bound.

        ``faces`` are the interior and exterior face offsets along the axis's left normal.
        """
        for end, offset, away in ((0, faces[0], -sign), (-1, faces[1], sign)):
            rooms = self._rooms_facing(axis, offset + away * FACE_PROBE_M, z_range)
            before = [layer.material_ref for layer in stack]
            stack, conflict = paint_stack_end(stack, end, rooms, self.plan.library, envelope)
            if len(stack) < len(before):
                self.stripped.add(wall.tag)
            if conflict:
                self.findings.append(conflict_finding(wall.tag, rooms))
        return stack

    def _rooms_facing(self, axis: tuple, offset: float,
                      z_range: tuple[float, float]) -> list[PaintRoom]:
        (x0, y0), (x1, y1) = axis
        run = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        if run <= 0.0:
            return []
        dx, dy = (x1 - x0) / run, (y1 - y0) / run
        nx, ny = -dy, dx
        pad = abs(offset) + FACE_PROBE_M
        box = (min(x0, x1) - pad, min(y0, y1) - pad, max(x0, x1) + pad, max(y0, y1) + pad)
        near = [room for room in self.rooms
                if min(z_range[1], room.z1) - max(z_range[0], room.z0) > MIN_ROOM_Z_OVERLAP_M
                and room.face.bounds[0] <= box[2] and room.face.bounds[2] >= box[0]
                and room.face.bounds[1] <= box[3] and room.face.bounds[3] >= box[1]]
        if not near:
            return []
        count = max(3, int(run / _STATION_M))
        hit: dict[str, PaintRoom] = {}
        for i in range(count):
            t = (i + 0.5) / count * run
            probe = Point(x0 + dx * t + nx * offset, y0 + dy * t + ny * offset)
            for room in near:
                if room.tag not in hit and room.prepared.contains(probe):
                    hit[room.tag] = room
        return [hit[tag] for tag in sorted(hit)]

    def envelope_findings(self, model: Any) -> list[Finding]:
        """A stripped face on a wall the derived envelope calls envelope: the proxy was wrong."""
        if not self.stripped:
            return []
        from typehaus.resolve.envelope_geometry import envelope_geometry

        envelope = envelope_geometry(model)
        return [Finding(
            severity=Severity.WARN, check_id="integrity.room_paint_envelope",
            message=f"wall {wall.tag}: an unpainted room stripped its paint, but the derived "
                    "envelope counts it as an exterior wall, whose room-face paint is its "
                    "vapour retarder",
            element_tags=(wall.tag,), result=Result.FAIL,
            fix_hint="give the wall an assembly with a CLADDING layer, or paint the room",
        ) for wall in model.walls
            if wall.tag in self.stripped and envelope.is_envelope_wall(wall)]


def conflict_finding(element_tag: str, rooms: list[PaintRoom]) -> Finding:
    return Finding(
        severity=Severity.WARN, check_id="integrity.room_paint_conflict",
        message=f"{element_tag}: one face bounds rooms {', '.join(r.tag for r in rooms)}, "
                "which disagree about paint — it is painted",
        element_tags=(element_tag, *(r.tag for r in rooms)), result=Result.UNKNOWN,
        fix_hint="split the face with a node, or give the rooms the same paint/unpainted",
    )


def lining_coating(plan: Any, storey_tag: str, lining: tuple, centre: tuple[float, float],
                   ) -> str | None:
    """The coating a ``FloorOpening.lining``'s well face resolves to, or None.

    The well is faced by the rooms holding its centre on its own storey and the one below.
    """
    if not lining:
        return None
    ordered = sorted(plan.storeys, key=lambda s: s.elevation.meters)
    index = next((i for i, s in enumerate(ordered) if s.tag == storey_tag), None)
    tags = {s.tag for s in ordered[max(0, (index or 0) - 1):(index or 0) + 1]}
    rooms = [paint_room(room, face, 0.0, 0.0)
             for tag in sorted(tags) for room, face in claimed_room_faces(plan, tag)
             if face.contains(Point(centre))]
    face = paint_stack_end(list(lining), 0, rooms, plan.library, envelope=False)[0]
    return face[0].material_ref if face and face[0].material_ref in coating_tags(
        plan.library) else None
