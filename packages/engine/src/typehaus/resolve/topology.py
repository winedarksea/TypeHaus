"""Wall topology + junction solver → per-layer polygons and explicit junction records.

The authored wall graph is classified before any bands are built.  Each endpoint then uses
the same topology decision for layer geometry and framing: collinear seams cap at the node,
L corners share an angular-bisector miter, and T/X branches butt against a continuous host.
Unsupported mixed/high-valence conditions are made non-overlapping and reported instead of
silently exporting intersecting solids.
"""

from __future__ import annotations

from dataclasses import replace

from shapely import get_coordinates, is_valid
from shapely.geometry import GeometryCollection, MultiPolygon, Polygon
from shapely.ops import unary_union

from typehaus.findings import Finding, Result, Severity
from typehaus.model.enums import LayerFunction
from typehaus.model.plan import PlanModel
from typehaus.resolve.geometry import length, polygon_area, rect_between, sub, unit
from typehaus.resolve.layer_bands import band_datums, band_spec, resolve_band_spec
from typehaus.resolve.model import (
    JunctionIncident,
    ResolvedJunction,
    ResolvedLayer,
    ResolvedWall,
)
from typehaus.resolve.orientation import resolve_storey_windings, wall_outward_sign
from typehaus.resolve.rooms import wall_lining_overrides

_EPS = 1e-4  # meters — cavity-insulation coincidence tolerance
_DIRECTION_EPS = 1e-9
_COLLINEAR_CROSS_TOLERANCE = 1e-5
_L_CORNER_EXTENSION_MULTIPLIER = 4.0
_MIN_POLYGON_AREA_M2 = 1e-10


_PERPENDICULAR = {"horizontal": "vertical", "vertical": "horizontal"}


def _board_run(layers: list, index: int) -> str | None:
    """Which way a board finish's boards run, from the furring immediately behind it.

    A board is fastened to what is behind it, so it lands *perpendicular* to its furring —
    that is the whole reason a liner straps horizontally with 1x4 in the first place, so a
    vertical T&G board's concealed flange has something to bite between the studs
    (``houses/catlin/plan/assemblies.py`` says so at the plant-room liner). So the direction
    is derived here rather than authored anywhere: the fact was already in the assembly.

    "Immediately behind" is literal — the next layer outward, not the next furring layer
    anywhere outward. A finish separated from the strapping by an insulation band is not
    fastened to that strapping, and guessing that it is would put boards the wrong way round
    on the first assembly that interleaves them.

    ``None`` for anything that is not a FINISH layer, and for a finish with no furring behind
    it: a direction nobody can derive must not be invented, because the viewer's fallback for
    ``None`` (vertical) is at least an honest default rather than a wrong answer dressed up
    as a derived one.
    """
    layer = layers[index]
    if layer.function is not LayerFunction.FINISH:
        return None
    behind = layers[index + 1] if index + 1 < len(layers) else None
    if behind is None or behind.function is not LayerFunction.FURRING:
        return None
    framing = getattr(behind, "framing", None)
    direction = getattr(framing, "direction", None) if framing is not None else None
    return _PERPENDICULAR.get(direction or "")


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
        if (0 <= j < len(layers) and layers[j].function is LayerFunction.STRUCTURE
                and abs(layers[j].thickness.meters - layer.thickness.meters) < _EPS):
            return j
    return None


def _slot_host(layers: list, index: int) -> int | None:
    """Index of the first layer of this layer's split row, or None if it is that layer.

    Layers naming the same ``Layer.slot`` are the regions of one row of the stack (a brick
    plinth under a different brick field, a parge below grade under a panel above it). They
    occupy ONE depth position between them, so every member after the first adds no depth
    and borrows the first's strip — mechanically the same trick ``_cavity_host`` plays, for
    a different reason. Returns None for an unslotted layer and for the slot's own first
    member, both of which pay their thickness normally.
    """
    slot = getattr(layers[index], "slot", None)
    if slot is None:
        return None
    for j in range(index):
        if getattr(layers[j], "slot", None) == slot:
            return j
    return None


def _added_thicknesses(layers: list) -> list[tuple[object, float, bool]]:
    """Per layer: (layer, added_thickness_m, is_cavity).

    Cavity insulation — whether the modern ``Layer.cavity`` (which is not a list entry at
    all) or a legacy sibling batt layer — occupies the framing bays and adds no wall depth.
    Neither does a non-first member of a ``Layer.slot``: it is another region of a row the
    first member already paid for. It is not flagged as a cavity, because it is not one —
    ``ResolvedLayer.cavity_of`` means "fills that layer's framing bays" and a split row
    fills nothing.
    """
    out: list[tuple[object, float, bool]] = []
    for i, layer in enumerate(layers):
        cavity = _cavity_host(layers, i) is not None
        shares = cavity or _slot_host(layers, i) is not None
        out.append((layer, 0.0 if shares else layer.thickness.meters, cavity))
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


def site_grade_elevation_m_from_plan(plan: PlanModel) -> float:
    """Finished grade in the project frame, or the main-floor datum when unstated.

    The same fallback ``resolve.site_earth.site_grade_elevation_m`` applies, read off the
    plan rather than the resolved model because wall geometry is resolved before there is a
    ``ResolvedModel`` to ask. Only ``LayerDatum.GRADE`` needs it.
    """
    grade = plan.project.site.grade
    return grade.meters if grade is not None else 0.0


def _storey_nodes(plan: PlanModel, storey_tag: str) -> dict[str, object]:
    return {e.tag: e for e in plan.storey_elements(storey_tag) if e.element_kind == "Node"}


def resolve_wall_geometry(plan: PlanModel, wall, storey_tag: str, z0: float,
                          z1: float, endpoint_extensions: dict[tuple[str, str], float],
                          is_foundation: bool,
                          outward_sign: float = 1.0,
                          lining_override: tuple | None = None,
                          nodes: dict[str, object] | None = None,
                          line: object | None = None) -> ResolvedWall | None:
    """Build a ResolvedWall with per-layer polygons for one authored wall.

    ``lining_override`` is a Room-authored replacement for the assembly's interior lining
    (``Room.wall_lining`` / ``wall_lining_exceptions``, mapped per wall by
    :func:`typehaus.resolve.rooms.wall_lining_overrides`). ``None`` means "no override";
    an empty tuple is an authored bare face.

    ``nodes`` is the storey's tag -> Node map. Building it here re-scanned every element of
    the storey once per wall — 67k ``element_kind`` reads per resolve on ``houses/catlin``
    — so :func:`resolve_storey_walls` builds it once and hands it down.
    """
    if nodes is None:
        nodes = _storey_nodes(plan, storey_tag)
    n0, n1 = nodes.get(wall.start_node), nodes.get(wall.end_node)
    if n0 is None or n1 is None:
        return None
    p0, p1 = n0.position.xy_m, n1.position.xy_m
    asm = plan.library.resolve_assembly(wall.assembly)
    if asm is None:
        return None

    # Full inside→outside stack: interior lining, then the core layers.
    lining = lining_override if lining_override is not None else asm.default_lining
    stack = list(lining) + list(asm.layers)
    added = _added_thicknesses(stack)
    total = sum(a for (_l, a, _c) in added)
    axis_from_int = _axis_offset_from_interior(stack, added, wall.alignment, total)

    ext0 = endpoint_extensions.get((wall.tag, "start"), 0.0)
    ext1 = endpoint_extensions.get((wall.tag, "end"), 0.0)

    # Interior→exterior spans, walked over the depth-bearing layers only. A cavity layer
    # borrows its host structure layer's span, so it must be placed after the walk rather
    # than during it (a batt authored *before* the studs would otherwise land nowhere).
    spans: list[tuple[float, float]] = []
    pos = 0.0
    for (_layer, add_t, cavity) in added:
        spans.append((pos, pos + add_t))
        if not cavity:
            pos += add_t

    if is_foundation:
        # Foundation elevations are absolute project elevations so a walkout wall
        # can differ from the storey's ordinary wall height without a shadow model.
        z0 = wall.bottom_elevation.meters if wall.bottom_elevation is not None else z0
        z1 = wall.top_elevation.meters if wall.top_elevation is not None else z1
    else:
        # ``Wall.base_elevation`` lifts a framed wall off the storey datum — a stud wall
        # standing on a concrete curb within its own storey. ``top`` stays relative to
        # whatever base the wall ends up with, which is what makes it a height and not an
        # elevation, so the order here matters.
        base = getattr(wall, "base_elevation", None)
        if base is not None:
            z0 = base.meters
        if getattr(wall, "top", None) is not None and hasattr(wall.top, "meters"):
            z1 = z0 + wall.top.meters

    def _ring(span_in: float, span_out: float):
        return rect_between(p0, p1, (span_in - axis_from_int) * outward_sign,
                            (span_out - axis_from_int) * outward_sign, ext0, ext1)

    grade_m = site_grade_elevation_m_from_plan(plan)
    datums = band_datums(z0, z1, grade_m, line)
    # Per-wall material substitution (Wall.layer_materials). Appearance only: it swaps the
    # material a named layer reports and touches nothing else, so every span, band and
    # framing decision above is computed from the assembly and is unaffected. This is what
    # lets one wall carry a second coil colour or a second brick body without duplicating
    # the whole Assembly to restate one `material_ref`. An override naming a layer the
    # assembly does not have is reported by `checks.integrity.wall_layer_material`.
    overrides = {lm.layer: lm.material for lm in getattr(wall, "layer_materials", ())}
    layers: list[ResolvedLayer] = []
    for index, (layer, _add_t, cavity) in enumerate(added):
        host_index = _cavity_host(stack, index) if cavity else None
        slot_index = None if cavity else _slot_host(stack, index)
        if host_index is not None:
            # Share the host structure layer's strip, inset from its interior face.
            host_in, _host_out = spans[host_index]
            span_in, span_out = host_in, host_in + layer.thickness.meters
        elif slot_index is not None:
            # Another region of the same row: the identical strip, at a different elevation.
            # ``spans[index]`` is zero-width for it, because it added no depth.
            span_in, span_out = spans[slot_index]
        else:
            span_in, span_out = spans[index]
        host_name = stack[host_index].name if host_index is not None else None
        spec = band_spec(layer)
        band_z0, band_z1 = resolve_band_spec(spec, z0, z1, datums)
        # A band clamped to nothing is not on this wall. `_band` clips a layer's extent to
        # the wall's own z range, so a layer banded above grade lands on a wall that stops AT
        # grade with bottom == top — catlin's garage grade beams (W-GF-E-DR/S-DR) against the
        # R316.4 gypsum band the ICF stem carries above the slab. Emitting it anyway produced
        # a ResolvedLayer with no height, which the geometry builder then skipped as a
        # zero-volume prism: the two disagreed about the wall's part count, which is exactly
        # what `test_geometry_ir_parity` exists to catch. Dropping it here is the honest
        # reading — the band is out of this wall's range — and it drops the layer's cavity
        # fill with it, since a cavity has no business outliving its host.
        if band_z0 is not None and band_z1 is not None and band_z1 - band_z0 <= 1e-9:
            continue
        layers.append(
            ResolvedLayer(
                name=layer.name,
                material_ref=overrides.get(layer.name, layer.material_ref),
                function=layer.function.value,
                thickness_m=layer.thickness.meters,
                polygon=_ring(span_in, span_out),
                control=frozenset(c.value for c in layer.control),
                is_cavity=cavity,
                cavity_host=host_name,
                z0_m=band_z0,
                z1_m=band_z1,
                slot=getattr(layer, "slot", None),
                band_spec=spec,
                board_run=_board_run(stack, index),
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
                    z0_m=band_z0,
                    z1_m=band_z1,
                    band_spec=spec,
                )
            )

    return ResolvedWall(
        uid=wall.uid, tag=wall.tag, storey=storey_tag, assembly=wall.assembly,
        axis=(p0, p1), layers=tuple(layers), z0_m=z0, z1_m=z1,
        is_foundation=is_foundation,
    )


def _wall_total_thickness(plan: PlanModel, wall) -> float:
    assembly = plan.library.resolve_assembly(wall.assembly)
    if assembly is None:
        return 0.0
    stack = list(assembly.default_lining) + list(assembly.layers)
    return sum(added for (_layer, added, _cavity) in _added_thicknesses(stack))


def _cross(a: tuple[float, float], b: tuple[float, float]) -> float:
    return a[0] * b[1] - a[1] * b[0]


def _dot(a: tuple[float, float], b: tuple[float, float]) -> float:
    return a[0] * b[0] + a[1] * b[1]


def _opposite(a: tuple[float, float], b: tuple[float, float]) -> bool:
    return abs(_cross(a, b)) <= _COLLINEAR_CROSS_TOLERANCE and _dot(a, b) < 0.0


def _through_pair(incidents: list[JunctionIncident]) -> tuple[int, int] | None:
    pairs = [
        (i, j) for i in range(len(incidents)) for j in range(i + 1, len(incidents))
        if _opposite(incidents[i].direction, incidents[j].direction)
    ]
    if not pairs:
        return None
    return min(pairs, key=lambda pair: (
        incidents[pair[0]].wall_tag, incidents[pair[1]].wall_tag
    ))


def _is_exterior_assembly(plan: PlanModel, assembly_tag: str) -> bool:
    assembly = plan.library.resolve_assembly(assembly_tag)
    return bool(assembly and any(
        layer.function is LayerFunction.CLADDING for layer in assembly.layers
    ))


def _is_basic_mixed_tee(plan: PlanModel, through: list[JunctionIncident],
                        branches: list[JunctionIncident]) -> bool:
    return (
        bool(through)
        and all(_is_exterior_assembly(plan, item.assembly) for item in through)
        and all(not _is_exterior_assembly(plan, item.assembly) for item in branches)
    )


# Named face role the junction solver binds to. Two walls that publish the same bearing
# material are structurally continuous, regardless of finish/insulation layers around it.
_BEARING_ROLE = "bearing"


def _bearing_layer(plan: PlanModel, assembly_tag: str):
    """The load-bearing layer via the assembly's published ``bearing`` interface role.

    Falls back to the first STRUCTURE layer when an assembly publishes no role, so a plan
    that has not yet authored interfaces still resolves — the *match* is always by role,
    never by layer index or a hard-coded layer name.
    """
    assembly = plan.library.resolve_assembly(assembly_tag)
    if assembly is None:
        return None
    stack = list(assembly.default_lining) + list(assembly.layers)
    role = assembly.interface(_BEARING_ROLE)
    if role is not None:
        by_name = next((layer for layer in stack if layer.name == role.layer_name), None)
        if by_name is not None:
            return by_name
    return next((layer for layer in assembly.layers
                 if layer.function is LayerFunction.STRUCTURE), None)


def _bearing_material(plan: PlanModel, assembly_tag: str) -> str | None:
    layer = _bearing_layer(plan, assembly_tag)
    return layer.material_ref if layer is not None else None


def _through_continuous(plan: PlanModel, through: list[JunctionIncident]) -> bool:
    """The through pair carries one continuous bearing element (same bearing material)."""
    materials = {_bearing_material(plan, item.assembly) for item in through}
    return bool(through) and None not in materials and len(materials) == 1


def _can_butt(plan: PlanModel, assembly_tag: str) -> bool:
    """A branch can terminate against a continuous host iff it has a bearing element."""
    return _bearing_material(plan, assembly_tag) is not None


def _shared_bearing(plan: PlanModel, incidents: list[JunctionIncident]) -> bool:
    """Every incident carries the same bearing material — a mixed corner that still miters
    cleanly because the load-bearing layers meet on one continuous plane (2x4 partition ⟂
    2x6 bearing wall, both SPF; concrete ⟂ concrete)."""
    materials = {_bearing_material(plan, item.assembly) for item in incidents}
    return None not in materials and len(materials) == 1


def _wall_z_range(storey, wall) -> tuple[float, float]:
    """Absolute elevation extent of a wall, used to split stacked bearing tiers apart."""
    base = storey.elevation.meters if storey is not None else 0.0
    if wall.element_kind == "FoundationWall":
        z0 = wall.bottom_elevation.meters if wall.bottom_elevation is not None else base
        z1 = wall.top_elevation.meters if wall.top_elevation is not None else base
        return (z0, z1) if z0 <= z1 else (z1, z0)
    # ``base_elevation`` lifts a framed wall off the storey datum (a stud wall on a
    # concrete curb), and this range is what splits a node's incidents into bearing TIERS —
    # so reading it here is what keeps the curb and the wall standing on it from being
    # graded as one junction.
    wall_base = getattr(wall, "base_elevation", None)
    if wall_base is not None:
        base = wall_base.meters
    top = getattr(wall, "top", None)
    height = top.meters if top is not None and hasattr(top, "meters") else (
        storey.default_ceiling_height.meters if storey is not None else 0.0)
    return base, base + height


def _tiers(incidents: list[JunctionIncident]) -> list[list[JunctionIncident]]:
    """Partition a plan node's incidents into vertically-overlapping bearing tiers.

    Two walls that share a plan point but not an elevation band (a masonry guard stacked on
    a concrete porch wall) are independent junctions, not one high-valence node. Incidents
    join a tier when their elevation extents overlap by at least half the shorter wall — a
    retaining wall poking a few inches above grade does not fuse with the guard above it.
    """
    parent = list(range(len(incidents)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(incidents)):
        for j in range(i + 1, len(incidents)):
            a, b = incidents[i], incidents[j]
            overlap = min(a.z1_m, b.z1_m) - max(a.z0_m, b.z0_m)
            span = min(a.z1_m - a.z0_m, b.z1_m - b.z0_m)
            joined = overlap > -_EPS if span <= _EPS else overlap >= 0.5 * span
            if joined:
                parent[find(i)] = find(j)

    groups: dict[int, list[JunctionIncident]] = {}
    for index, incident in enumerate(incidents):
        groups.setdefault(find(index), []).append(incident)
    return sorted(groups.values(), key=lambda tier: (
        min(item.z0_m for item in tier), tuple(item.wall_tag for item in tier)))


def _classify_tier(plan: PlanModel, node_tag: str, storey_tag: str,
                   point: tuple[float, float],
                   incidents: list[JunctionIncident]) -> ResolvedJunction:
    """Classify one bearing tier of a plan node into a resolved junction record."""
    count = len(incidents)
    pair = _through_pair(incidents)
    if count == 1:
        kind = "open_end"
    elif count == 2:
        kind = "collinear" if pair is not None else "l"
    elif count == 3:
        kind = "t" if pair is not None else "complex"
    elif count == 4:
        remaining = [item for index, item in enumerate(incidents)
                     if pair is None or index not in pair]
        kind = "x" if pair is not None and len(remaining) == 2 \
            and _opposite(remaining[0].direction, remaining[1].direction) else "complex"
    else:
        kind = "complex"

    through = [incidents[index] for index in pair] if pair is not None else []
    branches = [item for item in incidents if item not in through]
    same_assembly = len({item.assembly for item in incidents}) == 1
    # A mixed tee/multi-branch node resolves when the through pair is one continuous bearing
    # element (concrete-to-concrete return, partition-to-bearing tee) and every branch has a
    # bearing element to butt against it. High-valence tiers with a continuous through pair
    # are owned the same way — the extra walls are just more branches.
    continuous_tee = (
        bool(through)
        and _through_continuous(plan, through)
        and all(_can_butt(plan, item.assembly) for item in branches)
    )
    supported = (
        kind == "open_end"
        or (kind in {"collinear", "l", "t", "x"} and same_assembly)
        or (kind == "t" and _is_basic_mixed_tee(plan, through, branches))
        or (kind in {"t", "x", "complex"} and continuous_tee)
        or (kind in {"collinear", "l"} and _shared_bearing(plan, incidents))
    )
    diagnostic = None if supported else (
        "mixed-assembly junction requires interface rules"
        if kind != "complex" else
        f"{count}-way junction requires a project-specific construction rule"
    )
    framing_owner = None
    if kind == "l":
        starting = [item.wall_tag for item in incidents if item.endpoint == "start"]
        framing_owner = min(starting or [item.wall_tag for item in incidents])
    elif through:
        framing_owner = min(item.wall_tag for item in through)
    return ResolvedJunction(
        node_tag=node_tag,
        storey=storey_tag,
        point=point,
        kind=kind,
        incidents=tuple(incidents),
        through_walls=tuple(sorted(item.wall_tag for item in through)),
        branch_walls=tuple(sorted(item.wall_tag for item in branches)),
        framing_owner=framing_owner,
        supported=supported,
        diagnostic=diagnostic,
    )


def classify_storey_junctions(plan: PlanModel, storey_tag: str) -> list[ResolvedJunction]:
    """Classify every wall-graph node without depending on wall authoring direction."""
    storey = plan.storey(storey_tag)
    nodes = {
        element.tag: element.position.xy_m
        for element in plan.storey_elements(storey_tag)
        if element.element_kind == "Node"
    }
    by_node: dict[str, list[JunctionIncident]] = {}
    for wall in _walls(plan, storey_tag):
        start = nodes.get(wall.start_node)
        end = nodes.get(wall.end_node)
        if start is None or end is None:
            continue
        direction = unit(sub(end, start))
        if length(direction) <= _DIRECTION_EPS:
            continue
        z0, z1 = _wall_z_range(storey, wall)
        by_node.setdefault(wall.start_node, []).append(JunctionIncident(
            wall.tag, "start", direction, wall.assembly, z0, z1,
        ))
        by_node.setdefault(wall.end_node, []).append(JunctionIncident(
            wall.tag, "end", (-direction[0], -direction[1]), wall.assembly, z0, z1,
        ))

    junctions: list[ResolvedJunction] = []
    for node_tag, raw_incidents in sorted(by_node.items()):
        incidents = sorted(raw_incidents, key=lambda item: (item.wall_tag, item.endpoint))
        for tier in _tiers(incidents):
            junctions.append(
                _classify_tier(plan, node_tag, storey_tag, nodes[node_tag], tier))
    return junctions


def _endpoint_extensions(plan: PlanModel, junctions: list[ResolvedJunction]) \
        -> dict[tuple[str, str], float]:
    walls = {wall.tag: wall for wall in _walls(plan, junctions[0].storey)} if junctions else {}
    extensions: dict[tuple[str, str], float] = {}
    for junction in junctions:
        if junction.kind != "l":
            continue
        maximum_thickness = max(
            (_wall_total_thickness(plan, walls[item.wall_tag])
             for item in junction.incidents if item.wall_tag in walls),
            default=0.0,
        )
        extension = maximum_thickness * _L_CORNER_EXTENSION_MULTIPLIER
        for item in junction.incidents:
            extensions[(item.wall_tag, item.endpoint)] = extension
    return extensions


def _clip_to_incident_sector(ring: list[tuple[float, float]],
                             node: tuple[float, float],
                             own_direction: tuple[float, float],
                             other_direction: tuple[float, float]) \
        -> list[tuple[float, float]]:
    """Clip a convex wall band to its side of the two-ray angular bisector."""
    normal = (
        own_direction[0] - other_direction[0],
        own_direction[1] - other_direction[1],
    )

    def signed(point: tuple[float, float]) -> float:
        return (point[0] - node[0]) * normal[0] + (point[1] - node[1]) * normal[1]

    result: list[tuple[float, float]] = []
    for current, following in zip(ring, ring[1:] + ring[:1]):  # noqa: B905
        current_distance = signed(current)
        following_distance = signed(following)
        current_inside = current_distance >= -_EPS
        following_inside = following_distance >= -_EPS
        if current_inside:
            result.append(current)
        if current_inside != following_inside:
            denominator = current_distance - following_distance
            if abs(denominator) > _DIRECTION_EPS:
                fraction = current_distance / denominator
                result.append((
                    current[0] + (following[0] - current[0]) * fraction,
                    current[1] + (following[1] - current[1]) * fraction,
                ))
    return result


def _polygon_component(geometry, original: list[tuple[float, float]]) -> Polygon | None:
    if geometry.is_empty:
        return None
    candidates: list[Polygon]
    if isinstance(geometry, Polygon):
        candidates = [geometry]
    elif isinstance(geometry, (MultiPolygon, GeometryCollection)):
        candidates = [item for item in geometry.geoms if isinstance(item, Polygon)]
    else:
        candidates = []
    if not candidates:
        return None
    if len(candidates) == 1:
        # ``max(containing or candidates, ...)`` can only ever return the sole candidate, so
        # the containment test below is pure cost here — and on ``houses/catlin`` *every* one
        # of the 792 calls per resolve takes this branch. Skipping it drops a ``Polygon``
        # build, a ``representative_point`` and a ``buffer`` per call (~25 ms/resolve).
        return candidates[0]
    original_polygon = Polygon(original)
    representative = original_polygon.representative_point()
    containing = [item for item in candidates if item.buffer(_EPS).contains(representative)]
    return max(containing or candidates, key=lambda item: item.area)


def _normalized_ring(geometry, original: list[tuple[float, float]]) \
        -> list[tuple[float, float]]:
    component = _polygon_component(geometry, original)
    if component is None or component.area <= _MIN_POLYGON_AREA_M2:
        return []
    if not component.is_valid:
        component = _polygon_component(component.buffer(0), original)
        if component is None:
            return []
    # ``get_coordinates(...).tolist()`` costs ~2.6 us/ring against ~15 us for iterating the
    # CoordinateSequence, which is worth having at ~800 rings per resolve.
    points = [(x, y) for x, y in get_coordinates(component.exterior)[:-1].tolist()]
    if len(points) < 3:
        return []
    # Signed shoelace instead of ``Polygon(points).exterior.is_ccw``: ``component`` is a valid
    # polygon, so its exterior ring is simple and the two agree by definition. Saves a GEOS
    # polygon construction per ring; verified identical over every catlin ring before landing.
    if polygon_area(points) > 0.0:
        points.reverse()
    start = min(range(len(points)), key=lambda index: (
        round(points[index][0], 12), round(points[index][1], 12)
    ))
    return points[start:] + points[:start]


def _with_layer_polygons(wall: ResolvedWall,
                         polygons: dict[int, list[tuple[float, float]]]) -> ResolvedWall:
    """One wall rebuild for a whole clip pass.

    Each layer's new polygon depends only on that layer's *original* ring, so replacing them
    one at a time copied the layer tuple once per layer — quadratic in layer count for no
    reason.
    """
    if not polygons:
        return wall
    layers = list(wall.layers)
    for index, polygon in polygons.items():
        layers[index] = replace(layers[index], polygon=polygon)
    return replace(wall, layers=tuple(layers))


def _clip_l_corner(walls: dict[str, ResolvedWall], junction: ResolvedJunction) -> None:
    first, second = junction.incidents
    for own, other in ((first, second), (second, first)):
        if own.wall_tag not in walls:
            continue
        wall = walls[own.wall_tag]
        clipped_rings: dict[int, list[tuple[float, float]]] = {}
        for index, layer in enumerate(wall.layers):
            clipped = _clip_to_incident_sector(
                layer.polygon, junction.point, own.direction, other.direction,
            )
            clipped_rings[index] = _normalized_ring(Polygon(clipped), layer.polygon)
        walls[own.wall_tag] = _with_layer_polygons(wall, clipped_rings)


def _through_envelope(walls: dict[str, ResolvedWall], wall_tags: tuple[str, ...]):
    polygons = [
        Polygon(layer.polygon)
        for wall_tag in wall_tags
        for layer in walls[wall_tag].depth_layers()
        if len(layer.polygon) >= 3
    ]
    return unary_union(polygons) if polygons else GeometryCollection()


def _butt_branches(walls: dict[str, ResolvedWall], junction: ResolvedJunction) -> None:
    envelope = _through_envelope(walls, junction.through_walls)
    if envelope.is_empty:
        return
    for wall_tag in junction.branch_walls:
        if wall_tag not in walls:
            continue
        wall = walls[wall_tag]
        butted: dict[int, list[tuple[float, float]]] = {}
        for index, layer in enumerate(wall.layers):
            original = layer.polygon
            difference = Polygon(original).difference(envelope)
            butted[index] = _normalized_ring(difference, original)
        walls[wall_tag] = _with_layer_polygons(wall, butted)


def _remove_fallback_overlaps(walls: dict[str, ResolvedWall],
                              junction: ResolvedJunction) -> None:
    occupied = GeometryCollection()
    for incident in junction.incidents:
        if incident.wall_tag not in walls:
            continue
        wall = walls[incident.wall_tag]
        trimmed: dict[int, list[tuple[float, float]]] = {}
        for index, layer in enumerate(wall.layers):
            if layer.is_cavity or len(layer.polygon) < 3:
                continue
            original = layer.polygon
            polygon = Polygon(original)
            resolved = polygon.difference(occupied)
            normalized = _normalized_ring(resolved, original)
            # A fallback must never erase a real authored wall. Complete containment
            # means this condition needs a project-specific rule, not a guessed deletion.
            if not normalized:
                normalized = original
            trimmed[index] = normalized
            occupied = unary_union((occupied, polygon))
        walls[incident.wall_tag] = _with_layer_polygons(wall, trimmed)


def _synchronize_cavity_polygons(walls: dict[str, ResolvedWall]) -> None:
    for wall_tag, wall in list(walls.items()):
        layers = list(wall.layers)
        by_name = {layer.name: layer for layer in layers if not layer.is_cavity}
        changed = False
        for index, layer in enumerate(layers):
            host = by_name.get(layer.cavity_host or "") if layer.is_cavity else None
            if host is not None and layer.polygon != host.polygon:
                layers[index] = replace(layer, polygon=list(host.polygon))
                changed = True
        if changed:
            walls[wall_tag] = replace(wall, layers=tuple(layers))


def _invalid_polygon_findings(walls: dict[str, ResolvedWall]) -> list[Finding]:
    """Report every layer whose solved ring is degenerate or self-intersecting.

    One batched ``shapely.is_valid`` rather than ``Polygon(...).is_valid`` per ring: this
    walks ~840 rings per resolve on ``houses/catlin``, and paying shapely's per-call ufunc
    dispatch that many times measured ~1.5x the whole batched pass. Order of the findings
    still follows the wall/layer walk exactly.
    """
    labels: list[tuple[str, str, int | None]] = []
    candidates: list[Polygon] = []
    for wall in walls.values():
        for layer in wall.layers:
            if len(layer.polygon) < 3:
                labels.append((wall.tag, layer.name, None))
                continue
            labels.append((wall.tag, layer.name, len(candidates)))
            candidates.append(Polygon(layer.polygon))
    valid = is_valid(candidates) if candidates else ()
    return [
        Finding(
            severity=Severity.ERROR,
            check_id="integrity.junction_polygon",
            message=f"{wall_tag}/{layer_name} resolved to an invalid junction polygon",
            element_tags=(wall_tag,),
            result=Result.FAIL,
        )
        for wall_tag, layer_name, index in labels
        if index is None or not valid[index]
    ]


def solve_junction_polygons(resolved_walls: list[ResolvedWall],
                            junctions: list[ResolvedJunction]) -> tuple[list[ResolvedWall],
                                                                       list[Finding]]:
    walls = {wall.tag: wall for wall in resolved_walls}
    findings: list[Finding] = []
    for junction in junctions:
        if junction.kind == "l":
            _clip_l_corner(walls, junction)
        if junction.through_walls and (junction.kind in {"t", "x"} or junction.supported):
            _butt_branches(walls, junction)
        if not junction.supported:
            _remove_fallback_overlaps(walls, junction)
            findings.append(Finding(
                severity=Severity.WARN,
                check_id="integrity.junction_fallback",
                message=f"node {junction.node_tag}: {junction.diagnostic}",
                element_tags=tuple(item.wall_tag for item in junction.incidents),
                fix_hint="author assembly interface/construction rules for this junction",
                result=Result.UNKNOWN,
            ))
    _synchronize_cavity_polygons(walls)
    findings.extend(_invalid_polygon_findings(walls))
    return [walls[wall.tag] for wall in resolved_walls], findings


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


def resolve_storey_walls(plan: PlanModel, storey_tag: str, z0: float, z1: float,
                         layout_lines: dict | None = None,
                         ) -> tuple[list[ResolvedWall], list[ResolvedJunction],
                                    list[Finding]]:
    junctions = classify_storey_junctions(plan, storey_tag)
    endpoint_extensions = _endpoint_extensions(plan, junctions)
    # One graph trace per storey, split into independent structures: a storey key is a floor
    # level, not a building, so the basement and the sunken garden get their own windings.
    windings = resolve_storey_windings(plan, storey_tag)
    # Room-authored lining swaps (Room.wall_lining / wall_lining_exceptions), mapped to the
    # walls they reach once per storey, before any wall resolves.
    lining_overrides, findings = wall_lining_overrides(plan, storey_tag)
    nodes = _storey_nodes(plan, storey_tag)
    out: list[ResolvedWall] = []
    for wall in _walls(plan, storey_tag):
        rw = resolve_wall_geometry(
            plan, wall, storey_tag, z0, z1, endpoint_extensions,
            is_foundation=wall.element_kind == "FoundationWall",
            outward_sign=wall_outward_sign(plan, wall, storey_tag,
                                           windings.sign_for_wall(wall)),
            lining_override=lining_overrides.get(wall.tag),
            nodes=nodes,
            line=(layout_lines or {}).get(wall.tag),
        )
        if rw is not None:
            out.append(rw)
    solved, junction_findings = solve_junction_polygons(out, junctions)
    findings.extend(junction_findings)
    return solved, junctions, findings
