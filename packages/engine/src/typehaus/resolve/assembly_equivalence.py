"""Assemblies a drawing cannot tell apart (→ condition keys).

A ``variant_of`` assembly that differs from its base only in top-plate species frames the
same junctions, so its condition keys name the base: one detail sheet, not two.
"""

from __future__ import annotations


def layer_signature(asm) -> tuple:
    """Material and role per layer, plus framing: a 2x4 run meeting a staggered 2x6 wet wall
    jogs both faces, which material and role alone cannot see."""
    return tuple((layer.material_ref, layer.function,
                  getattr(getattr(layer, "framing", None), "member", None),
                  getattr(getattr(layer, "framing", None), "layout", None))
                 for layer in asm.layers)


def _drawn_layers(asm) -> list:
    """Every layer field but the top plates' species, which no detail draws."""
    out = []
    for layer in asm.layers:
        dump = layer.model_dump()
        if isinstance(dump.get("framing"), dict):
            dump["framing"].pop("top_plate_material_ref", None)
        out.append(dump)
    return out


def drawn_assembly(plan, tag: str) -> str:
    """``tag``, or its ``variant_of`` base when the two differ only in top-plate species."""
    asm = plan.library.resolve_assembly(tag) if plan is not None else None
    base_tag = getattr(asm, "variant_of", None)
    base = plan.library.resolve_assembly(base_tag) if base_tag else None
    if base is not None and _drawn_layers(asm) == _drawn_layers(base):
        return base_tag
    return tag
