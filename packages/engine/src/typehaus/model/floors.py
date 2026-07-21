"""Two-tier floor model + soffits + radiant heat (#21, #40, #39, → 11 §Floors)."""

from __future__ import annotations

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
    subfloor: DeckLayer | None = None
    ceiling_below: DeckLayer | None = None
    openings: tuple[str, ...] = ()  # FloorOpening tags
    iic: int | None = None  # empirical lookup (#50)
    source: str | None = None


@register_element
class Slab(Element):
    """Slab-on-grade or structural concrete deck (instead of a FloorSystem).

    Like a FloorSystem it may own FloorOpenings (the catlin main deck is a 9"
    slab with a stair hole, → 30 WP3.1)."""

    outline: tuple[Point2D, ...]
    thickness: Length
    assembly: str | None = None
    openings: tuple[str, ...] = ()  # FloorOpening tags


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


class FinishZone(HausModel):
    """An in-room floor-finish override zone (tile inlay, hearth pad) (#21)."""

    outline: tuple[Point2D, ...]
    material_ref: str


for _name, _obj in (
    ("JoistSpec", JoistSpec),
    ("DeckLayer", DeckLayer),
    ("FloorOpening", FloorOpening),
    ("FloorSystem", FloorSystem),
    ("Slab", Slab),
    ("Soffit", Soffit),
    ("FloorHeat", FloorHeat),
    ("FinishZone", FinishZone),
):
    register_constructor(_name, _obj)
