"""What every duct end lands on, and the part it takes there (decision #114).

* a plenum's branch collar: the collar with its balancing damper (M1-106);
* an equipment port: the type's ``PortKit`` — transition and flex (Broan, M1-103);
* a terminal: a boot matched on (duct section, neck face) (M4-103/114/120), one per
  ``Register`` naming the run, wherever on it the register sits.

``end_landings`` is the reading ``mep.duct_terminations`` grades: an end that is none of
these, joins no duct and caps no served leg is UNKNOWN there.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from typehaus.model.ducts import DuctStandard, duct_size_text
from typehaus.quantities import M_PER_IN
from typehaus.resolve.duct_branches import duct_ends, section
from typehaus.resolve.mep_ports import placed_ports, port_at
from typehaus.resolve.mep_soffit import (
    DUCT_JOINT_TOLERANCE_M,
    duct_joint_index,
    plan_distance_to_segment,
)
from typehaus.resolve.model_ducts import Point3, ResolvedDuctPart

#: A duct end this close to an exact port or collar lands on it.
PORT_TOLERANCE_M = 1.0 * M_PER_IN
#: A register this close (plan) to a run's end is that end's terminal (``BOOT_REACH_M``).
BOOT_REACH_M = 36.0 * M_PER_IN


@dataclass(frozen=True)
class EndLanding:
    """One duct end and what it lands on: ``collar`` / ``port`` / ``equipment`` /
    ``terminal`` / ``joined`` / ``cap`` / None (nothing — UNKNOWN downstream)."""

    run_tag: str
    index: int
    point: Point3
    axis: Point3
    landing: str | None
    other: str | None = None
    port: Any = None


def _row_fields(row: Any) -> dict[str, Any]:
    return {"product_ref": row.product_ref if row else None,
            "fabricated": bool(row and row.fabricated), "integral": bool(row and row.integral),
            "length_m": row.length.meters if row and row.length else None,
            "width_m": row.width.meters if row and row.width else None,
            "height_m": row.height.meters if row and row.height else None}


def _in_case(model: Any, point: Point3) -> Any | None:
    """The equipment canvas object whose case holds ``point``, or None."""
    from shapely.geometry import Point, Polygon

    heights = {t.tag: t.height.meters for t in model.plan.library.equipment_types
               if getattr(t, "height", None) is not None}
    for obj in model.canvas_objects:
        if obj.kind != "Equipment" or not obj.footprint:
            continue
        if Polygon(obj.footprint).distance(Point(point[:2])) > DUCT_JOINT_TOLERANCE_M:
            continue
        z0 = obj.body_z0_m if obj.body_z0_m is not None else obj.z_m
        z1 = obj.body_z1_m if obj.body_z1_m is not None else z0 + heights.get(obj.type_ref, 0)
        if z1 <= z0 or z0 - DUCT_JOINT_TOLERANCE_M <= point[2] <= z1 + DUCT_JOINT_TOLERANCE_M:
            return obj
    return None


def _registers(model: Any) -> dict[str, list[Any]]:
    out: dict[str, list[Any]] = {}
    objects = {o.tag: o for o in model.canvas_objects}
    for el in model.plan.all_elements():
        if el.element_kind == "Register" and el.duct_ref and el.tag in objects:
            out.setdefault(el.duct_ref, []).append(objects[el.tag])
    return out


def end_landings(model: Any) -> list[EndLanding]:
    """Both ends of every run, classified."""
    registers = _registers(model)
    out: list[EndLanding] = []
    for duct in sorted(model.ducts, key=lambda d: d.tag):
        for index, point, axis in duct_ends(duct):
            out.append(EndLanding(duct.tag, index, point, axis,
                                  *_classify(model, duct, point, registers)))
    return out


def _classify(model: Any, duct: Any, point: Point3,
              registers: dict[str, list[Any]]) -> tuple[str | None, str | None, Any]:
    port = port_at(model, point[:2], point[2], duct_system=duct.system,
                   tolerance_m=PORT_TOLERANCE_M)
    if port is not None:
        return ("collar" if port.collar else "port"), port.equipment_tag, port
    for other in model.ducts:
        if other is not duct and len(other.path) > 1 and duct_joint_index(
                point[:2], point[2], other.path, other.z_m) is not None:
            return "joined", other.tag, None
    for obj in registers.get(duct.tag, ()):
        if math.dist(obj.position, point[:2]) <= BOOT_REACH_M:
            return "terminal", obj.tag, None
    case = _in_case(model, point)
    if case is not None:
        # A plenum stating a collar count and no layout: a branch at its collar size still
        # lands on a collar, just not a dimensioned one.
        machine = next((t for t in model.plan.library.equipment_types
                        if t.tag == case.type_ref), None)
        collar = getattr(machine, "port_diameter", None)
        if (collar is not None and duct.diameter_m is not None
                and abs(collar.meters - duct.diameter_m) < 1e-4):
            return "collar", case.tag, None
        return "equipment", case.tag, None
    leg = duct.path[:2] if point[:2] == tuple(duct.path[0]) else duct.path[-2:]
    for obj in registers.get(duct.tag, ()):
        if plan_distance_to_segment(obj.position, leg[0], leg[1])[0] <= BOOT_REACH_M:
            return "cap", obj.tag, None
    return None, None, None


def termination_parts(model: Any, standard: DuctStandard,
                      landings: list[EndLanding]) -> list[ResolvedDuctPart]:
    by_tag = {d.tag: d for d in model.ducts}
    types = {o.tag: o.type_ref for o in model.canvas_objects}
    ports = {(p.equipment_tag, p.port_tag): p for p in placed_ports(model)}
    out: list[ResolvedDuctPart] = []
    for end in landings:
        duct = by_tag[end.run_tag]
        size = section(duct)
        base = {"run_tag": duct.tag, "storey": duct.storey, "size": size,
                "point": end.point, "axis": end.axis, "other": end.other}
        if end.landing == "collar":
            row = standard.part("collar_damper", size)
            out.append(ResolvedDuctPart(kind="collar_damper",
                                        port=end.port.port_tag if end.port else None,
                                        gap=None if row else f"no collar_damper row at {size}",
                                        **base, **_row_fields(row)))
        elif end.landing in ("port", "equipment"):
            port_tag = end.port.port_tag if end.port is not None else None
            out.extend(_kit(standard, types.get(end.other), port_tag,
                            ports.get((end.other, port_tag)), base))
    out.extend(_boots(model, standard))
    return out


def _kit(standard: DuctStandard, type_ref: str | None, port_tag: str | None,
         port: Any, base: dict[str, Any]) -> list[ResolvedDuctPart]:
    kit = standard.port_kit(type_ref, port_tag)
    if kit is None:
        return []
    out = []
    port_size = (duct_size_text(port.section_m[0]) if port is not None and port.section_m
                 and abs(port.section_m[0] - port.section_m[1]) < 1e-6 else None)
    if kit.transition_product_ref and port_size != base["size"]:
        out.append(ResolvedDuctPart(
            kind="transition", port=port_tag, branch=port_size,
            product_ref=kit.transition_product_ref,
            length_m=kit.transition_length.meters if kit.transition_length else None,
            **base))
    if kit.flex_product_ref:
        out.append(ResolvedDuctPart(
            kind="connector" if kit.connector else "flex", port=port_tag,
            product_ref=kit.flex_product_ref,
            length_m=kit.flex_length.meters if kit.flex_length else None, **base))
    return out


def neck_text(register_type: Any) -> str:
    """A terminal's neck face as a boot is ordered: the inlet, else the neck box face,
    else ``none``."""
    neck = getattr(register_type, "neck", None)
    if neck is None:
        return "none"
    inlet = neck.inlet
    if inlet is not None:
        return (duct_size_text(inlet.width.meters) if inlet.section == "round"
                else duct_size_text(None, inlet.width.meters, inlet.height.meters))
    return duct_size_text(None, neck.width.meters, neck.height.meters)


def _boots(model: Any, standard: DuctStandard) -> list[ResolvedDuctPart]:
    types = {t.tag: t for t in model.plan.library.register_types}
    by_tag = {d.tag: d for d in model.ducts}
    out = []
    for duct_tag, objects in sorted(_registers(model).items()):
        duct = by_tag.get(duct_tag)
        if duct is None or len(duct.path) < 2:
            continue
        size = section(duct)
        for obj in sorted(objects, key=lambda o: o.tag):
            neck = neck_text(types.get(obj.type_ref))
            row = standard.part("boot", size, neck)
            point, axis = _nearest(duct, obj.position)
            out.append(ResolvedDuctPart(
                kind="boot", run_tag=duct.tag, storey=duct.storey, size=size, branch=neck,
                point=point, axis=axis, other=obj.tag,
                gap=None if row else f"no boot row for {size} to {neck}",
                **_row_fields(row)))
    return out


def _nearest(duct: Any, at: tuple[float, float]) -> tuple[Point3, Point3]:
    """The point on the run nearest ``at`` in plan, and the run's axis there."""
    best = None
    for i in range(len(duct.path) - 1):
        span, t = plan_distance_to_segment(at, duct.path[i], duct.path[i + 1])
        if best is None or span < best[0] - 1e-9:
            best = (span, i, t)
    _, i, t = best  # type: ignore[misc]
    a = (*duct.path[i], duct.z_m[i])
    b = (*duct.path[i + 1], duct.z_m[i + 1])
    point = tuple(pa + t * (pb - pa) for pa, pb in zip(a, b, strict=True))
    d = [pb - pa for pa, pb in zip(a, b, strict=True)]
    norm = math.sqrt(sum(v * v for v in d)) or 1.0
    return point, (d[0] / norm, d[1] / norm, d[2] / norm)  # type: ignore[return-value]
