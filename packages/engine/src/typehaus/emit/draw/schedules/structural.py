"""The S-series take-off pages: the framing bill of materials and the hardware schedule.

Both are pure views of ``typehaus.takeoff`` — nothing on either sheet is summed here.
"""

from __future__ import annotations

from typehaus.emit.draw.schedules.paged_tables import (
    PagedTable,
    continuation_number,
    draw_page,
)
from typehaus.emit.draw.schedules.tables import _add_table
from typehaus.emit.draw.sheet_writer import schedule_sheet, section
from typehaus.resolve.model import ResolvedModel


def framing_bom_tables(model: ResolvedModel) -> list[PagedTable]:
    """S-601's two tables: a rollup by lumber size, then the full grouped-by-size-and-type
    cut list with per-stock-length buckets (→ takeoff.framing_takeoff — one row per
    resolved member, nothing dropped)."""
    from typehaus.takeoff import framing_bom_by_size, framing_takeoff

    by_size = framing_bom_by_size(model)
    size_rows = [(row["profile"], f"{row['pieces']:,}", f"{row['order_length_ft']:,}",
                  f"{row['board_feet']:,.0f}" if row["board_feet"] else "—")
                 for row in by_size]
    size_rows.append(("TOTAL", f"{sum(int(r['pieces']) for r in by_size):,}",
                      f"{sum(int(r['order_length_ft']) for r in by_size):,}", ""))
    bom_rows = [
        (row["profile"], row["category"], f"{row['pieces']:,}", f"{row['cut_length_ft']:,.0f}",
         ", ".join(f"{b['count']}×{b['length_ft']}'" for b in row["stock"]))
        for row in framing_takeoff(model)
    ]
    return [
        PagedTable("SUMMARY BY LUMBER SIZE", ("Size", "Pieces", "Ordered LF", "Board ft"),
                   tuple(size_rows)),
        PagedTable("CUT LIST — BY SIZE AND MEMBER TYPE",
                   ("Size", "Type", "Pieces", "Cut LF", "Stock lengths"), tuple(bom_rows)),
    ]


def hardware_tables(model: ResolvedModel) -> list[PagedTable]:
    """Connection hardware and structural solids — the parts of the take-off the lumber cut
    list cannot represent (a screw has no cut length; concrete is billed by volume).

    The basis-of-quantity sentences are NOT printed: a plan checker grades the part and the
    count, and 120 derivation paragraphs were most of what overprinted this sheet. They stay
    on every row of ``hardware_takeoff`` for the takeoff, bid and CLI outputs.
    """
    from typehaus.takeoff import hardware_takeoff, structural_solids_takeoff

    hardware_rows = tuple(
        (f"{index}", row["scope"], row["part_number"] or "—", row["size"] or "—",
         f"{row['count']:,}" if row["count"] is not None else "—", row["unit"],
         row["manufacturer"] or "—")
        for index, row in enumerate(hardware_takeoff(model), start=1))
    solid_rows = tuple(
        (row["category"], row["assembly"] or "—", f"{row['count']:,}",
         f"{row['plan_area_sqft']:,.1f}", f"{row['volume_cubic_yards']:,.2f}")
        for row in structural_solids_takeoff(model))
    return [
        PagedTable("CONNECTION HARDWARE",
                   ("#", "Scope", "Part", "Size", "Qty", "Unit", "Manufacturer"), hardware_rows),
        PagedTable("STRUCTURAL SOLIDS — BY CATEGORY",
                   ("Category", "Assembly", "Count", "Plan sf", "Cu yd"), solid_rows),
    ]


def _write_paged(pdf, model: ResolvedModel, number: str, name: str,
                 tables: list[PagedTable], page: int) -> None:
    """One sheet of a paged schedule; ``number`` is this page's own (``S-602.1``)."""
    base = number if page == 0 else number.rsplit(".", 1)[0]
    with schedule_sheet(pdf, model, number, name) as fig:
        size = tuple(fig.get_size_inches())
        draw_page(fig, tables, size, page, continuation_number(base, page + 1))


def _write_framing_bom(pdf, model: ResolvedModel, number: str, name: str, *,
                       page: int = 0) -> None:
    """S-601 (and its continuations): the framing bill of materials."""
    _write_paged(pdf, model, number, name, framing_bom_tables(model), page)


def _write_hardware_schedule(pdf, model: ResolvedModel, number: str, name: str, *,
                             page: int = 0) -> None:
    """S-602 (and its continuations): connection hardware, then structural solids."""
    _write_paged(pdf, model, number, name, hardware_tables(model), page)


def _write_engineering_register(pdf, model: ResolvedModel, number: str, name: str, *,
                                house_dir=None) -> None:
    """S-603 — the engineered requirements, what governs each, and who sealed it.

    The model carries a *reference* to a sealed document and never a seal graphic. Drawing
    a stamp would be forging one; naming the engineer, the licence, the date and the
    document is what a set is actually for.

    Emitted only when the house has engineering items at all, so a house answered entirely
    by prescriptive tables gets no empty page (``build_sheet_index``).
    """
    from typehaus.checks import run_from_model
    from typehaus.engineering import Freshness, load_register

    with schedule_sheet(pdf, model, number, name) as fig:
        report = run_from_model(model, [], house_dir)
        register = load_register(house_dir)
        item_ids = sorted({x.engineering_item for x in report.findings
                           if x.engineering_item})
        rows = []
        for item_id in item_ids:
            record = report.engineering[item_id]
            state, signoff = register.freshness(record)
            governing = record.governing
            rows.append((
                item_id,
                ", ".join(record.element_tags) or record.key,
                record.basis or "—",
                governing.name if governing else "—",
                f"{governing.ratio:.2f}" if governing else "—",
                _LOCAL_LABEL[record.status],
                signoff.id if signoff else "—",
                state.value.upper() if state is Freshness.STALE else state.value,
                # The hand-worked note that independently reproduces this item's
                # arithmetic. Without it the drawing set states a result and gives a
                # reviewer no route to the check behind it — which was true of this sheet
                # until the calculation package existed.
                ", ".join(oracle.note for oracle in record.oracle) or "—",
            ))
        section(fig, 0.04, 0.90, "ENGINEERED REQUIREMENTS")
        _add_table(fig, rows,
                   ("Item", "Elements", "Basis", "Governing", "d/c", "Local", "Signoff",
                    "Seal", "Checked against"),
                   bbox=(0.04, 0.58, 0.92, 0.30))

        section(fig, 0.04, 0.535, "SIGNOFFS")
        line = 0.515
        if not register.signoffs:
            fig.text(0.04, line, "None recorded. Every item above rests on this engine's "
                                 "own calculation, or on none — this sheet carries no "
                                 "professional seal.",
                     fontsize=6, family="monospace")
        for signoff in register.signoffs:
            fig.text(0.04, line, f"{signoff.id} — {signoff.scope}",
                     fontsize=6, family="monospace")
            fig.text(0.06, line - 0.016, f"{signoff.credit()}"
                     + (f"  ·  {signoff.document}" if signoff.document else ""),
                     fontsize=5.5, family="monospace")
            if signoff.note:
                fig.text(0.06, line - 0.030, signoff.note, fontsize=5.5,
                         family="monospace")
            line -= 0.055

        section(fig, 0.04, 0.16, "WHAT THIS PAGE DOES AND DOES NOT SAY")
        for offset, text in enumerate((
            "\"draft\" means this engine computed the item from first principles and it "
            "checks out. It is NOT a professional seal.",
            "\"sealed\" means the named engineer stamped the referenced document AND the "
            "pinned inputs still match this model.",
            "\"STALE\" means the model or the calculation changed after the seal was "
            "made: the stamp no longer describes what is drawn.",
            "This set encodes a declared subset of the code. Verify local amendments "
            "with the authority having jurisdiction.",
            "The CALCULATIONS behind this table are `out/calcs/` — one sheet per item, "
            "term by term. Regenerate with `haus calcs`.",
            "\"Checked against\" names the hand-worked note in `houses/<house>/notes/` "
            "that independently reproduces the item; `out/calcs/` prints both together.",
        )):
            fig.text(0.04, 0.14 - offset * 0.016, f"\u2022 {text}", fontsize=5.5,
                     family="monospace")


#: How each local status letters on the sheet. Deliberately the same four words the CLI
#: prints, so a reader moving between `haus engineering` and S-603 sees one vocabulary.
_LOCAL_LABEL = {}


def _init_labels() -> None:
    from typehaus.engineering import Status

    _LOCAL_LABEL.update({
        Status.OK: "draft",
        Status.OVER: "OVER",
        Status.INCOMPLETE: "incomplete",
        Status.NO_CALC: "no local calc",
    })


_init_labels()
