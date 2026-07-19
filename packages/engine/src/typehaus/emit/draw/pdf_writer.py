"""matplotlib writer for the 2D drawing IR — PDF sheet + headless raster (→ 20 §WP2.7).

The same IR that feeds the DXF writer renders here, so PDF and DXF agree by construction
(→ 20: "PDF and DXF of the same slice visibly agree"). This writer also backs ``haus render``
(→ 20 §Agent eyes) — it draws to PNG/SVG so Claude can *look* at the plan it just edited.
Neither writer computes geometry; placement math already happened IR-side.
"""

from __future__ import annotations

import math
from pathlib import Path

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
}
_HATCH_MPL = {"batt": "....", "osb": "//", "lumber": "\\\\", "concrete": "..", "SOLID": None}


def _fig(scene: Scene, title: str | None):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(11, 8.5))
    ax.set_aspect("equal")
    ax.axis("off")
    _render_nodes(ax, scene)
    if title:
        ax.set_title(title, fontsize=9, family="monospace", loc="left")
    ax.autoscale_view()
    fig.tight_layout()
    return fig


def _render_nodes(ax: object, scene: Scene) -> None:
    from matplotlib.patches import Arc, PathPatch, Polygon
    from matplotlib.path import Path as MplPath

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
            hatch = _HATCH_MPL.get(node.pattern, "..")
            ax.add_patch(Polygon(list(node.boundary), closed=True, fill=False,
                                 hatch=hatch, edgecolor="#9a8a5a", linewidth=0.0))
        elif isinstance(node, Text):
            ha = {"left": "left", "center": "center", "right": "right"}[node.align]
            ax.text(node.anchor[0], node.anchor[1], node.content, fontsize=node.height * 1.7,
                    ha=ha, va="center", rotation=node.rotation, family="monospace",
                    color="#222")
        elif isinstance(node, ArchDimension):
            _draw_dimension(ax, node)
        elif isinstance(node, Symbol):
            _draw_symbol(ax, node, Arc)
        elif isinstance(node, Leader):
            ax.plot([node.at[0], node.to[0]], [node.at[1], node.to[1]],
                    color="#555", linewidth=0.5)
            ax.text(node.to[0], node.to[1], node.text, fontsize=6, family="monospace")
    _ = (PathPatch, MplPath)  # imported for parity with richer node kinds


def _draw_dimension(ax: object, node: ArchDimension) -> None:
    y = node.p0[1] + node.offset
    ax.annotate("", xy=(node.p1[0], y), xytext=(node.p0[0], y),
                arrowprops=dict(arrowstyle="<->", color="#204070", lw=0.6))
    dist_in = math.hypot(node.p1[0] - node.p0[0], node.p1[1] - node.p0[1])
    label = node.text or _feet_inches(dist_in)
    ax.text((node.p0[0] + node.p1[0]) / 2, y + 2, label, fontsize=6.5, ha="center",
            family="monospace", color="#204070")


def _draw_symbol(ax: object, node: Symbol, Arc: object) -> None:
    w = node.params.get("width_in", node.scale) or node.scale
    if node.name == "door-swing":
        a = math.radians(node.rotation)
        end = (node.insert[0] + w * math.cos(a + math.pi / 2),
               node.insert[1] + w * math.sin(a + math.pi / 2))
        ax.plot([node.insert[0], end[0]], [node.insert[1], end[1]], color="#a05a20", lw=0.9)
        ax.add_patch(Arc(node.insert, 2 * w, 2 * w, angle=0,
                         theta1=node.rotation, theta2=node.rotation + 90,
                         edgecolor="#a05a20", linewidth=0.6))
    else:
        ax.plot(node.insert[0], node.insert[1], marker="o", markersize=2,
                color="#3a6a8a")


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
