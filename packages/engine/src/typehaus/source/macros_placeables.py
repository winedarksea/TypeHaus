"""Placeable editing macros: move, rotate, attach, mount, retype, duplicate, place.

Split out of :mod:`typehaus.source.macros` along its ``# --- shared placeable editing`` and
``# --- coupled drain followers`` bands. The two belong together: a drag is not a scalar
patch on one element, because a drained fixture carries a cast-in sleeve and a routed pipe
run with it, and the code that decides what follows a move has to sit next to the move.

Kind-agnostic by construction — furniture, fixtures, appliances, equipment, registers, and
electrical devices all take the same edits (→ 21b).
"""

from __future__ import annotations

import math

from typehaus.model.elements import Door, RoughOpening
from typehaus.model.enums import DeviceKind, DuctSystem, EquipmentKind, Service
from typehaus.model.mep import ElectricalDevice, Equipment, Register
from typehaus.model.placeables import Mount
from typehaus.model.plan import PlanModel
from typehaus.model.refs import from_node
from typehaus.model.remap import Impact, MutationResult
from typehaus.model.spatial import Appliance, Fixture, Furniture
from typehaus.quantities import deg
from typehaus.quantities.length import ft, m
from typehaus.quantities.point import pt
from typehaus.source.macros_common import (
    ROTATION_SNAP_DEGREES,
    XY,
    MacroError,
    _as_length,
    _copy_tag,
    _meters,
    _next_tag,
    _nodes,
    _openings,
    _placeable,
    _point_expr,
    _point_expr_m,
    _resolved_rooms,
    _rooms,
    _walls,
)
from typehaus.source.macros_followers import _follower_ops, _wall_axis
from typehaus.source.macros_geometry import _dist
from typehaus.source.macros_openings import (
    _opening_start_offset,
    _opening_width,
    _validate_opening_station,
    place_opening,
)
from typehaus.source.ops import DELETE_FIELD, PatchOp, RawExpr
from typehaus.source.serialize import element_add_op


def move_placeable(plan: PlanModel, storey: str, *, tag: str, position: XY,
                   rooms=None) -> MutationResult:
    """Move a free object, persisting the room containing its new footprint center.

    A drained fixture is not a free object: its waste leaves through a cast-in-place
    :class:`SleevePenetration` and drops into a routed :class:`PipeRun`, and neither of
    those is derived from the fixture — both are authored plan geometry that a drag would
    otherwise leave behind (`macros_followers._drain_follower_ops`). Every relationship the
    move touches comes back as an impact.
    """
    item = _placeable(plan, storey, tag)
    if item is None:
        raise MacroError(f"no placeable {tag!r} on storey {storey!r}")
    x, y = _meters(position[0]), _meters(position[1])
    ops = [PatchOp("update", item.element_kind, tag, {
        "position": _point_expr(position[0], position[1]), "location": DELETE_FIELD,
        "room": _containing_room(plan, storey, (x, y), rooms=rooms),
    })]
    followers, impacts = _follower_ops(plan, storey, item, (x, y))
    ops.extend(followers)
    return _with_impacts(ops, tag, impacts)


def _with_impacts(ops: list[PatchOp], tag: str, impacts: list[Impact]) -> MutationResult:
    # A carried note about the moved item itself is informational, not a warning.
    warnings = tuple(i.reason for i in impacts if i.tag != tag or i.kind != "carried")
    return MutationResult(ops=ops, warnings=warnings, impacts=tuple(impacts))


def rotate_placeable(plan: PlanModel, storey: str, *, tag: str, degrees: float,
                     free_rotation: bool = False) -> MutationResult:
    item = _placeable(plan, storey, tag)
    if item is None:
        raise MacroError(f"no placeable {tag!r} on storey {storey!r}")
    resolved_degrees = (float(degrees) if free_rotation
                        else round(float(degrees) / ROTATION_SNAP_DEGREES) * ROTATION_SNAP_DEGREES)
    return MutationResult(ops=[PatchOp("update", item.element_kind, tag,
                                       {"rotation": RawExpr(deg(resolved_degrees).to_source())})])


def attach_placeable(plan: PlanModel, storey: str, *, tag: str, wall: str, face: str,
                     distance: float | str, gap: float | str = 0,
                     rotation_offset: float = 0) -> MutationResult:
    item = _placeable(plan, storey, tag)
    if item is None:
        raise MacroError(f"no placeable {tag!r} on storey {storey!r}")
    if face not in {"left", "right"}:
        raise MacroError("attachment face must be 'left' or 'right'")
    if not any(candidate.tag == wall for candidate in _walls(plan, storey)):
        raise MacroError(f"no wall {wall!r} on storey {storey!r}")
    d, normal_gap = _as_length(distance), _as_length(gap)
    location = (f'Location(attachment=WallAttachment(wall_ref="{wall}", face="{face}", '
                f'distance_from_start={d.to_source()}, normal_gap={normal_gap.to_source()}, '
                f'rotation_offset={deg(rotation_offset).to_source()}))')
    return MutationResult(ops=[PatchOp("update", item.element_kind, tag,
                                       {"location": RawExpr(location)})])


def set_placeable_mount(plan: PlanModel, storey: str, *, tag: str,
                        elevation: float | str) -> MutationResult:
    """Raise or lower a mounted object, rewriting only the mount's elevation.

    The other three mount fields are authored intent that a height edit must not silently
    discard: ``kind`` says what surface the object hangs on, ``drop`` how far a pendant hangs
    below its ceiling, and ``recessed_into_host_surface`` whether it obstructs a neighbour's
    clear floor space. So the whole constructor is rebuilt from the current mount rather than
    replaced with a bare ``Mount(elevation=…)``.
    """
    item = _placeable(plan, storey, tag)
    if item is None:
        raise MacroError(f"no placeable {tag!r} on storey {storey!r}")
    mount = getattr(item, "mount", None) or Mount()
    height = _as_length(elevation)
    if height.meters < 0:
        raise MacroError("mount elevation must be at or above the floor")
    fields = [f"kind=MountKind.{mount.kind.name}", f"elevation={height.to_source()}"]
    if mount.drop is not None:
        fields.append(f"drop={mount.drop.to_source()}")
    if mount.recessed_into_host_surface:
        fields.append("recessed_into_host_surface=True")
    return MutationResult(ops=[PatchOp("update", item.element_kind, tag,
                                       {"mount": RawExpr(f"Mount({', '.join(fields)})")})])


def detach_placeable(plan: PlanModel, storey: str, *, tag: str,
                     position: XY | None = None, rooms=None) -> MutationResult:
    item = _placeable(plan, storey, tag)
    if item is None:
        raise MacroError(f"no placeable {tag!r} on storey {storey!r}")
    fields: dict[str, object] = {"location": DELETE_FIELD}
    if position is None:
        return MutationResult(ops=[PatchOp("update", item.element_kind, tag, fields)])
    xy = (_meters(position[0]), _meters(position[1]))
    fields["position"] = _point_expr(position[0], position[1])
    fields["room"] = _containing_room(plan, storey, xy, rooms=rooms)
    followers, impacts = _follower_ops(plan, storey, item, xy)
    # Detaching is the point here, so the dropped attachment is not news.
    impacts = [i for i in impacts if "attachment to" not in i.reason]
    return _with_impacts([PatchOp("update", item.element_kind, tag, fields), *followers],
                         tag, impacts)


def slide_placeable(plan: PlanModel, storey: str, *, tag: str,
                    distance: float | str) -> MutationResult:
    """Slide a wall-attached object along its wall: only ``distance_from_start`` changes.

    The rest of the attachment (wall, face, gap, rotation offset) and any authored location
    rotation are rebuilt from the current record, the way :func:`set_placeable_mount` keeps
    a mount's other fields."""
    item = _placeable(plan, storey, tag)
    if item is None:
        raise MacroError(f"no placeable {tag!r} on storey {storey!r}")
    location = getattr(item, "location", None)
    attachment = getattr(location, "attachment", None)
    if attachment is None:
        raise MacroError(f"placeable {tag!r} is not attached to a wall")
    d = _as_length(distance)
    axis = _wall_axis(plan, storey, attachment.wall_ref)
    if axis is not None:
        length = _dist(*axis)
        if not 0.0 <= d.meters <= length:
            d = m(round(max(0.0, min(length, d.meters)), 4))
    parts = [f'wall_ref="{attachment.wall_ref}"', f'face="{attachment.face}"',
             f"distance_from_start={d.to_source()}",
             f"normal_gap={attachment.normal_gap.to_source()}"]
    if attachment.rotation_offset is not None:
        parts.append(f"rotation_offset={_source(attachment.rotation_offset)}")
    fields = [f"attachment=WallAttachment({', '.join(parts)})"]
    if location.position is not None:
        fields.insert(0, f"position={_source(location.position)}")
    if location.rotation is not None:
        fields.insert(0, f"rotation={_source(location.rotation)}")
    return MutationResult(ops=[PatchOp("update", item.element_kind, tag,
                                       {"location": RawExpr(f"Location({', '.join(fields)})")})])


def _source(value: object) -> str:
    from typehaus.source.serialize import value_source

    return value_source(value)


def delete_placeable(plan: PlanModel, storey: str, *, tag: str) -> MutationResult:
    """Delete a placeable, refusing while anything else names it (a drain run serving it, a
    sleeve, a switch leg, a shelf bank hosted on it): those would dangle silently."""
    item = _placeable(plan, storey, tag)
    if item is None:
        raise MacroError(f"no placeable {tag!r} on storey {storey!r}")
    referencing = _references_to(plan, tag)
    if referencing:
        raise MacroError(f"{tag} is still referenced by {'; '.join(referencing)} — "
                         "remove or re-point those first")
    return MutationResult(ops=[PatchOp("delete", item.element_kind, tag, {})],
                          deleted_tags=(tag,))


def _references_to(plan: PlanModel, tag: str) -> list[str]:
    found: list[str] = []
    for element in plan.all_elements():
        if element.tag == tag:
            continue
        fields = sorted(name for name, value in element.model_dump().items()
                        if value == tag or (isinstance(value, (list, tuple)) and tag in value))
        if fields:
            found.append(f"{element.element_kind} {element.tag} ({', '.join(fields)})")
    return found


def retype_placeable(plan: PlanModel, storey: str, *, tag: str,
                     type_ref: str) -> MutationResult:
    """Swap a placeable's product type, keeping its wall-mounted face where it was.

    A bare ``type_ref`` PATCH grows/shrinks the footprint about the authored *center*
    (position is the footprint centroid, ``resolve/placeables.py::_local_footprint``),
    which un-seats a wall-backed unit. This macro does that arithmetic: when both types carry a
    rectangular footprint and the item names a ``wall_ref``, the position shifts by
    ``(d_old − d_new)/2`` along the *back* direction (local +y under the item's rotation
    — ``resolve/placeables.py`` defines local −y as the room-facing front), so the
    mounted back face stays exactly where it was. The along-wall center station keeps;
    re-centring in an alcove stays the author's call. Items placed by a
    ``location.attachment`` need no shift (the resolver re-derives their center from the
    wall face each build), and items with neither get a warning instead of a guess.

    Every other authored reference to the tag (``PipeRun.serves``,
    ``Sleeve.serves_fixture``, lighting ``controlled_by``, …) stays *valid* — the tag
    does not change — but sizing that was authored against the old type (drain/trap
    diameters, slice cut planes) is not rewritten; those surface as warnings for review.
    Out of scope, deliberately: tag renames, catalog/type edits, rewriting dependent
    diameters."""
    from typehaus.resolve.placeables import _TYPE_COLLECTIONS

    item = _placeable(plan, storey, tag)
    if item is None:
        raise MacroError(f"no placeable {tag!r} on storey {storey!r}")
    types = {entry.tag: entry for collection, _, _ in _TYPE_COLLECTIONS
             for entry in getattr(plan.library, collection)}
    new_type = types.get(type_ref)
    if new_type is None:
        raise MacroError(f"unknown product type {type_ref!r}")
    old_type = types.get(getattr(item, "type_ref", None))
    fields: dict[str, object] = {"type_ref": type_ref}
    warnings: list[str] = []

    old_fp = getattr(old_type, "footprint", None) if old_type is not None else None
    new_fp = getattr(new_type, "footprint", None)
    if old_fp is not None and new_fp is not None:
        depth_shift_m = (old_fp[1].meters - new_fp[1].meters) / 2.0
        footprint_changed = (abs(old_fp[0].meters - new_fp[0].meters) > 1e-9
                             or abs(depth_shift_m) > 1e-9)
        location = getattr(item, "location", None)
        attached = location is not None and getattr(location, "attachment", None) is not None
        if footprint_changed and not attached:
            if getattr(item, "wall_ref", None) and abs(depth_shift_m) > 1e-9:
                rotation = getattr(item, "rotation", None)
                theta = rotation.radians if rotation is not None else 0.0
                x, y = item.position.xy_m
                fields["position"] = _point_expr_m(
                    x - depth_shift_m * math.sin(theta),
                    y + depth_shift_m * math.cos(theta))
                warnings.append(
                    f"{tag} re-anchored: back face held against {item.wall_ref} "
                    f"(center moved {abs(depth_shift_m) / 0.0254:.1f}\" "
                    f"{'toward' if depth_shift_m > 0 else 'away from'} the wall)")
            elif not getattr(item, "wall_ref", None):
                warnings.append(
                    f"{tag} footprint changed ({old_fp[0].fmt()} x {old_fp[1].fmt()} → "
                    f"{new_fp[0].fmt()} x {new_fp[1].fmt()}) but it names no wall_ref — "
                    "position kept as-is; verify placement")

    for element in plan.all_elements():
        if element.tag == tag:
            continue
        referencing = sorted(
            field for field, value in element.model_dump().items()
            if value == tag or (isinstance(value, (list, tuple)) and tag in value))
        if referencing:
            warnings.append(
                f"{element.element_kind} {element.tag} references {tag} via "
                f"{', '.join(referencing)} — authored against the old type; review "
                "sizing/placement")
    return MutationResult(ops=[PatchOp("update", item.element_kind, tag, fields)],
                          warnings=tuple(warnings))


def assign_placeable_room(plan: PlanModel, storey: str, *, tag: str,
                          room: str | None) -> MutationResult:
    """Set or clear the explicit room claim; geometry containment remains resolver-owned."""
    item = _placeable(plan, storey, tag)
    if item is None:
        raise MacroError(f"no placeable {tag!r} on storey {storey!r}")
    if room is not None and not any(candidate.tag == room for candidate in _rooms(plan, storey)):
        raise MacroError(f"no room {room!r} on storey {storey!r}")
    return MutationResult(ops=[PatchOp("update", item.element_kind, tag, {"room": room})])


def duplicate_canvas_object(plan: PlanModel, storey: str, *, tag: str,
                            rooms=None) -> MutationResult:
    """Duplicate a canvas instance through the same source-backed macro path as placement.

    New instances deliberately receive a fresh mutable tag/UID.  Free placeables are offset
    by one foot so the duplicate is immediately visible; hosted openings seek the next
    non-overlapping station on their existing wall.
    """
    placeable = _placeable(plan, storey, tag)
    if placeable is not None:
        if placeable.type_ref is None:
            raise MacroError(f"placeable {tag!r} has no catalog type")
        x, y = placeable.position.xy_m
        return place_placeable(plan, storey, type_ref=placeable.type_ref,
                               position=(x + 0.3048, y + 0.3048), tag=_copy_tag(plan, tag),
                               kind=getattr(getattr(placeable, "kind", None), "value", None),
                               rooms=rooms)
    opening = next((item for item in _openings(plan, storey) if item.tag == tag), None)
    if opening is None:
        raise MacroError(f"no canvas object {tag!r} on storey {storey!r}")
    wall = next((item for item in _walls(plan, storey) if item.tag == opening.host), None)
    if wall is None:
        raise MacroError(f"opening {tag!r} hosts on missing wall {opening.host!r}")
    start = next((item for item in _nodes(plan, storey) if item.tag == wall.start_node), None)
    end = next((item for item in _nodes(plan, storey) if item.tag == wall.end_node), None)
    if start is None or end is None:
        raise MacroError(f"wall {wall.tag!r} has unresolved endpoints")
    length = ((start.position.x.meters - end.position.x.meters) ** 2 +
              (start.position.y.meters - end.position.y.meters) ** 2) ** .5
    width = _opening_width(plan, opening)
    original = _opening_start_offset(opening, wall, length, width)
    for station in (original + width + .1524, original - width - .1524):
        try:
            if isinstance(opening, RoughOpening):
                copied = RoughOpening(tag=_copy_tag(plan, tag), host=wall.tag,
                                      position=from_node(wall.start_node, m(station)),
                                      width=opening.width, height=opening.height,
                                      sill_height=opening.sill_height, arch=opening.arch)
                _validate_opening_station(plan, storey, copied, wall, m(station))
                op = element_add_op(copied, tag=copied.tag, hint_list="OPENINGS")
                op.fields["position"] = RawExpr(
                    f'from_node("{wall.start_node}", {m(station).to_source()})')
                return MutationResult(ops=[op])
            return place_opening(plan, storey, host=wall.tag, type_ref=opening.type_ref,
                                 along=station, is_door=isinstance(opening, Door),
                                 sill=(opening.sill_height.meters
                                       if opening.sill_height is not None else None),
                                 tag=_copy_tag(plan, tag))
        except MacroError as exc:
            if "does not fit" not in str(exc) and "conflicts" not in str(exc):
                raise
    raise MacroError(f"no non-overlapping station available to duplicate opening {tag!r}")


def place_placeable(plan: PlanModel, storey: str, *, type_ref: str, position: XY,
                    hint_file: str | None = None, tag: str | None = None,
                    kind: str | None = None, rotation: float | None = None,
                    rooms=None) -> MutationResult:
    """Instantiate a catalog type at a project position through the ordinary undo journal."""
    x, y = _as_length(position[0]), _as_length(position[1])
    collection_map = (
        ("furniture_types", Furniture, "FURNITURE", "F-"),
        ("fixture_types", Fixture, "FIXTURES", "FX-"),
        ("appliance_types", Appliance, "APPLIANCES", "APPL-"),
        ("equipment_types", Equipment, "EQUIPMENT", "EQ-"),
        ("register_types", Register, "REGISTERS", "REG-"),
        ("electrical_device_types", ElectricalDevice, "DEVICES", "ED-"),
    )
    selected = next(
        ((cls, list_name, prefix)
         for collection, cls, list_name, prefix in collection_map
         if any(product.tag == type_ref for product in getattr(plan.library, collection))),
        None)
    if selected is None:
        raise MacroError(f"unknown placeable type {type_ref!r}")
    cls, list_name, prefix = selected
    # Project source owns a mixed editable placeables list for each storey.  Keeping all
    # product domains together lets an imported appliance/device use the same journal path.
    list_name = f"{storey.upper()}_PLACEABLES"
    new_tag = tag or _next_tag(list(plan.storey_elements(storey)), prefix)
    common = {"tag": new_tag, "type_ref": type_ref, "position": pt(x, y),
              "room": _containing_room(plan, storey, (x.meters, y.meters), rooms=rooms)}
    if rotation is not None and float(rotation) % 360.0:
        common["rotation"] = deg(float(rotation) % 360.0)
    if cls is Equipment:
        item = Equipment(**common, kind=EquipmentKind(kind) if kind
                         else _infer_equipment_kind(plan, type_ref),
                         footprint=(ft(2), ft(2)))
    elif cls is Register:
        item = Register(**common, kind=DuctSystem(kind) if kind
                        else _infer_register_kind(plan, type_ref))
    elif cls is ElectricalDevice:
        item = ElectricalDevice(**common, kind=DeviceKind(kind) if kind
                                else _infer_device_kind(plan, type_ref))
    else:
        item = cls(**common)
    return MutationResult(ops=[element_add_op(item, tag=new_tag, hint_list=list_name,
                                               hint_file=hint_file)])


def _containing_room(plan: PlanModel, storey: str, position: tuple[float, float], *,
                     rooms=None) -> str | None:
    """The room whose resolved clear face covers ``position``, so an authored claim follows a drag.

    A room seed alone is not a boundary, so this reads resolved faces: ``rooms`` from the
    caller's live model when it has one (the server does — no second resolve per move), else
    a preview resolve. A plan that cannot resolve leaves the claim empty, which is safer than
    keeping a now-wrong room; the resolver reports the topology problem itself.
    """
    try:
        from shapely.geometry import Point, Polygon

        return next((room.tag for room in _resolved_rooms(plan, rooms)
                     if room.storey == storey and len(room.clear_face) >= 3
                     and Polygon(room.clear_face).covers(Point(position))), None)
    except Exception:  # noqa: BLE001 - macros must remain usable while a plan is mid-edit
        return None


# Tokens in a device type's plan symbol, tag or name → its kind; first match wins, so the
# more specific spellings come first. Anything unmatched is a receptacle.
_DEVICE_KIND_TOKENS = (
    ("gfci", DeviceKind.RECEPTACLE_GFCI), ("240", DeviceKind.RECEPTACLE_240),
    ("switch", DeviceKind.SWITCH), ("dimmer", DeviceKind.SWITCH),
    ("light", DeviceKind.LIGHT), ("sconce", DeviceKind.LIGHT), ("can", DeviceKind.LIGHT),
    ("panel", DeviceKind.PANEL), ("load centre", DeviceKind.PANEL),
    ("meter", DeviceKind.METER), ("disconnect", DeviceKind.DISCONNECT),
    ("junction", DeviceKind.JUNCTION_BOX), ("data", DeviceKind.DATA_OUTLET),
)


def _infer_device_kind(plan: PlanModel, type_ref: str) -> DeviceKind:
    product = next((t for t in plan.library.electrical_device_types if t.tag == type_ref), None)
    words = " ".join(str(part or "") for part in (
        getattr(product, "plan_symbol", None), type_ref, getattr(product, "name", None))).lower()
    return next((kind for token, kind in _DEVICE_KIND_TOKENS if token in words),
                DeviceKind.RECEPTACLE)


def _product_words(product, type_ref: str) -> str:
    return " ".join(str(part or "") for part in (
        getattr(product, "plan_symbol", None), type_ref, getattr(product, "name", None))).lower()


#: Ordered: the FIRST token found wins, so a more specific product is listed before the
#: family it is a member of ("water heater" before "heat pump", the ERV's own plenums and
#: hoods before "erv" itself, which their tags also carry).
_EQUIPMENT_KIND_TOKENS = (
    ("mixing", EquipmentKind.MIXING_BOX),
    ("manifold", EquipmentKind.DUCT_MANIFOLD), ("plenum", EquipmentKind.DUCT_MANIFOLD),
    ("hood", EquipmentKind.DUCT_MANIFOLD),
    ("water heater", EquipmentKind.WATER_HEATER),
    ("sauna", EquipmentKind.SAUNA_HEATER),
    ("batt", EquipmentKind.BATTERY), ("inverter", EquipmentKind.INVERTER),
    ("fireplace", EquipmentKind.SPACE_HEATER),
    ("heat kit", EquipmentKind.SPACE_HEATER), ("heatkit", EquipmentKind.SPACE_HEATER),
    ("ducted", EquipmentKind.DUCTED_AIR_HANDLER),
    ("head", EquipmentKind.INDOOR_HEAD), ("cassette", EquipmentKind.INDOOR_HEAD),
    ("outdoor", EquipmentKind.HEAT_PUMP), ("condenser", EquipmentKind.HEAT_PUMP),
    ("heat pump", EquipmentKind.HEAT_PUMP),
    ("erv", EquipmentKind.ERV), ("hrv", EquipmentKind.ERV),
    ("heater", EquipmentKind.SPACE_HEATER),
    ("air handler", EquipmentKind.AIR_HANDLER), ("furnace", EquipmentKind.FURNACE),
)

_REGISTER_KIND_TOKENS = (
    ("transfer", DuctSystem.TRANSFER), ("dryer", DuctSystem.DRYER),
    ("-ret", DuctSystem.RETURN), ("return", DuctSystem.RETURN),
    ("-exh", DuctSystem.EXHAUST), ("exhaust", DuctSystem.EXHAUST),
    ("extract", DuctSystem.EXHAUST), ("stale", DuctSystem.EXHAUST),
)


def _infer_equipment_kind(plan: PlanModel, type_ref: str) -> EquipmentKind:
    """Guess the machine from its product, so the catalog does not place every box as a furnace.

    Nothing on ``EquipmentType`` states the kind — ``needs`` is a service list, not a family —
    so this reads the product's own words, the way :func:`_infer_device_kind` does. It is
    oracled against catlin's 21 authored equipment types, which it reproduces exactly
    (``test_canvas_placeable_edits.py::test_equipment_kind_inference_matches_catlin``). A
    caller that knows better passes ``kind``; FURNACE stays the fallback.
    """
    product = next((t for t in plan.library.equipment_types if t.tag == type_ref), None)
    words = _product_words(product, type_ref)
    return next((kind for token, kind in _EQUIPMENT_KIND_TOKENS if token in words),
                EquipmentKind.FURNACE)


def _infer_register_kind(plan: PlanModel, type_ref: str) -> DuctSystem:
    """Which air system a grille belongs to — a guess the product genuinely cannot settle.

    One grille serves two systems: catlin files ``REG-T-ERV-EXH`` as EXHAUST six times and as
    RETURN seven, same product both ways. So this reads the words for the clear cases and
    falls back to the ``needs`` service, and SUPPLY last; the Inspector is where a placement
    that guessed wrong gets corrected. Never let a check treat this as authored intent.
    """
    product = next((t for t in plan.library.register_types if t.tag == type_ref), None)
    words = _product_words(product, type_ref)
    hit = next((system for token, system in _REGISTER_KIND_TOKENS if token in words), None)
    if hit is not None:
        return hit
    needs = getattr(product, "needs", frozenset()) or frozenset()
    if Service.RETURN_AIR in needs:
        return DuctSystem.RETURN
    if Service.EXHAUST_AIR in needs:
        return DuctSystem.EXHAUST
    return DuctSystem.SUPPLY
