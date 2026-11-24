"""``advisory.luminaire_placement``: where a ceiling luminaire stands against its surroundings.

House preference, never code, never FAIL. Four rules, each derived from the resolved model:

1. **Over a tall body.** The footprint is over a cabinet, appliance or machine whose top is
   higher than ``luminaire_body_clear_height_in`` above its floor and below the fixture.
2. **Too close to a tall face.** A recessed can or pendant within
   ``luminaire_tall_face_setback_in`` of a body taller than ``luminaire_tall_body_height_in``.
3. **A hung service under a surface fixture.** A duct, pipe, conduit or machine crossing its
   footprint within ``luminaire_service_band_in`` below it.
4. **Garage door.** In an overhead door's open-panel zone, or within
   ``luminaire_opener_clearance_in`` of the opener's rail line. Both are derived.

What counts as a body: an Appliance or Equipment, or Furniture whose type is ``storage`` or a
``work_surface`` (casework, bookcases, desks). Beds, seating, mirrors, art, towel bars, plants,
curtain tracks and blinds are neither, so no tag or name list is needed; plumbing Fixtures are
never bodies (a can over a shower or vanity is the point). An appliance standing on another
body (a kettle on a counter) is judged by what it stands on.

Recognising an opener: its type's placeable symbol is in ``GARAGE_OPENER_SYMBOLS``. The rail
runs from the opener's resolved position to the door's header at its centre.

Ceiling runs (``LightRun``) are those in a gypsum reveal or within 6" of the finished ceiling;
a wall, under-cabinet or exterior run is not graded. A ceiling run within 6" of its room's wall
face washes that wall, so rule 1 does not hold what stands against it.
"""

from __future__ import annotations

from dataclasses import dataclass

from shapely.geometry import LineString, Point, Polygon

from typehaus.checks._authoring import advisory
from typehaus.checks._authoring import not_applicable as _na
from typehaus.checks._authoring import passed as _pass
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.electrical import luminaire_types
from typehaus.model.enums import DoorOperation, LuminaireForm
from typehaus.model.placeable_symbols.appliances import GARAGE_OPENER_SYMBOLS
from typehaus.resolve.ceilings import ceiling_faces, finished_ceiling_at
from typehaus.resolve.geometry import wall_frame
from typehaus.resolve.geometry_door_products import finish_faces
from typehaus.resolve.room_floor import room_finished_floor_elevation
from typehaus.resolve.room_lookup import opening_rooms

CID = "advisory.luminaire_placement"
_IN = 0.0254
#: Forms that hang on or in a ceiling; a sconce, wall lamp, mirror light or tape does not.
_CEILING_FORMS = frozenset(LuminaireForm) - {
    LuminaireForm.SCONCE, LuminaireForm.WALL_LAMP, LuminaireForm.MIRROR_LIGHT,
    LuminaireForm.STRIP}
_DOWNLIGHT_FORMS = frozenset({LuminaireForm.RECESSED_CAN, LuminaireForm.PENDANT})
_BODY_KINDS = frozenset({"Furniture", "Appliance", "Equipment"})
_LEVEL_TOL_M = _IN
_MIN_OVERLAP_M2 = 1e-4
#: A run counts as ceiling-mounted within this of the finished ceiling (or in a reveal).
_RUN_CEILING_BAND_M = 6 * _IN
_RUN_HALF_WIDTH_M = 0.015
#: A ceiling run this near its room's wall face is a perimeter wash (rule 1 skips it).
_PERIMETER_M = 6 * _IN
#: A face is at least this tall: a closet shelf or a rod is a board, not a face to scallop.
_MIN_FACE_HEIGHT_M = 12 * _IN


@dataclass(frozen=True)
class _Fixture:
    tag: str
    shape: Polygon
    point: tuple[float, float]
    z0: float  # lowest point
    z1: float
    storey: str
    room: str | None
    downlight: bool
    surface: bool  # not recessed into its host
    perimeter: bool = False  # a run along a wall: it washes what stands against it


@dataclass(frozen=True)
class _Body:
    tag: str
    shape: Polygon
    z0: float
    z1: float
    storey: str
    room: str | None
    kind: str


def _fixtures(ctx: CheckContext) -> list[_Fixture]:
    types = luminaire_types(ctx.plan.library)
    out: list[_Fixture] = []
    for obj in ctx.model.canvas_objects:
        product = types.get(obj.type_ref or "")
        if (product is None or product.form not in _CEILING_FORMS or obj.mount is None
                or obj.mount.kind.value != "ceiling" or len(obj.footprint) < 3):
            continue
        z0 = obj.body_z0_m if obj.body_z0_m is not None else obj.z_m
        out.append(_Fixture(
            obj.tag, Polygon(obj.footprint), obj.position, z0,
            obj.body_z1_m if obj.body_z1_m is not None else z0, obj.storey, obj.room,
            product.form in _DOWNLIGHT_FORMS, not obj.mount.recessed_into_host_surface))
    faces = ceiling_faces(ctx.model)
    rooms = {room.tag: room for room in ctx.model.rooms}
    for run in ctx.model.light_runs:
        if run.room is None or len(run.path) < 2:
            continue
        zs = run.z_path_m or (run.z_m,)
        ceiling = finished_ceiling_at(faces, run.storey, run.room, tuple(run.path[0]))
        if run.profile != "shadow_gap" and (
                ceiling is None or ceiling - max(zs) > _RUN_CEILING_BAND_M):
            continue
        half = (run.aperture_m or 0.0) / 2 + _RUN_HALF_WIDTH_M
        shape = LineString(run.path).buffer(half, cap_style=2)
        mid = shape.centroid
        room = rooms.get(run.room)
        wall = (room is not None and len(room.clear_face) >= 3 and
                Polygon(room.clear_face).exterior.distance(LineString(run.path)) < _PERIMETER_M)
        out.append(_Fixture(run.tag, shape, (mid.x, mid.y), min(zs), min(zs), run.storey,
                            run.room, False, False, wall))
    return out


def _bodies(ctx: CheckContext) -> list[_Body]:
    furniture = {t.tag: t for t in ctx.plan.library.furniture_types}
    out: list[_Body] = []
    for obj in ctx.model.canvas_objects:
        if (obj.kind not in _BODY_KINDS or obj.body_z0_m is None or obj.body_z1_m is None
                or len(obj.footprint) < 3):
            continue
        if obj.kind == "Furniture":
            product = furniture.get(obj.type_ref or "")
            if product is None or not (product.storage or product.work_surface):
                continue
        out.append(_Body(obj.tag, Polygon(obj.footprint), obj.body_z0_m, obj.body_z1_m,
                         obj.storey, obj.room, obj.kind))
    return out


class _Floors:
    """Finished-floor elevation per room, read once, and a body's height above it."""

    def __init__(self, ctx: CheckContext) -> None:
        self._model = ctx.model
        self._rooms = {room.tag: room for room in ctx.model.rooms}
        self._cache: dict[str, float | None] = {}

    def of(self, room_tag: str | None) -> float | None:
        if room_tag is None or room_tag not in self._rooms:
            return None
        if room_tag not in self._cache:
            self._cache[room_tag] = room_finished_floor_elevation(
                self._model, self._rooms[room_tag])
        return self._cache[room_tag]

    def under(self, body: _Body, fx: _Fixture) -> float | None:
        """The floor the body stands on: its own room's, else the fixture's."""
        own = self.of(body.room)
        return own if own is not None else self.of(fx.room)


_Support = tuple[str, Polygon, float, float]  # storey, plan, top band (low, high)


def _supports(ctx: CheckContext, bodies: list[_Body]) -> list[_Support]:
    """Every surface an appliance may stand on: a body's top, or a slab over its hosts."""
    tops = {body.tag: body.z1 for body in bodies}
    out: list[_Support] = [(body.storey, body.shape, body.z1, body.z1) for body in bodies]
    for slab in ctx.model.countertops:
        z = max((tops[tag] for tag in slab.hosts if tag in tops), default=None)
        if z is not None and len(slab.outline) >= 3:
            # A host's type may or may not include the slab's own thickness.
            out.append((slab.storey, Polygon(slab.outline), z, z + slab.thickness_m))
    return out


def _stacked(body: _Body, floor: float, supports: list[_Support]) -> bool:
    """An appliance standing on a counter or another body: judged by its support."""
    if body.kind != "Appliance" or body.z0 - floor < _IN:
        return False
    return any(storey == body.storey and low - _IN <= body.z0 <= high + _IN
               and body.z1 > high and shape.intersection(body.shape).area > _MIN_OVERLAP_M2
               for storey, shape, low, high in supports)


def _inches(meters: float) -> str:
    return f'{meters / _IN:.0f}"'


def _more(tags: list[str]) -> str:
    return f" (+{len(tags) - 1} more: {', '.join(tags[1:])})" if len(tags) > 1 else ""


def _over_tall_body(fx: _Fixture, bodies: list[_Body], floors: _Floors, limit_m: float,
                    supports: list[_Support]) -> tuple[list[Finding], set[str]]:
    hits: list[tuple[_Body, float]] = []
    for body in bodies if not fx.perimeter else ():
        if (body.storey != fx.storey or body.z1 > fx.z0 + _LEVEL_TOL_M
                or fx.shape.intersection(body.shape).area <= _MIN_OVERLAP_M2):
            continue
        floor = floors.under(body, fx)
        if floor is None or body.z1 - floor <= limit_m or _stacked(body, floor, supports):
            continue
        hits.append((body, body.z1 - floor))
    if not hits:
        return [], set()
    hits.sort(key=lambda hit: -hit[1])
    tags = [body.tag for body, _ in hits]
    msg = (f'{fx.tag} is over {tags[0]} (top {_inches(hits[0][1])} AFF){_more(tags)}: it '
           f'lights the top of a body taller than {_inches(limit_m)}, not the work below it')
    return [advisory(CID, msg, (fx.tag, *tags), Result.ADVISORY,
                     fix="move the fixture off the body, onto the open floor or the work "
                         "surface in front of it")], set(tags)


def _near_tall_face(fx: _Fixture, bodies: list[_Body], floors: _Floors, tall_m: float,
                    setback_m: float, over: set[str]) -> list[Finding]:
    if not fx.downlight:
        return []
    hits: list[tuple[_Body, float]] = []
    point = Point(fx.point)
    for body in bodies:
        if (body.storey != fx.storey or body.tag in over or body.z0 >= fx.z1
                or body.z1 - body.z0 < _MIN_FACE_HEIGHT_M):
            continue
        floor, gap = floors.under(body, fx), body.shape.distance(point)
        if floor is None or body.z1 - floor <= tall_m or gap <= 1e-9 or gap > setback_m:
            continue
        hits.append((body, gap))
    if not hits:
        return []
    hits.sort(key=lambda hit: hit[1])
    tags = [body.tag for body, _ in hits]
    msg = (f'{fx.tag} stands {hits[0][1] / _IN:.1f}" from the face of {tags[0]}{_more(tags)}: '
           f'a downlight inside {_inches(setback_m)} of a face taller than {_inches(tall_m)} '
           f'scallops it')
    return [advisory(CID, msg, (fx.tag, *tags), Result.ADVISORY,
                     fix="move it to about 18\" off the face, or wash the face on purpose")]


@dataclass(frozen=True)
class _Service:
    tag: str
    kind: str
    segments: tuple[tuple[LineString, float, float], ...]  # (plan line, z at start, z at end)
    half_width_m: float
    half_depth_m: float


def _segments(path, zs) -> tuple[tuple[LineString, float, float], ...]:
    return tuple((LineString([path[i], path[i + 1]]), zs[i], zs[i + 1])
                 for i in range(len(path) - 1) if tuple(path[i]) != tuple(path[i + 1]))


def _services(ctx: CheckContext) -> list[_Service]:
    """Ducts, pipes and conduits on their per-vertex absolute centreline z."""
    out: list[_Service] = []
    for duct in ctx.model.ducts:
        if len(duct.z_m) == len(duct.path) >= 2:
            out.append(_Service(duct.tag, "duct", _segments(duct.path, duct.z_m),
                                duct.width_m / 2, duct.depth_m / 2))
    for pipe in ctx.model.pipe_runs:
        if pipe.z_m and len(pipe.z_m) == len(pipe.path) >= 2:
            radius = max(pipe.diameter_m, pipe.bundle_diameter_m or 0.0) / 2
            out.append(_Service(pipe.tag, "pipe", _segments(pipe.path, pipe.z_m), radius,
                                radius))
    for run in ctx.model.conduits:
        zs = run.z_m
        if not zs and run.z_start_m is not None and run.z_end_m is not None and len(run.path) == 2:
            zs = (run.z_start_m, run.z_end_m)
        if zs and len(zs) == len(run.path) >= 2:
            radius = run.trade_size_m / 2
            out.append(_Service(run.tag, "conduit", _segments(run.path, zs), radius, radius))
    return out


def _service_gap(fx: _Fixture, service: _Service) -> float | None:
    """The clear gap from ``service``'s top up to ``fx`` where it crosses the footprint."""
    best: float | None = None
    for line, za, zb in service.segments:
        if not line.buffer(service.half_width_m, cap_style=2).intersects(fx.shape):
            continue
        t = line.project(Point(fx.point), normalized=True)
        gap = fx.z0 - (za + (zb - za) * t + service.half_depth_m)
        if gap >= -_LEVEL_TOL_M and (best is None or gap < best):
            best = gap
    return best


def _under_surface_fixture(fx: _Fixture, services: list[_Service], bodies: list[_Body],
                           band_m: float, over: set[str]) -> list[Finding]:
    if not fx.surface:
        return []
    hits: list[tuple[str, str, float]] = []
    for service in services:
        gap = _service_gap(fx, service)
        if gap is not None and gap <= band_m:
            hits.append((service.tag, service.kind, gap))
    for body in bodies:  # a hung machine; a tall one was reported by rule 1
        gap = fx.z0 - body.z1
        if (body.kind == "Equipment" and body.storey == fx.storey and body.tag not in over
                and -_LEVEL_TOL_M <= gap <= band_m
                and fx.shape.intersection(body.shape).area > _MIN_OVERLAP_M2):
            hits.append((body.tag, "machine", gap))
    if not hits:
        return []
    hits.sort(key=lambda hit: hit[2])
    tags = [tag for tag, _, _ in hits]
    msg = (f'{fx.tag} has {hits[0][1]} {tags[0]} crossing it {max(hits[0][2], 0.0) / _IN:.1f}" '
           f'below{_more(tags)}: a service within {_inches(band_m)} under a surface fixture '
           f'shadows it and blocks the lamp change')
    return [advisory(CID, msg, (fx.tag, *tags), Result.ADVISORY,
                     fix="move the fixture off the run, or lift the run into the framing")]


@dataclass(frozen=True)
class _DoorZone:
    door: str
    zone: Polygon  # where the open panels ride
    header: tuple[float, float]  # the door's centre on its room-side face
    inward: tuple[float, float]
    storey: str


def _frame_point(wall, along: float, offset: float) -> tuple[float, float]:
    """The plan point ``along`` the wall axis and ``offset`` along its left normal."""
    origin, tangent, normal, _ = wall_frame(wall)
    return (origin[0] + tangent[0] * along + normal[0] * offset,
            origin[1] + tangent[1] * along + normal[1] * offset)


def _door_zones(ctx: CheckContext) -> list[_DoorZone]:
    """Each overhead door's open-panel zone: its width by its height into the room."""
    model = ctx.model
    overhead = {t.tag for t in ctx.plan.library.door_types
                if t.operation == DoorOperation.OVERHEAD}
    out: list[_DoorZone] = []
    for opening in model.openings:
        wall = model.wall(opening.host_wall)
        if opening.type_ref not in overhead or wall is None:
            continue
        normal, axis_length = wall_frame(wall)[2:]
        if axis_length <= 1e-9:
            continue
        faces = finish_faces(wall) or (-wall.thickness_m / 2, wall.thickness_m / 2)
        for side, room in zip((1, -1), opening_rooms(model, opening), strict=True):
            if room is None:
                continue
            half, depth, face = opening.width_m / 2, opening.height_m, faces[int(side > 0)]
            c = opening.center_along_m
            corners = [_frame_point(wall, c + u, face + side * v)
                       for u, v in ((-half, 0), (half, 0), (half, depth), (-half, depth))]
            out.append(_DoorZone(
                opening.tag, Polygon(corners), _frame_point(wall, c, face),
                (normal[0] * side, normal[1] * side), wall.storey))
    return out


def _opener_rails(ctx: CheckContext,
                  zones: list[_DoorZone]) -> list[tuple[str, str, LineString]]:
    """``(opener, door, rail line)``: opener position to the header of the door it faces."""
    openers = {t.tag for t in ctx.plan.library.appliance_types
               if getattr(t.model_representation, "symbol", None) in GARAGE_OPENER_SYMBOLS}
    out = []
    for obj in ctx.model.canvas_objects:
        if obj.type_ref not in openers:
            continue
        facing = [z for z in zones if z.storey == obj.storey
                  and (obj.position[0] - z.header[0]) * z.inward[0]
                  + (obj.position[1] - z.header[1]) * z.inward[1] > 0]
        if facing:
            zone = min(facing, key=lambda z: Point(z.header).distance(Point(obj.position)))
            out.append((obj.tag, zone.door, LineString([obj.position, zone.header])))
    return out


def _garage_door(fx: _Fixture, zones: list[_DoorZone],
                 rails: list[tuple[str, str, LineString]], clearance_m: float) -> list[Finding]:
    out: list[Finding] = []
    for zone in zones:
        if zone.storey == fx.storey and fx.shape.intersection(zone.zone).area > _MIN_OVERLAP_M2:
            out.append(advisory(
                CID, f'{fx.tag} is inside the open-panel zone of {zone.door}: the sectional '
                     f'panels ride up onto the horizontal track under it',
                (fx.tag, zone.door), Result.ADVISORY,
                fix="move it clear of the door's width x height into the room"))
    for opener, door, rail in rails:
        gap = fx.shape.distance(rail)
        if gap <= clearance_m:
            out.append(advisory(
                CID, f'{fx.tag} is {gap / _IN:.1f}" from the rail line of {opener} to {door}: '
                     f'inside {_inches(clearance_m)}, where the rail and trolley run',
                (fx.tag, opener, door), Result.ADVISORY,
                fix="move it off the rail line, or beside the opener's head"))
    return out


@check(Tier.ADVISORY, CID)
def luminaire_placement(ctx: CheckContext) -> list[Finding]:
    """Ceiling luminaires clear of tall bodies, hung services and the garage door's reach."""
    fixtures = _fixtures(ctx)
    if not fixtures:
        return [_na(CID, "no ceiling-mounted luminaire or ceiling light run in this building")]
    mep = ctx.preferences.mep
    bodies, floors, services = _bodies(ctx), _Floors(ctx), _services(ctx)
    supports = _supports(ctx, bodies)
    zones = _door_zones(ctx)
    rails = _opener_rails(ctx, zones)
    out: list[Finding] = []
    for fx in fixtures:
        over_findings, over = _over_tall_body(
            fx, bodies, floors, mep.luminaire_body_clear_height_in * _IN, supports)
        out += over_findings
        out += _near_tall_face(fx, bodies, floors, mep.luminaire_tall_body_height_in * _IN,
                               mep.luminaire_tall_face_setback_in * _IN, over)
        out += _under_surface_fixture(fx, services, bodies,
                                      mep.luminaire_service_band_in * _IN, over)
        out += _garage_door(fx, zones, rails, mep.luminaire_opener_clearance_in * _IN)
    if out:
        return out
    return [_pass(CID, f"{len(fixtures)} ceiling luminaires and light runs stand clear of tall "
                       f"bodies, hung services and the garage door's reach")]
