"""Two-tier floor model + soffits + radiant heat (#21, #40, #39, → 11 §Floors)."""

from __future__ import annotations

from typing import Literal

from typehaus.model.assembly import Layer
from typehaus.model.base import Element, HausModel
from typehaus.model.enums import FloorOpeningPurpose, RadiantSystem
from typehaus.model.refs import Embed
from typehaus.model.registry import register_constructor, register_element
from typehaus.quantities import Length, Point2D


class JoistSpec(HausModel):
    """Framing spec for a FloorSystem deck. Bearing refs are wall/beam tags."""

    member: str = "11.875 I-joist"
    spacing: Length | None = None  # o.c.; defaults to 16" at the solver
    direction: str = "x"  # "x" | "y" — joist span direction in the plan frame
    bearing_refs: tuple[str, ...] = ()
    # Overhang past the two outermost bearing lines (a balcony/porch deck cantilevers its
    # joist tips beyond the beam so the decking covers them). None = flush ends.
    cantilever: Length | None = None
    # Per-end overrides, for a deck whose two ends are not alike: the porch runs from a
    # concrete sill (flush) out over its back-beam line to the house gap (a 17" overhang),
    # and one symmetric scalar cannot say that — it either overshot the concrete wall to
    # the south or fell short of the deck edge to the north. Each defaults to ``cantilever``.
    # "start"/"end" are the low/high ends along the joist span direction.
    cantilever_start: Length | None = None
    cantilever_end: Length | None = None


class JoistReinforcement(HausModel):
    """Extra joist plies sistered under a concentrated load, plus solid blocking.

    A post landing mid-span — worse, out on a cantilever — is carried by one 1 1/2" joist
    unless something is added under it. Authoring the reinforcement here rather than as
    loose members keeps the *intent* ("this point load is answered") in the plan: the
    resolver derives the geometry, the take-off bills it, and
    ``structural.cantilever_point_load`` reads it as the mitigation it is.

    ``at`` is a plan point, not a joist index — the joist line nearest it is the one that
    gets the plies, so a post that moves 2" does not silently reinforce its neighbour.
    ``member`` defaults to the deck's own joist member (a sister is the same stock).
    """

    at: Point2D
    plies: int = 3  # total plies at the line, the authored joist included
    member: str | None = None  # None = the deck's own JoistSpec.member
    blocking: bool = True  # solid blocking out to the joist line on each side
    source: str | None = None


class DeckLayer(HausModel):
    material_ref: str
    thickness: Length


@register_element
class FloorOpening(Element):
    """First-class opening in a FloorSystem; referenced by tag from a Stair (#21)."""

    outline: tuple[Point2D, ...]
    purpose: FloorOpeningPurpose = FloorOpeningPurpose.STAIR
    # Authored support intent for opening edges.  The framing resolver never assumes
    # that a nearby partition can receive cut joists.
    bearing_refs: tuple[str, ...] = ()


@register_element
class FloorSystem(Element):
    """Per-storey structural deck: joists, subfloor, ceiling-below, and openings (#21).

    Its total depth feeds the storey elevation delta — one source of truth for
    floor-to-floor rise (→ 11 §Floors)."""

    joists: JoistSpec
    # Sistered plies + blocking under concentrated loads (a post bearing on the deck).
    # Empty is the ordinary case: a deck with no point load on it needs none.
    reinforcements: tuple[JoistReinforcement, ...] = ()
    subfloor: DeckLayer | None = None
    # The ceiling hung under this deck's joists, room side first (furring, membrane,
    # finish — same "interior -> exterior" convention as ``Assembly.default_lining``).
    # Empty means no ceiling is authored below this deck at all (open-to-structure).
    ceiling_below: tuple[Layer, ...] = ()
    openings: tuple[str, ...] = ()  # FloorOpening tags
    # What this deck *is*, structurally. "floor" is an interior floor: the 40 psf live +
    # dead residential floor tables in ``checks/structural/checks.py`` grade it. "deck" is an
    # exterior walking surface on posts and beams, which IRC R507 / AWC DCA6 govern instead —
    # different span tables, plus post, footing and guard rules that an interior floor has no
    # equivalent of. Nothing derives this from geometry: a freestanding deck and an interior
    # floor both resolve to joists on bearings, so the distinction has to be authored.
    service: Literal["floor", "deck"] = "floor"
    # Optional explicit footprint. When given, the joist field is scoped to this outline's
    # perpendicular extent instead of the storey's whole wall bbox — needed for a deck that
    # frames a freestanding sub-structure sharing a storey with the main building.
    outline: tuple[Point2D, ...] = ()
    iic: int | None = None  # empirical lookup (#50)
    source: str | None = None


class SlabThermalBreak(HausModel):
    """Vertical rigid-insulation break between a slab edge and whatever abuts it
    (stem wall, foundation wall) — the thermal cut that stops the slab conducting
    straight into the frost-depth concrete. Minimal by design: a material, its
    horizontal ``thickness`` in the joint, and how far ``depth`` runs down the slab
    edge (None = the slab's full thickness)."""

    material_ref: str
    thickness: Length  # horizontal insulation thickness in the edge joint
    depth: Length | None = None  # vertical extent down the slab edge; None = full slab


@register_element
class Slab(Element):
    """Slab-on-grade or structural concrete deck (instead of a FloorSystem).

    Like a FloorSystem it may own FloorOpenings (the catlin main deck is a 9"
    slab with a stair hole, → 30 WP3.1)."""

    outline: tuple[Point2D, ...]
    thickness: Length
    assembly: str | None = None
    openings: tuple[str, ...] = ()  # FloorOpening tags
    # Which side of the storey datum (= top of floor structure) this slab occupies.
    # "structure" — the slab *is* the floor structure, so it hangs its thickness below the
    # datum. This is the default and covers every slab-on-grade and structural concrete deck.
    # "walking_surface" — decking laid over a FloorSystem whose joists already top out at the
    # datum, so it rides on top instead, exactly like that FloorSystem's own subfloor sheet.
    # Authoring this explicitly rather than inferring it from a shared footprint keeps two
    # coincidentally-congruent elements (a patio slab under a deck, say) from silently
    # swapping conventions.
    datum: Literal["structure", "walking_surface"] = "structure"
    # Absolute top-of-slab elevation, in the project frame, when this slab does not sit on
    # its storey's datum at all — a garage slab left at grade while the house floor above it
    # stays at 0'-0", say. Mirrors ``FoundationWall.top_elevation``. When set it wins over
    # the storey datum outright and ``datum`` no longer applies: the slab hangs its
    # thickness below this elevation. Leave it None (the norm) and the storey datum plus
    # ``datum`` decide, exactly as before. Authoring it is what lets a slab be filed on the
    # storey it belongs to rather than on whichever storey happens to sit at its elevation.
    top_elevation: Length | None = None
    # Slab-on-grade only: rigid-insulation edge break against the abutting stem/foundation
    # wall. None = slab edge pours directly against the concrete it meets.
    perimeter_thermal_break: SlabThermalBreak | None = None
    # This slab's own top face is the finished floor wherever a room sits on it — a
    # polished or sealed cap, not a deck waiting for a covering. Where set, `resolve/rooms.py`
    # intersects this outline with each room's clear face and emits the result as a
    # ResolvedFinishZone, so the room's own `floor_finish` stays the FIELD finish and the
    # concrete bills, draws and prices as its own area. Leave it None (the norm) and a slab
    # is structure only. Not on FloorSystem: a joisted deck's top is a subfloor sheet, and
    # what goes over it is the room's decision, never the deck's.
    floor_finish: str | None = None
    # The ceiling hung under this slab, room side first, meaningful only where a room sits
    # under it (``datum == "structure"``): a slab-on-grade with no occupied space below
    # authors none. Same convention as ``FloorSystem.ceiling_below``.
    ceiling_below: tuple[Layer, ...] = ()


@register_element
class Soffit(Element):
    """Storey-level dropped ceiling; polygon may span rooms (#40)."""

    outline: tuple[Point2D, ...]
    drop: Length | None = None
    underside_elevation: Length | None = None
    framing: object | None = None  # FramingSpec | None (avoids import cycle)


@register_element
class FloorHeat(Element):
    """Zone-level radiant heat on a Slab/FloorSystem (#39). No routing solver."""

    zone: tuple[Point2D, ...] | None = None
    room_ref: str | None = None
    system: RadiantSystem = RadiantSystem.HYDRONIC
    spacing: Length | None = None
    embed: Embed | None = None
    stat: Point2D | None = None
    sensors: tuple[Point2D, ...] = ()
    # Connected electric input, when the mat is sized. Left None the output is unknown and the
    # mat contributes nothing to its zone's heating capacity — never inferred from area, since
    # a guessed W/ft2 would move a sizing verdict on an assumption the author never made.
    watts: float | None = None


class FinishZone(HausModel):
    """An in-room floor-finish override zone (tile inlay, hearth pad) (#21)."""

    outline: tuple[Point2D, ...]
    material_ref: str


for _name, _obj in (
    ("JoistSpec", JoistSpec),
    ("JoistReinforcement", JoistReinforcement),
    ("DeckLayer", DeckLayer),
    ("FloorOpening", FloorOpening),
    ("FloorSystem", FloorSystem),
    ("Slab", Slab),
    ("SlabThermalBreak", SlabThermalBreak),
    ("Soffit", Soffit),
    ("FloorHeat", FloorHeat),
    ("FinishZone", FinishZone),
):
    register_constructor(_name, _obj)
