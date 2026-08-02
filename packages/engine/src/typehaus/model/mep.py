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
    elevations: tuple[Length, ...] | None = None  # per-vertex inverts, len == len(path)
    serves: tuple[str, ...] = ()  # upstream Fixture tags
    wall_refs: tuple[str | None, ...] | None = None  # host wall per segment
    wall_ref: str | None = None  # sugar: every segment hosted by this one wall
    material: str | None = None  # "pex" | "pvc" | "abs" | "copper" — takeoff grouping


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
    """One authored HVAC duct run, optionally routed through a floor's joist bays."""

    system: DuctSystem
    path: tuple[Point2D, ...]
    width: Length  # plan width
    depth: Length  # vertical
    routing: DuctRouting = DuctRouting.EXPOSED
    floor_ref: str | None = None  # FloorSystem tag whose bays it occupies (JOIST_BAY)
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
    roof. The resolver derives the 4-point 3D polyline from these fields; it never invents
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
    exit_offset: Point2D  # horizontal delta chase -> exterior riser plan location
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
