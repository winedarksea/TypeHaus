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
from dataclasses import dataclass
from typing import Any

from shapely.geometry import GeometryCollection, MultiPolygon, Polygon

from typehaus.model.assembly import Layer
from typehaus.model.enums import LayerFunction
from typehaus.model.floors import FloorSystem, Slab
from typehaus.model.plan import PlanModel
from typehaus.model.refs import FollowRoof
from typehaus.model.spatial import Roof
from typehaus.resolve.construction_geometry import _EPS
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.overlay import difference, intersection, union_all


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
    over PART of the room, and the two kinds of caller take that differently: a clear-height
    check wants the MINIMUM underside (the worst head in the room), while anything drawing
    or billing the ceiling itself wants the pieces apportioned — :func:`ceiling_regions`.
    Neither may pick one and call it the room's.
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


def deck_structure_underside_m(storey: Any, deck: Any) -> float | None:
    """Absolute elevation of the naked structure underside — no ceiling hung on it yet.

    A FloorSystem's storey datum is the TOP of its structure, so this is the joist soffit.
    A Slab hangs its own thickness below the datum (or below ``top_elevation`` where it
    authors one), so this is the slab's own bottom face. Shared by
    :func:`ceiling_underside_m` (the deck's own authored ceiling) and
    :mod:`typehaus.resolve.ceilings` (which may hang a different, room-authored stack off
    the same structure), so both derive the same structural fact and only the layers below
    it can differ.
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
    return storey.elevation.meters - section.depth_m


def ceiling_underside_m(storey: Any, deck: Any) -> float | None:
    """Absolute elevation of the underside of ``deck``'s OWN ceiling, or None if derivable.

    A FloorSystem's storey datum is the TOP of its structure, so the room below sees the
    joist soffit less whatever membrane hangs on it. A Slab hangs its own thickness below
    the datum (or below ``top_elevation`` where it authors one).

    The resilient-channel standoff is deliberately NOT subtracted: a channel is a
    ``ConstructionRule`` return, not an element, and a check that reads it here would be
    grading a quantity rather than the model. It is 1/2", well inside the margin any room
    this applies to carries.
    """
    underside = deck_structure_underside_m(storey, deck)
    if underside is None:
        return None
    return underside - sum(layer.thickness.meters for layer in deck.ceiling_below)


def room_roof_over(plan: PlanModel, storey_tag: str, room: Any) -> Roof | None:
    """The ``Roof`` directly overhead a room with no deck above it, or None.

    An authored ``Room.ceiling=FollowRoof(roof_ref=...)`` names it outright — the room's
    ceiling follows that roof's slope, which is the whole reason ``FollowRoof`` exists.
    Absent that, the room's own storey may carry a ``Roof`` directly (a single-storey
    volume like the garage, ceilinged flat on the truss bottom chord): the first ``Roof``
    authored on the room's storey is taken, since a storey with a room and no deck above it
    has never authored more than one.
    """
    ceiling = getattr(room, "ceiling", None)
    if isinstance(ceiling, FollowRoof):
        return next((element for element in plan.storey_elements(storey_tag)
                     if isinstance(element, Roof) and element.tag == ceiling.roof_ref), None)
    return next((element for element in plan.storey_elements(storey_tag)
                 if isinstance(element, Roof)), None)


#: Below this, an overlap between a room face and a deck outline is a noding sliver rather
#: than a piece of ceiling. 1e-3 m2 is 1.6 sq in — smaller than any real ceiling region and
#: several orders above the micron grid :mod:`typehaus.resolve.overlay` snaps to.
_MIN_REGION_M2 = 1e-3


@dataclass(frozen=True)
class CeilingRegion:
    """One piece of a room's ceiling — the part of it under a single deck.

    A room under one deck has exactly one region, carrying the room's whole clear face.
    A room that straddles two decks has one per deck, because the two hang at *different
    elevations* and are two planes, not one: catlin's `RM-B-GYM` sits 234 SF under
    `FS-M-EAST`'s joist soffit at -11 7/8" and 90 SF under `SL-M-DECK`'s EPS soffit at
    -13 7/16", the 1 9/16" step one flat bearing seat costs (`params/main_deck.py`).
    Averaging them, or taking the lower as the room's one ceiling, draws 234 SF of gypsum
    an inch and a half below the joists it is screwed to.
    """

    storey: Any
    deck: Any
    face: Polygon
    structure_z_m: float
    #: True where a deck opening was cut out of this region — the face below is open to the
    #: storey above and there is no ceiling to hang there. Callers that would otherwise
    #: substitute the room's whole clear face (:mod:`typehaus.resolve.ceilings`) have to
    #: use ``face`` instead once this is set, or they draw gypsum across a stair shaft.
    voided: bool = False


def polygon_parts(geometry: Any) -> list[Polygon]:
    """``geometry`` as a list of real polygons — an overlay result may be neither.

    A ``GeometryCollection`` is unwrapped rather than discarded: cutting a face along a
    line that grazes a hole's edge returns the polygons *and* the degenerate edge itself,
    and dropping the whole collection loses a real piece of ceiling with it.
    """
    if isinstance(geometry, Polygon):
        return [geometry] if geometry.area > _MIN_REGION_M2 else []
    if isinstance(geometry, MultiPolygon):
        return [part for part in geometry.geoms if part.area > _MIN_REGION_M2]
    if isinstance(geometry, GeometryCollection):
        return [part for member in geometry.geoms for part in polygon_parts(member)]
    return []


def deck_void_face(plan: PlanModel, storey_tag: str, deck: Any) -> Polygon | None:
    """The union of the ``FloorOpening`` faces this deck carries, or None if it carries none.

    A hole in the deck is a hole in the ceiling hung under it. The take-off has always
    known this — :mod:`typehaus.takeoff.framing` bills ``gross - openings`` — but the
    geometry did not, so a room under a stair well resolved a gypsum plane straight across
    the shaft, in the 3D model and in every section cut through it.
    """
    faces = []
    for tag in getattr(deck, "openings", ()):
        opening = plan.by_tag(tag)
        outline = getattr(opening, "outline", ())
        if len(outline) < 3:
            continue
        faces.append(Polygon([point.xy_m for point in outline]))
    return union_all(faces) if faces else None


def ceiling_regions(plan: PlanModel, room_storey_tag: str,
                    face: Polygon) -> list[CeilingRegion]:
    """``face``, cut into one region per deck overhead, each with its structure elevation.

    The single-deck case returns the WHOLE face rather than its intersection with the
    deck's outline: a deck is authored to its own bearing lines and a room's clear face is
    inset from its wall axes, so the two agree to within a fraction of an inch that a clip
    would turn into a missing strip of ceiling. Only where two decks compete for one room
    does the outline become the thing that apportions them.

    A deck that authors no outline (catlin's ``FS-ATTIC``) takes whatever is left of the
    face after the outlined decks have taken their share — it is the storey's blanket deck,
    so "everything the others do not cover" is precisely what it covers.
    """
    usable = [(storey, deck, z)
              for storey, deck in ceiling_decks_over(plan, room_storey_tag, face)
              if (z := deck_structure_underside_m(storey, deck)) is not None]
    if not usable:
        return []
    if len(usable) == 1:
        storey, deck, z = usable[0]
        return _cut_voids(plan, storey, deck, z, [face])
    regions: list[CeilingRegion] = []
    taken: list[Polygon] = []
    for storey, deck, z in usable:
        if not getattr(deck, "outline", ()):
            continue
        outline = Polygon([point.xy_m for point in deck.outline])
        parts = polygon_parts(intersection(face, outline))
        regions.extend(_cut_voids(plan, storey, deck, z, parts))
        taken.extend(parts)
    for storey, deck, z in usable:
        if getattr(deck, "outline", ()):
            continue
        rest = difference(face, union_all(taken)) if taken else face
        parts = polygon_parts(rest)
        regions.extend(_cut_voids(plan, storey, deck, z, parts))
        taken.extend(parts)
    return regions


def _cut_voids(plan: PlanModel, storey: Any, deck: Any, z: float,
               parts: Sequence[Polygon]) -> list[CeilingRegion]:
    """``parts`` as regions, less whatever ``deck``'s openings take out of them.

    The share the deck's outline apportions is taken FIRST and the voids come out of that
    share, so a room straddling two decks loses the hole only from the deck that has it.
    """
    voids = deck_void_face(plan, storey.tag, deck)
    if voids is None:
        return [CeilingRegion(storey, deck, part, z) for part in parts]
    out: list[CeilingRegion] = []
    for part in parts:
        if not voids.intersects(part) or intersection(part, voids).area <= _MIN_REGION_M2:
            out.append(CeilingRegion(storey, deck, part, z))
            continue
        for piece in polygon_parts(difference(part, voids)):
            for simple in split_holes(piece):
                out.append(CeilingRegion(storey, deck, simple, z, voided=True))
    return out


def split_holes(part: Polygon) -> list[Polygon]:
    """``part`` as one or more polygons with no interior rings.

    A ``Ring`` — the shape every consumer of a resolved outline carries — is a single
    closed loop with no holes, so a ceiling with a stair well punched through its middle
    cannot be expressed as one. Dropping the interior ring is not an option: that is
    exactly the bug this whole subtraction exists to fix, and it fails silently.

    So the donut is sliced into simple pieces along the vertical lines through each hole's
    x-bounds. Cutting at *every* hole bound guarantees each band's x-interval either
    contains a hole's whole width — in which case the hole severs the band into disjoint
    pieces and no interior survives — or misses it entirely. Openings are rectangular and
    axis-aligned, so the seam this leaves runs along the well's own edge, which is where a
    reader would draw it anyway.
    """
    if not part.interiors:
        return [part]
    minx, miny, maxx, maxy = part.bounds
    cuts = sorted({minx, maxx} | {value for interior in part.interiors
                                  for value in (interior.bounds[0], interior.bounds[2])
                                  if minx < value < maxx})
    if len(cuts) < 3:
        return [part]  # the hole spans the full width — nothing to cut against
    out: list[Polygon] = []
    for lo, hi in zip(cuts, cuts[1:], strict=False):
        band = Polygon([(lo, miny), (hi, miny), (hi, maxy), (lo, maxy)])
        for piece in polygon_parts(intersection(part, band)):
            out.extend(split_holes(piece) if piece.interiors else [piece])
    return out


def finish_layer(layers: tuple[Layer, ...]) -> Layer | None:
    """The FINISH-function layer of a layer tuple, room side, or None if it has none."""
    return next((layer for layer in layers if layer.function == LayerFunction.FINISH), None)
