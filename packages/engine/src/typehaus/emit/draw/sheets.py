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
from typehaus.emit.draw.pdf_writer import _fig
from typehaus.emit.draw.plumbingplan import build_plumbing_plan, has_plumbing_content
from typehaus.emit.draw.roofplan import build_roof_plan
from typehaus.emit.draw.scene import Scene
from typehaus.emit.draw.details import DerivedDetail, build_detail, derive_detail_slices
from typehaus.emit.draw.section import build_center_section, build_section
from typehaus.emit.draw.siteplan import build_site_plan
from typehaus.resolve.model import ResolvedModel


def _derived_detail_scene(model: ResolvedModel, derived: "DerivedDetail") -> Scene:
    scene, _findings = build_detail(model, derived)
    return scene

if TYPE_CHECKING:
    from typehaus.checks.registry import Preferences

SceneFn = Callable[[ResolvedModel], Scene]
PageFn = Callable[["object", ResolvedModel, str, str], None]  # pdf: PdfPages


@dataclass(frozen=True)
class SheetSpec:
    number: str                # "S-100"
    title: str                 # "Foundation plan"
    scale_note: str = "1/4\" = 1'-0\""
    scene: SceneFn | None = None       # IR-backed sheets
    page: PageFn | None = None         # table/cover pages


def build_sheet_index(model: ResolvedModel,
                      preferences: "Preferences | None" = None) -> list[SheetSpec]:
    """Assemble the ordered permit-set sheet list — the one place sheet order/content lives."""
    sheets: list[SheetSpec] = [SheetSpec("A-000", "Cover / code summary")]
    sheets.append(SheetSpec("C-101", "Site plan", "project north", scene=build_site_plan))

    if has_foundation_content(model):
        sheets.append(SheetSpec("S-100", "Foundation plan", scene=build_foundation_plan))

    floors = sorted(model.floors, key=lambda f: _storey_elevation(model, f.storey))
    for index, floor in enumerate(floors, start=1):
        number = "S-101" if len(floors) == 1 else f"S-101.{index}"
        sheets.append(SheetSpec(number, f"Framing plan — {floor.storey}",
                                scene=partial(build_framing_plan, floor_tag=floor.tag)))

    storeys = sorted(model.plan.storeys, key=lambda s: s.elevation.meters)
    floor_pages = [(f"A-{101 + i:03d}", storey.tag) for i, storey in enumerate(storeys)
                   if any(wall.storey == storey.tag for wall in model.walls)]
    for number, storey in floor_pages:
        sheets.append(SheetSpec(number, f"{storey.title()} floor plan",
                                scene=partial(build_floorplan, storey=storey)))

    sheets.append(SheetSpec(f"A-{101 + len(floor_pages):03d}", "Roof plan",
                            scene=build_roof_plan))
    sheets.append(SheetSpec("A-301", "Building section", scene=build_center_section))
    for number, facing in (("A-201", "north"), ("A-202", "south"),
                           ("A-203", "east"), ("A-204", "west")):
        sheets.append(SheetSpec(number, f"{facing.title()} exterior elevation",
                                scene=partial(build_elevation, facing=facing)))

    details = [item for item in model.plan.elements_of_kind("Slice")
              if item.kind.value == "detail"]
    next_detail = 401
    for detail in details:
        sheets.append(SheetSpec(f"A-{next_detail}", detail.title or detail.tag,
                                scene=partial(build_section, view=detail)))
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

    sheets.append(SheetSpec("EN-1", "Energy compliance summary",
                            page=partial(_write_energy_sheet, preferences=preferences)))
    return sheets


def _storey_elevation(model: ResolvedModel, storey_tag: str) -> float:
    storey = next((s for s in model.plan.storeys if s.tag == storey_tag), None)
    return storey.elevation.meters if storey is not None else 0.0


def write_permit_set(model: ResolvedModel, output: Path,
                     preferences: "Preferences | None" = None) -> tuple[Path, dict[str, object]]:
    """Compose the permit-set baseline into one multi-page PDF.

    The source plan remains authoritative: plans are drawing-IR scenes and schedules are
    derived from the same resolved openings. The intentionally modest title-block format
    lets jurisdictions accept an 11x17 residential review set while retaining the exact
    sheets needed for a professional handoff.
    """
    from matplotlib.backends.backend_pdf import PdfPages

    output.parent.mkdir(parents=True, exist_ok=True)
    sheets = build_sheet_index(model, preferences)
    index = [(sheet.number, sheet.title) for sheet in sheets]
    with PdfPages(output) as pdf:
        for sheet in sheets:
            if sheet.number == "A-000":
                _write_cover(pdf, model, index)
            elif sheet.page is not None:
                sheet.page(pdf, model, sheet.number, sheet.title)
            elif sheet.scene is not None:
                title = f"{sheet.number} · {sheet.title} · {sheet.scale_note}"
                fig = _fig(sheet.scene(model), title)
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


def _write_cover(pdf, model: ResolvedModel, index: list[tuple[str, str]]) -> None:
    import matplotlib.pyplot as plt
    from typehaus.checks import evaluate_permit_checklist, run_from_model

    fig, axis = plt.subplots(figsize=(11, 8.5))
    axis.axis("off")
    site = model.plan.project.site
    checklist = evaluate_permit_checklist(run_from_model(model, []), "mn-2024")
    axis.text(0.08, 0.86, model.plan.project.name, fontsize=28, family="monospace")
    axis.text(0.08, 0.79, "MINNESOTA RESIDENTIAL PERMIT SET", fontsize=13, family="monospace")
    axis.text(0.08, 0.70, f"Site: {site.lat:.5f}, {site.lon:.5f}\n"
              f"Climate zone 6 · framed model derived from Type:Haus", fontsize=10,
              family="monospace", va="top")
    axis.text(0.08, 0.54, "SHEET INDEX", fontsize=12, family="monospace", weight="bold")
    for row, (number, name) in enumerate(index):
        axis.text(0.10, 0.50 - row * 0.027, f"{number:6}  {name}", fontsize=8,
                  family="monospace")
    axis.text(0.08, 0.08,
              "Declared MN checklist: " + ("PASS" if checklist.ok else "NOT READY") + ". "
              "This set encodes a declared subset only; verify local amendments, engineering, "
              "MEP, and energy before construction.", fontsize=8, family="sans-serif", wrap=True)
    pdf.savefig(fig)
    plt.close(fig)


def _write_opening_schedule(pdf, model: ResolvedModel, number: str, name: str) -> None:
    import matplotlib.pyplot as plt

    fig, axis = plt.subplots(figsize=(11, 8.5))
    axis.axis("off")
    axis.text(0.06, 0.94, f"{number} · {name}", fontsize=16, family="monospace")
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
    axis.table(cellText=rows, colLabels=("Tag", "Kind", "Type", "Nominal footprint"),
               loc="center", cellLoc="left", colLoc="left", fontsize=6)
    pdf.savefig(fig)
    plt.close(fig)


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

    fig, axis = plt.subplots(figsize=(11, 14))
    axis.axis("off")
    axis.text(0.04, 0.985, f"{number} · {name}", fontsize=16, family="monospace")

    axis.text(0.04, 0.95, "PRESCRIPTIVE ENVELOPE — MN 2024, CLIMATE ZONE 6", fontsize=10,
              family="monospace", weight="bold")
    prescriptive_rows = [
        (row.component, row.role, row.required, row.provided, row.verdict.upper())
        for row in evaluate_envelope(model, model.plan)
    ]
    _add_table(fig, prescriptive_rows,
              ("Component", "Use", "Required", "Provided", "Verdict"),
              bbox=(0.04, 0.66, 0.92, 0.27))

    axis.text(0.04, 0.615, "WINDOW-TO-WALL RATIO", fontsize=10, family="monospace", weight="bold")
    wwr = wwr_summary(model)
    wwr_rows = [("OVERALL", f"{wwr['overall']:.1%}")]
    wwr_rows.extend((item.facade, f"{item.ratio:.1%}") for item in wwr["per_facade"])
    _add_table(fig, wwr_rows, ("Facade", "Glazing / gross wall"), bbox=(0.04, 0.44, 0.4, 0.15))

    axis.text(0.04, 0.37, "BLOCK LOAD — NOT A MANUAL J", fontsize=10, family="monospace",
              weight="bold")
    load = estimate_block_load(model, prefs)
    load_rows = [(component.kind, f"{component.area_ft2:,.0f}",
                 f"{component.ua_btu_per_hour_f:,.1f}") for component in load.components]
    load_rows.append(("TOTAL HEATING", "", f"{load.heating_load_btu_per_hour:,.0f} BTU/h"))
    load_rows.append(("TOTAL COOLING", "", f"{load.cooling_load_btu_per_hour:,.0f} BTU/h "
                                            f"({load.cooling_tons:.1f} tons)"))
    _add_table(fig, load_rows, ("Component", "Area (ft2)", "UA / total"),
              bbox=(0.04, 0.14, 0.5, 0.19))
    if load.unknown_inputs:
        axis.text(0.04, 0.10, "NOT A MANUAL J — unknown inputs: "
                  + ", ".join(load.unknown_inputs), fontsize=7, family="sans-serif", wrap=True)
    else:
        axis.text(0.04, 0.10, "NOT A MANUAL J — a transparent block-load estimate only.",
                  fontsize=7, family="sans-serif")
    pdf.savefig(fig)
    plt.close(fig)


def _add_table(fig, rows: list[tuple], col_labels: tuple[str, ...],
               bbox: tuple[float, float, float, float]) -> None:
    if not rows:
        return
    ax = fig.add_axes(bbox)
    ax.axis("off")
    ax.table(cellText=rows, colLabels=col_labels, loc="upper left", cellLoc="left",
             colLoc="left", fontsize=6)


def _close(fig: object) -> None:
    import matplotlib.pyplot as plt

    plt.close(fig)  # type: ignore[arg-type]
