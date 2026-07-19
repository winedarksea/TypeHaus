"""House-local furniture catalog loader for ``haus import furniture`` (M3 #49)."""

from __future__ import annotations

import json
from pathlib import Path

from typehaus.findings import Finding, Result, Severity
from typehaus.model import Furniture, FurnitureType, MeshRef, deg, m, pt
from typehaus.model.ids import new_uid
from typehaus.model.plan import PlanModel

_CATALOG_RELATIVE_PATH = Path("furniture") / "imports.json"


def load_imported_furniture(house_dir: Path, plan: PlanModel,
                            findings: list[Finding]) -> PlanModel:
    """Merge explicit house-local imports into a loaded plan without editing Python source."""
    catalog_path = house_dir / _CATALOG_RELATIVE_PATH
    if not catalog_path.exists():
        return plan.model_copy(update={"source_root": str(house_dir)})
    try:
        catalog = json.loads(catalog_path.read_text())
        types = tuple(_type_from_record(record) for record in catalog.get("types", []))
        instances = tuple(catalog.get("instances", []))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        findings.append(_error("furniture.catalog", f"invalid furniture catalog: {exc}"))
        return plan.model_copy(update={"source_root": str(house_dir)})

    existing_types = {item.tag for item in plan.library.furniture_types}
    duplicate_types = existing_types & {item.tag for item in types}
    if duplicate_types:
        findings.append(_error("furniture.catalog", "duplicate furniture type(s): "
                               + ", ".join(sorted(duplicate_types))))
        return plan.model_copy(update={"source_root": str(house_dir)})
    all_types = (*plan.library.furniture_types, *types)
    known_types = {item.tag for item in all_types}
    rooms = {element.tag: storey.tag for storey in plan.storeys
             for element in plan.storey_elements(storey.tag)
             if element.element_kind == "Room"}
    elements = dict(plan.elements)
    imported_tags: set[str] = set()
    for record in instances:
        try:
            item = _instance_from_record(record, rooms, known_types)
        except (KeyError, TypeError, ValueError) as exc:
            findings.append(_error("furniture.catalog", f"invalid furniture instance: {exc}"))
            continue
        if item.tag in imported_tags or plan.by_tag(item.tag) is not None:
            findings.append(_error("furniture.catalog", f"duplicate furniture tag {item.tag!r}",
                                   (item.tag,)))
            continue
        imported_tags.add(item.tag)
        storey = rooms[record["room"]]
        elements[storey] = (*elements.get(storey, ()), item)
    library = plan.library.model_copy(update={"furniture_types": all_types})
    return plan.model_copy(update={"library": library, "elements": elements,
                                   "source_root": str(house_dir)})


def _type_from_record(record: dict) -> FurnitureType:
    width, depth = record["footprint_m"]
    return FurnitureType(
        tag=record["tag"], name=record["name"], footprint=(m(float(width)), m(float(depth))),
        height=m(float(record["height_m"])), storage=bool(record.get("storage", False)),
        mesh=MeshRef(path=record["mesh"]) if record.get("mesh") else None,
        source=record.get("source"),
    )


def _instance_from_record(record: dict, rooms: dict[str, str], known_types: set[str]) -> Furniture:
    if record["room"] not in rooms:
        raise ValueError(f"unknown room {record['room']!r}")
    if record["type_ref"] not in known_types:
        raise ValueError(f"unknown furniture type {record['type_ref']!r}")
    x, y = record["position_m"]
    return Furniture(
        uid=record.get("uid") or new_uid(), tag=record["tag"], type_ref=record["type_ref"],
        position=pt(m(float(x)), m(float(y))),
        rotation=deg(float(record["rotation_degrees"])) if "rotation_degrees" in record else None,
    )


def _error(check_id: str, message: str, tags: tuple[str, ...] = ()) -> Finding:
    return Finding(severity=Severity.ERROR, check_id=check_id, message=message,
                   element_tags=tags, result=Result.FAIL)
