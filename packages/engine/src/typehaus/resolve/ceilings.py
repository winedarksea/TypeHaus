"""Per-room ceiling construction: what covers a room overhead, and its finished plane.

Three sources, in priority order, mirroring ``Room.wall_lining``'s precedence over a wall
assembly's own ``default_lining``:

1. ``Room.ceiling_lining`` — an explicit override authored on the room (the plant room's
   humidity liner, the sauna's T&G).
2. The covering deck's ``ceiling_below`` (``FloorSystem`` or ``Slab``,
   :func:`typehaus.resolve.ceiling_over.ceiling_decks_over`).
3. Where the room has no deck above it at all, its own ``Roof``'s ``default_lining``
   (:func:`typehaus.resolve.ceiling_over.room_roof_over`) — the garage's boarded truss
   bottom chord, or an attic room's ``FollowRoof`` ceiling.

Open-to-structure — none of the three resolves a stack — is a legitimate fallback, not an
error: nothing is billed and nothing is drawn.

A flat plane (a deck overhead, or a room sitting under a truss roof's flat bottom chord)
gets a ``ResolvedSolid`` too, which is what makes it render — the same
``ResolvedSoffit``/``ResolvedSolid`` split :mod:`typehaus.resolve.envelope` already uses
for a dropped ceiling. A room whose ceiling follows a sloped roof
(``Room.ceiling=FollowRoof(...)``) has no single flat plane to draw, so only the layer
stack is carried, for the checks and the takeoff that read it.
"""

from __future__ import annotations

from shapely.geometry import Polygon

from typehaus.model.plan import PlanModel
from typehaus.model.refs import FollowRoof
from typehaus.resolve.ceiling_over import (
    ceiling_decks_over,
    deck_structure_underside_m,
    finish_layer,
    room_roof_over,
)
from typehaus.resolve.model import ResolvedCeiling, ResolvedModel, ResolvedSolid


def resolve_ceilings(plan: PlanModel, model: ResolvedModel) -> None:
    """Populate ``model.ceilings`` (and a "ceiling" ``ResolvedSolid`` per flat one).

    Runs after :func:`typehaus.resolve.rooms.resolve_rooms`: it reads each room's resolved
    clear face, so a room that has not yet claimed one has nothing for this stage to hang a
    ceiling under.
    """
    for storey in plan.storeys:
        for room in (e for e in plan.storey_elements(storey.tag)
                     if e.element_kind == "Room"):
            resolved_room = next((r for r in model.rooms if r.tag == room.tag), None)
            if resolved_room is None or len(resolved_room.clear_face) < 3:
                continue
            face = Polygon(resolved_room.clear_face)
            layers, structure_z = _resolve_stack(plan, storey.tag, room, face)
            if not layers:
                continue
            z0 = None if structure_z is None else structure_z - sum(
                layer.thickness.meters for layer in layers)
            z1 = structure_z
            uid, tag = f"{room.uid}-ceiling", f"CEIL-{room.tag}"
            model.ceilings.append(ResolvedCeiling(
                uid=uid, tag=tag, storey=storey.tag, room_ref=room.tag,
                outline=resolved_room.clear_face, z0_m=z0, z1_m=z1, layers=layers,
            ))
            if z0 is not None and z1 is not None:
                finish = finish_layer(layers)
                model.solids.append(ResolvedSolid(
                    uid, tag, storey.tag, "ceiling", resolved_room.clear_face, z0, z1,
                    material=finish.material_ref if finish is not None else None,
                ))


def _resolve_stack(plan: PlanModel, storey_tag: str, room,
                   face: Polygon) -> tuple[tuple, float | None]:
    """The room's ceiling layer stack, room side first, and its structure-side elevation.

    The elevation is None only for a room following a sloped roof — every other case
    resolves a real structural fact (a joist soffit, a slab underside, or the storey's own
    ceiling-height convention for a flat roof directly overhead) that the layer stack hangs
    below.
    """
    decks = [(s, d, z) for s, d in ceiling_decks_over(plan, storey_tag, face)
             if (z := deck_structure_underside_m(s, d)) is not None]
    if decks:
        _, deck, structure_z = min(decks, key=lambda item: item[2])
        layers = room.ceiling_lining or deck.ceiling_below
        return tuple(layers), structure_z
    roof = room_roof_over(plan, storey_tag, room)
    if roof is None:
        return (), None
    assembly = plan.library.resolve_assembly(roof.assembly)
    default_lining = assembly.default_lining if assembly is not None else ()
    layers = tuple(room.ceiling_lining or default_lining)
    if not layers:
        return (), None
    if isinstance(room.ceiling, FollowRoof):
        return layers, None
    storey = next(s for s in plan.storeys if s.tag == storey_tag)
    return layers, storey.elevation.meters + storey.default_ceiling_height.meters
