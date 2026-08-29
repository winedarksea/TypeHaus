"""The A-series and EN-1 table pages: cover, general notes, openings, energy summary."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from typehaus.emit.draw.schedules.tables import _add_table
from typehaus.emit.draw.sheet_writer import schedule_sheet, section
from typehaus.emit.draw.typography import wrap_columns_for
from typehaus.findings import Result
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel

if TYPE_CHECKING:  # pragma: no cover — annotations only
    from typehaus.checks.jurisdiction import JurisdictionProfile
    from typehaus.checks.permit import PermitChecklist
    from typehaus.checks.registry import Preferences

#: Lettering pitch for the sheet index, inches per row. 8pt monospace on a 0.135" pitch is
#: the density a real index prints at; the old layout used a *figure fraction* instead, so
#: the same 0.021 was 0.23" on ledger and 0.50" on 24x36 — an index twice as airy on the
#: bigger sheet, which is the opposite of what a bigger sheet is for.
_INDEX_PITCH_IN = 0.135

#: Narrowest index column, inches — the width the *column count* is decided against, so that
#: 11x17 still gets five columns rather than three luxurious ones and an overflow note.
_INDEX_COLUMN_IN = 2.95

#: Widest index column, inches. A derived detail's title carries the assembly pair that
#: distinguishes it ("TR-CATLIN-RIM-BAND · CATLIN_EXT_2X6 / CATLIN_ROOF"), which is what a
#: column this wide is for; past it the eye stops associating a number with its title.
_INDEX_COLUMN_MAX_IN = 6.2

#: Clear space between one index column's text and the next column's number, inches.
_INDEX_GUTTER_IN = 0.20

#: Index lettering. The number field is 9 characters plus its separating space, which is
#: where the ``- 10`` in the title's character budget comes from.
_INDEX_PT = 8.0

#: Longest index column worth printing, rows. Nothing but the paper stops a 24x36 cover
#: putting all 98 of catlin's sheets in one 13"-tall column — which fits, and is a worse
#: index than three short ones: the eye tracks a column top-to-bottom, and past about this
#: many rows it is scanning a wall of numbers. Above the cap the list balances across as
#: many columns as the sheet is wide enough to hold.
_INDEX_MAX_ROWS = 48


def _write_cover(pdf, model: ResolvedModel, index: list[tuple[str, str]],
                 profile: JurisdictionProfile,
                 preferences: Preferences | None = None) -> None:
    """A-000 — the identity of the set, the code data behind it, and the sheet index.

    Two things were wrong with this page and both were invisible on 11x17.

    **It disagreed with the gate.** The checklist was evaluated with no preferences at all,
    so ``[envelope].ach50`` was unreadable and the air-leakage item came back UNKNOWN on a
    house that passes it. ``haus print`` refuses to run unless the gate is clean, which
    means the one branch this page could actually reach printed the *opposite* verdict from
    the one that let it be printed. The preferences now arrive from the set writer.

    **It dropped sheets on the floor.** The index was laid out in figure fractions at a
    fixed 24 rows per column and a fixed 0.33-fraction column step, which is three columns
    before the fourth lands off the paper. Catlin's set is 98 sheets: 26 of them were drawn
    past the right edge, on the one page whose entire job is to say what is in the set. The
    layout is in paper inches now and takes its row count from :func:`content_box`, so the
    column count follows the paper — and if a set ever outgrows even that, the overflow is
    *stated on the sheet* rather than silently clipped.
    """
    from typehaus.checks import evaluate_permit_checklist, run_from_model
    from typehaus.emit.draw.sheet_writer import content_box

    site = model.plan.project.site
    checklist = evaluate_permit_checklist(
        run_from_model(model, [], profile=profile.name, preferences=preferences), profile)
    with schedule_sheet(pdf, model, "A-000", "Cover / code summary", heading="") as fig:
        width, height = fig.get_size_inches()
        x0, y0, x1, y1 = content_box((width, height))

        def _x(inches: float) -> float:
            return inches / width

        def _y(inches: float) -> float:
            return inches / height

        fig.text(_x(x0), _y(y1 - 0.55), model.plan.project.name, fontsize=28,
                 family="monospace")
        fig.text(_x(x0), _y(y1 - 1.15), f"{profile.edition.upper()} PERMIT SET",
                 fontsize=13, family="monospace")
        fig.text(_x(x0), _y(y1 - 1.70),
                 f"Site: {site.lat:.5f}, {site.lon:.5f}\n"
                 f"Climate zone 6 · framed model derived from Type:Haus",
                 fontsize=10, family="monospace", va="top")

        cursor = y1 - 2.70
        section(fig, _x(x0), _y(cursor), "CODE SUMMARY", fontsize=12)
        cursor -= 0.42
        for label, value in _code_summary_rows(profile):
            fig.text(_x(x0 + 0.1), _y(cursor), f"{label:<26}{value}", fontsize=8,
                     family="monospace")
            cursor -= _INDEX_PITCH_IN

        cursor -= 0.45
        section(fig, _x(x0), _y(cursor), "SHEET INDEX", fontsize=12)
        cursor -= 0.42
        # Rows are whatever fits between here and the statement above the title block; the
        # column count then follows from the sheet count, not from a guess about the paper.
        per_column, columns = _index_shape(
            len(index),
            rows=max(1, int((cursor - (y0 + 0.75)) / _INDEX_PITCH_IN)),
            columns=max(1, int((x1 - x0) / _INDEX_COLUMN_IN)))
        shown, dropped = index[:per_column * columns], index[per_column * columns:]
        # Having settled how many columns there are, spend the leftover width on them. Three
        # columns on 24x36 leave 34.8" to fill, and a title clipped to the 11x17 column
        # width on a sheet with that much room to spare is a clip for no reason.
        pitch_in = min(_INDEX_COLUMN_MAX_IN, (x1 - x0) / columns)
        # The column is the width the entry has, so it is the width the entry is fitted to.
        # Catlin's longest titles ("Framing schedule / bill of materials", "Framing plan —
        # main · FS-SG-PORCH") are wider than one 11x17 column and ran straight through the
        # next column's sheet number — two overlapping strings, both unreadable, on the page
        # that is meant to be the map.
        room = wrap_columns_for(pitch_in - _INDEX_GUTTER_IN, _INDEX_PT) - 10
        for row, (number, name) in enumerate(shown):
            column, line = divmod(row, per_column)
            fig.text(_x(x0 + 0.1 + column * pitch_in),
                     _y(cursor - line * _INDEX_PITCH_IN),
                     f"{number:9} {_fit(name, room)}",
                     fontsize=_INDEX_PT, family="monospace")
        if dropped:
            fig.text(_x(x0), _y(y0 + 0.52),
                     f"Index continues: {len(dropped)} further sheet(s) "
                     f"{dropped[0][0]}–{dropped[-1][0]} are in the set and not listed above.",
                     fontsize=8, family="monospace", weight="bold")

        fig.text(_x(x0), _y(y0 + 0.20), _gate_statement(profile, checklist),
                 fontsize=8, family="sans-serif", wrap=True)


def _fit(text: str, room: int) -> str:
    """``text`` clipped to ``room`` characters, ellipsised so the clip is visible.

    A silently truncated title reads as the real title. The ellipsis is the difference
    between "this sheet is called that" and "this sheet's name is longer than the column".
    """
    if room <= 1 or len(text) <= room:
        return text
    return text[:room - 1].rstrip() + "…"


def _index_shape(entries: int, *, rows: int, columns: int) -> tuple[int, int]:
    """(rows per column, columns) for ``entries`` index lines in a ``rows`` x ``columns`` grid.

    Two rules, in order. Cap a column at :data:`_INDEX_MAX_ROWS` so a tall sheet does not
    print one enormous column, then **balance**: having decided three columns are needed,
    print 33/33/32 rather than 48/48/2. An unbalanced index looks like the list was
    truncated and continues somewhere else, which is the exact thing this page must not
    suggest.

    The grid is a hard bound, not a target — a set too big for the paper returns the
    largest whole grid that fits and the caller says on the sheet what did not make it.
    """
    if entries <= 0:
        return (1, 1)
    per_column = min(rows, _INDEX_MAX_ROWS)
    needed = -(-entries // per_column)  # ceil
    columns = max(1, min(needed, columns))
    return (min(rows, -(-entries // columns)), columns)


def _code_summary_rows(profile: JurisdictionProfile) -> list[tuple[str, str]]:
    """The profile's own data, which A-000 has claimed to summarise since it was written.

    Every value here is authored on :class:`JurisdictionProfile` and was already deciding
    findings; none of it reached paper. A reviewer reading "42\" MIN BELOW THE LOWEST
    ADJACENT FINISHED GRADE" on S-100 could not see, anywhere in the set, which profile
    that 42 came from. A row is omitted rather than printed as "—" when the profile states
    nothing: a blank is a fact about the profile, and inventing a dash for it is not.
    """
    rows = [("Jurisdiction profile", profile.name),
            ("Code edition", profile.edition),
            ("Effective", profile.effective_date),
            ("IRC base", profile.irc_base)]
    if profile.frost_depth_in is not None:
        rows.append(("Frost depth", f"{profile.frost_depth_in:.0f}\" below lowest "
                                    f"adjacent finished grade (IRC R403.1.4.1)"))
    if profile.soil_bearing_psf is not None:
        rows.append(("Presumptive soil bearing", f"{profile.soil_bearing_psf:.0f} psf "
                                                 f"(IRC Table R401.4.1)"))
    if profile.soil_class is not None:
        rows.append(("Backfill soil class", f"{profile.soil_class} "
                                            f"(IRC Table R405.1 / R404.1.2)"))
    gating = sum(1 for item in profile.permit_items if item.blocking)
    rows.append(("Checklist items", f"{gating} gating, "
                                    f"{len(profile.permit_items) - gating} under review"))
    return rows


def _gate_statement(profile: JurisdictionProfile, checklist: PermitChecklist) -> str:
    """The verdict line, which now names what is unresolved instead of only that something is.

    "NOT READY" on its own sends a reader back to the CLI to find out why. Since this page
    is also written into the architect handoff — a path that does *not* go through the
    ``haus print`` gate — that branch is reachable with a real set attached to it, and the
    labels are the least it can say.
    """
    unresolved = [item.label for item in checklist.items
                  if item.blocking and item.result is not Result.PASS]
    verdict = ("PASS" if checklist.ok
               else "NOT READY — unresolved: " + ", ".join(unresolved))
    return (f"Declared {profile.name} checklist: {verdict}. This set encodes a declared "
            "subset only; verify local amendments, engineering, MEP, and energy before "
            "construction.")


def _write_general_notes(pdf, model: ResolvedModel, number: str, name: str,
                         profile: JurisdictionProfile | None = None) -> None:
    """G-002 — standard notes plus the markdown note files the transitions reference.

    ``Transition.notes`` point at house-relative markdown (→ details._notes_column); this
    sheet collects every distinct file once, so the assembly-junction guidance is readable
    without hunting each A-4xx detail. Wrapped-text columns, fixed lettering.
    """
    from typehaus.emit.draw.details import _load_markdown_notes
    with schedule_sheet(pdf, model, number, name, heading_xy=(0.03, 0.945)) as fig:
        blocks: list[tuple[str, list[str]]] = [("GENERAL", [
            f"• Code: {profile.edition if profile else 'see cover'} "
            f"(declared checklist {profile.name if profile else 'see cover'});",
            "  verify local amendments with the authority having jurisdiction.",
            "• Written dimensions govern; report discrepancies before proceeding.",
            "• This set encodes a declared subset only — engineering, MEP and",
            "  energy compliance must be verified before construction.",
            "• Climate zone 6. See EN-1 for the envelope summary.",
        ])]
        root = model.plan.source_root
        seen: set = set()
        for transition in model.plan.library.transitions:
            rel = transition.notes
            if not rel or rel in seen or not root:
                continue
            seen.add(rel)
            path = Path(root) / rel
            if not path.exists():
                continue
            title = Path(rel).stem.replace("_", " ").upper()
            blocks.append((title, _load_markdown_notes(path)[1:]))  # [0] is "NOTES:"

        columns_x = (0.03, 0.275, 0.52, 0.765)
        top, bottom, step = 0.90, 0.115, 0.011
        column, y = 0, top
        for title, lines in blocks:
            needed = (len(lines) + 2) * step
            if y - needed < bottom and y < top:  # start the block in the next column
                column, y = column + 1, top
            if column >= len(columns_x):
                break
            x = columns_x[column]
            section(fig, x, y, title, fontsize=7, va="top")
            y -= step * 1.6
            for line in lines:
                if y < bottom:
                    column, y = column + 1, top
                    if column >= len(columns_x):
                        break
                    x = columns_x[column]
                fig.text(x, y, line, fontsize=6, family="monospace", va="top")
                y -= step
            y -= step  # blank line between blocks


def _write_opening_schedule(pdf, model: ResolvedModel, number: str, name: str) -> None:
    """A-601, keyed to the plan.

    The Mark column is what makes the floor plan's bubbled ``D1``/``W3`` mean something: the
    plan stopped printing raw opening tags because a field of ``WIN-M-EAST-MID``-class text
    over the room plan is not an annotation of it, and a mark with no column to land in is
    only half of that trade. Marks come from ``plan_marks.opening_type_marks``, so the two
    cannot drift — the plan and the schedule read one mapping.

    A fixture or appliance has no mark: it is not an opening, carries no plan bubble, and
    rides this sheet only because it has nowhere else to be scheduled yet.
    """
    from typehaus.emit.draw.plan_marks import opening_type_marks

    with schedule_sheet(pdf, model, number, name) as fig:
        marks = opening_type_marks(model)
        rows = [(marks.get(opening.type_ref or "", "—"), opening.tag,
                 "Door" if opening.is_door else "Window", opening.type_ref or "RO",
                 f"{opening.width_m / M_PER_IN:.0f}\" × {opening.height_m / M_PER_IN:.0f}\"")
                for opening in sorted(model.openings, key=lambda item: item.tag)]
        types = {item.tag: item for item in (*model.plan.library.fixture_types,
                                             *model.plan.library.appliance_types)}
        rows.extend(
            ("—", fixture.tag, fixture.element_kind, fixture.type_ref,
             f"{types[fixture.type_ref].footprint[0].inches:.0f}\" × "
             f"{types[fixture.type_ref].footprint[1].inches:.0f}\"")
            for storey in model.plan.storeys
            for fixture in model.plan.storey_elements(storey.tag)
            if fixture.element_kind in {"Fixture", "Appliance"} and fixture.type_ref in types
        )
        _add_table(fig, rows, ("Mark", "Tag", "Kind", "Type", "Nominal footprint"),
                   bbox=(0.04, 0.11, 0.92, 0.80))


def _write_energy_sheet(pdf, model: ResolvedModel, number: str, name: str,
                        preferences: Preferences | None = None) -> None:
    """Three honest tables: prescriptive envelope, WWR, and a declared-not-Manual-J
    block load — the EN-1 rewrite (→ Permit-ready plan set Phase 7)."""

    from typehaus.checks.building_science.wwr import wwr_summary
    from typehaus.checks.code.mn_energy import evaluate_envelope
    from typehaus.checks.registry import Preferences
    from typehaus.energy import estimate_block_load

    prefs = preferences if preferences is not None else Preferences()
    with schedule_sheet(pdf, model, number, name) as fig:
        section(fig, 0.04, 0.90, "PRESCRIPTIVE ENVELOPE — MN 2024, CLIMATE ZONE 6")
        prescriptive_rows = [
            (row.component, row.role, row.required, row.provided, row.verdict.upper())
            for row in evaluate_envelope(model, model.plan)
        ]
        _add_table(fig, prescriptive_rows,
                  ("Component", "Use", "Required", "Provided", "Verdict"),
                  bbox=(0.04, 0.62, 0.92, 0.26))

        section(fig, 0.04, 0.575, "WINDOW-TO-WALL RATIO")
        wwr = wwr_summary(model)
        wwr_rows = [("OVERALL", f"{wwr['overall']:.1%}")]
        wwr_rows.extend((item.facade, f"{item.ratio:.1%}") for item in wwr["per_facade"])
        _add_table(fig, wwr_rows, ("Facade", "Glazing / gross wall"), bbox=(0.04, 0.40, 0.4, 0.16))

        section(fig, 0.04, 0.36, "BLOCK LOAD — NOT A MANUAL J")
        load = estimate_block_load(model, prefs)
        load_rows = [(component.kind, f"{component.area_ft2:,.0f}",
                     f"{component.ua_btu_per_hour_f:,.1f}") for component in load.components]
        load_rows.append(("TOTAL HEATING", "", f"{load.heating_load_btu_per_hour:,.0f} BTU/h"))
        load_rows.append(("TOTAL COOLING", "", f"{load.cooling_load_btu_per_hour:,.0f} BTU/h "
                                                f"({load.cooling_tons:.1f} tons)"))
        _add_table(fig, load_rows, ("Component", "Area (ft2)", "UA / total"),
                  bbox=(0.04, 0.15, 0.5, 0.20))
        if load.unknown_inputs:
            fig.text(0.04, 0.115, "NOT A MANUAL J — unknown inputs: "
                     + ", ".join(load.unknown_inputs), fontsize=7, family="sans-serif", wrap=True)
        else:
            fig.text(0.04, 0.115, "NOT A MANUAL J — a transparent block-load estimate only.",
                     fontsize=7, family="sans-serif")
