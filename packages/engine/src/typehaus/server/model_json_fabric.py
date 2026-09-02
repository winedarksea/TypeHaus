"""The built fabric: the wall graph, the shell, and the framed assemblies.

Three fragments rather than one because model.json emits them at three points in the
document, but they are one domain — resolver-owned construction geometry, all of it keyed
by uid and all of it carrying ``_member_json``/``_layer_json`` shapes. Splitting them
across modules would put the same reader in three files; splitting the file at the
document's own seams keeps the emitted key order intact without inventing a domain.
"""

from __future__ import annotations

from typing import Any

from typehaus.model.floors import FloorOpening, FloorSystem
from typehaus.model.spatial import Stair
from typehaus.resolve.model import ResolvedModel
from typehaus.server.model_json_shared import _layer_json, _member_json, _provenance
from typehaus.source.provenance import Provenance


def _layout_axis(model: ResolvedModel, wall_tag: str) -> list[list[float]] | None:
    """``[origin, origin + direction]`` of the wall's layout line, in plan metres."""
    line = next((ln for ln in model.layout_lines
                 if any(m.wall_tag == wall_tag for m in ln.members)), None)
    if line is None:
        return None
    (ox, oy), (dx, dy) = line.origin, line.direction
    return [[ox, oy], [ox + dx, oy + dy]]


def wall_graph_json(
    model: ResolvedModel, provenance: Provenance | None
) -> dict[str, Any]:
    """Walls, their solved junctions, the openings hosted in them, and the plan nodes."""
    return {
        "walls": [
            {
                "uid": w.uid, "tag": w.tag, "storey": w.storey, "assembly": w.assembly,
                "provenance": _provenance(provenance, w.tag),
                "axis": [list(w.axis[0]), list(w.axis[1])],
                "z0_m": w.z0_m, "z1_m": w.z1_m, "top_z0_m": w.top_z0_m,
                # Where the framing actually sits when the skin was dropped below it
                # (resolve/platform.extend_walls_to_foundation). The viewer measures
                # every sill from this, not from z0_m — mirrors ResolvedWall.base_ref_z_m.
                "plate_base_z_m": w.plate_base_z_m,
                # The mirror at the top: where the double top plate stops when the wall
                # body grew up through the joist band (extend_walls_to_platform). The band
                # between this and z1_m is rim board and joists, not wall.
                "plate_top_z_m": w.plate_top_z_m,
                # The facade datum this wall subdivides against, as an axis the viewer can
                # project onto: [origin, origin + direction] of its layout line. The standing
                # seam is a 16" module that has to run corner to corner, and the wall's own
                # axis restarts it at every tee the facade is chunked at — so the pan module
                # is measured from here, exactly as the outriggers it clips to are
                # (resolve/layout_lines.py). None for a wall on no line.
                "layout_axis": _layout_axis(model, w.tag),
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
    }


def shell_json(model: ResolvedModel, provenance: Provenance | None) -> dict[str, Any]:
    """Massing that is not a wall: solids, construction returns, footing beds, roofs."""
    return {
        "solids": [
            {"uid": solid.uid, "tag": solid.tag, "storey": solid.storey,
             "category": solid.category, "outline": [list(point) for point in solid.outline],
             "voids": [[list(point) for point in ring] for ring in solid.voids],
             "z0_m": solid.z0_m, "z1_m": solid.z1_m, "assembly": solid.assembly,
             "material": solid.material,
             # A run carried as one swept solid (→ resolve/sweep.py). Null on every prism,
             # which is every solid that is not a rail, a pipe or a raceway; the viewer
             # forks on it in ``buildSolid`` and mitres the tube itself.
             "sweep": (None if solid.sweep is None else {
                 "path": [list(point) for point in solid.sweep.path],
                 "profile": [list(point) for point in solid.sweep.profile]}),
             "provenance": _provenance(provenance, solid.tag)}
            for solid in sorted(model.solids, key=lambda item: item.uid)
        ],
        # WallPaneling bands (wainscot, tile splash). Unlike a construction return these ARE
        # render geometry: a band is a real applied surface on the room side of its wall. One
        # record per wall the band covers; ``outline`` is empty where the side could not be
        # derived (a line-scoped band), which the viewer skips.
        "panelings": [
            {"uid": band.uid, "tag": band.tag, "storey": band.storey, "room": band.room,
             "wall_tag": band.wall_tag, "material_ref": band.material_ref,
             "layout_line": band.layout_line,
             "replaces_wall_finish": band.replaces_wall_finish,
             "area_m2": band.area_m2, "run_m": band.run_m,
             "outline": [list(point) for point in band.outline],
             "z0_m": band.z0_m, "z1_m": band.z1_m, "thickness_m": band.thickness_m,
             "provenance": _provenance(provenance, band.tag)}
            for band in sorted(model.panelings, key=lambda item: (item.uid, item.wall_tag))
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
             "returning_layer": ret.returning_layer,
             "gasket_product": ret.gasket_product,
             "gasket_thickness_m": ret.gasket_thickness_m,
             "condition_key": ret.condition_key,
             "provenance": _provenance(provenance, ret.tag)}
            for ret in sorted(model.construction_returns, key=lambda item: item.uid)
        ],
        # Compacted washed-stone footing beds (undercut beneath each strip footing). The 3D
        # viewer draws these as a gravel prism so the bearing prep is visible below grade.
        "footing_beddings": [
            {"uid": bedding.uid, "tag": bedding.tag, "storey": bedding.storey,
             "host": bedding.host,
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
    }


def framing_json(model: ResolvedModel, provenance: Provenance | None) -> dict[str, Any]:
    """Framed assemblies filed by their host element: stairs, decks, braces, floor heat."""
    return {
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
             "authored_tread_depth_m": (authored.tread_depth.meters
                                         if authored.tread_depth is not None else None),
             "authored_nosing_depth_m": (authored.nosing_depth.meters
                                          if authored.nosing_depth is not None else None),
             "start": list(authored.start.xy_m) if authored.start is not None else None,
             "riser_count": stair.riser_count, "riser_height_m": stair.riser_height_m,
             "tread_depth_m": stair.tread_depth_m,
             "going_depth_m": stair.going_depth_m,
             "nosing_depth_m": stair.nosing_depth_m,
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
        "braces": [
            {"uid": brace.uid, "tag": brace.tag, "storey": brace.storey,
             "provenance": _provenance(provenance, brace.tag),
             "members": [_member_json(member) for member in brace.members]}
            for brace in sorted(model.braces, key=lambda item: item.uid)
        ],
        # Soffit ladder framing, on the brace shape exactly. It reached `all_members()` — so
        # the BOM and structural.member_interference saw it — but no emitter walked it, so a
        # Soffit was one solid prism in the viewer with its lumber invisible. A soffit that
        # authored no FramingSpec frames nothing and is skipped rather than emitting an empty
        # host. The UI files these under the FRAMING trade, not floors: the finished box is a
        # separate solid node on the same uid, and only the box belongs behind the floors
        # toggle (see emit/gltf/emitter.py, which makes the same split).
        "soffits": [
            {"uid": soffit.uid, "tag": soffit.tag, "storey": soffit.storey,
             "provenance": _provenance(provenance, soffit.tag),
             "members": [_member_json(member) for member in soffit.members]}
            for soffit in sorted(model.soffits, key=lambda item: item.uid)
            if soffit.members
        ],
        "floor_heat": [
            {"uid": zone.uid, "tag": zone.tag, "storey": zone.storey, "system": zone.system,
             "zone": [list(point) for point in zone.zone], "spacing_m": zone.spacing_m,
             "wire_length_m": zone.wire_length_m}
            for zone in model.floor_heat
        ],
    }
