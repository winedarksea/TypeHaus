"""Small, deterministic M3 permit-sheet composer built on the drawing IR."""

from __future__ import annotations

from pathlib import Path

from typehaus.emit.draw.floorplan import build_floorplan
from typehaus.emit.draw.elevation import build_elevation
from typehaus.emit.draw.roofplan import build_roof_plan
from typehaus.emit.draw.siteplan import build_site_plan
from typehaus.emit.draw.pdf_writer import _fig
from typehaus.emit.draw.section import build_center_section
from typehaus.resolve.model import ResolvedModel


def write_permit_set(model: ResolvedModel, output: Path) -> tuple[Path, dict[str, object]]:
    """Compose the Catlin permit-set baseline into one multi-page PDF.

    The source plan remains authoritative: plans are drawing-IR scenes and schedules are
    derived from the same resolved openings.  The intentionally modest title-block format
    lets jurisdictions accept an 11×17 residential review set while retaining the exact
    sheets needed for a professional handoff.
    """
    from matplotlib.backends.backend_pdf import PdfPages
    import matplotlib.pyplot as plt

    output.parent.mkdir(parents=True, exist_ok=True)
    storeys = sorted(model.plan.storeys, key=lambda item: item.elevation.meters)
    floor_pages = [(f"A-{101 + index:03d}", storey.tag)
                   for index, storey in enumerate(storeys)]
    page_index: list[tuple[str, str]] = [
        ("A-000", "Cover / code summary"), ("C-101", "Site plan"),
        ("S-100", "Foundation plan"),
        *[(number, f"{storey.title()} floor plan") for number, storey in floor_pages],
        (f"A-{101 + len(floor_pages):03d}", "Roof plan"), ("A-301", "Building section"),
        ("A-201", "North exterior elevation"), ("A-202", "South exterior elevation"),
        ("A-203", "East exterior elevation"), ("A-204", "West exterior elevation"),
        ("A-601", "Door / window schedule"), ("S-101", "Framing plans"),
        ("EN-1", "Energy compliance summary"),
    ]
    with PdfPages(output) as pdf:
        _write_cover(pdf, model, page_index)
        for number, name in page_index[1:]:
            if number == "C-101":
                _write_site_plan(pdf, model, number, name)
            elif number == "S-100":
                _write_plan(pdf, model, "basement", number, name)
            elif number in dict(floor_pages):
                _write_plan(pdf, model, dict(floor_pages)[number], number, name)
            elif name == "Roof plan":
                _write_roof_plan(pdf, model, number, name)
            elif number == "A-301":
                _write_section_summary(pdf, model, number, name)
            elif number.startswith("A-20"):
                _write_elevation(pdf, model, number, name)
            elif number == "A-601":
                _write_opening_schedule(pdf, model, number, name)
            elif number == "S-101":
                _write_plan(pdf, model, "second", number, name)
            else:
                _write_energy_summary(pdf, model, number, name)
    return output, {"index": page_index}


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


def _write_plan(pdf, model: ResolvedModel, storey: str, number: str, name: str) -> None:
    fig = _fig(build_floorplan(model, storey), f"{number} · {name} · 1/4\" = 1'-0\"")
    pdf.savefig(fig)
    _close(fig)


def _write_site_plan(pdf, model: ResolvedModel, number: str, name: str) -> None:
    fig = _fig(build_site_plan(model), f"{number} · {name} · project north")
    pdf.savefig(fig)
    _close(fig)


def _write_section_summary(pdf, model: ResolvedModel, number: str, name: str) -> None:
    fig = _fig(build_center_section(model), f"{number} · {name} · 1/4\" = 1'-0\"")
    pdf.savefig(fig)
    _close(fig)


def _write_elevation(pdf, model: ResolvedModel, number: str, name: str) -> None:
    facing = name.split()[0].lower()
    fig = _fig(build_elevation(model, facing), f"{number} · {name} · 1/4\" = 1'-0\"")
    pdf.savefig(fig)
    _close(fig)


def _write_roof_plan(pdf, model: ResolvedModel, number: str, name: str) -> None:
    fig = _fig(build_roof_plan(model), f"{number} · {name} · 1/4\" = 1'-0\"")
    pdf.savefig(fig)
    _close(fig)


def _write_opening_schedule(pdf, model: ResolvedModel, number: str, name: str) -> None:
    import matplotlib.pyplot as plt

    fig, axis = plt.subplots(figsize=(11, 8.5))
    axis.axis("off")
    axis.text(0.06, 0.94, f"{number} · {name}", fontsize=16, family="monospace")
    rows = [(opening.tag, "Door" if opening.is_door else "Window", opening.type_ref or "RO",
             f"{opening.width_m / 0.0254:.0f}\" × {opening.height_m / 0.0254:.0f}\"")
            for opening in sorted(model.openings, key=lambda item: item.tag)]
    types = {item.tag: item for item in model.plan.library.fixture_types}
    rows.extend(
        (fixture.tag, "Fixture", fixture.type_ref,
         f"{types[fixture.type_ref].footprint[0].inches:.0f}\" × "
         f"{types[fixture.type_ref].footprint[1].inches:.0f}\"")
        for storey in model.plan.storeys
        for fixture in model.plan.storey_elements(storey.tag)
        if fixture.element_kind == "Fixture" and fixture.type_ref in types
    )
    axis.table(cellText=rows, colLabels=("Tag", "Kind", "Type", "Nominal footprint"),
               loc="center", cellLoc="left", colLoc="left", fontsize=6)
    pdf.savefig(fig)
    plt.close(fig)


def _write_energy_summary(pdf, model: ResolvedModel, number: str, name: str) -> None:
    import matplotlib.pyplot as plt
    from typehaus.analysis import assembly_r_value

    fig, axis = plt.subplots(figsize=(11, 8.5))
    axis.axis("off")
    rows = [(assembly.tag, assembly_r_value(assembly, model.plan.library).fmt())
            for assembly in model.plan.library.assemblies]
    rows.extend((f"{zone.tag} radiant wire", f"{zone.wire_length_m / 0.3048:.0f} LF")
                for zone in model.floor_heat)
    axis.text(0.06, 0.94, f"{number} · {name}", fontsize=16, family="monospace")
    axis.table(cellText=rows, colLabels=("Assembly", "Nominal R-value"), loc="center",
               cellLoc="left", colLoc="left", fontsize=7)
    pdf.savefig(fig)
    plt.close(fig)


def _close(fig: object) -> None:
    import matplotlib.pyplot as plt

    plt.close(fig)  # type: ignore[arg-type]
