"""Spatial & annotation elements: Room, Stair, Roof, GridAxis, Annotation, Fixture,
Furniture (→ 10, → 11)."""

from __future__ import annotations

from typehaus.model.assembly import Layer
from typehaus.model.base import Element
from typehaus.model.enums import Occupancy, RoofForm
from typehaus.model.floors import FinishZone
from typehaus.model.refs import FollowRoof
from typehaus.model.registry import register_constructor, register_element
from typehaus.quantities import Length, Pitch, Point2D


class WallLiningException(Element):
    """A per-wall override of a Room's wall lining (the sauna asymmetric case, #34)."""

    tag: str = "lining-exc"
    wall_ref: str
    lining: tuple[Layer, ...]


@register_element
class Room(Element):
    """Derived from the wall graph, then claimed by a seed point (→ 11 §Room)."""

    seed: Point2D
    occupancy: Occupancy
    conditioned: bool = True
    ceiling: Length | FollowRoof | None = None
    floor_finish: str | None = None
    finish_zones: tuple[FinishZone, ...] = ()
    wall_lining: tuple[Layer, ...] = ()  # overrides assembly default_lining on all faces
    wall_lining_exceptions: tuple[WallLiningException, ...] = ()


@register_element
class Stair(Element):
    """Rise derived from storey elevations; solves treads/risers vs R311.7 (→ 10)."""

    floor_opening: str  # FloorOpening tag in the storey above
    from_storey: str
    to_storey: str
    width: Length
    run_direction: str = "x"
    start: Point2D | None = None


@register_element
class Roof(Element):
    """Constrained vocabulary — gable/shed first; zero overhang first-class (#29)."""

    form: RoofForm
    pitch: Pitch
    bearing_refs: tuple[str, ...]
    assembly: str
    overhang: Length | None = None
    edge_overhangs: tuple[tuple[str, Length], ...] = ()  # per-edge overrides
    ridge_direction: str = "x"


@register_element
class GridAxis(Element):
    """A structural grid line (drawn once, placed per Slice, → 11b)."""

    position: Point2D
    direction: str  # "x" | "y"
    label: str


@register_element
class Annotation(Element):
    """A shared annotation anchored once, placed per Slice (→ 11b §Slices)."""

    position: Point2D
    text: str
    leader_to: Point2D | None = None


@register_element
class Fixture(Element):
    """A placed plumbing/equipment fixture (M3)."""

    type_ref: str
    room: str
    position: Point2D
    rotation: object | None = None  # Angle | None


@register_element
class Furniture(Element):
    """A placed furniture instance driving dashboards/overlays (M3, #49)."""

    type_ref: str
    position: Point2D
    rotation: object | None = None  # Angle | None


for _name, _obj in (
    ("Room", Room),
    ("Stair", Stair),
    ("Roof", Roof),
    ("GridAxis", GridAxis),
    ("Annotation", Annotation),
    ("Fixture", Fixture),
    ("Furniture", Furniture),
    ("WallLiningException", WallLiningException),
):
    register_constructor(_name, _obj)
