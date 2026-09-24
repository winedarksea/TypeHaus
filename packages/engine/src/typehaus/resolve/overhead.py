"""What stands plumb over a plan point — the one probe a stair's headroom and a pendant's hang
both read, so the two cannot disagree about what is overhead.

By default it is structure only: floor decks (outside their voids) at their deepest framing,
roof planes at their structural underside, soffit faces. That is what R311.7.2 measures.
``finishes=True`` adds each room's flat finished ceiling, which is what a canopy screws to.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from shapely.geometry import Point, Polygon

from typehaus.resolve.roof_geometry import roof_underside_at

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel

#: Plan inset on every cover polygon, so a point on a deck's edge is not "under" it.
PLAN_EPS_M = 0.005
#: A surface must clear the probe's z by this much to count as over it.
OVERHEAD_EPS_M = 0.001


@dataclass(frozen=True)
class Overhead:
    z_m: float
    tag: str


class OverheadIndex:
    """Cover polygons built once; probe as many points as needed."""

    def __init__(self, model: ResolvedModel, *, finishes: bool = False) -> None:
        self._model = model
        self._flat: list[tuple[Any, float, str]] = []
        for floor in model.floors:
            if not floor.deck_outline:
                continue
            underside = min([member.z0_m for member in floor.members] + [floor.deck_z0_m])
            self._add_flat(Polygon(floor.deck_outline,
                                   holes=[list(void) for void in floor.deck_voids]),
                           underside, floor.tag)
        for soffit in model.soffits:
            if soffit.outline:
                self._add_flat(Polygon(soffit.outline), soffit.z0_m, soffit.tag)
        if finishes:
            for ceiling in model.ceilings:
                if ceiling.z0_m is not None and len(ceiling.outline) >= 3:
                    self._add_flat(Polygon(ceiling.outline), ceiling.z0_m, ceiling.tag)
        self._roofs = [(Polygon(roof.footprint), roof) for roof in model.roofs
                       if roof.footprint]

    def _add_flat(self, polygon: Any, z_m: float, tag: str) -> None:
        cover = polygon.buffer(-PLAN_EPS_M)
        if not cover.is_empty:
            self._flat.append((cover, z_m, tag))

    @property
    def has_roof(self) -> bool:
        return bool(self._roofs)

    def covers(self, x: float, y: float) -> bool:
        """Anything at all over this point in plan, at any height."""
        point = Point(x, y)
        return (any(p.contains(point) for p, _, _ in self._flat)
                or any(p.contains(point) for p, _ in self._roofs))

    def lowest_above(self, x: float, y: float, z_m: float) -> Overhead | None:
        """The lowest surface over ``(x, y)`` that is higher than ``z_m``."""
        point = Point(x, y)
        lowest: Overhead | None = None
        for polygon, underside, tag in self._flat:
            if (underside > z_m + OVERHEAD_EPS_M and polygon.contains(point)
                    and (lowest is None or underside < lowest.z_m)):
                lowest = Overhead(underside, tag)
        for polygon, roof in self._roofs:
            if polygon.contains(point):
                underside = roof_underside_at(self._model, roof, (x, y))
                if underside > z_m + OVERHEAD_EPS_M and (
                        lowest is None or underside < lowest.z_m):
                    lowest = Overhead(underside, roof.tag)
        return lowest
