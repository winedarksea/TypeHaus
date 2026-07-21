"""Project the baseline (ResolvedModel) and an external IFC onto DiffElem (→ 20 §Diff).

The baseline is the deterministic model rebuilt from source; the external side is the
architect's IFC read via ifcopenshell (the one optional edge — imported lazily so the
matcher and report stay dependency-light and unit-testable).
"""

from __future__ import annotations

import uuid
from pathlib import Path

from typehaus.diff.model import DiffElem
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
    thickness = w.thickness_m or 0.15
    height = w.z1_m - w.z0_m
    cx, cy, cz = (sx + ex) / 2, (sy + ey) / 2, (w.z0_m + w.z1_m) / 2
    dir_ = ((ex - sx) / length, (ey - sy) / length) if length else (0.0, 0.0)
    return (cx, cy, cz), (length, thickness, height), dir_


def baseline_elems(model: ResolvedModel) -> list[DiffElem]:
    """Project the resolved model onto DiffElem records (walls + openings)."""
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
        # Rough openings intentionally have no IfcDoor/IfcWindow filling to diff.
        if o.kind == "rough_opening":
            continue
        host = wall_by_tag.get(o.host_wall)
        if host is None:
            continue
        (sx, sy), (ex, ey) = host.axis
        length = ((ex - sx) ** 2 + (ey - sy) ** 2) ** 0.5 or 1.0
        t = o.center_along_m / length
        cx, cy = sx + (ex - sx) * t, sy + (ey - sy) * t
        elems.append(DiffElem(
            global_id=_guid(puid, o.uid), tag=o.tag,
            ifc_class="IfcDoor" if o.is_door else "IfcWindow", storey=host.storey,
            centroid=(cx, cy, o.sill_m + o.height_m / 2),
            bbox=(o.width_m, 0.1, o.height_m), axis_dir=(0.0, 0.0),
            attrs={"type": o.type_ref or ""},
        ))
    return elems


def external_elems(ifc_path: Path) -> list[DiffElem]:
    """Read an external IFC into DiffElem records. Requires ifcopenshell."""
    try:
        import ifcopenshell
        import ifcopenshell.util.placement as placement
    except ImportError as exc:  # pragma: no cover - exercised only in full installs
        raise RuntimeError("haus diff requires ifcopenshell to read external IFC") from exc

    model = ifcopenshell.open(str(ifc_path))
    elems: list[DiffElem] = []
    for cls in ("IfcWall", "IfcWindow", "IfcDoor"):
        for prod in model.by_type(cls):
            storey = _storey_name(prod)
            centroid = _placement_origin(prod, placement)
            elems.append(DiffElem(
                global_id=prod.GlobalId, tag=getattr(prod, "Tag", None) or prod.Name or "",
                ifc_class=cls, storey=storey, centroid=centroid,
                bbox=_bbox(prod), axis_dir=(0.0, 0.0),
            ))
    return elems


def _storey_name(prod: object) -> str:
    for rel in getattr(prod, "ContainedInStructure", []) or []:
        struct = getattr(rel, "RelatingStructure", None)
        if struct is not None and struct.is_a("IfcBuildingStorey"):
            return struct.Name or ""
    return ""


def _placement_origin(prod: object, placement: object) -> tuple[float, float, float]:
    try:
        mat = placement.get_local_placement(prod.ObjectPlacement)  # type: ignore[attr-defined]
        return (float(mat[0][3]), float(mat[1][3]), float(mat[2][3]))
    except Exception:  # noqa: BLE001 - malformed placement → origin
        return (0.0, 0.0, 0.0)


def _bbox(prod: object) -> tuple[float, float, float]:
    # Bounding-box quantities are optional in IFC; default to a neutral size when absent.
    return (0.0, 0.0, 0.0)
