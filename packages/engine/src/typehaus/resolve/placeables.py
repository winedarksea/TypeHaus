"""Resolve one physical placement contract for furniture, fixtures, and MEP devices."""

from __future__ import annotations

import math

from shapely.geometry import Point, Polygon

from typehaus.findings import Finding, Result, Severity
from typehaus.model.plan import PlanModel
from typehaus.resolve.model import ResolvedCanvasObject, ResolvedModel, Ring
from typehaus.resolve.placeable_clear_floor_obstruction import (
    CLEAR_FLOOR_SPACE_OBSTRUCTION_THRESHOLDS, ClearFloorSpaceObstruction,
    PlaceableBodyProfile, clear_floor_space_obstruction)
from typehaus.resolve.placeable_groups import (PlacementGroupAnchorZone,
                                               assign_placement_groups)

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
    for storey in plan.storeys:
        rooms = [room for room in model.rooms if room.storey == storey.tag]
        for item in plan.storey_elements(storey.tag):
            domain = kind_domains.get(item.element_kind)
            if domain is None:
                continue
            type_ref = getattr(item, "type_ref", None)
            type_entry = types.get(type_ref)
            product_type = type_entry[0] if type_entry is not None else None
            if product_type is None and item.element_kind not in {"Equipment", "Register", "ElectricalDevice"}:
                findings.append(_finding("integrity.unknown_placeable_type", item.tag,
                                         f"placeable {item.tag} references missing type {type_ref!r}"))
                continue
            center, rotation, attachment, attachment_face = _resolve_location(item, product_type, model, findings)
            if center is None:
                continue
            local_footprint = _local_footprint(product_type, item)
            footprint = _transformed_polygon(local_footprint, center, rotation)
            mount_elevation = resolved_mount_elevation(storey, item)
            obstruction_by_uid[item.uid] = clear_floor_space_obstruction(
                _body_profile(product_type, item, storey, mount_elevation, local_footprint))
            resolved_room = next((room.tag for room in rooms if Polygon(room.clear_face).covers(Point(center))), None)
            explicit_room = getattr(item, "room", None)
            if explicit_room is not None and explicit_room != resolved_room:
                findings.append(_finding("integrity.placeable_room_mismatch", item.tag,
                    f"placeable {item.tag} is assigned to {explicit_room} but its footprint center is outside that room",
                    Severity.WARN))
            zones = _resolved_clearance_zones(
                product_type, center, rotation, plan.project.active_code_profile,
            )
            resolved_objects.append(ResolvedCanvasObject(
                uid=item.uid, tag=item.tag, storey=storey.tag, domain=domain, kind=item.element_kind, type_ref=type_ref,
                room=explicit_room or resolved_room, position=center, rotation_degrees=rotation,
                z_m=mount_elevation,
                footprint=footprint,
                required_clearances=tuple(ring for zone, ring in zones if _is_required(zone)),
                recommended_clearances=tuple(ring for zone, ring in zones if not _is_required(zone)),
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
    findings.extend(_clearance_conflicts(model, obstruction_by_uid))
    findings.extend(_door_swing_conflicts(model))
    return findings


def resolved_mount_elevation(storey: object, item: object) -> float:
    """The one project-frame Z for a placeable — glTF, the UI, and IFC all read this.

    ``Mount`` is the single authoritative height contract: an explicit ``elevation`` is a
    storey-relative height and wins outright, because a ceiling-mounted fixture hung at a
    stated 8' must stay at 8' whatever the storey's default ceiling height is. Only a
    ceiling mount with no stated elevation falls back to hanging off the ceiling plane.
    """
    mount = getattr(item, "mount", None)
    floor = storey.elevation.meters
    if mount is None:
        return floor
    if mount.elevation is not None:
        return floor + mount.elevation.meters
    if mount.kind.value == "ceiling":
        drop = mount.drop.meters if mount.drop is not None else 0.0
        return floor + storey.default_ceiling_height.meters - drop
    return floor


def _body_profile(product_type: object | None, item: object, storey: object,
                  mount_elevation_m: float,
                  local_footprint: list[tuple[float, float]]) -> PlaceableBodyProfile:
    """Measure the placeable's solid against the floor of the storey it stands on.

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
    base_above_floor_m = mount_elevation_m - storey.elevation.meters
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


def _resolve_location(item: object, product_type: object | None, model: ResolvedModel,
                      findings: list[Finding]) -> tuple[tuple[float, float] | None, float, str | None, str | None]:
    location = getattr(item, "location", None)
    attachment = location.attachment if location is not None else None
    rotation = _degrees(getattr(location, "rotation", None) if location is not None else None)
    rotation = _degrees(getattr(item, "rotation", None)) if rotation == 0 else rotation
    if attachment is None:
        point = location.position if location is not None and location.position is not None else getattr(item, "position", None)
        return (point.xy_m if point is not None else None), rotation, None, None
    wall = model.wall(attachment.wall_ref)
    if wall is None:
        findings.append(_finding("integrity.orphan_wall_attachment", item.tag,
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
    resolved_rotation = math.degrees(math.atan2(tangent[1], tangent[0])) + _degrees(attachment.rotation_offset)
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
    return [(-width / 2, -depth / 2), (width / 2, -depth / 2), (width / 2, depth / 2), (-width / 2, depth / 2)]


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


def _clearance_conflicts(model: ResolvedModel,
                         obstruction_by_uid: dict[str, ClearFloorSpaceObstruction]) -> list[Finding]:
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
    """
    findings: list[Finding] = []
    for item in model.canvas_objects:
        # A list, not a generator: this is re-walked once per zone, and a generator was
        # exhausted by the first one — every zone after an object's first was silently never
        # compared against anything (a bed's second side-access zone, a fridge's swing).
        peers = [peer for peer in model.canvas_objects
                 if peer.storey == item.storey and peer.uid != item.uid
                 and obstruction_by_uid[peer.uid].obstructs]
        for zones, severity, policy_name in (
            (item.required_clearances, Severity.ERROR, "required"),
            (item.recommended_clearances, Severity.WARN, "recommended"),
        ):
            group_exempt = severity is Severity.WARN and item.placement_group is not None
            for zone in zones:
                zone_shape = Polygon(zone)
                if zone_shape.is_empty or not zone_shape.is_valid:
                    continue
                for peer in peers:
                    if group_exempt and peer.placement_group == item.placement_group:
                        continue
                    overlap = zone_shape.intersection(Polygon(peer.footprint))
                    if overlap.area <= 1e-8:
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


def _door_swing_conflicts(model: ResolvedModel) -> list[Finding]:
    """Door leaf sweeps are advisory overlays: flag encroachments without blocking edits.

    The sweep is a plan polygon but a leaf is not infinitely tall: it stops at the head.
    A body whose base sits at or above that head is not in the leaf's way — a recessed can
    at the 9' ceiling plane cannot obstruct a 6'-8" door, and reporting that it does trains
    the reader to skip the whole check.
    """
    findings: list[Finding] = []
    wall_by_tag = {wall.tag: wall for wall in model.walls}
    for opening in model.openings:
        if not opening.swing_clearance:
            continue
        wall = wall_by_tag.get(opening.host_wall)
        if wall is None:
            continue
        leaf_head_m = wall.z0_m + opening.sill_m + opening.height_m
        swing = Polygon(opening.swing_clearance)
        for item in model.canvas_objects:
            if item.storey != wall.storey or item.z_m >= leaf_head_m - 1e-6:
                continue
            if swing.intersection(Polygon(item.footprint)).area <= 1e-8:
                continue
            findings.append(Finding(
                severity=Severity.WARN, check_id="integrity.door_swing_conflict",
                message=f"door swing for {opening.tag} conflicts with physical footprint of {item.tag}",
                element_tags=(opening.tag, item.tag), result=Result.UNKNOWN,
            ))
    return findings


def _transformed_polygon(points: list[tuple[float, float]], center: tuple[float, float], rotation: float) -> list[tuple[float, float]]:
    radians = math.radians(rotation)
    cos, sin = math.cos(radians), math.sin(radians)
    return [(center[0] + x * cos - y * sin, center[1] + x * sin + y * cos) for x, y in points]


def _degrees(value: object | None) -> float:
    return float(getattr(value, "degrees", 0.0))


def _finding(check_id: str, tag: str, message: str, severity: Severity = Severity.ERROR) -> Finding:
    return Finding(severity=severity, check_id=check_id, message=message,
                   element_tags=(tag,), result=Result.FAIL if severity is Severity.ERROR else Result.UNKNOWN)
