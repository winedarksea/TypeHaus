"""What every duct end lands on, and the part it takes there (decision #114).

* a plenum's branch collar: the collar with its balancing damper (M1-106);
* an equipment port: the type's ``PortKit`` — transition and flex (Broan, M1-103);
* a terminal: a boot matched on (duct section, neck face) (M4-103/114/120), one per
  ``terminal_joints`` end, drop, inlet or side joint (decision #136), at the joint's point.

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
from typehaus.resolve.flex_bend import run_bend
from typehaus.resolve.mep_ports import placed_ports, port_at
from typehaus.resolve.mep_soffit import DUCT_JOINT_TOLERANCE_M, duct_joint_index, end_joins
from typehaus.resolve.model_ducts import Point3, ResolvedDuctPart
from typehaus.resolve.terminal_joints import DROP, END, INLET, SIDE, TerminalJoint, terminal_joints

#: A duct end this close to an exact port or collar lands on it.
PORT_TOLERANCE_M = 1.0 * M_PER_IN
#: A stub past the last take-off this long (along the run) is a capped trunk end.
CAP_STUB_MAX_M = 12.0 * M_PER_IN


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


def _end_leg(duct: Any, index: int) -> int:
    return 0 if index == 0 else len(duct.path) - 2


def _branch_stub(model: Any, duct: Any, index: int) -> str | None:
    """The run taking off this run's end leg nearest its end, within ``CAP_STUB_MAX_M``
    measured along the run: like a boot, it makes the stub past it a cap."""
    leg, end = _end_leg(duct, index), (*duct.path[index], duct.z_m[index])
    best: tuple[float, str] | None = None
    for other in model.ducts:
        if other is duct or len(other.path) < 2:
            continue
        for _, p, _ in duct_ends(other):
            stub = math.dist(p, end)
            if (stub <= CAP_STUB_MAX_M and (best is None or (stub, other.tag) < best)
                    and duct_joint_index(p[:2], p[2], duct.path, duct.z_m) == leg):
                best = (stub, other.tag)
    return best[1] if best else None


def _side_caps(model: Any, joints: dict[str, TerminalJoint]) -> dict[tuple[str, int], str]:
    """``{(run, end index): register}``: a SIDE joint on a run's end leg caps the stub
    past it (the nearest joint to that end wins)."""
    by_tag = {d.tag: d for d in model.ducts}
    best: dict[tuple[str, int], tuple[float, str]] = {}
    for tag, joint in joints.items():
        duct = by_tag.get(joint.run)
        if joint.kind != SIDE or duct is None:
            continue
        for index in {0, len(duct.path) - 1}:
            if joint.leg == _end_leg(duct, index):
                span = math.dist(joint.point, (*duct.path[index], duct.z_m[index]))
                if (key := (duct.tag, index)) not in best or (span, tag) < best[key]:
                    best[key] = (span, tag)
    return {key: tag for key, (_, tag) in best.items()}


def capped_by(model: Any, joints: dict[str, TerminalJoint] | None = None,
              ) -> dict[tuple[str, int], str]:
    """``{(run tag, end vertex index): what caps it}``: the register whose SIDE joint stands
    on the end leg, else the run taking off it within ``CAP_STUB_MAX_M`` along the run. Pure
    of the end's landing: callers read it for the ends that land on nothing else."""
    joints = terminal_joints(model) if joints is None else joints
    out = _side_caps(model, joints)
    for duct in model.ducts:
        for index, _, _ in duct_ends(duct):
            if (duct.tag, index) not in out and (tag := _branch_stub(model, duct, index)):
                out[(duct.tag, index)] = tag
    return out


def end_landings(model: Any, joints: dict[str, TerminalJoint] | None = None,
                 ) -> list[EndLanding]:
    """Both ends of every run, classified."""
    joints = terminal_joints(model) if joints is None else joints
    by_end = {(j.run, j.end_index): j for j in joints.values()
              if j.kind in (END, DROP, INLET) and j.end_index is not None}
    side = _side_caps(model, joints)
    out: list[EndLanding] = []
    for duct in sorted(model.ducts, key=lambda d: d.tag):
        for index, point, axis in duct_ends(duct):
            out.append(EndLanding(duct.tag, index, point, axis, *_classify(
                model, duct, index, point, by_end.get((duct.tag, index)),
                side.get((duct.tag, index)))))
    return out


def _classify(model: Any, duct: Any, index: int, point: Point3, joint: TerminalJoint | None,
              side_cap: str | None) -> tuple[str | None, str | None, Any]:
    port = port_at(model, point[:2], point[2], duct_system=duct.system,
                   tolerance_m=PORT_TOLERANCE_M)
    if port is not None:
        return ("collar" if port.collar else "port"), port.equipment_tag, port
    for other in model.ducts:
        if other is not duct and len(other.path) > 1 and end_joins(
                duct, point[:2], point[2], other):
            return "joined", other.tag, None
    # A drop seated badly lands on nothing; an inlet's fit is graded elsewhere.
    if joint is not None and not (joint.kind == DROP and joint.problem):
        return "terminal", joint.register, None
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
    cap = side_cap or _branch_stub(model, duct, index)
    return ("cap", cap, None) if cap else (None, None, None)


def termination_parts(model: Any, standard: DuctStandard, landings: list[EndLanding],
                      joints: dict[str, TerminalJoint] | None = None,
                      ) -> list[ResolvedDuctPart]:
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
        elif end.landing == "cap":
            row = standard.part("cap", size)
            out.append(ResolvedDuctPart(kind="cap", gap=None if row else f"no cap row at {size}",
                                        **base, **_row_fields(row)))
        elif end.landing in ("port", "equipment"):
            port_tag = end.port.port_tag if end.port is not None else None
            out.extend(_kit(standard, types.get(end.other), port_tag,
                            ports.get((end.other, port_tag)), base, (duct, end.index)))
    out.extend(_boots(model, standard, terminal_joints(model) if joints is None else joints))
    return out


def _kit(standard: DuctStandard, type_ref: str | None, port_tag: str | None,
         port: Any, base: dict[str, Any], end: tuple[Any, int]) -> list[ResolvedDuctPart]:
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
        length = kit.flex_length.meters if kit.flex_length else None
        bent: dict[str, Any] = {}
        trans = (out[0].length_m or 0.0) if out else 0.0  # an unread transition counts 0
        hit = run_bend(end[0], end[1], kit, standard, transition_m=trans)
        if hit is not None:  # the lead turns: cut the flex to the bend, not the nominal
            length = hit[0].flex_m
            bent = {"bend_deg": hit[0].angle_deg, "bend_vertex": hit[1],
                    "bend_out_m": hit[0].out_m}
        out.append(ResolvedDuctPart(
            kind="connector" if kit.connector else "flex", port=port_tag,
            product_ref=kit.flex_product_ref, length_m=length, **bent, **base))
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


def _boots(model: Any, standard: DuctStandard,
           joints: dict[str, TerminalJoint]) -> list[ResolvedDuctPart]:
    """One boot per END, DROP, INLET or SIDE joint, at the joint; none for THROUGH or
    UNREACHED (``mep.register_reach`` grades those)."""
    types = {t.tag: t for t in model.plan.library.register_types}
    refs = {o.tag: o.type_ref for o in model.canvas_objects}
    by_tag = {d.tag: d for d in model.ducts}
    out = []
    for joint in sorted(joints.values(), key=lambda j: (j.run, j.register)):
        duct = by_tag.get(joint.run)
        if duct is None or joint.kind not in (END, DROP, INLET, SIDE) or joint.point is None:
            continue
        size = section(duct)
        neck = neck_text(types.get(refs.get(joint.register)))
        row = standard.part("boot", size, neck)
        out.append(ResolvedDuctPart(
            kind="boot", run_tag=duct.tag, storey=duct.storey, size=size, branch=neck,
            point=joint.point, axis=joint.axis, other=joint.register,
            gap=None if row else f"no boot row for {size} to {neck}",
            joint=joint.kind, face=joint.face, turn=joint.turn, **_row_fields(row)))
    return out
