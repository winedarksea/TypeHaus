"""What a slab stands on, drawn: its assembly's layers below the pour.

A ``Slab`` resolves to one solid of its authored ``thickness``, and on a slab on grade that is
the concrete alone. The XPS, the vapour retarder and the stone base under it were billed
(``takeoff/envelope.py`` walks the assembly) and never drawn, so the viewer showed a 4" slab
floating on the soil it was meant to sit 8" above. Each such layer is added here as a
``derived`` solid stacked down from the pour's underside: the viewer and glTF draw it, and
everything that measures skips it (``ResolvedSolid.derived``), so nothing bills twice.

Only layers wholly below the drawn thickness, and only a base course or a board
(SHEATHING / INSULATION / MEMBRANE). A slab whose ``thickness`` already spans its stack (the
EPS deck form, the putting green) draws nothing more, and a suspended deck's furring and
gypsum are its ceiling, which ``resolve/ceilings.py`` draws. A layer under 1/4" (a 10-mil
poly) is skipped: it would only z-fight, and the layers below keep their true depth.
"""

from __future__ import annotations

from typehaus.model.enums import LayerFunction
from typehaus.resolve.model import ResolvedModel, ResolvedSolid

CATEGORY = "sub_slab"
_DRAWN = frozenset({LayerFunction.SHEATHING, LayerFunction.INSULATION, LayerFunction.MEMBRANE})
_MIN_DRAWN_M = 0.25 * 0.0254
_TOL_M = 1e-4


def resolve_slab_layers(model: ResolvedModel) -> None:
    """Append one derived ``sub_slab`` solid per drawable layer under each slab."""
    slabs = [s for s in model.solids if s.category == "slab" and s.assembly and not s.derived]
    for slab in slabs:
        assembly = model.plan.library.resolve_assembly(slab.assembly)
        if assembly is None:
            continue
        drawn_m = slab.z1_m - slab.z0_m
        depth_m = 0.0  # down from the slab's top
        for layer in assembly.layers:
            top_m, depth_m = depth_m, depth_m + layer.thickness.meters
            if top_m < drawn_m - _TOL_M:
                continue  # inside the solid the slab already draws
            if layer.function not in _DRAWN or layer.thickness.meters < _MIN_DRAWN_M:
                continue
            model.solids.append(ResolvedSolid(
                uid=f"{slab.uid}-{layer.name}", tag=f"{slab.tag}:{layer.name}",
                storey=slab.storey, category=CATEGORY, outline=list(slab.outline),
                z0_m=slab.z1_m - depth_m, z1_m=slab.z1_m - top_m, voids=slab.voids,
                material=layer.material_ref, derived=True))
