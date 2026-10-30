"""One DXF per fabricated piece, in inches, with true arcs.

Format: ``docs/countertop-fabrication-format.md``.

Written with ezdxf directly rather than through the Scene IR: a Scene ``Polyline`` has no
arcs, and a CNC file wants the bulged ``LWPOLYLINE`` a saw or router reads as one profile.

Layers: ``CUT`` (the closed outline), ``CUTOUT``, ``HOLE`` (circles), one ``EDGE-<KIND>``
overlay per edge kind, ``DIMS`` and ``TEXT``. The outline carries the model uid/tag as
``TYPEHAUS`` XDATA, the convention ``emit/draw/dxf_writer.py`` uses.
"""

from __future__ import annotations

from pathlib import Path

from typehaus.takeoff.stone_pieces import FabricatedPiece, inches_text

_XDATA_APPID = "TYPEHAUS"
#: (layer, ACI colour): cut red, openings magenta, finished edges green, scribed blue.
LAYERS = (("CUT", 1), ("CUTOUT", 6), ("HOLE", 6), ("EDGE-FINISHED", 3), ("EDGE-WALL", 5),
          ("EDGE-SEAM", 4), ("EDGE-ABUTMENT", 30), ("DIMS", 8), ("TEXT", 7))
_TEXT_HEIGHT_IN = 0.75
_DIM_OFFSET_IN = 3.0
_DIMSTYLE = "TYPEHAUS_IN"


def write_piece_dxf(piece: FabricatedPiece, path: Path) -> Path:
    import ezdxf

    doc = ezdxf.new(setup=True)
    doc.units = 1  # INSUNITS=1 -> inches
    doc.header["$MEASUREMENT"] = 0
    doc.appids.add(_XDATA_APPID)
    for name, color in LAYERS:
        doc.layers.add(name, color=color)
    # Decimal inches to 1/1000, text sized for a shop print of one piece.
    doc.dimstyles.new(_DIMSTYLE, dxfattribs={
        "dimtxt": 0.5, "dimasz": 0.25, "dimexe": 0.25, "dimexo": 0.125, "dimgap": 0.1,
        "dimlunit": 2, "dimdec": 3, "dimtad": 1, "dimzin": 8})
    msp = doc.modelspace()

    outline = msp.add_lwpolyline(_bulged(piece), format="xyb", close=True,
                                 dxfattribs={"layer": "CUT"})
    outline.set_xdata(_XDATA_APPID, [(1000, f"uid={piece.uid}"), (1000, f"tag={piece.tag}")])
    for cutout in piece.cutouts:
        msp.add_lwpolyline(cutout.ring, close=True, dxfattribs={"layer": "CUTOUT"})
    for hole in piece.holes:
        msp.add_circle(hole.center, hole.diameter_in / 2.0, dxfattribs={"layer": "HOLE"})
    for kind, (start, end) in piece.edge_runs():
        msp.add_line(start, end, dxfattribs={"layer": f"EDGE-{kind.upper()}"})
    _dimensions(msp, piece)
    _labels(msp, piece)

    path.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(path)
    return path


def _bulged(piece: FabricatedPiece) -> list[tuple[float, float, float]]:
    """``(x, y, bulge)`` vertices: a filleted corner is its two tangent points and one arc."""
    fillets = {fillet.index: fillet for fillet in piece.fillets}
    points: list[tuple[float, float, float]] = []
    for index, vertex in enumerate(piece.outline):
        fillet = fillets.get(index)
        if fillet is None:
            points.append((vertex[0], vertex[1], 0.0))
        else:
            points.append((fillet.start[0], fillet.start[1], fillet.bulge))
            points.append((fillet.end[0], fillet.end[1], 0.0))
    return points


def _dimensions(msp, piece: FabricatedPiece) -> None:  # type: ignore[no-untyped-def]
    attribs = {"layer": "DIMS"}
    msp.add_linear_dim(base=(0.0, -_DIM_OFFSET_IN), p1=(0.0, 0.0), p2=(piece.length_in, 0.0),
                       dimstyle=_DIMSTYLE, dxfattribs=attribs).render()
    msp.add_linear_dim(base=(-_DIM_OFFSET_IN, 0.0), p1=(0.0, 0.0), p2=(0.0, piece.depth_in),
                       angle=90, dimstyle=_DIMSTYLE, dxfattribs=attribs).render()
    for hole in piece.holes:
        _centre_dims(msp, hole.center, attribs)
    for cutout in piece.cutouts:
        xs = [x for x, _ in cutout.ring]
        ys = [y for _, y in cutout.ring]
        _centre_dims(msp, ((min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0), attribs)


def _centre_dims(msp, centre, attribs) -> None:  # type: ignore[no-untyped-def]
    """A centre located from the left end and the front (y = 0) edge."""
    x, y = centre
    msp.add_linear_dim(base=(0.0, y), p1=(0.0, y), p2=(x, y), dimstyle=_DIMSTYLE,
                       dxfattribs=attribs).render()
    msp.add_linear_dim(base=(x, 0.0), p1=(x, 0.0), p2=(x, y), angle=90,
                       dimstyle=_DIMSTYLE, dxfattribs=attribs).render()


def _labels(msp, piece: FabricatedPiece) -> None:  # type: ignore[no-untyped-def]
    lines = [piece.tag, f"{piece.material_name}",
             f'{piece.thickness_in:.3f}" thick - {piece.profile_words}',
             f'{piece.length_in:.3f}" x {piece.depth_in:.3f}"']
    top = piece.depth_in + 2.0 + _TEXT_HEIGHT_IN * 1.6 * (len(lines) - 1)
    for row, text in enumerate(lines):
        msp.add_text(text, height=_TEXT_HEIGHT_IN, dxfattribs={"layer": "TEXT"}).set_placement(
            (0.0, top - row * _TEXT_HEIGHT_IN * 1.6))
    for fillet in piece.fillets:
        x = (fillet.start[0] + fillet.end[0]) / 2.0
        y = (fillet.start[1] + fillet.end[1]) / 2.0
        msp.add_text(f"R{inches_text(fillet.radius_m)}", height=_TEXT_HEIGHT_IN / 2.0,
                     dxfattribs={"layer": "TEXT"}).set_placement((x, y))
    for hole in piece.holes:
        msp.add_text(f'{hole.diameter_in:.3f}" dia. - {hole.purpose}',
                     height=_TEXT_HEIGHT_IN / 2.0, dxfattribs={"layer": "TEXT"}).set_placement(
            (hole.center[0] + hole.diameter_in, hole.center[1]))
    for cutout in piece.cutouts:
        x = min(p[0] for p in cutout.ring) + 0.5
        y = (min(p[1] for p in cutout.ring) + max(p[1] for p in cutout.ring)) / 2.0
        msp.add_text(cutout.label, height=_TEXT_HEIGHT_IN / 2.0,
                     dxfattribs={"layer": "TEXT"}).set_placement((x, y))
