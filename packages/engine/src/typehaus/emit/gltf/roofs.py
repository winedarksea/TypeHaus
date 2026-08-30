"""Roof shells: the IR's layer bands serialized, plus the skin members that trim the edge.

The geometry — the sloped planes, the perpendicular offset with its mitered ridge, the
eave-drift-compensated per-layer setbacks and the closed eave/rake perimeter — moved to
``resolve/geometry_roofs.py``. It was the third of four copies of that math, and the one the
plan blesses as canonical. What is left here is the emitter's own job: pick each band's
colour and hand its mesh to the mesh builder.

Colour still comes from the *layer* rather than from the part's ``material_key``, the same
split walls use: the IR names what a surface is (``metal``, ``membrane``), and the exporter
decides what tone that reads as — which for a named finish like standing seam is a specific
base colour, not the family average.
"""

from __future__ import annotations

from typehaus.emit.gltf.members import _add_member, is_roof_framing_member
from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.emit.gltf.palette import _material_finish_color
from typehaus.resolve.geometry_roofs import (
    _FALLBACK_FUNCTION,
    _FALLBACK_MATERIAL_REF,
    roof_parts,
)
from typehaus.resolve.model import ResolvedModel, ResolvedRoof
from typehaus.resolve.roof_layer_setbacks import above_structure_layers


def _add_roof(mb: _MeshBuilder, roof: ResolvedRoof, model: ResolvedModel,
              authored: dict | None = None) -> None:
    """Render the roof as its authored above-structure assembly stack, then its skin members.

    Each band is a closed solid, so it reads (and imports into Revit/SketchUp) as real
    thickness rather than a zero-thickness plane. Rafters and other sticks are emitted by the
    caller into the framing node; only the skin members — closure bands, derived soffit, roof
    edge cladding — belong to the roof shell and are added here.
    """
    assembly = model.plan.library.resolve_assembly(roof.assembly) if roof.assembly else None
    layers = {layer.name: layer for layer in above_structure_layers(assembly)}
    for part in roof_parts(roof, assembly):
        layer = layers.get(part.key.split(":", 1)[1])
        if layer is None:  # the no-layers-above-structure fallback band
            color = _material_finish_color(_FALLBACK_MATERIAL_REF, _FALLBACK_FUNCTION,
                                           authored)
        else:
            color = _material_finish_color(layer.material_ref, layer.function.value,
                                           authored)
        for solid in part.solids:
            mb.add_mesh(solid, color)
    for member in roof.members:
        if not is_roof_framing_member(member):
            _add_member(mb, member)
