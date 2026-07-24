"""Spatial & annotation elements: Room, Stair, Roof, GridAxis, Annotation, Fixture,
Furniture (→ 10, → 11)."""

from __future__ import annotations

from typehaus.model.assembly import Layer
from typehaus.model.base import Element
from typehaus.model.enums import AlarmKind, Occupancy, RoofForm
from typehaus.model.floors import FinishZone
from typehaus.model.refs import FollowRoof
from typehaus.model.placeables import Location, Mount
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
    """Rise derived from storey elevations; geometry is selected by ``layout``."""

    floor_opening: str  # FloorOpening tag in the storey above
    from_storey: str
    to_storey: str
    width: Length
    run_direction: str = "x"
    run_reversed: bool = False
    # ``straight`` | ``u_split_landing`` | ``right_angle_winder``.
    # The explicit vocabulary prevents a non-zero winder count from silently meaning a
    # particular turn shape.
    layout: str = "straight"
    # Relative to ascent; required for a right-angle winder only.
    turn_direction: str | None = None
    winder_count: int = 0
    start: Point2D | None = None
    # Depth of the turn landing (in the run direction) for a ``u_split_landing``.
    # ``None`` keeps the historical behaviour of reserving one stair width for the
    # 180° turn; authoring a value renders a deeper walk-off platform and shortens the
    # flights to suit. IRC R311.7.6 wants a landing at least the stair width deep, so a
    # sub-width value is treated as the width floor by the resolver.
    landing_depth: Length | None = None


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
class Alarm(Element):
    """A smoke/CO life-safety symbol associated with one room (M3)."""

    kind: AlarmKind
    room: str | None = None


@register_element
class Fixture(Element):
    """A placed plumbing/equipment fixture (M3)."""

    type_ref: str
    # Nullable like every other placeable kind (Furniture/Appliance/Register/Equipment/
    # ElectricalDevice): the shared drag macros clear the claim when a drop lands outside a
    # resolvable room, so a required str made a legal UI move write unloadable source.
    # A fixture that ends up without a room is a check finding, not a load error.
    room: str | None = None
    position: Point2D
    wall_ref: str | None = None  # drain-stack wall when services need a vertical chase
    drain_position: Point2D | None = None  # contractor override; default = position
    rotation: object | None = None  # Angle | None
    location: Location | None = None
    mount: Mount = Mount()


@register_element
class Furniture(Element):
    """A placed furniture instance driving dashboards/overlays (M3, #49)."""

    type_ref: str
    position: Point2D
    rotation: object | None = None  # Angle | None
    room: str | None = None
    location: Location | None = None
    mount: Mount = Mount()


@register_element
class Appliance(Element):
    """A service-bearing free or wall-attached product, separate from plumbing fixtures."""

    type_ref: str
    position: Point2D
    room: str | None = None
    rotation: object | None = None
    location: Location | None = None
    mount: Mount = Mount()
    wall_ref: str | None = None
    drain_position: Point2D | None = None


for _name, _obj in (
    ("Room", Room),
    ("Stair", Stair),
    ("Roof", Roof),
    ("GridAxis", GridAxis),
    ("Annotation", Annotation),
    ("Alarm", Alarm),
    ("Fixture", Fixture),
    ("Furniture", Furniture),
    ("Appliance", Appliance),
    ("WallLiningException", WallLiningException),
):
    register_constructor(_name, _obj)
