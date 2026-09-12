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
from typehaus.model.refs import FollowRoof, PublishedSpan
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
    # An exterior composite wear surface and its PT carriage are different orders.
    # None preserves the framing material on the treads and the existing lumber bill.
    tread_material: str | None = None
    # Straight flights only: manufacturer maximum support spacing, evenly divided
    # across the width, including both edge stringers. None retains two edge stringers.
    stringer_spacing: Length | None = None
    # How the flight is carried: ``stringer`` (raked, notched 2x12s running the whole run)
    # or ``box`` (one framed box per tread, stacked). Straight flights only.
    #
    # ** A CUT STRINGER HAS TWO PRESCRIPTIVE LIMITS AND A BROAD SHALLOW FLIGHT BREAKS BOTH. **
    # DCA 6 Fig. 28 / IRC R507.13.1 cap the horizontal span at 6'-0" and the remaining
    # throat at 5". The throat is ``11.25 - R*T/hypot(R,T)``, and the intuition runs
    # backwards: a FLATTER pitch removes MORE material, because the notch depth is driven by
    # the long going. A terrace tier — a 6.8" rise on an 18"-24" going — lands near 4.7"-4.9"
    # and no 2x is wide enough to fix it (5" at 6.8:18 would want an 11.54" throat, so an
    # 11.25" 2x12 is 0.29" short and the next size is off every prescriptive table).
    #
    # A box tier sidesteps both: nothing is notched, so there is no throat, and each box
    # spans between its own footings rather than running the flight. It is how broad shallow
    # tiers are actually built — "essentially a mini deck, long and thin, just with joists in
    # between" — and DCA 6's hook is that an intermediate landing "must be designed and
    # constructed as a non-ledger deck using the details in this document", so the rims and
    # joists size off DCA 6's DECK tables and not off any stair table.
    #
    # Boxes resolve as ``landing_framing``, not ``stringer``: a tier IS a landing, and no
    # member of a box flight is a stringer. Checks that grade a carriage must not find one.
    #
    # ``cast`` is the third mode and it frames NOTHING. A poured concrete terrace has no
    # carriage to generate: each tier is a pour, authored as its own ``Slab`` with its own
    # outline, thickness, mix and elevation, because that is what a pour is and the model
    # already says it well. What stays on the ``Stair`` is the flight's CODE geometry — the
    # rise, the going, the width, the headroom, the guard it serves — which is exactly the
    # part a stack of slabs cannot state. So a cast flight is one element for the rule and n
    # elements for the concrete, and the members tuple is empty on purpose rather than by
    # omission. Grep the house for the tier tags before assuming a cast flight is unbuilt.
    carriage: str = "stringer"
    # The stock BOUGHT for this flight's walking surfaces — treads, winder panels and
    # landing decks alike. It is what says "1" of ply under 1/2" of carpet-over-cushion"
    # instead of the ordinary 1 1/2" tread board, and it is a takeoff fact, not a
    # dimensional one: every generator drops its boards by exactly this much
    # (``resolve/stairs/common.py::_notch_z``), so the finished rises do not move. Every
    # layout honours it. ``None`` retains the 1 1/2" board.
    tread_thickness: Length | None = None
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
    # The published table row that answers this member's span, where one does. A
    # manufacturer's table is a PRESCRIPTIVE read — a reviewer opens the document and the
    # question is closed — so authoring one here takes the requirement out of the
    # engineering register rather than into it. See ``model/refs.PublishedSpan``, which
    # carries the drift guards that stop a quotation outliving the model it was read for.
    published_span: PublishedSpan | None = None
    # Which of the two ridge-axis ends may be a GABLE END, by compass name. A gable end
    # takes a drop/gable-end frame instead of a field truss, and SBCA's own definition is
    # that such a frame has continuous vertical support from the end wall or beam under its
    # bottom chord — it is not a truss and does not span.
    #
    # ``None`` derives both ends from that definition: a wall top plate running under the
    # end station makes it a gable end, and nothing under it makes it a field truss.
    # A tuple NARROWS the derived answer and can never widen it, which is the whole point —
    # authoring an end here cannot conjure a gable frame over thin air, but it can say "that
    # plate belongs to somebody else's building", which no geometry can tell. ``()`` is
    # therefore "neither end is mine": RF-BW-CANOPY's north end station lands on the garage's
    # W-G-S plate, and the canopy is required to share no gravity with the garage.
    gable_ends: tuple[str, ...] | None = None
    # Edge closure (fascia boards + soffit). Derived along every eave and rake from the
    # resolved roof plane, so it tracks a raised-heel lift instead of drifting from it.
    eave_trim: EaveTrim | None = None
    # The coil the formed edge trim and ridge cap are ordered in, when it is not the roofing's
    # own. Default ``None`` means "same stock as the panels" — why a rake trim on a
    # zero-overhang gable was invisible: it inherited the panel colour in both renderers, so
    # the one piece standing at the rake could not read as an edge. Naming a second material
    # here is the ordinary way a standing-
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
