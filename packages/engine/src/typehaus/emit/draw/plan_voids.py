"""Floor openings on the architectural plan: the ring, and what is over the hole.

A hole in a deck and a deck look identical from above. The architectural plan never read
``FloorSystem.openings`` at all — the only sheet that drew a floor opening was the framing
plan, keyed to its header and trimmer marks — so A-104 showed the attic's stair hall as
floor, and ``houses/catlin/plan/views.py`` answered the question with a whole SECTION
(``SL-D-STAIRVOID``) because the plan could not. There was no ``OPEN TO BELOW`` string
anywhere in the repo.

Two entry points, not one, because the ring and the note want opposite sides of the stair:
the **ring must precede** ``emit_stairs`` — it seeds the segment ledger, and the well's own
edge is a flight's arrival nosing — while the **note must follow** it, to dodge ``UP 16 R``.

Source is the authoring ``FloorOpening``, never ``ResolvedFloor.deck_voids``:
``resolve/floors.py`` builds those as axis-aligned BOUNDING BOXES with the opening reference
discarded, and only when the deck carries a subfloor. The authored outline carries the true
ring, the ``purpose`` and the tag.

No ``OPEN TO ABOVE`` on the storey below. An opening is drawn once, on the plan of the deck
it perforates, and it is the deck it is a hole in that has something to say about it.
"""

from __future__ import annotations

from shapely.geometry import Polygon

from typehaus.emit.draw._shared import PLAN_RESERVATION_SCALE
from typehaus.emit.draw._shared import to_in as _in
from typehaus.emit.draw.lineweights import PROFILE
from typehaus.emit.draw.plan_labels import (
    BLOCK_FIT_FRACTION,
    _block_box,
    _block_half_width,
    _fitted_lines,
    _inside_point,
    _place_block,
    block_pitch_m,
)
from typehaus.emit.draw.scene import Polyline, SceneBuilder, Text
from typehaus.emit.draw.typography import TAG_PT
from typehaus.model.enums import FloorOpeningPurpose
from typehaus.resolve.assembly_material import is_flatwork
from typehaus.resolve.model import ResolvedModel

Pt = tuple[float, float]
Segment = tuple[Pt, Pt]
Box = tuple[float, float, float, float]

#: The layer the opening ring draws on. A-FLOR is the floor-construction family in the
#: AIA/NCS layer list and ``-OPEN`` is its opening modifier, exactly as ``S-FRAM-OPEN`` is
#: the structural one. It needs a row in BOTH writers' ``_LAYER_STYLE`` or
#: ``test_writer_layer_coverage`` fails — which is its job: ``A-STAIR`` itself once drew as
#: a generic pen.
VOID_LAYER = "A-FLOR-OPEN"

#: What a reader is told, per purpose. A stair well says which, because "OPEN TO BELOW" over
#: a stair is true and useless — the useful sentence is that the hole is the stairway.
_CAPTIONS = {
    FloorOpeningPurpose.STAIR: "OPEN TO BELOW",
    FloorOpeningPurpose.CHASE: "CHASE — OPEN TO BELOW",
    FloorOpeningPurpose.HATCH: "ACCESS HATCH",
    # A sonotube void in a walk slab: soil below, not a drop.
    FloorOpeningPurpose.PLANTING: "PLANTER",
}
_STAIR_BELOW_CAPTION = "OPEN TO STAIR BELOW"
#: What a hole too narrow for its full caption says instead, rather than spill next door.
_SHORT_CAPTIONS = {FloorOpeningPurpose.CHASE: "CHASE"}


def _openings(model: ResolvedModel, storey: str):
    """Every authored ``FloorOpening`` on ``storey``, once each (→ :func:`_deck_openings`)."""
    for _deck, opening in _deck_openings(model, storey):
        yield opening


def _deck_openings(model: ResolvedModel, storey: str):
    """``(deck, opening)`` for every authored ``FloorOpening`` on ``storey``, once each.

    The authored ``FloorSystem`` / ``Slab`` carries no storey of its own — a deck is filed
    on a storey by the source, and the RESOLVED record is what knows which — so the storey
    comes from ``model.floors`` / ``model.solids`` and the openings from the element behind
    it. A house is free to list one opening on two systems, and the framing plan already
    learned that drawing it twice breaks the DXF round-trip.
    """
    seen: set[str] = set()
    decks = [floor.tag for floor in model.floors if floor.storey == storey]
    # A flatwork slab is not drawn on a floor plan (→ floorplan._emit_slabs); nor are its voids.
    decks += [solid.tag for solid in model.solids
              if solid.category == "slab" and solid.storey == storey
              and not is_flatwork(model.plan, solid)]
    for deck in sorted(set(decks)):
        system = model.plan.by_tag(deck)
        for tag in getattr(system, "openings", ()):
            if tag in seen:
                continue
            opening = model.plan.by_tag(tag)
            if opening is None or len(getattr(opening, "outline", ())) < 3:
                continue
            seen.add(tag)
            yield system, opening


def emit_floor_opening_rings(b: SceneBuilder, model: ResolvedModel,
                             storey: str) -> list[Segment]:
    """Draw each opening's true ring. Returns its edges, for the stair symbol's ledger."""
    segments: list[Segment] = []
    for opening in _openings(model, storey):
        ring = [point.xy_m for point in opening.outline]
        b.add(Polyline(points=tuple(_in(point) for point in ring), closed=True,
                       layer=VOID_LAYER, lineweight=PROFILE, uid=opening.uid,
                       tag=opening.tag))
        segments.extend(zip(ring, [*ring[1:], ring[0]], strict=True))
    return segments


def _stair_below(model: ResolvedModel, storey: str, ring: list[Pt]) -> bool:
    """Is a stair what a reader would see looking down through this hole?

    Footprint intersection in plan, against a stair that ARRIVES either at this deck — its
    own well, where the flight comes up through the hole — or at the storey immediately
    under it, where the flight below is what the hole is over. Both are "a stair below": you
    are standing on this deck looking down at it.

    Nothing is authored for this. ``FO-A-HALL`` sits directly over ST-M2S's head and
    captions itself; ``FO-M-STAIR`` is ST-B2M's own well and captions itself too.
    """
    below = _storey_below(model, storey)
    hole = Polygon(ring)
    return any(stair.to_storey in {storey, below} and len(stair.outline) >= 3
               and hole.intersects(Polygon(stair.outline))
               for stair in model.stairs)


def _storey_below(model: ResolvedModel, storey: str) -> str | None:
    """The storey tag immediately under ``storey``, by elevation, in the same building."""
    here = model.plan.storey(storey)
    if here is None:
        return None
    lower = [s for s in model.plan.storeys
             if s.building == here.building and s.elevation.meters < here.elevation.meters]
    if not lower:
        return None
    return max(lower, key=lambda s: s.elevation.meters).tag


def _caption(model: ResolvedModel, storey: str, opening, scale: float) -> tuple[str, bool]:
    """``(caption, fits)``: the short form when the full one is wider than the hole."""
    caption = _CAPTIONS.get(opening.purpose, "OPEN TO BELOW")
    ring = [point.xy_m for point in opening.outline]
    if opening.purpose is FloorOpeningPurpose.STAIR and _stair_below(model, storey, ring):
        caption = _STAIR_BELOW_CAPTION
    room = (max(p[0] for p in ring) - min(p[0] for p in ring)) * BLOCK_FIT_FRACTION
    if 2.0 * _block_half_width([(caption, TAG_PT)], scale) > room:
        caption = _SHORT_CAPTIONS.get(opening.purpose, caption)
    return caption, 2.0 * _block_half_width([(caption, TAG_PT)], scale) <= room


def _repeats(model: ResolvedModel, storey: str, scale: float):
    """``(deck, caption, [openings])``: repeats too small for their caption grouped.

    A deck with a row of identical pockets is captioned ONCE, ``TYP. OF n``, not once per
    pocket: a caption wider than its 16" void cannot sit inside it, and a dozen of them
    stacked down a walk is the pile-up A-102 printed. A hole that holds its own caption
    keeps it, so the caption stays on the thing it names.
    """
    groups: dict[tuple, tuple] = {}
    for deck, opening in _deck_openings(model, storey):
        caption, fits = _caption(model, storey, opening, scale)
        area = round(Polygon([p.xy_m for p in opening.outline]).area, 2)
        key = (getattr(deck, "tag", None), caption, area, opening.tag if fits else None)
        groups.setdefault(key, (deck, caption, []))[2].append(opening)
    for deck, caption, members in groups.values():
        if len(members) > 1 and len(getattr(deck, "outline", ())) >= 3:
            yield deck, caption, members
        else:
            for opening in members:
                yield None, caption, [opening]


def emit_floor_opening_notes(b: SceneBuilder, model: ResolvedModel, storey: str,
                             avoid: list[Box] = (),
                             scale: float = PLAN_RESERVATION_SCALE) -> list[Box]:
    """Caption every opening on this deck, clear of ``avoid``. Returns the boxes used.

    Placement reuses ``plan_labels``' block machinery verbatim: it already takes an
    arbitrary ``Ring`` rather than a room, and a caption in a 3'-0" band of well that also
    carries a winder fan and ``UP 16 R`` is exactly the collision it was written for.
    Repeated openings share one ``TYP.`` caption placed on their deck, clear of every void.
    """
    boxes: list[Box] = []
    for deck, caption, members in _repeats(model, storey, scale):
        opening = members[0]
        ring = [point.xy_m for point in opening.outline]
        if deck is None:
            lines = _fitted_lines([(caption, TAG_PT)], ring, scale)
            anchor, lines = _place_block(_inside_point(ring), lines, ring,
                                         avoid=[*avoid, *boxes], scale=scale)
            uid = opening.uid
        else:
            ring = [point.xy_m for point in deck.outline]
            voids = [Polygon([p.xy_m for p in o.outline]).bounds for o in members]
            lines = _fitted_lines([(caption, TAG_PT), (f"TYP. OF {len(members)}", TAG_PT)],
                                  ring, scale)
            start = (sum(v[0] + v[2] for v in voids) / (2 * len(voids)),
                     sum(v[1] + v[3] for v in voids) / (2 * len(voids)))
            anchor, lines = _place_block(start, lines, ring, avoid=[*avoid, *boxes, *voids],
                                         scale=scale)
            uid = deck.uid
        for index, (content, height_pt) in enumerate(lines):
            b.add(Text(anchor=_in((anchor[0], anchor[1] - index * block_pitch_m(scale))),
                       content=content, height_pt=height_pt, layer="A-ANNO-TEXT",
                       align="center", uid=uid))
        boxes.append(_block_box(anchor, lines, scale))
    return boxes
