"""The panel a sheathing layer is bought in — one reading for the bracing check and the order.

``Layer.sheet_length`` is the premise both answer from: whether one sheet reaches a braced
wall's plate (Table R602.10.3(2) item 8) and how many sheets the order asks for. An unstated
length is ``None`` here; each consumer says what it does with that, and neither guesses a
different number from the other.
"""

from __future__ import annotations

import math

from typehaus.model.assembly import Layer

SHEET_WIDTH_IN = 48.0
#: What the ORDER bills an unstated layer in — the shelf panel. The bracing check never
#: uses it: an unstated length is UNKNOWN there.
ORDER_DEFAULT_SHEET_LENGTH_IN = 96.0


def layer_sheet_length_in(layer: Layer | None) -> float | None:
    """The layer's stated nominal sheet length in inches, or ``None``."""
    if layer is None or layer.sheet_length is None:
        return None
    return layer.sheet_length.inches


def wall_layer(plan, wall, name: str) -> Layer | None:
    """The authored ``Layer`` behind a resolved wall's layer ``name`` (core or lining)."""
    assembly = plan.library.resolve_assembly(wall.assembly)
    if assembly is None:
        return None
    return next((layer for layer in (*assembly.layers, *assembly.default_lining)
                 if layer.name == name), None)


def wall_sheathing(plan, wall) -> list[tuple[str, float | None]]:
    """``(layer name, stated sheet length in inches or None)`` per SHEATHING layer."""
    return [(layer.name, layer_sheet_length_in(wall_layer(plan, wall, layer.name)))
            for layer in wall.layers if layer.function == "sheathing"]


def order_sheet_length_in(stated: float | None) -> float:
    return ORDER_DEFAULT_SHEET_LENGTH_IN if stated is None else stated


def sheet_label(length_in: float) -> str:
    """``96.0`` -> ``"4x8"``, ``114.0`` -> ``"4x9.5"``; anything else prints its inches."""
    feet = length_in / 12.0
    return f"4x{feet:g}" if abs(feet * 2 - round(feet * 2)) < 1e-6 else f"4x{length_in:g}in"


def sheets_for(area_ft2: float, length_in: float) -> int:
    """Whole sheets covering ``area_ft2`` at 48" x ``length_in``."""
    return math.ceil(area_ft2 / (SHEET_WIDTH_IN * length_in / 144.0))
