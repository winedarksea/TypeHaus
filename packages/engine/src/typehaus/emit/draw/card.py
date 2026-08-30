"""Assembly section card (→ 12 §Assembly card) — the assemblies' visual feedback surface.

Deliberately model-free: renders an Assembly definition (not resolved geometry), so it
needs nothing from the resolve pipeline and doubles as the live canvas of the M2 assembly
editor. Progressive enrichment: STC badge (#50), source note (#46), Glaser plot (M5).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typehaus.analysis import assembly_r_value
from typehaus.emit.draw.ir import Badge, Drawing, Line, Rect, Text
from typehaus.emit.draw.palette import CONTROL_COLOR, material_color
from typehaus.model.assembly import Assembly
from typehaus.model.plan import Library

if TYPE_CHECKING:
    from typehaus.checks.building_science.condensation import CondensationAnalysis

_W = 460.0
_PX_PER_IN = 26.0
_MIN_DRAW_H = 10.0  # thin-layer clamp (ExaggerationSpec) with true thickness labeled
_LEFT = 30.0
_STACK_W = 150.0
_TOP = 70.0


def render_card(asm: Assembly, library: Library,
                condensation: CondensationAnalysis | None = None) -> Drawing:
    """Render one assembly's section card to a Drawing (SVG-serializable)."""
    stack = list(asm.default_lining) + list(asm.layers)
    core_start = len(asm.default_lining)

    heights = [max(_MIN_DRAW_H, layer.thickness.inches * _PX_PER_IN) for layer in stack]
    stack_h = sum(heights)
    plot_height = 128.0 if condensation is not None else 0.0
    height = max(_TOP + stack_h + 90.0 + plot_height, 240.0 + plot_height)
    d = Drawing(width=_W, height=height, bg="#ffffff")

    d.add(Text(_LEFT, 30, asm.tag, size=17, weight="bold"))
    if asm.variant_of:
        d.add(Text(_LEFT, 48, f"variant of {asm.variant_of}", size=11, fill="#8a857b"))

    y = _TOP
    # strict=True: `heights` is a comprehension over `stack`, so the two are the same
    # length by construction — a mismatch means that stopped being true.
    for layer, h in zip(stack, heights, strict=True):
        mat = library.material(layer.material_ref)
        color = material_color(mat.hatch if mat else None, mat.color if mat else None)
        hatch = mat.hatch if mat and mat.hatch in {
            "batt", "lumber", "rigid", "concrete", "osb", "metal"} else None
        d.add(Rect(_LEFT, y, _STACK_W, h, fill=color, hatch=hatch, stroke="#4a463f"))
        label = f"{layer.name} — {layer.thickness.fmt()}"
        d.add(Text(_LEFT + _STACK_W + 12, y + h / 2 + 4, label, size=11))
        if layer.cavity is not None:
            # Cavity fill occupies the same depth as its host framing — draw it as an
            # inset band over the structure swatch, never as a stack entry of its own.
            fill = layer.cavity
            fill_mat = library.material(fill.material_ref)
            fill_thk = fill.thickness if fill.thickness is not None else layer.thickness
            frac = min(1.0, fill_thk.inches / layer.thickness.inches) if \
                layer.thickness.inches else 1.0
            d.add(Rect(_LEFT + 6, y + 2, _STACK_W - 12, max(2.0, h * frac - 4),
                       fill=material_color(fill_mat.hatch if fill_mat else None,
                                           fill_mat.color if fill_mat else None),
                       hatch="batt", stroke="#4a463f"))
            d.add(Text(_LEFT + _STACK_W + 12, y + h / 2 + 17,
                       f"↳ cavity: {fill.material_ref} — {fill_thk.fmt()}"
                       f" (ff {fill.framing_factor:.0%})", size=9, fill="#8a857b"))
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
    if condensation is not None:
        _add_condensation_plot(d, condensation, ry + 36)
    return d


def _add_condensation_plot(d: Drawing, analysis: CondensationAnalysis, y: float) -> None:
    """Draw the same Glaser profile surfaced in the UI card and A-401 detail feed."""
    x0, width, height = _LEFT, 360.0, 82.0
    d.add(Text(x0, y, "Glaser design-day profile", size=10, weight="bold"))
    if not analysis.known:
        d.add(Text(x0, y + 18, "UNKNOWN — " + ", ".join(analysis.unknown_materials),
                   size=10, fill="#a66a00"))
        return
    points = analysis.points
    if not points:
        return
    d.add(Rect(x0, y + 8, width, height, fill="#f8f7f3", stroke="#b7b2aa"))
    pressures = [p.vapor_pressure_pa for p in points] + [p.saturation_pressure_pa for p in points]
    temperatures = [p.temperature_c for p in points]

    def scaled(values: list[float], value: float) -> float:
        lo, hi = min(values), max(values)
        return y + 8 + height / 2 if hi == lo else y + 8 + height * (1 - (value - lo) / (hi - lo))

    # Temperature (orange) and vapor/saturation (blue/red) are independently normalized;
    # labels make the two scales explicit while preserving readable small-card geometry.
    for values, getter, color in (
        (temperatures, lambda p: p.temperature_c, "#d67d24"),
        (pressures, lambda p: p.vapor_pressure_pa, "#246a9f"),
        (pressures, lambda p: p.saturation_pressure_pa, "#bf3e36"),
    ):
        # strict=False: offset-by-one pairwise walk along the profile — the tail is one
        # shorter by construction.
        for a, b in zip(points, points[1:], strict=False):
            d.add(Line(x0 + width * a.position, scaled(values, getter(a)),
                       x0 + width * b.position, scaled(values, getter(b)),
                       stroke=color, stroke_width=1.6))
    d.add(Text(x0 + width, y + 104, "orange: temperature · blue: vapor · red: saturation",
               size=8, fill="#6e6a64", anchor="end"))
    if analysis.has_risk:
        d.add(Badge(x0 + width - 54, y + 12, "RISK", "#bf3e36"))
    else:
        d.add(Badge(x0 + width - 54, y + 12, "SAFE", "#3c7d5c"))


def render_card_svg(asm: Assembly, library: Library,
                    condensation: CondensationAnalysis | None = None) -> str:
    return render_card(asm, library, condensation).to_svg()
