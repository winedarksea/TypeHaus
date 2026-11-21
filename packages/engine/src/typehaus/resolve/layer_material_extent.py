"""``LayerMaterial.extent``: a material swap that covers one band of a layer, not all of it.

Abuse-resistant board on the lower 4' under plain gypsum is one row of the stack in two
materials, which is what ``Layer.slot`` already is. The wall's stack is split BEFORE its
spans and bands resolve, so the existing slot/band machinery (one depth, two elevations)
does the rest: the band takes the override material, the remainder (below and/or above)
keeps the layer's own, as slot-mates named ``<layer>-lower`` / ``<layer>-upper``.
"""

from __future__ import annotations

from typing import Any

from typehaus.model.layer_extent import LayerExtent


def splittable(layer: Any) -> bool:
    """A plain full-height row: banded, slotted, run-spanned or cavity layers are not split."""
    return (getattr(layer, "extent", None) is None and getattr(layer, "slot", None) is None
            and getattr(layer, "run_span", None) is None
            and getattr(layer, "cavity", None) is None
            and getattr(layer, "framing", None) is None)


def split_extent_overrides(stack: list, layer_materials: tuple) -> tuple[list, set[str]]:
    """``stack`` with each extent override's layer split in two or three, and the names done.

    The caller drops the returned names from its whole-layer override map: the band layer
    already carries its material. An override on a layer that is not :func:`splittable`
    is left to the whole-layer path (``integrity.wall_layer_material`` reports it).
    """
    extents = {lm.layer: lm for lm in layer_materials if lm.extent is not None}
    if not extents:
        return stack, set()
    out: list = []
    done: set[str] = set()
    for layer in stack:
        override = extents.get(getattr(layer, "name", None))
        if override is None or not splittable(layer):
            out.append(layer)
            continue
        slot = f"{layer.name}-split"
        extent = override.extent
        regions = [(f"{layer.name}-lower", layer.material_ref,
                    LayerExtent(top=extent.bottom)) if extent.bottom is not None else None,
                   (layer.name, override.material, extent),
                   (f"{layer.name}-upper", layer.material_ref,
                    LayerExtent(bottom=extent.top)) if extent.top is not None else None]
        out.extend(layer.model_copy(update={"name": name, "material_ref": material,
                                            "extent": region, "slot": slot})
                   for name, material, region in filter(None, regions))
        done.add(layer.name)
    return out, done
