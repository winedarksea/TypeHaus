"""Placeables — the elements a designer drops into a room rather than draws.

Alarms, fixtures/appliances and furniture share one shape: an authored point on a storey
plus the *type* it instantiates, with the type's footprint/clearance resolved here so the
UI never joins an instance to a catalog row itself. They are one module because they are
one editing gesture, even though the payload files them under three keys.
"""

from __future__ import annotations

from typing import Any

from typehaus.resolve.model import ResolvedModel
from typehaus.server.model_json_shared import _provenance
from typehaus.source.provenance import Provenance


def placeables_json(
    model: ResolvedModel, provenance: Provenance | None
) -> dict[str, Any]:
    """Alarms, fixtures/appliances and furniture, each joined to its library type."""
    return {
        "alarms": [
            # ``circuit`` rides along for the same reason every other consumer's does: the
            # panel schedule names the alarms on a circuit, so the reader needs the reverse
            # edge to show which circuit a selected detector is on.
            {"uid": alarm.uid, "tag": alarm.tag, "storey": storey.tag,
             "kind": alarm.kind.value, "room": alarm.room, "circuit": alarm.circuit,
             "provenance": _provenance(provenance, alarm.tag)}
            for storey in model.plan.storeys
            for alarm in model.plan.storey_elements(storey.tag)
            if alarm.element_kind == "Alarm"
        ],
        "fixtures": [
            {"uid": fixture.uid, "tag": fixture.tag, "storey": storey.tag,
             "type": fixture.type_ref, "room": fixture.room,
             "wall_ref": fixture.wall_ref,
             "position": list(fixture.position.xy_m),
             "provenance": _provenance(provenance, fixture.tag),
             "footprint_m": [dimension.meters for dimension in fixture_type.footprint],
             "clearance_m": ([dimension.meters for dimension in fixture_type.clearance]
                             if fixture_type.clearance is not None else None),
             "needs": sorted(service.value for service in fixture_type.needs)}
            for storey in model.plan.storeys
            for fixture in model.plan.storey_elements(storey.tag)
            if fixture.element_kind in {"Fixture", "Appliance"}
            for fixture_type in (*model.plan.library.fixture_types,
                                 *model.plan.library.appliance_types)
            if fixture_type.tag == fixture.type_ref
        ],
        "furniture": [
            {"uid": furniture.uid, "tag": furniture.tag, "storey": storey.tag,
             "type": furniture.type_ref, "position": list(furniture.position.xy_m),
             "provenance": _provenance(provenance, furniture.tag),
             "footprint_m": [dimension.meters for dimension in furniture_type.footprint],
             "height_m": furniture_type.height.meters, "storage": furniture_type.storage,
             "clearance_m": ([dimension.meters for dimension in furniture_type.clearance]
                             if furniture_type.clearance is not None else None),
             "mesh": furniture_type.mesh.path if furniture_type.mesh is not None else None}
            for storey in model.plan.storeys
            for furniture in model.plan.storey_elements(storey.tag)
            if furniture.element_kind == "Furniture"
            for furniture_type in model.plan.library.furniture_types
            if furniture_type.tag == furniture.type_ref
        ],
    }
