"""The S-series take-off pages: the framing bill of materials and the hardware schedule.

Both are pure views of ``typehaus.takeoff`` — nothing on either sheet is summed here.
"""

from __future__ import annotations

from typehaus.emit.draw.schedules.tables import _add_table
from typehaus.emit.draw.sheet_writer import schedule_sheet, section
from typehaus.resolve.model import ResolvedModel


def _write_framing_bom(pdf, model: ResolvedModel, number: str, name: str) -> None:
    """The framing bill of materials: a rollup by lumber size, then the full grouped-by-size
    -and-type cut list with per-stock-length buckets, both derived from the resolved members
    (→ takeoff.framing_takeoff — one row per resolved member, nothing dropped)."""

    from typehaus.takeoff import framing_bom_by_size, framing_takeoff
    with schedule_sheet(pdf, model, number, name) as fig:
        by_size = framing_bom_by_size(model)
        section(fig, 0.04, 0.90, "SUMMARY BY LUMBER SIZE")
        size_rows = [(row["profile"], f"{row['pieces']:,}", f"{row['order_length_ft']:,}",
                      f"{row['board_feet']:,.0f}" if row["board_feet"] else "—")
                     for row in by_size]
        size_rows.append(("TOTAL", f"{sum(int(r['pieces']) for r in by_size):,}",
                          f"{sum(int(r['order_length_ft']) for r in by_size):,}", ""))
        _add_table(fig, size_rows, ("Size", "Pieces", "Ordered LF", "Board ft"),
                   bbox=(0.04, 0.62, 0.5, 0.26))

        section(fig, 0.04, 0.575, "CUT LIST — BY SIZE AND MEMBER TYPE")
        bom_rows = [
            (row["profile"], row["category"], f"{row['pieces']:,}",
             f"{row['cut_length_ft']:,.0f}",
             ", ".join(f"{b['count']}×{b['length_ft']}'" for b in row["stock"]))
            for row in framing_takeoff(model)
        ]
        _add_table(fig, bom_rows,
                   ("Size", "Type", "Pieces", "Cut LF", "Stock lengths"),
                   bbox=(0.04, 0.11, 0.92, 0.44))


def _write_hardware_schedule(pdf, model: ResolvedModel, number: str, name: str) -> None:
    """Connection hardware and structural solids — the parts of the take-off the lumber cut
    list cannot represent (a screw has no cut length; concrete is billed by volume).

    Every row carries the rule it was derived from, because a hardware count is only
    checkable if the reader can see the spacing it came from (→ takeoff.hardware_takeoff).
    """
    from typehaus.takeoff import hardware_takeoff, structural_solids_takeoff
    with schedule_sheet(pdf, model, number, name) as fig:
        hardware = hardware_takeoff(model)
        section(fig, 0.04, 0.90, "CONNECTION HARDWARE")
        # The derivation rules are printed as keyed notes rather than a table column: they run
        # to a full sentence each, and matplotlib scales a table's lettering to fit its widest
        # cell, so carrying them inline shrinks every other column past legibility.
        hardware_rows = [
            (f"{index}", row["scope"], row["part_number"] or "—", row["size"] or "—",
             f"{row['count']:,}" if row["count"] is not None else "—", row["unit"],
             row["manufacturer"] or "—")
            for index, row in enumerate(hardware, start=1)
        ]
        _add_table(fig, hardware_rows,
                   ("#", "Scope", "Part", "Size", "Qty", "Unit", "Manufacturer"),
                   bbox=(0.04, 0.62, 0.92, 0.26))

        section(fig, 0.04, 0.575, "BASIS OF QUANTITY")
        # Two columns: a ledger page holds ~12 basis notes per column above the solids block.
        per_column = (len(hardware) + 1) // 2 if len(hardware) > 12 else len(hardware)
        for index, row in enumerate(hardware, start=1):
            column, line = divmod(index - 1, per_column)
            fig.text(0.04 + column * 0.48, 0.555 - line * 0.014, f"{index}. {row['basis']}",
                     fontsize=5.5, family="monospace")

        solids = structural_solids_takeoff(model)
        section(fig, 0.04, 0.38, "STRUCTURAL SOLIDS — BY CATEGORY")
        solid_rows = [
            (row["category"], row["assembly"] or "—", f"{row['count']:,}",
             f"{row['plan_area_sqft']:,.1f}", f"{row['volume_cubic_yards']:,.2f}")
            for row in solids
        ]
        _add_table(fig, solid_rows,
                   ("Category", "Assembly", "Count", "Plan sf", "Cu yd"),
                   bbox=(0.04, 0.11, 0.7, 0.25))
