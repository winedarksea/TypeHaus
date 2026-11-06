"""Every ceiling's layer stack and the face it covers: the one walk ceilings bill from.

Board hangs between the walls, not over them. ``model.ceilings`` is each room's ceiling cut
to its clear face, per deck region and around every deck hole; a face no Room claims (the
attic stair hall) still has a ceiling, hung from its deck's or roof's own stack and net of
the storey's walls. Sheet goods, the envelope's liner rows and the paint all read this, so
they agree on one area. Roof cavity fill still bills off the gross bearing plane
(``roof_ceiling_area_m2``): it does run over the wall tops.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from shapely.geometry import Polygon

from typehaus.model.assembly import Layer
from typehaus.model.refs import FollowRoof
from typehaus.model.spatial import Roof
from typehaus.resolve.ceiling_over import ceiling_decks_over, ceiling_regions, room_roof_over
from typehaus.resolve.model import ResolvedModel, ResolvedRoof
from typehaus.resolve.overlay import difference
from typehaus.resolve.roof_geometry import roof_is_trussed
from typehaus.resolve.rooms import room_faces
from typehaus.resolve.wall_faces import storey_wall_mass


@dataclass(frozen=True)
class CeilingPiece:
    """One ceiling face: its stack (room side first), area, and where it hangs."""

    storey: str
    layers: tuple[Layer, ...]
    area_m2: float
    #: The room's own ``ceiling_lining``, not its deck's or roof's stack.
    lining: bool = False


def ceiling_pieces(model: ResolvedModel) -> list[CeilingPiece]:
    """Every resolved room ceiling, then every ceiling over a face no Room claims."""
    pieces = []
    for ceiling in model.ceilings:
        room = model.plan.by_tag(ceiling.room_ref)
        pieces.append(CeilingPiece(ceiling.storey, tuple(ceiling.layers),
                                   ceiling_area_m2(model, ceiling),
                                   bool(getattr(room, "ceiling_lining", ()))))
    return pieces + unroomed_ceilings(model)


def unroomed_ceilings(model: ResolvedModel) -> list[CeilingPiece]:
    """The host's stack over each face no Room claims, net of the storey's walls."""
    plan = model.plan
    pieces: list[CeilingPiece] = []
    for storey in plan.storeys:
        claimed, open_faces = room_faces(plan, storey.tag)
        if not open_faces:
            continue
        mass = storey_wall_mass(model, storey.tag,
                                [face for _room, face in claimed] + open_faces)
        for face in open_faces:
            if ceiling_decks_over(plan, storey.tag, face):
                pieces += [CeilingPiece(storey.tag, tuple(region.deck.ceiling_below),
                                        difference(region.face, mass).area)
                           for region in ceiling_regions(plan, storey.tag, face, model.walls)
                           if region.deck.ceiling_below]
                continue
            roof = next((r for r in model.roofs if r.storey == storey.tag
                         and len(r.footprint) >= 3
                         and Polygon(r.footprint).contains(face.representative_point())), None)
            assembly = (plan.library.resolve_assembly(roof.assembly)
                        if roof is not None and roof.assembly else None)
            if assembly is not None and assembly.default_lining:
                pieces.append(CeilingPiece(storey.tag, tuple(assembly.default_lining),
                                           difference(face, mass).area * _slope(model, roof)))
    return [piece for piece in pieces if piece.area_m2 > 0.0]


def _slope(model: ResolvedModel, roof: ResolvedRoof | None) -> float:
    """The sloped-to-plan area factor of a rafter roof's ceiling; 1.0 on a truss's flat one."""
    source = None if roof is None else model.plan.by_tag(roof.tag)
    if roof is None or roof_is_trussed(model, roof) or not isinstance(source, Roof):
        return 1.0
    return math.sqrt(1.0 + (source.pitch.rise / source.pitch.run) ** 2)


def ceiling_area_m2(model: ResolvedModel, ceiling) -> float:
    """The ceiling's face: its plan outline, sloped where it follows a rafter roof."""
    area = abs(Polygon(ceiling.outline).area)
    room = model.plan.by_tag(ceiling.room_ref)
    if not isinstance(getattr(room, "ceiling", None), FollowRoof):
        return area
    source = room_roof_over(model.plan, ceiling.storey, room)
    roof = next((r for r in model.roofs if source is not None and r.tag == source.tag), None)
    return area * _slope(model, roof)
