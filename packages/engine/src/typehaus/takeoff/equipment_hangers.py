"""A hung machine's trapeze, off ``ResolvedModel.equipment_hangers``: rod and strut by the
foot (pieces counted beside), one lag per bridge seat. Priced in ``[equipment_hangers]``
keyed on the product tag; a rod or strut row says ``unit = "LF"``."""

from __future__ import annotations

from typing import Any

_FT = 0.3048


def equipment_hanger_takeoff(model: Any) -> list[dict[str, object]]:
    rows: dict[tuple[str, str], dict[str, Any]] = {}

    def add(item: str, product: str, tag: str, count: int, length_m: float = 0.0) -> None:
        row = rows.setdefault((item, product), {"item": item, "product": product, "count": 0,
                                                "length_ft": 0.0, "tags": set()})
        row["count"] += count
        row["length_ft"] = round(row["length_ft"] + length_m / _FT, 2)
        row["tags"].add(tag)

    struts: set[tuple[str, int]] = set()
    for rod in getattr(model, "equipment_hangers", ()):
        tag = rod.equipment_tag
        add("rod", rod.rod_product_ref, tag, 1, rod.rod_length_m)
        if (tag, rod.strut) not in struts:
            struts.add((tag, rod.strut))
            add("strut", rod.strut_product_ref, tag, 1, rod.strut_length_m)
        if rod.bridge:
            add("strut", rod.strut_product_ref, tag, 1, rod.bridge_length_m)
            add("fixing", rod.fixing_product_ref, tag, len(rod.bridge))
    return [{**row, "tags": sorted(row["tags"])} for _, row in sorted(rows.items())]
