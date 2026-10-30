"""The shop drawing set for one countertop material: a cover, then one page per piece.

Cover: the material block (product, colour, thickness, finish, edge profile in the
fabricator's words, slab size) and the piece schedule. Each piece page: the piece drawn to
fit, overall dimensions, finished edges heavy with an edge legend, R callouts, cutout and
hole centres located from the left end and the front edge, the narrowest webs, and the
holds. Palette and page from ``takeoff/millwork_pdf.py``; byte-deterministic like it.
"""

from __future__ import annotations

import io
from html import escape
from pathlib import Path

from reportlab.platypus import Flowable

from typehaus.takeoff.millwork_pdf import ACCENT, BODY_W, INK, MARGIN, MUTED, PAGE_H, PAGE_W, STRIPE
from typehaus.takeoff.stone_pieces import FabricatedPiece, inches_text

#: Edge kind -> (stroke colour, width pt, dash pattern, legend words).
EDGE_STYLE = {
    "finished": (ACCENT, 2.6, None, "FINISHED (eased, polished) edge"),
    "wall": ("#3B6EA8", 0.9, (4, 2), "against a wall: scribe, unfinished"),
    "seam": ("#7A4FA0", 0.9, (1, 2), "seam to the next piece"),
    "abutment": ("#C27C2C", 0.9, (6, 2, 1, 2), "butts a tall cabinet or appliance"),
}
OPENING = "#B03A6E"
_DRAW_H = 4.6 * 72


def write_stone_pdf(path: Path, house: str, material: dict[str, str],
                    pieces: list[FabricatedPiece]) -> Path:
    from reportlab import rl_config

    path.parent.mkdir(parents=True, exist_ok=True)
    previous = rl_config.invariant
    rl_config.invariant = 1
    try:
        buffer = io.BytesIO()
        _build(buffer, house, material, pieces)
        path.write_bytes(buffer.getvalue())
    finally:
        rl_config.invariant = previous
    return path


def _styles():  # type: ignore[no-untyped-def]
    from reportlab.lib.colors import HexColor
    from reportlab.lib.styles import ParagraphStyle

    cell = ParagraphStyle("cell", fontName="Helvetica", fontSize=7.4, leading=9,
                          textColor=HexColor("#111111"))
    return {
        "cell": cell,
        "head": ParagraphStyle("head", parent=cell, fontName="Helvetica-Bold",
                               textColor=HexColor("#FFFFFF")),
        "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=12.5,
                                leading=15, textColor=HexColor("#FFFFFF")),
        "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=8.5, leading=11,
                             textColor=HexColor(ACCENT), spaceBefore=6, spaceAfter=3),
        "note": ParagraphStyle("note", parent=cell, leading=10),
    }


def _band(text: str, styles):  # type: ignore[no-untyped-def]
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import Paragraph, Table, TableStyle

    band = Table([[Paragraph(text, styles["title"])]], colWidths=(BODY_W,))
    band.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), HexColor(INK)),
                              ("LEFTPADDING", (0, 0), (-1, -1), 8),
                              ("TOPPADDING", (0, 0), (-1, -1), 3),
                              ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    return band


def _table(rows: list[list[str]], widths, styles, header: bool = True):  # type: ignore[no-untyped-def]
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import Paragraph, Table, TableStyle

    data = [[Paragraph(cell, styles["head" if header and r == 0 else "cell"]) for cell in row]
            for r, row in enumerate(rows)]
    table = Table(data, colWidths=widths, hAlign="LEFT", repeatRows=1 if header else 0)
    commands = [("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1 if header else 0), (-1, -1),
                 [HexColor(STRIPE), HexColor("#FFFFFF")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3)]
    if header:
        commands.append(("BACKGROUND", (0, 0), (-1, 0), HexColor(ACCENT)))
    table.setStyle(TableStyle(commands))
    return table


def _cover(house: str, material: dict[str, str], pieces: list[FabricatedPiece], styles):  # type: ignore[no-untyped-def]
    from reportlab.platypus import Paragraph, Spacer

    gross = sum(piece.area_sqft for piece in pieces)
    block = [[f"<b>{escape(key)}</b>", escape(value)] for key, value in material.items()]
    block.append(["<b>Pieces</b>", f"{len(pieces)} ({gross:.2f} SF gross, square-cornered)"])
    schedule = [["TAG", "KIND", "LOCATION", "L × D (IN)", "SF", "CORNERS",
                 "CUTOUTS / HOLES", "FINISHED EDGE"]]
    for piece in pieces:
        radii = sorted({inches_text(r) for r in piece.radii_in if r > 0.0})
        openings = [f"{len(piece.cutouts)} cutout" + ("s" if len(piece.cutouts) != 1 else "")
                    ] if piece.cutouts else []
        openings += [f'{inches_text(h.diameter_in)} {escape(h.purpose)}' for h in piece.holes]
        schedule.append([
            f"<b>{escape(piece.tag)}</b>", piece.kind, escape(piece.location),
            f"{piece.length_in:.3f} × {piece.depth_in:.3f}", f"{piece.area_sqft:.2f}",
            "R " + ", ".join(radii) if radii else "square", "; ".join(openings) or "–",
            f'{piece.edge_length_in("finished"):.1f}"'])
    widths = [x * 72 for x in (1.55, 0.45, 2.9, 1.15, 0.45, 0.8, 1.6, 0.75)]
    return [_band(f"{escape(house.upper())} HOUSE&nbsp;&nbsp;|&nbsp;&nbsp;COUNTERTOPS — "
                  f"{escape(material['Material'])}", styles), Spacer(1, 6),
            _table(block, (1.4 * 72, BODY_W - 1.4 * 72), styles, header=False),
            Paragraph("Piece schedule", styles["h2"]), _table(schedule, widths, styles),
            Paragraph("Edges", styles["h2"]),
            Paragraph("&nbsp;&nbsp;•&nbsp;&nbsp;".join(
                f"<b>{kind}</b>: {words}" for kind, (_c, _w, _d, words) in EDGE_STYLE.items()),
                styles["note"]),
            Paragraph("Each piece's DXF (inches) carries the true arcs; this set is for "
                      "quoting and pre-planning. Every piece is field templated.",
                      styles["note"])]


def _piece_story(piece: FabricatedPiece, styles):  # type: ignore[no-untyped-def]
    from reportlab.platypus import PageBreak, Paragraph, Spacer

    info = [
        ["<b>Material</b>", escape(f"{piece.material_name} — {piece.product}".strip(" —"))],
        ["<b>Thickness / edge</b>",
         escape(f'{piece.thickness_in:.3f}"; {piece.profile_words}')],
        ["<b>Overall</b>", f'{piece.length_in:.3f}" × {piece.depth_in:.3f}"; '
                           f"{piece.area_sqft:.2f} SF gross"],
        ["<b>Location</b>", escape(piece.location)],
    ]
    if piece.support:
        info.append(["<b>Support</b>", escape(piece.support)])
    for web in piece.webs:
        info.append(["<b>Web</b>", escape(f'{web.distance_in:.3f}" — {web.label}')])
    holds = "<br/>".join(f"{n}. {escape(text)}" for n, text in enumerate(piece.holds, 1))
    return [PageBreak(), _band(f"{escape(piece.tag)}&nbsp;&nbsp;|&nbsp;&nbsp;"
                               f"{escape(piece.kind.upper())}", styles), Spacer(1, 4),
            PieceDrawing(piece), Spacer(1, 4),
            _table(info, (1.3 * 72, BODY_W - 1.3 * 72), styles, header=False),
            Paragraph("Holds", styles["h2"]), Paragraph(holds, styles["note"])]


class PieceDrawing(Flowable):  # type: ignore[misc]
    """The piece fit to the page width and ``_DRAW_H``, with its annotation."""

    def __init__(self, piece: FabricatedPiece) -> None:
        super().__init__()
        self.piece = piece

    def wrap(self, available_width, available_height):  # type: ignore[no-untyped-def]
        return BODY_W, _DRAW_H

    def draw(self) -> None:
        from reportlab.lib.colors import HexColor

        piece, canvas = self.piece, self.canv
        pad = 0.75 * 72
        scale = min((BODY_W - 2 * pad) / max(piece.length_in, 1e-6),
                    (_DRAW_H - 2 * pad) / max(piece.depth_in, 1e-6))
        ox = (BODY_W - piece.length_in * scale) / 2.0
        oy = pad

        def at(point):  # type: ignore[no-untyped-def]
            return ox + point[0] * scale, oy + point[1] * scale

        def poly(points, fill: bool = False) -> None:  # type: ignore[no-untyped-def]
            path = canvas.beginPath()
            path.moveTo(*at(points[0]))
            for point in points[1:]:
                path.lineTo(*at(point))
            path.close()
            canvas.drawPath(path, stroke=1, fill=1 if fill else 0)

        canvas.saveState()
        canvas.setFillColor(HexColor("#EEF1F0"))
        canvas.setStrokeColor(HexColor(MUTED))
        canvas.setLineWidth(0.4)
        poly(piece.cut_ring(16), fill=True)
        for kind, (start, end) in piece.edge_runs():
            color, width, dash, _ = EDGE_STYLE.get(kind, EDGE_STYLE["wall"])
            canvas.setStrokeColor(HexColor(color))
            canvas.setLineWidth(width)
            if dash:
                canvas.setDash(list(dash))
            else:
                canvas.setDash()
            canvas.line(*at(start), *at(end))
        canvas.setDash()
        canvas.setStrokeColor(HexColor(OPENING))
        canvas.setFillColor(HexColor("#FFFFFF"))
        canvas.setLineWidth(0.9)
        for cutout in piece.cutouts:
            poly(cutout.ring, fill=True)
        for hole in piece.holes:
            canvas.circle(*at(hole.center), hole.diameter_in / 2.0 * scale, stroke=1, fill=1)
        self._annotate(at, scale)
        canvas.restoreState()

    def _annotate(self, at, scale: float) -> None:  # type: ignore[no-untyped-def]
        from reportlab.lib.colors import HexColor

        piece, canvas = self.piece, self.canv
        canvas.setFont("Helvetica", 6.6)
        canvas.setFillColor(HexColor(INK))
        canvas.setStrokeColor(HexColor(MUTED))
        canvas.setLineWidth(0.4)
        _dim(canvas, at((0, 0)), at((piece.length_in, 0)), -18, f'{piece.length_in:.3f}"')
        _dim(canvas, at((0, 0)), at((0, piece.depth_in)), 18, f'{piece.depth_in:.3f}"',
             vertical=True)
        for fillet in piece.fillets:
            x, y = at(((fillet.start[0] + fillet.end[0]) / 2.0,
                       (fillet.start[1] + fillet.end[1]) / 2.0))
            canvas.drawString(x + 3, y + 3, f"R{inches_text(fillet.radius_m)}"
                              + (" (clamped)" if fillet.clamped else ""))
        canvas.setFillColor(HexColor(OPENING))
        canvas.setStrokeColor(HexColor(OPENING))
        for hole in piece.holes:
            x, y = _centre_lines(canvas, at, hole.center)
            reach = hole.diameter_in / 2.0 * scale + 4
            canvas.drawString(x + reach, y + 1,
                              f"{inches_text(hole.diameter_in)} dia. {hole.purpose}")
            canvas.drawString(x + reach, y - 8, _cl(hole.center))
        for cutout in piece.cutouts:
            xs, ys = [p[0] for p in cutout.ring], [p[1] for p in cutout.ring]
            centre = ((min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0)
            x, y = _centre_lines(canvas, at, centre)
            for row, text in enumerate((f"{max(xs) - min(xs):.3f} × {max(ys) - min(ys):.3f}",
                                        cutout.label, _cl(centre))):
                canvas.drawCentredString(x, y + 10 - row * 9, text)
        canvas.setStrokeColor(HexColor("#C0392B"))
        canvas.setFillColor(HexColor("#C0392B"))
        for web in piece.webs:
            a, b = at(web.start), at(web.end)
            canvas.line(*a, *b)
            canvas.drawRightString((a[0] + b[0]) / 2 - 3, (a[1] + b[1]) / 2 - 2,
                                   f'web {web.distance_in:.3f}"')
        _legend(canvas)


def _cl(centre) -> str:  # type: ignore[no-untyped-def]
    return f'CL {centre[0]:.3f}" from left end, {centre[1]:.3f}" from front'


def _centre_lines(canvas, at, centre):  # type: ignore[no-untyped-def]
    """Dashed witness lines from the left end and the front edge to a centre."""
    x, y = at(centre)
    canvas.setDash(2, 2)
    canvas.line(at((0, centre[1]))[0], y, x, y)
    canvas.line(x, at((centre[0], 0))[1], x, y)
    canvas.setDash()
    return x, y


def _legend(canvas) -> None:  # type: ignore[no-untyped-def]
    from reportlab.lib.colors import HexColor

    x = 0.0
    for color, width, dash, words in EDGE_STYLE.values():
        canvas.setStrokeColor(HexColor(color))
        canvas.setLineWidth(width)
        if dash:
            canvas.setDash(list(dash))
        canvas.line(x, 4, x + 22, 4)
        canvas.setDash()
        canvas.setFillColor(HexColor(INK))
        canvas.drawString(x + 26, 1.5, words)
        x += 30 + canvas.stringWidth(words, "Helvetica", 6.6) + 14


def _dim(canvas, a, b, offset: float, text: str, vertical: bool = False) -> None:  # type: ignore[no-untyped-def]
    """A plain dimension line offset from ``a``-``b`` (pt), text at its middle."""
    if vertical:
        x = a[0] - offset
        canvas.line(x, a[1], x, b[1])
        canvas.line(x - 3, a[1], x + 3, a[1])
        canvas.line(x - 3, b[1], x + 3, b[1])
        canvas.saveState()
        canvas.translate(x - 3, (a[1] + b[1]) / 2)
        canvas.rotate(90)
        canvas.drawCentredString(0, 0, text)
        canvas.restoreState()
        return
    y = a[1] + offset
    canvas.line(a[0], y, b[0], y)
    canvas.line(a[0], y - 3, a[0], y + 3)
    canvas.line(b[0], y - 3, b[0], y + 3)
    canvas.drawCentredString((a[0] + b[0]) / 2, y - 9, text)


def _build(target, house: str, material: dict[str, str], pieces: list[FabricatedPiece]) -> None:  # type: ignore[no-untyped-def]
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import SimpleDocTemplate

    styles = _styles()
    story = _cover(house, material, pieces, styles)
    for piece in pieces:
        story.extend(_piece_story(piece, styles))

    def footer(canvas, document):  # type: ignore[no-untyped-def]
        canvas.saveState()
        canvas.setStrokeColor(HexColor(ACCENT))
        canvas.setLineWidth(0.65)
        canvas.line(MARGIN, MARGIN, PAGE_W - MARGIN, MARGIN)
        canvas.setFillColor(HexColor(MUTED))
        canvas.setFont("Helvetica", 5.8)
        canvas.drawString(MARGIN, MARGIN - 8,
                          "Design intent for quoting and pre-planning: field template after "
                          "cabinets are set. Inches. Unpriced.")
        canvas.drawRightString(PAGE_W - MARGIN, MARGIN - 8,
                               f"Countertops — {material['Material']} — {document.page}")
        canvas.restoreState()

    SimpleDocTemplate(target, pagesize=(PAGE_W, PAGE_H), leftMargin=MARGIN,
                      rightMargin=MARGIN, topMargin=MARGIN, bottomMargin=MARGIN + 3,
                      title=f"{house} countertops", creator="Type:Haus").build(
                          story, onFirstPage=footer, onLaterPages=footer)
