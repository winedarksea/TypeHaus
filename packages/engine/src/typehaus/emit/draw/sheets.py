"""Declarative permit-sheet composer built on the drawing IR (→ 20).

``build_sheet_index`` is the single source of truth for the sheet list: the cover's
printed index and the emitted pages are both derived from it, so they cannot drift.
Every plan/section/elevation sheet is a pure ``Scene`` builder; only the cover, opening
schedule, and energy summary compose matplotlib tables directly (no IR benefit for a table
page).
"""
from __future__ import annotations

from dataclasses import replace
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from typehaus.emit.draw.callouts import detail_sheets
from typehaus.emit.draw.cover_sheets import add_cover, cover_inputs
from typehaus.emit.draw.datum import model_at_level
from typehaus.emit.draw.detail_derive import DerivedDetail
from typehaus.emit.draw.detail_enlarged import enlarged_details
from typehaus.emit.draw.details import build_authored_detail_scene
from typehaus.emit.draw.elevation import elevation_sheets
from typehaus.emit.draw.floorplan import build_floorplan
from typehaus.emit.draw.floorplan_sheet import floorplan_sheet
from typehaus.emit.draw.hvacplan import build_hvac_plan
from typehaus.emit.draw.pdf_writer import _close
from typehaus.emit.draw.plan_enlarged import (
    enlarged_groups,
    enlarged_plan_sheet,
    enlarged_title,
)
from typehaus.emit.draw.roofplan_sheet import roof_plan_sheet
from typehaus.emit.draw.schedule_plan_sheet import schedule_plan_sheet
from typehaus.emit.draw.schedules import (  # noqa: F401 — _write_hardware_schedule re-exported
    _write_energy_sheet,
    _write_general_notes,
    _write_hardware_schedule,
    _write_opening_schedule,
    _write_room_finish_schedule,
    _write_specifications,
    _write_symbols_legend,
    _write_ventilation_sheet,
    write_compare_sheet,
)
from typehaus.emit.draw.schedules.architectural import specification_sections
from typehaus.emit.draw.schedules.casework import (
    casework_tables,
    has_casework_schedule,
    write_casework_schedule,
)
from typehaus.emit.draw.schedules.openings import opening_tables
from typehaus.emit.draw.schedules.paged_tables import page_count
from typehaus.emit.draw.schedules.paint import has_paint_schedule, write_paint_schedule
from typehaus.emit.draw.schedules.structural_notes import (
    _write_structural_notes,
    structural_notes_pages,
)
from typehaus.emit.draw.section import build_annotated_section, build_center_section
from typehaus.emit.draw.sheet_sets import (
    BOTH_SETS,
    FULL_ONLY,
    FULL_SET,
    PERMIT_SET,
    in_set,
    resolve_set_name,
)
from typehaus.emit.draw.sheet_spec import (  # noqa: F401 — re-exported
    PageFn,
    SceneFn,
    SheetSpec,
    _derived_detail_scene,
    _derived_detail_title,
    _has_engineered_items,
    _paged,
    _storey_elevation,
)
from typehaus.emit.draw.sheet_writer import (
    LEDGER,
    PORTRAIT_LEDGER,
    compose_sheet,
    set_paper,
    set_seal_block,
)
from typehaus.emit.draw.sheets_structural import structural_sheets
from typehaus.emit.draw.sheets_trades import trade_sheets
from typehaus.emit.draw.siteplan import build_site_plan
from typehaus.emit.draw.title_block import seal_block_for
from typehaus.resolve.model import ResolvedModel

# The schedule writers live in ``schedules/`` but are re-exported here: this module is
# still the one name the rest of the engine (and the tests) import a permit sheet from.
__all__ = [
    "BOTH_SETS",
    "FULL_ONLY",
    "FULL_SET",
    "PERMIT_SET",
    "PORTRAIT_LEDGER",
    "SheetSpec",
    "resolve_set_name",
    "build_sheet_index",
    "write_compare_sheet",
    "write_permit_set",
    "write_plan_dxfs",
]

if TYPE_CHECKING:
    from typehaus.checks.jurisdiction import JurisdictionProfile
    from typehaus.checks.registry import CheckReport, Preferences


def build_sheet_index(model: ResolvedModel,
                      preferences: Preferences | None = None,
                      profile: JurisdictionProfile | None = None,
                      details: str | None = None,
                      paper: tuple[float, float] = LEDGER,
                      house_dir: Path | None = None,
                      sets: str = FULL_SET,
                      report: CheckReport | None = None) -> list[SheetSpec]:
    """Assemble the ordered sheet list — the one place sheet order/content lives.

    ``sets="full"`` (the library default) is everything this engine can draw;
    ``"permit"`` is the submittal — no separate E or P drawings, no BOM, no room finish
    schedule, and only the starred derived details. ``haus print`` defaults the other way
    round, to ``permit``, which is the same asymmetry ``details`` already had: a bare call
    in a test wants everything, a person printing wants what they will hand in.

    ``details=`` is the deprecated older name and maps ``"primary"``->``"permit"``,
    ``"all"``->``"full"``.

    ``paper`` is stamped onto every spec on the way out rather than threaded through the
    thirty-odd constructors below: sheet *content* has no opinion about sheet size, and a
    set printed half on 11x17 and half on 24x36 should not be expressible. A bigger sheet
    is not just a bigger picture — ``select_scale`` gets a bigger viewport, so the drawing
    climbs the ladder for free: catlin's A-101 goes from 1/16" = 1'-0" on ledger to
    3/16" = 1'-0" on ARCH D, and its main floor plan from 1/8" to 3/8".

    ``report`` is an optional registry run for this same model, house and jurisdiction,
    supplied by a caller that already has one. Only S-603 reads it (→
    ``_has_engineered_items``); the index is otherwise identical either way. Omitted, the
    registry runs here, which on catlin is the most expensive thing this function does."""
    # NCS discipline order is G -> C -> S -> A -> P -> M -> E, and the second digit is the
    # SHEET TYPE: 0 general, 1 plans, 2 elevations, 3 sections, 4 large-scale views,
    # 5 details, 6 schedules, 7-8 user-defined, 9 3D. Sequence within a type is
    # deliberately non-consecutive so a sheet can be inserted without renumbering the set.
    # The cover is G-001, not A-000: a cover is general information, not architectural.
    cover_profile, report = cover_inputs(model, profile, preferences, house_dir, report)
    sheets: list[SheetSpec] = [SheetSpec("G-001", "Cover / code summary")]
    sheets.append(SheetSpec("G-002", "General notes",
                            page=partial(_write_general_notes, profile=profile)))
    sheets.append(SheetSpec("G-003", "Symbols, abbreviations and line weights",
                            page=_write_symbols_legend))
    # G-004, not EN-1. "EN" is not an NCS discipline designator at all — the energy summary
    # is general project information and belongs with the code summary it restates.
    sheets.append(SheetSpec("G-004", "Energy compliance summary",
                            page=partial(_write_energy_sheet, preferences=preferences)))
    # G-005 is ventilation + the MN Energy Code Compliance Certificate. It is its own sheet
    # rather than half of G-004 because the certificate is posted at the panel and read on
    # its own, and because G-004 was already a full page of compliance.
    sheets.append(SheetSpec("G-005", "Ventilation and energy certificate",
                            page=partial(_write_ventilation_sheet,
                                         preferences=preferences)))
    sheets.append(SheetSpec("C-101", "Site plan", "project north",
                            scene=schedule_plan_sheet(build_site_plan),
                            north_arrow=True))

    # S-001 — general structural notes, and it is UNCONDITIONAL. It replaces S-002, whose
    # gate was "any specification section exists": on catlin that printed one bullet, and
    # on a house with nothing authored it printed no sheet at all — precisely the house
    # that most needs a sheet saying what is and is not known. Divisions 03/05 are now one
    # block on it, so A-002 still keeps the remainder and nothing prints twice.
    # Its pages are spliced in HERE at the end: its cross-references read the set's own
    # numbers ("S-602, S-602.1"), so it is composed once the rest of the set is known.
    notes_at = len(sheets)

    # ONE SHEET PER LEVEL, NOT PER STOREY. A storey is a datum within one building, so
    # catlin has five at 0'-0" (the house's main floor, the garage deck, the porch, the north
    # entry, the yard pads) and iterating storeys gave nine plumbing plans and a main floor
    # plan with no porch drawn on it. A plan is a horizontal cut, and a cut crosses every
    # structure standing on the plane — so each level is drawn once, from a model whose
    # elements on that datum all wear the level's own tag (→ ``emit/draw/datum``).
    levels = model.plan.levels()
    level_tags = [primary.tag for primary, _ in levels]
    at = {tag: model_at_level(model, tag) for tag in level_tags}

    sheets.extend(structural_sheets(model, level_tags, at, paper, house_dir, report,
                                    profile=profile, preferences=preferences))

    if specification_sections(model):
        sheets.append(SheetSpec("A-002", "Architectural specifications",
                                page=_write_specifications))

    floor_pages = [(f"A-{101 + i:03d}", tag) for i, tag in enumerate(level_tags)
                   if any(wall.storey == tag for wall in at[tag].walls)]
    for number, storey in floor_pages:
        sheets.append(SheetSpec(number, f"{storey.title()} floor plan",
                                scene=floorplan_sheet(storey),
                                north_arrow=True))

    sheets.append(SheetSpec(f"A-{101 + len(floor_pages):03d}", "Roof plan",
                            scene=roof_plan_sheet(), north_arrow=True))
    # Elevations BEFORE sections: the type digit is the order (2 then 3), and the set was
    # emitting A-301 first. A reviewer works outside-in — what the building looks like, then
    # what it is cut open to show — and the numbering already said so. One scale for all
    # four (C7-E5): ``elevation_sheets`` frames them together.
    elevations = elevation_sheets()
    for number, facing in (("A-201", "north"), ("A-202", "south"),
                           ("A-203", "east"), ("A-204", "west")):
        sheets.append(SheetSpec(number, f"{facing.title()} exterior elevation",
                                scene=partial(elevations, facing=facing)))

    sheets.append(SheetSpec("A-301", "Building section", scene=build_center_section))
    # Authored SECTION slices join the A-301 series right after the auto centre section —
    # one sheet per authored cut, in authoring order (→ Permit-ready plan set Phase 6).
    sections = [item for item in model.plan.elements_of_kind("Slice")
                if item.kind.value == "section"]
    for index, view in enumerate(sections, start=1):
        # ``build_annotated_section``, not the bare cut: an authored section is a SHEET in
        # this set and a sheet carries its datums, its ground line and the names of the
        # volumes the cut passes through. Drawing it unannotated made A-301.1 the one
        # drawing in the permit set a reader could not take a dimension off.
        sheets.append(SheetSpec(f"A-301.{index}", view.title or view.tag,
                                scene=partial(build_annotated_section, view=view)))

    # NCS 4 is LARGE-SCALE VIEWS: the baths (A-401) and mechanical rooms (A-402) enlarged
    # to 1/2" off the level plan (C7-E8), one sheet per room group that fits the viewport.
    # A mechanical room enlarges the HVAC plan: its equipment and ducts are what overprint.
    for number, kind, occupancies, build in (
            ("A-401", "bath", frozenset({"bathroom"}), None),
            ("A-402", "mechanical", frozenset({"mechanical"}), build_hvac_plan)):
        groups = enlarged_groups(model, occupancies, paper)
        for index, group in enumerate(groups, start=1):
            sheets.append(SheetSpec(number if len(groups) == 1 else f"{number}.{index}",
                                    enlarged_title(kind, group), north_arrow=True,
                                    scene=partial(enlarged_plan_sheet, group=group,
                                                  build=build, setout=kind == "bath")))

    # A junction cut at 1-1/2" = 1'-0" is a DETAIL and belongs in the 5 series: authored
    # slices on whole numbers, each derived condition kind its own decimal series
    # (→ callouts.detail_sheets, which the callouts read too).
    for number, item in detail_sheets(model):
        if not isinstance(item, DerivedDetail):
            sheets.append(SheetSpec(number, item.title or item.tag,
                                    scene=partial(build_authored_detail_scene, view=item)))
            continue
        tr = item.transition
        starred = bool(tr.stars(item.key)) if tr is not None else False
        # NUMBERED BEFORE FILTERED, so a detail's number is the same in the permit set and
        # the full set: a callout must not move because a sheet ahead of it dropped.
        title = _derived_detail_title(item, model)
        sets_for = BOTH_SETS if starred else FULL_ONLY
        sheets.append(SheetSpec(number, title,
                                scene=partial(_derived_detail_scene, derived=item),
                                sets=sets_for))
        # Enlarged head/sill (C7-E4): A-560.1.1/.2 beside their parent, same sets.
        for index, child in enumerate(enlarged_details(model, item), start=1):
            sheets.append(SheetSpec(f"{number}.{index}", f"{title} · {child.part}",
                                    scene=partial(_derived_detail_scene, derived=child),
                                    sets=sets_for))

    # A-601 used to be doors, windows AND fixtures on one sheet. They are three schedules
    # with three readers — a door supplier, a glazing supplier, and whoever is setting
    # plumbing — and NCS gives each its own sheet in the 6 series.
    # Paged (C7-E3): a schedule that outgrows its sheet continues on A-601.1 …
    sheets.extend(_paged("A-601", "Door schedule",
                         partial(_write_opening_schedule, kinds="door"),
                         page_count(opening_tables(model, "door"), paper)))
    sheets.extend(_paged("A-602", "Window schedule",
                         partial(_write_opening_schedule, kinds="window"),
                         page_count(opening_tables(model, "window"), paper)))
    sheets.append(SheetSpec("A-603", "Room finish schedule",
                            page=_write_room_finish_schedule, sets=FULL_ONLY))
    if has_paint_schedule(model):
        sheets.append(SheetSpec("A-604", "Paint schedule", page=write_paint_schedule,
                                sets=FULL_ONLY))
    # Stair geometry and guards (S1-103, S3-107): R311.7 / R312 review reads both.
    from typehaus.emit.draw.guard_detail import build_guard_detail, has_guard_detail
    from typehaus.emit.draw.schedules.stairs import (
        has_stair_schedule,
        stair_schedule_tables,
        write_stair_schedule,
    )
    if has_stair_schedule(model):
        sheets.extend(_paged("A-605", "Stair and guard schedule", write_stair_schedule,
                             page_count(stair_schedule_tables(model), paper)))
    if has_guard_detail(model):
        sheets.append(SheetSpec("A-606", "Guard and handrail details",
                                scene=build_guard_detail))
    # A-607 (I1-106): the casework and countertop build-up, off ``haus countertops``' records.
    if has_casework_schedule(model):
        sheets.extend(_paged("A-607", "Casework and countertop schedule",
                             write_casework_schedule,
                             page_count(casework_tables(model), paper), sets=FULL_ONLY))

    sheets.extend(trade_sheets(model, level_tags, at, paper))

    chosen = resolve_set_name(sets, details)
    kept = [sheet for sheet in sheets if in_set(sheet, chosen, preferences)]
    notes = {"profile": profile, "preferences": preferences, "house_dir": house_dir,
             "sheets": tuple(sheet.number for sheet in kept)}
    s001 = [sheet for sheet in _paged("S-001", "General structural notes",
                                      partial(_write_structural_notes, **notes),
                                      structural_notes_pages(model, paper, **notes))
            if in_set(sheet, chosen, preferences)]
    at = sum(1 for sheet in sheets[:notes_at] if in_set(sheet, chosen, preferences))
    final = [replace(sheet, paper=paper) for sheet in kept[:at] + s001 + kept[at:]]
    return add_cover(final, model, cover_profile, report, paper)


def write_permit_set(model: ResolvedModel, output: Path,
                     preferences: Preferences | None = None,
                     profile: JurisdictionProfile | None = None,
                     details: str | None = None,
                     paper: tuple[float, float] = LEDGER,
                     house_dir: Path | None = None,
                     sets: str = FULL_SET,
                     report: CheckReport | None = None,
                     ) -> tuple[Path, dict[str, object]]:
    """Compose the permit-set baseline into one multi-page PDF.

    The source plan remains authoritative: plans are drawing-IR scenes and schedules are
    derived from the same resolved openings. Every page is a real sheet — ``paper`` with a
    border and title block (→ sheet_writer), 11x17 ledger by default; scene sheets print
    at TRUE architectural scale with a graphic scale bar, table pages get the same chrome.

    The PDF is vector: it has no resolution and plots at whatever the plotter can do, which
    is why 24x36 is a *paper* choice here and a ``--dpi`` choice only for ``haus render``.
    """
    from matplotlib.backends.backend_pdf import PdfPages

    from typehaus.checks.registry import Preferences
    from typehaus.checks.run import resolve_profile

    # The set is composed against one jurisdiction, and it has to be the same one the
    # checklist gate used — not "mn-2020" spelled out again on the cover and in the notes.
    if profile is None:
        profile = resolve_profile(preferences or Preferences())
    output.parent.mkdir(parents=True, exist_ok=True)
    sheets = build_sheet_index(model, preferences, profile, details=details,
                               paper=paper, house_dir=house_dir, sets=sets, report=report)
    index = [(sheet.number, sheet.title) for sheet in sheets]
    # ``set_paper`` is how the table pages learn the paper: they compose their own figures
    # inside ``schedules/`` against a preset name, and this is the only place that knows
    # which paper the *set* is on (→ sheet_writer.schedule_sheet).
    seal = seal_block_for(profile, house_dir)
    with PdfPages(output) as pdf, set_paper(paper), set_seal_block(seal):
        for sheet in sheets:
            if sheet.page is not None:
                sheet.page(pdf, model, sheet.number, sheet.title)
            elif sheet.scene is not None:
                fig = compose_sheet(sheet.scene(model), sheet, model, size=sheet.size)
                pdf.savefig(fig)
                _close(fig)
    return output, {"index": index}


def write_plan_dxfs(model: ResolvedModel, output_dir: Path) -> list[Path]:
    """Emit a DXF for every storey plan, alongside the single PDF package."""
    from typehaus.emit.draw.dxf_writer import write_dxf

    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for primary, _here in model.plan.levels():
        scoped = model_at_level(model, primary.tag)
        if any(wall.storey == primary.tag for wall in scoped.walls):
            paths.append(write_dxf(build_floorplan(scoped, primary.tag),
                                   output_dir / f"plan_{primary.tag}.dxf"))
    return paths


