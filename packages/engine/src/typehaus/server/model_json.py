"""model.json — the UI contract (→ 20 §model.json). Emitted from the ResolvedModel.

Carries resolved wall layer polygons, framed members, rooms, openings, and derived
conditions in canonical SI meters; element uid/tag ride along for pick → provenance.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import quote

from typehaus.checks.registry import Preferences
from typehaus.findings import Finding
from typehaus.resolve.model import ResolvedModel
from typehaus.source.provenance import Provenance


def _provenance(prov: Provenance | None, tag: str) -> dict[str, Any] | None:
    if prov is None:
        return None
    loc = prov.location(tag)
    return {"file": loc.file, "line": loc.line} if loc is not None else None


def _findings_json(findings: list[Finding] | None) -> list[dict[str, Any]]:
    return [f.model_dump(mode="json") for f in (findings or [])]


def model_to_dict(
    model: ResolvedModel,
    *,
    revision: str = "",
    provenance: Provenance | None = None,
    findings: list[Finding] | None = None,
    preferences: Preferences | None = None,
) -> dict[str, Any]:
    from typehaus.server.space_summary import build_space_summary

    building_science: dict[str, Any] | None = None
    if preferences is not None:
        from typehaus.checks.building_science.condensation import analyze_assembly
        from typehaus.checks.building_science.wwr import analyze_wwr
        from typehaus.energy import estimate_block_load

        heating = model.plan.project.site.design_temp_heating
        building_science = {
            "wwr": [item.as_dict() for item in analyze_wwr(model)],
            "energy": estimate_block_load(model, preferences).as_dict(),
            "condensation": [
                analyze_assembly(
                    assembly, model.plan.library,
                    heating_design_temp_f=heating.fahrenheit if heating else None,
                    preferences=preferences,
                ).as_dict()
                for assembly in model.plan.library.assemblies
            ],
        }
    return {
        # revision is the PATCH /plan precondition (#30); UI echoes it back on every op.
        "revision": revision,
        "units": "imperial",
        "projectNorth": model.plan.project.site.true_north.degrees,
        "findings": _findings_json(findings),
        "project": {
            "name": model.plan.project.name,
            "uuid": str(model.plan.project.project_uuid),
        },
        "site": {
            "lat": model.plan.project.site.lat,
            "lon": model.plan.project.site.lon,
            "true_north_deg": model.plan.project.site.true_north.degrees,
        },
        "underlays": [
            {"path": item.path, "storey": item.storey, "origin_x_m": item.origin_x_m,
             "origin_y_m": item.origin_y_m, "width_m": item.width_m, "height_m": item.height_m,
             "rotation_deg": item.rotation_deg, "opacity": item.opacity,
             # Encode '../' rather than letting the browser normalize a reference path before
             # it reaches the deliberately sandboxed /underlay route.
             "url": "/underlay/" + quote(item.path, safe="")}
            for item in (preferences.underlays if preferences is not None else ())
        ],
        "storeys": [
            {"tag": s.tag, "elevation_m": s.elevation.meters,
             "ceiling_m": s.default_ceiling_height.meters}
            for s in sorted(model.plan.storeys, key=lambda x: x.elevation.meters)
        ],
        "walls": [
            {
                "uid": w.uid, "tag": w.tag, "storey": w.storey, "assembly": w.assembly,
                "provenance": _provenance(provenance, w.tag),
                "axis": [list(w.axis[0]), list(w.axis[1])],
                "z0_m": w.z0_m, "z1_m": w.z1_m, "top_z0_m": w.top_z0_m,
                "top_z1_m": w.top_z1_m, "is_foundation": w.is_foundation,
                "layers": [
                    {"name": ly.name, "function": ly.function, "material": ly.material_ref,
                     "thickness_m": ly.thickness_m, "polygon": [list(p) for p in ly.polygon],
                     "control": sorted(ly.control)}
                    for ly in w.layers
                ],
                "members": [
                    {"key": m.child_key, "category": m.category, "profile": m.profile,
                     "p0": list(m.p0), "p1": list(m.p1), "z0_m": m.z0_m, "z1_m": m.z1_m,
                     "z0_end_m": m.z0_end_m, "z1_end_m": m.z1_end_m}
                    for m in w.members
                ],
            }
            for w in sorted(model.walls, key=lambda x: x.uid)
        ],
        "openings": [
            {"uid": o.uid, "tag": o.tag, "host": o.host_wall, "is_door": o.is_door,
             "provenance": _provenance(provenance, o.tag),
             "width_m": o.width_m, "height_m": o.height_m, "sill_m": o.sill_m,
             "center_along_m": o.center_along_m}
            for o in model.openings
        ],
        "alarms": [
            {"uid": alarm.uid, "tag": alarm.tag, "storey": storey.tag,
             "kind": alarm.kind.value, "room": alarm.room,
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
            if fixture.element_kind == "Fixture"
            for fixture_type in model.plan.library.fixture_types
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
        "solids": [
            {"uid": solid.uid, "tag": solid.tag, "storey": solid.storey,
             "category": solid.category, "outline": [list(point) for point in solid.outline],
             "z0_m": solid.z0_m, "z1_m": solid.z1_m, "assembly": solid.assembly,
             "provenance": _provenance(provenance, solid.tag)}
            for solid in sorted(model.solids, key=lambda item: item.uid)
        ],
        "roofs": [
            {"uid": roof.uid, "tag": roof.tag, "storey": roof.storey, "form": roof.form,
             "footprint": [list(point) for point in roof.footprint],
             "eave_z_m": roof.eave_z_m, "ridge_z_m": roof.ridge_z_m,
             "ridge_direction": roof.ridge_direction, "assembly": roof.assembly,
             "surface_area_m2": roof.surface_area_m2,
             "members": [
                 {"key": member.child_key, "category": member.category,
                  "profile": member.profile, "p0": list(member.p0), "p1": list(member.p1),
                  "z0_m": member.z0_m, "z1_m": member.z1_m,
                  "z0_end_m": member.z0_end_m, "z1_end_m": member.z1_end_m}
                 for member in roof.members
             ],
             "provenance": _provenance(provenance, roof.tag)}
            for roof in sorted(model.roofs, key=lambda item: item.uid)
        ],
        "stairs": [
            {"uid": stair.uid, "tag": stair.tag, "storey": stair.storey,
             "to_storey": stair.to_storey, "outline": [list(point) for point in stair.outline],
             "riser_count": stair.riser_count, "riser_height_m": stair.riser_height_m,
             "tread_depth_m": stair.tread_depth_m,
             "members": [
                 {"key": member.child_key, "category": member.category,
                  "profile": member.profile, "p0": list(member.p0), "p1": list(member.p1),
                  "z0_m": member.z0_m, "z1_m": member.z1_m}
                 for member in stair.members
             ], "provenance": _provenance(provenance, stair.tag)}
            for stair in sorted(model.stairs, key=lambda item: item.uid)
        ],
        "floors": [
            {"uid": floor.uid, "tag": floor.tag, "storey": floor.storey,
             "direction": floor.direction,
             "provenance": _provenance(provenance, floor.tag),
             "members": [
                 {"key": member.child_key, "category": member.category,
                  "profile": member.profile, "p0": list(member.p0), "p1": list(member.p1),
                  "z0_m": member.z0_m, "z1_m": member.z1_m}
                 for member in floor.members
             ]}
            for floor in sorted(model.floors, key=lambda item: item.uid)
        ],
        "floor_heat": [
            {"uid": zone.uid, "tag": zone.tag, "storey": zone.storey, "system": zone.system,
             "zone": [list(point) for point in zone.zone], "spacing_m": zone.spacing_m,
             "wire_length_m": zone.wire_length_m}
            for zone in model.floor_heat
        ],
        "rooms": [
            {"uid": r.uid, "tag": r.tag, "storey": r.storey, "occupancy": r.occupancy,
             "provenance": _provenance(provenance, r.tag),
             "conditioned": r.conditioned, "area_m2": r.area_m2,
             "clear_face": [list(p) for p in r.clear_face], "floor_finish": r.floor_finish}
            for r in model.rooms
        ],
        "space_summary": build_space_summary(model),
        "conditions": [
            {"kind": c.kind.value, "key": c.key, "elements": list(c.element_tags)}
            for c in model.conditions
        ],
        "stack_edges": [
            {"lower": e.lower_wall, "upper": e.upper_wall, "overlap_m": e.overlap_m,
             "width_change": e.width_change}
            for e in model.stack_edges
        ],
        "building_science": building_science,
    }


def write_model_json(
    model: ResolvedModel,
    path: Path,
    *,
    revision: str = "",
    provenance: Provenance | None = None,
    findings: list[Finding] | None = None,
    preferences: Preferences | None = None,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = model_to_dict(
        model, revision=revision, provenance=provenance, findings=findings,
        preferences=preferences,
    )
    # sort_keys for byte-determinism (→ 02 §Determinism).
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return path
