"""Minimal 2D drawing IR + SVG renderer (ported math from detail_utils.py, → 12/20).

The IR is a flat list of primitives in a top-left-origin pixel space; the SVG backend
serializes them. The same primitives power the assembly card (M1), detail slices (M2),
and permit sheets (M3) — one renderer, many consumers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union
from xml.sax.saxutils import escape


@dataclass
class Rect:
    x: float
    y: float
    w: float
    h: float
    fill: str = "none"
    stroke: str = "#33312c"
    stroke_width: float = 1.0
    hatch: str | None = None  # references a registered pattern id


@dataclass
class Line:
    x0: float
    y0: float
    x1: float
    y1: float
    stroke: str = "#33312c"
    stroke_width: float = 1.0
    dash: str | None = None


@dataclass
class Text:
    x: float
    y: float
    s: str
    size: float = 11.0
    fill: str = "#33312c"
    anchor: str = "start"  # start | middle | end
    weight: str = "normal"


@dataclass
class Badge:
    x: float
    y: float
    label: str
    color: str


Primitive = Union[Rect, Line, Text, Badge]


@dataclass
class Drawing:
    width: float
    height: float
    prims: list[Primitive] = field(default_factory=list)
    bg: str = "#ffffff"

    def add(self, prim: Primitive) -> None:
        self.prims.append(prim)

    def to_svg(self) -> str:
        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width:.0f}" '
            f'height="{self.height:.0f}" viewBox="0 0 {self.width:.0f} {self.height:.0f}">',
            _hatch_defs(),
            f'<rect width="100%" height="100%" fill="{self.bg}"/>',
        ]
        for p in self.prims:
            parts.append(_render(p))
        parts.append("</svg>")
        return "\n".join(parts)


def _render(p: Primitive) -> str:
    if isinstance(p, Rect):
        fill = f"url(#hatch-{p.hatch})" if p.hatch else p.fill
        return (f'<rect x="{p.x:.2f}" y="{p.y:.2f}" width="{p.w:.2f}" height="{p.h:.2f}" '
                f'fill="{fill}" stroke="{p.stroke}" stroke-width="{p.stroke_width}"/>')
    if isinstance(p, Line):
        dash = f' stroke-dasharray="{p.dash}"' if p.dash else ""
        return (f'<line x1="{p.x0:.2f}" y1="{p.y0:.2f}" x2="{p.x1:.2f}" y2="{p.y1:.2f}" '
                f'stroke="{p.stroke}" stroke-width="{p.stroke_width}"{dash}/>')
    if isinstance(p, Text):
        return (f'<text x="{p.x:.2f}" y="{p.y:.2f}" font-size="{p.size}" fill="{p.fill}" '
                f'text-anchor="{p.anchor}" font-weight="{p.weight}" '
                f'font-family="Helvetica, Arial, sans-serif">{escape(p.s)}</text>')
    if isinstance(p, Badge):
        w = 8 + len(p.label) * 6.2
        return (f'<g><rect x="{p.x:.2f}" y="{p.y:.2f}" width="{w:.1f}" height="15" rx="3" '
                f'fill="{p.color}"/><text x="{p.x + w/2:.2f}" y="{p.y + 11:.2f}" '
                f'font-size="10" fill="#fff" text-anchor="middle" '
                f'font-family="Helvetica, Arial, sans-serif">{escape(p.label)}</text></g>')
    return ""


def _hatch_defs() -> str:
    """A few simple SVG hatch patterns keyed by material hatch family."""
    patterns = {
        "batt": '<path d="M0,4 Q2,0 4,4 T8,4" stroke="#d98aa0" fill="none"/>',
        "lumber": '<line x1="0" y1="0" x2="8" y2="8" stroke="#b09a6a" stroke-width="0.6"/>',
        "rigid": '<line x1="0" y1="4" x2="8" y2="4" stroke="#c8b93a" stroke-width="0.6"/>',
        "concrete": '<circle cx="2" cy="2" r="0.6" fill="#888"/>'
                    '<circle cx="6" cy="6" r="0.6" fill="#888"/>',
        "osb": '<line x1="0" y1="8" x2="8" y2="0" stroke="#b0904a" stroke-width="0.5"/>',
        "metal": '<line x1="4" y1="0" x2="4" y2="8" stroke="#586066" stroke-width="0.8"/>',
    }
    defs = ['<defs>']
    for name, body in patterns.items():
        defs.append(
            f'<pattern id="hatch-{name}" width="8" height="8" '
            f'patternUnits="userSpaceOnUse">{body}</pattern>'
        )
    defs.append("</defs>")
    return "".join(defs)
