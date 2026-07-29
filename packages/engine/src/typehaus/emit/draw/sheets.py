"""Declarative permit-sheet composer built on the drawing IR (→ 20).

``build_sheet_index`` is the single source of truth for the sheet list: the cover's
printed index and the emitted pages are both derived from it, so they cannot drift.
Every plan/section/elevation sheet is a pure ``Scene`` builder; only the cover, opening
schedule, and energy summary compose matplotlib tables directly (no IR benefit for a table
page).
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from typehaus.emit.draw.electricalplan import build_electrical_plan, has_electrical_content
from typehaus.emit.draw.elevation import build_elevation
from typehaus.emit.draw.floorplan import build_floorplan
from typehaus.emit.draw.foundationplan import build_foundation_plan, has_foundation_content
from typehaus.emit.draw.framingplan import build_framing_plan
from typehaus.emit.draw.hvacplan import build_hvac_plan, has_hvac_content
from typehaus.emit.draw.lightingplan import build_lighting_plan, has_lighting_content
from typehaus.emit.draw.plumbingplan import build_plumbing_plan, has_plumbing_content
from typehaus.emit.draw.sheet_writer import LEDGER, compose_sheet, sheet_chrome
from typehaus.emit.draw.roofframingplan import build_roof_framing_plan
from typehaus.emit.draw.roofplan import build_roof_plan
from typehaus.emit.draw.scene import Scene
from typehaus.emit.draw.details import (
    DerivedDetail,
    build_authored_detail_scene,
    build_detail,
    derive_detail_slices,
)
from typehaus.emit.draw.section import build_center_section, build_section
from typehaus.emit.draw.siteplan import build_site_plan
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff import hardware_takeoff


def _derived_detail_scene(model: ResolvedModel, derived: "DerivedDetail") -> Scene:
    scene, _findings = build_detail(model, derived)
    return scene

if TYPE_CHECKING:
    from typehaus.checks.jurisdiction import JurisdictionProfile
    from typehaus.checks.registry import Preferences

SceneFn = Callable[[ResolvedModel], Scene]
PageFn = Callable[["object", ResolvedModel, str, str], None]  # pdf: PdfPages


@dataclass(frozen=True)
class SheetSpec:
    number: str                # "S-100"
    title: str                 # "Foundation plan"
    scale_note: str = "1/4\" = 1'-0\""  # hint only — compose_sheet prints the TRUE scale
    scene: SceneFn | None = None       # IR-backed sheets
    page: PageFn | None = None         # table/cover pages
    size: tuple[float, float] = LEDGER  # paper preset (width, height) in inches
    north_arrow: bool = False          # stamp a north arrow in the viewport (plan sheets)


def build_sheet_index(model: ResolvedModel,
                      preferences: "Preferences | None" = None,
                      profile: "JurisdictionProfile | None" = None) -> list[SheetSpec]:
    """Assemble the ordered permit-set sheet list — the one place sheet order/content lives."""
    sheets: list[SheetSpec] = [SheetSpec("A-000", "Cover / code summary")]
    sheets.append(SheetSpec("G-002", "General notes",
                            page=partial(_write_general_notes, profile=profile)))
    sheets.append(SheetSpec("C-101", "Site plan", "project north", scene=build_site_plan,
                            north_arrow=True))

    if has_foundation_content(model):
        sheets.append(SheetSpec("S-100", "Foundation plan",
                                scene=partial(build_foundation_plan, profile=profile),
                                north_arrow=True))

    floors = sorted(model.floors, key=lambda f: _storey_elevation(model, f.storey))
    for index, floor in enumerate(floors, start=1):
        number = "S-101" if len(floors) == 1 else f"S-101.{index}"
        # Name the deck, not just its storey: a storey may carry more than one framed deck
        # (catlin's second floor plus its balcony), and the cover index must stay unambiguous.
        title = (f"Framing plan — {floor.storey}" if len(floors) == 1
                 else f"Framing plan — {floor.storey} · {floor.tag}")
        sheets.append(SheetSpec(number, title,
                                scene=partial(build_framing_plan, floor_tag=floor.tag),
                                north_arrow=True))

    # Roof framing gets its own S-102 series rather than joining the S-101 floor series: a
    # roof is a framed level too, but numbering it S-101.n would make the floor-deck sheet
    # count depend on how many roofs a house happens to have.
    roofs = sorted(model.roofs, key=lambda r: (_storey_elevation(model, r.storey), r.tag))
    for index, roof in enumerate(roofs, start=1):
        number = "S-102" if len(roofs) == 1 else f"S-102.{index}"
        sheets.append(SheetSpec(number, f"Roof framing plan — {roof.tag}",
                                scene=partial(build_roof_framing_plan, roof_tag=roof.tag),
                                north_arrow=True))

    if model.all_members():
        sheets.append(SheetSpec("S-103", "Framing schedule / bill of materials",
                                page=_write_framing_bom))

    # Hardware gets its own sheet rather than a second page under S-103: a PageFn that
    # emits two pages would put the cover's printed index one page out of step with the
    # emitted set, which ``build_sheet_index`` exists to prevent.
    if hardware_takeoff(model):
        sheets.append(SheetSpec("S-104", "Connection hardware schedule",
                                page=_write_hardware_schedule))

    storeys = sorted(model.plan.storeys, key=lambda s: s.elevation.meters)
    floor_pages = [(f"A-{101 + i:03d}", storey.tag) for i, storey in enumerate(storeys)
                   if any(wall.storey == storey.tag for wall in model.walls)]
    for number, storey in floor_pages:
        sheets.append(SheetSpec(number, f"{storey.title()} floor plan",
                                scene=partial(build_floorplan, storey=storey),
                                north_arrow=True))

    sheets.append(SheetSpec(f"A-{101 + len(floor_pages):03d}", "Roof plan",
                            scene=build_roof_plan, north_arrow=True))
    sheets.append(SheetSpec("A-301", "Building section", scene=build_center_section))
    # Authored SECTION slices join the A-301 series right after the auto centre section —
    # one sheet per authored cut, in authoring order (→ Permit-ready plan set Phase 6).
    sections = [item for item in model.plan.elements_of_kind("Slice")
                if item.kind.value == "section"]
    for index, view in enumerate(sections, start=1):
        sheets.append(SheetSpec(f"A-301.{index}", view.title or view.tag,
                                scene=partial(build_section, view=view)))
    for number, facing in (("A-201", "north"), ("A-202", "south"),
                           ("A-203", "east"), ("A-204", "west")):
        sheets.append(SheetSpec(number, f"{facing.title()} exterior elevation",
                                scene=partial(build_elevation, facing=facing)))

    details = [item for item in model.plan.elements_of_kind("Slice")
              if item.kind.value == "detail"]
    next_detail = 401
    for detail in details:
        sheets.append(SheetSpec(f"A-{next_detail}", detail.title or detail.tag,
                                scene=partial(build_authored_detail_scene, view=detail)))
        next_detail += 1

    # Derived transition details — one per distinct bound condition key, sorted by key,
    # continuing the A-4xx block after any authored details (→ 11b transition details).
    for derived in derive_detail_slices(model):
        sheets.append(SheetSpec(f"A-{next_detail}", derived.view.title or derived.key,
                                scene=partial(_derived_detail_scene, derived=derived)))
        next_detail += 1

    sheets.append(SheetSpec("A-601", "Door / window schedule", page=_write_opening_schedule))

    plumbing_storeys = [s.tag for s in storeys if has_plumbing_content(model, s.tag)]
    for index, storey_tag in enumerate(plumbing_storeys, start=1):
        sheets.append(SheetSpec(f"P-{100 + index}", f"Plumbing plan — {storey_tag}",
                                scene=partial(build_plumbing_plan, storey=storey_tag)))

    hvac_storeys = [s.tag for s in storeys if has_hvac_content(model, s.tag)]
    for index, storey_tag in enumerate(hvac_storeys, start=1):
        sheets.append(SheetSpec(f"M-{100 + index}", f"HVAC plan — {storey_tag}",
                                scene=partial(build_hvac_plan, storey=storey_tag)))

    electrical_storeys = [s.tag for s in storeys if has_electrical_content(model, s.tag)]
    for index, storey_tag in enumerate(electrical_storeys, start=1):
        sheets.append(SheetSpec(f"E-{100 + index}", f"Electrical plan — {storey_tag}",
                                scene=partial(build_electrical_plan, storey=storey_tag)))

    # E-2xx: the lighting plans, one per storey that has luminaires. A separate series
    # from the E-10x power sheets on purpose — an electrician wiring devices and a reader
    # checking what hangs over the dining table want two different drawings, and merging
    # them produces a sheet too dense to be either.
    lighting_storeys = [s.tag for s in storeys if has_lighting_content(model, s.tag)]
    for index, storey_tag in enumerate(lighting_storeys, start=1):
        sheets.append(SheetSpec(f"E-{200 + index}", f"Lighting plan — {storey_tag}",
                                scene=partial(build_lighting_plan, storey=storey_tag)))

    if model.plan.library.circuits:
        sheets.append(SheetSpec("E-601", "Panel schedule / service load",
                                page=_write_panel_schedule))

    if lighting_storeys:
        sheets.append(SheetSpec("E-602", "Luminaire schedule / lighting controls",
                                page=_write_luminaire_schedule))

    sheets.append(SheetSpec("EN-1", "Energy compliance summary",
                            page=partial(_write_energy_sheet, preferences=preferences)))
    return sheets


def _storey_elevation(model: ResolvedModel, storey_tag: str) -> float:
    storey = next((s for s in model.plan.storeys if s.tag == storey_tag), None)
    return storey.elevation.meters if storey is not None else 0.0


def write_permit_set(model: ResolvedModel, output: Path,
                     preferences: "Preferences | None" = None,
                     profile: "JurisdictionProfile | None" = None,
                     ) -> tuple[Path, dict[str, object]]:
    """Compose the permit-set baseline into one multi-page PDF.

    The source plan remains authoritative: plans are drawing-IR scenes and schedules are
    derived from the same resolved openings. Every page is a real sheet — a fixed 11x17
    ledger with border and title block (→ sheet_writer); scene sheets print at TRUE
    architectural scale with a graphic scale bar, table pages get the same chrome.
    """
    from matplotlib.backends.backend_pdf import PdfPages

    from typehaus.checks.registry import Preferences
    from typehaus.checks.run import resolve_profile

    # The set is composed against one jurisdiction, and it has to be the same one the
    # checklist gate used — not "mn-2024" spelled out again on the cover and in the notes.
    if profile is None:
        profile = resolve_profile(preferences or Preferences())
    output.parent.mkdir(parents=True, exist_ok=True)
    sheets = build_sheet_index(model, preferences, profile)
    index = [(sheet.number, sheet.title) for sheet in sheets]
    with PdfPages(output) as pdf:
        for sheet in sheets:
            if sheet.number == "A-000":
                _write_cover(pdf, model, index, profile)
            elif sheet.page is not None:
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
    for storey in sorted(model.plan.storeys, key=lambda item: item.elevation.meters):
        if any(wall.storey == storey.tag for wall in model.walls):
            paths.append(write_dxf(build_floorplan(model, storey.tag),
                                   output_dir / f"plan_{storey.tag}.dxf"))
    return paths


def _write_cover(pdf, model: ResolvedModel, index: list[tuple[str, str]],
                 profile: "JurisdictionProfile") -> None:
    import matplotlib.pyplot as plt
    from typehaus.checks import evaluate_permit_checklist, run_from_model

    fig = plt.figure(figsize=LEDGER)
    site = model.plan.project.site
    checklist = evaluate_permit_checklist(
        run_from_model(model, [], profile=profile.name), profile)
    fig.text(0.05, 0.88, model.plan.project.name, fontsize=28, family="monospace")
    fig.text(0.05, 0.82, f"{profile.edition.upper()} PERMIT SET", fontsize=13,
             family="monospace")
    fig.text(0.05, 0.77, f"Site: {site.lat:.5f}, {site.lon:.5f}\n"
             f"Climate zone 6 · framed model derived from Type:Haus", fontsize=10,
             family="monospace", va="top")
    fig.text(0.05, 0.66, "SHEET INDEX", fontsize=12, family="monospace", weight="bold")
    # Two columns: an 11x17 cover holds ~24 rows per column above the title block.
    per_column = 24
    for row, (number, name) in enumerate(index):
        column, line = divmod(row, per_column)
        fig.text(0.06 + column * 0.33, 0.62 - line * 0.021, f"{number:8}  {name}",
                 fontsize=8, family="monospace")
    fig.text(0.05, 0.115,
             f"Declared {profile.name} checklist: "
             + ("PASS" if checklist.ok else "NOT READY") + ". "
             "This set encodes a declared subset only; verify local amendments, engineering, "
             "MEP, and energy before construction.", fontsize=8, family="sans-serif", wrap=True)
    sheet_chrome(fig, model, "A-000", "Cover / code summary")
    pdf.savefig(fig)
    plt.close(fig)


def _write_general_notes(pdf, model: ResolvedModel, number: str, name: str,
                         profile: "JurisdictionProfile | None" = None) -> None:
    """G-002 — standard notes plus the markdown note files the transitions reference.

    ``Transition.notes`` point at house-relative markdown (→ details._notes_column); this
    sheet collects every distinct file once, so the assembly-junction guidance is readable
    without hunting each A-4xx detail. Wrapped-text columns, fixed lettering.
    """
    import matplotlib.pyplot as plt

    from typehaus.emit.draw.details import _load_markdown_notes

    fig = plt.figure(figsize=LEDGER)
    fig.text(0.03, 0.945, f"{number} · {name}", fontsize=16, family="monospace")

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
        fig.text(x, y, title, fontsize=7, family="monospace", weight="bold", va="top")
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
    sheet_chrome(fig, model, number, name)
    pdf.savefig(fig)
    plt.close(fig)


def _write_opening_schedule(pdf, model: ResolvedModel, number: str, name: str) -> None:
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=LEDGER)
    fig.text(0.04, 0.945, f"{number} · {name}", fontsize=16, family="monospace")
    rows = [(opening.tag, "Door" if opening.is_door else "Window", opening.type_ref or "RO",
             f"{opening.width_m / 0.0254:.0f}\" × {opening.height_m / 0.0254:.0f}\"")
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
    sheet_chrome(fig, model, number, name)
    pdf.savefig(fig)
    plt.close(fig)


def _write_framing_bom(pdf, model: ResolvedModel, number: str, name: str) -> None:
    """The framing bill of materials: a rollup by lumber size, then the full grouped-by-size
    -and-type cut list with per-stock-length buckets, both derived from the resolved members
    (→ takeoff.framing_takeoff — one row per resolved member, nothing dropped)."""
    import matplotlib.pyplot as plt

    from typehaus.takeoff import framing_bom_by_size, framing_takeoff

    fig = plt.figure(figsize=LEDGER)
    fig.text(0.04, 0.945, f"{number} · {name}", fontsize=16, family="monospace")

    by_size = framing_bom_by_size(model)
    fig.text(0.04, 0.90, "SUMMARY BY LUMBER SIZE", fontsize=10, family="monospace",
             weight="bold")
    size_rows = [(row["profile"], f"{row['pieces']:,}", f"{row['order_length_ft']:,}",
                  f"{row['board_feet']:,.0f}" if row["board_feet"] else "—")
                 for row in by_size]
    size_rows.append(("TOTAL", f"{sum(int(r['pieces']) for r in by_size):,}",
                      f"{sum(int(r['order_length_ft']) for r in by_size):,}", ""))
    _add_table(fig, size_rows, ("Size", "Pieces", "Ordered LF", "Board ft"),
               bbox=(0.04, 0.62, 0.5, 0.26))

    fig.text(0.04, 0.575, "CUT LIST — BY SIZE AND MEMBER TYPE", fontsize=10,
             family="monospace", weight="bold")
    bom_rows = [
        (row["profile"], row["category"], f"{row['pieces']:,}",
         f"{row['cut_length_ft']:,.0f}",
         ", ".join(f"{b['count']}×{b['length_ft']}'" for b in row["stock"]))
        for row in framing_takeoff(model)
    ]
    _add_table(fig, bom_rows,
               ("Size", "Type", "Pieces", "Cut LF", "Stock lengths"),
               bbox=(0.04, 0.11, 0.92, 0.44))
    sheet_chrome(fig, model, number, name)
    pdf.savefig(fig)
    plt.close(fig)


def _write_hardware_schedule(pdf, model: ResolvedModel, number: str, name: str) -> None:
    """Connection hardware and structural solids — the parts of the take-off the lumber cut
    list cannot represent (a screw has no cut length; concrete is billed by volume).

    Every row carries the rule it was derived from, because a hardware count is only
    checkable if the reader can see the spacing it came from (→ takeoff.hardware_takeoff).
    """
    import matplotlib.pyplot as plt

    from typehaus.takeoff import hardware_takeoff, structural_solids_takeoff

    fig = plt.figure(figsize=LEDGER)
    fig.text(0.04, 0.945, f"{number} · {name}", fontsize=16, family="monospace")

    hardware = hardware_takeoff(model)
    fig.text(0.04, 0.90, "CONNECTION HARDWARE", fontsize=10, family="monospace",
             weight="bold")
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

    fig.text(0.04, 0.575, "BASIS OF QUANTITY", fontsize=10, family="monospace",
             weight="bold")
    # Two columns: a ledger page holds ~12 basis notes per column above the solids block.
    per_column = (len(hardware) + 1) // 2 if len(hardware) > 12 else len(hardware)
    for index, row in enumerate(hardware, start=1):
        column, line = divmod(index - 1, per_column)
        fig.text(0.04 + column * 0.48, 0.555 - line * 0.014, f"{index}. {row['basis']}",
                 fontsize=5.5, family="monospace")

    solids = structural_solids_takeoff(model)
    fig.text(0.04, 0.38, "STRUCTURAL SOLIDS — BY CATEGORY", fontsize=10,
             family="monospace", weight="bold")
    solid_rows = [
        (row["category"], row["assembly"] or "—", f"{row['count']:,}",
         f"{row['plan_area_sqft']:,.1f}", f"{row['volume_cubic_yards']:,.2f}")
        for row in solids
    ]
    _add_table(fig, solid_rows,
               ("Category", "Assembly", "Count", "Plan sf", "Cu yd"),
               bbox=(0.04, 0.11, 0.7, 0.25))
    sheet_chrome(fig, model, number, name)
    pdf.savefig(fig)
    plt.close(fig)


def _write_panel_schedule(pdf, model: ResolvedModel, number: str, name: str) -> None:
    """The panel schedule + NEC 220.82-style load summary + backup component list, all
    derived from Library.circuits (→ takeoff.electrical — nothing here is hand-summed)."""
    import matplotlib.pyplot as plt

    from typehaus.takeoff import backup_component_rows, panel_schedule, service_load_summary

    fig = plt.figure(figsize=LEDGER)
    fig.text(0.04, 0.945, f"{number} · {name}", fontsize=16, family="monospace")

    schedule = panel_schedule(model)
    fig.text(0.04, 0.90, "PANEL SCHEDULE — ED-B-PANEL (225A, 200A SERVICE)",
             fontsize=10, family="monospace", weight="bold")
    schedule_rows = [
        (row["circuit"], row["description"], f"{row['breaker_amps']}A/{row['poles']}p",
         f"{row['volts']}V", row["nema"] or "—",
         ("GFCI" if row["gfci"] else "") + ("+BKUP" if row["backup"] and row["gfci"] else
                                            "BKUP" if row["backup"] else "") or "—",
         f"{row['connected_va']:,.0f}")
        for row in schedule
    ]
    _add_table(fig, schedule_rows,
               ("Circuit", "Description", "Breaker", "Volts", "NEMA", "Prot.", "VA"),
               bbox=(0.04, 0.42, 0.92, 0.46))

    load = service_load_summary(model)
    fig.text(0.04, 0.38, "SERVICE LOAD — " + str(load["method"]).upper(), fontsize=10,
             family="monospace", weight="bold")
    load_rows = [
        ("Conditioned floor area", f"{load['floor_area_ft2']:,.0f} ft2"),
        ("General lighting + small appliance/laundry", f"{load['general_lighting_va']:,.0f} VA"),
        ("Fixed appliances", f"{load['fixed_appliance_va']:,.0f} VA"),
        ("Heating/cooling at 100%", f"{load['hvac_va']:,.0f} VA"),
        ("EV charging (continuous)", f"{load['ev_va']:,.0f} VA"),
        ("DEMAND", f"{load['demand_va']:,.0f} VA = {load['demand_amps']:.1f} A"),
        ("Service / panel rating", f"{load['service_amps']}A service, "
                                   f"{load['panel_rating_amps']}A panel — "
                                   + ("OK" if load["within_service"] else "OVER")),
    ]
    _add_table(fig, load_rows, ("Line", "Value"), bbox=(0.04, 0.18, 0.6, 0.18))

    backup = backup_component_rows(model)
    if backup:
        fig.text(0.04, 0.165, "BACKUP SUBSYSTEM COMPONENTS (ED-B-BACKUP-ENCL)", fontsize=10,
                 family="monospace", weight="bold")
        backup_rows = [(row["component"], f"{row['count']}", row["basis"])
                       for row in backup]
        _add_table(fig, backup_rows, ("Component", "Qty", "Basis"),
                   bbox=(0.04, 0.105, 0.92, 0.05))
    sheet_chrome(fig, model, number, name)
    pdf.savefig(fig)
    plt.close(fig)


def _write_luminaire_schedule(pdf, model: ResolvedModel, number: str, name: str) -> None:
    """Three tables that between them make the E-2xx plans readable.

    The plans carry marks, not specifications — that is the whole point of a mark — so this
    sheet is where a mark becomes a product: what lamp, how many lumens, at what colour
    temperature, listed for how wet a place, dimmable or not, how many, and where. Then the
    control schedule, which is the authoritative statement of the switch legs the plans can
    only draw as dashed lines. Then the runs, with each supply sized against the tape it
    actually drives (→ takeoff/lighting.py — nothing here is hand-summed).
    """
    import matplotlib.pyplot as plt

    from typehaus.takeoff import (connected_lighting_va, light_run_takeoff,
                                  lighting_controls, luminaire_schedule)

    fig = plt.figure(figsize=(11, 17))
    fig.text(0.04, 0.97, f"{number} · {name}", fontsize=16, family="monospace")

    schedule = luminaire_schedule(model)
    fig.text(0.04, 0.945, "LUMINAIRE SCHEDULE", fontsize=10, family="monospace",
             weight="bold")
    schedule_rows = [
        (row["mark"], row["description"], row["lamp"] or "—",
         _number(row["watts"], "{:.0f} W") or _number(row["watts_per_ft"], "{:.1f} W/ft"),
         _number(row["lumens"], "{:,.0f}"), _number(row["cct_k"], "{:.0f}K"),
         f"{row['volts']}V", row["mount"], row["dimming"], row["rating"],
         str(row["count"]) if row["count"] else f"{row['length_ft'] or 0:.0f} LF",
         ", ".join(row["rooms"])[:44])
        for row in schedule
    ]
    _add_table(fig, schedule_rows,
               ("Mark", "Description", "Lamp", "Watts", "Lumens", "CCT", "V", "Mount",
                "Dim", "Listing", "Qty", "Locations"),
               bbox=(0.03, 0.66, 0.94, 0.27))

    controls = lighting_controls(model)
    fig.text(0.04, 0.635, "LIGHTING CONTROL SCHEDULE", fontsize=10, family="monospace",
             weight="bold")
    control_rows = [
        (row["tag"], row["mark"] or "—", row["room"] or "—",
         row["circuit"] or (f"via {row['psu']}" if row["psu"] else "—"),
         ", ".join(row["switches"]) or ("switch on fixture" if row["integral_switch"]
                                        else "—"),
         ", ".join(sorted(set(row["controls"]))) or "—",
         "3-way+" if row["ways"] > 1 else "",
         "CROSS-CIRCUIT" if row["cross_circuit"] else "")
        for row in controls
    ]
    _add_table(fig, control_rows,
               ("Load", "Mark", "Room", "Circuit", "Switched by", "Control", "Ways", "Note"),
               bbox=(0.03, 0.24, 0.94, 0.37))

    runs = light_run_takeoff(model)
    fig.text(0.04, 0.215, "LED RUNS AND 24V SUPPLIES", fontsize=10, family="monospace",
             weight="bold")
    run_rows = [
        (row["tag"], row["mark"], row["room"] or "—", f"{row['length_ft']:.1f}",
         f"{row['watts']:.0f}", f"{row['volts']}V", row["psu"] or "—")
        for row in runs["runs"]
    ]
    run_rows.append(("TOTAL", "", "", f"{runs['total_length_ft']:.1f}", "", "", ""))
    _add_table(fig, run_rows,
               ("Run", "Mark", "Room", "LF", "Watts", "Volts", "Supply"),
               bbox=(0.03, 0.115, 0.52, 0.09))
    supply_rows = [
        (row["psu"], row["type"] or "—", f"{row['connected_watts']:.0f}",
         f"{row['required_watts']:.0f}",
         "—" if row["rated_watts"] is None else f"{row['rated_watts']:.0f}",
         "OK" if row["adequate"] else ("?" if row["adequate"] is None else "UNDERSIZED"))
        for row in runs["supplies"]
    ]
    _add_table(fig, supply_rows,
               ("Supply", "Type", "Connected W", "Req. W (125%)", "Rated W", ""),
               bbox=(0.57, 0.115, 0.40, 0.09))

    load = connected_lighting_va(model)
    fig.text(0.04, 0.09, "CONNECTED LIGHTING LOAD", fontsize=10, family="monospace",
             weight="bold")
    load_rows = [(row["circuit"], str(row["fixtures"]), f"{row['connected_va']:,.0f}")
                 for row in load["per_circuit"]]
    load_rows.append(("TOTAL CONNECTED", "", f"{load['total_connected_va']:,.0f} VA"))
    load_rows.append(("NEC 220.82 allowance", f"{load['conditioned_area_ft2']:,.0f} ft2",
                      f"{load['allowance_va']:,.0f} VA at "
                      f"{load['allowance_va_per_ft2']:.0f} VA/ft2"))
    _add_table(fig, load_rows, ("Circuit", "Fixtures", "Connected VA"),
               bbox=(0.03, 0.02, 0.52, 0.06))
    fig.text(0.57, 0.06, str(load["basis"]), fontsize=6, family="sans-serif", wrap=True)
    pdf.savefig(fig)
    plt.close(fig)


def _number(value: object, fmt: str) -> str:
    """A stated number in ``fmt``, or an em dash — never a plausible-looking zero."""
    return fmt.format(value) if isinstance(value, (int, float)) else ""


def _write_energy_sheet(pdf, model: ResolvedModel, number: str, name: str,
                        preferences: "Preferences | None" = None) -> None:
    """Three honest tables: prescriptive envelope, WWR, and a declared-not-Manual-J
    block load — the EN-1 rewrite (→ Permit-ready plan set Phase 7)."""
    import matplotlib.pyplot as plt

    from typehaus.checks.building_science.wwr import wwr_summary
    from typehaus.checks.code.mn_energy import evaluate_envelope
    from typehaus.checks.registry import Preferences
    from typehaus.energy import estimate_block_load

    prefs = preferences if preferences is not None else Preferences()

    fig = plt.figure(figsize=LEDGER)
    fig.text(0.04, 0.945, f"{number} · {name}", fontsize=16, family="monospace")

    fig.text(0.04, 0.90, "PRESCRIPTIVE ENVELOPE — MN 2024, CLIMATE ZONE 6", fontsize=10,
             family="monospace", weight="bold")
    prescriptive_rows = [
        (row.component, row.role, row.required, row.provided, row.verdict.upper())
        for row in evaluate_envelope(model, model.plan)
    ]
    _add_table(fig, prescriptive_rows,
              ("Component", "Use", "Required", "Provided", "Verdict"),
              bbox=(0.04, 0.62, 0.92, 0.26))

    fig.text(0.04, 0.575, "WINDOW-TO-WALL RATIO", fontsize=10, family="monospace",
             weight="bold")
    wwr = wwr_summary(model)
    wwr_rows = [("OVERALL", f"{wwr['overall']:.1%}")]
    wwr_rows.extend((item.facade, f"{item.ratio:.1%}") for item in wwr["per_facade"])
    _add_table(fig, wwr_rows, ("Facade", "Glazing / gross wall"), bbox=(0.04, 0.40, 0.4, 0.16))

    fig.text(0.04, 0.36, "BLOCK LOAD — NOT A MANUAL J", fontsize=10, family="monospace",
             weight="bold")
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
    sheet_chrome(fig, model, number, name)
    pdf.savefig(fig)
    plt.close(fig)


def write_compare_sheet(report: "object", output: Path) -> Path:
    """Render a one-page variant-compare sheet: element changes + quantity deltas.

    ``report`` is a ``typehaus.diff.CompareReport``. Kept off the permit-set index — this is a
    study sheet for comparing two design variants, not a permit deliverable.
    """
    import matplotlib.pyplot as plt

    output.parent.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(11, 14))
    fig.text(0.04, 0.975, "VARIANT COMPARE", fontsize=16, family="monospace")
    fig.text(0.04, 0.952, f"A: {report.label_a}", fontsize=9, family="monospace")
    fig.text(0.04, 0.936, f"B: {report.label_b}", fontsize=9, family="monospace")
    counts = ", ".join(f"{kind} {n}" for kind, n in sorted(report.diff.counts().items())) or "none"
    fig.text(0.04, 0.916, f"element changes: {counts}", fontsize=9, family="monospace")

    fig.text(0.04, 0.885, "ELEMENT CHANGES (A -> B)", fontsize=10, family="monospace",
             weight="bold")
    change_rows = [(c.kind.value, c.tag + (f" (was {c.was_tag})" if c.was_tag else ""),
                    c.ifc_class, c.delta) for c in report.diff.substantive()]
    _add_table(fig, change_rows or [("—", "no element changes", "", "")],
               ("Change", "Tag", "Class", "Delta"), bbox=(0.04, 0.45, 0.92, 0.40))

    fig.text(0.04, 0.41, "FRAMING QUANTITY DELTAS (A -> B)", fontsize=10, family="monospace",
             weight="bold")
    qty_rows = [(q.profile, q.metric, f"{q.baseline:,.1f}", f"{q.variant:,.1f}",
                 f"{q.delta:+,.1f}") for q in report.quantity_deltas]
    _add_table(fig, qty_rows or [("—", "no quantity change", "", "", "")],
               ("Size", "Metric", "A", "B", "Δ"), bbox=(0.04, 0.05, 0.7, 0.33))

    fig.savefig(output, dpi=110)
    plt.close(fig)
    return output


def _add_table(fig, rows: list[tuple], col_labels: tuple[str, ...],
               bbox: tuple[float, float, float, float]) -> None:
    """Contained tables: matplotlib's default rows are font-height-sized and spill past a
    short axes (the ledger page is 11" tall where the old portrait pages had 14-17").
    An explicit table bbox compresses rows to fit; a list too long for the box at legible
    lettering is split into two side-by-side runs, and the font tracks the row height."""
    if not rows:
        return
    height_pt = bbox[3] * fig.get_size_inches()[1] * 72.0
    capacity = max(4, int(height_pt / 7.5) - 1)  # rows that stay legible at ~6pt
    chunks = [rows]
    if len(rows) > capacity and len(rows) >= 8:
        half = (len(rows) + 1) // 2
        chunks = [rows[:half], rows[half:]]
    gap = 0.02
    width = (bbox[2] - gap * (len(chunks) - 1)) / len(chunks)
    for column, chunk in enumerate(chunks):
        ax = fig.add_axes((bbox[0] + column * (width + gap), bbox[1], width, bbox[3]))
        ax.axis("off")
        n = len(chunk) + 1  # + header row
        frac = min(1.0, n * 11.0 / height_pt)  # 11pt rows until the box is full
        row_pt = height_pt * frac / n
        table = ax.table(cellText=chunk, colLabels=col_labels, cellLoc="left",
                         colLoc="left", bbox=(0.0, 1.0 - frac, 1.0, frac))
        # ``fontsize=`` via ax.table does not stop the per-cell auto-shrink, which
        # crushes any run containing one wide cell; pin the size explicitly.
        table.auto_set_font_size(False)
        table.set_fontsize(max(3.2, min(6.0, row_pt * 0.72)))


def _close(fig: object) -> None:
    import matplotlib.pyplot as plt

    plt.close(fig)  # type: ignore[arg-type]
