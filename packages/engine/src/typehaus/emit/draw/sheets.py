"""Declarative permit-sheet composer built on the drawing IR (→ 20).

``build_sheet_index`` is the single source of truth for the sheet list: the cover's
printed index and the emitted pages are both derived from it, so they cannot drift.
Every plan/section/elevation sheet is a pure ``Scene`` builder; only the cover, opening
schedule, and energy summary compose matplotlib tables directly (no IR benefit for a table
page).
"""
from __future__ import annotations

from dataclasses import dataclass, replace
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
from typehaus.emit.draw.drainageplan import build_drainage_plan, has_drainage_content
from typehaus.emit.draw.plumbingplan import build_plumbing_plan, has_plumbing_content
from typehaus.emit.draw.sheet_writer import (
    LEDGER,
    PORTRAIT_LEDGER,
    compose_sheet,
    paper_for,
    set_paper,
)
from typehaus.emit.draw.roofframingplan import build_roof_framing_plan
from typehaus.emit.draw.roofplan import build_roof_plan
from typehaus.emit.draw.pdf_writer import _close
from typehaus.emit.draw.scene import Scene
from typehaus.emit.draw.schedules import (
    _has_data_content,
    _write_cover,
    _write_data_schedule,
    _write_energy_sheet,
    _write_framing_bom,
    _write_general_notes,
    _write_hardware_schedule,
    _write_luminaire_schedule,
    _write_opening_schedule,
    _write_panel_schedule,
    write_compare_sheet,
)
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


# The schedule writers live in ``schedules/`` but are re-exported here: this module is
# still the one name the rest of the engine (and the tests) import a permit sheet from.
__all__ = [
    "PORTRAIT_LEDGER",
    "SheetSpec",
    "build_sheet_index",
    "write_compare_sheet",
    "write_permit_set",
    "write_plan_dxfs",
]

def _derived_detail_title(derived: DerivedDetail) -> str:
    """A derived detail's sheet title, distinguished by the assemblies it actually cuts.

    ``derived.view.title`` is the *transition's* title, and a transition spawns one detail
    per distinct bound condition — so catlin printed fourteen consecutive sheets all called
    "TR-CATLIN-RIM-BAND", seven called "TR-CATLIN-FOUNDATION" and six "TR-CATLIN-EAVE". On
    the sheet index that is 27 of 98 rows saying nothing, and in the title block it means a
    sheet pulled off the pile cannot say which condition it is.

    ``derived.key`` is exactly the missing half — it is the bound condition, and it is
    unique by construction, which is why the detail set is keyed on it. ``condition:A|B``
    becomes "A / B" appended to the transition's own name.
    """
    title = derived.view.title or derived.key
    # ``rpartition``: a key is ``condition:A|B`` but a storey stack qualifies itself first
    # ("storey_stack:rim:A|B"), and splitting on the leading colon leaves that qualifier
    # stranded in front of the assemblies. The assembly list is always the last field.
    _, _, bound = derived.key.rpartition(":")
    pair = " / ".join(part for part in bound.split("|") if part)
    return f"{title} · {pair}" if pair else title


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
    # The paper the whole *set* is on, landscape (w, h) in inches — ``build_sheet_index``
    # stamps every spec with the one it was asked for, so a set cannot be half 11x17.
    paper: tuple[float, float] = LEDGER
    # Orientation is the sheet's own business: E-602's four stacked tables need portrait on
    # whatever paper the set is printing on, which is a rotation of ``paper`` and not a
    # second preset. ``size`` resolves the two.
    portrait: bool = False
    north_arrow: bool = False          # stamp a north arrow in the viewport (plan sheets)
    # Whether the sheet belongs in the *primary* set. Plans/sections/schedules and
    # authored details always do; a derived transition detail only when its Transition
    # is starred (model/views.py). ``build_sheet_index(details="primary")`` filters on it.
    primary: bool = True

    @property
    def size(self) -> tuple[float, float]:
        """The figure size this sheet composes at — ``paper``, turned if it is portrait."""
        return paper_for(self.paper, self.portrait)


def build_sheet_index(model: ResolvedModel,
                      preferences: "Preferences | None" = None,
                      profile: "JurisdictionProfile | None" = None,
                      details: str = "all",
                      paper: tuple[float, float] = LEDGER) -> list[SheetSpec]:
    """Assemble the ordered permit-set sheet list — the one place sheet order/content lives.

    ``details="all"`` (default) keeps every derived transition detail; ``"primary"``
    keeps only starred ones (the curated set a builder actually opens).

    ``paper`` is stamped onto every spec on the way out rather than threaded through the
    thirty-odd constructors below: sheet *content* has no opinion about sheet size, and a
    set printed half on 11x17 and half on 24x36 should not be expressible. A bigger sheet
    is not just a bigger picture — ``select_scale`` gets a bigger viewport, so the drawing
    climbs the ladder for free: catlin's A-101 goes from 1/16" = 1'-0" on ledger to
    3/16" = 1'-0" on ARCH D, and its main floor plan from 1/8" to 3/8"."""
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

    authored_details = [item for item in model.plan.elements_of_kind("Slice")
                        if item.kind.value == "detail"]
    next_detail = 401
    for detail in authored_details:
        sheets.append(SheetSpec(f"A-{next_detail}", detail.title or detail.tag,
                                scene=partial(build_authored_detail_scene, view=detail)))
        next_detail += 1

    # Derived transition details — one per distinct bound condition key, sorted by key,
    # continuing the A-4xx block after any authored details (→ 11b transition details).
    for derived in derive_detail_slices(model):
        tr = derived.transition
        starred = bool(tr.stars(derived.key)) if tr is not None else False
        if details == "primary" and not starred:
            continue
        sheets.append(SheetSpec(f"A-{next_detail}", _derived_detail_title(derived),
                                scene=partial(_derived_detail_scene, derived=derived),
                                primary=starred))
        next_detail += 1

    sheets.append(SheetSpec("A-601", "Door / window schedule", page=_write_opening_schedule))

    plumbing_storeys = [s.tag for s in storeys if has_plumbing_content(model, s.tag)]
    for index, storey_tag in enumerate(plumbing_storeys, start=1):
        sheets.append(SheetSpec(f"P-{100 + index}", f"Plumbing plan — {storey_tag}",
                                scene=partial(build_plumbing_plan, storey=storey_tag)))

    # P-2xx: the drainage plans, one per storey with stormwater content — the same
    # second-series-per-trade convention the lighting sheets use against E-10x. Gutters,
    # leaders, tile, trenches and pits are a different installer (and inspection) from the
    # sanitary/domestic rough-in on P-10x, and merging them buries the buried work.
    drainage_storeys = [s.tag for s in storeys if has_drainage_content(model, s.tag)]
    for index, storey_tag in enumerate(drainage_storeys, start=1):
        sheets.append(SheetSpec(f"P-{200 + index}", f"Drainage plan — {storey_tag}",
                                scene=partial(build_drainage_plan, storey=storey_tag),
                                north_arrow=True))

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
                                page=_write_luminaire_schedule, portrait=True))

    if _has_data_content(model):
        sheets.append(SheetSpec("E-603", "Data / low-voltage schedule",
                                page=_write_data_schedule))

    sheets.append(SheetSpec("EN-1", "Energy compliance summary",
                            page=partial(_write_energy_sheet, preferences=preferences)))
    return [replace(sheet, paper=paper) for sheet in sheets]


def _storey_elevation(model: ResolvedModel, storey_tag: str) -> float:
    storey = next((s for s in model.plan.storeys if s.tag == storey_tag), None)
    return storey.elevation.meters if storey is not None else 0.0


def write_permit_set(model: ResolvedModel, output: Path,
                     preferences: "Preferences | None" = None,
                     profile: "JurisdictionProfile | None" = None,
                     details: str = "all",
                     paper: tuple[float, float] = LEDGER,
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
    # checklist gate used — not "mn-2024" spelled out again on the cover and in the notes.
    if profile is None:
        profile = resolve_profile(preferences or Preferences())
    output.parent.mkdir(parents=True, exist_ok=True)
    sheets = build_sheet_index(model, preferences, profile, details=details, paper=paper)
    index = [(sheet.number, sheet.title) for sheet in sheets]
    # ``set_paper`` is how the table pages learn the paper: they compose their own figures
    # inside ``schedules/`` against a preset name, and this is the only place that knows
    # which paper the *set* is on (→ sheet_writer.schedule_sheet).
    with PdfPages(output) as pdf, set_paper(paper):
        for sheet in sheets:
            if sheet.number == "A-000":
                _write_cover(pdf, model, index, profile, preferences)
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
