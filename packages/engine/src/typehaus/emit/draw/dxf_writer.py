"""ezdxf writer for the 2D drawing IR (→ 20 §Drawing IR, WP2.6).

Writer obligations (→ 20): map ``layer`` → AIA names (already AIA in the IR), emit
``ArchDimension`` as real DXF ``DIMENSION`` entities with an architectural DIMSTYLE, and
stamp uid/tag XDATA. The writer computes **no** geometry — every coordinate comes from the
IR. Model space is inches with ``INSUNITS=1`` (→ 20 §DXF conventions).
"""

from __future__ import annotations

from pathlib import Path

from typehaus.emit.draw.scene import (
    ArchDimension,
    Hatch,
    Leader,
    Polyline,
    Scene,
    Symbol,
    Text,
    Viewport,
)

_XDATA_APPID = "TYPEHAUS"

# AIA layer → (ACI color, lineweight in 1/100 mm). A small default palette.
_LAYER_STYLE = {
    "A-WALL": (7, 35),
    "A-WALL-FINI": (8, 18),
    "A-WALL-INSU": (5, 13),
    "A-WALL-PATT": (250, 9),
    "S-FRAM": (3, 50),
    "A-DOOR": (30, 25),
    "A-GLAZ": (4, 18),
    "A-AREA-IDEN": (2, 18),
    "A-ANNO-DIMS": (1, 13),
    "A-ANNO-TEXT": (2, 18),
    "A-ANNO-SYMB": (6, 18),
}


def write_dxf(scene: Scene, path: Path) -> Path:
    import ezdxf

    doc = ezdxf.new(setup=True)
    doc.units = 1  # INSUNITS=1 → inches
    doc.appids.add(_XDATA_APPID)
    _ensure_layers(doc, scene)
    _ensure_arch_dimstyle(doc)
    msp = doc.modelspace()

    for node in scene.nodes:
        if isinstance(node, Polyline):
            _add_polyline(msp, node)
        elif isinstance(node, Hatch):
            _add_hatch(msp, node)
        elif isinstance(node, Text):
            _add_text(msp, node)
        elif isinstance(node, ArchDimension):
            _add_dimension(msp, node)
        elif isinstance(node, Symbol):
            _add_symbol(msp, node)
        elif isinstance(node, Leader):
            _add_leader(msp, node)
        elif isinstance(node, Viewport):
            continue  # paperspace composition is M3 (§Sheets)

    path.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(path)
    return path


def _ensure_layers(doc: object, scene: Scene) -> None:
    for name in sorted(scene.by_layer()):
        color, lw = _LAYER_STYLE.get(name, (7, 18))
        if name not in doc.layers:  # type: ignore[operator]
            doc.layers.add(name, color=color, lineweight=lw)  # type: ignore[attr-defined]


def _ensure_arch_dimstyle(doc: object) -> None:
    if "ARCH" in doc.dimstyles:  # type: ignore[attr-defined]
        return
    dimstyle = doc.dimstyles.add("ARCH")  # type: ignore[attr-defined]
    # Architectural: tick marks, feet-and-inches text, small text height.
    dimstyle.dxf.dimtxt = 3.0
    dimstyle.dxf.dimasz = 2.0
    dimstyle.dxf.dimtad = 1  # text above the dimension line
    dimstyle.dxf.dimtih = 0
    dimstyle.dxf.dimlunit = 4  # architectural units
    dimstyle.dxf.dimlfac = 1.0


def _xdata(entity: object, node: Polyline) -> None:
    if node.uid is None and node.tag is None:
        return
    entity.set_xdata(  # type: ignore[attr-defined]
        _XDATA_APPID,
        [(1000, f"uid={node.uid or ''}"), (1000, f"tag={node.tag or ''}")],
    )


def _add_polyline(msp: object, node: Polyline) -> None:
    e = msp.add_lwpolyline(  # type: ignore[attr-defined]
        list(node.points), close=node.closed,
        dxfattribs={"layer": node.layer, "lineweight": int(node.lineweight * 100)},
    )
    _xdata(e, node)


def _add_hatch(msp: object, node: Hatch) -> None:
    pattern = "ANSI31" if node.pattern in ("lumber", "structure") else "ANSI37"
    h = msp.add_hatch(color=252, dxfattribs={"layer": node.layer})  # type: ignore[attr-defined]
    try:
        h.set_pattern_fill(pattern, scale=max(node.scale, 0.5) * 6.0, angle=node.angle)
    except Exception:  # noqa: BLE001 - pattern table variance across ezdxf builds
        h.set_solid_fill(color=252)
    h.paths.add_polyline_path(list(node.boundary), is_closed=True)


def _add_text(msp: object, node: Text) -> None:
    align = {"left": "LEFT", "center": "MIDDLE_CENTER", "right": "RIGHT"}[node.align]
    e = msp.add_text(  # type: ignore[attr-defined]
        node.content,
        dxfattribs={"layer": node.layer, "height": node.height, "rotation": node.rotation},
    )
    e.set_placement(node.anchor, align=getattr(__import__("ezdxf").enums.TextEntityAlignment, align))


def _add_dimension(msp: object, node: ArchDimension) -> None:
    dim = msp.add_linear_dim(  # type: ignore[attr-defined]
        base=(node.p0[0], node.p0[1] + node.offset),
        p1=node.p0, p2=node.p1,
        dimstyle="ARCH",
        override={"dimtxt": 3.0},
        dxfattribs={"layer": node.layer},
    )
    dim.render()


def _add_symbol(msp: object, node: Symbol) -> None:
    import math

    w = node.params.get("width_in", node.scale) or node.scale
    if node.name == "door-swing":
        # Leaf + 90° swing arc, oriented along the wall.
        a = math.radians(node.rotation)
        hinge = node.insert
        leaf_end = (hinge[0] + w * math.cos(a + math.pi / 2),
                    hinge[1] + w * math.sin(a + math.pi / 2))
        msp.add_line(hinge, leaf_end, dxfattribs={"layer": node.layer})  # type: ignore[attr-defined]
        msp.add_arc(  # type: ignore[attr-defined]
            center=hinge, radius=w,
            start_angle=node.rotation, end_angle=node.rotation + 90,
            dxfattribs={"layer": node.layer},
        )
    else:  # window mark: a short cross tick
        msp.add_circle(node.insert, radius=max(w * 0.1, 1.0),  # type: ignore[attr-defined]
                       dxfattribs={"layer": node.layer})


def _add_leader(msp: object, node: Leader) -> None:
    msp.add_leader([node.at, node.to], dxfattribs={"layer": node.layer})  # type: ignore[attr-defined]
    msp.add_text(  # type: ignore[attr-defined]
        node.text, dxfattribs={"layer": node.layer, "height": 3.0},
    ).set_placement(node.to)
