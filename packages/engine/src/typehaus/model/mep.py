"""Authored MEP routing: plumbing/HVAC/electrical (→ Permit-ready plan set Phases 2-3).

Authored routing only — the user places runs/ducts/devices; the resolver validates them
against the framing (joist bays, bearing lines, slab hosts) and the sheets draw them.
Auto-routing is a declared non-goal.
"""

from __future__ import annotations

from typehaus.model.base import Element
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
    """One authored plumbing run — a plan-frame polyline with inverts at each end."""

    system: PipeSystem
    path: tuple[Point2D, ...]  # plan-frame polyline, >= 2 points
    diameter: Length
    start_elevation: Length | None = None  # invert at path[0], storey-relative
    end_elevation: Length | None = None
    serves: tuple[str, ...] = ()  # upstream Fixture tags


@register_element
class SleevePenetration(Element):
    """A cast-in-place sleeve through a structural slab — position cannot move after pour."""

    host_ref: str  # Slab tag, e.g. "SL-M-DECK"
    position: Point2D  # exact cast-in-place center
    pipe_diameter: Length  # 3" WC, 2" shower, 1.5" lav
    sleeve_diameter: Length  # pipe + annular space
    serves_fixture: str | None = None
    purpose: Service = Service.DRAIN


@register_element
class DuctRun(Element):
    """One authored HVAC duct run, optionally routed through a floor's joist bays."""

    system: DuctSystem
    path: tuple[Point2D, ...]
    width: Length  # plan width
    depth: Length  # vertical
    routing: DuctRouting = DuctRouting.EXPOSED
    floor_ref: str | None = None  # FloorSystem tag whose bays it occupies (JOIST_BAY)


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
class ElectricalDevice(Element):
    """A device symbol — schema keeps a ``circuit`` hook for a future panel schedule.

    Height comes from ``mount`` like every other placeable; the former ``mount_height``
    scalar was a second, device-only source of truth that the placeable resolver never
    read, so every light silently resolved to the floor."""

    kind: DeviceKind
    position: Point2D
    wall_ref: str | None = None
    circuit: str | None = None  # future panel-schedule hook; no consumer yet
    type_ref: str | None = None
    room: str | None = None
    rotation: object | None = None
    location: Location | None = None
    mount: Mount = Mount()


for _name, _obj in (
    ("PipeRun", PipeRun),
    ("SleevePenetration", SleevePenetration),
    ("DuctRun", DuctRun),
    ("Register", Register),
    ("Equipment", Equipment),
    ("ElectricalDevice", ElectricalDevice),
    ("Sump", Sump),
    ("VentRun", VentRun),
):
    register_constructor(_name, _obj)
