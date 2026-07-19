"""Resolve authored radiant zones to plan footprints and wire-length estimates."""

from __future__ import annotations

from shapely.geometry import Polygon

from typehaus.findings import Finding, Result, Severity
from typehaus.model.floors import FloorHeat
from typehaus.quantities import inch
from typehaus.resolve.model import ResolvedFloorHeat, ResolvedModel


def resolve_floor_heat(model: ResolvedModel) -> list[Finding]:
    findings: list[Finding] = []
    for storey in model.plan.storeys:
        for authored in model.plan.storey_elements(storey.tag):
            if not isinstance(authored, FloorHeat):
                continue
            zone = _zone(model, storey.tag, authored)
            if not zone:
                findings.append(Finding(
                    severity=Severity.ERROR, check_id="integrity.floor_heat_zone",
                    message=f"floor heat {authored.tag} has no resolvable zone", element_tags=(authored.tag,),
                    result=Result.FAIL,
                ))
                continue
            spacing = (authored.spacing or inch(6)).meters
            area = Polygon(zone).area
            model.floor_heat.append(ResolvedFloorHeat(
                uid=authored.uid, tag=authored.tag, storey=storey.tag,
                system=authored.system.value, zone=zone, spacing_m=spacing,
                wire_length_m=area / spacing,
            ))
    return findings


def _zone(model: ResolvedModel, storey: str, authored: FloorHeat):
    if authored.zone:
        return [point.xy_m for point in authored.zone]
    if authored.room_ref:
        room = next((item for item in model.rooms
                     if item.storey == storey and item.tag == authored.room_ref), None)
        if room is not None:
            return room.clear_face
    return []
