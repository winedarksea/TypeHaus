"""Resolve pipeline: PlanModel -> ResolvedModel (→ 02 §Pipeline, → 11).

Whole-building: each storey resolves in the shared project-north frame, then storeys are
placed at derived elevations. Order: per-storey junction solve → openings → framing →
rooms → vertical stacking → derived boundary conditions.
"""

from __future__ import annotations

from typehaus.findings import Finding, Result, Severity
from typehaus.model.enums import ConditionKind
from typehaus.model.plan import PlanModel
from typehaus.resolve.framing.solver import frame_model
from typehaus.resolve.envelope import resolve_envelope_geometry
from typehaus.resolve.floors import resolve_floors
from typehaus.resolve.geometry import length, sub
from typehaus.resolve.model import BoundaryCondition, ResolvedModel, ResolvedOpening
from typehaus.resolve.rooms import resolve_rooms
from typehaus.resolve.stacking import resolve_stacking
from typehaus.resolve.topology import detect_gaps, resolve_storey_walls


def resolve(plan: PlanModel) -> tuple[ResolvedModel, list[Finding]]:
    """Resolve a validated plan into the IR. Returns (model, resolve-time findings)."""
    model = ResolvedModel(plan=plan)
    findings: list[Finding] = []

    ordered = sorted(plan.storeys, key=lambda s: s.elevation.meters)
    for storey in ordered:
        z0 = storey.elevation.meters
        z1 = z0 + storey.default_ceiling_height.meters
        findings.extend(detect_gaps(plan, storey.tag))
        model.walls.extend(resolve_storey_walls(plan, storey.tag, z0, z1))

    _resolve_openings(plan, model, findings)
    frame_model(plan, model)
    findings.extend(resolve_floors(model))
    findings.extend(resolve_envelope_geometry(model))
    findings.extend(resolve_rooms(plan, model))
    findings.extend(resolve_stacking(model))
    _assembly_change_conditions(model)

    return model, findings


def _resolve_openings(plan: PlanModel, model: ResolvedModel, findings: list[Finding]) -> None:
    for storey in plan.storeys:
        for el in plan.storey_elements(storey.tag):
            if el.element_kind not in ("Door", "Window", "RoughOpening"):
                continue
            rw = model.wall(el.host)
            if rw is None:
                findings.append(
                    Finding(
                        severity=Severity.ERROR, check_id="integrity.orphan_opening",
                        message=f"opening {el.tag} hosts on missing wall {el.host}",
                        element_tags=(el.tag,), result=Result.FAIL,
                    )
                )
                continue
            width, height, is_door, type_ref = _opening_size(plan, el)
            axis_len = length(sub(rw.axis[1], rw.axis[0]))
            center = _opening_center(plan, el, rw, axis_len, width)
            sill = _opening_sill(el)
            model.openings.append(
                ResolvedOpening(
                    uid=el.uid, tag=el.tag, host_wall=el.host, type_ref=type_ref,
                    width_m=width, height_m=height, sill_m=sill,
                    center_along_m=center, is_door=is_door,
                )
            )
            model.conditions.append(
                BoundaryCondition(
                    kind=ConditionKind.OPENING_PERIMETER, assemblies=(rw.assembly,),
                    detail="door" if is_door else "window", element_tags=(el.tag,),
                    key=f"opening_perimeter:{rw.assembly}",
                )
            )


def _opening_size(plan: PlanModel, el) -> tuple[float, float, bool, str | None]:
    if el.element_kind == "RoughOpening":
        return el.width.meters, el.height.meters, False, None
    is_door = el.element_kind == "Door"
    types = plan.library.door_types if is_door else plan.library.window_types
    t = next((x for x in types if x.tag == el.type_ref), None)
    if t is None:
        return 0.9, 2.0, is_door, el.type_ref
    return t.width.meters, t.height.meters, is_door, el.type_ref


def _opening_center(plan: PlanModel, el, rw, axis_len: float, width: float) -> float:
    pos = el.position
    if pos.mode == "centered":
        return axis_len / 2.0
    # from_node: offset measured from the named node along the axis to opening start
    start_tag = rw.tag  # resolve node ordering
    wall = plan.by_tag(rw.tag)
    off = pos.offset.meters if pos.offset else 0.0
    if wall is not None and pos.node == wall.end_node:
        return axis_len - off - width / 2.0
    return off + width / 2.0


def _opening_sill(el) -> float:
    if el.element_kind == "Door":
        return el.sill_height.meters if el.sill_height else 0.0
    return el.sill_height.meters if getattr(el, "sill_height", None) else 0.0


def _assembly_change_conditions(model: ResolvedModel) -> None:
    """Nodes where two walls of different assemblies meet become assembly-change
    conditions (#35, → 11b). Face jogs quantified downstream by the coverage check."""
    seen: set[str] = set()
    by_node: dict[str, list] = {}
    plan = model.plan
    for storey in plan.storeys:
        nodes = {e.tag for e in plan.storey_elements(storey.tag)
                 if e.element_kind == "Node"}
        for w in plan.storey_elements(storey.tag):
            if w.element_kind in ("Wall", "FoundationWall"):
                for nt in (w.start_node, w.end_node):
                    if nt in nodes:
                        by_node.setdefault(f"{storey.tag}/{nt}", []).append(w)
    for key, walls in by_node.items():
        asms = sorted({w.assembly for w in walls})
        if len(asms) > 1:
            k = f"assembly_change:{'|'.join(asms)}"
            if k in seen:
                continue
            seen.add(k)
            model.conditions.append(
                BoundaryCondition(
                    kind=ConditionKind.ASSEMBLY_CHANGE, assemblies=tuple(asms),
                    detail="node", element_tags=tuple(w.tag for w in walls), key=k,
                )
            )
