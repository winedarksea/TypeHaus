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
class ElectricalDevice(Element):
    """A device symbol — schema keeps a ``circuit`` hook for a future panel schedule."""

    kind: DeviceKind
    position: Point2D
    wall_ref: str | None = None
    mount_height: Length | None = None
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
):
    register_constructor(_name, _obj)
