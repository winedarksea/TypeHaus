"""Pre-framing ConstructionRule application pass (#45, → 10 §Element model).

``ConstructionRule`` objects are typed, pre-resolve declarations of the physical *returns*
the junction solver leaves for framing/take-off — the membrane / foam / liner / masonry lap
that actually closes a resolved junction (a PT sill where framed walls — or a joisted deck —
land on concrete, the sauna liner wrapping onto the centre concrete wall, the exterior
foundation foam turning a corner for thermal continuity, the masonry guard's corner
return). They are *authored* on
``PlanModel.construction_rules`` and, until this pass existed, emitted nothing.

This pass runs once, after the envelope is resolved and **before final framing** (so the
returns are construction geometry, not documentation), and for each rule:

* records a :class:`ResolvedConstructionReturn` carrying the return's geometry (outline, z
  range, thickness, length), the take-off quantity and the overlay metadata (element tags,
  lap / sealant / flashing / thermal-continuity) a detail recipe binds to.

The record is documentation + take-off, **not** render geometry: a correctly-placed return
duplicates the mitred ``ResolvedLayer.polygon`` the host wall already draws, so no
``ResolvedSolid`` is emitted (that only ever produced z-fighting prisms in 3D and phantom
concrete rectangles in the sections). ``model.construction_returns`` is serialized to
``model.json`` and emitted as an ``IfcCovering`` directly.

It is declarative: a ``ConstructionRule.applies_to`` predicate selects *where* the return
lands via the finders registered in ``_FINDERS``. It never mutates a resolved wall polygon
or a framing member — a Transition documents the return post-resolve (``documents_rules``),
keyed to the ordinary boundary condition the return names in ``condition_key``.
"""

from __future__ import annotations

from collections.abc import Iterator

from typehaus.findings import Finding
from typehaus.model.assembly import Assembly, ConstructionRule
from typehaus.model.enums import ControlLayer, LayerFunction
from typehaus.model.floors import FloorSystem
from typehaus.model.plan import PlanModel
from typehaus.model.structure import FoundationWall
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.geometry import add, length, normal, scale, sub, unit
from typehaus.resolve.model import (
    ResolvedConstructionReturn,
    ResolvedModel,
    ResolvedWall,
)

# A framed wall must overlap a concrete wall below by at least this much before a sill plate
# is billed — a token clip of a passing wall is not a bearing line. Matches the stacking
# pass's minimum vertical stack overlap (2 ft) so the two agree on what "stacks" means.
_MIN_STACK_OVERLAP_M = 0.6096  # 2 ft
_EPS = 1e-6


# --- assembly characterisation ------------------------------------------------
def _stack(asm: Assembly) -> list:
    return list(asm.default_lining) + list(asm.layers)


def _is_concrete(asm: Assembly) -> bool:
    return any(layer.material_ref == "concrete" for layer in _stack(asm))


def _is_masonry(asm: Assembly) -> bool:
    """A true CMU/brick masonry wall — a unit-masonry layer that is not a concrete core.

    Excludes ICF (a concrete core that happens to carry a ``MasonrySpec`` for its unit
    take-off): that is a concrete foundation stem, billed by the foam return, not the
    masonry guard's corner return.
    """
    return any(layer.masonry is not None and layer.material_ref != "concrete"
               for layer in _stack(asm))


def _framed_wood_layer(asm: Assembly):
    """The wood STRUCTURE (stud) layer of a framed wall, or None."""
    return next(
        (
            layer
            for layer in _stack(asm)
            if layer.function is LayerFunction.STRUCTURE and layer.framing is not None
        ),
        None,
    )


def _exterior_thermal_layers(asm: Assembly) -> list:
    """Continuous exterior insulation: INSULATION/THERMAL layers outboard of the structure."""
    structure_index = next(
        (i for i, layer in enumerate(asm.layers)
         if layer.function is LayerFunction.STRUCTURE),
        -1,
    )
    return [
        layer
        for i, layer in enumerate(asm.layers)
        if i > structure_index
        and layer.function is LayerFunction.INSULATION
        and ControlLayer.THERMAL in layer.control
    ]


def _liner_layer(asm: Assembly):
    """The vapour-control liner (foil-faced polyiso) of a sauna hot-side assembly, or None."""
    return next(
        (
            layer
            for layer in _stack(asm)
            if layer.function is LayerFunction.INSULATION
            and ControlLayer.VAPOR in layer.control
        ),
        None,
    )


# --- geometry helpers ---------------------------------------------------------
def _axis_dir(rw: ResolvedWall) -> tuple[float, float]:
    return unit(sub(rw.axis[1], rw.axis[0]))


def _strip(anchor: tuple[float, float], direction: tuple[float, float],
           run_m: float, near: float, far: float) -> list[tuple[float, float]]:
    """A rectangle from ``anchor`` running ``run_m`` along ``direction``, spanning the
    perpendicular offsets ``near``..``far`` (positive = left of ``direction``)."""
    tip = add(anchor, scale(direction, run_m))
    n = normal(direction)
    return [
        add(anchor, scale(n, near)),
        add(tip, scale(n, near)),
        add(tip, scale(n, far)),
        add(anchor, scale(n, far)),
    ]


def _stack_overlap(lower: ResolvedWall, upper: ResolvedWall) -> \
        tuple[tuple[float, float], tuple[float, float]] | None:
    """The collinear plan overlap of two stacked walls as a world segment, or None.

    Tolerant of the exterior-insulation datum offset (a ``face("sheathing-ext")`` framed
    wall sits outboard of the concrete centreline): the perpendicular gate is the two walls'
    combined depth, i.e. "the framed wall sits within the concrete wall's footprint band".
    """
    a0, a1 = lower.axis
    da = _axis_dir(lower)
    db = _axis_dir(upper)
    if length(da) < _EPS or length(db) < _EPS:
        return None
    if abs(da[0] * db[1] - da[1] * db[0]) > 1e-3:  # not parallel
        return None
    n = normal(da)
    perp = abs(sub(upper.axis[0], a0)[0] * n[0] + sub(upper.axis[0], a0)[1] * n[1])
    if perp > (lower.thickness_m + upper.thickness_m):
        return None

    def proj(point: tuple[float, float]) -> float:
        v = sub(point, a0)
        return v[0] * da[0] + v[1] * da[1]

    lo_a, hi_a = 0.0, length(sub(a1, a0))
    lo_b, hi_b = sorted((proj(upper.axis[0]), proj(upper.axis[1])))
    lo, hi = max(lo_a, lo_b), min(hi_a, hi_b)
    if hi - lo < _MIN_STACK_OVERLAP_M:
        return None
    return add(a0, scale(da, lo)), add(a0, scale(da, hi))


def _walls_by_storey(model: ResolvedModel) -> dict[str, list[ResolvedWall]]:
    out: dict[str, list[ResolvedWall]] = {}
    for rw in model.walls:
        out.setdefault(rw.storey, []).append(rw)
    return out


def _condition_key(prefix: str, *assemblies: str) -> str:
    return f"{prefix}:{'|'.join(sorted(set(assemblies)))}"


# --- finders (one per applies_to predicate) -----------------------------------
# Each yields a fully-formed ResolvedConstructionReturn for the given rule. The finders own
# geometry/placement; ``apply_construction_rules`` owns the solid + book-keeping.
def _find_framed_on_concrete(model: ResolvedModel, rule: ConstructionRule) \
        -> Iterator[ResolvedConstructionReturn]:
    """PT sill where a framed wood wall lands on the concrete wall stacked below it."""
    lap = rule.dimension.meters if rule.dimension is not None else 0.0381  # 1.5"
    by_storey = _walls_by_storey(model)
    ordered = sorted(model.plan.storeys, key=lambda s: s.elevation.meters)
    for lower in model.walls:
        lower_asm = model.plan.library.resolve_assembly(lower.assembly)
        if lower_asm is None or not _is_concrete(lower_asm):
            continue
        # Framed walls in the first storey above that carries a collinear wall over it.
        lower_i = next((i for i, s in enumerate(ordered) if s.tag == lower.storey), None)
        if lower_i is None:
            continue
        for upper_s in ordered[lower_i + 1:]:
            hits = []
            for upper in by_storey.get(upper_s.tag, []):
                upper_asm = model.plan.library.resolve_assembly(upper.assembly)
                if upper_asm is None or _framed_wood_layer(upper_asm) is None:
                    continue
                if _is_concrete(upper_asm):  # a concrete tier stacked on concrete is not framed
                    continue
                segment = _stack_overlap(lower, upper)
                if segment is not None:
                    hits.append((upper, upper_asm, segment))
            if not hits:
                continue
            for upper, upper_asm, (p0, p1) in hits:
                bearing = _framed_wood_layer(upper_asm)
                width = bearing.thickness.meters
                run = length(sub(p1, p0))
                direction = unit(sub(p1, p0))
                z0 = upper.z0_m
                yield ResolvedConstructionReturn(
                    uid=f"CR-{lower.uid}-{upper.uid}-sill",
                    tag=rule.tag, storey=upper.storey, kind=rule.kind,
                    applies_to=rule.applies_to, takeoff_category=rule.takeoff_category,
                    material_ref="spf",
                    element_tags=(lower.tag, upper.tag),
                    outline=_strip(p0, direction, run, -width / 2.0, width / 2.0),
                    z0_m=z0, z1_m=z0 + lap, thickness_m=width, length_m=run,
                    lap_m=lap, thermal_continuity=False, sealant="sill-gasket",
                    flashing="capillary-break", returning_layer=bearing.name,
                    condition_key=_condition_key(
                        "wall_foundation", lower.assembly, upper.assembly),
                )
            break  # first storey above with a stack owns this concrete wall


# The plate a joisted deck lands on where it bears on concrete. Laid *flat* — its bearing
# width is the member's depth (3.5") and its build-up is the member's width (1.5") — which
# is why this cannot be authored as a ``Beam`` and has to be a construction return.
_SILL_PLATE_MEMBER = "2x4"


def _floor_run_on_wall(rw: ResolvedWall, system: FloorSystem) \
        -> tuple[tuple[float, float], tuple[float, float]] | None:
    """The stretch of ``rw``'s axis the floor system actually bears over, or None.

    The bearing run is the wall axis clipped to the deck outline's extent along that axis —
    a 20'-axis cross-wall under a 19'-wide deck bills 19' of plate, not 20'.
    """
    a0, a1 = rw.axis
    direction = unit(sub(a1, a0))
    if length(direction) < _EPS:
        return None
    span = length(sub(a1, a0))
    ring = [p.xy_m for p in system.outline]
    if not ring:
        return None

    def proj(point: tuple[float, float]) -> float:
        v = sub(point, a0)
        return v[0] * direction[0] + v[1] * direction[1]

    lo = max(0.0, min(proj(p) for p in ring))
    hi = min(span, max(proj(p) for p in ring))
    if hi - lo < _MIN_STACK_OVERLAP_M:
        return None
    return add(a0, scale(direction, lo)), add(a0, scale(direction, hi))


def _find_floor_on_concrete(model: ResolvedModel, rule: ConstructionRule) \
        -> Iterator[ResolvedConstructionReturn]:
    """PT sill plate where a joisted deck bears on a concrete wall.

    The framed-wall case above is a *wall* landing on concrete; this is the same physical
    return one element down — a ``FloorSystem`` whose ``joists.bearing_refs`` names a
    ``FoundationWall``. The plate lies flat on the wall's bearing ledge with its top at the
    joist soffit (one joist depth below the storey datum), sill seal under it and the same
    capillary break, so the joists butt a rim on it instead of sitting on bare concrete.
    """
    plate = cross_section(_SILL_PLATE_MEMBER)
    width = plate.depth_m          # laid flat: the 3.5" face bears
    lap = rule.dimension.meters if rule.dimension is not None else plate.width_m  # 1.5"
    for storey in model.plan.storeys:
        for system in model.plan.storey_elements(storey.tag):
            if not isinstance(system, FloorSystem):
                continue
            z1 = storey.elevation.meters - cross_section(system.joists.member).depth_m
            for ref in system.joists.bearing_refs:
                if not isinstance(model.plan.by_tag(ref), FoundationWall):
                    continue
                rw = model.wall(ref)
                if rw is None:
                    continue
                asm = model.plan.library.resolve_assembly(rw.assembly)
                if asm is None or not _is_concrete(asm):
                    continue
                run_segment = _floor_run_on_wall(rw, system)
                if run_segment is None:
                    continue
                p0, p1 = run_segment
                direction = unit(sub(p1, p0))
                run = length(sub(p1, p0))
                # Land the plate on the deck side of the wall — the bearing ledge is the
                # face the joists come from, not the middle of a 16" pier section.
                n = normal(direction)
                ring = [p.xy_m for p in system.outline]
                centroid = (sum(p[0] for p in ring) / len(ring),
                            sum(p[1] for p in ring) / len(ring))
                toward = sub(centroid, p0)
                side = 1.0 if (toward[0] * n[0] + toward[1] * n[1]) >= 0.0 else -1.0
                far = side * rw.thickness_m / 2.0
                near = side * (rw.thickness_m / 2.0 - width)
                yield ResolvedConstructionReturn(
                    uid=f"CR-{rw.uid}-{system.uid}-sill",
                    tag=rule.tag, storey=storey.tag, kind=rule.kind,
                    applies_to=rule.applies_to, takeoff_category=rule.takeoff_category,
                    material_ref="spf",
                    element_tags=(rw.tag, system.tag),
                    outline=_strip(p0, direction, run, min(near, far), max(near, far)),
                    z0_m=z1 - lap, z1_m=z1, thickness_m=width, length_m=run,
                    lap_m=lap, thermal_continuity=False, sealant="sill-gasket",
                    flashing="capillary-break", returning_layer=_SILL_PLATE_MEMBER,
                    condition_key=_condition_key("floor_foundation", rw.assembly),
                )


def _corner_incidents(junction) -> Iterator[tuple[object, object]]:
    """Ordered (own, other) incident pairs of a plan junction — every directed corner leg."""
    incidents = junction.incidents
    for i, own in enumerate(incidents):
        for j, other in enumerate(incidents):
            if i != j:
                yield own, other


def _find_exterior_return(model: ResolvedModel, rule: ConstructionRule, *,
                          predicate, material_of, layer_of, thermal: bool,
                          continuity_field: str, treatment: dict,
                          kinds: frozenset[str] | None = None) \
        -> Iterator[ResolvedConstructionReturn]:
    """Generic corner-return finder: a control/finish layer of one wall turns the corner
    onto the exterior face of the perpendicular wall it meets at a plan junction.

    ``kinds`` restricts which junction topologies qualify (``{"l"}`` for a clean corner
    return); ``None`` accepts any junction (a liner that tees into a through wall)."""
    lap = rule.dimension.meters if rule.dimension is not None else 0.1
    seen: set[str] = set()
    for junction in model.junctions:
        if kinds is not None and junction.kind not in kinds:
            continue
        for own, other in _corner_incidents(junction):
            own_wall = model.wall(own.wall_tag)
            other_wall = model.wall(other.wall_tag)
            if own_wall is None or other_wall is None:
                continue
            own_asm = model.plan.library.resolve_assembly(own.assembly)
            other_asm = model.plan.library.resolve_assembly(other.assembly)
            if own_asm is None or other_asm is None:
                continue
            match = predicate(own_asm, other_asm)
            if not match:
                continue
            layer = layer_of(own_asm)
            if layer is None:
                continue
            width = material_of(own_asm)
            # Return runs along the *other* wall's leg, on the exterior face, from the corner.
            direction = other.direction  # node -> other wall interior
            exterior = own_wall.thickness_m / 2.0
            key = f"{rule.tag}:{junction.node_tag}:{own.wall_tag}->{other.wall_tag}"
            if key in seen:
                continue
            seen.add(key)
            z0, z1 = min(own.z0_m, other.z0_m), max(own.z1_m, other.z1_m)
            yield ResolvedConstructionReturn(
                uid=f"CR-{junction.node_tag}-{own.wall_tag}-{other.wall_tag}-ret",
                tag=rule.tag, storey=junction.storey, kind=rule.kind,
                applies_to=rule.applies_to, takeoff_category=rule.takeoff_category,
                material_ref=layer.material_ref,
                element_tags=(own.wall_tag, other.wall_tag, junction.node_tag),
                outline=_strip(junction.point, direction, lap,
                               exterior, exterior + width),
                z0_m=z0, z1_m=z1, thickness_m=width, length_m=lap,
                lap_m=lap, thermal_continuity=thermal,
                air_vapor_continuity=continuity_field == "air_vapor",
                sealant=treatment.get("sealant"), flashing=treatment.get("flashing"),
                returning_layer=layer.name,
                condition_key=_condition_key(
                    "assembly_change", own.assembly, other.assembly),
            )


def _find_foundation_foam_return(model: ResolvedModel, rule: ConstructionRule) \
        -> Iterator[ResolvedConstructionReturn]:
    """Exterior foundation foam (XPS) turning an L corner for thermal continuity."""
    def predicate(own: Assembly, other: Assembly) -> bool:
        return (
            _is_concrete(own) and _is_concrete(other)
            and bool(_exterior_thermal_layers(own))
        )

    def material_of(asm: Assembly) -> float:
        return sum(layer.thickness.meters for layer in _exterior_thermal_layers(asm))

    def layer_of(asm: Assembly):
        layers = _exterior_thermal_layers(asm)
        return layers[0] if layers else None

    yield from _find_exterior_return(
        model, rule, predicate=predicate, material_of=material_of, layer_of=layer_of,
        thermal=True, continuity_field="thermal",
        treatment={"sealant": "foam-adhesive"}, kinds=frozenset({"l"}),
    )


def _find_porch_masonry_return(model: ResolvedModel, rule: ConstructionRule) \
        -> Iterator[ResolvedConstructionReturn]:
    """The masonry guard/parapet's structural (CMU) leg returning around its corner."""
    def predicate(own: Assembly, other: Assembly) -> bool:
        return _is_masonry(own) and _is_masonry(other)

    def layer_of(asm: Assembly):
        return next((layer for layer in _stack(asm)
                     if layer.function is LayerFunction.STRUCTURE), None)

    def material_of(asm: Assembly) -> float:
        layer = layer_of(asm)
        return layer.thickness.meters if layer is not None else 0.0

    yield from _find_exterior_return(
        model, rule, predicate=predicate, material_of=material_of, layer_of=layer_of,
        thermal=False, continuity_field="", treatment={"flashing": "through-wall-flashing"},
        kinds=frozenset({"l"}),
    )


def _find_sauna_liner_return(model: ResolvedModel, rule: ConstructionRule) \
        -> Iterator[ResolvedConstructionReturn]:
    """The sauna hot-side liner (foil-polyiso + T&G) wrapping onto the concrete it meets."""
    def predicate(own: Assembly, other: Assembly) -> bool:
        # The framed sauna wall carries the liner; it returns onto the concrete partner.
        return (
            _liner_layer(own) is not None
            and _framed_wood_layer(own) is not None
            and _is_concrete(other)
        )

    def layer_of(asm: Assembly):
        return _liner_layer(asm)

    def material_of(asm: Assembly) -> float:
        # Whole hot-side liner package (foil-polyiso + furring + T&G), per assembly authoring.
        return sum(
            layer.thickness.meters
            for layer in _stack(asm)
            if layer.function in (LayerFunction.INSULATION, LayerFunction.FURRING,
                                  LayerFunction.FINISH)
        ) or (_liner_layer(asm).thickness.meters if _liner_layer(asm) else 0.0)

    yield from _find_exterior_return(
        model, rule, predicate=predicate, material_of=material_of, layer_of=layer_of,
        thermal=True, continuity_field="air_vapor",
        treatment={"sealant": "foil-tape"},
    )


# Registry: applies_to predicate -> finder. Adding a rule/finder here is all that a new
# declarative return needs; unknown predicates simply emit nothing (and are flagged once).
_FINDERS = {
    "wall:framed_on_concrete": _find_framed_on_concrete,
    "floor:on_concrete_wall": _find_floor_on_concrete,
    "wall:foundation_foam_return": _find_foundation_foam_return,
    "wall:porch_masonry_return": _find_porch_masonry_return,
    "wall:sauna_liner_return": _find_sauna_liner_return,
}


def apply_construction_rules(model: ResolvedModel) -> list[Finding]:
    """Apply ``PlanModel.construction_rules`` to the resolved model, pre-framing.

    Appends each matched return's record to ``model.construction_returns``. Records only —
    never fails a build, never mutates a resolved wall or framing member, and never emits a
    ``ResolvedSolid`` (see the module docstring).
    """
    plan: PlanModel = model.plan
    for rule in plan.library.construction_rules:
        finder = _FINDERS.get(rule.applies_to)
        if finder is None:
            continue
        for ret in finder(model, rule):
            model.construction_returns.append(ret)
    return []
