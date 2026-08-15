"""Corner returns: a control or finish layer of one wall turning onto the wall it meets.

Three declarative finders over one generic engine (:func:`_find_exterior_return`) — the
foundation foam turning an L for thermal continuity, the masonry guard's CMU leg, the sauna
liner wrapping onto the concrete it tees into. Each supplies only a predicate, the layer to
return and its treatment; the corner arithmetic, the de-duplication of directed legs and
the ``condition_key`` are written once here, because a second copy of that walk is how two
returns start disagreeing about which junction they belong to.
"""

from __future__ import annotations

from collections.abc import Iterator

from typehaus.model.assembly import Assembly, ConstructionRule
from typehaus.model.enums import LayerFunction
from typehaus.resolve.construction_assemblies import (
    _exterior_thermal_layers,
    _framed_wood_layer,
    _is_concrete,
    _is_masonry,
    _liner_layer,
    _stack,
)
from typehaus.resolve.construction_geometry import _condition_key, _strip
from typehaus.resolve.model import ResolvedConstructionReturn, ResolvedModel


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
