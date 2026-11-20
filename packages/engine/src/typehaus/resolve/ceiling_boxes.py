"""Ceiling boxes, only where a fixture mounts to one (decision #140).

A line-voltage ceiling fixture or device that ``takes_box`` (not a housing or wafer that owns
its j-box, not a PSU-fed fitting) and every hardwired alarm head get a box on the finished
ceiling over their point: flat from ``model.ceilings``, sloped under a ``FollowRoof`` room.
The host is read like a wall's (``device_boxes._host_layers``), the framing above standing in
for the stud layer: bare concrete or masonry is ``surface``; a lined framed ceiling is
``flush``, the box rising ``depth`` into the cavity; crossing an air-control membrane takes
the ``air-sealed-<use>`` row. A ceiling on resilient channel still takes its box, with a WARN
that the box bridges the decoupling. Under a soffit the soffit's ladder hosts it, lined like
the room's ceiling; with no ceiling, a lined roof's underside. No lining over the point (a
porch under a bare deck), or no framing, is no box: ``electrical.box_fill`` lists it UNKNOWN.
A ``remote_box`` type mounts on its own bracket; its junction box is a surface box on the
nearest framing beside it (``remote_feed_box``).

The resolver never moves a fixture or snaps it to framing: ``electrical.ceiling_box_framing``
grades the clash and names the shift. A ``pancake`` row is flush too: its depth sits inside
the board, so it clears the joist it screws under.
"""

from __future__ import annotations

import math
from typing import Any, NamedTuple

from shapely.geometry import MultiPoint, Point, Polygon
from shapely.geometry.polygon import orient

from typehaus.findings import Finding, Result, Severity
from typehaus.model.electrical import BoxRow, BoxStandard
from typehaus.model.refs import FollowRoof
from typehaus.resolve.ceiling_over import ceiling_channel_depth_m
from typehaus.resolve.coatings import layer_depth_m
from typehaus.resolve.device_box_mesh import box_mesh
from typehaus.resolve.device_boxes import (
    AIR_SEALED,
    ResolvedDeviceBox,
    _host_layers,
    _house,
    box_use,
    takes_box,
)
from typehaus.resolve.model import ResolvedModel, ResolvedSolid
from typehaus.resolve.overhead import OverheadIndex
from typehaus.resolve.remote_feed_box import remote_box_point
from typehaus.resolve.roof_geometry import (
    roof_height_at,
    roof_slope_factor,
    roof_underside_depth_m,
)

Vec3 = tuple[float, float, float]
_DOWN: Vec3 = (0.0, 0.0, -1.0)
_FACE_TOL_M = 0.02  # a ceiling this far under the probe's base still counts as over it
_SLOPE_STEP_M = 0.05  # the finite-difference half-step for a sloped ceiling's normal
DECOUPLING_CID = "electrical.ceiling_box_decoupling"


class _Layer(NamedTuple):
    """A ceiling ``Layer`` in the shape ``_host_layers`` reads off a wall's resolved layer."""

    name: str
    function: str
    material_ref: str
    thickness_m: float
    control: frozenset[str]


class _Face(NamedTuple):
    z: float
    axis: Vec3
    layers: tuple[Any, ...]
    room: str | None
    #: A soffit hosts its own box: (its tag, the top of its cavity).
    soffit: tuple[str, float] | None = None


def resolve_ceiling_boxes(model: ResolvedModel) -> list[Finding]:
    """Append a ``host="ceiling"`` record and an ``electrical_box`` solid per boxed fixture."""
    standard, _ = _house(model.plan)
    if standard is None:
        return []
    types = {t.tag: t for t in model.plan.library.electrical_device_types}
    stage = _Stage(model, standard)
    for obj in model.canvas_objects:
        if (obj.kind != "ElectricalDevice" or obj.mount is None
                or obj.mount.kind.value != "ceiling"):
            continue
        item = model.plan.by_tag(obj.tag)
        product_type = types.get(obj.type_ref or "")
        if item is None or not takes_box(item, product_type):
            continue
        if getattr(product_type, "remote_box", False):
            stage.place_remote(item, product_type, obj.storey, obj.room, obj.position,
                               obj.z_m, tuple(obj.footprint), item.kind.value)
        else:
            stage.place(item, product_type, obj.storey, obj.room, obj.position, obj.z_m,
                        tuple(obj.footprint), item.kind.value)
    for head in model.alarm_heads:
        if head.mount != "ceiling" or head.x is None or head.z is None:
            continue
        alarm = model.plan.by_tag(head.tag)
        product_type = types.get(alarm.type_ref or "") if alarm is not None else None
        if alarm is not None and takes_box(alarm, product_type):
            ring = tuple(head.body.solids[0].ring) if head.body is not None else ()
            stage.place(alarm, product_type, head.storey, alarm.room, (head.x, head.y),
                        head.z - _FACE_TOL_M, ring, "alarm")
    return stage.findings


class _Stage:
    def __init__(self, model: ResolvedModel, standard: BoxStandard) -> None:
        self.model, self.standard = model, standard
        self.findings: list[Finding] = []
        self.structure = OverheadIndex(model)
        self.floors = {floor.tag: floor for floor in model.floors}
        self.ceilings = [(c, Polygon(c.outline).buffer(1e-6)) for c in model.ceilings
                         if len(c.outline) >= 3]
        self.roofs = {roof.tag: roof for roof in model.roofs}
        self.soffits = [(s, Polygon(s.outline).buffer(1e-6)) for s in model.soffits
                        if len(s.outline) >= 3]

    def place(self, item: Any, product_type: Any, storey: str, room: str | None,
              xy: tuple[float, float], base_z: float, device_footprint: tuple,
              kind: str) -> None:
        face = self._face(xy, base_z, storey, room)
        if face is None:
            return
        over = self.structure.lowest_above(xy[0], xy[1], face.z)
        if over is None:
            return
        layers = [_Layer(layer.name, layer.function.value, layer.material_ref,
                         layer_depth_m(self.model.plan.library, layer),
                         frozenset(c.value for c in layer.control)) for layer in face.layers]
        floor = None if face.soffit else self.floors.get(over.tag)
        host_tag, top = face.soffit or (over.tag, floor.deck_z0_m if floor else None)
        # The framing above stands in for a wall's stud layer: its depth is the cavity.
        cavity_above = (top - face.z - sum(layer.thickness_m for layer in layers)
                        if top is not None else 0.0)
        layers.append(_Layer(host_tag, "structure", "", max(cavity_above, 0.0), frozenset()))
        found = _host_layers(self.model, layers)
        if found is None:
            return
        mounting, cavity, host_layer, crossed = found
        air = mounting != "surface" and any(
            layer.function == "membrane" and "air" in layer.control for layer in crossed)
        row = _row(self.standard, mounting, box_use(item, product_type), air)
        if row is None:
            return
        if floor is not None:
            self._decoupling(item, floor.tag, face.room)
        self._record(item, storey, face.room or room, xy, face, row, mounting,
                     cavity if top is not None else None,
                     host_layer, air, device_footprint, kind)

    def place_remote(self, item: Any, product_type: Any, storey: str, room: str | None,
                     xy: tuple[float, float], base_z: float, device_footprint: tuple,
                     kind: str) -> None:
        """A self-mounting fitting's junction box: surface, on the framing beside it."""
        over = self.structure.lowest_above(xy[0], xy[1], base_z)
        floor = None if over is None else self.floors.get(over.tag)
        row = _row(self.standard, "surface", box_use(item, product_type), False)
        if floor is None or row is None:
            return
        found = remote_box_point(floor, xy, device_footprint, row.box_size[0].meters, base_z)
        if found is None:
            return
        at, z, member = found
        face = _Face(z, _DOWN, (), room)
        self._record(item, storey, room, at, face, row, "surface", None,
                     f"{floor.tag}/{member}", False, device_footprint, kind)

    def _face(self, xy: tuple[float, float], base_z: float, storey: str,
              room: str | None) -> _Face | None:
        """The lowest finished face over ``xy`` above ``base_z``: a ceiling, a soffit lined
        like the room's ceiling, else a lined roof's underside."""
        limit = self.structure.lowest_above(xy[0], xy[1], base_z)
        point = Point(xy)
        best = self._ceiling_face(point, xy, base_z, limit)
        soffit = next((s for s, cover in self.soffits if limit is not None
                       and s.tag == limit.tag and cover.covers(point)), None)
        if soffit is not None and (best is None or soffit.z0_m < best.z):
            lining = next((c for c, cover in self.ceilings if c.storey == storey
                           and cover.covers(point)), None)
            if lining is None:
                return None
            return _Face(soffit.z0_m, _DOWN, lining.layers, lining.room_ref,
                         (soffit.tag, soffit.z1_m))
        if best is None and limit is not None and limit.tag in self.roofs:
            return self._roof_face(self.roofs[limit.tag], xy, room)
        return best

    def _ceiling_face(self, point: Any, xy: tuple[float, float], base_z: float,
                      limit: Any) -> _Face | None:
        best = None
        for ceiling, cover in self.ceilings:
            if not cover.covers(point):
                continue
            if ceiling.z0_m is not None:
                z, axis = ceiling.z0_m, _DOWN
            else:
                sloped = self._sloped(ceiling, xy)
                if sloped is None:
                    continue
                z, axis = sloped
            if z < base_z - _FACE_TOL_M or (limit is not None and z > limit.z_m + _FACE_TOL_M):
                continue
            if best is None or z < best.z:
                best = _Face(z, axis, ceiling.layers, ceiling.room_ref)
        return best

    def _sloped(self, ceiling: Any, xy: tuple[float, float]) -> tuple[float, Vec3] | None:
        room = self.model.plan.by_tag(ceiling.room_ref)
        if room is None or not isinstance(room.ceiling, FollowRoof):
            return None
        roof = self.roofs.get(room.ceiling.roof_ref)
        depth = None if roof is None else roof_underside_depth_m(self.model, roof, room.tag)
        if depth is None:
            return None
        return roof_height_at(roof, xy) - depth, _slope_axis(roof, xy)

    def _roof_face(self, roof: Any, xy: tuple[float, float], room: str | None) -> _Face | None:
        assembly = self.model.plan.library.resolve_assembly(roof.assembly)
        lining = tuple(getattr(assembly, "default_lining", ()) or ())
        depth = roof_underside_depth_m(self.model, roof)
        if not lining or depth is None:
            return None
        board = sum(layer_depth_m(self.model.plan.library, layer) for layer in lining)
        z = roof_height_at(roof, xy) - depth - board * roof_slope_factor(roof)
        return _Face(z, _slope_axis(roof, xy), lining, room)

    def _decoupling(self, item: Any, deck_tag: str, room: str) -> None:
        deck = self.model.plan.by_tag(deck_tag)
        if deck is None or ceiling_channel_depth_m(self.model.plan.library, deck, room) <= 0:
            return
        self.findings.append(Finding(
            severity=Severity.WARN, check_id=DECOUPLING_CID, result=Result.ADVISORY,
            message=f"{item.tag}'s ceiling box in {room} is fixed to {deck_tag}'s framing "
                    "through a resilient-channel ceiling: it bridges the decoupling",
            element_tags=(item.tag,),
            fix="a wall mount instead, or a box on the channel alone, sealed in the board"))

    def _record(self, item: Any, storey: str, room: str, xy: tuple[float, float], face: _Face,
                row: BoxRow, mounting: str, cavity: float | None, host_layer: str, air: bool,
                device_footprint: tuple, kind: str) -> None:
        width, height, depth = (part.meters for part in row.box_size)
        axis = face.axis
        tangent = _unit((-axis[1], axis[0], 0.0)) if math.hypot(axis[0], axis[1]) > 1e-9 \
            else (1.0, 0.0, 0.0)
        up = _cross(tangent, axis)
        mesh = box_mesh((xy[0], xy[1], face.z), tangent, axis, up=up, width=width,
                        height=height, depth=depth, shape=row.shape, mounting=mounting,
                        cover_rise=row.cover_rise.meters)
        hull = orient(MultiPoint([p[:2] for p in mesh.positions]).convex_hull, 1.0)
        ring = tuple(tuple(p) for p in list(hull.exterior.coords)[:-1])
        z0 = min(p[2] for p in mesh.positions)
        z1 = max(p[2] for p in mesh.positions)
        projection = depth + row.cover_rise.meters if mounting == "surface" else 0.0
        circuit = getattr(item, "circuit", None)
        self.model.device_boxes.append(ResolvedDeviceBox(
            device_tag=item.tag, device_uid=item.uid, storey=storey, room=room,
            device_kind=kind, circuit=circuit, mounting=mounting, gangs=row.gangs,
            box_product=row.box_product_ref, cover_product=row.cover_product_ref,
            volume_in3=row.volume_in3, width_m=width, height_m=height, depth_m=depth,
            projection_m=projection, cavity_m=cavity, wall_tag=None, host_layer=host_layer,
            footprint=ring, z0_m=z0, z1_m=z1, face_point=xy, normal=(axis[0], axis[1]),
            device_footprint=device_footprint, uid=f"{item.uid}-box", shape=row.shape,
            air_barrier=air, box_use=row.use, internal_clamps=row.internal_clamps,
            support_fittings=row.support_fittings, terminal_blocks=row.terminal_blocks,
            device_tags=(item.tag,), device_uids=(item.uid,), device_kinds=(kind,),
            circuits=(circuit,), member_footprints=(device_footprint,), snap_shifts_m=(0.0,),
            member_gangs=(row.gangs,), host="ceiling", axis=axis))
        self.model.solids.append(ResolvedSolid(
            uid=f"{item.uid}-box", tag=f"{item.tag}-BOX", storey=storey,
            category="electrical_box", outline=list(ring), z0_m=z0, z1_m=z1,
            product=row.box_product_ref, material=row.material_ref, body_mesh=mesh,
            derived=True))  # billed in [electrical_boxes]


def _row(standard: BoxStandard, mounting: str, use: str | None, air: bool) -> BoxRow | None:
    """The ``use`` row, else ``"ceiling"``, else the general one; an air-sealed row first."""
    chain = [use, "ceiling"] if use not in (None, "ceiling") else [use] if use else []

    def exact(want: str | None) -> BoxRow | None:
        return next((r for r in standard.rows
                     if r.mounting == mounting and r.gangs == 1 and r.use == want), None)

    if air:
        for want in [f"{AIR_SEALED}-{u}" for u in chain] + [AIR_SEALED]:
            if (row := exact(want)) is not None:
                return row
    return next((row for row in map(exact, chain) if row is not None), None) or exact(None)


def _slope_axis(roof: Any, xy: tuple[float, float]) -> Vec3:
    """The unit normal into the room under a roof plane at ``xy``."""
    x, y, h = xy[0], xy[1], _SLOPE_STEP_M
    fx = (roof_height_at(roof, (x + h, y)) - roof_height_at(roof, (x - h, y))) / (2 * h)
    fy = (roof_height_at(roof, (x, y + h)) - roof_height_at(roof, (x, y - h))) / (2 * h)
    norm = math.sqrt(fx * fx + fy * fy + 1.0)
    return (fx / norm, fy / norm, -1.0 / norm)


def _unit(v: Vec3) -> Vec3:
    norm = math.sqrt(sum(c * c for c in v))
    return (v[0] / norm, v[1] / norm, v[2] / norm)


def _cross(a: Vec3, b: Vec3) -> Vec3:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
