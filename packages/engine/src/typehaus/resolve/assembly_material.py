"""Assembly → finish-material reduction, shared where an element's *assembly* has to
collapse to one material ref.

A finish-only assembly (``POST_WHITE_PAINT``: one painted-lumber layer standing in for a
6x6's body) says what an element is made of, but a :class:`~typehaus.resolve.model.
FramedMember` carries a single ``material`` slot, not a layer stack. The reduction is the
one ``emit/gltf/palette.py::_solid_color`` already applies to solids with an assembly: the
STRUCTURE layer's material, falling back to the first layer. Factored here so the resolver
(a knee brace's diagonal) and the palette agree on which layer speaks for the assembly —
duplicating the index rule is how the .glb and the IFC would drift.
"""

from __future__ import annotations


def assembly_structure_material(plan, assembly_tag: str | None) -> str | None:
    """The material ref of ``assembly_tag``'s STRUCTURE layer (first layer when none is
    marked), or ``None`` for no/unknown assembly. Mirrors the assembly branch of
    ``emit/gltf/palette.py::_solid_color``."""
    if not assembly_tag:
        return None
    assembly = plan.library.resolve_assembly(assembly_tag)
    if assembly is None or not assembly.layers:
        return None
    idx = assembly.structure_index()
    return assembly.layers[idx if idx is not None else 0].material_ref


def solid_material_ref(plan, solid) -> str:
    """What a resolved solid is *made of* — its own ref, its assembly's, else a default.

    ``emit/draw/section.py::_solid_material`` was this walk, with a docstring admitting it
    duplicated ``emit/gltf/palette.py::_solid_color``. Hatching a detail and colouring the
    GLB are different questions with the same answer underneath, and they disagreed: every
    solid hatched as concrete in section, which is right for a footing and wrong for a
    composite deck, an aluminium extrusion or a glass baluster panel — all of which a detail
    exists to tell apart.

    The direct ref is read first because the assembly cannot answer for a solid that has no
    business having one: a guard's glass lite and its aluminium posts share one
    ``Railing.assembly``, and the whole point of the per-part material refs is that they are
    not the same material.

    Without either, the fallback reads the member's own *section*, because that is what
    actually says what it is made of: a "6x6" or a "2-2x8" is dressed lumber, a "12 round" is
    a sonotube-cast concrete pier. Slabs, footings and pads stay concrete — the case the old
    blanket rule was right about.
    """
    if solid.material:
        return solid.material
    from_assembly = assembly_structure_material(plan, solid.assembly)
    if from_assembly:
        return from_assembly
    if solid.category in ("beam", "column"):
        element = plan.by_tag(solid.tag)
        size = getattr(element, "size", "") or ""
        if not size.strip().endswith("round"):
            return "spf"
    return "concrete"
