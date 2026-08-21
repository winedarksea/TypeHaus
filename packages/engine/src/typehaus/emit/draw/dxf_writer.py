"""ezdxf writer for the 2D drawing IR (→ 20 §Drawing IR, WP2.6).

Writer obligations (→ 20): map ``layer`` → AIA names (already AIA in the IR), emit
``ArchDimension`` as real DXF ``DIMENSION`` entities with an architectural DIMSTYLE, and
stamp uid/tag XDATA. The writer computes **no** geometry — every coordinate comes from the
IR. Model space is inches with ``INSUNITS=1`` (→ 20 §DXF conventions).
"""

from __future__ import annotations

from pathlib import Path

from typehaus.emit.draw.door_symbols import DOOR_SYMBOL_NAMES, door_symbol_geometry
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
# Loaded by ``ezdxf.new(setup=True)``; used for symbol geometry above the plan cut plane.
_DASHED_LINETYPE = "DASHED"

# Point devices, drawn as a small circle on their own discipline layer — DXF has no marker
# glyphs, so the layer, not the shape, carries the kind. A smoke/CO alarm belongs here too:
# left out, it fell through to the window-glass branch and drew as glazing.
_DEVICE_SYMBOLS = frozenset({
    "register-supply", "register-return", "receptacle", "gfci", "receptacle_240",
    "switch", "light", "panel", "spot-elev", "utility-entry", "level-marker", "alarm",
    "junction_box", "meter", "disconnect", "data_outlet",
})

# Symbols drawn by a branch of their own; anything else falls through to the window mark,
# so an unlisted name is a wrong glyph rather than a missing one. Tests assert the plan
# builders emit nothing outside this set (in both writers, which must stay in step).
SYMBOL_NAMES_WITH_DEDICATED_GLYPH = (
    DOOR_SYMBOL_NAMES | _DEVICE_SYMBOLS | frozenset({"post", "span-arrow", "sleeve"})
)

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
    "S-FNDN": (9, 60),
    "S-FNDN-FTNG": (9, 25),
    "A-SLAB": (9, 25),
    "S-COLS": (3, 40),
    "S-BEAM": (3, 40),
    "S-WALL": (7, 70),
    "S-WALL-BELW": (9, 15),
    "S-FRAM-OPEN": (30, 25),
    "A-WALL-BELW": (9, 15),
    "P-SANR-PIPE": (33, 30),
    "P-DOMW-PIPE": (5, 30),
    # Stormwater (P-2xx drainage plans + the C-101 overlay); colours track the PDF palette.
    "P-STRM-GUTR": (140, 30),
    "P-STRM-LEDR": (140, 35),
    "P-STRM-TILE": (37, 25),
    "P-STRM-PIT": (36, 35),
    "C-STRM-DRAN": (150, 18),
    "M-HVAC-SDFF": (92, 30),
    "M-HVAC-RDFF": (94, 30),
    "M-HVAC-EXHS": (72, 30),
    "M-HVAC-EQPM": (92, 40),
    "E-POWR-DEVC": (10, 25),
    "E-POWR-CNDT": (12, 18),
    # Low-voltage is its own AIA discipline (E-COMM), not a flavour of E-POWR: the
    # separation is the whole point on site, where comms and power may not share a raceway,
    # and a low-voltage tech wants the branch-circuit layers off. Cyan, clear of the power
    # reds and the E-LITE ambers.
    "E-COMM-DEVC": (4, 25),
    "E-COMM-CNDT": (140, 18),
    "E-LITE": (50, 25),
    # Cove/tape runs read as a continuous source, not a device: a heavier line than the
    # fixtures so a 21' run is legible against the can grid it shares a room with.
    "E-LITE-COVE": (40, 40),
    # Switch legs. Thin and dashed — a leg is a control relationship the reader traces,
    # not a raceway anyone pulls.
    "E-LITE-CIRC": (52, 13),
    "C-PROP": (7, 30),
    "C-PROP-SETB": (1, 15),
    "C-UTIL-WATER": (5, 15),
    "C-UTIL-SEWER": (33, 15),
    "C-UTIL-GAS": (50, 15),
    "C-UTIL-POWER": (10, 15),
    "C-TOPO-ARRW": (94, 13),
    "C-TOPO-GRAD": (94, 18),
    "C-TOPO-MINR": (94, 9),
    "C-TOPO-IMPV": (43, 18),
    "L-SITE-GRAD": (94, 70),
    # Layers the PDF writer styled but the DXF table never carried, so they fell back to the
    # default pen on export. Colours track the PDF palette so a sheet reads the same in CAD.
    "A-ROOF": (7, 40),
    "A-FIXT": (4, 18),
    "A-FLR-HEAT": (12, 9),
    "A-SITE-ROOF": (7, 25),
    "A-SITE-WALL": (2, 18),
    "A-SITE-FOUND": (9, 13),
    "A-SITE-ANNO": (1, 18),
    "A-STAIR": (7, 25),
    "A-RAIL": (7, 20),
    "A-FURN": (43, 15),
    "E-POWR": (10, 25),
    "M-EQPT": (92, 25),
    "A-ANNO-TABL": (2, 15),
    "A-DETL-CMPT": (8, 18),
    "A-DETL-TRMT": (33, 18),
}


def model_text_height(height_in: float, height_pt: float | None, scene: Scene) -> float:
    """The height to bake into a model-space DXF entity, in model inches.

    DXF has no annotative-at-render-time concept the way matplotlib does — a ``TEXT`` entity
    carries a height in drawing units and that is that. But it has the *other* half: with
    ``doc.units = 1`` the paper units are inches too, so a printed size converts exactly,
    once the sheet's scale is known.

    ``height_pt / 72`` is the size on paper; multiplying by ``12 / frame.scale`` (model
    inches per paper inch, since ``scale`` is paper inches per model foot) puts it in the
    model. At 1-1/2" = 1'-0" a 7 pt label bakes to 0.778" against the 1.6" the ladder
    authored — the 2x oversize the rendered details showed, arrived at independently.

    With no frame there is no scale to convert through, so the model-space height stands.
    """
    if height_pt is None or scene.frame is None or scene.frame.scale <= 0.0:
        return height_in
    return height_pt / 72.0 * (12.0 / scene.frame.scale)


def write_dxf(scene: Scene, path: Path) -> Path:
    import ezdxf

    doc = ezdxf.new(setup=True)
    doc.units = 1  # INSUNITS=1 → inches
    doc.appids.add(_XDATA_APPID)
    _ensure_layers(doc, scene)
    _ensure_arch_dimstyle(doc)
    msp = doc.modelspace()

    paper = [n for n in scene.nodes if getattr(n, "space", "model") == "paper"]
    for node in scene.nodes:
        if getattr(node, "space", "model") == "paper":
            continue  # drawn into Layout1 below, in paper inches
        if isinstance(node, Polyline):
            _add_polyline(msp, node)
        elif isinstance(node, Hatch):
            _add_hatch(msp, node)
        elif isinstance(node, Text):
            _add_text(msp, node, scene)
        elif isinstance(node, ArchDimension):
            _add_dimension(msp, node, scene)
        elif isinstance(node, Symbol):
            _add_symbol(msp, node)
        elif isinstance(node, Leader):
            _add_leader(msp, node, scene)
        elif isinstance(node, Viewport):
            continue  # a Viewport node describes a sheet; the frame below is what we honour

    if scene.frame is not None:
        _compose_layout(doc, scene, paper)

    path.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(path)
    return path


def _compose_layout(doc, scene: Scene, paper_nodes) -> None:
    """Put the drawing in a real paper-space layout, at the scale the scene chose.

    This is where DXF is *better* placed than either raster writer: ``doc.units = 1`` makes
    paper units inches too, so the sheet, the viewport window and the annotation heights are
    all in one unit system and the layout needs no conversion at all. It is also, finally,
    where the ``Viewport`` node kind defined in ``scene.py`` and handled here since M2 —
    and never once emitted — actually lands.
    """
    frame = scene.frame
    paper_w, paper_h = frame.paper
    layout = (doc.layouts.get("Detail") if "Detail" in doc.layouts
              else doc.layouts.new("Detail"))
    layout.page_setup(size=(paper_w * 25.4, paper_h * 25.4), margins=(0, 0, 0, 0),
                      units="mm")
    vx, vy, vw, vh = frame.viewport
    if vw > 0.01 and vh > 0.01:
        layout.add_viewport(
            center=(vx + vw / 2.0, vy + vh / 2.0), size=(vw, vh),
            view_center_point=frame.center,
            # Model height the window shows: paper height x model inches per paper inch.
            view_height=vh * 12.0 / frame.scale)
    for node in paper_nodes:
        if isinstance(node, Polyline):
            _add_polyline(layout, node)
        elif isinstance(node, Hatch):
            _add_hatch(layout, node)
        elif isinstance(node, Text):
            _add_paper_text(layout, node)


def _add_paper_text(msp, node: Text) -> None:
    """Paper-space lettering: ``height_pt`` straight to inches, no scale to convert through.

    That is the definition of paper space — the sheet is 1:1, so 7 points is 7/72".
    """
    align = {"left": "LEFT", "center": "MIDDLE_CENTER", "right": "RIGHT"}[node.align]
    height = (node.height_pt / 72.0) if node.height_pt is not None else node.height
    e = msp.add_text(
        node.content,
        dxfattribs={"layer": node.layer, "height": height, "rotation": node.rotation},
    )
    e.set_placement(node.anchor,
                    align=getattr(__import__("ezdxf").enums.TextEntityAlignment, align))


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
        dxfattribs={"layer": node.layer, "lineweight": int(node.lineweight * 100),
                    "linetype": node.linetype},
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


def _add_text(msp: object, node: Text, scene: Scene) -> None:
    align = {"left": "LEFT", "center": "MIDDLE_CENTER", "right": "RIGHT"}[node.align]
    height = model_text_height(node.height, node.height_pt, scene)
    e = msp.add_text(  # type: ignore[attr-defined]
        node.content,
        dxfattribs={"layer": node.layer, "height": height, "rotation": node.rotation},
    )
    e.set_placement(node.anchor, align=getattr(__import__("ezdxf").enums.TextEntityAlignment, align))


def _add_dimension(msp: object, node: ArchDimension, scene: Scene) -> None:
    dx, dy = node.p1[0] - node.p0[0], node.p1[1] - node.p0[1]
    if abs(dx) < abs(dy):  # vertical dimension (→ elevation vertical dim string)
        base = (node.p0[0] + node.offset, node.p0[1])
        angle = 90.0
    else:
        base = (node.p0[0], node.p0[1] + node.offset)
        angle = 0.0
    dim = msp.add_linear_dim(  # type: ignore[attr-defined]
        base=base, p1=node.p0, p2=node.p1, angle=angle,
        dimstyle="ARCH",
        override={"dimtxt": model_text_height(3.0, node.height_pt, scene)},
        dxfattribs={"layer": node.layer},
    )
    dim.render()


def _add_symbol(msp: object, node: Symbol) -> None:
    import math

    w = node.params.get("width_in", node.scale) or node.scale
    if node.name in DOOR_SYMBOL_NAMES:
        # Every door glyph resolves through the shared geometry module, so the DXF and the
        # PDF of the same plan cannot drift apart when a new operation is added.
        geometry = door_symbol_geometry(node)
        for stroke in geometry.strokes:
            msp.add_lwpolyline(  # type: ignore[attr-defined]
                list(stroke.points),
                dxfattribs={"layer": node.layer,
                            "linetype": _DASHED_LINETYPE if stroke.dashed else "CONTINUOUS"},
            )
        for arc in geometry.arcs:
            msp.add_arc(  # type: ignore[attr-defined]
                center=arc.center, radius=arc.radius,
                start_angle=arc.start_angle_deg, end_angle=arc.end_angle_deg,
                dxfattribs={"layer": node.layer},
            )
    elif node.name == "post":
        half = max(w * 0.1, 2.0)
        x, y = node.insert
        msp.add_lwpolyline(  # type: ignore[attr-defined]
            [(x - half, y - half), (x + half, y - half), (x + half, y + half),
             (x - half, y + half)], close=True, dxfattribs={"layer": node.layer},
        )
    elif node.name == "span-arrow":
        a = math.radians(node.rotation)
        half = max(w, 12.0) / 2
        x, y = node.insert
        end = (x + half * math.cos(a), y + half * math.sin(a))
        start = (x - half * math.cos(a), y - half * math.sin(a))
        msp.add_line(start, end, dxfattribs={"layer": node.layer})  # type: ignore[attr-defined]
    elif node.name == "sleeve":
        msp.add_circle(node.insert, radius=max(w * 0.5, 1.0),  # type: ignore[attr-defined]
                       dxfattribs={"layer": node.layer})
    elif node.name in _DEVICE_SYMBOLS:
        msp.add_circle(node.insert, radius=max(w * 0.15, 1.5),  # type: ignore[attr-defined]
                       dxfattribs={"layer": node.layer})
    else:  # window mark: full glazing bar with a centre mullion tick
        a = math.radians(node.rotation)
        dx, dy = w * math.cos(a) / 2, w * math.sin(a) / 2
        nx, ny = -math.sin(a) * 2.5, math.cos(a) * 2.5
        msp.add_line((node.insert[0] - dx, node.insert[1] - dy),
                     (node.insert[0] + dx, node.insert[1] + dy),
                     dxfattribs={"layer": node.layer})  # type: ignore[attr-defined]
        msp.add_line((node.insert[0] - nx, node.insert[1] - ny),
                     (node.insert[0] + nx, node.insert[1] + ny),
                     dxfattribs={"layer": node.layer})  # type: ignore[attr-defined]


def _add_leader(msp: object, node: Leader, scene: Scene) -> None:
    """The leader line, plus its note at the **label** end.

    Two long-standing bugs, both here. The height was hardcoded at 3.0, so ``scene.py``'s
    claim that "both writers honor ``Leader.height``" was simply false — every DXF leader
    lettered the same size whatever the IR said. And ``set_placement(node.to)`` put the text
    at the *arrow tip*, inside the thing the leader points at, where both other renderers put
    it at ``node.at``. A note printed over the hatch it labels is not a note.
    """
    msp.add_leader([node.at, node.to], dxfattribs={"layer": node.layer})  # type: ignore[attr-defined]
    height = model_text_height(node.height, node.height_pt, scene)
    align = "RIGHT" if node.at[0] < node.to[0] else "LEFT"
    e = msp.add_text(  # type: ignore[attr-defined]
        node.text, dxfattribs={"layer": node.layer, "height": height},
    )
    e.set_placement(node.at,
                    align=getattr(__import__("ezdxf").enums.TextEntityAlignment, align))
