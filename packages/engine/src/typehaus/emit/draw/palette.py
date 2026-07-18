"""The centralized Nordic presentation preset — one muted palette shared by the 3D
viewer, the SVG editor, and 2D detail hatches (#24, → 21 §Nordic preset)."""

from __future__ import annotations

# Muted Nordic palette; material colors fall back to these hatch-family defaults.
NORDIC_BG = "#f4f2ed"
NORDIC_INK = "#33312c"
NORDIC_LINE = "#5b574f"
NORDIC_ACCENT = "#6d8a96"

HATCH_FAMILY_COLOR: dict[str, str] = {
    "lumber": "#d8c9a6",
    "osb": "#c9a86a",
    "rigid": "#e8d64f",
    "batt": "#f3c6d0",
    "gypsum": "#efeae2",
    "membrane": "#4a4a4a",
    "siding": "#b8bcc0",
    "metal": "#6b7076",
    "concrete": "#a9a9a9",
}

# Control-layer badge colors.
CONTROL_COLOR: dict[str, str] = {
    "air": "#c0392b",
    "water": "#2980b9",
    "vapor": "#8e44ad",
    "thermal": "#e67e22",
}


def material_color(hatch: str | None, explicit: str | None) -> str:
    if explicit:
        return explicit
    if hatch and hatch in HATCH_FAMILY_COLOR:
        return HATCH_FAMILY_COLOR[hatch]
    return "#cfc9bd"
