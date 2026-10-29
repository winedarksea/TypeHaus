"""The floor build-up at a door, read from the plan before rooms resolve.

A derived RO height starts from the finished floor (``resolve/door_sizing``), but openings
resolve before rooms and floors, because framing needs their heights. So this reads the
same three sources ``rooms._finish_zones`` does, off the plan alone: an authored finish
zone, a ``Slab`` carrying its own ``floor_finish``, then the room's field finish. The room
is found by its seed in the wall-axis face, as ``resolve_rooms`` claims it. An unstated
covering depth counts as zero (``advisory.floor_finish_depth`` reports it).
"""
from __future__ import annotations

from shapely.geometry import Point, Polygon

from typehaus.resolve.door_sizing import CASED_DOOR_DEFAULTS, DoorSizing, door_sizing

_IN = 0.0254


class DoorFloorFinish:
    """Per-resolve cache of storey faces and their rooms."""

    def __init__(self, plan):
        self._plan = plan
        self._faces: dict[str, list[tuple[Polygon, object | None]]] = {}
        self._depths = {material.tag: material for material in plan.library.materials}

    def at_opening(self, wall, center_along_m: float, sill_m: float) -> float:
        """Metres of finish over the subfloor, the higher side; 0 for a raised sill."""
        if sill_m > CASED_DOOR_DEFAULTS.raised_sill_m:
            return 0.0
        (sx, sy), (ex, ey) = wall.axis
        run = ((ex - sx) ** 2 + (ey - sy) ** 2) ** 0.5 or 1.0
        ux, uy = (ex - sx) / run, (ey - sy) / run
        cx, cy = sx + ux * center_along_m, sy + uy * center_along_m
        reach = wall.thickness_m / 2 + CASED_DOOR_DEFAULTS.room_probe_m
        return max(self._finish_at(wall.storey, (cx - uy * side * reach, cy + ux * side * reach))
                   for side in (-1, 1))

    def _finish_at(self, storey: str, point: tuple[float, float]) -> float:
        probe = Point(point)
        room = next((room for face, room in self._storey(storey) if face.covers(probe)), None)
        if room is None:
            return 0.0
        for zone in room.finish_zones:
            outline = Polygon([p.xy_m for p in zone.outline])
            if outline.is_valid and outline.covers(probe):
                return self._depth(zone.material_ref)
        for slab in self._plan.storey_elements(storey):
            if slab.element_kind == "Slab" and getattr(slab, "floor_finish", None):
                outline = Polygon([p.xy_m for p in slab.outline])
                if outline.is_valid and outline.covers(probe):
                    return self._depth(slab.floor_finish)
        return self._depth(room.floor_finish)

    def _depth(self, ref: str | None) -> float:
        material = self._depths.get(ref) if ref else None
        if material is None or material.finish_thickness_in is None:
            return 0.0
        return material.finish_thickness_in * _IN

    def _storey(self, storey: str):
        if storey not in self._faces:
            from typehaus.resolve.rooms import _storey_faces

            rooms = [e for e in self._plan.storey_elements(storey) if e.element_kind == "Room"]
            faces = []
            for face in _storey_faces(self._plan, storey):
                room = next((r for r in rooms if face.contains(Point(r.seed.xy_m))), None)
                faces.append((face, room))
            self._faces[storey] = faces
        return self._faces[storey]


def trim_standard_of(plan):
    """The house's one ``TrimStandard``, or None (none, or ambiguous)."""
    from typehaus.model.millwork import TrimStandard

    standards = [item for item in plan.all_elements() if isinstance(item, TrimStandard)]
    return standards[0] if len(standards) == 1 else None


def size_door(plan, el, wall, standard, finishes: DoorFloorFinish, sill_m: float,
              center_of) -> DoorSizing | None:
    """``door_sizing`` for a typed ``Door``; None for anything else. ``center_of(width)``
    places the opening along its wall."""
    from typehaus.hardware.catalog import pocket_frame_kit
    from typehaus.model.enums import DoorOperation
    from typehaus.resolve.framing.tables import pocket_wall_is_deep

    if el.element_kind != "Door":
        return None
    door_type = next((x for x in plan.library.door_types if x.tag == el.type_ref), None)
    if door_type is None:
        return None
    kit = None
    if door_type.operation == DoorOperation.POCKET and door_type.pocket_frame:
        # A family with no kit at this width raises in the takeoff; frame it at 2W + 1".
        try:
            kit = pocket_frame_kit(door_type.pocket_frame, round(door_type.width.inches),
                                   pocket_wall_is_deep(getattr(wall, "layers", ())))
        except LookupError:
            kit = None
    # The finish is probed at the opening's centre, which needs its width; the width never
    # depends on the finish.
    probe = door_sizing(el, door_type, standard, kit, 0.0)
    finish = finishes.at_opening(wall, center_of(probe.passage_w_m), sill_m)
    return door_sizing(el, door_type, standard, kit, finish)
