"""A banded coating on a wall, as an ``IfcCovering`` over its band.

A coating takes no depth (decision #104), so a full-height one is an ``IfcMaterialLayer`` of
``LayerThickness`` 0 in the wall's layer set. A coating with an authored ``Layer.extent``
(a foundation protection coat to grade, a paint band above wainscot) cannot be a layer-set
row, which has no vertical extent, and is not a part of the wall's body either. It is an
applied finish, which is what ``IfcCovering`` + ``IfcRelCoversBldgElements`` say. Its body
is the same display skin glTF draws (``coating_skin_ring``), cut by the same openings, so
the two exports agree piece for piece.
"""

from __future__ import annotations

from typing import Any

from typehaus.emit.ifc import lowlevel as ll
from typehaus.model.ids import derive_child_guid
from typehaus.resolve.coatings import coating_skin_ring
from typehaus.resolve.geometry_walls import layer_solids
from typehaus.resolve.model import ResolvedLayer, ResolvedWall

#: IFC4 ``IfcCoveringTypeEnum`` has no paint or coating member.
COATING_OBJECT_TYPE = "COATING"


def is_banded_coating(layer: ResolvedLayer) -> bool:
    """A coating the layer set cannot hold: its assembly bands it (``band_spec``)."""
    return bool(layer.coating and layer.band_spec is not None and layer.polygon)


def banded_coating_pieces(rw: ResolvedWall,
                          openings: Any = ()) -> list[tuple[str, str, Any, str]]:
    """(name, guid key, solid, material) per piece; several pieces take indexed keys."""
    out = []
    for layer in rw.body_layers():
        if not is_banded_coating(layer):
            continue
        z0, z1 = layer.band(rw)
        if z1 - z0 <= 1e-9:
            continue
        pieces = [piece for piece in layer_solids(rw, coating_skin_ring(rw, layer), openings,
                                                  band=(z0, z1), layer_name=layer.name)
                  if getattr(piece, "ring", None) is not None and len(piece.ring) >= 3]
        key = f"{rw.uid}/{layer.name}"
        for index, piece in enumerate(pieces):
            if len(pieces) == 1:
                out.append((f"{rw.tag}:{layer.name}", key, piece, layer.material_ref))
            else:
                out.append((f"{rw.tag}:{layer.name} ({index + 1}/{len(pieces)})",
                            f"{key}#{index}", piece, layer.material_ref))
    return out


def emit_banded_coatings(f: Any, body: Any, wall: Any, rw: ResolvedWall, storey: Any,
                         project_uuid: Any, openings: Any = ()) -> list[Any]:
    """One ``IfcCovering`` per banded-coating piece, related to ``wall`` as its covering.

    The GUID namespace is the banded part's (``wall-parts``): these exported as parts
    before coatings lost their depth, and an identity outlives a change of class.
    """
    coverings = []
    for name, key, piece, material_ref in banded_coating_pieces(rw, openings):
        covering = ll.create_entity(f, "IfcCovering", name=name)
        covering.GlobalId = derive_child_guid(project_uuid, "wall-parts", key)
        covering.PredefinedType = "USERDEFINED"
        covering.ObjectType = COATING_OBJECT_TYPE
        ll.assign_representation(f, covering, ll.add_prism_from_profile(
            f, body, [(x, y) for x, y in piece.ring], piece.z1_m - piece.z0_m, piece.z0_m))
        material = f.create_entity("IfcMaterial", Name=material_ref)
        f.create_entity("IfcRelAssociatesMaterial", GlobalId=ll.new_guid(),
                        RelatedObjects=[covering], RelatingMaterial=material)
        ll.assign_container(f, covering, storey)
        coverings.append(covering)
    if coverings:
        f.create_entity("IfcRelCoversBldgElements", GlobalId=ll.new_guid(),
                        RelatingBuildingElement=wall, RelatedCoverings=coverings)
    return coverings
