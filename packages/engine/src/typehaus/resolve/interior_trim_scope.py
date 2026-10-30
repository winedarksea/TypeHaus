"""What the interior trim pass needs to know before it lays a board (→ interior_trim.py).

Three questions shared by the base and the casing: which ``TrimStandard`` (one, or an
error), which rooms take trim at all, and whether a wall face is a finish face.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from typehaus.findings import Finding, Result, Severity, element_error
from typehaus.model.enums import DoorOperation, LayerFunction
from typehaus.model.millwork import TrimStandard
from typehaus.model.plan import PlanModel
from typehaus.resolve.model import ResolvedModel, ResolvedRoom, ResolvedWall

# How far into a wall the face test probes: inside any finish layer, short of the next.
_FACE_PROBE_M = 0.002


@dataclass(frozen=True)
class TrimScope:
    standard: TrimStandard
    materials: dict
    door_types: dict
    rooms: dict[str, ResolvedRoom]  # the rooms that take trim, by tag
    # Wall bodies and floor planes, each computed once for the whole pass.
    _cache: dict = field(default_factory=dict, compare=False, repr=False)

    @property
    def thickness_m(self) -> float:
        return self.standard.thickness.meters

    def body(self, wall: ResolvedWall):
        from typehaus.resolve.wall_faces import wall_body

        key = ("body", wall.tag)
        if key not in self._cache:
            self._cache[key] = wall_body(wall, wall.z0_m, wall.z1_m)
        return self._cache[key]

    def floors(self, model: ResolvedModel, room: ResolvedRoom) -> tuple[float, float]:
        """``(finished, structural)`` floor elevations of ``room``."""
        from typehaus.resolve.room_floor import (
            room_finished_floor_elevation,
            room_floor_elevation,
        )

        key = ("floor", room.tag)
        if key not in self._cache:
            self._cache[key] = (room_finished_floor_elevation(model, room),
                                room_floor_elevation(model, room))
        return self._cache[key]

    def fixed_footprints(self, plan, model: ResolvedModel, storey: str) -> list:
        """``(tag, plan polygon, z0, z1)`` of the fixed things trim stops at, on ``storey``.

        Casework (a declared ``work_surface``, or any furniture hung on a wall), a fixture
        with a basin body (it needs hot water: a tub, a vanity — not a floor WC, whose
        pedestal the base runs behind) or hung on a wall, and an appliance. The caller tests
        the body's height against the board it is laying.
        """
        from shapely.geometry import Polygon

        from typehaus.model.enums import Service

        key = ("fixed", storey)
        if key in self._cache:
            return self._cache[key]
        furniture = {t.tag: t for t in plan.library.furniture_types}
        fixtures = {t.tag: t for t in plan.library.fixture_types}
        out = []
        for item in model.canvas_objects:
            if item.storey != storey or len(item.footprint) < 3:
                continue
            hung = item.attachment_wall is not None
            if item.kind == "Furniture":
                ftype = furniture.get(item.type_ref or "")
                # A curtain hangs in front of the trim; its envelope is cloth, not casework.
                if ftype is None or ftype.curtain_track is not None or (
                        ftype.work_surface is None and not hung):
                    continue
            elif item.kind == "Fixture":
                ftype = fixtures.get(item.type_ref or "")
                if ftype is None or (Service.WATER_HOT not in ftype.needs and not hung):
                    continue
            elif item.kind != "Appliance":
                continue
            footprint = Polygon(item.footprint)
            if not footprint.is_valid or footprint.is_empty:
                continue
            z0 = item.body_z0_m if item.body_z0_m is not None else item.z_m
            z1 = item.body_z1_m if item.body_z1_m is not None else float("inf")
            out.append((item.tag, footprint, z0, z1))
        self._cache[key] = out
        return out

    def casing_half_width(self, opening, room: str | None = None) -> float | None:
        """Half the width a door takes out of a wall face on a side it is cased.

        ``None`` for a door that takes no applied casing, whose base break is then the
        rough opening (trimless) or the factory frame (a bookcase door), per
        :func:`base_break_half_width`.
        """
        door_type = self.door_types.get(opening.type_ref or "")
        if not cased(door_type) or opening.tag in self.standard.uncased_doors:
            return None
        inner, _head = casing_edges(opening, door_type, self.standard)
        return inner + self.standard.casing_width_for(room, opening.tag).meters

    def base_break_half_width(self, opening, room: str | None = None) -> float | None:
        """Half the base break at a door; ``None`` where the base runs under it (a hatch)."""
        if opening.sill_m >= self.standard.base_height.meters:
            return None
        half = self.casing_half_width(opening, room)
        return opening.width_m / 2.0 if half is None else half


def cased(door_type) -> bool:
    """Whether a door takes applied casing: not trimless, not overhead."""
    if door_type is None:
        return True
    return not (door_type.trimless or door_type.operation == DoorOperation.OVERHEAD)


def casing_edges(opening, door_type, standard: TrimStandard) -> tuple[float, float]:
    """``(inner edge from the opening centre, head bottom above the sill)`` of its casing.

    A site-hung door's casing stands ``jamb_allowance - reveal`` inside the rough opening. A
    bookcase door's laps its face frame by the product's ``casing_lap`` instead.
    """
    product = getattr(door_type, "bookcase_door", None)
    if product is not None:
        lap = product.casing_lap.meters
        return product.body_width.meters / 2.0 - lap, product.body_height.meters - lap
    step = standard.jamb_allowance.meters - standard.reveal.meters
    return opening.width_m / 2.0 - step, opening.height_m - step


def cased_side(door_type, side: int) -> bool:
    """Whether the wall face at ``side`` (+1 = +normal) takes casing: a bookcase only its own."""
    product = getattr(door_type, "bookcase_door", None)
    if product is None:
        return True
    return side == (-1 if product.mounting_face == "negative_normal" else 1)


def trim_scope(plan: PlanModel, model: ResolvedModel) -> tuple[TrimScope | None, list[Finding]]:
    """The house's trim scope, or None (no standard, two standards, or a bad ref)."""
    found = [el for el in plan.all_elements() if isinstance(el, TrimStandard)]
    if not found:
        return None, []
    tags = tuple(sorted(el.tag for el in found))
    if len(found) > 1:
        return None, [Finding(
            severity=Severity.ERROR, check_id="integrity.trim_standard",
            message=f"a house declares at most one TrimStandard; found {len(found)}: "
                    f"{', '.join(tags)}",
            element_tags=tags, result=Result.FAIL)]
    standard = found[0]
    materials = {material.tag: material for material in plan.library.materials}
    missing = [ref for ref in standard.material_refs() if ref not in materials]
    if missing:
        return None, [element_error(
            "integrity.trim_standard",
            f"trim standard {standard.tag} names no material {missing[0]!r}",
            standard.tag)]
    room_tags = {r.tag for r in model.rooms}
    findings = [element_error(
        "integrity.trim_standard",
        f"trim standard {standard.tag} {verb} {tag!r}, which is not a room", standard.tag)
        for verb, tags in (("excludes", standard.excluded_rooms),
                           ("trims", tuple(
                               t for o in standard.room_trims for t in o.rooms)))
        for tag in tags if tag not in room_tags]
    stair_tags = {stair.tag for stair in model.stairs}
    findings += [element_error(
        "integrity.trim_standard",
        f"trim standard {standard.tag} skirts stair {tag!r}, which is not a stair", standard.tag)
        for tag in (standard.stair_skirt.stair_refs if standard.stair_skirt else ())
        if tag not in stair_tags]
    opening_tags = {o.tag for o in model.openings}
    findings += [element_error(
        "integrity.trim_standard",
        f"trim standard {standard.tag} cases door {door!r}, which is not an opening",
        standard.tag)
        for door in (*(d for accent in standard.door_trims for d in accent.doors),
                     *standard.uncased_doors)
        if door not in opening_tags]
    findings += [element_error(
        "integrity.trim_standard",
        f"trim standard {standard.tag} cases a face in {accent.room!r}, which is not a room",
        standard.tag)
        for accent in standard.door_trims
        if accent.room is not None and accent.room not in room_tags]
    excluded = set(standard.excluded_rooms)
    rooms = {room.tag: room for room in model.rooms
             if room.conditioned and room.floor_finish and room.tag not in excluded
             and len(room.clear_face) >= 3}
    return TrimScope(standard=standard, materials=materials,
                     door_types={dt.tag: dt for dt in plan.library.door_types},
                     rooms=rooms), findings


def base_kind(scope: TrimScope, room: ResolvedRoom) -> str:
    """``trim`` / ``tile`` / ``integral_cove`` / ``resilient_base`` / ``none``, off the floor."""
    material = scope.materials.get(room.floor_finish or "")
    detail = getattr(material, "base_detail", None)
    return detail or "trim"


def face_function(wall: ResolvedWall, point: tuple[float, float],
                  into_wall: tuple[float, float], z0: float, z1: float) -> str | None:
    """The layer function at ``wall``'s face at ``point``, over the band ``z0..z1``.

    ``into_wall`` is a unit vector pointing from the room into the wall. The layer whose
    polygon holds a point just behind the face is the face; failing that (a face exactly on
    a polygon edge), the nearest. ``None`` for a layerless wall.
    """
    from shapely.geometry import Point, Polygon

    probe = Point(point[0] + into_wall[0] * _FACE_PROBE_M,
                  point[1] + into_wall[1] * _FACE_PROBE_M)
    best, best_d = None, float("inf")
    for layer in getattr(wall, "layers", ()):
        if layer.is_cavity or len(layer.polygon) < 3:
            continue
        b0, b1 = layer.band(wall)
        if b1 <= z0 or b0 >= z1:
            continue
        polygon = Polygon(layer.polygon)
        if polygon.covers(probe):
            return layer.function
        distance = polygon.distance(probe)
        if distance < best_d:
            best, best_d = layer.function, distance
    return best


def is_finish(function: str | None) -> bool:
    return function == LayerFunction.FINISH.value
