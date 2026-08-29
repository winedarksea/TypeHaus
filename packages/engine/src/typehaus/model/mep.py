"""Authored MEP routing: plumbing/HVAC/electrical (→ Permit-ready plan set Phases 2-3).

Authored routing only — the user places runs/ducts/devices; the resolver validates them
against the framing (joist bays, bearing lines, slab hosts) and the sheets draw them.
Auto-routing is a declared non-goal.
"""

from __future__ import annotations

from typehaus.model.base import Element, HausModel
from typehaus.model.enums import (
    DeviceKind,
    DuctRouting,
    DuctSystem,
    EquipmentKind,
    PipeAccessoryKind,
    PipeSystem,
    Service,
)
from typehaus.model.registry import register_constructor, register_element
from typehaus.model.placeables import Location, Mount
from typehaus.quantities import Length, Point2D


@register_element
class PipeRun(Element):
    """One authored plumbing run — a routed 3D polyline.

    ``path`` is the plan-frame polyline; ``elevations`` (optional) gives the invert at
    every vertex, storey-relative, so a run can slope per segment and drop vertically —
    a vertical drop is a repeated plan point with two different elevations. When
    ``elevations`` is None the resolver interpolates linearly between
    ``start_elevation``/``end_elevation`` over developed plan length, which is exactly
    the old two-invert behaviour — existing authored runs resolve unchanged.

    An ``elevations`` entry may itself be ``None``, meaning "solve me": with
    ``slope_in_per_ft`` set, the resolver falls at that grade over the developed plan length
    from the last invert that *was* authored. A vertical leg is the one place that cannot
    work — a drop does not fall at a grade — so both its ends must be authored.

    ``wall_refs`` names the host wall per segment (len == len(path) - 1); a None entry
    means the segment is in-floor/under-slab/exposed, not in a wall. ``wall_ref`` is
    sugar for a run living in one wall throughout. The resolver validates in-wall
    segments against the named wall's structure cavity (mep.wet_wall_occupancy) —
    the pipe must actually fit the wall it claims.
    """

    system: PipeSystem
    path: tuple[Point2D, ...]  # plan-frame polyline, >= 2 points
    diameter: Length
    start_elevation: Length | None = None  # invert at path[0], storey-relative
    end_elevation: Length | None = None
    # Per-vertex inverts, ``len == len(path)``. An entry may be **None**: "fall at
    # ``slope_in_per_ft`` from the last invert I did author". A drain that runs at one grade
    # for forty feet is one fact — the grade — and authoring twelve hand-computed inverts
    # off it is twelve chances to get the arithmetic wrong and no way for the file to say
    # what it meant. A UI drag simply writes a concrete ``ft(...)`` into the slot, so the
    # editable dialect and its write-back are untouched (``None`` in a tuple is what
    # ``wall_refs`` has always done).
    elevations: tuple[Length | None, ...] | None = None
    # Inches of fall per foot of developed plan run, used to solve every ``None`` above.
    # Positive falls in path order, which is flow order for a drain. ``None`` means every
    # invert is authored — set one without an anchor invert and the resolver errors rather
    # than picking a datum out of the air (``integrity.pipe_run_slope``).
    slope_in_per_ft: float | None = None
    serves: tuple[str, ...] = ()  # upstream Fixture tags
    wall_refs: tuple[str | None, ...] | None = None  # host wall per segment
    wall_ref: str | None = None  # sugar: every segment hosted by this one wall
    material: str | None = None  # "pex" | "pvc" | "abs" | "copper" — takeoff grouping
    # How the pipe is finished where it is seen. Separate from ``material`` because it is a
    # separate purchase and a separate operation: copper is the pipe, lacquer is a coating
    # applied to it, and a takeoff that folded the two into one string would bill the same
    # copper twice under two names the moment one run was left bare.
    finish: str | None = None  # e.g. "lacquered"
    # The pipe insulation spec, billed by the foot. A field rather than an element because
    # insulation has no route of its own — it is exactly as long as the run it sleeves, and
    # an authored second polyline tracking a first is a second source of truth for one
    # length. ``None`` means bare pipe, which for a hot line is what N1103.4.2 fails.
    insulation: str | None = None  # e.g. '1" fiberglass, ASJ'
    # Self-regulating heater cable on the run, billed by the foot exactly as ``insulation``
    # is, and a field for the same reason: a heat trace has no route of its own, it is as
    # long as the pipe it follows, and a second authored polyline tracking the first would be
    # a second source of truth for one length.
    #
    # It is a SEPARATE field from ``insulation`` and not a value of it. The two are different
    # purchases, different trades and different failure modes — cable is an electrical item on
    # a circuit, lagging is a thermal one — and a run very often wants both, the insulation
    # over the cable. Folding them into one string would make "traced AND insulated"
    # unsayable, which is the normal specification for an outdoor drain in this climate.
    #
    # ``None`` means no cable, which is the right answer for every interior run and the wrong
    # one for a condensate line leaving a cold-climate heat pump: defrost meltwater running
    # in an unheated pipe in February is how the pipe, and then whatever it discharges into,
    # plugs with ice.
    freeze_protection: str | None = None  # e.g. '5 W/ft self-regulating, 120 V'


@register_element
class PipeAccessory(Element):
    """One in-line device on a supply run — valve, backflow preventer, arrestor, seal.

    ``pipe_ref`` names the ``PipeRun`` it sits on, which is what gives it a system, a
    diameter and a route; ``position`` is its plan point. ``elevation`` is storey-relative
    and optional — left off, the resolver takes the host run's invert at the nearest path
    vertex, which is nearly always what is meant (a valve is *on* the pipe) and is the one
    number an author would otherwise have to copy by hand and keep in step.

    ``install_parts`` is the kit that comes with the device and is billed with it: the
    balcony hydrant's silicone gasket, plastic mounting bracket and closed-cell foam are
    three line items nobody stocks as a "hydrant", and they are properties of *this*
    installation rather than of the hydrant type, which is why they ride the accessory and
    not the catalog.

    ``accessible`` is the claim P2903.9.1 tests on a main shutoff — reachable without
    removing a panel or standing on something. Authored, never inferred: whether a valve
    behind the water heater can be reached is a judgement about the room, and the model
    would only be guessing.
    """

    kind: PipeAccessoryKind
    position: Point2D
    pipe_ref: str | None = None  # host PipeRun tag
    elevation: Length | None = None  # storey-relative; None -> host run z at nearest vertex
    serves: tuple[str, ...] = ()  # Fixture/Equipment/PipeRun tags downstream of it
    accessible: bool = False
    room: str | None = None
    wall_ref: str | None = None
    model: str = ""  # manufacturer/model, for the plumbing schedule
    install_parts: tuple[str, ...] = ()  # sealing/mounting kit billed with the device


@register_element
class SleevePenetration(Element):
    """A cast-in-place sleeve through concrete — position cannot move after pour.

    ``host_ref`` may name a slab, footing, or concrete wall. ``axis`` is "vertical" for
    the common slab drop; "horizontal" for a foundation-wall or rim crossing (sewer
    exit, water-service entry), where ``position`` is the plan point on the host and
    ``center_elevation`` is the project-frame elevation of the sleeve centerline.
    """

    host_ref: str  # Slab/Footing/Wall tag, e.g. "SL-M-DECK"
    position: Point2D  # exact cast-in-place center
    pipe_diameter: Length  # 3" WC, 2" shower, 1.5" lav
    sleeve_diameter: Length  # pipe + annular space
    serves_fixture: str | None = None
    purpose: Service = Service.DRAIN
    axis: str = "vertical"  # "vertical" | "horizontal"
    center_elevation: Length | None = None  # horizontal sleeves: project-frame center z


@register_element
class DuctRun(Element):
    """One authored HVAC duct run — a routed 3D polyline, round or rectangular.

    Section is *either* ``diameter`` (round: semi-rigid radial, flex, spiral) *or*
    ``width`` + ``depth`` (rectangular sheet metal), never both and never neither —
    ``integrity.duct_run_section`` says so. Both spellings are optional fields because
    both spellings are real ducts, and a round run forced to declare a width would be
    declaring a number nobody could measure on site.

    Elevations work exactly as :class:`PipeRun`'s inverts do, and for the same reason: a
    four-storey ERV is not a set of plan polylines that teleport between floors. A vertical
    riser is a repeated plan point at two elevations — no new concept. Where ``elevations``
    is absent the resolver derives z from the ``floor_ref`` bay (JOIST_BAY) or the storey
    datum, so every duct authored before this field existed still resolves, and gains a 3D
    solid for free.

    ``soffit_ref`` names the modeled :class:`~typehaus.model.floors.Soffit` a run is
    concealed in, mirroring ``floor_ref`` for a joist bay. It is what turns
    ``routing=SOFFIT`` from an escape hatch — the flag that told ``duct_bay_occupancy`` to
    stop looking — into a checked claim: ``mep.duct_soffit_occupancy`` measures everything
    naming a soffit against that soffit's *derived* clear section. ``CHASE`` keeps its
    honest meaning, a framed shaft that is not modeled as a ``Soffit``, and stays a
    declared unchecked case rather than a silent one.
    """

    system: DuctSystem
    path: tuple[Point2D, ...]
    # Exactly one of (diameter) or (width + depth). See the class docstring.
    diameter: Length | None = None  # round section
    width: Length | None = None  # rectangular: plan width
    depth: Length | None = None  # rectangular: vertical
    routing: DuctRouting = DuctRouting.EXPOSED
    floor_ref: str | None = None  # FloorSystem tag whose bays it occupies (JOIST_BAY)
    soffit_ref: str | None = None  # Soffit tag the run is concealed in (SOFFIT routing)
    # Storey-relative centreline elevations, mirroring PipeRun's inverts. ``elevations``
    # is one per path vertex and an entry may be None ("solve me" — see mep_slope); the
    # start/end pair is the two-point sugar. All absent -> the resolver derives one z from
    # the floor bay or the storey, which is what every duct authored before this field
    # existed already meant.
    start_elevation: Length | None = None
    end_elevation: Length | None = None
    elevations: tuple[Length | None, ...] | None = None
    #: Inches of fall per foot of developed plan run, solving every ``None`` above. Rare on
    #: a duct — air does not need a grade — but a condensing-side run does get pitched, and
    #: the solver is the same one.
    slope_in_per_ft: float | None = None
    material: str | None = None  # "galv" | "semi_rigid" | "flex" — takeoff grouping
    # The duct insulation spec, billed by the foot, exactly as ``PipeRun.insulation`` is.
    # ``None`` means bare, which for an outdoor-air duct through conditioned space is what
    # sweats all winter.
    insulation: str | None = None  # e.g. 'R-8 wrap, vapour-sealed'
    # The airflow this run is *intended* to carry, for the duct schedule and the HVAC sheet.
    # Documentation, not a solved quantity: there is no airflow solver here, and inventing
    # one from the section would be exactly the kind of guess this model refuses to make.
    design_cfm: float | None = None


@register_element
class Register(Element):
    """A supply/return grille terminating a DuctRun."""

    kind: DuctSystem
    position: Point2D
    duct_ref: str | None = None
    type_ref: str | None = None
    room: str | None = None
    rotation: object | None = None
    location: Location | None = None
    mount: Mount = Mount()
    circuit: str | None = None  # Circuit tag (panel schedule), mirrors ElectricalDevice
    # The airflow this *terminal* is balanced to — the number a mechanical schedule prints
    # against a grille, and what a balancing report measures at it. ``DuctRun.design_cfm``
    # cannot stand in for it: a trunk with seven pickups on it carries seven rooms' air, so
    # crediting its total to any one of them would overstate that room by a factor of seven.
    # Documentation like the run's, not a solved quantity; unstated stays UNKNOWN.
    design_cfm: float | None = None


@register_element
class Equipment(Element):
    """Mechanical/water-heating equipment with a declared footprint."""

    kind: EquipmentKind
    position: Point2D
    footprint: tuple[Length, Length]
    room: str | None = None
    type_ref: str | None = None
    rotation: object | None = None
    location: Location | None = None
    mount: Mount = Mount()
    # Circuit tag (panel schedule) — hard-wired equipment has no receptacle device,
    # so the circuit hook lives on the equipment itself, mirroring ElectricalDevice.
    circuit: str | None = None
    # The Room tags this unit conditions. A zone is a *grouping of rooms*, not a storey: a
    # whole-storey zone is authored as that storey's room tags, spelled out (the editable
    # plan dialect has no helpers to expand one, and a spelled-out list is what a plan
    # reader checks against the floor plan). Authored, never inferred — the check compares
    # a condenser's capacity against the load of exactly these rooms and reports any
    # conditioned room no unit claims, rather than guessing a partition.
    zone_rooms: tuple[str, ...] = ()
    # An indoor head/air handler names the outdoor condenser it is paired with (its
    # ``Equipment`` tag). Refrigerant lineset geometry is deliberately not modeled — this
    # pairing is what the schedule and the capacity check need.
    outdoor_ref: str | None = None
    # --- P2804: temperature and pressure relief, water heaters -------------------------
    # The TPR valve's discharge pipe, as a PipeRun tag. It is the one piece of a water
    # heater that is a life-safety device rather than a convenience, and the ways it is got
    # wrong are geometric: it traps, it terminates somewhere nobody would see it discharge,
    # or it was never run at all. All three are answerable once the run is named.
    relief_discharge_ref: str | None = None
    # P2801.6: a pan under a heater installed where a leak damages what is below it, and
    # the indirect waste that empties the pan.
    drain_pan: bool = False
    pan_drain_ref: str | None = None
    # The modeled ``Soffit`` this unit is installed inside, mirroring ``DuctRun.soffit_ref``.
    # Two things follow from it and neither could be said before: the placeable hangs off the
    # soffit's underside instead of the storey's default ceiling plane (an air handler in a
    # 14" dropped box was resolving at 9'-0", the ceiling above it), and
    # ``mep.duct_soffit_occupancy`` counts its case against the box's clear width alongside
    # every duct sharing it.
    soffit_ref: str | None = None


class SumpPump(HausModel):
    """The pump in a pit. A spec, not an element: it has no plan position of its own — it
    sits in the ``Sump`` that carries it, and moving the pit moves the pump.

    ``discharge`` says where the pumped water goes ("daylight", a ``Drywell`` tag, a storm
    lateral); ``circuit_ref`` is the branch it must be on, which is the thing an inspector
    actually looks for — a pit with no dedicated circuit is a pit that stops working when
    something else trips."""

    model: str = ""
    horsepower: float = 0.0
    discharge: str | None = None
    circuit_ref: str | None = None


@register_element
class Sump(Element):
    """A sump pit (basement slab low point) with an optional radon-vent takeoff.

    The pit is cast below the slab; when ``radon_vent`` is set it is a sealed radon sump
    whose passive vent leaves the sealed cover and rises through the mechanical chase —
    the ``vent_ref`` names the shared ``VentRun`` it feeds."""

    position: Point2D
    diameter: Length  # pit inside diameter
    depth: Length  # pit depth below the slab underside
    host_ref: str | None = None  # slab the pit is cast into
    sealed_cover: bool = True  # gasketed/sealed cover (required for a radon sump)
    radon_vent: bool = True
    vent_ref: str | None = None  # VentRun tag the radon takeoff joins
    # None means the pit takes water and lets it go by gravity. A pit with a pump exports an
    # IfcPump/SUMPPUMP joined to the stormwater system.
    pump: SumpPump | None = None


@register_element
class VentRun(Element):
    """A vertical vent riser bundling one or more systems up a shared mechanical chase.

    Encodes the Catlin routing intent: up the chase to ``exit_elevation`` (below the roof
    plane, so the jog stays inside), a 90° turn out through the wall by ``exit_offset``,
    then 90° back up the siding — clamped to the standing seam — terminating 12" above the
    roof. Optionally with one horizontal jog taken inside first (``chase_offset`` at
    ``chase_offset_elevation``), for a chase that surfaces where the roof leaves no height
    to rise in. The resolver derives the 3D polyline from these fields; it never invents
    the route. ``systems`` is typically (RADON, VENT).

    The termination height is *derived* from the roof plane at the exterior riser
    (resolve/vent_termination.py), not authored: an authored absolute cannot follow a rake
    it does not know about. ``roof_termination_elevation`` is therefore optional — supply
    it only where no roof is derivable, or as an assertion the ``mep.vent_termination_height``
    check validates against the derived value."""

    systems: tuple[PipeSystem, ...]
    diameter: Length
    chase_position: Point2D  # plan location of the chase
    start_elevation: Length  # where the riser starts (project-frame absolute)
    exit_elevation: Length  # below the roof plane at the chase, where it turns out
    exit_offset: Point2D  # horizontal delta chase top -> exterior riser plan location
    # An OPTIONAL horizontal jog taken *inside*, before the riser continues up to
    # ``exit_elevation`` and turns out through the wall — the same "rise to here, then step
    # sideways" pair ``exit_elevation``/``exit_offset`` already is, one storey earlier.
    #
    # A chase that is fine for its whole height can still surface somewhere it cannot rise:
    # under a story-and-a-half's rake the roof underside at the eave is inches above the
    # deck, and a riser in that chase has nowhere to go. Jogging it across the floor band to
    # a station with height is the cheap fix, and it is a fix the model could not express —
    # the alternative was moving ``chase_position`` and dragging the stack through every
    # storey below. Both fields must be set for the jog to take; ``None`` (every riser
    # written before this) resolves the original four-point route unchanged.
    chase_offset: Point2D | None = None
    chase_offset_elevation: Length | None = None
    roof_termination_elevation: Length | None = None  # optional; normally derived
    wall_ref: str | None = None  # exterior wall the riser penetrates / rides
    attachment: str = "standing_seam_clamp"  # how the exterior riser is fixed to the siding


@register_element
class ConduitRun(Element):
    """One authored raceway trunk — plan polyline plus project-frame end elevations.

    Not a ``PipeRun``: pipe systems feed plumbing checks (slope, vent reachability) that
    must never see a power raceway. Elevations are project-frame absolute because trunks
    cross storeys (panel → attic riser); where they differ the run rises vertically at
    its last point, and the developed length is plan length plus that rise. The point of
    conduit (electrical_notes.md line 3) is making future pulls easy, so only main
    trunks are modeled — branch wiring stays undrawn."""

    path: tuple[Point2D, ...]  # plan-frame polyline, >= 2 points
    trade_size: Length  # EMT trade size, e.g. inch(1)
    start_elevation: Length | None = None  # project-frame absolute
    end_elevation: Length | None = None
    from_ref: str | None = None  # feeding device, e.g. "ED-B-PANEL"
    to_ref: str | None = None  # served device/area, e.g. "ED-A-PV-JB"
    # What this raceway carries. One service per run, never a set: NEC 800.133/725 forbids
    # comms sharing a raceway with power, so a run that could name both would be able to
    # express an illegal install. ``None`` means a capped spare with a pull string and no
    # conductors — it joins no distribution system and bills no wire, which is the honest
    # reading of an empty pipe.
    service: Service | None = Service.POWER_120


@register_element
class ElectricalDevice(Element):
    """A device symbol; ``circuit`` names the ``Circuit`` feeding it (panel schedule).

    Height comes from ``mount`` like every other placeable; the former ``mount_height``
    scalar was a second, device-only source of truth that the placeable resolver never
    read, so every light silently resolved to the floor."""

    kind: DeviceKind
    position: Point2D
    wall_ref: str | None = None
    circuit: str | None = None  # Circuit tag in Library.circuits (panel schedule)
    type_ref: str | None = None
    room: str | None = None
    rotation: object | None = None
    location: Location | None = None
    mount: Mount = Mount()
    # SWITCH tags that control this device. N tags means N-way switching (two tags = a
    # 3-way pair). Named on the *load*, not the switch, because a switch commonly drives
    # several fixtures and a fixture is the thing a plan reader looks up. Empty on a
    # switch itself, on an always-on device, and on a fixture whose type carries
    # ``integral_switch``.
    controlled_by: tuple[str, ...] = ()


@register_element
class LightRun(Element):
    """One continuous run of linear luminaire — a cove/shadow-gap LED strip.

    A ``ConduitRun`` sibling, not an ``ElectricalDevice``: a strip has a *length*, not a
    position, so it is priced per foot and drawn as a polyline. It stays out of the
    placeable pipeline entirely (no ``_TYPE_COLLECTIONS`` entry, no ``model/canvas.py``
    allowlist entry) for the same reason conduit does — there is no footprint to place,
    rotate or clear.

    ``mount`` carries the run's height the way every placeable does: ``Mount(CEILING)``
    for a shadow gap, ``Mount(WALL, elevation=inch(34))`` for a stair railing light.
    ``psu_ref`` names the AC/DC supply feeding it when ``type_ref`` is a 24V type — a
    24V strip has no branch circuit of its own, its PSU does.
    """

    path: tuple[Point2D, ...]  # plan-frame polyline, >= 2 points
    type_ref: str  # a LuminaireType with form=STRIP
    mount: Mount = Mount()
    circuit: str | None = None  # line-voltage runs only; 24V runs feed from psu_ref
    controlled_by: tuple[str, ...] = ()
    psu_ref: str | None = None  # ElectricalDevice tag of the AC/DC supply (24V runs)
    room: str | None = None


for _name, _obj in (
    ("PipeRun", PipeRun),
    ("PipeAccessory", PipeAccessory),
    ("SleevePenetration", SleevePenetration),
    ("DuctRun", DuctRun),
    ("Register", Register),
    ("Equipment", Equipment),
    ("ElectricalDevice", ElectricalDevice),
    ("ConduitRun", ConduitRun),
    ("LightRun", LightRun),
    ("Sump", Sump),
    ("SumpPump", SumpPump),
    ("VentRun", VentRun),
):
    register_constructor(_name, _obj)
