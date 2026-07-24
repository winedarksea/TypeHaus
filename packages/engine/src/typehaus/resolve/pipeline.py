"""Resolve pipeline: PlanModel -> ResolvedModel (→ 02 §Pipeline, → 11).

Whole-building: each storey resolves in the shared project-north frame, then storeys are
placed at derived elevations. Order: per-storey junction solve → openings → framing →
rooms → vertical stacking → derived boundary conditions.
"""

from __future__ import annotations

import math
import time
from contextlib import contextmanager

from typehaus.findings import Finding, Result, Severity
from typehaus.model.enums import ConditionKind
from typehaus.model.plan import PlanModel
from typehaus.resolve.accessories import resolve_accessories
from typehaus.resolve.construction import apply_construction_rules
from typehaus.resolve.envelope import resolve_columns_and_beams, resolve_envelope_geometry
from typehaus.resolve.floor_heat import resolve_floor_heat
from typehaus.resolve.floors import resolve_floors
from typehaus.resolve.framing.roof import frame_roofs
from typehaus.resolve.framing.solver import frame_model
from typehaus.resolve.geometry import length, sub
from typehaus.resolve.mep import resolve_mep
from typehaus.resolve.model import BoundaryCondition, ResolvedModel, ResolvedOpening
from typehaus.resolve.placeables import resolve_placeables
from typehaus.resolve.platform import extend_walls_to_platform
from typehaus.resolve.roof_geometry import apply_to_roof_wall_tops
from typehaus.resolve.rooms import resolve_rooms
from typehaus.resolve.stacking import resolve_stacking
from typehaus.resolve.topology import detect_gaps, resolve_storey_walls


def resolve(plan: PlanModel) -> tuple[ResolvedModel, list[Finding]]:
    """Resolve a validated plan into the IR. Returns (model, resolve-time findings)."""
    model = ResolvedModel(plan=plan)
    findings: list[Finding] = []

    @contextmanager
    def _stage(name: str):
        t0 = time.perf_counter()
        try:
            yield
        finally:
            model.timings[name] = (time.perf_counter() - t0) * 1000.0

    with _stage("junctions"):
        ordered = sorted(plan.storeys, key=lambda s: s.elevation.meters)
        for storey in ordered:
            z0 = storey.elevation.meters
            z1 = z0 + storey.default_ceiling_height.meters
            findings.extend(detect_gaps(plan, storey.tag))
            walls, junctions, junction_findings = resolve_storey_walls(
                plan, storey.tag, z0, z1
            )
            model.walls.extend(walls)
            model.junctions.extend(junctions)
            findings.extend(junction_findings)
        extend_walls_to_platform(model)

    with _stage("openings"):
        _resolve_openings(plan, model, findings)
    with _stage("envelope"):
        findings.extend(resolve_envelope_geometry(model))
        apply_to_roof_wall_tops(model)
    with _stage("construction"):
        # Pre-framing (#45): apply authored ConstructionRule returns (sill/foam/liner/masonry
        # laps) as construction geometry + take-off + overlay data, before members are framed.
        findings.extend(apply_construction_rules(model))
    with _stage("framing"):
        findings.extend(frame_model(plan, model))
        findings.extend(frame_roofs(model))
        # After roof framing so authored ridge Beams are already emitted as roof members.
        findings.extend(resolve_columns_and_beams(model))
    with _stage("floors"):
        findings.extend(resolve_floors(model))
    with _stage("mep"):
        findings.extend(resolve_mep(model))
    with _stage("accessories"):
        # Dowels/connectors/railings/sumps/vents/edge-trim → solids. After floors+mep so
        # slabs a sump hosts into already exist in model.solids.
        findings.extend(resolve_accessories(model))
    with _stage("rooms"):
        findings.extend(resolve_rooms(plan, model))
    with _stage("placeables"):
        findings.extend(resolve_placeables(plan, model))
    with _stage("floor_heat"):
        findings.extend(resolve_floor_heat(model))
    with _stage("stacking"):
        findings.extend(resolve_stacking(model))
    with _stage("conditions"):
        _assembly_change_conditions(model)

    return model, findings


def resolve_preview(plan: PlanModel) -> ResolvedModel:
    """A reduced resolve for a live drag preview (→ responsiveness plan, Phase 4): junctions,
    openings, envelope, and rooms only — skips framing/floors/floor_heat/stacking/conditions,
    which a ghost preview during a drag doesn't render and which are the pipeline's costlier
    stages. Runs no checks and produces no findings; callers must not treat this as the
    authoritative resolved model, only as fast-turnaround geometry for the overlay."""
    model = ResolvedModel(plan=plan)
    findings: list[Finding] = []

    ordered = sorted(plan.storeys, key=lambda s: s.elevation.meters)
    for storey in ordered:
        z0 = storey.elevation.meters
        z1 = z0 + storey.default_ceiling_height.meters
        walls, junctions, _junction_findings = resolve_storey_walls(
            plan, storey.tag, z0, z1
        )
        model.walls.extend(walls)
        model.junctions.extend(junctions)
    extend_walls_to_platform(model)
    _resolve_openings(plan, model, findings)
    resolve_envelope_geometry(model)
    apply_to_roof_wall_tops(model)
    resolve_rooms(plan, model)
    resolve_placeables(plan, model)
    return model


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
            kind = {"Door": "door", "Window": "window", "RoughOpening": "rough_opening"}[el.element_kind]
            axis_len = length(sub(rw.axis[1], rw.axis[0]))
            center = _opening_center(plan, el, rw, axis_len, width)
            sill = _opening_sill(el)
            swing_clearance = _door_swing_clearance(rw, center, width, el) if is_door else ()
            framing_bumper = _opening_framing_bumper(rw, center, width)
            arch = getattr(el, "arch", None)
            arch_rise = arch.rise.meters if arch is not None else 0.0
            model.openings.append(
                ResolvedOpening(
                    uid=el.uid, tag=el.tag, host_wall=el.host, type_ref=type_ref,
                    width_m=width, height_m=height, sill_m=sill,
                    center_along_m=center, kind=kind, is_door=is_door,
                    swing_clearance=swing_clearance, framing_bumper=framing_bumper,
                    arch_rise_m=arch_rise,
                )
            )
            model.conditions.append(
                BoundaryCondition(
                    kind=ConditionKind.OPENING_PERIMETER, assemblies=(rw.assembly,),
                    detail=kind, element_tags=(el.tag,),
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


def _opening_framing_bumper(wall, center_along_m: float, width_m: float) -> list[tuple[float, float]]:
    """A thin resolved overlay around a rough opening for framing-aware placement preview."""
    (sx, sy), (ex, ey) = wall.axis
    length = math.hypot(ex - sx, ey - sy) or 1.0
    tangent = ((ex - sx) / length, (ey - sy) / length)
    normal = (-tangent[1], tangent[0])
    center = (sx + tangent[0] * center_along_m, sy + tangent[1] * center_along_m)
    half_width = width_m / 2 + .05
    half_depth = wall.thickness_m / 2 + .05
    return [(center[0] + sign_u * tangent[0] * half_width + sign_n * normal[0] * half_depth,
             center[1] + sign_u * tangent[1] * half_width + sign_n * normal[1] * half_depth)
            for sign_u, sign_n in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def _door_swing_clearance(wall, center_along_m: float, width_m: float, door) -> list[tuple[float, float]]:
    """Approximate the door leaf sweep as a true local-sector polygon in plan space."""
    (sx, sy), (ex, ey) = wall.axis
    length = math.hypot(ex - sx, ey - sy) or 1.0
    tangent = ((ex - sx) / length, (ey - sy) / length)
    start = (sx + tangent[0] * (center_along_m - width_m / 2),
             sy + tangent[1] * (center_along_m - width_m / 2))
    hinge_at_start = not bool(getattr(door, "flip_hinge", False))
    hinge = start if hinge_at_start else (start[0] + tangent[0] * width_m, start[1] + tangent[1] * width_m)
    closed = tangent if hinge_at_start else (-tangent[0], -tangent[1])
    direction = -1 if bool(getattr(door, "flip_swing", False)) else 1
    points = [hinge]
    for index in range(9):
        angle = direction * math.pi / 2 * index / 8
        cos, sin = math.cos(angle), math.sin(angle)
        points.append((hinge[0] + width_m * (closed[0] * cos - closed[1] * sin),
                       hinge[1] + width_m * (closed[0] * sin + closed[1] * cos)))
    return points


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
