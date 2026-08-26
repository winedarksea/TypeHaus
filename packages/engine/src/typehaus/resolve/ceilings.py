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

**A room is not guaranteed one ceiling.** Where two decks meet inside a room, each hangs
its own board at its own elevation, so the room resolves one record per deck region
(:func:`typehaus.resolve.ceiling_over.ceiling_regions`) — see catlin's `RM-B-GYM`, which
steps 1 9/16" where `FS-M-EAST`'s joist soffit meets `SL-M-DECK`'s deeper EPS band. Every
consumer here reads ``model.ceilings`` as a list and filters by ``room_ref``, so this is a
question of how many records a room contributes, not of a changed shape.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from shapely.geometry import Polygon

from typehaus.model.assembly import Layer
from typehaus.model.plan import PlanModel
from typehaus.model.refs import FollowRoof
from typehaus.resolve.ceiling_over import (
    ceiling_regions,
    finish_layer,
    polygon_parts,
    room_roof_over,
)
from typehaus.resolve.model import ResolvedCeiling, ResolvedModel, ResolvedSolid, Ring
from typehaus.resolve.overlay import union_all

#: A ceiling's layer stack, room side first — the shape ``ResolvedCeiling.layers`` carries.
Stack = tuple[Layer, ...]
#: Two stacks with equal keys are the same construction, so the decks carrying them line
#: up as ONE ceiling rather than a step. A ``Layer`` is not itself hashable.
StackKey = tuple[tuple[str, str, float, str], ...]


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
            for uid, tag, outline, layers, structure_z in _pieces(
                    plan, storey.tag, room, face, resolved_room.clear_face):
                z0 = None if structure_z is None else structure_z - sum(
                    layer.thickness.meters for layer in layers)
                z1 = structure_z
                model.ceilings.append(ResolvedCeiling(
                    uid=uid, tag=tag, storey=storey.tag, room_ref=room.tag,
                    outline=outline, z0_m=z0, z1_m=z1, layers=layers,
                ))
                if z0 is not None and z1 is not None:
                    finish = finish_layer(layers)
                    model.solids.append(ResolvedSolid(
                        uid, tag, storey.tag, "ceiling", outline, z0, z1,
                        material=finish.material_ref if finish is not None else None,
                    ))


def _pieces(plan: PlanModel, storey_tag: str, room: Any, face: Polygon,
            clear_face: Ring) -> Iterator[tuple[str, str, Ring, Stack, float | None]]:
    """``(uid, tag, outline, layers, structure_z)`` per ceiling this room resolves.

    A room whose ceiling resolves to ONE plane — under a single deck, under none, or under
    two decks that hang the same board at the same elevation — keeps the plain
    ``CEIL-<room>`` tag and the room's own clear face verbatim, which is the shape this
    stage emitted before a room could be split, and what an IFC GlobalId minted from the
    uid depends on staying put. Only a room whose ceiling genuinely *steps* takes suffixed
    tags: a deck seam is not by itself a step, and `RM-M-LIVING` spanning both halves of
    the second floor's 11 7/8"-deep truss/I-joist split is one flat ceiling, deliberately
    (`houses/catlin/CLAUDE.md`). What splits `RM-B-GYM` is the 1 9/16" the EPS band hangs
    below the joists beside it, not the fact that two decks meet in the room.
    """
    regions = ceiling_regions(plan, storey_tag, face)
    if not regions:
        layers, structure_z = _no_deck_stack(plan, storey_tag, room)
        if not layers:
            return
        yield f"{room.uid}-ceiling", f"CEIL-{room.tag}", clear_face, layers, structure_z
        return
    planes: dict[tuple[float, StackKey], list[tuple[Any, Stack]]] = {}
    for region in regions:
        layers = tuple(room.ceiling_lining or region.deck.ceiling_below)
        if not layers:
            continue
        planes.setdefault((round(region.structure_z_m, 6), _stack_key(layers)),
                          []).append((region, layers))
    if len(planes) == 1:
        (region, layers), = [group[0] for group in planes.values()]
        yield (f"{room.uid}-ceiling", f"CEIL-{room.tag}", clear_face, layers,
               region.structure_z_m)
        return
    for group in planes.values():
        region, layers = group[0]
        # Named for the deck, not numbered: "the piece under SL-M-DECK" is what a reader
        # wants off a step, and a deck belongs to exactly one plane so it stays unique.
        # Where a plane is more than one disjoint patch (an L around a chase), the ordinal
        # separates them and nothing else does.
        stem = f"ceiling-{region.deck.tag}"
        for index, part in enumerate(_merged(group), start=1):
            nth = "" if index == 1 else f"-{index}"
            yield (f"{room.uid}-{stem}{nth}", f"CEIL-{room.tag}-{region.deck.tag}{nth}",
                   part, layers, region.structure_z_m)


def _stack_key(layers: Stack) -> StackKey:
    """A comparable identity for a layer stack — two decks lining alike are one plane."""
    return tuple((layer.name, layer.material_ref, layer.thickness.meters,
                  str(layer.function)) for layer in layers)


def _merged(group: list[tuple[Any, Stack]]) -> list[Ring]:
    """One ring per connected patch of a plane's regions, dissolving any shared edge."""
    merged = union_all([region.face for region, _ in group])
    return [_ring(part) for part in polygon_parts(merged)]


def _ring(polygon: Polygon) -> Ring:
    """A region polygon's exterior as an open ring, the shape ``Ring`` carries."""
    coords = list(polygon.exterior.coords)
    if len(coords) > 1 and coords[0] == coords[-1]:
        coords = coords[:-1]
    return [(float(x), float(y)) for x, y in coords]


def _no_deck_stack(plan: PlanModel, storey_tag: str, room: Any) -> tuple[Stack, float | None]:
    """The stack for a room with nothing decked over it — its own roof's lining, or none.

    The elevation is None only for a room following a sloped roof; a room ceilinged flat on
    a truss bottom chord still resolves the storey's own ceiling-height convention, which is
    the plane :mod:`typehaus.resolve.envelope` hangs a `Soffit` from.
    """
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
