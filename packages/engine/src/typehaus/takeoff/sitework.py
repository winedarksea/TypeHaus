"""Sub-footing bedding: aggregate by the cubic yard, geotextile and drain tile by the foot.

``ResolvedFootingBedding`` carries an outline, an excavation depth, an aggregate spec, a
geotextile flag and a ``DrainTile``. The browser BOM bills these; the engine did not, so
``haus takeoff`` and the browser disagreed about whether the stone under every footing on
the project was part of the order.
"""

from __future__ import annotations

from collections import defaultdict

from typehaus.quantities import M_PER_IN
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
    groups: dict[tuple[str, bool, tuple], dict[str, object]] = {}
    for bedding in model.footing_beddings:
        area = _ring_area(bedding.outline)
        depth = max(bedding.z1_m - bedding.z0_m, 0.0)
        perimeter = _ring_perimeter(bedding.outline)
        key = (bedding.aggregate, bedding.geotextile, _tile_key(bedding))
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
    for (aggregate, geotextile, tile_key), entry in sorted(groups.items()):
        has_tile, diameter_m, material, sock, discharge = tile_key
        diameter_m = diameter_m if diameter_m >= 0.0 else None
        rows.append({
            "aggregate": aggregate,
            "beddings": int(entry["count"]),
            "volume_cubic_yards": round(float(entry["volume_m3"]) * _M3_TO_CY, 2),
            "geotextile": geotextile,
            "geotextile_sqft": round(float(entry["fabric_m2"]) * _M2_TO_FT2, 1),
            "drain_tile": has_tile,
            "drain_tile_ft": round(float(entry["tile_m"]) * _M_TO_FT, 1),
            # What is actually being ordered. A row that says only "1,240 ft of drain tile"
            # cannot be priced or bought: 4" sock-wrapped HDPE to daylight and 6" bare pipe
            # to a sump are two deliveries, and grouping them together said they were one.
            "drain_tile_diameter_in": (round(diameter_m / M_PER_IN, 2)
                                       if diameter_m is not None else None),
            "drain_tile_material": material,
            "drain_tile_sock": sock,
            "drain_tile_discharge": discharge,
            "tags": sorted(entry["tags"]),
        })
    return rows


def _tile_key(bedding) -> tuple:
    """The drain-tile group key: the bool, then the product spec where one is authored.

    Every slot is the same type across beddings so the row sort never compares a ``None``
    diameter against a real one; an unspecified size is ``-1.0`` here and ``None`` in the row.
    """
    if not bedding.drain_tile:
        return (False, -1.0, "", False, "")
    spec = bedding.drain_tile_spec
    if spec is None:
        return (True, -1.0, "", False, "")
    return (True, round(spec.diameter_m, 6), spec.material, spec.sock, spec.discharge or "")
