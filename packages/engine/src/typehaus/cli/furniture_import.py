"""House-local mesh import for the M3 furniture workflow (#49)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from typehaus.model.ids import new_uid
from typehaus.source.placeable_import import analyze_placeable_asset


def import_furniture_mesh(source: Path, house_dir: Path, *, tag: str | None = None,
                          name: str | None = None, room: str | None = None,
                          position_m: tuple[float, float] | None = None,
                          storage: bool = False) -> dict[str, object]:
    """Convert a mesh to a private GLB sidecar and append its catalog record.

    Mesh coordinates are interpreted as meters, which is glTF's native unit.  Warehouse
    downloads commonly need unit confirmation before import; refusing ambiguous placement
    (room without an explicit position) keeps a catalog record from becoming a phantom plan
    object.
    """
    source = source.resolve()
    analysis = analyze_placeable_asset(source)
    if source.suffix.lower() not in {".glb", ".gltf", ".dae"}:
        raise ValueError("furniture import accepts .glb, .gltf, or .dae")
    if not source.is_file():
        raise ValueError(f"mesh file not found: {source}")
    if (room is None) != (position_m is None):
        raise ValueError("--room and --at-m must be supplied together to place imported furniture")
    try:
        import trimesh
    except ImportError as exc:  # pragma: no cover - environment-dependent dependency
        raise RuntimeError("furniture import needs trimesh; "
                           "install typehaus with its mesh dependencies") from exc

    scene = trimesh.load(source, force="scene")
    bounds = scene.bounds
    extents = bounds[1] - bounds[0]
    if min(extents) <= 0:
        raise ValueError("mesh has an empty or flat bounding box")
    slug = _slug(tag or source.stem)
    type_tag = f"FURN-{slug}"
    catalog_path = house_dir / "furniture" / "imports.json"
    mesh_rel = Path("furniture") / "meshes" / f"{slug}.glb"
    catalog = _load_catalog(catalog_path)
    if any(record.get("tag") == type_tag for record in catalog["types"]):
        raise ValueError(f"furniture type {type_tag} already exists")
    mesh_path = house_dir / mesh_rel
    mesh_path.parent.mkdir(parents=True, exist_ok=True)
    scene.export(mesh_path, file_type="glb")
    record: dict[str, object] = {
        "tag": type_tag,
        "name": name or source.stem.replace("_", " ").title(),
        "footprint_m": [round(float(extents[0]), 6), round(float(extents[1]), 6)],
        "height_m": round(float(extents[2]), 6),
        "storage": storage,
        "mesh": mesh_rel.as_posix(),
        "source": (f"House-local import from {source.name}; "
                   "verify redistribution rights before library promotion."),
        "content_hash": analysis.content_hash,
    }
    catalog["types"].append(record)
    instance: dict[str, object] | None = None
    if room is not None and position_m is not None:
        instance = {
            "uid": new_uid(), "tag": f"F-{slug}", "type_ref": type_tag, "room": room,
            "position_m": [position_m[0], position_m[1]],
        }
        catalog["instances"].append(instance)
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n")
    return {"type": record, "instance": instance, "mesh": str(mesh_path)}


def _load_catalog(path: Path) -> dict[str, list[dict[str, object]]]:
    if not path.exists():
        return {"types": [], "instances": []}
    data = json.loads(path.read_text())
    if (not isinstance(data, dict)
            or not isinstance(data.get("types", []), list)
            or not isinstance(data.get("instances", []), list)):
        raise ValueError(f"invalid furniture catalog {path}")
    return {"types": list(data.get("types", [])), "instances": list(data.get("instances", []))}


def _slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").upper()
    if not slug:
        raise ValueError("furniture tag must contain a letter or digit")
    return slug
