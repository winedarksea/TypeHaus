"""Room derivation (#, → 11 §Room): polygonize the wall axis network, claim by seed,
derive the finish tier, and assert space-boundary zero-gap closure (#41)."""

from __future__ import annotations

from shapely.geometry import LineString, Point, Polygon
from shapely.ops import polygonize, unary_union

from typehaus.findings import Finding, Result, Severity
from typehaus.model.plan import PlanModel
from typehaus.resolve.model import ResolvedFinishZone, ResolvedModel, ResolvedRoom


def _storey_faces(plan: PlanModel, storey_tag: str) -> list[Polygon]:
    """Extract closed faces from the storey's wall axis network via polygonize."""
    nodes = {e.tag: e.position.xy_m
             for e in plan.storey_elements(storey_tag) if e.element_kind == "Node"}
    segments = []
    for w in plan.storey_elements(storey_tag):
        if w.element_kind in ("Wall", "FoundationWall"):
            a, b = nodes.get(w.start_node), nodes.get(w.end_node)
            if a and b:
                segments.append(LineString([a, b]))
    if not segments:
        return []
    merged = unary_union(segments)
    return list(polygonize(merged))


# A wall's axis midpoint sits *on* its room face boundary exactly (the faces are polygonized
# from the wall axes themselves), so the tolerance only absorbs shapely's floating-point
# noise. Verified empirically on the catlin plan: boundary distance for a bounding wall is
# < 1e-12 m; the nearest non-bounding wall is a full wall thickness away.
_LINING_FACE_TOLERANCE_M = 1e-6


def wall_lining_overrides(plan: PlanModel,
                          storey_tag: str) -> tuple[dict[str, tuple], list[Finding]]:
    """Per-wall lining overrides authored on the storey's Rooms, plus their findings.

    ``Room.wall_lining`` / ``wall_lining_exceptions`` existed in the schema (and set the
    clear-face inset via :func:`_lining_inset`) but never reached wall geometry: the
    resolver always stacked ``assembly.default_lining``. This is the missing map — wall tag
    → lining layer tuple — computed from plan inputs only (the same seed-claimed faces
    :func:`resolve_rooms` uses) so :func:`~typehaus.resolve.topology.resolve_storey_walls`
    can consume it before any wall resolves.

    Rules: a room's override reaches every wall whose axis midpoint lies on its claimed
    face boundary; a ``WallLiningException`` naming one of those walls wins over the
    room-wide lining. Two rooms overriding one shared wall apply NEITHER and warn
    (``integrity.wall_lining_conflict``); an override on a wall whose assembly has no
    ``default_lining`` is not applied and warns (``integrity.wall_lining_unlined``) — that
    assembly carries its finishes in ``layers`` (or has no finish at all), so swapping a
    lining it does not have would silently do nothing or invent a face.
    """
    findings: list[Finding] = []
    rooms = [e for e in plan.storey_elements(storey_tag)
             if e.element_kind == "Room"
             and (e.wall_lining or e.wall_lining_exceptions)]
    if not rooms:
        return {}, findings
    faces = _storey_faces(plan, storey_tag)
    nodes = {e.tag: e.position.xy_m
             for e in plan.storey_elements(storey_tag) if e.element_kind == "Node"}
    walls = {e.tag: e for e in plan.storey_elements(storey_tag)
             if e.element_kind in ("Wall", "FoundationWall")}
    # wall tag -> [(room tag, lining), ...]: every claim first, then conflicts resolved.
    claims: dict[str, list[tuple[str, tuple]]] = {}
    for room in rooms:
        face = next((f for f in faces if f.contains(Point(room.seed.xy_m))), None)
        if face is None:
            continue  # resolve_rooms already reports the unclaimed seed as an ERROR
        boundary = face.exterior
        exceptions = {exc.wall_ref: tuple(exc.lining)
                      for exc in room.wall_lining_exceptions}
        for wall in walls.values():
            a, b = nodes.get(wall.start_node), nodes.get(wall.end_node)
            if a is None or b is None:
                continue
            midpoint = Point((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
            if boundary.distance(midpoint) > _LINING_FACE_TOLERANCE_M:
                continue
            if wall.tag in exceptions:
                lining = exceptions[wall.tag]
            elif room.wall_lining:
                lining = tuple(room.wall_lining)
            else:
                continue
            claims.setdefault(wall.tag, []).append((room.tag, lining))
    overrides: dict[str, tuple] = {}
    for wall_tag in sorted(claims):
        claimed = claims[wall_tag]
        room_tags = sorted({room_tag for room_tag, _lining in claimed})
        if len(room_tags) > 1:
            findings.append(Finding(
                severity=Severity.WARN,
                check_id="integrity.wall_lining_conflict",
                message=f"wall {wall_tag}: rooms {', '.join(room_tags)} both override its "
                        "lining — a wall has one interior lining stack, so neither is "
                        "applied",
                element_tags=(wall_tag, *room_tags),
                fix_hint="keep the room-wide wall_lining on one room and name the shared "
                         "wall in the other room's wall_lining_exceptions (or drop one)",
                result=Result.UNKNOWN,
            ))
            continue
        assembly = plan.library.resolve_assembly(walls[wall_tag].assembly)
        if assembly is None or not assembly.default_lining:
            findings.append(Finding(
                severity=Severity.WARN,
                check_id="integrity.wall_lining_unlined",
                message=f"wall {wall_tag} ({walls[wall_tag].assembly}) has no "
                        f"default_lining for room {room_tags[0]}'s override to replace — "
                        "not applied",
                element_tags=(wall_tag, room_tags[0]),
                fix_hint="that assembly carries its finish in `layers` (or is deliberately "
                         "unlined); author a variant assembly instead of a lining override",
                result=Result.UNKNOWN,
            ))
            continue
        overrides[wall_tag] = claimed[0][1]
    return overrides, findings


def resolve_rooms(plan: PlanModel, model: ResolvedModel) -> list[Finding]:
    """Claim faces by room seeds; derive clear-face polygons + areas; check closure."""
    findings: list[Finding] = []
    for storey in plan.storeys:
        faces = _storey_faces(plan, storey.tag)
        for room in (e for e in plan.storey_elements(storey.tag)
                     if e.element_kind == "Room"):
            seed = Point(room.seed.xy_m)
            face = next((f for f in faces if f.contains(seed)), None)
            if face is None:
                findings.append(
                    Finding(
                        severity=Severity.ERROR,
                        check_id="integrity.room_unclaimed",
                        message=f"room {room.tag} seed lands in no closed face — loop not "
                                "closed here",
                        element_tags=(room.tag,),
                        result=Result.FAIL,
                    )
                )
                continue
            # Clear-face polygon: inset by resolved interior lining thickness.
            inset = _lining_inset(plan, room)
            clear = face.buffer(-inset) if inset > 0 else face
            if clear.is_empty or clear.geom_type != "Polygon":
                clear = face
            ring = [(x, y) for x, y in clear.exterior.coords[:-1]]
            model.rooms.append(
                ResolvedRoom(
                    uid=room.uid, tag=room.tag, storey=storey.tag,
                    occupancy=room.occupancy.value, conditioned=room.conditioned,
                    clear_face=ring, area_m2=clear.area, floor_finish=room.floor_finish,
                    finish_zones=_finish_zones(room, clear),
                )
            )
    return findings


def _finish_zones(room, clear: Polygon) -> tuple[ResolvedFinishZone, ...]:
    """Authored in-room finish overrides, clipped to the room's clear face.

    ``Room.finish_zones`` used to stop here: ``ResolvedRoom`` had no field for it, so a
    ``FinishZone`` written in plan source was accepted by the loader and then silently
    dropped, reaching no viewer, emitter or takeoff. Clipping is what makes the areas
    subtractable — a hearth pad drawn a little proud of the wall must not bill more tile
    than the room has floor.
    """
    zones: list[ResolvedFinishZone] = []
    for zone in room.finish_zones:
        outline = Polygon([point.xy_m for point in zone.outline])
        if not outline.is_valid:
            outline = outline.buffer(0)
        clipped = outline.intersection(clear)
        if clipped.is_empty or clipped.area <= 0.0:
            continue
        zones.append(ResolvedFinishZone(
            outline=[(x, y) for x, y in outline.exterior.coords[:-1]],
            material_ref=zone.material_ref, area_m2=clipped.area,
        ))
    return tuple(zones)


def _lining_inset(plan: PlanModel, room) -> float:
    """Interior lining thickness for the room's faces (assembly default unless overridden)."""
    if room.wall_lining:
        return sum(layer.thickness.meters for layer in room.wall_lining)
    # Approximate: use the default_lining of the first bounding wall's assembly.
    for w in plan.storey_elements(room_storey(plan, room)):
        if w.element_kind in ("Wall", "FoundationWall"):
            asm = plan.library.resolve_assembly(w.assembly)
            if asm and asm.default_lining:
                return sum(layer.thickness.meters for layer in asm.default_lining)
    return 0.0


def room_storey(plan: PlanModel, room) -> str:
    for storey in plan.storeys:
        if any(e.tag == room.tag for e in plan.storey_elements(storey.tag)):
            return storey.tag
    return plan.storeys[0].tag if plan.storeys else ""
