"""Resolve one physical placement contract for furniture, fixtures, and MEP devices."""

from __future__ import annotations

import math

from shapely.geometry import Point, Polygon

from typehaus.findings import Finding, Result, Severity
from typehaus.model.plan import PlanModel
from typehaus.resolve.model import ResolvedCanvasObject, ResolvedModel

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
            footprint = _transformed_polygon(_local_footprint(product_type, item), center, rotation)
            resolved_room = next((room.tag for room in rooms if Polygon(room.clear_face).covers(Point(center))), None)
            explicit_room = getattr(item, "room", None)
            if explicit_room is not None and explicit_room != resolved_room:
                findings.append(_finding("integrity.placeable_room_mismatch", item.tag,
                    f"placeable {item.tag} is assigned to {explicit_room} but its footprint center is outside that room",
                    Severity.WARN))
            required, recommended = _clearance_polygons(
                product_type, center, rotation, plan.project.active_code_profile,
            )
            model.canvas_objects.append(ResolvedCanvasObject(
                uid=item.uid, tag=item.tag, storey=storey.tag, domain=domain, kind=item.element_kind, type_ref=type_ref,
                room=explicit_room or resolved_room, position=center, rotation_degrees=rotation,
                z_m=_resolved_mount_elevation(storey, item),
                footprint=footprint, required_clearances=required, recommended_clearances=recommended,
                attachment_wall=attachment, attachment_face=attachment_face,
            ))
    findings.extend(_clearance_conflicts(model))
    findings.extend(_door_swing_conflicts(model))
    return findings


def _resolved_mount_elevation(storey: object, item: object) -> float:
    """Resolve floor, wall, and ceiling mount elevations into the project Z frame."""
    mount = getattr(item, "mount", None)
    floor = storey.elevation.meters
    if mount is None:
        return floor
    if mount.kind.value == "ceiling":
        drop = mount.drop.meters if mount.drop is not None else 0.0
        return floor + storey.default_ceiling_height.meters - drop
    return floor + (mount.elevation.meters if mount.elevation is not None else 0.0)


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


def _clearance_polygons(product_type: object | None, center: tuple[float, float], rotation: float,
                        active_code_profile: str | None) -> tuple[tuple[list[tuple[float, float]], ...], tuple[list[tuple[float, float]], ...]]:
    if product_type is None:
        return (), ()
    required: list[list[tuple[float, float]]] = []
    recommended: list[list[tuple[float, float]]] = []
    for zone in getattr(product_type, "clearances", ()):
        if zone.code_profile is not None and zone.code_profile != active_code_profile:
            continue
        polygon = _transformed_polygon([point.xy_m for point in zone.footprint.points], center, rotation)
        (required if zone.policy.value == "required" else recommended).append(polygon)
    return tuple(required), tuple(recommended)


def _clearance_conflicts(model: ResolvedModel) -> list[Finding]:
    """Report use-space encroachments without rejecting the drag that created one.

    A clearance is an occupied planning zone, so compare it against other physical
    footprints rather than their own clearance zones.  That avoids false conflicts
    between two deliberately overlapping advisory envelopes.
    """
    findings: list[Finding] = []
    for item in model.canvas_objects:
        peers = (peer for peer in model.canvas_objects
                 if peer.storey == item.storey and peer.uid != item.uid)
        for zones, severity, policy_name in (
            (item.required_clearances, Severity.ERROR, "required"),
            (item.recommended_clearances, Severity.WARN, "recommended"),
        ):
            for zone in zones:
                zone_shape = Polygon(zone)
                if zone_shape.is_empty or not zone_shape.is_valid:
                    continue
                for peer in peers:
                    overlap = zone_shape.intersection(Polygon(peer.footprint))
                    if overlap.area <= 1e-8:
                        continue
                    findings.append(Finding(
                        severity=severity,
                        check_id=f"integrity.placeable_{policy_name}_clearance_conflict",
                        message=(f"{policy_name} clearance for {item.tag} conflicts with "
                                 f"physical footprint of {peer.tag}"),
                        element_tags=(item.tag, peer.tag),
                        result=Result.FAIL if severity is Severity.ERROR else Result.UNKNOWN,
                    ))
    return findings


def _door_swing_conflicts(model: ResolvedModel) -> list[Finding]:
    """Door leaf sweeps are advisory overlays: flag encroachments without blocking edits."""
    findings: list[Finding] = []
    wall_by_tag = {wall.tag: wall for wall in model.walls}
    for opening in model.openings:
        if not opening.swing_clearance:
            continue
        wall = wall_by_tag.get(opening.host_wall)
        if wall is None:
            continue
        swing = Polygon(opening.swing_clearance)
        for item in model.canvas_objects:
            if item.storey != wall.storey or swing.intersection(Polygon(item.footprint)).area <= 1e-8:
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
