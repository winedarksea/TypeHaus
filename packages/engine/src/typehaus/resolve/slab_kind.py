"""What a ``Slab`` is — pour, deck, platform or band — and the solid category it resolves to.

``Slab`` is the model's only horizontal sheet that may leave its storey datum, so it carries
laid decking, framed platforms and ground bands as well as concrete. The derivation, in order:

1. an assembly with ``role="band"`` is a ``band``;
2. ``datum="walking_surface"`` is a ``deck``;
3. no concrete layer is a ``platform`` when walls carry it, else a ``deck``;
4. anything else — an unassembled slab included — is a ``pour``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from typehaus.model.floors import Slab
    from typehaus.resolve.model import ResolvedModel

SlabKind = Literal["pour", "deck", "platform", "band"]

#: The ``ResolvedSolid.category`` each kind resolves to; all share ``slab_family="slab"``.
CATEGORY_FOR_KIND: dict[str, str] = {
    "pour": "slab", "deck": "slab_deck", "platform": "slab_platform", "band": "slab_band",
}

#: A wall plate within this of a slab's underside is carrying it.
CARRY_TOLERANCE_M = 0.3


def has_concrete_layer(plan, assembly_tag: str | None) -> bool:
    """Whether the assembly names a concrete layer; unassembled or unresolved reads True."""
    assembly = plan.library.resolve_assembly(assembly_tag) if assembly_tag else None
    if assembly is None:
        return True
    stack = list(assembly.default_lining) + list(assembly.layers)
    return any(layer.material_ref == "concrete" for layer in stack)


def _bbox(points) -> tuple[float, float, float, float]:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def _overlap(a, b) -> bool:
    return a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3]


def carried_by_walls(model: ResolvedModel, storey: str, outline, z0_m: float) -> bool:
    """Walls on the slab's storey topping out at its underside and standing under it.

    Not a foundation wall (a slab-on-grade abuts its stems), and a plate above the storey
    datum (a platform stands on the floor); both at the underside and under the outline."""
    slab_box = _bbox(outline)
    datum = next((s.elevation.meters for s in model.plan.storeys if s.tag == storey), 0.0)
    for wall in model.walls:
        if wall.storey != storey or wall.is_foundation:
            continue
        if wall.z1_m <= datum + CARRY_TOLERANCE_M or abs(wall.z1_m - z0_m) > CARRY_TOLERANCE_M:
            continue
        points = [point for layer in wall.layers for point in layer.polygon]
        if points and _overlap(slab_box, _bbox(points)):
            return True
    return False


def derive_slab_kind(model: ResolvedModel, slab: Slab, storey: str, z0_m: float) -> SlabKind:
    plan = model.plan
    assembly = plan.library.resolve_assembly(slab.assembly) if slab.assembly else None
    if assembly is not None and assembly.role == "band":
        return "band"
    if slab.datum == "walking_surface":
        return "deck"
    if not has_concrete_layer(plan, slab.assembly):
        outline = [point.xy_m for point in slab.outline]
        return "platform" if carried_by_walls(model, storey, outline, z0_m) else "deck"
    return "pour"


def slab_kind(model: ResolvedModel, slab: Slab, storey: str, z0_m: float) -> SlabKind:
    """The authored kind where there is one, else the derivation."""
    return slab.kind or derive_slab_kind(model, slab, storey, z0_m)
