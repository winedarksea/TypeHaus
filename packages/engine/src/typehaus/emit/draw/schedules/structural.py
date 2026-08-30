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


def _write_engineering_register(pdf, model: ResolvedModel, number: str, name: str, *,
                                house_dir=None) -> None:
    """S-105 — the engineered requirements, what governs each, and who sealed it.

    The model carries a *reference* to a sealed document and never a seal graphic. Drawing
    a stamp would be forging one; naming the engineer, the licence, the date and the
    document is what a set is actually for.

    Emitted only when the house has engineering items at all, so a house answered entirely
    by prescriptive tables gets no empty page (``build_sheet_index``).
    """
    from typehaus.checks import run_from_model
    from typehaus.engineering import Freshness, Status, load_register

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
            ))
        section(fig, 0.04, 0.90, "ENGINEERED REQUIREMENTS")
        _add_table(fig, rows,
                   ("Item", "Elements", "Basis", "Governing", "d/c", "Local", "Signoff",
                    "Seal"),
                   bbox=(0.04, 0.58, 0.92, 0.30))

        section(fig, 0.04, 0.535, "SIGNOFFS")
        line = 0.515
        if not register.signoffs:
            fig.text(0.04, line, "None recorded. Every item above rests on this engine's "
                                 "own calculation, or on none — NOT FOR CONSTRUCTION.",
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
        )):
            fig.text(0.04, 0.14 - offset * 0.016, f"\u2022 {text}", fontsize=5.5,
                     family="monospace")


#: How each local status letters on the sheet. Deliberately the same four words the CLI
#: prints, so a reader moving between `haus engineering` and S-105 sees one vocabulary.
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
