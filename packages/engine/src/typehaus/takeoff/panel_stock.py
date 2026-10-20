"""Whole-sheet purchasing from grain-aligned blanks, without exporting a cut schedule."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True)
class PanelStockConfig:
    width_in: float = 48
    length_in: float = 96
    saw_kerf_in: float = 0.125
    edge_trim_in: float = 0.25

    def __post_init__(self):
        if (self.saw_kerf_in < 0 or self.edge_trim_in < 0
                or min(self.width_in, self.length_in) <= 2 * self.edge_trim_in):
            raise ValueError("Panel stock must have positive usable dimensions and allowances")


DEFAULT_PANEL_STOCK = PanelStockConfig()


def _sheet_count(blanks: list[tuple[float, float]], stock: PanelStockConfig) -> int:
    """Conservative guillotine packing; lengths follow veneer grain, never rotated.

    Free rectangles are disjoint and each placement reserves kerf at both cut edges.
    This supplies a feasible order quantity, not a claim of the optimal nesting yield.
    """
    usable_width = stock.width_in - 2 * stock.edge_trim_in
    usable_length = stock.length_in - 2 * stock.edge_trim_in
    free_rectangles: list[tuple[float, float]] = []
    sheets = 0
    for width, length in sorted(blanks, key=lambda blank: blank[0] * blank[1], reverse=True):
        if width <= 0 or length <= 0 or width > usable_width or length > usable_length:
            raise ValueError(f"Panel blank {width:g} x {length:g} in does not fit "
                             f"{stock.width_in:g} x {stock.length_in:g} in stock "
                             "with grain and edge trim allowances")
        candidates = [
            (free_width * free_length, index)
            for index, (free_width, free_length) in enumerate(free_rectangles)
            if width <= free_width and length <= free_length
        ]
        if candidates:
            _, index = min(candidates)
            available_width, available_length = free_rectangles.pop(index)
        else:
            sheets += 1
            available_width, available_length = usable_width, usable_length
        remaining_width = available_width - width - stock.saw_kerf_in
        remaining_length = available_length - length - stock.saw_kerf_in
        # Retain the full-length side offcut so long narrow blanks remain possible.
        if remaining_width > 0:
            free_rectangles.append((remaining_width, available_length))
        if remaining_length > 0:
            free_rectangles.append((width, remaining_length))
    return sheets


def panel_order_rows(cut_rows: list[dict], stock: PanelStockConfig = DEFAULT_PANEL_STOCK
                     ) -> list[dict]:
    """One purchase row per material, with quantities for all installed occurrences."""
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in cut_rows:
        grouped[row["material"]].append(row)
    orders = []
    for material, rows in sorted(grouped.items()):
        blanks = [(row["finished_width_in"], row["finished_length_in"])
                  for row in rows for _ in range(row["pieces"])]
        sheets = _sheet_count(blanks, stock)
        first = rows[0]
        orders.append({
            "use": "plywood sheets", "stock_kind": "panel", "material": material,
            "species": first["species"], "sheets_to_order": sheets,
            "sheet_size": f'{stock.width_in:g}" x {stock.length_in:g}"',
            "nominal_stock": first["nominal_stock"],
            "panel_grade": first["panel_grade"], "panel_core": first["panel_core"],
            "finish": first["finish"], "grain_direction": "veneer grain along sheet length",
            "tags": sorted({tag for row in rows for tag in row["tags"]}),
            "stock_note": (
                f"Whole stock sheets; {stock.saw_kerf_in:g} in saw kerf, "
                f"{stock.edge_trim_in:g} in edge trim per side. "
                "Grain-aligned rectangular blank allowance; conservative layout, "
                "no spare sheets. Verify supplied thickness before joinery. "
                + (first.get("material_source") or "")
            ),
            "also_in_placeables": True,
        })
    return orders
