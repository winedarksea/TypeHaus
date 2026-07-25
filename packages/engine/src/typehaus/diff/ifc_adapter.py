"""Project the baseline (ResolvedModel) and an external IFC onto DiffElem (→ 20 §Diff).

The baseline is the deterministic model rebuilt from source; the external side is the
architect's IFC read via ifcopenshell (the one optional edge — imported lazily so the
matcher and report stay dependency-light and unit-testable).
"""

from __future__ import annotations

import math
import uuid
from pathlib import Path

from typehaus._meta import PSET_SOURCE
from typehaus.diff.model import DiffElem
from typehaus.model.ids import derive_child_guid
from typehaus.resolve.model import ResolvedModel, ResolvedWall


def _guid(project_uuid: uuid.UUID, uid: str) -> str:
    """Compressed IFC GlobalId when ifcopenshell is present; the raw uid otherwise.

    Real diffs run with ifcopenshell so both sides derive matching GUIDs; the fallback keeps
    the baseline projection importable (and unit-testable) without the heavy dependency.
    """
    try:
        from ifcopenshell.guid import compress

        return str(compress(uuid.uuid5(project_uuid, uid).hex))
    except ImportError:
        return uid


def _wall_geometry(w: ResolvedWall) -> tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float]]:
    (sx, sy), (ex, ey) = w.axis
    length = ((ex - sx) ** 2 + (ey - sy) ** 2) ** 0.5
    dir_ = ((ex - sx) / length, (ey - sy) / length) if length else (0.0, 0.0)
    points = [point for layer in w.layers for point in layer.polygon]
    centroid, bbox = _bounds(points, w.z0_m, w.z1_m)
    return centroid, bbox, dir_


def baseline_elems(model: ResolvedModel) -> list[DiffElem]:
    """Project every emitted occurrence onto the stable reconciliation vocabulary."""
    puid = model.plan.project.project_uuid
    elems: list[DiffElem] = []
    wall_by_tag = {w.tag: w for w in model.walls}
    for w in model.walls:
        centroid, bbox, direction = _wall_geometry(w)
        elems.append(DiffElem(
            global_id=_guid(puid, w.uid), tag=w.tag, ifc_class="IfcWall", storey=w.storey,
            centroid=centroid, bbox=bbox, axis_dir=direction,
            attrs={"assembly": w.assembly},
        ))
    for o in model.openings:
        host = wall_by_tag.get(o.host_wall)
        if host is None:
            continue
        (sx, sy), (ex, ey) = host.axis
        length = ((ex - sx) ** 2 + (ey - sy) ** 2) ** 0.5 or 1.0
        t = o.center_along_m / length
        cx, cy = sx + (ex - sx) * t, sy + (ey - sy) * t
        frame_points = _opening_frame_bounds(host, o)
        centroid, bbox = _bounds(frame_points, host.z0_m + o.sill_m,
                                 host.z0_m + o.sill_m + o.height_m)
        elems.append(DiffElem(
            global_id=(derive_child_guid(puid, o.uid, "void") if o.kind == "rough_opening" else _guid(puid, o.uid)), tag=o.tag,
            ifc_class=("IfcDoor" if o.is_door else "IfcWindow") if o.kind != "rough_opening" else "IfcOpeningElement",
            storey=host.storey,
            centroid=centroid, bbox=bbox, axis_dir=(0.0, 0.0),
            attrs={key: value for key, value in {"type": o.type_ref, "host_wall": o.host_wall}.items()
                   if value},
        ))
    class_for_kind = {
        "furniture": "IfcFurniture", "plumbing": "IfcSanitaryTerminal",
        "appliance": "IfcBuildingElementProxy",
        "Register": "IfcAirTerminal", "Equipment": "IfcBuildingElementProxy",
    }
    electrical_classes = {
        "receptacle": "IfcOutlet", "gfci": "IfcOutlet", "receptacle_240": "IfcOutlet",
        "switch": "IfcSwitchingDevice", "light": "IfcLightFixture",
        "panel": "IfcElectricDistributionBoard",
    }
    for item in model.canvas_objects:
        source = model.plan.by_tag(item.tag)
        ifc_class = (electrical_classes.get(getattr(getattr(source, "kind", None), "value", ""), "IfcBuildingElementProxy")
                     if item.kind == "ElectricalDevice"
                     else class_for_kind.get(item.kind, class_for_kind.get(item.domain, "IfcBuildingElementProxy")))
        height = _placeable_height(model, item, source)
        centroid, bbox = _bounds(item.footprint, item.z_m, item.z_m + height)
        attrs = {"type": item.type_ref or ""}
        attrs["rotation_degrees"] = f"{item.rotation_degrees:.6f}"
        ports = _type_ports(model, item.type_ref)
        if ports:
            attrs["ports"] = ports
        elems.append(DiffElem(
            global_id=_guid(puid, item.uid), tag=item.tag,
            ifc_class=ifc_class, storey=item.storey,
            centroid=centroid, bbox=bbox, axis_dir=(0.0, 0.0),
            attrs=attrs,
        ))
    return elems


def external_elems(ifc_path: Path) -> list[DiffElem]:
    """Read an external IFC into DiffElem records. Requires ifcopenshell."""
    try:
        import ifcopenshell
        import ifcopenshell.geom
    except ImportError as exc:  # pragma: no cover - exercised only in full installs
        raise RuntimeError("haus diff requires ifcopenshell to read external IFC") from exc

    model = ifcopenshell.open(str(ifc_path))
    elems: list[DiffElem] = []
    for cls in ("IfcWall", "IfcOpeningElement", "IfcWindow", "IfcDoor", "IfcFurniture",
                "IfcSanitaryTerminal", "IfcBuildingElementProxy", "IfcOutlet", "IfcAirTerminal",
                "IfcSwitchingDevice", "IfcLightFixture", "IfcElectricDistributionBoard"):
        for prod in model.by_type(cls):
            # A door/window's void is implementation detail of its filling relationship.
            # Unfilled rough openings remain independently reconcilable occurrences.
            if cls == "IfcOpeningElement" and getattr(prod, "HasFillings", ()):
                continue
            if cls == "IfcBuildingElementProxy" and not _has_pset(prod, "TypeHaus_Identity"):
                continue
            storey = _storey_name(prod)
            centroid, bbox = _ifc_geometry_bounds(prod, ifcopenshell.geom)
            elems.append(DiffElem(
                global_id=prod.GlobalId, tag=getattr(prod, "Tag", None) or prod.Name or "",
                ifc_class=cls, storey=storey, centroid=centroid,
                bbox=bbox, axis_dir=(0.0, 0.0), attrs=_external_attrs(prod),
            ))
    return elems


def _has_pset(product: object, name: str) -> bool:
    for relation in getattr(product, "IsDefinedBy", []) or []:
        definition = getattr(relation, "RelatingPropertyDefinition", None)
        if getattr(definition, "Name", None) == name:
            return True
    return False


def _external_attrs(product: object) -> dict[str, str]:
    """Read only facts the TypeHaus exporter persists on every comparable occurrence."""
    try:
        import ifcopenshell.util.element

        psets = ifcopenshell.util.element.get_psets(product, psets_only=True)
    except Exception:  # noqa: BLE001 - a third-party IFC may omit property sets entirely
        return {}
    attrs: dict[str, str] = {}
    source = psets.get(PSET_SOURCE, {})
    if source.get("assembly") is not None:
        attrs["assembly"] = str(source["assembly"])
    if source.get("host_wall") is not None:
        attrs["host_wall"] = str(source["host_wall"])
    if source.get("rotation_degrees") is not None:
        attrs["rotation_degrees"] = str(source["rotation_degrees"])
    identity = psets.get("TypeHaus_Identity", {})
    if identity.get("source_type") is not None:
        attrs["type"] = str(identity["source_type"])
    ports = _external_ports(product)
    if ports:
        attrs["ports"] = ports
    return attrs


def _storey_name(prod: object) -> str:
    for rel in getattr(prod, "ContainedInStructure", []) or []:
        struct = getattr(rel, "RelatingStructure", None)
        if struct is not None and struct.is_a("IfcBuildingStorey"):
            return struct.Name or ""
    return ""


def _bounds(points: list[tuple[float, float]], z0: float, z1: float) -> tuple[tuple[float, float, float],
                                                                                tuple[float, float, float]]:
    if not points:
        return ((0.0, 0.0, (z0 + z1) / 2), (0.0, 0.0, z1 - z0))
    xs, ys = zip(*points)
    minimum, maximum = (min(xs), min(ys), z0), (max(xs), max(ys), z1)
    return (tuple((minimum[index] + maximum[index]) / 2 for index in range(3)),
            tuple(maximum[index] - minimum[index] for index in range(3)))  # type: ignore[return-value]


def _opening_frame_bounds(wall: ResolvedWall, opening: object) -> list[tuple[float, float]]:
    (sx, sy), (ex, ey) = wall.axis
    length = math.hypot(ex - sx, ey - sy) or 1.0
    ux, uy = (ex - sx) / length, (ey - sy) / length
    nx, ny = -uy, ux
    center = (sx + ux * opening.center_along_m, sy + uy * opening.center_along_m)
    # Bare rough openings are emitted as a full wall-depth void; installed doors/windows
    # are emitted as their intentionally thin filling frame.
    half_width = opening.width_m / 2
    half_depth = (wall.thickness_m / 2) if opening.kind == "rough_opening" else 0.025
    return [(center[0] + x * ux + y * nx, center[1] + x * uy + y * ny)
            for x, y in ((-half_width, -half_depth), (half_width, -half_depth),
                         (half_width, half_depth), (-half_width, half_depth))]


def _placeable_height(model: ResolvedModel, item: object, source: object | None) -> float:
    types = {product.tag: product for collection in (
        model.plan.library.furniture_types, model.plan.library.fixture_types,
        model.plan.library.appliance_types, model.plan.library.equipment_types,
        model.plan.library.register_types, model.plan.library.electrical_device_types,
    ) for product in collection}
    product_type = types.get(item.type_ref)
    if product_type is not None:
        return product_type.height.meters
    if item.kind == "Equipment":
        return 1.5
    return 0.05


def _type_ports(model: ResolvedModel, type_ref: str | None) -> str:
    if type_ref is None:
        return ""
    products = (model.plan.library.furniture_types, model.plan.library.fixture_types,
                model.plan.library.appliance_types, model.plan.library.equipment_types,
                model.plan.library.register_types, model.plan.library.electrical_device_types)
    product_type = next((item for collection in products for item in collection if item.tag == type_ref), None)
    if product_type is None:
        return ""
    return ";".join(sorted(
        f"{port.tag}:{port.service.value}:{port.position[0].meters:.6f},{port.position[1].meters:.6f},{port.position[2].meters:.6f}"
        for port in product_type.ports
    ))


def _external_ports(product: object) -> str:
    """Read TypeHaus' stable nested endpoints without inventing route topology."""
    try:
        import ifcopenshell.util.element

        ports: list[str] = []
        for relation in getattr(product, "IsNestedBy", ()) or ():
            for port in getattr(relation, "RelatedObjects", ()) or ():
                if not port.is_a("IfcDistributionPort"):
                    continue
                pset = ifcopenshell.util.element.get_psets(port, psets_only=True).get("TypeHaus_Port", {})
                if not pset:
                    continue
                ports.append(
                    f"{pset.get('tag', port.Name or '')}:{pset.get('service', '')}:"
                    f"{float(pset.get('x_m', 0)):.6f},{float(pset.get('y_m', 0)):.6f},{float(pset.get('z_m', 0)):.6f}"
                )
        return ";".join(sorted(ports))
    except Exception:  # noqa: BLE001 - third-party IFCs may omit nested port semantics
        return ""


def product_world_bounds(product: object):
    """(low, high) world-coordinate corners in metres, or None without usable geometry.

    ifcopenshell converts to metres whatever the file's length unit is, which is what makes a
    millimetre-authored foreign IFC comparable with our metre-authored export. A product with
    no representation at all (a pure aggregation container) returns None rather than a
    degenerate box at the origin — the caller decides what an extent-less element means.
    """
    try:
        import ifcopenshell.geom
    except ImportError as exc:  # pragma: no cover - exercised only in slim installs
        raise RuntimeError("reading IFC geometry requires ifcopenshell") from exc

    if getattr(product, "Representation", None) is None:
        return None
    try:
        settings = ifcopenshell.geom.settings()
        settings.set("use-world-coords", True)
        shape = ifcopenshell.geom.create_shape(settings, product)
        vertices = shape.geometry.verts
        if not vertices:
            return None
        points = [vertices[index:index + 3] for index in range(0, len(vertices), 3)]
        return (tuple(min(point[axis] for point in points) for axis in range(3)),
                tuple(max(point[axis] for point in points) for axis in range(3)))
    except Exception:  # noqa: BLE001 - a foreign malformed representation is simply unusable
        return None


def _ifc_geometry_bounds(prod: object, geom: object) -> tuple[tuple[float, float, float],
                                                               tuple[float, float, float]]:
    try:
        settings = geom.settings()  # type: ignore[attr-defined]
        settings.set(settings.USE_WORLD_COORDS, True)
        shape = geom.create_shape(settings, prod)  # type: ignore[attr-defined]
        vertices = shape.geometry.verts
        if not vertices:
            raise ValueError("no vertices")
        points = [vertices[index:index + 3] for index in range(0, len(vertices), 3)]
        minimum = tuple(min(point[index] for point in points) for index in range(3))
        maximum = tuple(max(point[index] for point in points) for index in range(3))
        return (tuple((minimum[index] + maximum[index]) / 2 for index in range(3)),
                tuple(maximum[index] - minimum[index] for index in range(3)))  # type: ignore[return-value]
    except Exception:  # noqa: BLE001 - an external malformed representation remains comparable by identity
        return ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
