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
from typehaus.resolve.orientation import storey_outward_sign

_EPS = 1e-4  # meters — cavity-insulation coincidence tolerance


def _cavity_host(layers: list, index: int) -> int | None:
    """Index of the STRUCTURE layer a legacy sibling batt fills, or None.

    Back-compat only: assemblies used to spell cavity insulation as its own INSULATION
    layer next to the studs, at the same thickness. Those add no depth and share the
    structure layer's polygon — the modern spelling is ``Layer.cavity`` (:class:`CavityFill`).
    """
    layer = layers[index]
    if layer.function is not LayerFunction.INSULATION:
        return None
    for j in (index - 1, index + 1):
        if 0 <= j < len(layers) and layers[j].function is LayerFunction.STRUCTURE:
            if abs(layers[j].thickness.meters - layer.thickness.meters) < _EPS:
                return j
    return None


def _added_thicknesses(layers: list) -> list[tuple[object, float, bool]]:
    """Per layer: (layer, added_thickness_m, is_cavity).

    Cavity insulation — whether the modern ``Layer.cavity`` (which is not a list entry at
    all) or a legacy sibling batt layer — occupies the framing bays and adds no wall depth.
    """
    out: list[tuple[object, float, bool]] = []
    for i, layer in enumerate(layers):
        cavity = _cavity_host(layers, i) is not None
        out.append((layer, 0.0 if cavity else layer.thickness.meters, cavity))
    return out


def _axis_offset_from_interior(layers: list, added: list, alignment: object,
                               total: float) -> float:
    """Where the node-to-node axis sits, measured from the interior face outward.

    ``FaceRef.offset`` shifts the axis off the named face, positive = further outboard.
    That is what lets a layer be added to one side of an existing wall without moving the
    layer that actually holds the datum — e.g. lining the sauna side of a bearing wall
    while the concrete stays centred on the structural grid.
    """
    base = _face_offset_from_interior(layers, added, alignment, total)
    shift = getattr(alignment, "offset", None) if alignment is not None else None
    return base + (shift.meters if shift is not None else 0.0)


def _face_offset_from_interior(layers: list, added: list, alignment: object,
                               total: float) -> float:
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
                          is_foundation: bool,
                          outward_sign: float = 1.0) -> ResolvedWall | None:
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

    # Interior→exterior spans, walked over the depth-bearing layers only. A cavity layer
    # borrows its host structure layer's span, so it must be placed after the walk rather
    # than during it (a batt authored *before* the studs would otherwise land nowhere).
    spans: list[tuple[float, float]] = []
    pos = 0.0
    for (_layer, add_t, cavity) in added:
        spans.append((pos, pos + add_t))
        if not cavity:
            pos += add_t

    def _ring(span_in: float, span_out: float):
        return rect_between(p0, p1, (span_in - axis_from_int) * outward_sign,
                            (span_out - axis_from_int) * outward_sign, ext0, ext1)

    layers: list[ResolvedLayer] = []
    for index, (layer, _add_t, cavity) in enumerate(added):
        host_index = _cavity_host(stack, index) if cavity else None
        if host_index is not None:
            # Share the host structure layer's strip, inset from its interior face.
            host_in, _host_out = spans[host_index]
            span_in, span_out = host_in, host_in + layer.thickness.meters
        else:
            span_in, span_out = spans[index]
        host_name = stack[host_index].name if host_index is not None else None
        layers.append(
            ResolvedLayer(
                name=layer.name,
                material_ref=layer.material_ref,
                function=layer.function.value,
                thickness_m=layer.thickness.meters,
                polygon=_ring(span_in, span_out),
                control=frozenset(c.value for c in layer.control),
                is_cavity=cavity,
                cavity_host=host_name,
            )
        )
        fill = getattr(layer, "cavity", None)
        if fill is not None:
            fill_t = fill.thickness.meters if fill.thickness is not None else \
                layer.thickness.meters
            layers.append(
                ResolvedLayer(
                    name=f"{layer.name}-cavity",
                    material_ref=fill.material_ref,
                    function=LayerFunction.INSULATION.value,
                    thickness_m=fill_t,
                    polygon=_ring(span_in, span_in + fill_t),
                    control=frozenset(c.value for c in fill.control),
                    is_cavity=True,
                    cavity_host=layer.name,
                )
            )

    if is_foundation:
        # Foundation elevations are absolute project elevations so a walkout wall
        # can differ from the storey's ordinary wall height without a shadow model.
        z0 = wall.bottom_elevation.meters if wall.bottom_elevation is not None else z0
        z1 = wall.top_elevation.meters if wall.top_elevation is not None else z1
    elif getattr(wall, "top", None) is not None and hasattr(wall.top, "meters"):
        z1 = z0 + wall.top.meters

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
    sign = storey_outward_sign(plan, storey_tag)
    out: list[ResolvedWall] = []
    for wall in _walls(plan, storey_tag):
        rw = resolve_wall_geometry(
            plan, wall, storey_tag, z0, z1, half,
            is_foundation=wall.element_kind == "FoundationWall",
            outward_sign=sign,
        )
        if rw is not None:
            out.append(rw)
    return out


def wall_axis_length(rw: ResolvedWall) -> float:
    return length(sub(rw.axis[1], rw.axis[0]))
