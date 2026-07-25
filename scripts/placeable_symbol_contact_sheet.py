"""Render every registered placeable symbol at its catalog size into one SVG contact sheet.

Reviewing ~30 glyphs one at a time is not practical, and a symbol only fails in a way you can
see. This is the review surface: run it, open the SVG, and check that a sofa reads as a sofa
and a toilet as a toilet.

    PYTHONPATH=packages/engine/src:. .venv/bin/python \\
        scripts/placeable_symbol_contact_sheet.py out/symbols.svg
"""

from __future__ import annotations

import sys
from pathlib import Path

from typehaus.model.placeable_symbols import _REGISTRY, part_hex, plan_symbol_strokes

from library.placeables import (STARTER_APPLIANCE_TYPES, STARTER_FIXTURE_TYPES,
                                STARTER_FURNITURE_TYPES)

CELL_PX = 190
COLUMNS = 6
PADDING_PX = 22
# Sizes for the symbols no starter catalog entry uses yet (Catlin owns these house-locally).
FALLBACK_SIZES_M = {"furnace": (0.60, 0.75), "water-heater": (0.55, 0.55),
                    "panel": (0.36, 0.12), "register": (0.30, 0.10),
                    "washer": (0.69, 0.76)}


def _catalog_sizes() -> dict[str, tuple[float, float]]:
    sizes = dict(FALLBACK_SIZES_M)
    for item in (*STARTER_FURNITURE_TYPES, *STARTER_APPLIANCE_TYPES, *STARTER_FIXTURE_TYPES):
        if item.plan_symbol and item.plan_symbol not in sizes:
            sizes[item.plan_symbol] = tuple(part.meters for part in item.footprint)
    return sizes


def _cell(symbol: str, width_m: float, depth_m: float, ox: float, oy: float) -> list[str]:
    scale = (CELL_PX - 2 * PADDING_PX) / max(width_m, depth_m)
    cx, cy = ox + CELL_PX / 2, oy + CELL_PX / 2
    out = [f'<rect x="{ox}" y="{oy}" width="{CELL_PX}" height="{CELL_PX}" fill="none" '
           f'stroke="#e3e3e0"/>',
           f'<text x="{cx}" y="{oy + CELL_PX - 6}" font-size="9" text-anchor="middle" '
           f'fill="#555">{symbol} · {width_m * 39.37:.0f}"×{depth_m * 39.37:.0f}"</text>']
    for stroke in plan_symbol_strokes(symbol, width_m, depth_m):
        # Screen y is inverted, exactly as Canvas2D and the sheet writers project it.
        points = " ".join(f"{cx + x * scale:.2f},{cy - y * scale:.2f}"
                          for x, y in stroke["points"])
        fill = part_hex(stroke["fill"]) if stroke["fill"] else "none"
        tag = "polygon" if stroke["closed"] else "polyline"
        out.append(f'<{tag} points="{points}" fill="{fill}" stroke="#222" '
                   f'stroke-width="{stroke["weight"] * 3.2:.2f}" stroke-linejoin="round"/>')
    return out


def main(destination: Path) -> None:
    sizes = _catalog_sizes()
    symbols = sorted(_REGISTRY)
    rows = (len(symbols) + COLUMNS - 1) // COLUMNS
    body: list[str] = []
    for index, symbol in enumerate(symbols):
        width_m, depth_m = sizes.get(symbol, (1.0, 0.7))
        body.extend(_cell(symbol, width_m, depth_m,
                          (index % COLUMNS) * CELL_PX, (index // COLUMNS) * CELL_PX))
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{COLUMNS * CELL_PX}" '
        f'height="{rows * CELL_PX}" viewBox="0 0 {COLUMNS * CELL_PX} {rows * CELL_PX}">'
        f'<rect width="100%" height="100%" fill="#fbfbf9"/>' + "".join(body) + "</svg>")
    print(f"{len(symbols)} symbols -> {destination}")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "out/placeable_symbols.svg"))
