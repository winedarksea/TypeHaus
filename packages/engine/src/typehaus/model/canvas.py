"""Normalized read contract shared by the canvas, schedules, and interchange adapters."""

from __future__ import annotations

from typing import Any
from math import atan2, degrees

from typehaus.model.plan import PlanModel
from typehaus.model.placeables import PlacementStrategy
from typehaus.model.placeable_symbols import (lamp_role, model_parts, part_hex,
                                              plan_symbol_strokes)


_TYPE_COLLECTIONS = (
    ("door_types", "opening", "Door", PlacementStrategy.OPENING_HOSTED),
    ("window_types", "opening", "Window", PlacementStrategy.OPENING_HOSTED),
    ("furniture_types", "furniture", "Furniture", PlacementStrategy.FREE_PLACED),
    ("fixture_types", "plumbing", "Fixture", PlacementStrategy.FREE_PLACED),
    ("appliance_types", "appliance", "Appliance", PlacementStrategy.FREE_PLACED),
    ("equipment_types", "mechanical", "Equipment", PlacementStrategy.FREE_PLACED),
    ("register_types", "mechanical", "Register", PlacementStrategy.FREE_PLACED),
    ("electrical_device_types", "electrical", "ElectricalDevice", PlacementStrategy.FREE_PLACED),
)


def canvas_object_types(plan: PlanModel) -> list[dict[str, Any]]:
    """Return all catalog types with a uniform placement declaration."""
    result: list[dict[str, Any]] = []
    for collection, domain, kind, default_strategy in _TYPE_COLLECTIONS:
        for item in getattr(plan.library, collection):
            footprint = getattr(item, "footprint", None)
            result.append({
                "tag": item.tag, "name": getattr(item, "name", item.tag), "domain": domain, "kind": kind,
                "placement": getattr(item, "placement", default_strategy).value,
                "footprint_m": [part.meters for part in footprint] if footprint else None,
                "height_m": item.height.meters if hasattr(item, "height") else None,
                "footprint_shape_m": _polygon(getattr(item, "footprint_shape", None)),
                "clearances": [_clearance(zone) for zone in getattr(item, "clearances", ())],
                "mount": _mount(getattr(item, "mount", None)),
                "ports": [{"tag": port.tag, "service": port.service.value}
                          for port in getattr(item, "ports", ())],
                "plan_svg": (f"/asset/{item.plan_representation.svg}"
                             if getattr(item, "plan_representation", None) is not None
                             and item.plan_representation.svg else None),
                "model_glb": (f"/asset/{item.model_representation.glb}"
                              if getattr(item, "model_representation", None) is not None
                              and item.model_representation.glb else
                              f"/asset/{item.mesh.path}" if getattr(item, "mesh", None) is not None else None),
                "model_primitive": (item.model_representation.primitive
                                    if getattr(item, "model_representation", None) is not None else None),
                **_symbol_geometry(item, footprint),
            })
    return result


def _symbol_geometry(item: Any, footprint: Any) -> dict[str, Any]:
    """Project a type's generated plan glyph and 3D massing into the wire contract.

    Colours resolve to hex *here*, so the UI needs no palette table of its own — the viewer
    and the glTF export read the same numbers instead of hand-mirrored constants. Geometry is
    in the symbol's local frame (origin at the footprint centre); every consumer already owns
    the rotate-and-translate, and ``placeable_symbols.place_local`` is that one transform.
    """
    symbol = getattr(item, "plan_symbol", None)
    height = getattr(item, "height", None)
    if symbol is None or footprint is None:
        return {"plan_strokes": [], "model_parts": []}
    width_m, depth_m = (part.meters for part in footprint)
    height_m = height.meters if height is not None else 0.0
    lamp = lamp_role(getattr(item, "cct_k", None))
    return {
        "plan_strokes": [{"points": [list(point) for point in stroke["points"]],
                          "closed": stroke["closed"], "weight": stroke["weight"],
                          "fill": part_hex(_lamp(stroke["fill"], lamp)) if stroke["fill"] else None}
                         for stroke in plan_symbol_strokes(symbol, width_m, depth_m)],
        "model_parts": [{"center": list(part["center"]), "size": list(part["size"]),
                         "color": part_hex(_lamp(part["color"], lamp))}
                        for part in model_parts(symbol, width_m, depth_m, height_m)],
    }


def _lamp(role: str, lamp: str) -> str:
    """Swap the generic ``lamp`` role for the type's colour-temperature bin.

    Builders emit ``lamp`` because they only know a size; the CCT lives on the product
    type, which is only in hand here and in the glTF emitter's ``_add_canvas_parts``. Both
    apply this same substitution — the two must agree, or the viewer and the export
    disagree about what a 4000K can looks like.
    """
    return lamp if role == "lamp" else role


def canvas_objects(plan: PlanModel) -> list[dict[str, Any]]:
    """Project authored placeables to a stable, domain-neutral inspection shape."""
    type_domains = {item["tag"]: item["domain"] for item in canvas_object_types(plan)}
    objects: list[dict[str, Any]] = []
    for storey in plan.storeys:
        for item in plan.storey_elements(storey.tag):
            if item.element_kind not in {"Door", "Window", "RoughOpening", "Furniture", "Fixture",
                                         "Appliance", "Equipment", "Register", "ElectricalDevice"}:
                continue
            position = getattr(item, "position", None)
            location = getattr(item, "location", None)
            objects.append({
                "uid": item.uid, "tag": item.tag, "storey": storey.tag,
                "kind": item.element_kind, "type": getattr(item, "type_ref", None),
                "domain": type_domains.get(getattr(item, "type_ref", ""), item.element_kind.lower()),
                "room": getattr(item, "room", None),
                # OpeningPosition is an along-wall topology reference, not a Point2D.
                "position_m": list(position.xy_m) if hasattr(position, "xy_m") else None,
                "rotation": _rotation_degrees(getattr(item, "rotation", None)),
                "host": getattr(item, "host", None),
                "attachment": ({"wall": location.attachment.wall_ref, "face": location.attachment.face}
                               if location is not None and location.attachment is not None else None),
            })
    return objects


def resolved_canvas_objects(
    model: Any, provenance_of: Any = None
) -> list[dict[str, Any]]:
    """Serialize resolver-owned object geometry without exposing internal dataclasses.

    ``provenance_of`` is an optional ``tag -> provenance dict | None`` callable (the server
    passes ``model_json._provenance``). Canvas objects are *the* drag-and-move population, so
    without it the UI cannot tell a movable object from one authored in a file it can never
    write back to — the drag would appear to work and then revert.
    """
    type_metadata = {item["tag"]: item for item in canvas_object_types(model.plan)}
    prov_of = provenance_of if provenance_of is not None else (lambda _tag: None)
    placeables = [{
        "uid": item.uid, "tag": item.tag, "storey": item.storey, "kind": item.kind,
        "type": item.type_ref, "domain": item.domain, "room": item.room,
        "position_m": list(item.position), "z_m": item.z_m, "rotation": item.rotation_degrees,
        "host": None,
        "attachment": ({"wall": item.attachment_wall, "face": item.attachment_face}
                       if item.attachment_wall is not None else None),
        "footprint": [list(point) for point in item.footprint],
        "required_clearances": [[list(point) for point in polygon]
                                for polygon in item.required_clearances],
        "recommended_clearances": [[list(point) for point in polygon]
                                   for polygon in item.recommended_clearances],
        # Tag of the furniture set this object belongs to (a table and its chairs), or null.
        "placement_group": item.placement_group,
        # Feeding circuit for the placeables that consume power, else null.
        "circuit": item.circuit,
        "ports": type_metadata.get(item.type_ref, {}).get("ports", []),
        "plan_svg": type_metadata.get(item.type_ref, {}).get("plan_svg"),
        "model_glb": type_metadata.get(item.type_ref, {}).get("model_glb"),
        "model_primitive": type_metadata.get(item.type_ref, {}).get("model_primitive"),
        "provenance": prov_of(item.tag),
    } for item in model.canvas_objects]
    return [*_resolved_openings(model, type_metadata, prov_of), *placeables]


def _rotation_degrees(rotation: object | None) -> float | None:
    """Avoid leaking a quantity object over the JSON API."""
    return rotation.degrees if rotation is not None and hasattr(rotation, "degrees") else None


def _polygon(footprint: Any) -> list[list[float]] | None:
    return [[point.x.meters, point.y.meters] for point in footprint.points] if footprint else None


def _clearance(zone: Any) -> dict[str, Any]:
    return {"footprint_m": _polygon(zone.footprint), "purpose": zone.purpose,
            "policy": zone.policy.value, "source": zone.source,
            "code_profile": zone.code_profile}


def _mount(mount: Any) -> dict[str, Any] | None:
    if mount is None:
        return None
    return {"kind": mount.kind.value,
            "elevation_m": mount.elevation.meters if mount.elevation is not None else None,
            "drop_m": mount.drop.meters if mount.drop is not None else None,
            "recessed_into_host_surface": mount.recessed_into_host_surface}


def _resolved_openings(
    model: Any, type_metadata: dict[str, dict[str, Any]], prov_of: Any
) -> list[dict[str, Any]]:
    """Project hosted openings into the same read contract without weakening their topology."""
    wall_by_tag = {wall.tag: wall for wall in model.walls}
    records: list[dict[str, Any]] = []
    for opening in model.openings:
        wall = wall_by_tag.get(opening.host_wall)
        if wall is None:
            continue
        (sx, sy), (ex, ey) = wall.axis
        length = ((ex - sx) ** 2 + (ey - sy) ** 2) ** 0.5
        if length == 0:
            continue
        ux, uy = (ex - sx) / length, (ey - sy) / length
        nx, ny = -uy, ux
        center = (sx + ux * opening.center_along_m, sy + uy * opening.center_along_m)
        half_width, half_depth = opening.width_m / 2, wall.thickness_m / 2
        footprint = [(center[0] - ux * half_width - nx * half_depth,
                      center[1] - uy * half_width - ny * half_depth),
                     (center[0] + ux * half_width - nx * half_depth,
                      center[1] + uy * half_width - ny * half_depth),
                     (center[0] + ux * half_width + nx * half_depth,
                      center[1] + uy * half_width + ny * half_depth),
                     (center[0] - ux * half_width + nx * half_depth,
                      center[1] - uy * half_width + ny * half_depth)]
        metadata = type_metadata.get(opening.type_ref or "", {})
        records.append({
            "uid": opening.uid, "tag": opening.tag, "storey": wall.storey,
            "kind": opening.kind, "type": opening.type_ref, "domain": "opening", "room": None,
            "position_m": list(center), "z_m": wall.z0_m + opening.sill_m,
            "rotation": degrees(atan2(uy, ux)), "host": opening.host_wall, "attachment": None,
            "footprint": [list(point) for point in footprint],
            "required_clearances": [],
            "recommended_clearances": [[list(point) for point in opening.swing_clearance]] if opening.swing_clearance else [],
            "framing_bumper": [list(point) for point in opening.framing_bumper], "ports": [],
            "plan_svg": metadata.get("plan_svg"), "model_glb": metadata.get("model_glb"),
            "model_primitive": metadata.get("model_primitive"),
            "provenance": prov_of(opening.tag),
        })
    return records
