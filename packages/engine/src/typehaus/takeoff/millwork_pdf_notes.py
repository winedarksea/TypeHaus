"""The millwork PDF's notes pages: what the one-page schedule has no cell for."""
from __future__ import annotations

from html import escape


def notes_story(notes, panels: list[dict], totals: dict[str, float],  # type: ignore[no-untyped-def]
                styles) -> list:
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import KeepTogether, Paragraph, Table, TableStyle

    from typehaus.takeoff.millwork_pdf import ACCENT, BODY_W, INK, MUTED, STRIPE, number

    def table(rows: list[list[str]], widths: list[float], header: bool = True,
              right: tuple[int, ...] = ()) -> Table:
        style = styles["note"]
        cells = [[Paragraph(text, styles["right"] if column in right else style)
                  for column, text in enumerate(row)] for row in rows]
        built = Table(cells, colWidths=widths, hAlign="LEFT", repeatRows=1 if header else 0)
        commands = [("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3.2),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3.2),
                    ("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6),
                    ("ROWBACKGROUNDS", (0, 1 if header else 0), (-1, -1),
                     [HexColor(STRIPE), HexColor("#FFFFFF")])]
        if header:
            commands.append(("LINEBELOW", (0, 0), (-1, 0), 0.6, HexColor(ACCENT)))
        built.setStyle(TableStyle(commands))
        return built

    def head(*names: str) -> list[str]:
        return [f'<font color="{INK}"><b>{name}</b></font>' for name in names]

    story: list = []
    if notes:
        rows = [[f'<font color="{ACCENT}"><b>{n}</b></font>',
                 f'<font color="{MUTED}">{escape(", ".join(note.tags))}</font>',
                 escape(note.text, quote=False)]
                for n, note in enumerate(notes, start=1)]
        story += [Paragraph("STOCK AND CUT NOTES", styles["h2"]),
                  table(rows, [18, 150, BODY_W - 168], header=False)]
    if panels:
        rows = [head("Material", "Sheets", "Size", "Stock", "Grade", "Core", "Finish", "Grain")]
        rows += [[escape(str(row.get(key) or "–"), quote=False) for key in
                  ("material", "sheets_to_order", "sheet_size", "nominal_stock",
                   "panel_grade", "panel_core", "finish", "grain_direction")]
                 for row in panels]
        story.append(KeepTogether([
            Paragraph("PLYWOOD PURCHASING", styles["h2"]),
            table(rows, [100, 40, 70, 70, 40, 70, 110, BODY_W - 500]),
            Paragraph(f'<font color="{MUTED}">Order whole stock sheets. Counts allow for '
                      "grain, saw kerf and edge trimming; the conservative layout includes "
                      "no spare sheets. Part blanks remain available in --json.</font>",
                      styles["note"])]))
    if totals:
        rows = [head("Species", "Rough BF")]
        rows += [[escape(species.title()), number(round(bf, 1))] for species, bf in totals.items()]
        rows.append(["<b>Total</b>", f"<b>{number(round(sum(totals.values()), 1))}</b>"])
        story.append(KeepTogether([
            Paragraph("ROUGH BOARD FEET BY SPECIES", styles["h2"]),
            table(rows, [90, 60], right=(1,)),
            Paragraph(f'<font color="{MUTED}">Rough figures include a straight-line/joint '
                      "width loss and a defect-and-trim length allowance.</font>",
                      styles["note"])]))
    return story
