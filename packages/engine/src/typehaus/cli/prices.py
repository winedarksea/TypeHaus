"""Pricing a bill of materials — the join, the roll-up, and what it refuses to guess.

Split from :mod:`typehaus.cli.price_file`, which owns the *file format*: this module owns
the *join* between a ``prices.toml`` and a ``bill_of_materials`` payload, and the two change
for different reasons. Everything the old single module exported is still importable from
here, so ``from typehaus.cli.prices import ...`` keeps working for every caller.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, Optional

from typehaus.cli.price_file import (  # noqa: F401  (re-exported: this is the public name)
    _SECTIONS,
    BASES,
    INSTALLED,
    LABOUR,
    MATERIAL,
    PRICES_FILENAME,
    WASTE_IN_QUANTITY,
    ZERO,
    Adjustments,
    PriceRange,
    Prices,
    UnitPrice,
    _dollars,
    _price,
    load_prices,
    waste_in_quantity,
)

#: The re-export surface. ``price_file`` owns the file format and this module owns the join,
#: but every existing caller says ``from typehaus.cli.prices import ...`` — naming the names
#: here keeps that path a declared contract rather than an implicit one.
__all__ = [
    "BASES", "INSTALLED", "LABOUR", "MATERIAL", "PRICES_FILENAME", "Adjustments",
    "ESTIMATE_PLANS", "EXCLUDED_FROM_TOTAL", "PriceRange", "Prices", "UnitPrice",
    "WASTE_IN_QUANTITY", "ZERO", "estimate_costs", "load_prices", "waste_in_quantity",
]

#: BOM fields that read as a human description, most specific first. A CSV row that says
#: only "framing / 2x6" is not something a supplier can quote from.
_DESCRIPTION_FIELDS = ("description", "scope", "name", "label", "product", "assembly")


def _describe(row: Mapping[str, object], section: str, key: str) -> str:
    for field_name in _DESCRIPTION_FIELDS:
        value = row.get(field_name)
        if isinstance(value, str) and value:
            return value
    types = row.get("types")
    if isinstance(types, (list, tuple)) and types:
        return ", ".join(str(t) for t in types)
    return f"{section.replace('_', ' ')} · {key}"


def _sum(ranges: Iterable[PriceRange]) -> PriceRange:
    total = ZERO
    for item in ranges:
        total = total.plus(item)
    return total


#: How each price section joins the BOM, authored once: ``(estimate section, bom key,
#: price key field, quantity field, unit)``. The price table itself is the ``Prices``
#: attribute named by the section. Both :func:`estimate_costs` and the cost-tracking
#: payload (``takeoff/costs.py``) read this — the ``(section, key)`` a paid check-off is
#: stored under has to be the *same* join the estimate prices, or the two views drift.
#:
#: ``waste_in_quantity`` is derived from :data:`WASTE_IN_QUANTITY` rather than repeated as a
#: sixth tuple element: one list, one place to be wrong.
ESTIMATE_PLANS = (
    ("framing", "framing_by_size", "profile", "order_length_ft", "LF"),
    ("sheet_goods", "sheet_goods", "material", "sheets_4x8", "sheets"),
    ("hardware", "hardware", "part_number", "count", "ea"),
    ("concrete", "structural_solids", "category", "volume_cubic_yards", "cy"),
    ("floor_heat", "floor_heat", "system", "wire_length_ft", "LF"),
    ("placeables", "placeables", "type", "count", "ea"),
    # Priced on the *order* quantity, not the net area: a finish is bought with its
    # waste, and pricing net area would under-cost every plank and tile room.
    ("floor_finishes", "floor_finishes", "finish", "order_area_sqft", "SF"),
    ("envelope_layers", "envelope_layers", "material", "net_area_sqft", "SF"),
    # Order quantity like floor_finishes (wood is bought with its waste). Timber rows
    # carry no order_area_sqft and price as 0 here — they bill via structural_solids.
    ("wood_surfaces", "wood_surfaces", "material", "order_area_sqft", "SF"),
    ("openings", "openings", "type", "count", "ea"),
    ("footing_bedding", "footing_bedding", "aggregate", "volume_cubic_yards", "cy"),
    ("pipe_runs", "pipe_runs", "system", "length_ft", "LF"),
    ("ducts", "ducts", "system", "length_ft", "LF"),
    ("sleeves", "sleeves", "sleeve_diameter_in", "count", "ea"),
    ("conduit", "conduit", "trade_size_in", "length_ft", "LF"),
    ("plumbing_specialties", "plumbing_specialties", "kind", "count", "ea"),
    ("install_parts", "install_parts", "part", "count", "ea"),
    ("pipe_insulation", "pipe_insulation", "spec", "length_ft", "LF"),
    ("edge_trim", "edge_trim", "category", "length_ft", "LF"),
    # Placed by the yard, keyed on the assembly — see the field comment on ``Prices``.
    ("wall_structure", "wall_structure", "assembly", "volume_cubic_yards", "cy"),
    ("railings", "railings", "type", "length_ft", "LF"),
    ("drainage", "drainage", "category", "length_ft", "LF"),
    # Reads the *same* BOM rows as ``placeables`` — see ``EXCLUDED_FROM_TOTAL``.
    ("furnishings", "placeables", "type", "count", "ea"),
)

#: Sections priced and reported but held out of the construction total. They stay in
#: ``sections`` (with ``in_total: False``) and roll up into ``excluded_total`` /
#: ``grand_total``, so nothing is hidden — only re-filed.
EXCLUDED_FROM_TOTAL = frozenset({"furnishings"})

#: The price table an estimate section reads: every section except concrete (which prices
#: the ``structural_solids`` rows) shares its table's name.
_PLAN_TABLE = {name: name for name, *_ in ESTIMATE_PLANS}



def estimate_costs(bom: dict[str, Any], prices: Prices,
                   areas: Optional[Mapping[str, float]] = None) -> dict[str, Any]:
    """Price a :func:`typehaus.takeoff.bill_of_materials` payload against ``prices``.

    Returns ``{"sections": {name: {"rows": [...], "subtotal": {...}}}, "total": {...},
    "unpriced": [...]}}``. Sections the BOM has no rows for are omitted; rows without a
    price land in ``unpriced`` so the total is honest about what it excludes.

    ``total`` is the *construction* total: sections in :data:`EXCLUDED_FROM_TOTAL` are
    priced and reported like any other, then summed into ``excluded_total`` instead.
    ``grand_total`` is the two together, for the reader who wants one number.

    Three further roll-ups ride alongside, each of them opt-in and each zero unless the
    house's ``prices.toml`` asks for it (decision #28 — the house owns its numbers):

    - ``basis``: material / labour / merged subtotals, per section and overall. A row is
      merged when its price is ``installed`` with no declared split, and a merged number is
      **never divided**.
    - ``bid``: the ``net -> waste -> ordered -> contingency -> markup -> tax -> total``
      ladder from :mod:`typehaus.takeoff.cost_model`, each stage its own reported line.
    - ``per_sf``: $/sf against the ``areas`` mapping the caller supplies (conditioned and
      gross, from ``server/space_summary.build_space_summary``). Absent when ``areas`` is.
    """
    from typehaus.takeoff.cost_codes import cost_code
    from typehaus.takeoff.cost_model import (
        apply_waste,
        buckets_as_dict,
        empty_buckets,
        per_sf,
        roll_up,
        split_by_basis,
    )
    sections: dict[str, dict[str, Any]] = {}
    total = ZERO
    excluded_total = ZERO
    # A BOM table may feed more than one price section (``placeables`` feeds both
    # [placeables] and [furnishings]), so a miss is only really unpriced when *no* section
    # reading that table priced the key. Collect misses first, then drop the ones another
    # plan caught — otherwise every furnished row would read as unpriced in the other.
    priced: dict[str, set[str]] = {}
    misses: list[tuple[str, dict[str, Any]]] = []
    section_buckets: dict[str, dict[str, PriceRange]] = {}
    section_waste: dict[str, PriceRange] = {}
    adjustments = prices.adjustments
    for name, bom_key, key_field, quantity_field, unit in ESTIMATE_PLANS:
        table = getattr(prices, _PLAN_TABLE[name])
        rows = []
        buckets = empty_buckets()
        waste_sum = ZERO
        for row in bom.get(bom_key, []) or []:
            key = str(row.get(key_field))
            quantity = float(row.get(quantity_field) or 0.0)
            price = table.get(key)
            if price is None:
                if quantity:
                    misses.append((bom_key, {"section": name, "key": key,
                                             "quantity": round(quantity, 2), "unit": unit}))
                continue
            priced.setdefault(bom_key, set()).add(key)
            # Rounded to the cent *before* it is split or summed, so the three basis
            # subtotals, the section subtotal and the grand total are all sums of the same
            # numbers. Splitting the unrounded value instead lands the bid ladder a cent
            # away from the total printed above it.
            cost = PriceRange(**price.times(quantity).as_dict())
            parts = split_by_basis(cost, price)
            for bucket, value in parts.items():
                buckets[bucket] = buckets[bucket].plus(value)
            waste = apply_waste(name, key, cost, adjustments)
            waste_sum = waste_sum.plus(waste)
            code = cost_code(name, key, dict(prices.codes))
            rows.append({"key": key, "description": _describe(row, name, key),
                         "quantity": round(quantity, 2), "unit": unit,
                         "unit_price": price.as_dict(), "cost": cost.as_dict(),
                         "cost_fmt": cost.fmt(),
                         "basis": getattr(price, "basis", MATERIAL),
                         "material": parts[MATERIAL].as_dict(),
                         "labour": parts[LABOUR].as_dict(),
                         "merged": parts["merged"].as_dict(),
                         "waste_pct": round(adjustments.waste_rate(name, key), 4),
                         "waste_in_quantity": waste_in_quantity(name),
                         "order_quantity": round(quantity * (1.0 + (
                             0.0 if waste_in_quantity(name)
                             else adjustments.waste_rate(name, key))), 2),
                         **code.as_dict()})
        if rows:
            subtotal = _sum(PriceRange(r["cost"]["low"], r["cost"]["high"]) for r in rows)
            in_total = name not in EXCLUDED_FROM_TOTAL
            sections[name] = {"rows": rows, "subtotal": subtotal.as_dict(),
                              "subtotal_fmt": subtotal.fmt(), "in_total": in_total,
                              "basis": prices.basis.get(name, MATERIAL),
                              "basis_note": prices.basis_notes.get(name),
                              "basis_subtotals": buckets_as_dict(buckets),
                              "waste": waste_sum.as_dict(),
                              "waste_in_quantity": waste_in_quantity(name)}
            section_buckets[name] = buckets
            section_waste[name] = waste_sum
            if in_total:
                total = total.plus(subtotal)
            else:
                excluded_total = excluded_total.plus(subtotal)
    unpriced = [row for bom_key, row in misses
                if row["key"] not in priced.get(bom_key, ())]
    grand_total = total.plus(excluded_total)
    bid = roll_up(section_buckets, section_waste, adjustments, EXCLUDED_FROM_TOTAL)
    payload = {"sections": sections, "total": total.as_dict(), "total_fmt": total.fmt(),
               "excluded_sections": sorted(n for n in sections
                                           if n in EXCLUDED_FROM_TOTAL),
               "excluded_total": excluded_total.as_dict(),
               "excluded_total_fmt": excluded_total.fmt(),
               "grand_total": grand_total.as_dict(), "grand_total_fmt": grand_total.fmt(),
               "basis_declared": prices.basis_declared,
               "basis": dict(prices.basis), "basis_notes": dict(prices.basis_notes),
               "bid": bid,
               "unpriced": unpriced}
    if areas:
        payload["areas"] = dict(areas)
        payload["per_sf"] = {
            "total": per_sf(total.as_dict(), areas),
            "bid_total": per_sf(bid["total"], areas),
            "sections": {name: per_sf(body["subtotal"], areas)
                         for name, body in sections.items()},
        }
    return payload
