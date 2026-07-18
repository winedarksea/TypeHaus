"""Assembly section card (→ 12 §Assembly card) — the assemblies' visual feedback surface.

Deliberately model-free: renders an Assembly definition (not resolved geometry), so it
needs nothing from the resolve pipeline and doubles as the live canvas of the M2 assembly
editor. Progressive enrichment: STC badge (#50), source note (#46), Glaser plot (M5).
"""

from __future__ import annotations

from typehaus.analysis import assembly_r_value
from typehaus.emit.draw.ir import Badge, Drawing, Line, Rect, Text
from typehaus.emit.draw.palette import CONTROL_COLOR, material_color
from typehaus.model.assembly import Assembly
from typehaus.model.plan import Library

_W = 460.0
_PX_PER_IN = 26.0
_MIN_DRAW_H = 10.0  # thin-layer clamp (ExaggerationSpec) with true thickness labeled
_LEFT = 30.0
_STACK_W = 150.0
_TOP = 70.0


def render_card(asm: Assembly, library: Library) -> Drawing:
    """Render one assembly's section card to a Drawing (SVG-serializable)."""
    stack = list(asm.default_lining) + list(asm.layers)
    core_start = len(asm.default_lining)

    heights = [max(_MIN_DRAW_H, layer.thickness.inches * _PX_PER_IN) for layer in stack]
    stack_h = sum(heights)
    height = max(_TOP + stack_h + 90.0, 240.0)
    d = Drawing(width=_W, height=height, bg="#ffffff")

    d.add(Text(_LEFT, 30, asm.tag, size=17, weight="bold"))
    if asm.variant_of:
        d.add(Text(_LEFT, 48, f"variant of {asm.variant_of}", size=11, fill="#8a857b"))

    y = _TOP
    for i, (layer, h) in enumerate(zip(stack, heights)):
        mat = library.material(layer.material_ref)
        color = material_color(mat.hatch if mat else None, mat.color if mat else None)
        hatch = mat.hatch if mat and mat.hatch in {
            "batt", "lumber", "rigid", "concrete", "osb", "metal"} else None
        d.add(Rect(_LEFT, y, _STACK_W, h, fill=color, hatch=hatch, stroke="#4a463f"))
        label = f"{layer.name} — {layer.thickness.fmt()}"
        d.add(Text(_LEFT + _STACK_W + 12, y + h / 2 + 4, label, size=11))
        bx = _LEFT + _STACK_W + 250
        for ctrl in sorted(c.value for c in layer.control):
            d.add(Badge(bx, y + h / 2 - 7, ctrl.upper()[:1], CONTROL_COLOR[ctrl]))
            bx += 22
        y += h

    # Core / lining boundary marker.
    if core_start > 0:
        by = _TOP + sum(heights[:core_start])
        d.add(Line(_LEFT - 6, by, _LEFT + _STACK_W + 6, by, stroke="#c0392b",
                   stroke_width=1.4, dash="4 3"))
        d.add(Text(_LEFT - 8, by - 3, "lining", size=9, fill="#c0392b", anchor="end"))

    # R-value rollup + STC badge + source note.
    ry = y + 26
    rv = assembly_r_value(asm, library)
    d.add(Text(_LEFT, ry, f"R-value (core + lining): {rv.fmt()}", size=13, weight="bold"))
    if asm.stc is not None:
        d.add(Badge(_LEFT + 300, ry - 12, f"STC {asm.stc}", CONTROL_COLOR["air"]))
    if asm.source:
        d.add(Text(_LEFT, ry + 20, f"source: {asm.source}", size=9, fill="#8a857b"))
    return d


def render_card_svg(asm: Assembly, library: Library) -> str:
    return render_card(asm, library).to_svg()
