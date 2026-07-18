"""2D drawing IR + primitives + assembly card + Nordic palette (→ 12, → 20).

Two IRs live here: the SVG card IR (``ir.py``, M1) that powers the assembly section card,
and the M2 drawing scenegraph (``scene.py``) that feeds the DXF/PDF/raster writers. They are
kept distinct on purpose — the card is a fixed-layout inspector graphic; the scene is a
model-space CAD drawing.
"""

from __future__ import annotations

from typehaus.emit.draw.card import render_card, render_card_svg
from typehaus.emit.draw.dxf_writer import write_dxf
from typehaus.emit.draw.floorplan import build_floorplan
from typehaus.emit.draw.ir import Drawing, Line, Rect, Text
from typehaus.emit.draw.pdf_writer import write_pdf, write_raster
from typehaus.emit.draw.render import render_plan, render_views
from typehaus.emit.draw.scene import Scene, SceneBuilder

__all__ = [
    "render_card", "render_card_svg", "Drawing", "Rect", "Line", "Text",
    "Scene", "SceneBuilder", "build_floorplan",
    "write_dxf", "write_pdf", "write_raster",
    "render_plan", "render_views",
]
