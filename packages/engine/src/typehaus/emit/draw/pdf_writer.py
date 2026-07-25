"""matplotlib writer for the 2D drawing IR — PDF sheet + headless raster (→ 20 §WP2.7).

The same IR that feeds the DXF writer renders here, so PDF and DXF agree by construction
(→ 20: "PDF and DXF of the same slice visibly agree"). This writer also backs ``haus render``
(→ 20 §Agent eyes) — it draws to PNG/SVG so Claude can *look* at the plan it just edited.
Neither writer computes geometry; placement math already happened IR-side.
"""

from __future__ import annotations

import math
from pathlib import Path

from typehaus.emit.draw.door_symbols import DOOR_SYMBOL_NAMES, door_symbol_geometry
from typehaus.emit.draw.palette import detail_fill
from typehaus.emit.draw.scene import (
    ArchDimension,
    Hatch,
    Leader,
    Polyline,
    Scene,
    Symbol,
    Text,
)

# AIA layer → matplotlib stroke color + width (points at final scale, roughly).
_LAYER_STYLE = {
    "A-WALL": ("#1a1a1a", 1.4),
    "A-WALL-FINI": ("#666666", 0.6),
    "A-WALL-INSU": ("#8a6d9a", 0.5),
    "A-WALL-PATT": ("#b0a060", 0.4),
    "S-FRAM": ("#8a5a20", 1.0),
    "A-DOOR": ("#a05a20", 0.9),
    "A-GLAZ": ("#3a6a8a", 0.7),
    "A-ROOF": ("#2d3b46", 1.2),
    "A-AREA-IDEN": ("#333333", 0.0),
    "A-ANNO-DIMS": ("#204070", 0.6),
    "A-ANNO-TEXT": ("#333333", 0.6),
    "A-ANNO-SYMB": ("#555555", 0.6),
    "A-FLR-HEAT": ("#c05030", 0.35),
    "A-FIXT": ("#4d7080", 0.55),
    "A-SITE-ROOF": ("#2d3b46", 0.8),
    "A-SITE-WALL": ("#333333", 0.6),
    "A-SITE-FOUND": ("#777777", 0.4),
    "A-SITE-ANNO": ("#204070", 0.6),
    "S-FNDN": ("#555555", 1.2),
    "S-FNDN-FTNG": ("#888888", 0.5),
    "A-SLAB": ("#777777", 0.5),
    "S-COLS": ("#8a5a20", 0.9),
    "S-BEAM": ("#8a5a20", 0.9),
    "S-WALL": ("#1a1a1a", 1.4),
    "S-WALL-BELW": ("#aaaaaa", 0.3),
    "S-FRAM-OPEN": ("#a05a20", 0.5),
    "A-WALL-BELW": ("#aaaaaa", 0.3),
    "P-SANR-PIPE": ("#6a4a2a", 0.6),
    "P-DOMW-PIPE": ("#3a6a8a", 0.6),
    "M-HVAC-SDFF": ("#2a6a4a", 0.6),
    "M-HVAC-RDFF": ("#4a8a6a", 0.6),
    "M-HVAC-EQPM": ("#2a6a4a", 0.8),
    "E-POWR-DEVC": ("#8a2a2a", 0.5),
    "E-LITE": ("#c08a00", 0.5),
    "C-PROP": ("#333333", 0.6),
    "C-PROP-SETB": ("#204070", 0.4),
    "C-UTIL-WATER": ("#3a6a8a", 0.4),
    "C-UTIL-SEWER": ("#6a4a2a", 0.4),
    "C-UTIL-GAS": ("#c08a00", 0.4),
    "C-UTIL-POWER": ("#8a2a2a", 0.4),
    "C-TOPO-ARRW": ("#5a8a5a", 0.4),
    "C-TOPO-GRAD": ("#5a8a5a", 0.5),
    "C-TOPO-MINR": ("#8aab8a", 0.25),
    "C-TOPO-IMPV": ("#9a8a70", 0.5),
    "L-SITE-GRAD": ("#5a8a5a", 0.7),
    "A-STAIR": ("#3a4a55", 0.7),
    "A-FURN": ("#8a7550", 0.45),
    "E-POWR": ("#8a2a2a", 0.5),
    "M-EQPT": ("#2a6a4a", 0.7),
    "A-ANNO-TABL": ("#333333", 0.5),
    "A-DETL-CMPT": ("#444444", 0.5),
    "A-DETL-TRMT": ("#7a5a3a", 0.5),
}
_HATCH_MPL = {
    "batt": "....", "osb": "//", "lumber": "\\\\", "concrete": "..", "SOLID": None,
    "rigid": "xx", "gypsum": None, "membrane": None, "metal": None,
    "gravel": "oo", "soil": "..", "foam": "**",
}

# name -> (marker, color) for the simple device/register/equipment symbol vocabulary.
# Each colour matches the symbol's own AIA layer, so a marker never reads as a device from
# another discipline. A smoke/CO alarm is an annotation symbol (A-ANNO-SYMB) drawn as a
# hexagonal head — distinct from the round receptacle, and captioned SD/CO by the builder.
_MARKER_STYLE = {
    "register-supply": ("^", "#2a6a4a"), "register-return": ("v", "#4a8a6a"),
    "receptacle": ("o", "#8a2a2a"), "gfci": ("D", "#8a2a2a"),
    "receptacle_240": ("s", "#8a2a2a"), "switch": ("$S$", "#c08a00"),
    "light": ("*", "#c08a00"), "panel": ("P", "#8a2a2a"),
    "spot-elev": ("+", "#5a8a5a"), "utility-entry": ("x", "#333333"),
    "level-marker": ("<", "#204070"), "alarm": ("h", "#555555"),
}
# Symbols drawn by a branch of their own. Anything else falls through to the window-glass
# bar, so an unlisted name is not a missing glyph but a *wrong* one — how every smoke alarm
# came to be drawn as glazing. Tests assert the plan builders emit nothing outside this set.
SYMBOL_NAMES_WITH_DEDICATED_GLYPH = (
    DOOR_SYMBOL_NAMES | frozenset(_MARKER_STYLE) | frozenset({"post", "span-arrow", "sleeve"})
)


# Leader notes have no authored height; this is their model-space size in inches.
_LEADER_TEXT_H = 1.6
# Clamps in points, so a sheet-scale plan's labels stay readable and a tight detail's
# lettering cannot swallow the drawing.
_MIN_PT, _MAX_PT = 3.0, 14.0


def _scene_bounds(scene: Scene) -> tuple[float, float, float, float] | None:
    """Model-space bbox of the scene, allowing for the width labels occupy.

    Text is placed by its anchor, so a bbox over anchors alone crops the lettering off the
    sheet — a detail's callout column would run past the right edge every time.
    """
    us: list[float] = []
    zs: list[float] = []
    for node in scene.nodes:
        points = getattr(node, "points", None) or getattr(node, "boundary", None)
        if points:
            us.extend(p[0] for p in points)
            zs.extend(p[1] for p in points)
        elif isinstance(node, (Text, Leader)):
            content = node.content if isinstance(node, Text) else node.text
            height = node.height if isinstance(node, Text) else _LEADER_TEXT_H
            anchor = node.anchor if isinstance(node, Text) else node.at
            if not isinstance(anchor, tuple):
                continue
            width = max(len(line) for line in content.split("\n")) * height * _CHAR_ASPECT
            lines = content.count("\n") + 1
            align = getattr(node, "align", "left")
            u0 = {"left": anchor[0], "center": anchor[0] - width / 2,
                  "right": anchor[0] - width}[align]
            us.extend((u0, u0 + width))
            zs.extend((anchor[1] - height * lines, anchor[1] + height * lines))
    if not us or not zs:
        return None
    return min(us), min(zs), max(us), max(zs)


# Monospace advance width as a fraction of cap height — used only to reserve room.
_CHAR_ASPECT = 0.62
_MAX_FIG = (14.0, 11.0)
_MIN_FIG = (5.0, 4.0)


def _fig(scene: Scene, title: str | None):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    bounds = _scene_bounds(scene)
    figsize = (11.0, 8.5)
    if bounds is not None:
        u0, z0, u1, z1 = bounds
        span_u, span_z = max(u1 - u0, 1e-6), max(z1 - z0, 1e-6)
        # Fit the drawing's own aspect inside the sheet envelope, so a tall detail is
        # rendered tall rather than stranded in the middle of a landscape page.
        scale = min(_MAX_FIG[0] / span_u, _MAX_FIG[1] / span_z)
        figsize = (max(_MIN_FIG[0], span_u * scale), max(_MIN_FIG[1], span_z * scale))

    fig, ax = plt.subplots(figsize=figsize)
    ax.set_aspect("equal")
    ax.axis("off")
    scaled_text = _render_nodes(ax, scene)
    if title:
        ax.set_title(title, fontsize=9, family="monospace", loc="left")
    if bounds is not None:
        u0, z0, u1, z1 = bounds
        pad = max(u1 - u0, z1 - z0) * 0.02
        ax.set_xlim(u0 - pad, u1 + pad)
        ax.set_ylim(z0 - pad, z1 + pad)
    else:
        ax.autoscale_view()
    fig.tight_layout()
    _apply_text_scale(fig, ax, scaled_text)
    return fig


def _apply_text_scale(fig, ax, scaled_text) -> None:
    """Convert each label's model-space height into a point size at the drawn scale."""
    if not scaled_text:
        return
    origin = ax.transData.transform((0.0, 0.0))
    unit = ax.transData.transform((0.0, 1.0))
    pixels_per_unit = abs(unit[1] - origin[1])
    if pixels_per_unit <= 0.0:
        return
    points_per_unit = pixels_per_unit * 72.0 / fig.dpi
    for artist, height in scaled_text:
        artist.set_fontsize(min(_MAX_PT, max(_MIN_PT, height * points_per_unit)))


def _render_nodes(ax: object, scene: Scene) -> None:
    from matplotlib.patches import Arc, PathPatch, Polygon
    from matplotlib.path import Path as MplPath

    # (artist, model-space height in inches) — resized once the data limits are known.
    # ``Text.height`` is model space (→ scene.py), so it cannot be handed to matplotlib as
    # a point size: a detail cropped to 3 ft and a plan spanning 40 ft would otherwise get
    # identical, and in the detail's case invisible, lettering.
    scaled_text: list[tuple[object, float]] = []

    for node in scene.nodes:
        if isinstance(node, Polyline):
            color, lw = _LAYER_STYLE.get(node.layer, ("#333", 0.6))
            xs = [p[0] for p in node.points]
            ys = [p[1] for p in node.points]
            if node.closed and len(node.points) >= 3:
                ax.add_patch(Polygon(list(node.points), closed=True, fill=False,
                                     edgecolor=color, linewidth=lw))
            else:
                ax.plot(xs, ys, color=color, linewidth=lw, solid_capstyle="round")
        elif isinstance(node, Hatch):
            # Fill by material, then overlay the hatch — an unfilled hatch alone makes
            # concrete, XPS, EPS and polyiso read as the same grey stipple.
            hatch = _HATCH_MPL.get(node.pattern, "..")
            fill = detail_fill(node.material, None)
            ax.add_patch(Polygon(list(node.boundary), closed=True, facecolor=fill,
                                 edgecolor="none", linewidth=0.0, zorder=0.5))
            if hatch:
                ax.add_patch(Polygon(list(node.boundary), closed=True, fill=False,
                                     hatch=hatch, edgecolor="#6f6a5e", linewidth=0.0,
                                     zorder=0.6))
        elif isinstance(node, Text):
            ha = {"left": "left", "center": "center", "right": "right"}[node.align]
            scaled_text.append((
                ax.text(node.anchor[0], node.anchor[1], node.content,
                        ha=ha, va="center", rotation=node.rotation, family="monospace",
                        color="#222"),
                node.height,
            ))
        elif isinstance(node, ArchDimension):
            _draw_dimension(ax, node)
        elif isinstance(node, Symbol):
            _draw_symbol(ax, node, Arc)
        elif isinstance(node, Leader):
            # Leader geometry is anchor→shoulder; the note sits at the free end (``at``).
            ax.plot([node.to[0], node.at[0]], [node.to[1], node.at[1]],
                    color="#555", linewidth=0.5)
            ax.plot([node.to[0]], [node.to[1]], marker=".", markersize=2, color="#555")
            scaled_text.append((
                ax.text(node.at[0], node.at[1], node.text, family="monospace",
                        va="center", color="#222"),
                _LEADER_TEXT_H,
            ))
    _ = (PathPatch, MplPath)  # imported for parity with richer node kinds
    return scaled_text


def _draw_dimension(ax: object, node: ArchDimension) -> None:
    dx, dy = node.p1[0] - node.p0[0], node.p1[1] - node.p0[1]
    dist_in = math.hypot(dx, dy)
    label = node.text or _feet_inches(dist_in)
    if abs(dx) < abs(dy):  # vertical dimension (→ elevation vertical dim string)
        x = node.p0[0] + node.offset
        ax.annotate("", xy=(x, node.p1[1]), xytext=(x, node.p0[1]),
                    arrowprops=dict(arrowstyle="<->", color="#204070", lw=0.6))
        ax.text(x + 2, (node.p0[1] + node.p1[1]) / 2, label, fontsize=6.5, va="center",
                family="monospace", color="#204070", rotation=90)
    else:
        y = node.p0[1] + node.offset
        ax.annotate("", xy=(node.p1[0], y), xytext=(node.p0[0], y),
                    arrowprops=dict(arrowstyle="<->", color="#204070", lw=0.6))
        ax.text((node.p0[0] + node.p1[0]) / 2, y + 2, label, fontsize=6.5, ha="center",
                family="monospace", color="#204070")


# Door glyph stroke weights: the closed panel/leaf reads heavier than its swept path.
_DOOR_COLOR = "#a05a20"
_DOOR_LEAF_LW, _DOOR_SWEEP_LW = 0.9, 0.6


def _draw_symbol(ax: object, node: Symbol, Arc: object) -> None:
    w = node.params.get("width_in", node.scale) or node.scale
    if node.name in DOOR_SYMBOL_NAMES:
        geometry = door_symbol_geometry(node)
        for stroke in geometry.strokes:
            ax.plot([p[0] for p in stroke.points], [p[1] for p in stroke.points],
                    color=_DOOR_COLOR,
                    lw=_DOOR_SWEEP_LW if stroke.dashed else _DOOR_LEAF_LW,
                    linestyle="--" if stroke.dashed else "-")
        for arc in geometry.arcs:
            # matplotlib takes the full width/height of the ellipse, not the radius.
            ax.add_patch(Arc(arc.center, 2 * arc.radius, 2 * arc.radius, angle=0,
                             theta1=arc.start_angle_deg, theta2=arc.end_angle_deg,
                             edgecolor=_DOOR_COLOR, linewidth=_DOOR_SWEEP_LW))
    elif node.name == "post":
        ax.plot(node.insert[0], node.insert[1], marker="s", markersize=5,
                color="#8a5a20", markerfacecolor="none")
    elif node.name == "span-arrow":
        a = math.radians(node.rotation)
        dx, dy = w * math.cos(a), w * math.sin(a)
        ax.annotate("", xy=(node.insert[0] + dx, node.insert[1] + dy),
                    xytext=(node.insert[0] - dx, node.insert[1] - dy),
                    arrowprops=dict(arrowstyle="->", color="#8a5a20", lw=1.0))
    elif node.name == "sleeve":
        size = max(w, 2.0)
        ax.plot(node.insert[0], node.insert[1], marker="o", markersize=size,
                markerfacecolor="none", markeredgecolor="#6a4a2a", markeredgewidth=0.8)
    elif node.name in _MARKER_STYLE:
        marker, color = _MARKER_STYLE[node.name]
        ax.plot(node.insert[0], node.insert[1], marker=marker, markersize=5, color=color)
    else:  # window mark: glass bar across the full opening plus a short centre mullion
        a = math.radians(node.rotation)
        dx, dy = w * math.cos(a) / 2, w * math.sin(a) / 2
        nx, ny = -math.sin(a) * 2.5, math.cos(a) * 2.5
        ax.plot([node.insert[0] - dx, node.insert[0] + dx],
                [node.insert[1] - dy, node.insert[1] + dy], color="#3a6a8a", lw=2.2)
        ax.plot([node.insert[0] - nx, node.insert[0] + nx],
                [node.insert[1] - ny, node.insert[1] + ny], color="#3a6a8a", lw=0.8)


def _feet_inches(total_in: float) -> str:
    total = round(total_in)
    return f"{total // 12}'-{total % 12}\""


def write_pdf(scene: Scene, path: Path, title: str | None = None) -> Path:
    fig = _fig(scene, title or scene.name)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, format="pdf")
    _close(fig)
    return path


def write_raster(scene: Scene, path: Path, title: str | None = None, dpi: int = 110) -> Path:
    """Render the scene to PNG or SVG (by suffix) — the ``haus render`` backend."""
    fig = _fig(scene, title or scene.name)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi)
    _close(fig)
    return path


def _close(fig: object) -> None:
    import matplotlib.pyplot as plt

    plt.close(fig)  # type: ignore[arg-type]
