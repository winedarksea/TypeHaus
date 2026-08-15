"""Revisioned project-local placeable catalog (``assets/placeables.json``)."""

from __future__ import annotations

import json
from pathlib import Path

from typehaus.findings import Finding, failed
from typehaus.model import (ApplianceType, ClearancePolicy, ClearanceZone, ElectricalDeviceType,
                            EquipmentType, FixtureType, Footprint2D, FurnitureType, ModelRepresentation,
                            Mount, MountKind, PlacementStrategy, PlanRepresentation, RegisterType, Service,
                            ServicePort, m, pt)
from typehaus.model.placeable_symbols import SYMBOL_NAMES
from typehaus.model.plan import PlanModel

_PATH = Path("assets/placeables.json")
_TYPE_CLASS = {
    "furniture": FurnitureType, "plumbing": FixtureType, "appliance": ApplianceType,
    "mechanical": EquipmentType, "register": RegisterType, "electrical": ElectricalDeviceType,
}


def load_project_placeables(house_dir: Path, plan: PlanModel,
                            findings: list[Finding]) -> PlanModel:
    """Merge imported types without making the shared library writable.

    The file is intentionally data-only; binary visuals live beside it and are content
    addressed by the import pipeline.  Unknown domains fail loudly instead of becoming
    generic metadata that no resolver can safely interpret.
    """
    path = house_dir / _PATH
    if not path.exists():
        return plan
    try:
        document = json.loads(path.read_text())
        if not isinstance(document, dict) or document.get("revision", 1) < 1:
            raise ValueError("expected a revisioned object")
        records = document.get("types", [])
        if not isinstance(records, list):
            raise ValueError("types must be a list")
    except (OSError, ValueError, TypeError) as exc:
        findings.append(_error(f"invalid {_PATH}: {exc}"))
        return plan

    additions: dict[str, list[object]] = {name: [] for name in _TYPE_CLASS}
    existing = {item.tag for collection in _TYPE_CLASS for item in getattr(
        plan.library, f"{collection}_types" if collection != "plumbing" else "fixture_types", ())}
    for record in records:
        try:
            domain = record["domain"]
            cls = _TYPE_CLASS[domain]
            tag = record["tag"]
            if tag in existing:
                raise ValueError(f"duplicate type {tag!r}")
            width, depth = record["footprint_m"]
            common = dict(tag=tag, name=record["name"], footprint=(m(float(width)), m(float(depth))),
                          height=m(float(record["height_m"])), source=record.get("source"),
                          import_provenance=_provenance(record.get("provenance")),
                          placement=PlacementStrategy(record.get("placement", "free_placed")),
                          footprint_shape=_footprint(record.get("footprint_shape_m")),
                          clearances=_clearances(record.get("clearances", [])),
                          ports=_ports(record.get("ports", [])),
                          mount=_mount(record.get("mount")),
                          plan_symbol=_plan_symbol(record.get("plan_symbol")))
            if record.get("model"):
                common["model_representation"] = ModelRepresentation(
                    glb=str(record["model"]), primitive=record.get("model_primitive"),
                )
            elif record.get("model_primitive"):
                common["model_representation"] = ModelRepresentation(primitive=str(record["model_primitive"]))
            if record.get("plan_svg"):
                common["plan_representation"] = PlanRepresentation(svg=str(record["plan_svg"]))
            if "needs" in record:
                common["needs"] = frozenset(Service(value) for value in record["needs"])
            additions[domain].append(cls(**common))
            existing.add(tag)
        except (KeyError, TypeError, ValueError) as exc:
            findings.append(_error(f"invalid placeable type: {exc}"))
    key_map = {"furniture": "furniture_types", "plumbing": "fixture_types",
               "appliance": "appliance_types", "mechanical": "equipment_types",
               "register": "register_types", "electrical": "electrical_device_types"}
    changes = {key_map[domain]: (*getattr(plan.library, key_map[domain]), *items)
               for domain, items in additions.items() if items}
    return plan.model_copy(update={"library": plan.library.model_copy(update=changes)}) if changes else plan


def _error(message: str) -> Finding:
    return failed("placeables.catalog", message)


def _plan_symbol(value: object) -> str | None:
    """Unknown symbol names fail loudly: silently drawing nothing hides the typo forever."""
    if value is None:
        return None
    if value not in SYMBOL_NAMES:
        raise ValueError(f"unknown plan_symbol {value!r}")
    return str(value)


def _footprint(value: object) -> Footprint2D | None:
    if value is None:
        return None
    if not isinstance(value, list):
        raise ValueError("footprint_shape_m must be a list of [x, y] points")
    return Footprint2D(points=tuple(_point(point, "footprint_shape_m") for point in value))


def _clearances(value: object) -> tuple[ClearanceZone, ...]:
    if not isinstance(value, list):
        raise ValueError("clearances must be a list")
    zones: list[ClearanceZone] = []
    for index, record in enumerate(value):
        if not isinstance(record, dict):
            raise ValueError(f"clearances[{index}] must be an object")
        footprint = _footprint(record.get("footprint_m"))
        if footprint is None:
            raise ValueError(f"clearances[{index}].footprint_m is required")
        zones.append(ClearanceZone(footprint=footprint, purpose=str(record["purpose"]),
                                   policy=ClearancePolicy(record.get("policy", "recommended")),
                                   source=record.get("source"),
                                   code_profile=record.get("code_profile")))
    return tuple(zones)


def _ports(value: object) -> tuple[ServicePort, ...]:
    if not isinstance(value, list):
        raise ValueError("ports must be a list")
    ports: list[ServicePort] = []
    for index, record in enumerate(value):
        if not isinstance(record, dict):
            raise ValueError(f"ports[{index}] must be an object")
        position = record.get("position_m")
        if not isinstance(position, list) or len(position) != 3:
            raise ValueError(f"ports[{index}].position_m must be [x, y, z]")
        ports.append(ServicePort(tag=str(record["tag"]), service=Service(record["service"]),
                                 position=tuple(m(float(part)) for part in position),
                                 connection_size=(m(float(record["connection_size_m"]))
                                                  if record.get("connection_size_m") is not None else None),
                                 notes=record.get("notes")))
    return tuple(ports)


def _mount(value: object) -> Mount:
    if value is None:
        return Mount()
    if not isinstance(value, dict):
        raise ValueError("mount must be an object")
    return Mount(kind=MountKind(value.get("kind", "floor")),
                 elevation=(m(float(value["elevation_m"])) if value.get("elevation_m") is not None else None),
                 drop=m(float(value["drop_m"])) if value.get("drop_m") is not None else None,
                 recessed_into_host_surface=bool(value.get("recessed_into_host_surface", False)))


def _provenance(value: object) -> dict[str, object] | None:
    if value is None:
        return None
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise ValueError("provenance must be an object with string keys")
    return value


def _point(value: object, field: str):
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError(f"{field} points must be [x, y]")
    return pt(m(float(value[0])), m(float(value[1])))
