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
