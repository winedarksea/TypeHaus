"""A pipe riser standing in the open air of a finished room: one predicate, two readers.

``mep.run_in_finished_volume`` grades a riser (a leg with no plan length) by whether its
plan point is in wall cover or a soffit and its z band reaches into the room's air. The
router reads the SAME functions through :class:`RiserCover`, so it cannot lay a riser the
check then fails. Pipes only; ducts and raceways are not attached (``routing/graph``).

Flat ceilings only: a ``FollowRoof`` room, a mechanical room and a room declared
``exposed_services`` (graded against a headroom line, a preference) are not zones here.

A served fixture's body excuses the legs from a run's end inside it and under its top (the
check's ``fixture_trim``); :func:`served_bodies` and :func:`in_body` are that one predicate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from shapely.geometry import Point, Polygon

from typehaus.model.enums import EXPOSED_SERVICE_OCCUPANCIES, Occupancy
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.overlay import difference, union_all

#: The check's default ``ceiling_intrusion_in`` (3"): a riser exposed less than this is excused.
RISER_TOL_M = 3.0 * M_PER_IN
_M_TO_FT = 1.0 / 0.3048


def wall_cover(model: ResolvedModel, storeys: set[str]) -> Any:
    """The union of every wall layer polygon on ``storeys`` — "somewhere to strap to".

    Layer polygons rather than the axis: the question is physical, and a 5 1/2" stud bay is
    5 1/2" of support where the axis is a line. Through :mod:`.overlay`, because GEOS 3.12.1
    (the published web app) is fatal on an un-gridded overlay of nearly-collinear polygons.
    It does not ask whether the wall could HOST the run (``mep.wet_wall_occupancy`` does).
    """
    polygons = [Polygon(layer.polygon)
                for wall in model.walls if wall.storey in storeys
                for layer in wall.layers if len(layer.polygon) >= 3]
    valid = [poly for poly in polygons if poly.is_valid and not poly.is_empty]
    return union_all(valid) if valid else None


def soffit_cover(model: ResolvedModel, storey: str) -> Any:
    """The plan union of ``storey``'s soffits — a run inside a bulkhead is boxed out. PER
    STOREY: a house-wide union read a bulkhead as covering every room stacked over it."""
    polygons = [Polygon(soffit.outline) for soffit in model.soffits
                if soffit.storey == storey and len(soffit.outline) >= 3]
    valid = [poly for poly in polygons if poly.is_valid and not poly.is_empty]
    return union_all(valid) if valid else None


def served_bodies(model: ResolvedModel, serves: Any) -> list[tuple[Any, float]]:
    """``[(footprint grown 1 mm, body top)]`` of each fixture in ``serves`` that has a body."""
    tags = set(serves)
    return [(Polygon(c.footprint).buffer(1e-3), c.body_z1_m) for c in model.canvas_objects
            if c.tag in tags and len(c.footprint) >= 3 and c.body_z1_m is not None]


def in_body(bodies: Any, piece: Any, top: float) -> bool:
    """Whether ``piece`` (plan geometry) lies in a body's footprint with ``top`` under its top."""
    return any(shape.covers(piece) and top <= body_top + 1e-3 for shape, body_top in bodies)


def riser_row(a: tuple[float, float], za: float, zb: float, radius: float, outline: Any,
              cover: Any, soffits: Any, floor: float, ceiling_z: float,
              tol: float) -> list[tuple[float, float]]:
    """``[(exposure_ft, intrusion_in)]`` for a riser at ``a`` against one ceiling, or ``[]``
    when it stands outside the room, in cover, in a soffit, or above the plane (within
    ``tol``). The check's riser branch, lifted whole."""
    if not outline.covers(Point(a)):
        return []
    if cover is not None and cover.covers(Point(a)):
        return []
    if soffits is not None and soffits.covers(Point(a)):
        return []
    low, high = riser_band(za, zb, radius, floor, ceiling_z)
    if high - low <= tol:
        return []
    return [((high - low) * _M_TO_FT, (ceiling_z - low) / M_PER_IN)]


def riser_band(za: float, zb: float, radius: float, floor: float,
               ceiling_z: float) -> tuple[float, float]:
    """The pipe's outside, clamped to the room's air: floor to ceiling plane."""
    return max(min(za, zb) - radius, floor), min(max(za, zb) + radius, ceiling_z)


@dataclass
class _Zone:
    open_air: Any  # the room's ceiling outline less wall cover and soffits, prepared
    floor: float
    ceiling_z: float


@dataclass
class RiserCover:
    """The open-air zones of every graded room: where a pipe riser may not stand."""

    zones: list[_Zone] = field(default_factory=list)
    tol_m: float = RISER_TOL_M
    #: Plan points a route starts or ends at; the check excuses the leg that connects them.
    exempt: list[tuple[float, float, float | None]] = field(default_factory=list)
    #: Served fixture bodies holding an exempt end: a riser in one, under its top, is its
    #: trap and drop (``fixture_trim``), excused in the room the body stands in.
    bodies: list[tuple[Any, float]] = field(default_factory=list)
    _at: dict[tuple[float, float], list[_Zone]] = field(default_factory=dict, repr=False)

    def exposed(self, x: float, y: float, za: float, zb: float, radius: float) -> bool:
        """Whether a riser at ``(x, y)`` from ``za`` to ``zb`` stands in a room's open air."""
        key = (round(x, 4), round(y, 4))
        zones = self._at.get(key)
        if zones is None:
            probe = Point(x, y)
            zones = self._at[key] = [z for z in self.zones if z.open_air.covers(probe)]
        ends = [ez for ex, ey, ez in self.exempt if abs(x - ex) < 1e-3 and abs(y - ey) < 1e-3]
        for zone in zones:
            # The check excuses the end leg only in the room the fixture stands IN (its own
            # storey): a riser passing through the room below is in that room's air.
            if any(ez is None or zone.floor - 1e-3 <= ez <= zone.ceiling_z for ez in ends):
                continue
            if self.bodies and in_body(
                    [b for b in self.bodies if zone.floor - 1e-3 <= b[1] <= zone.ceiling_z],
                    Point(x, y), max(za, zb) + radius):
                continue
            low, high = riser_band(za, zb, radius, zone.floor, zone.ceiling_z)
            if high - low > self.tol_m:
                return True
        return False


def riser_cover(model: ResolvedModel, bbox: tuple[float, float, float, float] | None = None,
                exempt: Any = (), *, tol_m: float = RISER_TOL_M,
                serves: Any = ()) -> RiserCover:
    """Open-air zones for ``model``'s graded flat-ceiling rooms, inside ``bbox`` if given;
    a riser at an ``exempt`` point (a route's own end) is excused in the room at its z, and
    one inside a ``serves`` fixture's body holding an exempt end, under its top, likewise."""
    from shapely import prepare
    from shapely.geometry import box

    window = box(*bbox) if bbox is not None else None
    occupancies = {room.tag: room.occupancy for room in model.rooms}
    closed = {room.tag for room in model.rooms if room.closed_to_services}
    declared = {room.tag for room in model.rooms if room.exposed_services}
    storey_z = {storey.tag: storey.elevation.meters for storey in model.plan.storeys}
    covers: dict[str, Any] = {}
    soffits: dict[str, Any] = {}
    out = RiserCover(tol_m=tol_m,
                     exempt=[(p[0], p[1], p[2] if len(p) > 2 else None) for p in exempt])
    out.bodies = [b for b in served_bodies(model, serves) if serves
                  and any(b[0].covers(Point(p[0], p[1])) for p in exempt)]
    for ceiling in model.ceilings:
        if ceiling.z0_m is None or ceiling.room_ref in declared or len(ceiling.outline) < 3:
            continue
        occupancy = occupancies.get(ceiling.room_ref)
        if (occupancy is not None and Occupancy(occupancy) in EXPOSED_SERVICE_OCCUPANCIES
                and ceiling.room_ref not in closed):
            continue
        outline = Polygon(ceiling.outline)
        if not outline.is_valid or outline.is_empty:
            continue
        if window is not None and not outline.intersects(window):
            continue
        if ceiling.storey not in covers:
            covers[ceiling.storey] = wall_cover(model, {ceiling.storey})
            soffits[ceiling.storey] = soffit_cover(model, ceiling.storey)
        open_air = outline
        for part in (covers[ceiling.storey], soffits[ceiling.storey]):
            if part is not None:
                open_air = difference(open_air, part)
        if open_air.is_empty:
            continue
        prepare(open_air)
        out.zones.append(_Zone(open_air, storey_z.get(ceiling.storey, 0.0), ceiling.z0_m))
    return out
