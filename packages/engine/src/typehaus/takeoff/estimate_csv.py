"""The estimate as one flat CSV — the contractor-intake artifact.

RSMeans Online and Craftsman Cloud both accept CSV/Excel alongside their AI PDF upload, and
what their parsers want is exactly this: one clean row per item, each carrying a code, a
unit, a quantity and a price. Buildertrend and a QuickBooks job-cost import read the same
shape.

The column set is fixed and authored here (:data:`ESTIMATE_COLUMNS`) rather than derived
from whatever keys happen to be present, so adding a field to the estimate payload cannot
silently widen a file that somebody's import mapping is pinned to.

Actual-vs-estimated rides in the last two columns, read from ``costs.toml`` through the same
``(section, key)`` join everything else uses — which is what lets the file round-trip:
export, edit ``actual_cost`` in a spreadsheet, and ``haus costs import`` reads it back.
"""

from __future__ import annotations

from typing import Any

from typehaus.takeoff.costs import CostsState

#: One row per priced BOM line. Order is the contract — see the module docstring.
ESTIMATE_COLUMNS = (
    "nahb_code", "csi_code", "trade", "section", "key", "description",
    "quantity", "unit", "waste_pct", "order_quantity", "basis",
    "unit_price_low", "unit_price_high",
    "material_low", "material_high", "labour_low", "labour_high",
    "total_low", "total_high", "actual_cost", "paid",
)


#: Columns summed when two estimate rows share one ``(section, key)``.
_ADDITIVE = ("quantity", "order_quantity", "total_low", "total_high",
             "material_low", "material_high", "labour_low", "labour_high")


def estimate_rows(estimate: dict[str, Any],
                  state: CostsState | None = None) -> list[dict[str, Any]]:
    """Flatten ``estimate_costs``'s nested payload into CSV rows, deterministically sorted.

    **One row per ``(section, key)``.** The estimate payload can carry several rows under
    one key — ``structural_solids`` bills three different assemblies as ``concrete/column``
    — but ``(section, key)`` is the join every other cost surface uses: it is what
    ``costs.toml`` files an ``actual_cost`` under and what ``haus costs import`` reads back.
    Emitting the un-aggregated rows would produce a file whose lines cannot be written back
    unambiguously, so they are summed here and their descriptions merged.

    Sorted by ``(section, key)`` rather than left in payload order: the payload's order is
    ``ESTIMATE_PLANS``' order, which is authored for reading, and a re-export after an
    unrelated plan edit should diff as the rows that changed and nothing else.
    """
    entries = (state.entries if state is not None else {})
    merged: dict[tuple[str, str], dict[str, Any]] = {}
    descriptions: dict[tuple[str, str], list[str]] = {}
    for section, body in estimate.get("sections", {}).items():
        section_entries = entries.get(section, {})
        for row in body.get("rows", []):
            entry = section_entries.get(row["key"])
            built = {
                "nahb_code": row.get("nahb_code"),
                "csi_code": row.get("csi_code"),
                "trade": row.get("trade"),
                "section": section,
                "key": row["key"],
                "description": row.get("description"),
                "quantity": row["quantity"],
                "unit": row["unit"],
                "waste_pct": row.get("waste_pct", 0.0),
                "order_quantity": row.get("order_quantity", row["quantity"]),
                "basis": row.get("basis"),
                "unit_price_low": row["unit_price"]["low"],
                "unit_price_high": row["unit_price"]["high"],
                # Blank, not zero, where the split is unknown: an ``installed`` row with no
                # declared split has no material figure, and a 0 would read as "free".
                **_split_columns(row),
                "total_low": row["cost"]["low"],
                "total_high": row["cost"]["high"],
                "actual_cost": getattr(entry, "actual_cost", None),
                "paid": getattr(entry, "paid", False),
            }
            slot = (section, row["key"])
            descriptions.setdefault(slot, [])
            if built["description"] and built["description"] not in descriptions[slot]:
                descriptions[slot].append(built["description"])
            if slot not in merged:
                merged[slot] = built
                continue
            first = merged[slot]
            for column in _ADDITIVE:
                left, right = first.get(column), built.get(column)
                # A blank material/labour column means "this row is merged, the split is
                # not known". Adding a known half to an unknown one would report a split
                # that covers only part of the money, so the pair goes blank instead.
                first[column] = None if left is None or right is None else round(
                    left + right, 2)
            first["unit_price_low"] = min(first["unit_price_low"], built["unit_price_low"])
            first["unit_price_high"] = max(first["unit_price_high"], built["unit_price_high"])
    for slot, row in merged.items():
        names = descriptions.get(slot, [])
        row["description"] = "; ".join(names[:4]) + (" …" if len(names) > 4 else "")
    return [merged[slot] for slot in sorted(merged)]


def _split_columns(row: dict[str, Any]) -> dict[str, Any]:
    merged = row.get("merged") or {"low": 0.0, "high": 0.0}
    is_merged = bool(merged.get("low") or merged.get("high"))
    material = row.get("material") or {}
    labour = row.get("labour") or {}
    if is_merged:
        return {"material_low": None, "material_high": None,
                "labour_low": None, "labour_high": None}
    return {"material_low": material.get("low"), "material_high": material.get("high"),
            "labour_low": labour.get("low"), "labour_high": labour.get("high")}
