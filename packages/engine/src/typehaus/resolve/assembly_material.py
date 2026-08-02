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


def assembly_structure_material(plan, assembly_tag: "str | None") -> "str | None":
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
