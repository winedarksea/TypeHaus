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
from typehaus.model.remap import MutationResult
from typehaus.model.spatial import Appliance, Fixture, Furniture
from typehaus.quantities import deg
from typehaus.quantities.length import ft, m
from typehaus.quantities.point import pt
from typehaus.resolve.mep import _PIPE_SLEEVE_SNAP_M
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
    _rooms,
    _walls,
)
from typehaus.source.macros_geometry import _dist, _project_param
from typehaus.source.macros_openings import (
    _opening_start_offset,
    _opening_width,
    _validate_opening_station,
    place_opening,
)
from typehaus.source.ops import DELETE_FIELD, PatchOp, RawExpr
from typehaus.source.serialize import element_add_op


def move_placeable(plan: PlanModel, storey: str, *, tag: str, position: XY) -> MutationResult:
    """Move a free object, persisting the room containing its new footprint center.

    A drained fixture is not a free object: its waste leaves through a cast-in-place
    :class:`SleevePenetration` and drops into a routed :class:`PipeRun`, and neither of
    those is derived from the fixture — both are authored plan geometry that a drag would
    otherwise leave behind (`_drain_follower_ops`).
    """
    item = _placeable(plan, storey, tag)
    if item is None:
        raise MacroError(f"no placeable {tag!r} on storey {storey!r}")
    x, y = _meters(position[0]), _meters(position[1])
    ops = [PatchOp("update", item.element_kind, tag, {
        "position": _point_expr(position[0], position[1]), "location": DELETE_FIELD,
        "room": _containing_room(plan, storey, (x, y)),
    })]
    followers, warnings = _drain_follower_ops(plan, storey, item, (x, y))
    ops.extend(followers)
    return MutationResult(ops=ops, warnings=warnings)


# --- coupled drain followers -------------------------------------------------
#
# Dragging a floor-drained fixture moves a closet flange, and a closet flange is the top of
# a pipe that is already through the concrete: a pre-pour SleevePenetration at that point
# and a PipeRun dropping through it.  Neither is resolver-derived — both are authored plan
# geometry with their own coordinates — so a bare `position` patch silently decouples them.
# That is the 76c1871 defect: FX-M-BATH2-WC was nudged 6.46" in a drive-by edit, SP-M-WC2
# and PR-B-WC2-DRAIN stayed put, the plan still loaded and built, and only
# `mep.sleeve_alignment` (and one plumbing test) ever said so.  So the move carries them.
#
# A fixture with an authored ``drain_position`` is excluded on purpose: that field *is* the
# author saying where the waste leaves, independently of where the bowl sits, so moving the
# bowl is not a statement about the drain at all (it is how FX-M-BATH1-WC's wall-hung
# carrier stays put while its bowl slides along W-M-BAE).
#
# Followers are searched across the WHOLE plan, not the moved item's storey: the drain of a
# main-floor WC is hung from the basement ceiling, one storey down from the thing that moved.


def _placeable_type(plan: PlanModel, item: object) -> object | None:
    """The fixture/appliance catalog entry behind ``item``, for its service list."""
    return next((entry for entry in (*plan.library.fixture_types, *plan.library.appliance_types)
                 if entry.tag == getattr(item, "type_ref", None)), None)


def _convention_drain_point(plan: PlanModel, storey: str, item: object,
                            at_m: tuple[float, float]) -> tuple[float, float] | None:
    """Where ``item``'s waste would leave the floor if the unit stood at ``at_m``.

    The plan-side mirror of ``resolve/mep_sleeves.py::_expected_drain_point``'s convention branch,
    and it reads the same signal for the same reason: a water closet is the only common
    fixture with no hot-water connection, which makes "no WATER_HOT" the one reliable mark
    of a floor-drained unit (drain under its own footprint) as against a wall-drained one
    (trap arm back to the wet wall it names, so the drain rides that wall's axis).

    It is stated twice rather than imported because the resolver can only answer for the
    position a fixture *has*; a move macro has to answer for the position it is about to
    have, which no resolved model holds.  The authored-``drain_position`` branch is the
    caller's (a fixture that has one never gets here).
    """
    fixture_type = _placeable_type(plan, item)
    if fixture_type is None:
        return None
    if Service.WATER_HOT not in fixture_type.needs:
        return at_m
    wall_ref = getattr(item, "wall_ref", None)
    if wall_ref is None:
        return None
    wall = next((candidate for candidate in _walls(plan, storey)
                 if candidate.tag == wall_ref), None)
    if wall is None:
        return None
    by_tag = {node.tag: node for node in _nodes(plan, storey)}
    start, end = by_tag.get(wall.start_node), by_tag.get(wall.end_node)
    if start is None or end is None:
        return None
    p0, p1 = start.position.xy_m, end.position.xy_m
    t = _project_param(p0, p1, at_m)
    return (p0[0] + t * (p1[0] - p0[0]), p0[1] + t * (p1[1] - p0[1]))


def _drain_follower_ops(plan: PlanModel, storey: str, item: object,
                        new_xy: tuple[float, float]) -> tuple[list[PatchOp], tuple[str, ...]]:
    """Patches that keep a moved fixture's sleeve and drain run under its flange.

    Followers are claimed by proximity to the fixture's OLD drain point, within the same
    ``_PIPE_SLEEVE_SNAP_M`` the resolver uses to decide a routed vertex belongs to a sleeve
    — so the two agree on what "at the flange" means, and a collector that merely *serves*
    the fixture from twenty feet away (PR-B-MAIN-DRAIN serves seventeen of them) is not
    dragged along with it.  Everything found is reported either way: what followed, because
    a cast-in sleeve moving is a fact the author must see, and what did not, because a
    served run left behind is exactly the tie-in that now needs re-cutting by hand.
    """
    if not isinstance(item, (Fixture, Appliance)) or item.drain_position is not None:
        return [], ()
    sleeves = [element for element in plan.elements_of_kind("SleevePenetration")
               if element.serves_fixture == item.tag]
    runs = [element for element in plan.elements_of_kind("PipeRun")
            if item.tag in element.serves]
    if not sleeves and not runs:
        return [], ()

    old_xy = _convention_drain_point(plan, storey, item, item.position.xy_m)
    target_xy = _convention_drain_point(plan, storey, item, new_xy)
    if old_xy is None or target_xy is None:
        # No convention applies (unknown type, or a wall-drained unit naming no wall), so
        # there is no defensible delta.  Say so rather than guess: the drain is now stale.
        return [], (f"{item.tag} moved but its drain point cannot be derived — "
                    f"{', '.join(sorted(element.tag for element in (*sleeves, *runs)))} "
                    "left in place; re-point by hand",)
    dx, dy = target_xy[0] - old_xy[0], target_xy[1] - old_xy[1]
    if abs(dx) < 1e-9 and abs(dy) < 1e-9:
        return [], ()  # a wall-drained unit slid off its wall: the drain point is unchanged

    ops: list[PatchOp] = []
    warnings: list[str] = []
    for sleeve in sleeves:
        gap = _dist(sleeve.position.xy_m, old_xy)
        if gap > _PIPE_SLEEVE_SNAP_M:
            warnings.append(
                f"sleeve {sleeve.tag} serves {item.tag} but sat {m(gap).fmt()} from its old "
                "drain point — left where it was; re-point it by hand")
            continue
        sx, sy = sleeve.position.xy_m
        ops.append(PatchOp("update", "SleevePenetration", sleeve.tag,
                           {"position": _point_expr_m(sx + dx, sy + dy)}))
        warnings.append(
            f"sleeve {sleeve.tag} moved {m(_dist((0, 0), (dx, dy))).fmt()} with {item.tag} — "
            "it is cast in place, so confirm the pour has not happened")
    stayed: list[str] = []
    for run in runs:
        # EVERY vertex at the old point moves, not just the first: a vertical drop is
        # authored as the same plan point repeated with two inverts (path[0] == path[1] on
        # every riser here), so rewriting one of the pair would fold the riser into a slope.
        moved = {index for index, vertex in enumerate(run.path)
                 if _dist(vertex.xy_m, old_xy) <= _PIPE_SLEEVE_SNAP_M}
        if not moved:
            # Normal and expected for most of them — a WC's supply, its vent and the house
            # collector all serve it without ever touching the flange — so these are one
            # line, not one toast each, and they name a distance so a near miss stands out.
            nearest = min((_dist(vertex.xy_m, old_xy) for vertex in run.path), default=None)
            stayed.append(run.tag + (f" ({m(nearest).fmt()} away)" if nearest is not None else ""))
            continue
        vertices: list[str] = []
        for index, vertex in enumerate(run.path):
            if index in moved:
                vx, vy = vertex.xy_m
                vertices.append(_point_expr_m(vx + dx, vy + dy).expr)
            else:
                # Untouched vertices are re-emitted in their authored units, not round-tripped
                # through meters, so a path rewrite never smears the rest of the route.
                vertices.append(f"pt({vertex.x.to_source()}, {vertex.y.to_source()})")
        ops.append(PatchOp("update", "PipeRun", run.tag,
                           {"path": RawExpr("(" + ", ".join(vertices) + ",)")}))
        warnings.append(
            f"run {run.tag} followed {item.tag} ({len(moved)} of {len(run.path)} vertices "
            "re-pointed); its inverts and slope were not re-solved")
    if stayed:
        warnings.append(
            f"{len(stayed)} run(s) serving {item.tag} had no vertex at its old drain point "
            f"and were left as routed — check the tie-ins: {', '.join(stayed)}")
    return ops, tuple(warnings)


def rotate_placeable(plan: PlanModel, storey: str, *, tag: str, degrees: float,
                     free_rotation: bool = False) -> MutationResult:
    item = _placeable(plan, storey, tag)
    if item is None:
        raise MacroError(f"no placeable {tag!r} on storey {storey!r}")
    resolved_degrees = float(degrees) if free_rotation else round(float(degrees) / ROTATION_SNAP_DEGREES) * ROTATION_SNAP_DEGREES
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
                     position: XY | None = None) -> MutationResult:
    item = _placeable(plan, storey, tag)
    if item is None:
        raise MacroError(f"no placeable {tag!r} on storey {storey!r}")
    fields: dict[str, object] = {"location": DELETE_FIELD}
    if position is not None:
        fields["position"] = _point_expr(position[0], position[1])
        fields["room"] = _containing_room(plan, storey, (_meters(position[0]), _meters(position[1])))
    return MutationResult(ops=[PatchOp("update", item.element_kind, tag, fields)])


def retype_placeable(plan: PlanModel, storey: str, *, tag: str,
                     type_ref: str) -> MutationResult:
    """Swap a placeable's product type, keeping its wall-mounted face where it was.

    A bare ``type_ref`` PATCH grows/shrinks the footprint about the authored *center*
    (position is the footprint centroid, ``resolve/placeables.py::_local_footprint``),
    which un-seats a wall-backed unit: the 2026-07-30 shower→tub-shower hand edit had to
    recompute position by hand. This macro does that arithmetic: when both types carry a
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


def duplicate_canvas_object(plan: PlanModel, storey: str, *, tag: str) -> MutationResult:
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
                               kind=getattr(getattr(placeable, "kind", None), "value", None))
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
                op.fields["position"] = RawExpr(f'from_node("{wall.start_node}", {m(station).to_source()})')
                return MutationResult(ops=[op])
            return place_opening(plan, storey, host=wall.tag, type_ref=opening.type_ref,
                                 along=station, is_door=isinstance(opening, Door),
                                 sill=opening.sill_height.meters if opening.sill_height is not None else None,
                                 tag=_copy_tag(plan, tag))
        except MacroError as exc:
            if "does not fit" not in str(exc) and "conflicts" not in str(exc):
                raise
    raise MacroError(f"no non-overlapping station available to duplicate opening {tag!r}")


def place_placeable(plan: PlanModel, storey: str, *, type_ref: str, position: XY,
                    hint_file: str | None = None, tag: str | None = None,
                    kind: str | None = None) -> MutationResult:
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
    selected = next(((cls, list_name, prefix) for collection, cls, list_name, prefix in collection_map
                     if any(product.tag == type_ref for product in getattr(plan.library, collection))), None)
    if selected is None:
        raise MacroError(f"unknown placeable type {type_ref!r}")
    cls, list_name, prefix = selected
    # Project source owns a mixed editable placeables list for each storey.  Keeping all
    # product domains together lets an imported appliance/device use the same journal path.
    list_name = f"{storey.upper()}_PLACEABLES"
    new_tag = tag or _next_tag(list(plan.storey_elements(storey)), prefix)
    common = {"tag": new_tag, "type_ref": type_ref, "position": pt(x, y),
              "room": _containing_room(plan, storey, (x.meters, y.meters))}
    if cls is Equipment:
        item = Equipment(**common, kind=EquipmentKind(kind or EquipmentKind.FURNACE.value), footprint=(ft(2), ft(2)))
    elif cls is Register:
        item = Register(**common, kind=DuctSystem(kind or DuctSystem.SUPPLY.value))
    elif cls is ElectricalDevice:
        item = ElectricalDevice(**common, kind=DeviceKind(kind or DeviceKind.RECEPTACLE.value))
    else:
        item = cls(**common)
    return MutationResult(ops=[element_add_op(item, tag=new_tag, hint_list=list_name,
                                               hint_file=hint_file)])


def _containing_room(plan: PlanModel, storey: str, position: tuple[float, float]) -> str | None:
    """Resolve room faces once at the mutation edge so authored assignment follows a drag.

    A room seed alone is not a boundary, so this deliberately uses the same resolver as the
    canvas.  If a partially authored plan cannot resolve, leaving the claim empty is safer
    than retaining a now-wrong previous room assignment; the normal resolver then reports
    any topology problem as its own finding.
    """
    try:
        from shapely.geometry import Point, Polygon
        from typehaus.resolve import resolve

        model, _ = resolve(plan)
        return next((room.tag for room in model.rooms if room.storey == storey and
                     Polygon(room.clear_face).covers(Point(position))), None)
    except Exception:  # noqa: BLE001 - macros must remain usable while a plan is mid-edit
        return None
