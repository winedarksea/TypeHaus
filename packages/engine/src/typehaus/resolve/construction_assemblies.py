"""What kind of wall is this? — the assembly predicates every construction finder asks.

A finder's ``applies_to`` predicate is nearly always a question about the *layers* of the
two assemblies meeting at a junction: is this concrete, is it real unit masonry (and not an
ICF core wearing a ``MasonrySpec``), which layer is the stud, which is the continuous
exterior insulation, which is the sauna's vapour liner. Those readings are shared here so
two finders cannot disagree about what "concrete" means — the foam return and the sill
plate must select the same set of walls or one of them bills a return that is not there.
"""

from __future__ import annotations

from typehaus.model.assembly import Assembly
from typehaus.model.enums import ControlLayer, LayerFunction


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

