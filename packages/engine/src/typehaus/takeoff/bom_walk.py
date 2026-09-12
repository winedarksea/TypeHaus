"""One walk over the bill of materials, the way the estimate reads it.

``cli/prices.ESTIMATE_PLANS`` says which BOM table each estimate section prices, on which
key field and quantity field. Three consumers re-derived that walk on their own —
``takeoff/tasks`` (twice), ``takeoff/bid_package`` — and each could disagree about what a
row's key or tags were. This is the one walk; the others project it.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BomRow:
    """One BOM row under one estimate section, with the facts every consumer keys on."""

    section: str
    #: The bare price key (``slab``), what ``tasks.toml`` rows and check-offs name.
    key: str
    #: The qualified key (``slab:DECK_EPS_INT``), where the row carries qualifiers.
    qualified_key: str
    row: Mapping[str, Any]
    quantity: float
    unit: str
    tags: tuple[str, ...]
    material: str | None

    @property
    def bare_key(self) -> str:
        return self.key


def walk_bom(bom: Mapping[str, Any], *, every_section: bool = False) -> list[BomRow]:
    """Every BOM row under its estimate section, in ``ESTIMATE_PLANS`` order.

    Two estimate sections read the same table (``concrete``/``timber`` over
    ``structural_solids``, ``placeables``/``furnishings`` over ``placeables``). By default a
    table is walked ONCE, under the first section that names it — a bid package must hold
    each row exactly once. ``every_section=True`` is the estimate's own view, one entry per
    section, which is what the work packages have always seen.
    """
    from typehaus.cli.prices import ESTIMATE_PLANS, candidate_keys, qualifier_fields

    out: list[BomRow] = []
    seen_tables: set[str] = set()
    for section, bom_key, key_field, quantity_field, unit in ESTIMATE_PLANS:
        if not every_section and bom_key in seen_tables:
            continue
        seen_tables.add(bom_key)
        fields = qualifier_fields(section)
        for row in bom.get(bom_key, []) or []:
            key = str(row.get(key_field))
            qualifiers = tuple(row.get(f) for f in fields) if fields else None
            qualified = candidate_keys(key, qualifiers)[0] if qualifiers else key
            tags = row.get("tags")
            out.append(BomRow(
                section=section, key=key, qualified_key=qualified, row=row,
                quantity=float(row.get(quantity_field) or 0.0), unit=unit,
                tags=tuple(str(t) for t in tags) if isinstance(tags, (list, tuple)) else (),
                material=(str(row["structure_material"])
                          if row.get("structure_material") else None)))
    return out
