"""Stock inventory for the formed cladding trim that has been resolved."""

from __future__ import annotations

from typehaus.library.trim.metal_sales import PROFILES
from typehaus.resolve.model import ResolvedModel


def cladding_trim_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Group individual cut pieces by catalog part and purchased stock length.

    A piece is ordered independently; combining short cuts into a shop cutting plan
    requires an explicit packing calculation and is not assumed here.
    """
    groups: dict[tuple[str, float], dict[str, object]] = {}
    for solid in model.solids:
        if solid.category != "cladding_trim":
            continue
        profile = PROFILES.get(solid.product or "")
        if profile is None or solid.trim_length_m is None or solid.trim_stock_length_in is None:
            raise ValueError(f"{solid.tag}: cladding trim lacks profile or stock metadata")
        stock = solid.trim_stock_length_in
        if (stock not in profile.stock_lengths_in or solid.trim_length_m <= 0
                or solid.trim_length_m > stock * 0.0254 + 1e-9):
            raise ValueError(f"{solid.tag}: invalid cut or stock length")
        matches = [number for gauge, finish, length, number in profile.part_numbers
                   if gauge == 24 and length == stock and finish == "PVDF"]
        part = matches[0] if matches else solid.product
        key = (str(part), stock)
        if key not in groups:
            groups[key] = {"part": part, "profile": profile.name, "stock_length_in": stock,
                           "count": 0, "cut_length_ft": 0.0, "tags": []}
        row = groups[key]
        row["count"] = int(row["count"]) + 1
        row["cut_length_ft"] = float(row["cut_length_ft"]) + solid.trim_length_m / 0.3048
        row["tags"].append(solid.tag)
    for row in groups.values():
        row["cut_length_ft"] = round(float(row["cut_length_ft"]), 2)
        row["quantity"] = row["count"]
        row["unit"] = "ea"
        row["tags"].sort()
    return [groups[key] for key in sorted(groups)]
