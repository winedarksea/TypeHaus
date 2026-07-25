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
from typehaus.model.canvas import canvas_object_types, resolved_canvas_objects
from typehaus.model.floors import FloorOpening, FloorSystem
from typehaus.model.spatial import Stair
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import FramedMember, ResolvedModel
from typehaus.source.provenance import Provenance


def _provenance(prov: Provenance | None, tag: str) -> dict[str, Any] | None:
    if prov is None:
        return None
    loc = prov.location(tag)
    return {"file": loc.file, "line": loc.line} if loc is not None else None


def _member_json(m: FramedMember) -> dict[str, Any]:
    """The one member serialization every trade (walls/roofs/floors/stairs) shares.

    The UI never parses ``profile`` strings — this is the only place that calls
    :func:`cross_section`, so every consumer gets ``shape``/``width_m``/``depth_m``
    (and i-joist flange/web dims) pre-resolved.
    """
    section = cross_section(m.profile)
    return {
        "key": m.child_key, "category": m.category, "profile": m.profile,
        "p0": list(m.p0), "p1": list(m.p1), "z0_m": m.z0_m, "z1_m": m.z1_m,
        "z0_end_m": m.z0_end_m, "z1_end_m": m.z1_end_m,
        "shape": section.shape, "width_m": section.width_m, "depth_m": section.depth_m,
        "flange_width_m": section.flange_width_m,
        "flange_thickness_m": section.flange_thickness_m,
        "web_thickness_m": section.web_thickness_m, "plies": section.plies,
        "orient": list(m.orient) if m.orient is not None else None,
        "connection": m.connection,
        "material": m.material,
    }


def _layer_json(layer) -> dict[str, Any]:
    return {"name": layer.name, "material": layer.material_ref, "function": layer.function,
            "thickness_m": layer.thickness_m, "polygon": [list(point) for point in layer.polygon],
            "control": sorted(layer.control),
            "is_cavity": layer.is_cavity, "cavity_host": layer.cavity_host}


def _findings_json(findings: list[Finding] | None) -> list[dict[str, Any]]:
    return [f.model_dump(mode="json") for f in (findings or [])]


def _enum_value(value: Any) -> Any:
    return value.value if hasattr(value, "value") else value


def _catalog(model: ResolvedModel, provenance: Provenance | None) -> dict[str, Any]:
    """The authoring palette the UI's placement + assembly tools draw from (→ 21b).

    Everything the editor can *add* — window/door product types, the occupancy vocabulary,
    every library + project assembly with its resolved layer stack, and the material list —
    surfaced from the plan's :class:`~typehaus.model.plan.Library` so the client never has to
    hard-code a catalog. ``editable`` flags assemblies authored in the house's ``plan/``
    (provenance-tracked, so a layer edit can write back) versus shared ``library/`` presets
    the editor must duplicate before tweaking.
    """
    from typehaus.model.enums import Occupancy

    lib = model.plan.library
    assemblies: list[dict[str, Any]] = []
    for asm in lib.assemblies:
        resolved = lib.resolve_assembly(asm.tag)
        if resolved is None:
            continue
        prov = _provenance(provenance, asm.tag)
        assemblies.append({
            "tag": asm.tag,
            "editable": prov is not None,
            "provenance": prov,
            "stc": resolved.stc,
            "variant_of": asm.variant_of,
            "layers": [
                {"name": ly.name, "material": ly.material_ref,
                 "function": _enum_value(ly.function), "thickness_m": ly.thickness.meters}
                for ly in resolved.layers
            ],
        })
    return {
        "window_types": [
            {"tag": wt.tag, "width_m": wt.width.meters, "height_m": wt.height.meters,
             "operation": wt.operation}
            for wt in lib.window_types
        ],
        "door_types": [
            {"tag": dt.tag, "width_m": dt.width.meters, "height_m": dt.height.meters,
             "operation": dt.operation, "exterior": dt.exterior}
            for dt in lib.door_types
        ],
        "occupancies": [o.value for o in Occupancy],
        # ``color``/``finish`` are the authored *appearance* of a material. Without them the
        # viewer can only guess a material's look from substrings in its tag (nordic/palette
        # familyOf), which cannot distinguish white brick from red — so they ship with the
        # catalog and take precedence there. ``hatch`` deliberately stays out: it is the 2D
        # cut-pattern key and already disagrees with the 3D family (face brick hatches as
        # "concrete"), so feeding it to the viewer would mis-classify masonry.
        "materials": [
            {"tag": mat.tag, "name": mat.name, "r_per_inch": mat.r_per_inch,
             "perm_rating": mat.perm_rating, "density": mat.density,
             "color": mat.color, "finish": mat.finish}
            for mat in lib.materials
        ],
        "assemblies": assemblies,
    }


def model_to_dict(
    model: ResolvedModel,
    *,
    revision: str = "",
    provenance: Provenance | None = None,
    findings: list[Finding] | None = None,
    preferences: Preferences | None = None,
) -> dict[str, Any]:
    from typehaus.server.building_height_summary import build_building_height_summary
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
        "canvas_objects": resolved_canvas_objects(model),
        "projectNorth": model.plan.project.site.true_north.degrees,
        "findings": _findings_json(findings),
        "project": {
            "name": model.plan.project.name,
            "uuid": str(model.plan.project.project_uuid),
            "active_code_profile": model.plan.project.active_code_profile,
        },
        "site": {
            "lat": model.plan.project.site.lat,
            "lon": model.plan.project.site.lon,
            "true_north_deg": model.plan.project.site.true_north.degrees,
            "grade_m": (model.plan.project.site.grade.meters
                        if model.plan.project.site.grade is not None else None),
            "parcel": [list(point.xy_m) for point in model.plan.project.site.parcel],
            # Spot elevations are currently consumed by 2D site/elevation emitters. Keep
            # them in the shared UI contract so a future earth surface can triangulate the
            # same authored grade data without inventing a second source of truth.
            "spot_elevations": [
                {"position": list(spot.position.xy_m), "elevation_m": spot.elevation.meters}
                for spot in model.plan.project.site.spot_elevations
            ],
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
                "layers": [_layer_json(ly) for ly in w.layers],
                "members": [_member_json(m) for m in w.members],
            }
            for w in sorted(model.walls, key=lambda x: x.uid)
        ],
        "junctions": [
            {
                "node": junction.node_tag,
                "storey": junction.storey,
                "point": list(junction.point),
                "kind": junction.kind,
                "incidents": [
                    {
                        "wall": incident.wall_tag,
                        "endpoint": incident.endpoint,
                        "direction": list(incident.direction),
                        "assembly": incident.assembly,
                    }
                    for incident in junction.incidents
                ],
                "through_walls": list(junction.through_walls),
                "branch_walls": list(junction.branch_walls),
                "framing_owner": junction.framing_owner,
                "supported": junction.supported,
                "diagnostic": junction.diagnostic,
            }
            for junction in model.junctions
        ],
        "openings": [
            {"uid": o.uid, "tag": o.tag, "host": o.host_wall, "kind": o.kind, "is_door": o.is_door,
             "provenance": _provenance(provenance, o.tag),
             "type_ref": o.type_ref,
             "width_m": o.width_m, "height_m": o.height_m, "sill_m": o.sill_m,
             "center_along_m": o.center_along_m, "arch_rise_m": o.arch_rise_m,
             "swing_clearance": [list(point) for point in o.swing_clearance],
             "framing_bumper": [list(point) for point in o.framing_bumper],
             # Handing is authored data, rather than resolved geometry, but it changes the
             # plan symbol and must therefore cross the UI boundary with the opening.
             "flip_hinge": bool(getattr(model.plan.by_tag(o.tag), "flip_hinge", False)),
             "flip_swing": bool(getattr(model.plan.by_tag(o.tag), "flip_swing", False))}
            for o in model.openings
        ],
        # Authored plan nodes: the editor addresses stretch / heal / draw-snap by node *tag*
        # (uids are minted, positions round-trip), so the wall-graph vertices ride along with
        # their tag + storey. Positions are the same project-north SI metres as wall axes.
        "nodes": [
            {"tag": node.tag, "storey": storey.tag,
             "x_m": node.position.xy_m[0], "y_m": node.position.xy_m[1],
             "open_end": node.open_end, "provenance": _provenance(provenance, node.tag)}
            for storey in model.plan.storeys
            for node in model.plan.storey_elements(storey.tag)
            if node.element_kind == "Node"
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
            if fixture.element_kind in {"Fixture", "Appliance"}
            for fixture_type in (*model.plan.library.fixture_types, *model.plan.library.appliance_types)
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
             "voids": [[list(point) for point in ring] for ring in solid.voids],
             "z0_m": solid.z0_m, "z1_m": solid.z1_m, "assembly": solid.assembly,
             "provenance": _provenance(provenance, solid.tag)}
            for solid in sorted(model.solids, key=lambda item: item.uid)
        ],
        # ConstructionRule returns (#45): documentation + take-off records, not render
        # geometry — a correctly-placed return duplicates the host wall's own mitred layer
        # polygon, so no solid is emitted for one. Carried here for the inspector/overlay.
        "construction_returns": [
            {"uid": ret.uid, "tag": ret.tag, "storey": ret.storey, "kind": ret.kind,
             "takeoff_category": ret.takeoff_category, "material_ref": ret.material_ref,
             "element_tags": list(ret.element_tags),
             "outline": [list(point) for point in ret.outline],
             "z0_m": ret.z0_m, "z1_m": ret.z1_m, "thickness_m": ret.thickness_m,
             "length_m": ret.length_m, "lap_m": ret.lap_m,
             "thermal_continuity": ret.thermal_continuity,
             "air_vapor_continuity": ret.air_vapor_continuity,
             "sealant": ret.sealant, "flashing": ret.flashing,
             "returning_layer": ret.returning_layer, "condition_key": ret.condition_key,
             "provenance": _provenance(provenance, ret.tag)}
            for ret in sorted(model.construction_returns, key=lambda item: item.uid)
        ],
        # Compacted washed-stone footing beds (undercut beneath each strip footing). The 3D
        # viewer draws these as a gravel prism so the bearing prep is visible below grade.
        "footing_beddings": [
            {"uid": bedding.uid, "tag": bedding.tag, "storey": bedding.storey,
             "host_footing": bedding.host_footing,
             "outline": [list(point) for point in bedding.outline],
             "z0_m": bedding.z0_m, "z1_m": bedding.z1_m, "aggregate": bedding.aggregate,
             "geotextile": bedding.geotextile, "drain_tile": bedding.drain_tile,
             "provenance": _provenance(provenance, bedding.tag)}
            for bedding in sorted(model.footing_beddings, key=lambda item: item.uid)
        ],
        "roofs": [
            {"uid": roof.uid, "tag": roof.tag, "storey": roof.storey, "form": roof.form,
             "footprint": [list(point) for point in roof.footprint],
             "eave_z_m": roof.eave_z_m, "ridge_z_m": roof.ridge_z_m,
             # Plate top the roof bears on (eave_z_m is the deck plane above it) and the
             # per-layer edge setbacks (golden eave detail clips) the 3D viewer consumes.
             "bearing_z_m": roof.bearing_z_m,
             "layer_edge_setbacks": [dict(entry) for entry in roof.layer_edge_setbacks],
             "ridge_direction": roof.ridge_direction, "assembly": roof.assembly,
             "surface_area_m2": roof.surface_area_m2,
             "members": [_member_json(member) for member in roof.members],
             "provenance": _provenance(provenance, roof.tag)}
            for roof in sorted(model.roofs, key=lambda item: item.uid)
        ],
        "stairs": [
            {"uid": stair.uid, "tag": stair.tag, "storey": stair.storey,
             "to_storey": stair.to_storey, "outline": [list(point) for point in stair.outline],
             # The designer edits these authored inputs; all of the geometry below remains
             # resolver-owned so the browser never becomes a second stair solver.
             "floor_opening": authored.floor_opening,
             "width_m": authored.width.meters,
             "run_direction": authored.run_direction,
             "run_reversed": authored.run_reversed,
             "layout": authored.layout,
             "turn_direction": authored.turn_direction,
             "winder_count": authored.winder_count,
             "landing_depth_m": (authored.landing_depth.meters
                                 if authored.landing_depth is not None else None),
             "start": list(authored.start.xy_m) if authored.start is not None else None,
             "riser_count": stair.riser_count, "riser_height_m": stair.riser_height_m,
             "tread_depth_m": stair.tread_depth_m,
             "members": [_member_json(member) for member in stair.members],
             "provenance": _provenance(provenance, stair.tag)}
            for stair in sorted(model.stairs, key=lambda item: item.uid)
            if isinstance((authored := model.plan.by_tag(stair.tag)), Stair)
        ],
        "floors": [
            {"uid": floor.uid, "tag": floor.tag, "storey": floor.storey,
             "direction": floor.direction,
             "subfloor": ({"material": authored.subfloor.material_ref,
                            "thickness_m": authored.subfloor.thickness.meters}
                           if isinstance((authored := model.plan.by_tag(floor.tag)), FloorSystem)
                           and authored.subfloor is not None else None),
             "openings": [[list(point.xy_m) for point in opening.outline]
                          for opening in model.plan.storey_elements(floor.storey)
                          if isinstance(opening, FloorOpening)
                          and isinstance(authored, FloorSystem)
                          and opening.tag in authored.openings],
             "provenance": _provenance(provenance, floor.tag),
             "members": [_member_json(member) for member in floor.members]}
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
        "building_height_summary": build_building_height_summary(model),
        "conditions": [
            {"kind": c.kind.value, "key": c.key, "elements": list(c.element_tags)}
            for c in model.conditions
        ],
        "transitions": [
            {"tag": t.tag, "pattern": t.condition_pattern, "overlay": t.overlay,
             "notes": t.notes,
             "continuity": [{"control": c.control, "from_face": c.from_face,
                             "to_face": c.to_face} for c in t.continuity],
             "joins": [{"layer": j.layer, "side": j.side,
                        "termination_m": j.termination.meters, "treatment": j.treatment}
                       for j in t.joins]}
            for t in model.plan.library.transitions
        ],
        "stack_edges": [
            {"lower": e.lower_wall, "upper": e.upper_wall, "overlap_m": e.overlap_m,
             "width_change": e.width_change}
            for e in model.stack_edges
        ],
        "building_science": building_science,
        "catalog": {**_catalog(model, provenance), "canvas_object_types": canvas_object_types(model.plan)},
    }


def preview_to_dict(model: ResolvedModel) -> dict[str, Any]:
    """A minimal geometry payload for a live drag preview (→ Phase 4): just wall axes,
    opening placements, and room outlines — no layers/members/checks/catalog, so the
    reduced-resolve win isn't spent again re-serializing fields a ghost overlay never
    draws. Not the model.json contract; a preview client discards this once the drag ends
    and the next ``GET /model`` (post the real ``PATCH /plan``) lands."""
    return {
        "walls": [
            {"tag": w.tag, "storey": w.storey, "axis": [list(w.axis[0]), list(w.axis[1])]}
            for w in sorted(model.walls, key=lambda x: x.uid)
        ],
        "openings": [
            {"tag": o.tag, "host": o.host_wall, "kind": o.kind, "is_door": o.is_door,
             "width_m": o.width_m, "center_along_m": o.center_along_m}
            for o in model.openings
        ],
        "rooms": [
            {"tag": r.tag, "storey": r.storey, "area_m2": r.area_m2,
             "clear_face": [list(p) for p in r.clear_face]}
            for r in model.rooms
        ],
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
