"""Build the derived-geometry IR from a resolved model — the pipeline's final stage.

This is where geometry stops being re-derived per emitter. Each stage below turns one family
of resolved records into :class:`ElementGeometry`, applying the shape math *once*; the IFC,
glTF, model.json and 2D-section consumers then read the result.

Landing in sequence (→ the vision-alignment plan, D3): members, solids and solar panels
first, with a shadow-parity test proving the IR reproduces what the emitters draw today.
Walls, openings, roofs, floors and earth follow.
"""

from __future__ import annotations

from typehaus.emit.finishes import member_material_key, normalize
from typehaus.resolve.geometry_ir import (
    ElementGeometry,
    GBox,
    GeometryModel,
    GPart,
    GPrism,
)
from typehaus.resolve.geometry_members import member_box, member_part_key, member_uid
from typehaus.resolve.model import FramedMember, ResolvedModel, ResolvedSolid


def _member_parts(members: tuple[FramedMember, ...] | list[FramedMember],
                  owner_uid: str) -> tuple[GPart, ...]:
    parts: list[GPart] = []
    for member in members:
        box = member_box(member)
        if box is None:  # too degenerate to draw at all
            continue
        parts.append(GPart(
            key=member_part_key(member),
            solids=(box,),
            material_key=member_material_key(member),
            layer_group="framing",
            member_uid=member_uid(member),
        ))
    return tuple(parts)


def _solid_geometry(solid: ResolvedSolid) -> ElementGeometry:
    """A slab/footing/pad: its plan outline extruded between its two elevations.

    ``voids`` ride the prism rather than being pre-subtracted, so the IFC emitter can express
    them as real openings while the glTF emitter tessellates them away — same input, each
    format's own idiom.
    """
    prism = GPrism(ring=solid.outline, z0_m=solid.z0_m, z1_m=solid.z1_m,
                   voids=tuple(solid.voids))
    return ElementGeometry(
        uid=solid.uid, kind=solid.category, trade="concrete",
        parts=(GPart(key="body", solids=(prism,),
                     material_key=normalize(solid.category),
                     layer_group="structure"),),
    )


def _solar_geometry(panel) -> ElementGeometry:
    """The precedent this IR generalized: a PV module already *was* eight corners."""
    return ElementGeometry(
        uid=panel.uid, kind="solar_panel", trade="electrical",
        parts=(GPart(key="module",
                     solids=(GBox(corners_bottom=panel.corners_bottom,
                                  corners_top=panel.corners_top),),
                     material_key="solar", layer_group="cladding"),),
    )


def build_geometry(model: ResolvedModel) -> GeometryModel:
    """Derive the whole building's geometry once."""
    elements: list[ElementGeometry] = []

    # Framing rides its owner, so a wall's studs stay addressable as that wall's parts —
    # which is what lets the exporter merge them into one node per owner and still resolve a
    # pick back to the individual stick.
    for owner, trade in ((model.walls, "walls"), (model.floors, "floors"),
                         (model.roofs, "roof"), (getattr(model, "stairs", ()), "stairs")):
        for host in owner:
            parts = _member_parts(getattr(host, "members", ()), host.uid)
            if parts:
                elements.append(ElementGeometry(
                    uid=f"{host.uid}::framing", kind="framing", trade="framing", parts=parts,
                ))

    for solid in model.solids:
        elements.append(_solid_geometry(solid))
    for panel in getattr(model, "solar_panels", ()):
        elements.append(_solar_geometry(panel))

    return GeometryModel(elements=tuple(elements))
