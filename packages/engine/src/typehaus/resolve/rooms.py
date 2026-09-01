"""Room derivation (#, → 11 §Room): polygonize the wall axis network, claim by seed,
derive the finish tier, and assert space-boundary zero-gap closure (#41)."""

from __future__ import annotations

from dataclasses import replace

from shapely.geometry import LineString, Point, Polygon
from shapely.ops import polygonize, unary_union

from typehaus.findings import Finding, Result, Severity
from typehaus.model.plan import PlanModel
from typehaus.resolve.model import ResolvedFinishZone, ResolvedModel, ResolvedRoom
from typehaus.resolve.room_openings import room_glazing_areas


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
            head, soffit_m2 = _clear_head(plan, model, storey, clear)
            resolved = ResolvedRoom(
                uid=room.uid, tag=room.tag, storey=storey.tag,
                occupancy=room.occupancy.value, conditioned=room.conditioned,
                clear_face=ring, area_m2=clear.area, floor_finish=room.floor_finish,
                finish_zones=_finish_zones(plan, storey.tag, room, clear),
                clear_height_m=head, soffit_area_m2=soffit_m2,
            )
            glazing = room_glazing_areas(plan, model, resolved)
            if glazing is not None:
                resolved = replace(resolved, glazed_area_m2=glazing[0],
                                   operable_glazed_area_m2=glazing[1])
            model.rooms.append(resolved)
    return findings


def _clear_head(plan: PlanModel, model, storey, clear: Polygon) -> tuple[float | None, float]:
    """``(clear height above this storey's datum, soffited area)`` for a room face.

    **The soffit is the point.** ``ceiling_over._is_ceiling_deck`` admits a ``FloorSystem``
    and a non-walking ``Slab`` and nothing else, which is exactly why a dropped duct box was
    invisible to every question about head height in this engine: R305 measured the deck two
    feet above the box and passed a room you cannot stand up in half of. ``ResolvedSoffit``
    has carried ``z0_m`` — the finished underside — all along, so nothing had to be derived,
    only looked at.

    The height returned is the LOWEST underside over any part of the room, so it is the
    number a "can you stand here" question wants at its worst point. ``soffit_area_m2`` is
    what that low head actually covers, which is what keeps the answer usable: SF-S-HP1
    covers 43 sf of RM-S-STUDY2's 160, and a room is not disqualified by a duct box in one
    corner. A consumer that needs to grade the two areas separately has both numbers; one
    that only needs "how low does it get" has the height.

    Height is measured from the storey datum, which omits the subfloor sheet standing on the
    joists — the same known gap ``resolve.rooms.room_floor_elevation`` carries, so the
    derived height reads 3/4" GENEROUS on a joisted floor. Recorded so nobody reads it as
    exact.
    """
    from typehaus.resolve.ceiling_over import ceiling_decks_over, ceiling_underside_m

    datum = storey.elevation.meters
    undersides = [value for value in
                  (ceiling_underside_m(deck_storey, deck)
                   for deck_storey, deck in ceiling_decks_over(plan, storey.tag, clear))
                  if value is not None]
    soffit_m2 = 0.0
    for soffit in getattr(model, "soffits", ()):
        if soffit.storey != storey.tag or len(soffit.outline) < 3:
            continue
        box = Polygon(soffit.outline)
        if not box.is_valid:
            continue
        covered = box.intersection(clear).area
        if covered <= 1e-9:
            continue
        soffit_m2 += covered
        undersides.append(soffit.z0_m)
    if not undersides:
        return None, soffit_m2
    return min(undersides) - datum, soffit_m2


def _finish_zones(plan: PlanModel, storey_tag: str, room,
                  clear: Polygon) -> tuple[ResolvedFinishZone, ...]:
    """In-room finish overrides — authored on the room, then derived from the floor under it.

    ``Room.finish_zones`` used to stop here: ``ResolvedRoom`` had no field for it, so a
    ``FinishZone`` written in plan source was accepted by the loader and then silently
    dropped, reaching no viewer, emitter or takeoff. Clipping is what makes the areas
    subtractable — a hearth pad drawn a little proud of the wall must not bill more tile
    than the room has floor.

    The derived half answers a room that spans two structures. ``Room.floor_finish`` is one
    string, so a room half over a joisted deck and half over a slab whose cap *is* the
    finished floor bills the covering across both. A ``Slab`` carrying ``floor_finish``
    claims its own footprint back: the intersection with the room's clear face becomes a
    zone, and the room's string stays the field finish over everything else. Authored zones
    win — a hearth pad laid on the band is still a hearth pad — so the derived rings are cut
    against them.
    """
    zones: list[ResolvedFinishZone] = []
    authored: list[Polygon] = []
    for zone in room.finish_zones:
        outline = Polygon([point.xy_m for point in zone.outline])
        if not outline.is_valid:
            outline = outline.buffer(0)
        clipped = outline.intersection(clear)
        if clipped.is_empty or clipped.area <= 0.0:
            continue
        authored.append(outline)
        zones.append(ResolvedFinishZone(
            outline=[(x, y) for x, y in outline.exterior.coords[:-1]],
            material_ref=zone.material_ref, area_m2=clipped.area,
        ))
    zones.extend(_derived_finish_zones(plan, storey_tag, room, clear, authored))
    return tuple(zones)


# A derived zone whose remnant is a sliver — a slab edge crossing a room by a millimetre of
# floating-point overlap — is not a finish change anyone builds. 1 cm2, comfortably below
# any authored geometry and far above shapely's noise on these coordinates.
_DERIVED_ZONE_MIN_AREA_M2 = 1e-4


def _derived_finish_zones(plan: PlanModel, storey_tag: str, room, clear: Polygon,
                          authored: list[Polygon]) -> list[ResolvedFinishZone]:
    """Zones taken from the slabs under the room whose own top face is the finished floor.

    Unlike the authored path — which draws as authored and bills clipped — a derived zone's
    outline is the *clipped* ring. It has no reason to be drawn proud of the room: it is not
    a thing someone laid out, it is the part of the room that sits on that slab.
    """
    out: list[ResolvedFinishZone] = []
    blocked = unary_union(authored) if authored else None
    for slab in plan.storey_elements(storey_tag):
        if slab.element_kind != "Slab" or not slab.floor_finish:
            continue
        if slab.floor_finish == room.floor_finish:
            continue  # the field finish already says it; a zone here would be a duplicate
        footprint = Polygon([point.xy_m for point in slab.outline])
        if not footprint.is_valid:
            footprint = footprint.buffer(0)
        part = footprint.intersection(clear)
        if blocked is not None and not part.is_empty:
            part = part.difference(blocked)
        if part.is_empty:
            continue
        for piece in getattr(part, "geoms", (part,)):
            if piece.geom_type != "Polygon" or piece.area <= _DERIVED_ZONE_MIN_AREA_M2:
                continue
            out.append(ResolvedFinishZone(
                outline=[(x, y) for x, y in piece.exterior.coords[:-1]],
                material_ref=slab.floor_finish, area_m2=piece.area,
                source_ref=slab.tag,
            ))
    return out


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
