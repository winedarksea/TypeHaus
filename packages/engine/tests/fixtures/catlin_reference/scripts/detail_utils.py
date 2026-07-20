"""
Shared helper functions for plotting construction detail schematics.
"""

import textwrap
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, Optional, Tuple, Union

import numpy as np
from matplotlib.patches import Circle, FancyBboxPatch, Polygon, Rectangle

# Standard material colors for consistent drawings.
MATERIAL_COLORS = {
    "aggregate": "#7F7F7F",
    "block": "#A0A0A0",
    "cladding_white": "#FFFDFD",
    "concrete": "#BFBFBF",
    "drywall": "#E6E6E6",
    "eps": "#C8E0F8",
    "equipment": "#7F7F7F",
    "fiber_cement": "#E6E6E6",
    "gutter": "#8B8B8B",
    "flashing": "#7A0C0C",
    "glass": "#BEE3F8",
    "insulation": "#DDECC8",
    "membrane": "#1E3A5F",
    "metal": "#FFFFFF",
    "metal_dark": "#2F2F2F",
    "mineral_wool": "#A8A8A8",
    "osb": "#D9C8A0",
    "polyiso": "#F4E6B1",
    "river_rock": "#A9A9A9",
    "rubber": "#3A3A3A",
    "sealant": "#6E4F2A",
    "sheathing": "#D9C8A0",
    "soil": "#D2B48C",
    "soffit": "#E0E0E0",
    "spray_foam": "#FFD966",
    "tile": "#E9ECEF",
    "underlayment": "#4A4A4A",
    "wood": "#C8A26A",
    "xps": "#A7D7C5",
}

COLORS = SimpleNamespace(**MATERIAL_COLORS)
HATCHES = SimpleNamespace(
    gravel="o",
    compacted="..",
    diagonal="//",
    cross="xx",
    joist="\\\\",
    dense_plus="++",
)

LayerMap = Dict[str, Tuple[float, float]]


def _wrap_notes(lines, width=58):
    wrapped = []
    for line in lines:
        if line.strip().startswith("•"):
            wrapped.extend(textwrap.wrap(line, width=width))
        else:
            wrapped.append(line)
    return "\n".join(wrapped)


def _rect(ax, x, y, w, h, *, fc="white", ec="black", lw=1.2, ls="-", hatch=None, z=1, alpha=1.0):
    rect = Rectangle(
        (x, y),
        w,
        h,
        facecolor=fc,
        edgecolor=ec,
        linewidth=lw,
        linestyle=ls,
        hatch=hatch,
        zorder=z,
        alpha=alpha,
    )
    ax.add_patch(rect)
    return rect


def _poly(ax, pts, *, fc="white", ec="black", lw=1.2, ls="-", hatch=None, z=1, alpha=1.0):
    poly = Polygon(
        np.asarray(pts, dtype=float),
        closed=True,
        facecolor=fc,
        edgecolor=ec,
        linewidth=lw,
        linestyle=ls,
        hatch=hatch,
        zorder=z,
        alpha=alpha,
    )
    ax.add_patch(poly)
    return poly


def _leader(ax, xy, text_xy, text, *, ha="left", va="center", zorder=100):
    ax.annotate(
        text,
        xy=xy,
        xytext=text_xy,
        textcoords="data",
        ha=ha,
        va=va,
        fontsize=9,
        bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="none", alpha=0.85),
        arrowprops=dict(arrowstyle="-", linewidth=1.0, shrinkA=0, shrinkB=0),
        zorder=zorder,
    )


def _dim_h(ax, x0, x1, y, text, *, text_dy=0.9):
    ax.annotate("", xy=(x0, y), xytext=(x1, y), arrowprops=dict(arrowstyle="<->", linewidth=1.1))
    ax.text((x0 + x1) / 2, y + text_dy, text, ha="center", va="bottom", fontsize=9)


def _dim_v(ax, y0, y1, x, text, *, text_dx=0.9):
    ax.annotate("", xy=(x, y0), xytext=(x, y1), arrowprops=dict(arrowstyle="<->", linewidth=1.1))
    ax.text(x + text_dx, (y0 + y1) / 2, text, ha="left", va="center", fontsize=9, rotation=90)


def _offset_segment(p0, p1, offset):
    p0 = np.asarray(p0, dtype=float)
    p1 = np.asarray(p1, dtype=float)
    delta = p1 - p0
    normal = np.array([-delta[1], delta[0]], dtype=float)
    normal /= np.linalg.norm(normal) + 1e-9
    return p0 + offset * normal, p1 + offset * normal


def _quad_from_segment(p0, p1, thickness):
    a0, a1 = _offset_segment(p0, p1, thickness / 2)
    b0, b1 = _offset_segment(p0, p1, -thickness / 2)
    return np.vstack([a0, a1, b1, b0])


def _round_rect(ax, x, y, w, h, *, fc="white", ec="black", lw=1.0, ls="-", radius=0.5, z=1, alpha=1.0):
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle=f"round,pad=0.02,rounding_size={radius}",
        facecolor=fc,
        edgecolor=ec,
        linewidth=lw,
        linestyle=ls,
        zorder=z,
        alpha=alpha,
    )
    ax.add_patch(patch)
    return patch


def _pipe(ax, x, y, d, *, fc=COLORS.metal, ec="black", lw=1.1, z=6, fill_alpha=0.85):
    ax.add_patch(Circle((x, y), radius=d / 2, facecolor="white", edgecolor=ec, lw=lw, zorder=z))
    ax.add_patch(Circle((x, y), radius=d / 2 - 0.25, facecolor=fc, edgecolor="none", alpha=fill_alpha, zorder=z + 1))


def _dotted_pipe(ax, p0, p1, d, *, fc=COLORS.metal, ec="black", lw=1.6, dash=(1.0, 2.2), z=15):
    p0 = np.asarray(p0, dtype=float)
    p1 = np.asarray(p1, dtype=float)
    ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=ec, linewidth=lw, linestyle=(0, dash), zorder=z)
    for p in (p0, p1):
        ax.add_patch(Circle((p[0], p[1]), radius=d / 2, facecolor="white", edgecolor=ec, lw=1.0, zorder=z + 1))
        ax.add_patch(Circle((p[0], p[1]), radius=d / 2 - 0.25, facecolor=fc, edgecolor="none", alpha=0.85, zorder=z + 2))


def _rebar_L(ax, x_cover_from_face, x_face, y_base_bot, y_base_top, y_wall_top, *, hook=14.0, color="black", lw=1.6, z=20):
    """
    Draw a schematic L-bar: vertical along wall, hooks into base slab.

    x_face: soil-facing outer face of stem.
    x_cover_from_face: positive distance into concrete from x_face.
    """

    x_vert = x_face + x_cover_from_face
    y_hook = y_base_bot + 3.0
    x_hook = x_vert + np.sign(x_cover_from_face) * hook

    ax.plot([x_vert, x_vert, x_hook], [y_wall_top - 6.0, y_hook, y_hook], color=color, linewidth=lw, zorder=z)
    ax.add_patch(Circle((x_vert, y_base_top + 24.0), radius=0.85, facecolor=color, edgecolor="none", zorder=z + 1))


def _rebar_h(ax, x0, x1, y, *, color="black", lw=1.4, z=20, end_hooks=True):
    ax.plot([x0, x1], [y, y], color=color, linewidth=lw, zorder=z)
    if end_hooks:
        for x in (x0 + 10.0, x1 - 10.0):
            ax.add_patch(Circle((x, y), radius=0.75, facecolor=color, edgecolor="none", zorder=z + 1))


def _screw(ax, x_start, x_end, y_center, diam, *, color=COLORS.flashing, z=6):
    lw = max(1.2, diam * 6)
    ax.plot([x_start, x_end], [y_center, y_center], color=color, linewidth=lw, solid_capstyle="round", zorder=z)
    head_r = diam / 2
    tip_r = diam / 2 * 0.8
    ax.add_patch(Circle((x_start, y_center), radius=head_r, facecolor=color, edgecolor="black", linewidth=0.6, zorder=z + 1))
    ax.add_patch(Circle((x_end, y_center), radius=tip_r, facecolor=color, edgecolor="black", linewidth=0.6, zorder=z + 1))


def _batt_insulation(ax, x, y, w, h, *, fc=COLORS.insulation, ec="black", lw=0.8, hatch=HATCHES.compacted, radius=0.6, z=1):
    patch = _round_rect(ax, x, y, w, h, fc=fc, ec=ec, lw=lw, ls="-", radius=radius, z=z, alpha=1.0)
    patch.set_hatch(hatch)
    return patch


def _stud_pattern(ax, positions, *, axis="y", fixed=0.0, depth, thickness, fc=COLORS.wood, ec="black", lw=1.2, z=3, hatch=None):
    """
    Draw repeated studs either along y (top view) or along x (section view).
    """

    patches = []
    if axis == "y":
        for pos in positions:
            patches.append(_rect(ax, fixed, pos, depth, thickness, fc=fc, ec=ec, lw=lw, hatch=hatch, z=z))
    elif axis == "x":
        for pos in positions:
            patches.append(_rect(ax, pos, fixed, thickness, depth, fc=fc, ec=ec, lw=lw, hatch=hatch, z=z))
    else:
        raise ValueError("axis must be 'x' or 'y'")
    return patches


def _path_from_steps(start_xy, steps):
    """
    Build a polyline from a start point and a list of (dx, dy) steps.

    Useful for sheet-metal flashing profiles (Z-flashing, drip edges, etc.) when combined
    with `_thick_polyline`.
    """

    x, y = (float(start_xy[0]), float(start_xy[1]))
    pts = [(x, y)]
    for dx, dy in steps:
        x += float(dx)
        y += float(dy)
        pts.append((x, y))
    return np.asarray(pts, dtype=float)


def _thick_polyline(points, thickness, *, miter_min_dot=0.25):
    """
    Convert a polyline centerline into a closed polygon with constant thickness.

    `miter_min_dot` prevents miter spikes at sharp corners; lower values allow longer miters.
    """

    pts = np.asarray(points, dtype=float)
    if len(pts) < 2:
        raise ValueError("need at least 2 points")

    seg = pts[1:] - pts[:-1]
    norms = np.stack([-seg[:, 1], seg[:, 0]], axis=1)
    norms /= np.linalg.norm(norms, axis=1, keepdims=True) + 1e-9

    vnorms = np.zeros_like(pts)
    vnorms[0] = norms[0]
    vnorms[-1] = norms[-1]

    for i in range(1, len(pts) - 1):
        n0 = norms[i - 1]
        n1 = norms[i]
        m = n0 + n1
        m_norm = np.linalg.norm(m)
        if m_norm < 1e-6:
            vnorms[i] = n1
            continue
        m /= m_norm
        denom = float(np.dot(m, n1))
        denom = max(denom, float(miter_min_dot))
        vnorms[i] = m / denom

    half = float(thickness) / 2.0
    outer = pts + half * vnorms
    inner = pts - half * vnorms
    return np.vstack([outer, inner[::-1]])


def _flashing(ax, centerline_points, thickness, *, fc=COLORS.metal, ec="black", lw=1.0, z=8, alpha=0.9):
    """
    Draw sheet-metal flashing as a thickened polyline.

    `centerline_points` is an Nx2 polyline; `thickness` is schematic/visual thickness.
    """

    poly = _thick_polyline(centerline_points, thickness)
    patch = Polygon(poly, closed=True, facecolor=fc, edgecolor=ec, linewidth=lw, zorder=z, alpha=alpha)
    ax.add_patch(patch)
    return patch


def _lumber(ax, x, y, w, h, *, fc=COLORS.wood, ec="black", lw=1.1, ls="-", z=5, alpha=1.0, draw_x=True):
    """
    Draw cross-section lumber with standard X marking (for sill plates, top plates, headers, etc.).
    
    The X is drawn as actual lines that scale with the rectangle size, not as a matplotlib hatch pattern.
    Set draw_x=False to omit the X marking if needed.
    """
    rect = _rect(ax, x, y, w, h, fc=fc, ec=ec, lw=lw, ls=ls, hatch=None, z=z, alpha=alpha)
    
    if draw_x:
        # Draw diagonal X lines across the lumber cross-section
        x_lw = 0.8  # line weight for X
        ax.plot([x, x + w], [y, y + h], color="black", linewidth=x_lw, zorder=z + 1)
        ax.plot([x + w, x], [y, y + h], color="black", linewidth=x_lw, zorder=z + 1)
    
    return rect


def _french_drain(ax, x, y, diameter, *, fc=COLORS.metal, ec="black", lw=1.1, z=3, fill_alpha=0.75):
    """
    Draw a french drain (perforated pipe) in cross-section.
    
    Parameters:
    -----------
    x, y : float
        Center coordinates of the pipe
    diameter : float
        Diameter of the pipe
    fc : color
        Fill color for the pipe wall
    ec : color
        Edge color
    lw : float
        Line width
    z : int
        Z-order for layering
    fill_alpha : float
        Alpha transparency for the pipe wall
    """
    # Outer circle (white background)
    ax.add_patch(Circle((x, y), radius=diameter / 2, facecolor="white", edgecolor=ec, lw=lw, zorder=z))
    # Inner circle (pipe wall with material color)
    ax.add_patch(Circle((x, y), radius=diameter / 2 - 0.25, facecolor=fc, edgecolor="none", alpha=fill_alpha, zorder=z + 1))


def _slab_assembly(ax, x0, x1, y_top, *, slab_thk=4.0, xps_thk=2.0, vapor_thk=0.05, stone_thk=4.0, 
                   thermal_break_thk=1.0, sealant_thk=0.5, thermal_break_side='left',
                   thermal_break_x=None, show_stone=True):
    """
    Draw a complete slab assembly with optional thermal break at perimeter.
    
    Parameters:
    -----------
    ax : matplotlib axes
        The axes to draw on
    x0, x1 : float
        Left and right x-coordinates of the slab
    y_top : float
        Top surface of the slab
    slab_thk : float
        Thickness of concrete slab (default 4.0")
    xps_thk : float
        Thickness of XPS insulation under slab (default 2.0")
    vapor_thk : float
        Thickness of vapor barrier (schematic, default 0.05")
    stone_thk : float
        Thickness of gravel base (default 4.0")
    thermal_break_thk : float
        Thickness of thermal break XPS at perimeter (default 1.0")
    sealant_thk : float
        Thickness of sealant at top of thermal break (default 0.5")
    thermal_break_side : str
        'left', 'right', 'both', or None for thermal break location
    thermal_break_x : float or tuple
        X-coordinate(s) for thermal break. If None, uses x0 for 'left' or x1 for 'right'
    show_stone : bool
        Whether to show the stone/gravel base layer
    
    Returns:
    --------
    dict with layer y-coordinates: 'slab_bot', 'vapor_bot', 'xps_bot', 'stone_bot'
    """
    COL = COLORS
    
    y_slab_bot = y_top - slab_thk
    y_vapor_bot = y_slab_bot - vapor_thk
    y_xps_bot = y_vapor_bot - xps_thk
    y_stone_bot = y_xps_bot - stone_thk
    
    # Draw thermal break(s) if specified
    if thermal_break_side and thermal_break_side != 'none':
        if thermal_break_side == 'left' or thermal_break_side == 'both':
            tb_x = thermal_break_x if thermal_break_x is not None else x0
            _rect(ax, tb_x, y_slab_bot, thermal_break_thk, slab_thk, fc=COL.xps, lw=1.0, z=3)
            _rect(ax, tb_x, y_top, thermal_break_thk, sealant_thk, fc=COL.sealant, ec="black", lw=0.9, z=5)
            # Adjust slab start if thermal break is at edge
            if thermal_break_x is None:
                x0 = x0 + thermal_break_thk
        
        if thermal_break_side == 'right' or thermal_break_side == 'both':
            tb_x = thermal_break_x if (thermal_break_x is not None and thermal_break_side == 'right') else (x1 - thermal_break_thk)
            _rect(ax, tb_x, y_slab_bot, thermal_break_thk, slab_thk, fc=COL.xps, lw=1.0, z=3)
            _rect(ax, tb_x, y_top, thermal_break_thk, sealant_thk, fc=COL.sealant, ec="black", lw=0.9, z=5)
            # Adjust slab end if thermal break is at edge
            if thermal_break_x is None:
                x1 = x1 - thermal_break_thk
    
    # Draw slab layers
    _rect(ax, x0, y_slab_bot, x1 - x0, slab_thk, fc=COL.concrete, lw=1.2, z=2)
    _rect(ax, x0, y_vapor_bot, x1 - x0, vapor_thk, fc=COL.membrane, ec="black", lw=0.6, z=1)
    _rect(ax, x0, y_xps_bot, x1 - x0, xps_thk, fc=COL.xps, lw=1.0, z=1)
    
    if show_stone:
        _rect(ax, x0, y_stone_bot, x1 - x0, stone_thk, fc=COL.aggregate, lw=0.9, hatch=HATCHES.gravel, z=0)
    
    return {
        'slab_bot': y_slab_bot,
        'vapor_bot': y_vapor_bot,
        'xps_bot': y_xps_bot,
        'stone_bot': y_stone_bot
    }


def _translate_layers(layers: LayerMap, dx: float) -> LayerMap:
    """Shift a layer coordinate map by dx."""
    if abs(dx) < 1e-9:
        return layers
    return {k: (v[0] + dx, v[1] + dx) for k, v in layers.items()}


@dataclass
class ExteriorWoodWallAssembly:
    """
    Layered exterior stud wall with continuous insulation.

    Coordinates are returned as (x0, x1) tuples running interior->exterior.
    `membrane` is a real thickness; if you want a visual-only membrane that
    does not push out foam, set membrane=0 and draw the membrane separately.
    """

    drywall: float
    stud_depth: float
    sheathing: float
    membrane: float
    polyiso: float
    eps: float
    furring: float
    cladding: float
    x_clad1: float = 1.0  # default exterior face reference

    def coords(self, *, x_clad1: Optional[float] = None, dx: float = 0.0) -> LayerMap:
        xc1 = self.x_clad1 if x_clad1 is None else x_clad1
        x_clad0 = xc1 - self.cladding
        x_fur1 = x_clad0
        x_fur0 = x_fur1 - self.furring
        x_eps1 = x_fur0
        x_eps0 = x_eps1 - self.eps
        x_poly1 = x_eps0
        x_poly0 = x_poly1 - self.polyiso
        x_mem1 = x_poly0
        x_mem0 = x_mem1 - self.membrane
        x_sheath1 = x_mem0
        x_sheath0 = x_sheath1 - self.sheathing
        x_stud1 = x_sheath0
        x_stud0 = x_stud1 - self.stud_depth
        x_dry1 = x_stud0
        x_dry0 = x_dry1 - self.drywall

        layers: LayerMap = {
            "drywall": (x_dry0, x_dry1),
            "stud": (x_stud0, x_stud1),
            "sheathing": (x_sheath0, x_sheath1),
            "membrane": (x_mem0, x_mem1),
            "polyiso": (x_poly0, x_poly1),
            "eps": (x_eps0, x_eps1),
            "furring": (x_fur0, x_fur1),
            "cladding": (x_clad0, xc1),
        }
        layers = _translate_layers(layers, dx)
        layers["interior_face"] = layers["drywall"][0]
        layers["stud_face"] = layers["stud"][1]
        layers["sheathing_face"] = layers["sheathing"][1]
        layers["exterior_face"] = layers["cladding"][1]
        return layers


@dataclass
class BasementConcreteWallAssembly:
    """
    Exterior concrete wall with optional continuous insulation/furring/cladding.

    Coordinates are returned as (x0, x1) tuples running interior->exterior.
    """

    conc_thk: float
    membrane: float
    polyiso: float
    eps: float
    furring: float
    cladding: float
    x_clad1: float = 1.0

    def coords(self, *, x_clad1: Optional[float] = None, dx: float = 0.0) -> LayerMap:
        xc1 = self.x_clad1 if x_clad1 is None else x_clad1
        x_clad0 = xc1 - self.cladding
        x_fur1 = x_clad0
        x_fur0 = x_fur1 - self.furring
        x_eps1 = x_fur0
        x_eps0 = x_eps1 - self.eps
        x_poly1 = x_eps0
        x_poly0 = x_poly1 - self.polyiso
        x_mem1 = x_poly0
        x_mem0 = x_mem1 - self.membrane
        x_conc_ext = x_mem0
        x_conc_int = x_conc_ext - self.conc_thk

        layers: LayerMap = {
            "concrete": (x_conc_int, x_conc_ext),
            "membrane": (x_mem0, x_mem1),
            "polyiso": (x_poly0, x_poly1),
            "eps": (x_eps0, x_eps1),
            "furring": (x_fur0, x_fur1),
            "cladding": (x_clad0, xc1),
        }
        layers = _translate_layers(layers, dx)
        layers["interior_face"] = layers["concrete"][0]
        layers["exterior_face"] = layers["cladding"][1]
        return layers

def load_markdown_notes(path: Union[str, Path], *, header: str = "NOTES:") -> list[str]:
    p = Path(path)
    lines = p.read_text(encoding="utf-8").splitlines()

    i = 0
    if lines and lines[0].strip() == "---":
        i = 1
        while i < len(lines) and lines[i].strip() != "---":
            i += 1
        if i < len(lines) and lines[i].strip() == "---":
            i += 1

    out: list[str] = [header, ""]
    pending_bullet: list[str] | None = None

    def flush_bullet() -> None:
        nonlocal pending_bullet
        if not pending_bullet:
            pending_bullet = None
            return
        text = " ".join(part.strip() for part in pending_bullet if part.strip()).strip()
        if text:
            out.append(f"• {text}")
            out.append("")
        pending_bullet = None

    def add_blank() -> None:
        if out and out[-1] != "":
            out.append("")

    for raw in lines[i:]:
        if not raw.strip():
            flush_bullet()
            add_blank()
            continue

        stripped = raw.lstrip()
        if stripped.startswith("#"):
            flush_bullet()
            continue

        if (stripped.startswith("- ") or stripped.startswith("* ")) and not stripped.startswith(("- [", "* [")):
            flush_bullet()
            pending_bullet = [stripped[2:].strip()]
            continue

        if pending_bullet is not None and (raw.startswith("  ") or raw.startswith("\t")):
            pending_bullet.append(stripped.strip())
            continue

        flush_bullet()
        out.append(stripped.rstrip())

    flush_bullet()
    while out and out[-1] == "":
        out.pop()
    return out
