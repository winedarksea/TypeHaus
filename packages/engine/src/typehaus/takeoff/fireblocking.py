"""Firestop sealant by the lineal foot of fireblock penetration (IRC R302.11 item 4).

The perimeters are derived per resolve (``resolve/opening_fireblock.py``); the sheet itself
bills in ``sheet_goods`` under scope ``fireblock``.
"""

from __future__ import annotations

from typehaus.resolve.model import ResolvedModel

_M_TO_FT = 3.280839895013123


def fireblock_sealant_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """One row per sealant material: penetrations counted, annulus perimeter in LF."""
    rows: dict[str, dict[str, object]] = {}
    for block in model.fireblocks:
        material = getattr(model.plan.by_tag(block.opening_tag), "fireblock_sealant", None)
        if not material or not block.penetrations:
            continue
        row = rows.setdefault(material, {"material": material, "count": 0,
                                         "length_m": 0.0, "tags": set()})
        row["count"] = int(row["count"]) + len(block.penetrations)
        row["length_m"] = float(row["length_m"]) + sum(p for _, p in block.penetrations)
        row["tags"].add(block.opening_tag)  # type: ignore[union-attr]
    return [{"material": m, "count": r["count"],
             "length_ft": round(float(r["length_m"]) * _M_TO_FT, 1),
             "tags": sorted(r["tags"])}  # type: ignore[arg-type]
            for m, r in sorted(rows.items())]
