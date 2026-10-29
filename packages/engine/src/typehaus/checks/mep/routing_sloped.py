"""The ceiling plane of a ``FollowRoof`` room, for ``mep.run_in_finished_volume``.

A room whose ceiling follows its roof has no flat plane; its finished ceiling is the roof
structure's underside less the lining hung on it. A gable folds at the ridge, so a segment
crossing it is cut there and each half meets a plane that is linear along it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from shapely.geometry import LineString, Polygon

from typehaus.model.refs import FollowRoof
from typehaus.resolve.ceiling_over import room_roof_over
from typehaus.resolve.model import ResolvedCeiling, ResolvedModel, ResolvedRoof
from typehaus.resolve.roof_geometry import (
    MIN_COUNTABLE_HEAD_M,
    roof_headroom_region,
    roof_height_at,
    roof_ridge_coordinate,
    roof_slope_coordinate,
    roof_structure_depth_m,
)

#: ``(start xy, z at start, z at end, segment, plane at start, plane at end)``
Piece = tuple[tuple[float, float], float, float, LineString, float, float]


@dataclass(frozen=True)
class SlopedPlane:
    """A finished ceiling that follows ``roof``: its plane sits ``drop_m`` under the deck."""

    roof: ResolvedRoof
    drop_m: float

    def z_at(self, point: tuple[float, float]) -> float:
        return roof_height_at(self.roof, point) - self.drop_m

    def standing_part(self, outline: Polygon, floor_m: float) -> Any:
        """``outline`` where the finished ceiling clears R304.3's 5'-0" over the floor.

        Under that rake nobody stands, so a run lying on the floor there is in the eave and
        not in the room — the same line ``room_head_limited_area_m2`` uses for area.
        """
        region = roof_headroom_region(self.roof, floor_m, MIN_COUNTABLE_HEAD_M + self.drop_m)
        return outline.intersection(region)

    def pieces(self, a: tuple[float, float], b: tuple[float, float], za: float,
               zb: float) -> list[Piece]:
        """The segment cut at the ridge, each piece with the plane's height at its ends."""
        ridge = roof_ridge_coordinate(self.roof)
        cuts = [0.0, 1.0]
        if ridge is not None:
            ca, cb = roof_slope_coordinate(self.roof, a), roof_slope_coordinate(self.roof, b)
            if (ca - ridge) * (cb - ridge) < 0:
                cuts.insert(1, (ridge - ca) / (cb - ca))
        out: list[Piece] = []
        for t0, t1 in zip(cuts, cuts[1:], strict=False):
            p0 = (a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0)
            p1 = (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)
            if p0 == p1:
                continue
            out.append((p0, za + (zb - za) * t0, za + (zb - za) * t1, LineString([p0, p1]),
                        self.z_at(p0), self.z_at(p1)))
        return out


def sloped_plane(model: ResolvedModel, plan: Any, ceiling: ResolvedCeiling) -> SlopedPlane | None:
    """The plane under a ``FollowRoof`` ceiling, or ``None`` when its roof does not resolve."""
    room = next((e for e in plan.storey_elements(ceiling.storey)
                 if getattr(e, "tag", None) == ceiling.room_ref
                 and isinstance(getattr(e, "ceiling", None), FollowRoof)), None)
    source = room_roof_over(plan, ceiling.storey, room) if room is not None else None
    roof = next((r for r in model.roofs if source is not None and r.tag == source.tag), None)
    if roof is None or not roof.footprint:
        return None
    lining = sum(layer.thickness.meters for layer in ceiling.layers)
    return SlopedPlane(roof, roof_structure_depth_m(model, roof) + lining)
