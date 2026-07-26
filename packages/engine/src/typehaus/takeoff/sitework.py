"""Sub-footing bedding: aggregate by the cubic yard, geotextile and drain tile by the foot.

``ResolvedFootingBedding`` carries an outline, an excavation depth, an aggregate spec, a
geotextile flag and a ``DrainTile``. The browser BOM bills these; the engine did not, so
``haus takeoff`` and the browser disagreed about whether the stone under every footing on
the project was part of the order.
"""

from __future__ import annotations

from collections import defaultdict

from typehaus.resolve.model import ResolvedModel

_M_TO_FT = 3.280839895
_M3_TO_CY = 1.30795062
_M2_TO_FT2 = 10.7639104


def _ring_area(ring) -> float:
    """Shoelace area of a closed ring, unsigned."""
    if len(ring) < 3:
        return 0.0
    total = 0.0
    for (x0, y0), (x1, y1) in zip(ring, list(ring[1:]) + [ring[0]]):
        total += x0 * y1 - x1 * y0
    return abs(total) / 2.0


def _ring_perimeter(ring) -> float:
    if len(ring) < 2:
        return 0.0
    return sum(((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
               for (x0, y0), (x1, y1) in zip(ring, list(ring[1:]) + [ring[0]]))


def footing_bedding_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """One row per aggregate spec: stone by the yard, fabric by the square foot, tile by LF.

    Grouped on the aggregate string because that is the product being ordered — two beddings
    of the same stone are one delivery whatever they sit under. Geotextile area is the
    excavation's plan area plus its walls, which is what actually gets lined; drain tile runs
    the bedding's perimeter.
    """
    groups: dict[tuple[str, bool, bool], dict[str, object]] = {}
    for bedding in model.footing_beddings:
        area = _ring_area(bedding.outline)
        depth = max(bedding.z1_m - bedding.z0_m, 0.0)
        perimeter = _ring_perimeter(bedding.outline)
        key = (bedding.aggregate, bedding.geotextile, bedding.drain_tile)
        entry = groups.setdefault(key, {
            "volume_m3": 0.0, "fabric_m2": 0.0, "tile_m": 0.0, "count": 0, "tags": [],
        })
        entry["volume_m3"] += area * depth
        # The fabric lines the bottom and the cut faces — a no-slip liner that stopped at the
        # bottom would let the stone migrate into the sidewall it is there to separate from.
        entry["fabric_m2"] += area + perimeter * depth if bedding.geotextile else 0.0
        entry["tile_m"] += perimeter if bedding.drain_tile else 0.0
        entry["count"] += 1
        entry["tags"].append(bedding.tag)

    rows = []
    for (aggregate, geotextile, drain_tile), entry in sorted(groups.items()):
        rows.append({
            "aggregate": aggregate,
            "beddings": int(entry["count"]),
            "volume_cubic_yards": round(float(entry["volume_m3"]) * _M3_TO_CY, 2),
            "geotextile": geotextile,
            "geotextile_sqft": round(float(entry["fabric_m2"]) * _M2_TO_FT2, 1),
            "drain_tile": drain_tile,
            "drain_tile_ft": round(float(entry["tile_m"]) * _M_TO_FT, 1),
            "tags": sorted(entry["tags"]),
        })
    return rows
