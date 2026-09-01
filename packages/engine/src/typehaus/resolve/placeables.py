"""Resolve one physical placement contract for furniture, fixtures, and MEP devices."""

from __future__ import annotations

import math

# ``shapely`` ships no ``py.typed``. The ``shapely.geometry`` line below does not trip the
# same check, so the ignore is scoped to this one import rather than to the module.
from shapely import get_coordinates  # type: ignore[import-untyped]
from shapely.geometry import Point, Polygon

from typehaus.findings import Finding, Result, Severity, advisory
from typehaus.model.plan import PlanModel
from typehaus.resolve.model import ResolvedCanvasObject, ResolvedModel, Ring
from typehaus.resolve.placeable_clear_floor_obstruction import (
    CLEAR_FLOOR_SPACE_OBSTRUCTION_THRESHOLDS,
    ClearFloorSpaceObstruction,
    PlaceableBodyProfile,
    clear_floor_space_obstruction,
)
from typehaus.resolve.placeable_groups import PlacementGroupAnchorZone, assign_placement_groups
from typehaus.resolve.room_floor import room_floor_elevation

_TYPE_COLLECTIONS = (
    ("furniture_types", "Furniture", "furniture"),
    ("fixture_types", "Fixture", "plumbing"),
    ("appliance_types", "Appliance", "appliance"),
    ("equipment_types", "Equipment", "mechanical"),
    ("register_types", "Register", "mechanical"),
    ("electrical_device_types", "ElectricalDevice", "electrical"),
)


def resolve_placeables(plan: PlanModel, model: ResolvedModel) -> list[Finding]:
    """Resolve transformed footprints, wall-face attachments, and room containment."""
    findings: list[Finding] = []
    types = {item.tag: (item, domain) for collection, _, domain in _TYPE_COLLECTIONS
             for item in getattr(plan.library, collection)}
    kind_domains = {kind: domain for _, kind, domain in _TYPE_COLLECTIONS}
    # Objects are collected before they are published: a placeable's furniture group depends
    # on the peers standing in its zone, so no object's record is final until all are placed.
    resolved_objects: list[ResolvedCanvasObject] = []
    anchor_zones: list[PlacementGroupAnchorZone] = []
    # Whether each body actually stands in a clear floor space, keyed by uid. Built here
    # because it needs the product type, which the resolved record deliberately does not carry.
    obstruction_by_uid: dict[str, ClearFloorSpaceObstruction] = {}
    # The profile the verdict above was computed from, kept rather than discarded: the
    # over-the-fixture exemption in ``_clearance_conflicts`` needs a *pair* of bodies, and
    # ``ClearFloorSpaceObstruction`` is a per-body answer with the numbers already spent.
    profiles_by_uid: dict[str, PlaceableBodyProfile] = {}
    # ``room_floor_elevation`` walks every wall and slab, so the answer is memoised per room
    # tag — a hundred placeables in the same room ask the same question.
    floor_by_room: dict[str, float] = {}
    for storey in plan.storeys:
        # One shape per room, not one per (room, placeable): this was rebuilding every room's
        # polygon for every placeable on the storey (~1,700 GEOS polygon builds per resolve).
        # The bounds ride along so the common far-away case never reaches ``covers``.
        room_shapes: list[tuple[str, Polygon, _Bounds]] = []
        for room in model.rooms:
            if room.storey == storey.tag:
                shape = Polygon(room.clear_face)
                room_shapes.append((room.tag, shape, shape.bounds))
        for item in plan.storey_elements(storey.tag):
            domain = kind_domains.get(item.element_kind)
            if domain is None:
                continue
            type_ref = getattr(item, "type_ref", None)
            type_entry = types.get(type_ref)
            product_type = type_entry[0] if type_entry is not None else None
            if (product_type is None
                    and item.element_kind not in {"Equipment", "Register",
                                                  "ElectricalDevice"}):
                findings.append(_finding(
                    "integrity.unknown_placeable_type", item.tag,
                    f"placeable {item.tag} references missing type {type_ref!r}"))
                continue
            center, rotation, attachment, attachment_face = _resolve_location(
                item, product_type, model, findings)
            if center is None:
                continue
            local_footprint = _local_footprint(product_type, item)
            footprint = _transformed_polygon(local_footprint, center, rotation)
            resolved_room = _containing_room(room_shapes, center)
            explicit_room = getattr(item, "room", None)
            # Mount heights are measured off the floor the thing stands on, which is the
            # storey datum everywhere except where a room's slab is filed on another storey
            # (→ resolve/room_floor.py). Resolved before the elevation, not after, because the
            # elevation depends on it.
            floor = _floor_elevation(model, storey, explicit_room or resolved_room,
                                     floor_by_room)
            mount_elevation = resolved_mount_elevation(
                storey, item, floor_m=floor,
                soffit_underside_m=_soffit_underside(model, item))
            profile = _body_profile(product_type, item, floor, mount_elevation, local_footprint)
            profiles_by_uid[item.uid] = profile
            obstruction_by_uid[item.uid] = clear_floor_space_obstruction(profile)
            if (explicit_room is not None and explicit_room != resolved_room
                    and not _set_into_room_wall(item, explicit_room, center, model, room_shapes)):
                findings.append(_finding("integrity.placeable_room_mismatch", item.tag,
                    f"placeable {item.tag} is assigned to {explicit_room} but its "
                    "footprint center is outside that room",
                    Severity.WARN))
            zones = _resolved_clearance_zones(
                product_type, center, rotation, plan.project.active_code_profile,
            )
            resolved_objects.append(ResolvedCanvasObject(
                uid=item.uid, tag=item.tag, storey=storey.tag, domain=domain,
                kind=item.element_kind, type_ref=type_ref,
                room=explicit_room or resolved_room, position=center, rotation_degrees=rotation,
                z_m=mount_elevation,
                footprint=footprint,
                required_clearances=tuple(ring for zone, ring in zones if _is_required(zone)),
                recommended_clearances=tuple(
                    ring for zone, ring in zones if not _is_required(zone)),
                attachment_wall=attachment, attachment_face=attachment_face,
                circuit=getattr(item, "circuit", None),
                mount=getattr(item, "mount", None),
            ))
            anchor_zones.extend(
                PlacementGroupAnchorZone(anchor_uid=item.uid, anchor_tag=item.tag,
                                         storey=storey.tag, zone_polygon=ring,
                                         occupant_types=frozenset(zone.occupant_types))
                for zone, ring in zones if zone.occupant_types and not _is_required(zone))
    model.canvas_objects.extend(assign_placement_groups(resolved_objects, anchor_zones))
    # One shape per placed object, shared by both conflict passes: each was building its own
    # copy of the same ~300 footprints, and the per-pair rebuild inside them was ~800 more.
    footprints = {obj.uid: Polygon(obj.footprint) for obj in model.canvas_objects}
    findings.extend(_clearance_conflicts(model, obstruction_by_uid, footprints, profiles_by_uid))
    findings.extend(_door_swing_conflicts(model, obstruction_by_uid, footprints))
    return findings


_Bounds = tuple[float, float, float, float]

#: How far a room's clear face may stand off the wall solid bounding it and still count as
#: bounded by it. The clear face is built from those wall faces, so the true answer is zero;
#: the allowance only absorbs the finish-face rounding that a resolved polygon carries.
_WALL_BOUNDS_ROOM_M = 0.01


def _set_into_room_wall(item: object, room_tag: str, center: tuple[float, float],
                        model: ResolvedModel,
                        room_shapes: list[tuple[str, Polygon, _Bounds]]) -> bool:
    """True when the placeable is set INTO a wall that bounds the room it names.

    A wall hydrant pierces the wall between its room and the weather: the escutcheon is
    outdoors, so the footprint centre is *necessarily* outside the room, and the room behind
    the wall is still the true answer for the permit fixture schedule
    (``advisory.fixture_room_unassigned`` is what asks for it). Reporting that as a room
    mismatch asks the author to choose between two findings rather than to fix anything.

    Both halves of the claim are checked, so an ordinary drag error still reports: the body
    has to stand in the wall it names, and that wall has to bound the room it names. A
    placeable pulled off its host, or one naming a wall on the far side of the house, fails
    the first test; one set into a wall of some other room fails the second.
    """
    wall = model.wall(getattr(item, "wall_ref", None) or "")
    if wall is None:
        return False
    rings = [Polygon(layer.polygon) for layer in wall.layers if len(layer.polygon) >= 3]
    point = Point(center)
    if not any(ring.covers(point) for ring in rings):
        return False
    shape = next((s for tag, s, _bounds in room_shapes if tag == room_tag), None)
    return shape is not None and any(shape.distance(ring) <= _WALL_BOUNDS_ROOM_M
                                     for ring in rings)


def _containing_room(room_shapes: list[tuple[str, Polygon, _Bounds]],
                     center: tuple[float, float]) -> str | None:
    """Tag of the first room whose clear face covers ``center``, in ``model.rooms`` order."""
    x, y = center
    point = None
    for tag, shape, (min_x, min_y, max_x, max_y) in room_shapes:
        if not (min_x <= x <= max_x and min_y <= y <= max_y):
            continue
        if point is None:
            point = Point(center)
        if shape.covers(point):
            return tag
    return None


def _floor_elevation(model: ResolvedModel, storey: object, room_tag: str | None,
                     cache: dict[str, float]) -> float:
    """The absolute Z of the floor a placeable in ``room_tag`` stands on."""
    if room_tag is None:
        return storey.elevation.meters
    if room_tag not in cache:
        room = next((r for r in model.rooms if r.tag == room_tag), None)
        cache[room_tag] = (storey.elevation.meters if room is None
                           else room_floor_elevation(model, room))
    return cache[room_tag]


def _soffit_underside(model: ResolvedModel, item: object) -> float | None:
    """The clear underside of the ``Soffit`` a placeable names, if it names one.

    The *clear* underside — inside the lining and the ladder's bottom rail — not the
    finished face of the box: a machine hung in a soffit sits on the framing, not on the
    gypsum. Unnamed, or naming a soffit that does not resolve, gives None and the caller
    falls back to the storey ceiling exactly as before; a dangling ``soffit_ref`` is
    reported by ``mep.duct_soffit_occupancy``, not silently here.
    """
    from typehaus.resolve.framing.soffit import soffit_clear_section

    ref = getattr(item, "soffit_ref", None)
    if not ref:
        return None
    soffit = next((s for s in model.soffits if s.tag == ref), None)
    if soffit is None:
        return None
    section = soffit_clear_section(soffit)
    return soffit.z0_m if section is None else section.z[0]


def resolved_mount_elevation(storey: object, item: object,
                             floor_m: float | None = None,
                             soffit_underside_m: float | None = None) -> float:
    """The one project-frame Z for a placeable — glTF, the UI, and IFC all read this.

    ``Mount`` is the single authoritative height contract: an explicit ``elevation`` is a
    floor-relative height and wins outright, because a ceiling-mounted fixture hung at a
    stated 8' must stay at 8' whatever the storey's default ceiling height is. Only a
    ceiling mount with no stated elevation falls back to hanging off the ceiling plane.

    ``floor_m`` is the plane those heights are measured from. It defaults to the storey
    datum, which is the same thing for every room whose slab is filed on its own storey;
    ``resolve_placeables`` passes the room's actual floor instead (→ resolve/room_floor.py),
    which is what keeps the Catlin garage's contents on the slab at grade rather than 22"
    up in the air on the ICF stem top the storey datum sits at. Callers holding an element
    that is not in a room — a PipeRun, an unplaced device — keep the storey default, which
    is what their authored elevations have always meant.

    ``soffit_underside_m`` is the *other* plane a ceiling mount can hang from, and it exists
    because the fallback above was wrong for everything installed in a dropped box: an air
    handler concealed inside a 14" duct soffit was resolving at the 9'-0" storey ceiling,
    fourteen inches above the box every comment in the plan says it lives in — and the strip
    heater in the same soffit with it. ``resolve_placeables`` passes it whenever the item
    names a modeled ``Soffit`` through ``soffit_ref``. This is the second time
    ``default_ceiling_height`` has been the wrong plane for a consumer that had no way to say
    so (→ resolve/ceiling_over.py, which fixed it for the room-height side and for that
    consumer only); it is fixed here for placeables, in the one function they all go through.
    """
    mount = getattr(item, "mount", None)
    floor = storey.elevation.meters if floor_m is None else floor_m
    if mount is None:
        return floor
    if mount.elevation is not None:
        return floor + mount.elevation.meters
    if mount.kind.value == "ceiling":
        drop = mount.drop.meters if mount.drop is not None else 0.0
        plane = (floor + storey.default_ceiling_height.meters
                 if soffit_underside_m is None else soffit_underside_m)
        return plane - drop
    return floor


def _body_profile(product_type: object | None, item: object, floor_m: float,
                  mount_elevation_m: float,
                  local_footprint: list[tuple[float, float]]) -> PlaceableBodyProfile:
    """Measure the placeable's solid against the floor it stands on.

    ``resolved_mount_elevation`` gives the *base* of the body, so the band is
    ``[base, base + height]`` — except for a recessed floor mount, whose body drops into the
    floor cavity and whose face lands flush, making the band ``[base - height, base]``. A
    recessed wall mount reaches nothing into the room for the same reason.
    """
    mount = getattr(item, "mount", None)
    mount_kind = mount.kind.value if mount is not None else "floor"
    recessed = bool(getattr(mount, "recessed_into_host_surface", False))
    height = getattr(product_type, "height", None)
    body_height_m = height.meters if height is not None else None
    base_above_floor_m = mount_elevation_m - floor_m
    if recessed and mount_kind == "floor" and body_height_m is not None:
        base_above_floor_m -= body_height_m
    projection_m = None
    if mount_kind == "wall":
        # Local ``-y`` is the room-facing front of every authored placeable footprint
        # (→ library/placeables/_zones), so the local y extent is how far a wall-mounted body
        # reaches off its wall — the dimension A117.1 §307.2 caps.
        projection_m = 0.0 if recessed else _local_depth_extent(local_footprint)
    return PlaceableBodyProfile(base_above_storey_floor_m=base_above_floor_m,
                                body_height_m=body_height_m,
                                horizontal_projection_from_wall_m=projection_m)


def _local_depth_extent(local_footprint: list[tuple[float, float]]) -> float:
    depths = [y for _, y in local_footprint]
    return max(depths) - min(depths) if depths else 0.0


def _resolve_location(
    item: object, product_type: object | None, model: ResolvedModel,
    findings: list[Finding],
) -> tuple[tuple[float, float] | None, float, str | None, str | None]:
    location = getattr(item, "location", None)
    attachment = location.attachment if location is not None else None
    rotation = _degrees(getattr(location, "rotation", None) if location is not None else None)
    rotation = _degrees(getattr(item, "rotation", None)) if rotation == 0 else rotation
    if attachment is None:
        point = (location.position
                 if location is not None and location.position is not None
                 else getattr(item, "position", None))
        return (point.xy_m if point is not None else None), rotation, None, None
    wall = model.wall(attachment.wall_ref)
    if wall is None:
        findings.append(_finding(
            "integrity.orphan_wall_attachment", item.tag,
            f"placeable {item.tag} attaches to missing wall {attachment.wall_ref}"))
        return None, rotation, attachment.wall_ref, attachment.face
    (x0, y0), (x1, y1) = wall.axis
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy)
    if length < 1e-9:
        findings.append(_finding("integrity.invalid_wall_attachment", item.tag,
                                 f"placeable {item.tag} cannot attach to a zero-length wall"))
        return None, rotation, wall.tag, attachment.face
    tangent = (dx / length, dy / length)
    left = (-tangent[1], tangent[0])
    sign = 1 if attachment.face == "left" else -1
    distance = max(0.0, min(length, attachment.distance_from_start.meters))
    # Layer vertices encode the resolved finish assembly, so their extreme normal offset
    # tracks thickness changes without storing a fragile authored wall-depth number.
    offsets = [(point[0] - x0) * left[0] + (point[1] - y0) * left[1]
               for layer in wall.layers for point in layer.polygon]
    finish_offset = (max(offsets) if sign > 0 else min(offsets)) if offsets else 0.0
    gap = attachment.normal_gap.meters
    resolved_rotation = (math.degrees(math.atan2(tangent[1], tangent[0]))
                         + _degrees(attachment.rotation_offset))
    # Align the *nearest footprint edge*, not its center, to the resolved finish face.
    # Project the rotated local polygon onto the wall's left-normal: left attachments use
    # the minimum (wallward) edge; right attachments use the maximum edge.
    radians = math.radians(resolved_rotation)
    cos, sin = math.cos(radians), math.sin(radians)
    normal_projections = [(px * cos - py * sin) * left[0] + (px * sin + py * cos) * left[1]
                          for px, py in _local_footprint(product_type, item)]
    wallward_edge = min(normal_projections) if sign > 0 else max(normal_projections)
    center_offset = finish_offset + sign * gap - wallward_edge
    return ((x0 + tangent[0] * distance + left[0] * center_offset,
             y0 + tangent[1] * distance + left[1] * center_offset),
            resolved_rotation, wall.tag, attachment.face)


def _local_footprint(product_type: object | None, item: object) -> list[tuple[float, float]]:
    shape = getattr(product_type, "footprint_shape", None)
    if shape is not None:
        return [point.xy_m for point in shape.points]
    footprint = getattr(product_type, "footprint", getattr(item, "footprint", None))
    if footprint is None:
        return [(-0.225, -0.225), (0.225, -0.225), (0.225, 0.225), (-0.225, 0.225)]
    width, depth = (part.meters for part in footprint)
    return [(-width / 2, -depth / 2), (width / 2, -depth / 2),
            (width / 2, depth / 2), (-width / 2, depth / 2)]


def _is_required(zone: object) -> bool:
    return zone.policy.value == "required"


def _resolved_clearance_zones(product_type: object | None, center: tuple[float, float],
                              rotation: float,
                              active_code_profile: str | None) -> list[tuple[object, Ring]]:
    """Each clearance zone that applies to the active code profile, with its project ring.

    The zone object is kept alongside its geometry so callers can read ``policy`` and
    ``occupant_types`` without re-walking the product type.
    """
    if product_type is None:
        return []
    return [
        (zone, _transformed_polygon([point.xy_m for point in zone.footprint.points],
                                    center, rotation))
        for zone in getattr(product_type, "clearances", ())
        if zone.code_profile is None or zone.code_profile == active_code_profile
    ]


def _local_y_values(geometry: object, center: tuple[float, float],
                    rotation: float) -> list[float]:
    """Every vertex of ``geometry`` expressed as a depth in the owner's own frame.

    The inverse of the rotation ``_transformed_polygon`` applies, taking only the component
    that matters here: ``+y`` runs toward the object's back (the frame convention documented
    at resolve/mep_sleeves.py). Minimising a linear functional over a polygon is attained at a
    vertex, so reading the coordinates is exact — and ``shapely.get_coordinates`` walks the
    multipart geometry that ``zone − owner footprint`` routinely produces.
    """
    radians = math.radians(rotation)
    cos, sin = math.cos(radians), math.sin(radians)
    return [-(px - center[0]) * sin + (py - center[1]) * cos
            for px, py in get_coordinates(geometry)]


def _mounted_over_the_fixture(item: ResolvedCanvasObject, peer: ResolvedCanvasObject,
                              overlap: object, own_footprint: Polygon,
                              profiles: dict[str, PlaceableBodyProfile]) -> bool:
    """A body hung above a fixture, beside or behind it, takes none of its use space.

    UPC 402.5's 15 in is elbow room for someone SEATED on the fixture and its 24 in is
    standing room in front of it. Both are measured through a person, not up to the ceiling,
    so a body whose lowest edge is above the fixture's own can reduce neither — which is why
    stock over-toilet storage is 24-30 in wide and 8-12 in DEEP and is built without comment.
    The A117.1 protrusion allowance the obstruction test offers instead is an accessibility
    limit, and Minn. R. 1341 does not reach a detached one- or two-family dwelling. A117.1
    §604.3.2 says the same thing positively: grab bars, dispensers, coat hooks and *shelves*
    are permitted to overlap the clearance around a water closet.

    The last condition is what keeps the check honest: a cabinet on the wall someone FACES
    from the fixture is in front of it, is walked into, and still reports.

    ``item.kind == "Fixture"`` is a **proxy**, and an acknowledged one — the obstruction test
    it sits beside promises to be about geometry, never about domain. It is the only axis
    available: ``ResolvedCanvasObject`` carries ``required_clearances`` as bare rings, having
    dropped ``policy``, ``code_profile`` and ``purpose``. The honest model is a
    ``ClearanceZone`` field separating body space from keep-out; scoping to fixtures leaves
    the catalogue's other required zone — ``EQ-T-ESS-BATT``'s separation band, which is about
    heat and fire spread, not use space — graded exactly as before.
    """
    own = profiles.get(item.uid)
    hung = profiles.get(peer.uid)
    if own is None or hung is None:
        return False
    if hung.horizontal_projection_from_wall_m is None:
        return False  # not wall-mounted: it stands on the floor the fixture's user needs
    if own.body_height_m is None:
        return False  # an unknown body is never assumed short enough
    own_top_m = own.base_above_storey_floor_m + own.body_height_m
    if hung.base_above_storey_floor_m < own_top_m - 1e-9:
        return False
    front_m = min(_local_y_values(own_footprint, item.position, item.rotation_degrees))
    return min(_local_y_values(overlap, item.position, item.rotation_degrees)) >= front_m - 1e-9


def _clearance_conflicts(model: ResolvedModel,
                         obstruction_by_uid: dict[str, ClearFloorSpaceObstruction],
                         footprints: dict[str, Polygon],
                         profiles_by_uid: dict[str, PlaceableBodyProfile]) -> list[Finding]:
    """Report use-space encroachments without rejecting the drag that created one.

    A clearance is an occupied planning zone, so compare it against other physical
    footprints rather than their own clearance zones.  That avoids false conflicts
    between two deliberately overlapping advisory envelopes.

    Plan overlap is necessary but not sufficient: the peer's *body* has to stand in the zone's
    clear floor space (→ resolve/placeable_clear_floor_obstruction). That vertical test is
    physics and so applies to required and recommended zones alike.

    Members of one furniture group (→ resolve/placeable_groups) are exempt from each other's
    *recommended* zones: the chairs tucked under a dining table are what its chair-use zone is
    for. A required zone is a code minimum and is never exempted — grouping describes intent,
    not permission.

    Two more things a zone is not. It is not the space its *owner* stands in: a
    ``surround_zone`` is authored as the whole enlarged rectangle, so the owner's own
    footprint is subtracted before comparing, and a pendant hung over the table it lights
    stops reading as an encroachment on that table's chair-use margin. And it does not reach
    through a partition: a zone drawn past a wall into the next room is already stopped by the
    wall, so a peer standing in a different room is not encroaching on it. And a third: a
    zone is not a column of air — a body hung on the wall above a fixture, beside or behind
    it, takes none of that fixture's use space (→ ``_mounted_over_the_fixture``).
    """
    findings: list[Finding] = []
    peers_by_key = _obstructing_peers_by_key(model, obstruction_by_uid)
    for item in model.canvas_objects:
        # A list, not a generator: this is re-walked once per zone, and a generator was
        # exhausted by the first one — every zone after an object's first was silently never
        # compared against anything (a bed's second side-access zone, a fridge's swing).
        peers = [peer for peer in peers_by_key[(item.storey, item.room)]
                 if peer.uid != item.uid]
        own_footprint = footprints[item.uid]
        for zones, severity, policy_name in (
            (item.required_clearances, Severity.ERROR, "required"),
            (item.recommended_clearances, Severity.WARN, "recommended"),
        ):
            group_exempt = severity is Severity.WARN and item.placement_group is not None
            over_fixture_exempt = severity is Severity.ERROR and item.kind == "Fixture"
            for zone in zones:
                zone_shape = Polygon(zone)
                if zone_shape.is_valid and own_footprint.is_valid:
                    zone_shape = zone_shape.difference(own_footprint)
                if zone_shape.is_empty or not zone_shape.is_valid:
                    continue
                zone_min_x, zone_min_y, zone_max_x, zone_max_y = zone_shape.bounds
                for peer in peers:
                    if group_exempt and peer.placement_group == item.placement_group:
                        continue
                    peer_shape = footprints[peer.uid]
                    # Disjoint bounding boxes cannot intersect, so this skips the GEOS call
                    # for the overwhelming majority of pairs without changing any answer.
                    min_x, min_y, max_x, max_y = peer_shape.bounds
                    if (max_x < zone_min_x or min_x > zone_max_x
                            or max_y < zone_min_y or min_y > zone_max_y):
                        continue
                    overlap = zone_shape.intersection(peer_shape)
                    if overlap.area <= 1e-8:
                        continue
                    if over_fixture_exempt and _mounted_over_the_fixture(
                            item, peer, overlap, own_footprint, profiles_by_uid):
                        continue
                    findings.append(Finding(
                        severity=severity,
                        check_id=f"integrity.placeable_{policy_name}_clearance_conflict",
                        message=(f"{policy_name} clearance for {item.tag} conflicts with "
                                 f"physical footprint of {peer.tag}: "
                                 f"{obstruction_by_uid[peer.uid].reason}"),
                        element_tags=(item.tag, peer.tag),
                        code_ref=CLEAR_FLOOR_SPACE_OBSTRUCTION_THRESHOLDS.source,
                        result=Result.FAIL if severity is Severity.ERROR else Result.UNKNOWN,
                    ))
    return findings


def _obstructing_peers_by_key(model: ResolvedModel,
                              obstruction_by_uid: dict[str, ClearFloorSpaceObstruction],
                              ) -> dict[tuple[str, str | None], list[ResolvedCanvasObject]]:
    """Candidate peers for every ``(storey, room)`` an object can occupy, in model order.

    A peer only counts if it stands on the same storey, actually obstructs, and is not
    separated from the object by construction. Rooms are resolved from the wall faces that
    bound them, so two different room tags on one storey mean a partition (or a chase, or a
    stair well) stands between the two bodies: the 18" of side access a bed wants is not
    taken by the wardrobe standing on the *other* side of the bedroom wall, and reporting it
    as taken sends the reader to a room where nothing is wrong. ``None`` on either side means
    the object resolved to no room at all (a porch light, a body standing in a doorway),
    which is not evidence of separation — those still compare.

    All three conditions read only ``(storey, room)``, so the answer is shared by every
    object with that key instead of being recomputed per pair — the per-item filter was
    O(objects^2) with a dict lookup and a predicate call per pair. Self-exclusion is the
    caller's one remaining per-item step. Lists stay in ``model.canvas_objects`` order so the
    findings come out in exactly the order the per-item scan produced them.
    """
    obstructing: dict[str, list[ResolvedCanvasObject]] = {}
    for obj in model.canvas_objects:
        if obstruction_by_uid[obj.uid].obstructs:
            obstructing.setdefault(obj.storey, []).append(obj)
    out: dict[tuple[str, str | None], list[ResolvedCanvasObject]] = {}
    for obj in model.canvas_objects:
        key = (obj.storey, obj.room)
        if key in out:
            continue
        out[key] = [peer for peer in obstructing.get(obj.storey, ())
                    if obj.room is None or peer.room is None or peer.room == obj.room]
    return out


def _door_swing_conflicts(model: ResolvedModel,
                          obstruction_by_uid: dict[str, ClearFloorSpaceObstruction],
                          footprints: dict[str, Polygon]) -> list[Finding]:
    """Door leaf sweeps are advisory overlays: flag encroachments without blocking edits.

    The sweep is a plan polygon but a leaf is not infinitely tall: it stops at the head.
    A body whose base sits at or above that head is not in the leaf's way — a recessed can
    at the 9' ceiling plane cannot obstruct a 6'-8" door, and reporting that it does trains
    the reader to skip the whole check.

    Below the head the same three-dimensional question applies as to a clearance zone, and it
    has the same published answer, so the obstruction test is shared rather than re-derived
    (→ resolve/placeable_clear_floor_obstruction). A leaf passes over a flush floor register
    and clears a switch plate proud of its own wall by 2"; only a body that really stands in
    the sweep stops the door.
    """
    findings: list[Finding] = []
    wall_by_tag = {wall.tag: wall for wall in model.walls}
    for opening in model.openings:
        if not opening.swing_clearance:
            continue
        wall = wall_by_tag.get(opening.host_wall)
        if wall is None:
            continue
        leaf_head_m = wall.base_ref_z_m + opening.sill_m + opening.height_m
        swing = Polygon(opening.swing_clearance)
        swing_min_x, swing_min_y, swing_max_x, swing_max_y = swing.bounds
        for item in model.canvas_objects:
            if item.storey != wall.storey or item.z_m >= leaf_head_m - 1e-6:
                continue
            if not obstruction_by_uid[item.uid].obstructs:
                continue
            item_shape = footprints[item.uid]
            min_x, min_y, max_x, max_y = item_shape.bounds
            # Disjoint bounding boxes cannot intersect — a cheap exact prefilter.
            if (max_x < swing_min_x or min_x > swing_max_x
                    or max_y < swing_min_y or min_y > swing_max_y):
                continue
            if swing.intersection(item_shape).area <= 1e-8:
                continue
            findings.append(Finding(
                severity=Severity.WARN, check_id="integrity.door_swing_conflict",
                message=f"door swing for {opening.tag} conflicts with physical "
                        f"footprint of {item.tag}",
                element_tags=(opening.tag, item.tag), result=Result.UNKNOWN,
            ))
    return findings


def _transformed_polygon(points: list[tuple[float, float]], center: tuple[float, float],
                         rotation: float) -> list[tuple[float, float]]:
    radians = math.radians(rotation)
    cos, sin = math.cos(radians), math.sin(radians)
    return [(center[0] + x * cos - y * sin, center[1] + x * sin + y * cos) for x, y in points]


def _degrees(value: object | None) -> float:
    return float(getattr(value, "degrees", 0.0))


def _finding(check_id: str, tag: str, message: str, severity: Severity = Severity.ERROR) -> Finding:
    return advisory(check_id, message, (tag,),
                    Result.FAIL if severity is Severity.ERROR else Result.UNKNOWN,
                    severity=severity)
