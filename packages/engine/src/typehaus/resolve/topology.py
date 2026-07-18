"""Wall topology + junction solver → per-layer polygons, gap detection (→ 11 §Topology).

Walls are edges between shared nodes. The junction solver closes corners by construction:
each wall's layer band is extended along its axis at each node by the neighbouring walls'
half-thickness, so orthogonal L/T corners resolve gap-free (the "no gaps" fix). Multi-way
priority follows JunctionPolicy; M1 ships the STRUCTURE_BUTTS_FINISH_WRAPS default.
"""

from __future__ import annotations

from typehaus.findings import Finding, Result, Severity
from typehaus.model.enums import LayerFunction
from typehaus.model.plan import PlanModel
from typehaus.resolve.geometry import length, rect_between, sub
from typehaus.resolve.model import ResolvedLayer, ResolvedWall

_EPS = 1e-4  # meters — cavity-insulation coincidence tolerance


def _added_thicknesses(layers: list) -> list[tuple[object, float, bool]]:
    """Per layer: (layer, added_thickness_m, is_cavity). Cavity insulation whose
    thickness matches an adjacent STRUCTURE layer adds no wall depth (→ resolver note)."""
    out: list[tuple[object, float, bool]] = []
    for i, layer in enumerate(layers):
        t = layer.thickness.meters
        cavity = False
        if layer.function is LayerFunction.INSULATION:
            for j in (i - 1, i + 1):
                if 0 <= j < len(layers) and layers[j].function is LayerFunction.STRUCTURE:
                    if abs(layers[j].thickness.meters - t) < _EPS:
                        cavity = True
                        break
        out.append((layer, 0.0 if cavity else t, cavity))
    return out


def _axis_offset_from_interior(layers: list, added: list, alignment: object,
                               total: float) -> float:
    """Where the node-to-node axis sits, measured from the interior face outward."""
    if alignment is None:
        return total / 2.0
    role = getattr(alignment, "role", "center")
    if role in ("center", ""):
        return total / 2.0
    # face:<name>-ext / face:<name>-int -> the outboard/inboard face of that layer.
    target = role.replace("face:", "")
    pos = 0.0
    for (layer, add_t, _cav) in added:
        pos_out = pos + add_t
        lname = getattr(layer, "name", "")
        if target.startswith(lname) or lname.startswith(target.split("-")[0]):
            return pos_out if target.endswith("ext") else pos
        pos = pos_out
    return total / 2.0


def resolve_wall_geometry(plan: PlanModel, wall, storey_tag: str, z0: float,
                          z1: float, half_by_node: dict[str, float],
                          is_foundation: bool) -> ResolvedWall | None:
    """Build a ResolvedWall with per-layer polygons for one authored wall."""
    nodes = {e.tag: e for e in plan.storey_elements(storey_tag) if e.element_kind == "Node"}
    n0, n1 = nodes.get(wall.start_node), nodes.get(wall.end_node)
    if n0 is None or n1 is None:
        return None
    p0, p1 = n0.position.xy_m, n1.position.xy_m
    asm = plan.library.resolve_assembly(wall.assembly)
    if asm is None:
        return None

    # Full inside→outside stack: interior lining, then the core layers.
    stack = list(asm.default_lining) + list(asm.layers)
    added = _added_thicknesses(stack)
    total = sum(a for (_l, a, _c) in added)
    axis_from_int = _axis_offset_from_interior(stack, added, wall.alignment, total)

    ext0 = half_by_node.get(wall.start_node, total / 2.0)
    ext1 = half_by_node.get(wall.end_node, total / 2.0)

    layers: list[ResolvedLayer] = []
    pos = 0.0
    for (layer, add_t, cavity) in added:
        # Cavity insulation shares the strip of its structure neighbour (draw in place).
        span_in = pos
        span_out = pos + (add_t if not cavity else 0.0)
        if cavity:
            # locate structure neighbour span already emitted or upcoming: reuse current pos
            span_out = pos + layer.thickness.meters
            left = span_in - axis_from_int
            right = span_out - axis_from_int
        else:
            left = span_in - axis_from_int
            right = span_out - axis_from_int
        ring = rect_between(p0, p1, left, right, ext0, ext1)
        layers.append(
            ResolvedLayer(
                name=layer.name,
                material_ref=layer.material_ref,
                function=layer.function.value,
                thickness_m=layer.thickness.meters,
                polygon=ring,
                control=frozenset(c.value for c in layer.control),
            )
        )
        if not cavity:
            pos = span_out

    return ResolvedWall(
        uid=wall.uid, tag=wall.tag, storey=storey_tag, assembly=wall.assembly,
        axis=(p0, p1), layers=tuple(layers), z0_m=z0, z1_m=z1,
        is_foundation=is_foundation,
    )


def storey_wall_half_thickness(plan: PlanModel, storey_tag: str) -> dict[str, float]:
    """Per node: the max half-thickness of walls meeting there (for corner extension)."""
    half: dict[str, float] = {}
    for wall in _walls(plan, storey_tag):
        asm = plan.library.resolve_assembly(wall.assembly)
        if asm is None:
            continue
        stack = list(asm.default_lining) + list(asm.layers)
        total = sum(a for (_l, a, _c) in _added_thicknesses(stack))
        for node_tag in (wall.start_node, wall.end_node):
            half[node_tag] = max(half.get(node_tag, 0.0), total / 2.0)
    return half


def detect_gaps(plan: PlanModel, storey_tag: str) -> list[Finding]:
    """Any node with exactly one non-open_end wall edge is a gap error (→ 11)."""
    degree: dict[str, int] = {}
    for wall in _walls(plan, storey_tag):
        for nt in (wall.start_node, wall.end_node):
            degree[nt] = degree.get(nt, 0) + 1
    findings: list[Finding] = []
    for node in (e for e in plan.storey_elements(storey_tag) if e.element_kind == "Node"):
        if node.open_end:
            continue
        d = degree.get(node.tag, 0)
        if d == 1:
            findings.append(
                Finding(
                    severity=Severity.ERROR,
                    check_id="integrity.wall_loop_open",
                    message=f"node {node.tag} has a single wall edge — loop not closed",
                    element_tags=(node.tag,),
                    fix_hint="add the missing wall, or mark the node open_end=True",
                    result=Result.FAIL,
                )
            )
    return findings


def _walls(plan: PlanModel, storey_tag: str) -> list:
    return [
        e for e in plan.storey_elements(storey_tag)
        if e.element_kind in ("Wall", "FoundationWall")
    ]


def resolve_storey_walls(plan: PlanModel, storey_tag: str, z0: float,
                         z1: float) -> list[ResolvedWall]:
    half = storey_wall_half_thickness(plan, storey_tag)
    out: list[ResolvedWall] = []
    for wall in _walls(plan, storey_tag):
        rw = resolve_wall_geometry(
            plan, wall, storey_tag, z0, z1, half,
            is_foundation=wall.element_kind == "FoundationWall",
        )
        if rw is not None:
            out.append(rw)
    return out


def wall_axis_length(rw: ResolvedWall) -> float:
    return length(sub(rw.axis[1], rw.axis[0]))
