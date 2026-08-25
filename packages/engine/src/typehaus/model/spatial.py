"""Spatial & annotation elements: Room, Stair, Roof, GridAxis, Annotation, Fixture,
Furniture (→ 10, → 11)."""

from __future__ import annotations

from typehaus.model.assembly import Layer
from typehaus.model.base import Element
from typehaus.model.enums import (
    HUMIDITY_CLASS_DESIGN_RH,
    AlarmKind,
    HumidityClass,
    Occupancy,
    RoofForm,
)
from typehaus.model.floors import FinishZone
from typehaus.model.placeables import Location, Mount
from typehaus.model.refs import FollowRoof
from typehaus.model.registry import register_constructor, register_element
from typehaus.model.trim import EaveTrim
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
    # Overrides the derived ceiling — the deck's ``ceiling_below``, or the roof's
    # ``default_lining`` for a room with no deck above — on this room's ceiling plane.
    # Room side first, same convention as ``wall_lining``. Empty = no override, fall
    # through to the derived default.
    ceiling_lining: tuple[Layer, ...] = ()
    # How wet this room is run — a separate axis from `occupancy` (see HumidityClass).
    # It is what scopes the condensation walk and the humid-room checks to the RH a
    # bounding assembly actually faces, instead of the whole-house design figure.
    humidity_class: HumidityClass = HumidityClass.NORMAL
    # An explicit override of the class's design RH, for a room whose setpoint is its own
    # decision rather than the class default. Authored as a fraction (0.70 == 70%).
    design_relative_humidity: float | None = None
    # This room's own dry-bulb setpoint, where it is not the house's. Dew point is a
    # function of both numbers, so a room held warmer *and* wetter than the house — the
    # tropical case — cannot state only one of them and be analysed honestly. None means
    # the house's ``Preferences.interior_setpoint_f``.
    design_temperature_f: float | None = None

    @property
    def interior_design_relative_humidity(self) -> float | None:
        """The RH this room's bounding assemblies are analysed at, or None for house-wide.

        None is not "unknown": it means the room carries no humidity decision of its own,
        so the house's ``Preferences.interior_relative_humidity`` is the right number and
        the caller supplies it. Only a room that is deliberately run wet answers here.
        """
        if self.design_relative_humidity is not None:
            return self.design_relative_humidity
        return HUMIDITY_CLASS_DESIGN_RH.get(self.humidity_class)


@register_element
class Stair(Element):
    """Rise derived from storey elevations; geometry is selected by ``layout``."""

    # The hole the flight comes up through, in the storey above. ``None`` for a run that
    # does not pass through a floor at all — a step-down within one storey, of which the
    # garage service stair is the reference case: five risers from the garage slab to the
    # house entry landing, no deck overhead, nothing to open. That case had to be authored
    # as a stack of ``Slab``s for want of this field, and a stack of slabs is invisible to
    # every stair check in the engine (``structural.stair_riser_uniformity`` and
    # ``code.R311_7_8_handrail`` both iterate ``model.stairs``), so a 5-riser flight with
    # no handrail drew no finding at all. A flight with no opening states its own
    # elevations below.
    floor_opening: str | None = None
    from_storey: str
    to_storey: str
    # Explicit absolute elevations, for a flight whose rise is not the gap between two
    # storey data. Authored together or not at all: ``base_elevation`` is the walking
    # surface the flight springs from and ``top_elevation`` the one it arrives at, both in
    # the project frame, exactly as a storey elevation is. Unset — the ordinary case — the
    # rise stays ``to_storey.elevation - from_storey.elevation`` and nothing moves.
    base_elevation: Length | None = None
    top_elevation: Length | None = None
    # What the flight is built of. ``Stair`` carried no material at all: the generators
    # build ``FramedMember``s with hard-coded "2x12"/"2x8" profiles and passed no
    # ``material=``, so every stair in every house rendered — in the viewer, the sections
    # and the glTF alike — as the generic lumber the category palette paints. A pressure-
    # treated exterior flight beside a painted interior one was the same colour as it.
    # A catalog material ref (``kdat``, ``spf``); ``None`` keeps the category palette.
    material: str | None = None
    width: Length
    run_direction: str = "x"
    run_reversed: bool = False
    # ``straight`` | ``u_split_landing`` | ``right_angle_winder``.
    # The explicit vocabulary prevents a non-zero winder count from silently meaning a
    # particular turn shape.
    layout: str = "straight"
    # Relative to ascent. Required for a right-angle winder. Optional for a
    # ``u_split_landing``, where it names the hand of the 180° turn: ``"right"`` (the
    # default) puts the springing flight in the lane nearest the ``start`` corner and the
    # arriving flight beyond the well partition, ``"left"`` mirrors the pair across the
    # well so the stair springs from the far lane and arrives in the near one.
    turn_direction: str | None = None
    winder_count: int = 0
    start: Point2D | None = None
    # Walls the flight is permitted to bear on, beyond the ones the resolver picks by
    # geometry + structural role. This grants permission, never restricts it: a tag here
    # promotes an otherwise non-bearing wall to a valid host, and a tag that names no wall
    # on ``from_storey`` is an ``integrity.stair_bearing`` error.
    bearing_refs: tuple[str, ...] = ()
    # Depth of the turn landing (in the run direction) for a ``u_split_landing``.
    # ``None`` keeps the historical behaviour of reserving one stair width for the
    # 180° turn; authoring a value renders a deeper walk-off platform and shortens the
    # flights to suit. IRC R311.7.6 wants a landing at least the stair width deep, so a
    # sub-width value is treated as the width floor by the resolver.
    landing_depth: Length | None = None
    # Nominal newel-post profile at the winder turn (e.g. "4x4", "6x6"). A wider newel
    # widens the well the winders wrap, moving their narrow ends apart — the sanctioned
    # lever on ``structural.winder_narrow_tread_depth`` short of adding risers.
    newel_profile: str = "4x4"
    # A tread is deliberately wider than its step-to-step going: the default 1" nose overhangs
    # the riser below, leaving a 10" code-minimum going on an 11" physical board.
    # ``None`` is retained for source compatibility with older authored plans and resolves to
    # the defaults below.
    tread_depth: Length | None = None
    nosing_depth: Length | None = None


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
    # Edge closure (fascia boards + soffit). Derived along every eave and rake from the
    # resolved roof plane, so it tracks a raised-heel lift instead of drifting from it.
    eave_trim: EaveTrim | None = None
    # The coil the formed edge trim and ridge cap are ordered in, when it is not the roofing's
    # own. Default ``None`` means "same stock as the panels", which is what every wrapped edge
    # assumed before this existed — and why a rake trim on a zero-overhang gable was invisible:
    # it inherited the panel colour in both renderers, so the one piece standing at the rake
    # could not read as an edge. Naming a second material here is the ordinary way a standing-
    # seam roof gets an accent trim, and it is a *product* choice, so it belongs on the roof
    # rather than in the resolver (the garage's white fascia must not follow the house's).
    edge_trim_material: str | None = None


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
    """A smoke/CO/heat life-safety symbol associated with one room (M3)."""

    kind: AlarmKind
    room: str | None = None
    # The branch circuit the detector's primary power comes off. R314.4 wants alarms on an
    # unswitched circuit; naming it here is what lets `electrical.circuit_refs` reconcile the
    # alarms against the panel schedule the way it already does for every other consumer.
    # ``None`` = not yet assigned, which is a modelling gap rather than a battery-only alarm.
    circuit: str | None = None
    # Where the head actually mounts. ``None`` falls back to the hosted room's seed, which is
    # the right answer for a compact room. It is the wrong answer for the alarm IRC R314.3
    # puts "in the immediate vicinity of the bedrooms": that one is hosted by the big open
    # room the corridor is part of, so the seed would draw it out in the middle of the living
    # space instead of in the hall lobe outside the bedroom doors. An explicit position says
    # where the detector is without inventing a room to hang it on.
    position: Point2D | None = None


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
    """A service-bearing free or wall-attached product, separate from plumbing fixtures.

    ``install_parts`` is the loose kit *this* installation carries, spelled the same way
    :class:`~typehaus.model.mep.PipeAccessory` spells it and billed through the same
    ``install_parts`` takeoff section. It is how a product whose accessories are not
    geometry still reaches the order: a disposer's 24V control loop is a power supply, a
    contactor, an enclosure, two buttons and a spool of cable — seven part numbers from
    three aisles, none of them a thing you can drag on a canvas. Modelling that loop as
    conduit and devices would be inventing routes nobody has decided; counting the parts is
    the true statement the model can make today.
    """

    type_ref: str
    position: Point2D
    room: str | None = None
    rotation: object | None = None
    location: Location | None = None
    mount: Mount = Mount()
    wall_ref: str | None = None
    drain_position: Point2D | None = None
    install_parts: tuple[str, ...] = ()  # loose kit billed with this installation


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
