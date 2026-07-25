"""Shared physical contracts for objects that can appear on the design canvas.

The values in this module deliberately describe *local* product geometry.  Resolvers
turn them into project geometry; source files never need to duplicate that math.
"""

from __future__ import annotations

from enum import Enum

from typehaus.model.base import HausModel
from typehaus.model.enums import Service
from typehaus.quantities import Length, Point2D, m


class PlacementStrategy(str, Enum):
    OPENING_HOSTED = "opening_hosted"
    FREE_PLACED = "free_placed"
    WALL_ATTACHED = "wall_attached"


class MountKind(str, Enum):
    FLOOR = "floor"
    WALL = "wall"
    CEILING = "ceiling"


class ClearancePolicy(str, Enum):
    REQUIRED = "required"
    RECOMMENDED = "recommended"


class Footprint2D(HausModel):
    """Closed local polygon in metres/feet project quantities, clockwise or counter-clockwise."""

    points: tuple[Point2D, ...]


class ClearanceZone(HausModel):
    footprint: Footprint2D
    purpose: str
    policy: ClearancePolicy = ClearancePolicy.RECOMMENDED
    source: str | None = None
    code_profile: str | None = None
    # Product types this zone exists to accommodate: a dining chair standing in its table's
    # chair-use zone is the arrangement working, not an encroachment. Naming them here lets
    # the resolver recover the furniture *group* (table + its chairs) that no source file has
    # to spell out, while a sofa parked in the same zone still reports a conflict. Only
    # meaningful on a RECOMMENDED zone — a code-required clearance is never "for" whatever
    # happens to be standing in it.
    occupant_types: tuple[str, ...] = ()


class ServicePort(HausModel):
    tag: str
    service: Service
    position: tuple[Length, Length, Length]
    connection_size: Length | None = None
    notes: str | None = None


class PlanRepresentation(HausModel):
    label: str | None = None
    svg: str | None = None


class ModelRepresentation(HausModel):
    primitive: str | None = None
    glb: str | None = None


class WallAttachment(HausModel):
    """Persistent finish-face relationship, measured from the wall start node."""

    wall_ref: str
    face: str  # left | right, relative to authored wall direction
    distance_from_start: Length
    normal_gap: Length = m(0)
    rotation_offset: object | None = None


class Location(HausModel):
    position: Point2D | None = None
    rotation: object | None = None
    attachment: WallAttachment | None = None


class Mount(HausModel):
    kind: MountKind = MountKind.FLOOR
    elevation: Length | None = None
    drop: Length | None = None
    # ``True`` when the body is set *into* its host surface rather than standing on it — a
    # floor register dropped into its boot, a can light buried in the ceiling, a medicine
    # cabinet let into the wall. The type's ``height`` then measures the cavity behind the
    # finish plane, not a protrusion in front of it, which is what decides whether the object
    # obstructs a neighbour's clear floor space (→ resolve/placeable_clear_floor_obstruction).
    # Default ``False`` so an unstated mount is read as surface-mounted and still obstructs.
    recessed_into_host_surface: bool = False
