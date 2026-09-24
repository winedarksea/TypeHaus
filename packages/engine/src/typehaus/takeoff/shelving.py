"""Factory shelf stock by material, with the cut sizes the supplier must see.

``ShelfBank`` is geometry first: it says how many boards fit a host and what each board
finishes to.  When those boards are bought rather than custom-milled, this module turns that
geometry into the material order.  Host-included shelves stay with their cabinet price and
custom-milled shelves stay in ``haus millwork``; neither belongs here.
"""

from __future__ import annotations

import math
from collections import defaultdict

from typehaus.resolve.model import ResolvedModel

_M2_TO_FT2 = 10.7639104
_M_TO_IN = 39.37007874
_WASTE = 0.10


def shelving_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Separately purchased shelf stock, grouped by material/product.

    Price rows are material keyed, so the order quantity is aggregated before waste and
    rounding.  The nested ``cuts`` stay alongside it for a supplier who needs the actual
    board sizes rather than only the square footage.
    """
    materials = {material.tag: material for material in model.plan.library.materials}
    groups: dict[str, dict[str, object]] = {}
    cut_groups: dict[str, dict[tuple[float, float, float], dict[str, object]]] = defaultdict(dict)

    for bank in model.shelf_banks:
        if bank.procurement != "purchased_separately":
            continue
        material = materials.get(bank.material_ref)
        group = groups.setdefault(bank.material_ref, {
            "material": bank.material_ref,
            "known": material is not None,
            "pieces": 0,
            "net_area_sqft": 0.0,
            "tags": set(),
        })
        for shelf in bank.shelves:
            if shelf.depth_m is None:
                continue
            thickness = round(bank.thickness_m * _M_TO_IN, 3)
            width = round(shelf.width_m * _M_TO_IN, 3)
            depth = round(shelf.depth_m * _M_TO_IN, 3)
            key = (thickness, width, depth)
            cut = cut_groups[bank.material_ref].setdefault(key, {
                "pieces": 0,
                "finished_thickness_in": thickness,
                "finished_width_in": width,
                "finished_depth_in": depth,
                "tags": set(),
            })
            pieces = shelf.count
            group["pieces"] = int(group["pieces"]) + pieces
            group["net_area_sqft"] = float(group["net_area_sqft"]) + (
                pieces * shelf.width_m * shelf.depth_m * _M2_TO_FT2)
            tags = group["tags"]
            cut_tags = cut["tags"]
            assert isinstance(tags, set) and isinstance(cut_tags, set)
            tags.add(bank.tag)
            cut_tags.add(bank.tag)
            cut["pieces"] = int(cut["pieces"]) + pieces

    rows: list[dict[str, object]] = []
    for material_ref in sorted(groups):
        group = groups[material_ref]
        net = float(group["net_area_sqft"])
        cuts = []
        for key in sorted(cut_groups[material_ref]):
            cut = cut_groups[material_ref][key]
            cuts.append({**cut, "tags": sorted(cut["tags"])})
        rows.append({
            "material": material_ref,
            "known": group["known"],
            "pieces": group["pieces"],
            "net_area_sqft": round(net, 1),
            "waste_pct": _WASTE * 100.0,
            "order_area_sqft": float(math.ceil(net * (1.0 + _WASTE) - 1e-9)),
            "cuts": cuts,
            "tags": sorted(group["tags"]),
        })
    return rows
