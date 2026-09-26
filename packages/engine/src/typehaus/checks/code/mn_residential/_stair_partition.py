"""A switchback's inner side: the lane across its well partition, and what closes it.

The two lanes of a U-stair face each other over the generated well partition
(``resolve/stairs/u_split.py``), whose top stops flush with the arrival deck. Near the head,
the arriving lane's nosings stand a riser or two under that top while the departing lane
beside them is still near the floor below — an open side over a storey-deep fall, inside the
stair's own outline where ``code.R312_1_guard`` (the well's four perimeter edges) never
looks. ``code.R312_1_1_stair_open_side`` grades it with these helpers.
"""

from __future__ import annotations

from typing import Any

from typehaus.quantities import inch

#: How far the probe segment may pass from a partition member and still cross it.
_CROSS_TOL_M = 0.05
#: How far a nosing end may sit from a partition member and still be the face it lands on.
_REACH_M = 0.20
#: Solids stacked on one line with no more than a 4" sphere between them are one band.
_SPHERE_M = inch(4).meters


def partition_solids(stair) -> list[tuple[Any, float, float]]:
    """``(plan geometry, z0, z1)`` per generated partition member.

    Every member is floored at the partition's own base: studs, plates and the head stud
    are one solid in section, and a nosing between two studs is still walled.
    """
    from shapely.geometry import LineString, Point

    members = [m for m in stair.members if m.category == "partition"]
    if not members:
        return []
    base = min(m.z0_m for m in members)
    return [((Point(m.p0) if m.p0 == m.p1 else LineString([m.p0, m.p1])), base, m.z1_m)
            for m in members]


def crossed(solids, near, probe) -> list[tuple[float, float]]:
    """The ``(z0, z1)`` bands of partition members between ``near`` and ``probe``."""
    from shapely.geometry import LineString, Point

    seg, at = LineString([near, (probe.x, probe.y)]), Point(near)
    return [(z0, z1) for geom, z0, z1 in solids
            if seg.distance(geom) <= _CROSS_TOL_M and at.distance(geom) <= _REACH_M]


def closure_top(bands, z: float) -> float | None:
    """Top of the solid band that stands on the line through the nosing at ``z``.

    Bands touching within a sphere merge — a wall authored on the partition's top plate
    continues it — and the band has to reach down to the nosing to close anything.
    """
    merged: list[list[float]] = []
    for z0, z1 in sorted(bands):
        if merged and z0 <= merged[-1][1] + _SPHERE_M:
            merged[-1][1] = max(merged[-1][1], z1)
        else:
            merged.append([z0, z1])
    return next((z1 for z0, z1 in merged if z0 <= z + _CROSS_TOL_M < z1), None)


def lane_surface(flights, key: str, probe, z: float, riser: float) -> float | None:
    """The other lane's walking surface under ``probe``, or ``None`` if none is there.

    Each pair of consecutive stations bounds one tread (or a landing) at the lower station's
    elevation. A surface more than a riser above the nosing is no fall at all.
    """
    from shapely.geometry import Polygon

    hits = []
    for other, stations in flights.items():
        if other == key:
            continue
        for (a0, b0, z0), (a1, b1, _z1) in zip(stations, stations[1:], strict=False):
            quad = Polygon([a0, b0, b1, a1])
            if quad.is_valid and quad.area > 1e-9 and quad.covers(probe):
                hits.append(z0)
    if not hits:
        return None
    lower = [h for h in hits if h <= z + riser + 1e-9]
    return max(lower) if lower else z
