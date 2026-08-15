"""The A-series and EN-1 table pages: cover, general notes, openings, energy summary."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from typehaus.emit.draw.schedules.tables import _add_table
from typehaus.emit.draw.sheet_writer import schedule_sheet, section
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel

if TYPE_CHECKING:  # pragma: no cover — annotations only
    from typehaus.checks.jurisdiction import JurisdictionProfile
    from typehaus.checks.registry import Preferences

def _write_cover(pdf, model: ResolvedModel, index: list[tuple[str, str]],
                 profile: JurisdictionProfile) -> None:
    from typehaus.checks import evaluate_permit_checklist, run_from_model

    site = model.plan.project.site
    checklist = evaluate_permit_checklist(
        run_from_model(model, [], profile=profile.name), profile)
    with schedule_sheet(pdf, model, "A-000", "Cover / code summary", heading="") as fig:
        fig.text(0.05, 0.88, model.plan.project.name, fontsize=28, family="monospace")
        fig.text(0.05, 0.82, f"{profile.edition.upper()} PERMIT SET", fontsize=13,
                 family="monospace")
        fig.text(0.05, 0.77, f"Site: {site.lat:.5f}, {site.lon:.5f}\n"
                 f"Climate zone 6 · framed model derived from Type:Haus", fontsize=10,
                 family="monospace", va="top")
        section(fig, 0.05, 0.66, "SHEET INDEX", fontsize=12)
        # Two columns: an 11x17 cover holds ~24 rows per column above the title block.
        per_column = 24
        for row, (number, name) in enumerate(index):
            column, line = divmod(row, per_column)
            fig.text(0.06 + column * 0.33, 0.62 - line * 0.021, f"{number:8}  {name}",
                     fontsize=8, family="monospace")
        fig.text(0.05, 0.115,
                 f"Declared {profile.name} checklist: "
                 + ("PASS" if checklist.ok else "NOT READY") + ". "
                 "This set encodes a declared subset only; verify local amendments, "
                 "engineering, MEP, and energy before construction.",
                 fontsize=8, family="sans-serif", wrap=True)


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
    with schedule_sheet(pdf, model, number, name) as fig:
        rows = [(opening.tag, "Door" if opening.is_door else "Window", opening.type_ref or "RO",
                 f"{opening.width_m / M_PER_IN:.0f}\" × {opening.height_m / M_PER_IN:.0f}\"")
                for opening in sorted(model.openings, key=lambda item: item.tag)]
        types = {item.tag: item for item in (*model.plan.library.fixture_types,
                                             *model.plan.library.appliance_types)}
        rows.extend(
            (fixture.tag, fixture.element_kind, fixture.type_ref,
             f"{types[fixture.type_ref].footprint[0].inches:.0f}\" × "
             f"{types[fixture.type_ref].footprint[1].inches:.0f}\"")
            for storey in model.plan.storeys
            for fixture in model.plan.storey_elements(storey.tag)
            if fixture.element_kind in {"Fixture", "Appliance"} and fixture.type_ref in types
        )
        _add_table(fig, rows, ("Tag", "Kind", "Type", "Nominal footprint"),
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
