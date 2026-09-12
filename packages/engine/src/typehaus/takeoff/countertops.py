"""Countertops by material — the fabricator's order, in the square feet they quote.

One row per material, because that is the unit of a countertop purchase: a slab yard prices
a material at $/SF fabricated and installed, and the number of pieces it is cut into is the
fabricator's problem, not a line on the estimate. The rows carry which runs they came from
so a reader can see the derivation rather than take the total on faith.

Waste is deliberately NOT applied here, unlike ``floor_finishes`` and ``wood_surfaces``.
A slab yard quotes the finished square footage of the top; the yield loss between a 57" x
120" slab and a 25"-deep strip is inside the fabricated rate, and adding a percentage on top
of it would bill the same loss twice. Where a top's shape forces a jumbo slab that is a
*rate* question (the material costs more), which is exactly what the price file's
qualified-key escape hatch is for.
"""

from __future__ import annotations

from collections import defaultdict

from typehaus.resolve.model import ResolvedModel

_M2_TO_FT2 = 10.7639104
_M_TO_IN = 39.37007874


def countertop_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """One row per countertop material: net area, run length, and the tops it covers."""
    area: dict[str, float] = defaultdict(float)
    length: dict[str, float] = defaultdict(float)
    tops: dict[str, list[str]] = defaultdict(list)
    thicknesses: dict[str, set[float]] = defaultdict(set)
    for top in model.countertops:
        area[top.material_ref] += top.area_m2
        length[top.material_ref] += top.length_m
        tops[top.material_ref].append(top.tag)
        thicknesses[top.material_ref].add(round(top.thickness_m * _M_TO_IN, 3))

    materials = {material.tag: material for material in model.plan.library.materials}
    rows: list[dict[str, object]] = []
    for ref in sorted(area):
        material = materials.get(ref)
        rows.append({
            "material": ref,
            "name": material.name if material is not None else ref,
            "net_area_sqft": round(area[ref] * _M2_TO_FT2, 2),
            "length_ft": round(length[ref] / 0.3048, 2),
            # A run of one thickness is the normal case; a set says outright that this row
            # mixes two, which is a fabrication fact and not a rounding artefact.
            "thickness_in": sorted(thicknesses[ref]),
            "tops": sorted(tops[ref]),
        })
    return rows
