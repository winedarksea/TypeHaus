"""Safe, non-mutating analysis stage for project-local visual assets."""

from __future__ import annotations

import hashlib
import json
import math
import re
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ImportLimits:
    max_total_bytes: int = 100 * 1024 * 1024
    max_files: int = 20
    staging_expiry_seconds: int = 30 * 60


@dataclass(frozen=True)
class AssetAnalysis:
    source: Path
    format: str
    content_hash: str
    total_bytes: int
    dependencies: tuple[Path, ...] = ()
    warnings: tuple[str, ...] = ()
    analyzed_at_epoch: float = 0.0
    ifc_candidates: tuple["IfcAssetCandidate", ...] = ()


@dataclass(frozen=True)
class IfcAssetCandidate:
    """One selectable IFC product occurrence; analysis never imports the whole building."""

    occurrence_id: str
    global_id: str
    ifc_class: str
    name: str
    type_global_id: str | None = None
    bounds_m: tuple[float, float, float] | None = None
    footprint_m: tuple[float, float] | None = None
    orientation_degrees: float | None = None
    materials: tuple[str, ...] = ()
    properties: dict[str, object] | None = None
    ports: tuple[dict[str, object], ...] = ()


@dataclass(frozen=True)
class ImportConfirmation:
    """Explicit normalization decisions required between analysis and mutation."""

    units: str
    up_axis: str
    origin: str


def analyze_placeable_asset(source: Path, limits: ImportLimits = ImportLimits()) -> AssetAnalysis:
    """Validate a self-contained/import package before it can mutate a project catalog.

    This intentionally does no geometry conversion. The caller presents its result and
    requires unit/up-axis/origin confirmation before committing the normalized GLB.
    """
    source = source.resolve()
    if not source.is_file():
        raise ValueError(f"asset file not found: {source}")
    suffix = source.suffix.lower()
    allowed = {".glb", ".gltf", ".dae", ".svg", ".ifc"}
    if suffix not in allowed:
        raise ValueError("asset import accepts .glb, .gltf, .dae, .svg, or .ifc")
    dependencies = _gltf_dependencies(source) if suffix == ".gltf" else ()
    files = (source, *dependencies)
    if len(files) > limits.max_files:
        raise ValueError(f"asset package exceeds {limits.max_files} files")
    total = sum(path.stat().st_size for path in files)
    if total > limits.max_total_bytes:
        raise ValueError(f"asset package exceeds {limits.max_total_bytes // 1024 // 1024} MB")
    if suffix == ".svg":
        _validate_svg(source.read_text(errors="replace"))
    candidates = _ifc_candidates(source) if suffix == ".ifc" else ()
    digest = hashlib.sha256()
    for path in sorted(files):
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return AssetAnalysis(source=source, format=suffix[1:], content_hash=digest.hexdigest(),
                         total_bytes=total, dependencies=dependencies, analyzed_at_epoch=time.time(),
                         ifc_candidates=candidates)


def commit_placeable_asset(analysis: AssetAnalysis, house_dir: Path, *, domain: str, tag: str,
                           name: str, confirmation: ImportConfirmation,
                           limits: ImportLimits = ImportLimits(), now_epoch: float | None = None,
                           ifc_occurrence: str | None = None) -> dict[str, object]:
    """Atomically commit a confirmed visual asset and its project-local type record.

    GLB remains the canonical detailed model. SVG is retained as a sanitized plan symbol;
    IFC extraction deliberately stops at analysis until an occurrence is selected.
    """
    now = time.time() if now_epoch is None else now_epoch
    if analysis.analyzed_at_epoch <= 0 or now - analysis.analyzed_at_epoch > limits.staging_expiry_seconds:
        raise ValueError("asset analysis has expired; analyze it again before committing")
    if confirmation.units not in {"m", "mm", "ft"}:
        raise ValueError("confirm units as m, mm, or ft")
    if confirmation.up_axis not in {"y", "z"}:
        raise ValueError("confirm up-axis as y or z")
    if confirmation.origin != "floor_center":
        raise ValueError("confirm origin as floor_center")
    if domain not in {"furniture", "plumbing", "appliance", "mechanical", "register", "electrical"}:
        raise ValueError(f"unknown placeable domain {domain!r}")
    candidate = _selected_ifc_candidate(analysis, ifc_occurrence)
    asset_dir = house_dir / "assets" / "placeables"
    asset_dir.mkdir(parents=True, exist_ok=True)
    extension = ".svg" if analysis.format == "svg" else ".glb"
    target = asset_dir / f"{analysis.content_hash}{extension}"
    catalog_path = house_dir / "assets" / "placeables.json"
    document = _catalog_document(catalog_path)
    previous_visual = target.read_bytes() if target.exists() else None
    try:
        width, depth, height = _normalize_visual_asset(analysis.source, target, analysis.format, confirmation,
                                                        ifc_occurrence=ifc_occurrence)
    except Exception:
        _restore_visual(target, previous_visual)
        raise
    record = {
        "domain": domain, "tag": tag, "name": name,
        "footprint_m": [round(width, 6), round(depth, 6)], "height_m": round(height, 6),
        "model": target.relative_to(house_dir).as_posix() if extension == ".glb" else None,
        "plan_svg": target.relative_to(house_dir).as_posix() if extension == ".svg" else None,
        "content_hash": analysis.content_hash,
        "provenance": {"filename": analysis.source.name, "format": analysis.format,
                       "units": confirmation.units, "up_axis": confirmation.up_axis,
                       "origin": confirmation.origin, **_ifc_provenance(analysis.source, candidate)},
    }
    if candidate is not None and candidate.ports:
        record["ports"] = list(candidate.ports)
    types = document["types"]
    matching = next((index for index, item in enumerate(types)
                     if item.get("tag") == tag or item.get("content_hash") == analysis.content_hash), None)
    if matching is None:
        types.append(record)
    else:
        # Re-import keeps the pre-existing tag (and therefore all placed instance refs) and
        # any hand-authored generated-symbol opt-in, which the asset analysis cannot know.
        record["tag"] = types[matching]["tag"]
        if types[matching].get("plan_symbol"):
            record["plan_symbol"] = types[matching]["plan_symbol"]
        types[matching] = record
    try:
        _atomic_json(catalog_path, document)
    except Exception:
        _restore_visual(target, previous_visual)
        raise
    return record


def _normalize_visual_asset(source: Path, target: Path, format_: str,
                            confirmation: ImportConfirmation,
                            ifc_occurrence: str | None = None) -> tuple[float, float, float]:
    if format_ == "svg":
        target.write_bytes(source.read_bytes())
        return (1.0, 1.0, 0.01)
    try:
        import trimesh
    except ImportError as exc:  # pragma: no cover - dependency edge
        raise RuntimeError("normalizing glTF/DAE requires trimesh") from exc
    scene = _ifc_scene(source, ifc_occurrence) if format_ == "ifc" else trimesh.load(source, force="scene")
    if scene.bounds is None:
        raise ValueError("asset has no geometry bounds")
    scene.apply_transform(_normalization_matrix(scene.bounds, confirmation))
    extents = scene.bounds[1] - scene.bounds[0]
    scene.export(target, file_type="glb")
    return tuple(float(value) for value in extents)


def _ifc_candidates(source: Path) -> tuple[IfcAssetCandidate, ...]:
    try:
        import ifcopenshell
        import ifcopenshell.geom
        import ifcopenshell.util.element
        import ifcopenshell.util.placement
    except ImportError as exc:  # pragma: no cover - dependency edge
        raise RuntimeError("IFC asset analysis requires ifcopenshell") from exc
    try:
        model = ifcopenshell.open(str(source))
    except Exception as exc:  # noqa: BLE001 - parser diagnostics are user-facing
        raise ValueError(f"invalid IFC: {exc}") from exc
    candidates: list[IfcAssetCandidate] = []
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    for product in model.by_type("IfcProduct"):
        if not getattr(product, "Representation", None) or not getattr(product, "GlobalId", None):
            continue
        if product.is_a("IfcOpeningElement") or product.is_a("IfcSpatialElement"):
            continue
        type_guid = next((getattr(relation.RelatingType, "GlobalId", None)
                         for relation in getattr(product, "IsTypedBy", ()) or []), None)
        bounds = _ifc_candidate_bounds(product, ifcopenshell.geom, settings)
        materials = tuple(sorted({material.Name for material in ifcopenshell.util.element.get_materials(product)
                                  if getattr(material, "Name", None)}))
        properties = ifcopenshell.util.element.get_psets(product, psets_only=True)
        orientation = _ifc_orientation(product, ifcopenshell.util.placement)
        candidates.append(IfcAssetCandidate(occurrence_id=str(product.id()), global_id=product.GlobalId,
                                            ifc_class=product.is_a(), name=product.Name or product.GlobalId,
                                            type_global_id=type_guid, bounds_m=bounds,
                                            footprint_m=bounds[:2] if bounds is not None else None,
                                            orientation_degrees=orientation, materials=materials,
                                            properties=properties or None, ports=_ifc_ports(product)))
    if not candidates:
        raise ValueError("IFC contains no selectable product occurrence with geometry")
    return tuple(candidates)


def _ifc_ports(product: object) -> tuple[dict[str, object], ...]:
    """Promote only our stable endpoint schema; generic IFC ports lack a safe service map."""
    try:
        import ifcopenshell.util.element

        ports: list[dict[str, object]] = []
        for relation in getattr(product, "IsNestedBy", ()) or ():
            for port in getattr(relation, "RelatedObjects", ()) or ():
                if not port.is_a("IfcDistributionPort"):
                    continue
                pset = ifcopenshell.util.element.get_psets(port, psets_only=True).get("TypeHaus_Port", {})
                service = pset.get("service")
                if not pset or service not in {"water_cold", "water_hot", "drain", "vent", "gas", "power_120",
                                                "power_240", "supply_air", "return_air"}:
                    continue
                ports.append({"tag": str(pset.get("tag", port.Name or "port")), "service": str(service),
                              "position_m": [float(pset.get("x_m", 0)), float(pset.get("y_m", 0)),
                                             float(pset.get("z_m", 0))], "notes": str(pset.get("notes", ""))})
        return tuple(sorted(ports, key=lambda item: (str(item["tag"]), str(item["service"]))))
    except Exception:  # noqa: BLE001 - third-party port topology is optional import metadata
        return ()


def _ifc_candidate_bounds(product: object, geom: object, settings: object) -> tuple[float, float, float] | None:
    try:
        shape = geom.create_shape(settings, product)  # type: ignore[attr-defined]
        vertices = shape.geometry.verts
        if not vertices:
            return None
        points = [vertices[index:index + 3] for index in range(0, len(vertices), 3)]
        return tuple(float(max(point[index] for point in points) - min(point[index] for point in points))
                     for index in range(3))  # type: ignore[return-value]
    except Exception:  # noqa: BLE001 - analysis still allows a geometry-less preview entry
        return None


def _ifc_orientation(product: object, placement: object) -> float | None:
    try:
        matrix = placement.get_local_placement(product.ObjectPlacement)  # type: ignore[attr-defined]
        return round(math.degrees(math.atan2(float(matrix[1][0]), float(matrix[0][0]))), 6)
    except Exception:  # noqa: BLE001 - optional preview fact
        return None


def _selected_ifc_candidate(analysis: AssetAnalysis, occurrence_id: str | None) -> IfcAssetCandidate | None:
    if analysis.format != "ifc":
        if occurrence_id is not None:
            raise ValueError("--ifc-occurrence is only valid for IFC assets")
        return None
    if occurrence_id is None:
        raise ValueError("select exactly one IFC occurrence before committing an IFC asset")
    candidate = next((item for item in analysis.ifc_candidates if item.occurrence_id == occurrence_id or
                      item.global_id == occurrence_id), None)
    if candidate is None:
        raise ValueError("selected IFC occurrence was not present in the analyzed asset")
    return candidate


def _ifc_scene(source: Path, occurrence_id: str | None):
    if occurrence_id is None:
        raise ValueError("select exactly one IFC occurrence before extracting IFC geometry")
    try:
        import ifcopenshell
        import ifcopenshell.geom
        import trimesh
    except ImportError as exc:  # pragma: no cover - dependency edge
        raise RuntimeError("IFC extraction requires ifcopenshell and trimesh") from exc
    model = ifcopenshell.open(str(source))
    product = model.by_guid(occurrence_id) if len(occurrence_id) == 22 else model.by_id(int(occurrence_id))
    if product is None or not getattr(product, "Representation", None):
        raise ValueError("selected IFC occurrence has no extractable geometry")
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    try:
        shape = ifcopenshell.geom.create_shape(settings, product)
        vertices = shape.geometry.verts
        faces = shape.geometry.faces
        if not vertices or not faces:
            raise ValueError("selected IFC occurrence has empty geometry")
        mesh = trimesh.Trimesh(vertices=[vertices[index:index + 3] for index in range(0, len(vertices), 3)],
                               faces=[faces[index:index + 3] for index in range(0, len(faces), 3)], process=False)
        return trimesh.Scene(mesh)
    except Exception as exc:  # noqa: BLE001 - geometry kernel messages vary by platform
        raise ValueError(f"could not extract selected IFC geometry: {exc}") from exc


def _ifc_provenance(source: Path, candidate: IfcAssetCandidate | None) -> dict[str, object]:
    if candidate is None:
        return {}
    try:
        import ifcopenshell
        import ifcopenshell.util.element

        model = ifcopenshell.open(str(source))
        product = model.by_guid(candidate.global_id)
        properties = ifcopenshell.util.element.get_psets(product, psets_only=True) if product else {}
    except Exception:  # noqa: BLE001 - provenance must not make a successfully selected asset unusable
        properties = {}
    return {"ifc_class": candidate.ifc_class, "ifc_global_id": candidate.global_id,
            "ifc_type_global_id": candidate.type_global_id or "", "ifc_properties": properties}


def _normalization_matrix(bounds: object, confirmation: ImportConfirmation) -> list[list[float]]:
    """Return the declared source → TypeHaus (metres, Z-up, floor-centred) transform."""
    scale = {"m": 1.0, "mm": 0.001, "ft": 0.3048}[confirmation.units]
    # TypeHaus plan coordinates are X/Y with Z vertical.  A Y-up asset rotates its
    # authored vertical axis onto Z while retaining right-handed geometry.
    if confirmation.up_axis == "y":
        rotate = ((1.0, 0.0, 0.0, 0.0), (0.0, 0.0, -1.0, 0.0),
                  (0.0, 1.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0))
    else:
        rotate = ((1.0, 0.0, 0.0, 0.0), (0.0, 1.0, 0.0, 0.0),
                  (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0))
    # Bounds need the same orientation and scale before removing the lateral centre and
    # lowest Z.  Constructing the eight corners keeps this independent of trimesh/numpy.
    minimum, maximum = bounds  # type: ignore[misc]
    corners = [(x, y, z) for x in (minimum[0], maximum[0]) for y in (minimum[1], maximum[1])
               for z in (minimum[2], maximum[2])]
    oriented = [
        (scale * (rotate[0][0] * x + rotate[0][1] * y + rotate[0][2] * z),
         scale * (rotate[1][0] * x + rotate[1][1] * y + rotate[1][2] * z),
         scale * (rotate[2][0] * x + rotate[2][1] * y + rotate[2][2] * z))
        for x, y, z in corners
    ]
    min_x, max_x = min(point[0] for point in oriented), max(point[0] for point in oriented)
    min_y, max_y = min(point[1] for point in oriented), max(point[1] for point in oriented)
    min_z = min(point[2] for point in oriented)
    return [
        [scale * rotate[0][0], scale * rotate[0][1], scale * rotate[0][2], -(min_x + max_x) / 2],
        [scale * rotate[1][0], scale * rotate[1][1], scale * rotate[1][2], -(min_y + max_y) / 2],
        [scale * rotate[2][0], scale * rotate[2][1], scale * rotate[2][2], -min_z],
        [0.0, 0.0, 0.0, 1.0],
    ]


def _catalog_document(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"revision": 1, "types": []}
    document = json.loads(path.read_text())
    if not isinstance(document, dict) or not isinstance(document.get("types"), list):
        raise ValueError(f"invalid project catalog {path}")
    return document


def _atomic_json(path: Path, document: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(json.dumps(document, indent=2, sort_keys=True) + "\n")
        temporary = Path(handle.name)
    temporary.replace(path)


def _restore_visual(target: Path, previous_visual: bytes | None) -> None:
    if previous_visual is None:
        target.unlink(missing_ok=True)
    else:
        target.write_bytes(previous_visual)


def _gltf_dependencies(source: Path) -> tuple[Path, ...]:
    try:
        document = json.loads(source.read_text())
    except (OSError, ValueError) as exc:
        raise ValueError(f"invalid glTF JSON: {exc}") from exc
    uris = [item.get("uri") for section in ("buffers", "images") for item in document.get(section, [])]
    dependencies: list[Path] = []
    for uri in uris:
        if not uri or uri.startswith("data:"):
            continue
        if not isinstance(uri, str) or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", uri):
            raise ValueError("glTF external URLs are not permitted")
        candidate = (source.parent / uri).resolve()
        if source.parent not in candidate.parents or not candidate.is_file():
            raise ValueError("glTF dependency escapes its package or is missing")
        dependencies.append(candidate)
    return tuple(dependencies)


def _validate_svg(svg: str) -> None:
    lowered = svg.lower()
    prohibited = ("<script", "<foreignobject", "<iframe", "<object", "<embed", "onload=", "javascript:", "http://", "https://")
    if any(token in lowered for token in prohibited):
        raise ValueError("SVG contains active content or an external URL")
