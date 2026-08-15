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
from typehaus.resolve.drainage import resolve_drainage
from typehaus.resolve.construction import apply_construction_rules
from typehaus.resolve.envelope import resolve_columns_and_beams, resolve_envelope_geometry
from typehaus.resolve.floor_heat import resolve_floor_heat
from typehaus.resolve.floors import resolve_floors
from typehaus.resolve.framing.furring import frame_furring
from typehaus.resolve.framing.roof import frame_roofs
from typehaus.resolve.framing.soffit import frame_soffits
from typehaus.resolve.framing.solver import frame_model
from typehaus.resolve.geometry import length, sub
from typehaus.resolve.mep import resolve_mep
from typehaus.resolve.solar import resolve_solar
from typehaus.resolve.model import BoundaryCondition, ResolvedModel, ResolvedOpening
from typehaus.resolve.paneling import resolve_paneling
from typehaus.resolve.placeables import resolve_placeables
from typehaus.resolve.platform import extend_walls_to_platform
from typehaus.resolve.roof_edge import resolve_roof_edges
from typehaus.resolve.roof_geometry import apply_to_roof_wall_tops, apply_truss_heel_lift
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
        # A truss roof's deck rises by its raised heel; establish that *before* anything
        # reads the plane, or every ToRoof wall rakes to a stale roof and stops a
        # heel-plus-chord short of it (a band of daylight at the gable).
        apply_truss_heel_lift(model)
        apply_to_roof_wall_tops(model)
    with _stage("construction"):
        # Pre-framing (#45): apply authored ConstructionRule returns (sill/foam/liner/masonry
        # laps) as construction geometry + take-off + overlay data, before members are framed.
        findings.extend(apply_construction_rules(model))
    with _stage("framing"):
        findings.extend(frame_model(plan, model))
        # Strapping over whatever the wall turned out to be: a separate pass because a
        # FURRING layer frames its own grid in its own band even when the wall behind it
        # is a pour, and `frame_wall` returns early for those (→ framing/furring.py).
        findings.extend(frame_furring(plan, model))
        # Soffit ladders hang off records the envelope stage already created.
        findings.extend(frame_soffits(model))
        findings.extend(frame_roofs(model))
        # After roof framing: the wall→roof closure and the eave/rake trim attach to the
        # roof's member list, which frame_roofs rebuilds.
        resolve_roof_edges(model)
        # After roof framing so authored ridge Beams are already emitted as roof members.
        findings.extend(resolve_columns_and_beams(model))
    with _stage("floors"):
        findings.extend(resolve_floors(model))
    with _stage("mep"):
        findings.extend(resolve_mep(model))
    with _stage("solar"):
        # After framing: panels ride the resolved roof planes.
        findings.extend(resolve_solar(model))
    with _stage("accessories"):
        # Dowels/connectors/railings/sumps/vents/edge-trim → solids. After floors+mep so
        # slabs a sump hosts into already exist in model.solids.
        findings.extend(resolve_accessories(model))
        # Authored site drainage, beside the accessories for the same reason: it reads the
        # slabs and footings the earlier stages produced and adds only solids.
        findings.extend(resolve_drainage(model))
    with _stage("rooms"):
        findings.extend(resolve_rooms(plan, model))
    with _stage("paneling"):
        findings.extend(resolve_paneling(plan, model))
    with _stage("placeables"):
        findings.extend(resolve_placeables(plan, model))
    with _stage("floor_heat"):
        findings.extend(resolve_floor_heat(model))
    with _stage("stacking"):
        findings.extend(resolve_stacking(model))
    with _stage("conditions"):
        _assembly_change_conditions(model)
    with _stage("geometry"):
        # Last: every earlier stage's records are inputs to it. The emitters read this
        # instead of re-deriving solids from the records themselves.
        from typehaus.resolve.geometry_build import build_geometry

        model.geometry = build_geometry(model)

    model.index_by_tag()
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
    apply_truss_heel_lift(model)
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
            operation = _door_operation(plan, el) if is_door else None
            swing_clearance = (_door_swing_clearance(rw, center, width, el, operation)
                               if is_door else ())
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


def _door_operation(plan: PlanModel, el) -> str:
    """A door's leaf motion, off its ``DoorType``. Defaults to ``"swing"``, which is what an
    untyped door has always been drawn and framed as."""
    door_type = next((x for x in plan.library.door_types if x.tag == el.type_ref), None)
    operation = getattr(door_type, "operation", None)
    return str(getattr(operation, "value", operation) or "swing")


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


# How much of a leaf's width actually sweeps into the room, by how the leaf moves. A slider,
# a pocket door and an overhead sectional sweep nothing at all — the leaf stays in the wall
# plane or runs up onto a ceiling track — and giving them the 90-degree quarter-circle every
# door used to get invented a clearance they do not have. Catlin's mudroom-closet bypass
# (D-M-MUDC) reported a permanent `integrity.door_swing_conflict` against the bench in front
# of it for exactly that reason, and the plan sheets drew an arc for a slider besides. A
# bifold's leaves do project, but folded, so roughly half the width rather than all of it.
_LEAF_SWEEP_FRACTION: dict[str, float] = {
    "swing": 1.0,
    "double_swing": 0.5,  # a French pair is two leaves, each half the rough opening
    "bifold": 0.5,
    "slide": 0.0,
    "pocket": 0.0,
    "overhead": 0.0,
}


def _door_swing_clearance(wall, center_along_m: float, width_m: float, door,
                          operation: str = "swing") -> list[tuple[float, float]]:
    """Approximate the door leaf sweep as a true local-sector polygon in plan space.

    ``operation`` selects how much of the leaf sweeps (:data:`_LEAF_SWEEP_FRACTION`); a
    non-swinging door returns an empty ring, which every consumer already treats as "no
    clearance to draw or defend".
    """
    sweep = _LEAF_SWEEP_FRACTION.get(str(operation or "swing"), 1.0)
    if sweep <= 0.0:
        return []
    (sx, sy), (ex, ey) = wall.axis
    length = math.hypot(ex - sx, ey - sy) or 1.0
    tangent = ((ex - sx) / length, (ey - sy) / length)
    start = (sx + tangent[0] * (center_along_m - width_m / 2),
             sy + tangent[1] * (center_along_m - width_m / 2))
    hinge_at_start = not bool(getattr(door, "flip_hinge", False))
    hinge = start if hinge_at_start else (start[0] + tangent[0] * width_m, start[1] + tangent[1] * width_m)
    closed = tangent if hinge_at_start else (-tangent[0], -tangent[1])
    direction = -1 if bool(getattr(door, "flip_swing", False)) else 1
    radius = width_m * sweep
    points = [hinge]
    for index in range(9):
        angle = direction * math.pi / 2 * index / 8
        cos, sin = math.cos(angle), math.sin(angle)
        points.append((hinge[0] + radius * (closed[0] * cos - closed[1] * sin),
                       hinge[1] + radius * (closed[0] * sin + closed[1] * cos)))
    return points


# An assembly change is an in-plan face jog *along a wall run*. Three gates keep the
# derivation from firing on junctions that are not that:
_MIN_Z_OVERLAP_M = 0.025  # walls meeting only at a bearing plane are stacked, not jogged
_COLLINEAR_DOT = -0.9  # directions away from the node ~opposite → the run continues


def _assembly_change_conditions(model: ResolvedModel) -> None:
    """Nodes where a wall *run continues* in a different assembly become assembly-change
    conditions (#35, → 11b). Face jogs quantified downstream by the coverage check.

    Sharing a node is not enough — three gates keep junction noise out of the set:

    * **collinearity** — the two walls must run through the node roughly end-to-end.
      A partition tee-ing into an exterior wall or two walls cornering is a *junction*
      (solved and documented elsewhere); the detail this condition scaffolds cuts
      perpendicular to a run and cannot show a corner or tee at all.
    * **z-overlap** — the walls must share more than ``_MIN_Z_OVERLAP_M`` of height.
      A masonry railing standing *on* the concrete wall below reuses its nodes but
      never coexists with it in any plan cut.
    * **layer equivalence** — assemblies whose layer sequences are the same materials
      (thickness aside) present no documentable junction; see ``_layers_equivalent``.
    """
    plan = model.plan
    seen: set[str] = set()
    for storey in plan.storeys:
        node_xy = {e.tag: (e.position.x.meters, e.position.y.meters)
                   for e in plan.storey_elements(storey.tag)
                   if e.element_kind == "Node"}
        by_node: dict[str, list] = {}
        for w in plan.storey_elements(storey.tag):
            if w.element_kind in ("Wall", "FoundationWall"):
                for nt in (w.start_node, w.end_node):
                    if nt in node_xy:
                        by_node.setdefault(nt, []).append(w)
        for node_tag, walls in by_node.items():
            changed = _assembly_change_walls(model, storey, node_tag, walls, node_xy)
            if not changed:
                continue
            asms = sorted({w.assembly for w in changed})
            k = f"assembly_change:{'|'.join(asms)}"
            if k in seen:
                continue
            seen.add(k)
            model.conditions.append(
                BoundaryCondition(
                    kind=ConditionKind.ASSEMBLY_CHANGE, assemblies=tuple(asms),
                    detail="node", element_tags=tuple(w.tag for w in changed), key=k,
                )
            )


def _assembly_change_walls(model: ResolvedModel, storey, node_tag: str, walls: list,
                           node_xy: dict) -> list:
    """The walls at this node that actually participate in an assembly change."""
    picked: list = []
    picked_tags: set[str] = set()
    for i, a in enumerate(walls):
        for b in walls[i + 1:]:
            if a.assembly == b.assembly:
                continue
            if _layers_equivalent(model.plan, a.assembly, b.assembly):
                continue
            if not _runs_through(a, b, node_tag, node_xy):
                continue
            if _z_overlap(model, storey, a, b) <= _MIN_Z_OVERLAP_M:
                continue
            for w in (a, b):
                if w.tag not in picked_tags:
                    picked_tags.add(w.tag)
                    picked.append(w)
    return picked


def _runs_through(a, b, node_tag: str, node_xy: dict) -> bool:
    """True when the two walls continue one run through the node (roughly end-to-end)."""
    da = _direction_away(a, node_tag, node_xy)
    db = _direction_away(b, node_tag, node_xy)
    if da is None or db is None:
        return False
    return da[0] * db[0] + da[1] * db[1] <= _COLLINEAR_DOT


def _direction_away(w, node_tag: str, node_xy: dict):
    """Unit vector from the shared node toward the wall's other end, if resolvable."""
    other = w.end_node if w.start_node == node_tag else w.start_node
    p, q = node_xy.get(node_tag), node_xy.get(other)
    if p is None or q is None:
        return None
    dx, dy = q[0] - p[0], q[1] - p[1]
    n = math.hypot(dx, dy)
    if n < 1e-9:
        return None
    return dx / n, dy / n


def _z_overlap(model: ResolvedModel, storey, a, b) -> float:
    """Shared wall height in metres (<= 0 when the walls never coexist vertically)."""
    a0, a1 = _wall_z_range(model, storey, a)
    b0, b1 = _wall_z_range(model, storey, b)
    return min(a1, b1) - max(a0, b0)


def _wall_z_range(model: ResolvedModel, storey, w) -> tuple[float, float]:
    """The wall's vertical extent — resolved when available, authored/storey defaults else."""
    rw = model.wall(w.tag)
    if rw is not None:
        return rw.z0_m, rw.z1_m
    z0 = storey.elevation.meters
    z1 = z0 + storey.default_ceiling_height.meters
    bottom = getattr(w, "bottom_elevation", None)
    top = getattr(w, "top_elevation", None)
    if bottom is not None:
        z0 = bottom.meters
    if top is not None:
        z1 = top.meters
    return z0, z1


def _layers_equivalent(plan: PlanModel, asm_tag_a: str, asm_tag_b: str) -> bool:
    """Assemblies whose layer sequences are the same materials in the same roles.

    A 12" and a 16" wall of one concrete layer differ only in thickness — there is no
    junction of dissimilar construction to document, so the pair does not constitute an
    assembly change. Same philosophy as ``diff/equivalence.py`` (semantic identity over
    literal identity), but deliberately not imported from there: that module compares
    emitted IFC, which is the wrong altitude for a resolve-time derivation gate.
    """
    a = plan.library.resolve_assembly(asm_tag_a)
    b = plan.library.resolve_assembly(asm_tag_b)
    if a is None or b is None:
        return False

    def signature(asm) -> tuple:
        return tuple((layer.material_ref, layer.function) for layer in asm.layers)

    return signature(a) == signature(b)
