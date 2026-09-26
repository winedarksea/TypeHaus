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
    # The group can reach beyond the clear floor zone. A nightstand at the head of a bed
    # remains its companion even when side access starts farther toward the foot.
    occupant_footprint: Footprint2D | None = None


class PortCertainty(str, Enum):
    """How much a port's ``position`` and ``direction`` are worth.

    **The default is APPROXIMATE, and that is the whole point of the field.** A datasheet
    normally gives a FACE — "ports are all on top and all 6" round" — not four coordinates,
    and the Catlin ERV is authored the way every such sheet reads: four ports at the same
    local ``(0, 0, 21.6")``. ``mep.equipment_port_service``'s docstring records what that
    costs — a positional match against four coincident points is vacuous, so the check had
    to drop to the service level for every machine in the house, including the ones whose
    ports really are dimensioned.

    Stating the certainty separates the two. An EXACT port is a dimensioned station with a
    real outlet direction: a router may terminate on it, and a check may grade a duct end
    against it positionally. An APPROXIMATE one stays usable for a preliminary route —
    getting air to the case is still the right first answer — but it cannot establish an
    exact connection, and every report that rests on one says so rather than implying a
    precision the datasheet never gave.
    """

    EXACT = "exact"
    APPROXIMATE = "approximate"


class ServicePort(HausModel):
    """One connection a product declares: where it is, which way it faces, how big it is.

    ``direction`` is a unit vector in the PRODUCT frame, the same frame ``position`` is in,
    so a placement's rotation carries both (``resolve/mep_sleeves.rotate_into_plan``). It
    points the way air or water LEAVES the machine — an ERV's supply outlet on top points
    ``(0, 0, 1)`` — which is what lets a router leave the port along its axis instead of
    starting with a turn no fitting can make.

    The section is the port's own, and is stated in the pair the product is: ``connection_
    size`` for a round spigot, ``width``/``depth`` for a rectangular one. It is not the
    connected run's size — a 6" spigot fed by a 6" duct is the ordinary case and a 6" spigot
    on a transition off an 8" trunk is a real and different one.
    """

    tag: str
    service: Service
    position: tuple[Length, Length, Length]
    connection_size: Length | None = None
    #: Rectangular section, when the port is not round. Both or neither.
    width: Length | None = None
    depth: Length | None = None
    #: Unit vector in the product frame; ``None`` when the sheet does not say.
    direction: tuple[float, float, float] | None = None
    certainty: PortCertainty = PortCertainty.APPROXIMATE
    notes: str | None = None

    def is_exact(self) -> bool:
        return self.certainty is PortCertainty.EXACT

    def section_m(self) -> tuple[float, float] | None:
        """``(width, depth)`` in metres, round or rectangular, or None if unstated."""
        if self.connection_size is not None:
            return self.connection_size.meters, self.connection_size.meters
        if self.width is not None and self.depth is not None:
            return self.width.meters, self.depth.meters
        return None


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


def require_placed_or_hosted(item: object) -> None:
    """Exactly one of a plan point (``position`` / ``location.position``) or a wall
    attachment: an attached placeable's centre is derived, so a second, authored one could
    only disagree with it."""
    location = getattr(item, "location", None)
    attachment = getattr(location, "attachment", None)
    position = getattr(item, "position", None)
    tag = getattr(item, "tag", "?")
    if attachment is not None and position is not None:
        raise ValueError(f"{tag}: author `position` or `location.attachment`, not both — "
                         "an attached placeable's centre comes from its wall face")
    if attachment is None and position is None and getattr(location, "position", None) is None:
        raise ValueError(f"{tag}: a placeable needs a `position` or a `location.attachment`")
