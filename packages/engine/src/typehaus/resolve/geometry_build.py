"""Build the derived-geometry IR from a resolved model — the pipeline's final stage.

This is where geometry stops being re-derived per emitter. Each stage below turns one family
of resolved records into :class:`ElementGeometry`, applying the shape math *once*; the IFC,
glTF, model.json and 2D-section consumers then read the result.

Landed in sequence (→ the vision-alignment plan, D3–D5): members, solids and solar panels
first, then walls, then openings, roofs, floor decks and the site earth — each with a
shadow-parity test proving the IR reproduces what the emitters drew, except where the plan
blesses a diff. Both Python emitters now read this instead of deriving anything: ``emit/gltf``
end to end, and ``emit/ifc`` for the roof shell, the site earth sheet and the floor deck (it
keeps its own swept solids for members and its opening/void idiom for walls, which are proper
IFC, and which the IR's member solid was ported *from*).

The four blessed diffs, all landed: the glTF member box gains its true section; IFC's roof
layers gain the perpendicular offset and eave-drift compensation the viewer already had; a
floor gains a real deck (no emitter drew one); and the earth becomes geometry — the glTF
``earth`` trade was empty, and IFC's pad stood 5cm *above* grade rather than under it.

The viewer's three.js builders are deliberately *not* on this path: that render path stays
(→ ``WHOLE_HOUSE_GLB_PRIMARY``), so the vocabularies it shares with the emitters are pinned by
parity tests instead.
"""

from __future__ import annotations

from typehaus.emit.finishes import (
    layer_material_key,
    layer_visibility_group,
    member_material_key,
    normalize,
)
from typehaus.emit.trades import solid_trade
from typehaus.resolve.assembly_material import solid_material_ref
from typehaus.resolve.geometry_ir import (
    ElementGeometry,
    GBox,
    GeometryModel,
    GPart,
    GPrism,
    PartCatalogRef,
)
from typehaus.resolve.geometry_members import member_box, member_part_key, member_uid
from typehaus.resolve.geometry_openings import opening_parts
from typehaus.resolve.geometry_roofs import roof_parts
from typehaus.resolve.geometry_walls import layer_solids
from typehaus.resolve.model import (
    FramedMember,
    ResolvedFloor,
    ResolvedModel,
    ResolvedRoof,
    ResolvedSolid,
    ResolvedWall,
)
from typehaus.resolve.site_earth import earth_plane_void_rings, site_grade_elevation_m

# The site sheet is a presentation surface, not an excavation model: thick enough to read as
# ground from any angle, thin enough that no consumer mistakes it for fill.
EARTH_SHEET_THICKNESS_M = 0.05


def _member_parts(members: tuple[FramedMember, ...] | list[FramedMember],
                  owner_uid: str) -> tuple[GPart, ...]:
    parts: list[GPart] = []
    for member in members:
        if member.plan_outline is not None:
            # Polygonal stair treads (winders): a GBox can't express a trapezoid, so the
            # member's own footprint rides straight through as a prism instead of being
            # silently dropped.
            solid = GPrism(ring=member.plan_outline, z0_m=member.z0_m, z1_m=member.z1_m)
        else:
            solid = member_box(member)
        if solid is None:  # too degenerate to draw at all
            continue
        parts.append(GPart(
            key=member_part_key(member),
            solids=(solid,),
            material_key=member_material_key(member),
            # Framing is a trade toggle, not a band of an assembly stack — except for
            # the skin members (closure bands, derived trim), which belong with the
            # layer they continue.
            layer_group=(layer_visibility_group(member.category)
                         if member.material else "structure"),
            member_uid=member_uid(member),
            catalog=PartCatalogRef(material_ref=member.material, role=member.category,
                                   name=member.child_key, profile=member.profile),
        ))
    return tuple(parts)


def _wall_geometry(wall: ResolvedWall, openings) -> ElementGeometry:
    """A wall's body: one part per depth-bearing layer, jamb-split around its openings.

    Every layer with a body of its own gets a part — which is ``body_layers()``, not
    ``depth_layers()``: the latter counts a ``Layer.slot``'s regions once for *depth*
    accounting, and building from it left a brick plinth standing with its own field and
    bands missing above it. Cavity fill shares the structure layer's polygon, so a second
    solid there would only z-fight it, and neither list carries it.
    """
    parts: list[GPart] = []
    for layer in wall.body_layers():
        if not layer.polygon:
            continue
        solids = layer_solids(wall, layer.polygon, openings,
                              band=layer.band(wall) if layer.is_banded else None)
        if not solids:
            continue
        function = (layer.function.value if hasattr(layer.function, "value")
                    else str(layer.function))
        parts.append(GPart(
            key=f"layer:{layer.name}",
            solids=solids,
            material_key=normalize(function),
            layer_group=layer_visibility_group(function),
            catalog=PartCatalogRef(material_ref=layer.material_ref, role=function,
                                   name=layer.name,
                                   thickness_m=layer.thickness_m),
        ))
    return ElementGeometry(uid=wall.uid, kind="wall", trade="walls", parts=tuple(parts))


def _solid_geometry(solid: ResolvedSolid, plan) -> ElementGeometry:
    """Any solid — pour, beam, post, pipe run, trim: its plan outline extruded between its
    two elevations.

    ``voids`` ride the prism rather than being pre-subtracted, so the IFC emitter can express
    them as real openings while the glTF emitter tessellates them away — same input, each
    format's own idiom.
    """
    prism = GPrism(ring=solid.outline, z0_m=solid.z0_m, z1_m=solid.z1_m,
                   voids=tuple(solid.voids))
    return ElementGeometry(
        uid=solid.uid, kind=solid.category, trade=solid_trade(solid.category),
        parts=(GPart(key="body", solids=(prism,),
                     material_key=normalize(solid.category),
                     layer_group="structure",
                     catalog=PartCatalogRef(material_ref=solid_material_ref(plan, solid),
                                            role=solid.category, name=solid.tag)),),
    )


def _opening_geometry(wall: ResolvedWall, opening, door_types) -> ElementGeometry:
    """The door or window product standing in a wall's void — frame, mullion, leaf, glass."""
    door_type = door_types.get(opening.type_ref) if opening.is_door else None
    parts = opening_parts(
        wall, opening,
        operation=door_type.operation if door_type is not None else None,
        is_glazed=door_type is not None and door_type.glazed,
        is_trimless=door_type is not None and door_type.trimless,
    )
    return ElementGeometry(uid=opening.uid, kind="opening", trade="openings", parts=parts)


def _roof_geometry(roof: ResolvedRoof, model: ResolvedModel) -> ElementGeometry:
    assembly = model.plan.library.resolve_assembly(roof.assembly) if roof.assembly else None
    return ElementGeometry(uid=roof.uid, kind="roof", trade="roof",
                           parts=roof_parts(roof, assembly))


def _floor_deck_geometry(floor: ResolvedFloor) -> ElementGeometry | None:
    """The subfloor sheet over a floor's joists.

    One of the plan's four blessed diffs: glTF drew no deck at all (joists hanging in space)
    and IFC drew none either, so a floor exported as a field of beams with nothing on them.
    """
    if len(floor.deck_outline) < 3 or floor.deck_z1_m <= floor.deck_z0_m:
        return None
    prism = GPrism(ring=tuple(tuple(p) for p in floor.deck_outline),
                   z0_m=floor.deck_z0_m, z1_m=floor.deck_z1_m,
                   voids=tuple(tuple(tuple(p) for p in ring) for ring in floor.deck_voids))
    return ElementGeometry(
        uid=floor.uid, kind="floor", trade="floors",
        parts=(GPart(key="deck", solids=(prism,),
                     material_key=layer_material_key(floor.deck_material_ref, "sheathing"),
                     layer_group="sheathing",
                     catalog=PartCatalogRef(material_ref=floor.deck_material_ref,
                                            role="sheathing", name="deck",
                                            thickness_m=floor.deck_z1_m - floor.deck_z0_m)),),
    )


def _earth_geometry(model: ResolvedModel) -> ElementGeometry | None:
    """The site earth sheet: the parcel at grade, cut by everything excavated out of it.

    Blessed diff: glTF's ``earth`` trade was empty, so the exported model floated with no
    ground under it while the viewer drew a sheet. The pad hangs *below* grade — its top face
    is the grade plane — because that is where soil is; IFC's site pad currently sits the same
    5cm above grade it always has, and reconciling that is part of the IFC switchover.
    """
    parcel = [point.xy_m for point in model.plan.project.site.parcel]
    if len(parcel) < 3:
        return None
    grade_z = site_grade_elevation_m(model)
    voids = tuple(tuple(tuple(p) for p in ring) for ring in earth_plane_void_rings(model))
    prism = GPrism(ring=tuple(tuple(p) for p in parcel),
                   z0_m=grade_z - EARTH_SHEET_THICKNESS_M, z1_m=grade_z, voids=voids)
    return ElementGeometry(
        uid="site-earth", kind="earth", trade="earth",
        parts=(GPart(key="sheet", solids=(prism,), material_key="earth", layer_group="other"),),
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

    openings_by_wall: dict[str, list] = {}
    for opening in model.openings:
        openings_by_wall.setdefault(opening.host_wall, []).append(opening)
    walls_by_tag = {wall.tag: wall for wall in model.walls}
    for wall in model.walls:
        elements.append(_wall_geometry(wall, openings_by_wall.get(wall.tag, ())))

    door_types = {dt.tag: dt for dt in model.plan.library.door_types}
    for opening in model.openings:
        host = walls_by_tag.get(opening.host_wall)
        if host is not None:
            elements.append(_opening_geometry(host, opening, door_types))

    for roof in model.roofs:
        elements.append(_roof_geometry(roof, model))

    for floor in model.floors:
        deck = _floor_deck_geometry(floor)
        if deck is not None:
            elements.append(deck)

    for solid in model.solids:
        elements.append(_solid_geometry(solid, model.plan))
    for panel in getattr(model, "solar_panels", ()):
        elements.append(_solar_geometry(panel))

    earth = _earth_geometry(model)
    if earth is not None:
        elements.append(earth)

    return GeometryModel(elements=tuple(elements))
