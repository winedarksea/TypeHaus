"""The resilient-channel field return — the one finder that names no junction.

Every other construction finder closes a *boundary* between two assemblies. This one bills
a field of material a single resolved element leaves for the trades: hat channel across a
deck's joist soffit, optionally clipped to one room's clear face, net of the deck's own
openings. That difference is why it sits alone — it derives a room polygon pre-framing
(sharing the rooms stage's own helpers so the two cannot drift) and emits no
``condition_key`` for an overlay to join on.
"""

from __future__ import annotations

from collections.abc import Iterator

from shapely.geometry import Point, Polygon

from typehaus.model.assembly import ConstructionRule
from typehaus.model.floors import FloorOpening, FloorSystem
from typehaus.model.plan import PlanModel
from typehaus.resolve.construction_geometry import _EPS
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import ResolvedConstructionReturn, ResolvedModel

# Private, deliberately: a scoped rule has to measure the *same* room polygon the rooms
# stage will publish later (see ``_room_clear_face``), and sharing the derivation is the
# only way to guarantee that. Precedent elsewhere in the tree: ``checks.building_science.
# energy_load`` imports the WWR check's facade helpers (``checks.building_science.wwr``)
# rather than re-deriving them.
from typehaus.resolve.rooms import _lining_inset, _storey_faces

# --- ceiling channel ----------------------------------------------------------
# Resilient channel: light-gauge hat channel screwed across the joist soffit with the
# ceiling membrane hung on *it* instead of on the framing. The small stand-off it holds is
# the whole product — it is what breaks the structure-borne path from the deck into the
# room below — and it is also this return's z extent.
_RC_STANDOFF_M = 0.0127  # 1/2", the depth of a standard RC-1 hat
# 16" o.c., the spacing the joist solver itself falls back to when a deck authors none.
_RC_DEFAULT_SPACING_M = 0.4064
# The channel is not a layer of any authored assembly (that is exactly why it needs a
# ConstructionRule), so it names its own stock rather than borrowing a wall's material.
_RC_MATERIAL = "galv-steel"


def _room_clear_face(plan: PlanModel, storey_tag: str, room_tag: str) -> Polygon | None:
    """A room's clear-face polygon, derived the way the rooms stage derives it.

    Re-derived rather than read off ``model.rooms``: this pass runs pre-framing, several
    stages ahead of ``resolve_rooms``, so ``model.rooms`` is still empty here. Sharing
    ``_storey_faces`` / ``_lining_inset`` with that stage is what keeps the two polygons
    identical — a scoped rule has to bill the same room the plan draws, not an
    approximation of it.
    """
    room = next((element for element in plan.storey_elements(storey_tag)
                 if element.element_kind == "Room" and element.tag == room_tag), None)
    if room is None:
        return None
    seed = Point(room.seed.xy_m)
    face = next((f for f in _storey_faces(plan, storey_tag) if f.contains(seed)), None)
    if face is None:
        return None
    inset = _lining_inset(plan, room)
    clear = face.buffer(-inset) if inset > 0 else face
    return face if clear.is_empty or clear.geom_type != "Polygon" else clear


def _room_storey(plan: PlanModel, room_tag: str):
    """The storey that authors ``room_tag``, or None."""
    return next((storey for storey in plan.storeys
                 if any(element.element_kind == "Room" and element.tag == room_tag
                        for element in plan.storey_elements(storey.tag))), None)


def _deck_holes(plan: PlanModel, storey_tag: str, system: FloorSystem) -> list[Polygon]:
    """The FloorOpenings cut through ``system`` — no ceiling hangs under a stair well."""
    return [Polygon([point.xy_m for point in opening.outline])
            for opening in plan.storey_elements(storey_tag)
            if isinstance(opening, FloorOpening) and opening.tag in system.openings]


def _find_ceiling_channel(model: ResolvedModel, rule: ConstructionRule) \
        -> Iterator[ResolvedConstructionReturn]:
    """Resilient channel carrying a deck's ceiling membrane, billed by the lineal foot.

    The runs cross the joists — a channel laid *with* them would screw to one joist and
    decouple nothing — stepping along the joist line at ``rule.dimension`` o.c. That
    orientation drops out of the arithmetic, which is why ``joists.direction`` is not read
    here: parallel runs at ``spacing`` over a field of area A are A/spacing of channel
    however the field is turned. Same derivation, and same reason, as the wire length
    ``resolve_floor_heat`` gives a radiant zone: what is ordered is lineal feet of a
    serpentine over an area.

    ``scope_ref`` clips the field to one room's clear face. Channel is a room-by-room
    decision (one quiet living room under the second-storey deck), not a property of the
    deck, and without the clip the only way to say so would be a one-off predicate per
    room. An unscoped rule bills the deck's whole authored ``outline`` instead; a deck that
    authors none is skipped, because the extent the sheet take-off uses for it is derived
    from framing members that do not exist yet at this stage.

    Either way the deck's own FloorOpenings are cut out: a stair well has no ceiling.
    """
    plan = model.plan
    spacing = rule.dimension.meters if rule.dimension is not None else _RC_DEFAULT_SPACING_M
    if spacing < _EPS:
        return
    # Membraned decks, lowest first: a channel with no ceiling hung on it is not a thing.
    decks = [(storey, system)
             for storey in sorted(plan.storeys, key=lambda s: s.elevation.meters)
             for system in plan.storey_elements(storey.tag)
             if isinstance(system, FloorSystem) and system.ceiling_below is not None]

    fields: list[tuple[object, FloorSystem, Polygon, tuple[str, ...]]] = []
    if rule.scope_ref is not None:
        room_storey = _room_storey(plan, rule.scope_ref)
        face = (None if room_storey is None
                else _room_clear_face(plan, room_storey.tag, rule.scope_ref))
        if face is None:
            return
        # The ceiling over that room is the LOWEST membraned deck above it, which is not
        # the same thing as "the next storey up": catlin wedges its garage storey between
        # main and second by elevation, and the garage decks nothing over the living room.
        pair = next(((storey, system) for storey, system in decks
                     if storey.elevation.meters > room_storey.elevation.meters), None)
        if pair is not None:
            fields.append((pair[0], pair[1], face, (pair[1].tag, rule.scope_ref)))
    else:
        fields.extend((storey, system, Polygon([p.xy_m for p in system.outline]),
                       (system.tag,))
                      for storey, system in decks if system.outline)

    for storey, system, field, tags in fields:
        for hole in _deck_holes(plan, storey.tag, system):
            field = field.difference(hole)
        # The channel hangs off the joist soffit, one joist depth below the storey datum —
        # the same datum the deck's own PT sill plate is measured from.
        z1 = storey.elevation.meters - cross_section(system.joists.member).depth_m
        pieces = [piece for piece in getattr(field, "geoms", (field,))
                  if piece.geom_type == "Polygon" and piece.area > _EPS]
        for index, piece in enumerate(pieces, start=1):
            yield ResolvedConstructionReturn(
                uid=f"CR-{system.uid}-{rule.scope_ref or system.tag}-rc{index}",
                # Filed under the deck's storey, like the deck's joists and its sill plate:
                # the ceiling is this deck's underside, not a separate element of the room.
                tag=rule.tag, storey=storey.tag, kind=rule.kind,
                applies_to=rule.applies_to, takeoff_category=rule.takeoff_category,
                material_ref=_RC_MATERIAL,
                element_tags=tags,
                # The field's boundary. A deck opening that falls *inside* it (the stair
                # well does) is a hole, and the record has no ring for holes — so the
                # opening comes off the quantity below, not off this outline.
                outline=[(x, y) for x, y in piece.exterior.coords[:-1]],
                z0_m=z1 - _RC_STANDOFF_M, z1_m=z1,
                # A field, not a strip: there is no plan width to report, so the thickness
                # is the channel's own depth — the same span as the z extent above it.
                thickness_m=_RC_STANDOFF_M, length_m=piece.area / spacing,  # net of holes
                lap_m=spacing,  # the authored dimension is a spacing here, not a lap
                thermal_continuity=False,
                returning_layer=system.ceiling_below.material_ref,
                # No junction: a field return under a deck documents no boundary condition,
                # so there is no condition key for an overlay to join on.
                condition_key=None,
            )
