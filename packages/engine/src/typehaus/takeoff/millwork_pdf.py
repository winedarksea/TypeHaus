"""Readable shop schedules from the same flattened rows as CSV/Markdown exports."""
from __future__ import annotations

from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    LongTable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    TableStyle,
)

PAGE_MARGIN_PT = 30
CELL_FONT_PT = 7
COLUMNS = ("use", "location", "material", "pieces", "finished_size", "nominal_stock",
           "grain_direction", "stock_note")
PANEL_COLUMNS = ("material", "sheets_to_order", "sheet_size", "nominal_stock",
                 "panel_grade", "panel_core", "stock_note")
PANEL_COLUMN_WIDTHS_PT = (90, 45, 65, 60, 40, 65, 298)
COLUMN_WIDTHS_PT = (54, 55, 78, 36, 85, 58, 65, 232)


def write_millwork_pdf(path: Path, house: str, hardwood: list[dict], panels: list[dict],
                       bench_specs=()) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    styles["BodyText"].fontSize = CELL_FONT_PT
    styles["BodyText"].leading = CELL_FONT_PT + 2

    def paragraph(value):
        return Paragraph(escape(str(value)), styles["BodyText"])

    story = [Paragraph(f"{escape(house.title())} — Millwork and plywood order", styles["Title"]),
             paragraph("Unpriced shop view: costs remain in their original estimate sections. "
                       "Solid wood dimensions are finished inches. Plywood quantities are whole "
                       "stock sheets from a conservative grain-aligned blank layout, including "
                       "kerf and "
                       "edge trim, with no spare sheets. Confirm actual thickness before joinery."),
             Spacer(1, 12)]
    for title, rows in (("Solid wood", hardwood), ("Plywood sheets to order", panels)):
        story.append(Paragraph(title, styles["Heading2"]))
        if not rows:
            story.append(paragraph("None scheduled."))
            continue
        columns = PANEL_COLUMNS if title == "Plywood sheets to order" else COLUMNS
        widths = PANEL_COLUMN_WIDTHS_PT if columns == PANEL_COLUMNS else COLUMN_WIDTHS_PT
        data = [[paragraph(column.replace("_", " ")) for column in columns]]
        for row in rows:
            record = dict(row)
            if row.get("stock_kind") == "panel":
                record["stock_note"] = f"Finish: {row['finish']}; {row['stock_note']}"
            else:
                record["stock_note"] = (f"{row.get('rough_board_feet', '')} rough bf; "
                                        f"{row.get('layup', '')}; {row.get('stock_note', '')}")
            data.append([paragraph(record.get(column, "")) for column in columns])
        table = LongTable(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e9e4dc")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f6f2")]),
            ("GRID", (0, 0), (-1, -1), .25, colors.HexColor("#d4cfc5")),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.extend([table, Spacer(1, 12)])
    if bench_specs:
        from typehaus.takeoff.bench_millwork import bench_fit_notes

        story.append(Paragraph("Bench upholstery and fit", styles["Heading2"]))
        for spec in bench_specs:
            story.append(paragraph(bench_fit_notes(spec)))

    def footer(canvas, document):
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(762, 16, f"Millwork — {document.page}")

    SimpleDocTemplate(str(path), pagesize=landscape(letter), leftMargin=PAGE_MARGIN_PT,
                      rightMargin=PAGE_MARGIN_PT, topMargin=PAGE_MARGIN_PT,
                      bottomMargin=PAGE_MARGIN_PT, title=f"{house} millwork").build(
                          story, onFirstPage=footer, onLaterPages=footer)
