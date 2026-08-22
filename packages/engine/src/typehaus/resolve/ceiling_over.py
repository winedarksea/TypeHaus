"""What forms the ceiling over a room, and how low its underside hangs.

Two very different consumers ask the same question and used to answer it separately:

* ``resolve/construction_ceiling.py`` bills resilient channel across the joist soffit of
  "the deck above this room", and derived that privately;
* ``checks/code/mn_residential/rules.py`` grades R305.1 clear height, and did not derive it
  at all — it read ``Storey.default_ceiling_height``, which is an authored number nothing
  reconciles against the structure. Catlin's basement authors 9'-0" and the decks over it
  actually leave 8'-3 1/2".

Deriving it twice is how the drawing and the code check come to disagree about the same
ceiling, so the selection lives here and both call it.

Nothing in this module reads framing: it works off authored outlines, storey elevations and
member profiles, so it is safe both pre-framing (where the channel finder runs) and
post-resolve (where the checks run).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from shapely.geometry import Polygon

from typehaus.model.floors import FloorSystem, Slab
from typehaus.model.plan import PlanModel
from typehaus.resolve.construction_geometry import _EPS
from typehaus.resolve.framing.profiles import cross_section


def decks_covering(face: Polygon,
                   candidates: Sequence[tuple[Any, Any]]) -> list[tuple[Any, Any]]:
    """Those of ``candidates`` — ``(storey, deck)`` pairs — that actually roof ``face``.

    AREA, not ``intersects()``: two split-deck halves share a boundary edge, and a boundary
    touch alone satisfies ``intersects()`` for both, so a room on one side of the split
    would read as sitting under both.

    A candidate with NO authored outline cannot be tested and is kept. That is right where
    it is the storey's only deck — catlin's ``FS-ATTIC`` authors none because it spans the
    whole attic footprint — and it is why a single candidate comes back unfiltered rather
    than through a test it would fail for lack of data.
    """
    if len(candidates) <= 1:
        return list(candidates)
    return [(storey, deck) for storey, deck in candidates
            if not getattr(deck, "outline", ())
            or Polygon([point.xy_m for point in deck.outline]).intersection(face).area > _EPS]


def _is_ceiling_deck(element: Any) -> bool:
    """Could this element be somebody's ceiling?

    A ``walking_surface`` Slab is explicitly not: it rides on TOP of a floor system's
    joists, so its underside is that deck's top, not a room's head. (All three of catlin's
    were converted to floor-system subfloors on 2026-08-22 and none is left, but the rule
    is the model's, not the house's.)
    """
    if isinstance(element, FloorSystem):
        return True
    return isinstance(element, Slab) and element.datum != "walking_surface"


def ceiling_decks_over(plan: PlanModel, room_storey_tag: str,
                       face: Polygon) -> list[tuple[Any, Any]]:
    """The ``(storey, deck)`` pairs whose underside is the ceiling over ``face``.

    Storeys are searched upward from the room's own and the FIRST one that covers the room
    wins. Elevation order alone is not enough: catlin wedges its garage storey between main
    and second by elevation and the garage decks nothing over the basement, so a storey that
    is merely higher has to be able to come back empty and let the search continue.

    More than one pair comes back where the room straddles a split deck (the second floor's
    truss/I-joist halves) or sits under two different structures — a concrete deck band and
    a joisted deck, which is exactly catlin's basement. Every one of them is a real ceiling
    over part of the room, which is why the caller takes the MINIMUM underside rather than
    picking one.
    """
    room_storey = next((storey for storey in plan.storeys
                        if storey.tag == room_storey_tag), None)
    if room_storey is None:
        return []
    above = [storey for storey in sorted(plan.storeys, key=lambda s: s.elevation.meters)
             if storey.elevation.meters > room_storey.elevation.meters]
    for index, storey in enumerate(above):
        candidates = [(storey, element) for element in plan.storey_elements(storey.tag)
                      if _is_ceiling_deck(element)]
        if not candidates:
            continue
        if index == 0:
            covering = decks_covering(face, candidates)
        else:
            # Past the storey directly overhead, an UNTESTABLE candidate is not evidence.
            # ``decks_covering``'s "keep a deck that authors no outline" rule is safe one
            # storey up, where the deck is the thing over your head by construction; four
            # storeys up it is how the garage came to report its ceiling as the attic floor
            # 20 feet above it, having stepped past a main and a second floor that plainly
            # do not cover it. Real overlap, or nothing.
            outlined = [(s, deck) for s, deck in candidates
                        if getattr(deck, "outline", ())]
            covering = [(s, deck) for s, deck in outlined
                        if Polygon([point.xy_m for point in deck.outline])
                        .intersection(face).area > _EPS]
        if covering:
            return covering
    return []


def ceiling_underside_m(storey: Any, deck: Any) -> float | None:
    """Absolute elevation of the underside of ``deck``, or None where it cannot be derived.

    A FloorSystem's storey datum is the TOP of its structure, so the room below sees the
    joist soffit less whatever membrane hangs on it. A Slab hangs its own thickness below
    the datum (or below ``top_elevation`` where it authors one).

    The resilient-channel standoff is deliberately NOT subtracted: a channel is a
    ``ConstructionRule`` return, not an element, and a check that reads it here would be
    grading a quantity rather than the model. It is 1/2", well inside the margin any room
    this applies to carries.
    """
    if isinstance(deck, Slab):
        top: float = (deck.top_elevation.meters if deck.top_elevation is not None
                      else storey.elevation.meters)
        return top - deck.thickness.meters
    if not isinstance(deck, FloorSystem):
        return None
    section = cross_section(deck.joists.member)
    if section is None:
        return None
    underside: float = storey.elevation.meters - section.depth_m
    if deck.ceiling_below is not None:
        underside -= deck.ceiling_below.thickness.meters
    return underside
