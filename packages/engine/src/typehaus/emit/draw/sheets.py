"""Declarative permit-sheet composer built on the drawing IR (→ 20).

``build_sheet_index`` is the single source of truth for the sheet list: the cover's
printed index and the emitted pages are both derived from it, so they cannot drift.
Every plan/section/elevation sheet is a pure ``Scene`` builder; only the cover, opening
schedule, and energy summary compose matplotlib tables directly (no IR benefit for a table
page).
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from typehaus.emit.draw.bracedwallplan import (
    build_braced_wall_plan,
    has_braced_wall_content,
)
from typehaus.emit.draw.details import (
    DerivedDetail,
    build_authored_detail_scene,
    build_detail,
    derive_detail_slices,
)
from typehaus.emit.draw.drainageplan import build_drainage_plan, has_drainage_content
from typehaus.emit.draw.electricalplan import build_electrical_plan, has_electrical_content
from typehaus.emit.draw.elevation import build_elevation
from typehaus.emit.draw.floorplan import build_floorplan
from typehaus.emit.draw.foundationplan import build_foundation_plan, has_foundation_content
from typehaus.emit.draw.framingplan import build_framing_plan
from typehaus.emit.draw.hvacplan import build_hvac_plan, has_hvac_content
from typehaus.emit.draw.lightingplan import build_lighting_plan, has_lighting_content
from typehaus.emit.draw.pdf_writer import _close
from typehaus.emit.draw.plumbingplan import build_plumbing_plan, has_plumbing_content
from typehaus.emit.draw.roofframingplan import build_roof_framing_plan
from typehaus.emit.draw.roofplan import build_roof_plan
from typehaus.emit.draw.scene import Scene
from typehaus.emit.draw.schedules import (
    _has_data_content,
    _write_cover,
    _write_data_schedule,
    _write_energy_sheet,
    _write_engineering_register,
    _write_framing_bom,
    _write_general_notes,
    _write_hardware_schedule,
    _write_luminaire_schedule,
    _write_opening_schedule,
    _write_panel_schedule,
    _write_room_finish_schedule,
    _write_specifications,
    _write_symbols_legend,
    _write_ventilation_sheet,
    write_compare_sheet,
)
from typehaus.emit.draw.schedules.architectural import specification_sections
from typehaus.emit.draw.schedules.structural_notes import _write_structural_notes
from typehaus.emit.draw.section import build_center_section, build_section
from typehaus.emit.draw.sheet_sets import (
    BOTH_SETS,
    FULL_ONLY,
    FULL_SET,
    PERMIT_SET,
    in_set,
    resolve_set_name,
)
from typehaus.emit.draw.sheet_writer import (
    LEDGER,
    PORTRAIT_LEDGER,
    compose_sheet,
    paper_for,
    set_paper,
    set_seal_block,
)
from typehaus.emit.draw.siteplan import build_site_plan
from typehaus.emit.draw.title_block import SealBlock
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff import hardware_takeoff

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


def _derived_detail_scene(model: ResolvedModel, derived: DerivedDetail) -> Scene:
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
    # Which SETS this sheet belongs to. "full" is everything this engine can draw;
    # "permit" is what a Saint Paul DSI plan checker is asked to review, which is a
    # deliberately smaller thing — no separate E or P drawings (fixtures go on the floor
    # plans), no BOM, no room finish schedule, and only the starred derived details.
    # ``build_sheet_index(sets="permit")`` filters on it at the return.
    sets: frozenset[str] = BOTH_SETS

    @property
    def primary(self) -> bool:
        """Deprecated alias for permit-set membership. Kept for one release."""
        return PERMIT_SET in self.sets
    # What this sheet is ABOUT, for a caller that needs to find one without parsing its
    # title — ``{"storey": "main"}`` on the plan sheets. A dict rather than fields because
    # the set has no fixed vocabulary and a title is prose, not an index.
    keywords: Mapping[str, str] = field(default_factory=dict)

    @property
    def size(self) -> tuple[float, float]:
        """The figure size this sheet composes at — ``paper``, turned if it is portrait."""
        return paper_for(self.paper, self.portrait)


def build_sheet_index(model: ResolvedModel,
                      preferences: Preferences | None = None,
                      profile: JurisdictionProfile | None = None,
                      details: str | None = None,
                      paper: tuple[float, float] = LEDGER,
                      house_dir: Path | None = None,
                      sets: str = FULL_SET) -> list[SheetSpec]:
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
    3/16" = 1'-0" on ARCH D, and its main floor plan from 1/8" to 3/8"."""
    # NCS discipline order is G -> C -> S -> A -> P -> M -> E, and the second digit is the
    # SHEET TYPE: 0 general, 1 plans, 2 elevations, 3 sections, 4 large-scale views,
    # 5 details, 6 schedules, 7-8 user-defined, 9 3D. Sequence within a type is
    # deliberately non-consecutive so a sheet can be inserted without renumbering the set.
    # The cover is G-001, not A-000: a cover is general information, not architectural.
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
    sheets.append(SheetSpec("C-101", "Site plan", "project north", scene=build_site_plan,
                            north_arrow=True))

    # S-001 — general structural notes, and it is UNCONDITIONAL. It replaces S-002, whose
    # gate was "any specification section exists": on catlin that printed one bullet, and
    # on a house with nothing authored it printed no sheet at all — precisely the house
    # that most needs a sheet saying what is and is not known. Divisions 03/05 are now one
    # block on it, so A-002 still keeps the remainder and nothing prints twice.
    sheets.append(SheetSpec("S-001", "General structural notes",
                            page=partial(_write_structural_notes, profile=profile,
                                         preferences=preferences, house_dir=house_dir)))

    if has_foundation_content(model):
        sheets.append(SheetSpec("S-100", "Foundation plan",
                                scene=partial(build_foundation_plan, profile=profile),
                                north_arrow=True))

    # S-101.n — ONE SHEET PER STOREY, not one per ``ResolvedFloor``. Catlin's main floor is
    # six framed bays, which used to be six sheets of one floor; a reviewer holding six
    # sheets of one floor cannot see the floor, and no sheet in that pile could show a beam
    # two bays share. ``framed_levels`` assigns the marks storey-wide, which is what makes
    # the merge honest rather than a collage.
    framed_storeys = [storey.tag for storey in sorted(model.plan.storeys,
                                                      key=lambda s: s.elevation.meters)
                      if any(floor.storey == storey.tag for floor in model.floors)]
    for index, storey_tag in enumerate(framed_storeys, start=1):
        number = "S-101" if len(framed_storeys) == 1 else f"S-101.{index}"
        sheets.append(SheetSpec(number, f"Framing plan — {storey_tag}",
                                scene=partial(build_framing_plan, storey=storey_tag),
                                north_arrow=True, keywords={"storey": storey_tag}))

    # Roof framing keeps its own S-102 series: a roof is a framed level too, but numbering
    # it S-101.n would make the floor-sheet count depend on how many roofs a house has.
    # S-102 is emitted BEFORE S-103 — the loops used to run the other way round, so the set
    # printed every braced-wall sheet and then the roof sheets behind them, out of number
    # order for anyone flipping through the pile.
    roofs = sorted(model.roofs, key=lambda r: (_storey_elevation(model, r.storey), r.tag))
    for index, roof in enumerate(roofs, start=1):
        number = "S-102" if len(roofs) == 1 else f"S-102.{index}"
        sheets.append(SheetSpec(number, f"Roof framing plan — {roof.tag}",
                                scene=partial(build_roof_framing_plan, roof_tag=roof.tag),
                                north_arrow=True))

    # S-103.n — the braced wall plan, one per storey that has a braced wall line. MNSPECT
    # requires it per floor and runs a discrete braced-wall inspection against it. It stays
    # its own sheet rather than folding into S-101: braced-wall content exists on the
    # basement and the garage where no framed deck does, and S-101 is now the densest sheet
    # in the set.
    braced_storeys = [s.tag for s in sorted(model.plan.storeys,
                                            key=lambda s: s.elevation.meters)
                      if has_braced_wall_content(model, s.tag)]
    for index, storey_tag in enumerate(braced_storeys, start=1):
        number = "S-103" if len(braced_storeys) == 1 else f"S-103.{index}"
        sheets.append(SheetSpec(number, f"Braced wall plan — {storey_tag}",
                                scene=partial(build_braced_wall_plan, storey=storey_tag),
                                north_arrow=True, keywords={"storey": storey_tag}))

    if model.all_members():
        # Full only: a bill of materials is a builder's document, not a plan check's.
        # S-602 stays in the permit set (the framing inspection is run against it) and so
        # does S-603 (it says which items rest on a seal).
        sheets.append(SheetSpec("S-601", "Framing schedule / bill of materials",
                                page=_write_framing_bom, sets=FULL_ONLY))

    # Hardware gets its own sheet rather than a second page under S-103: a PageFn that
    # emits two pages would put the cover's printed index one page out of step with the
    # emitted set, which ``build_sheet_index`` exists to prevent.
    if hardware_takeoff(model):
        sheets.append(SheetSpec("S-602", "Connection hardware schedule",
                                page=_write_hardware_schedule))

    # S-105 only where the house actually has engineering in it. A set answered entirely by
    # prescriptive tables gets no page saying so — an empty register reads as an omission,
    # and the cover already states the checklist verdict for that case.
    if _has_engineered_items(model, house_dir):
        sheets.append(SheetSpec("S-603", "Engineering register",
                                page=partial(_write_engineering_register,
                                             house_dir=house_dir)))

    if specification_sections(model):
        sheets.append(SheetSpec("A-002", "Architectural specifications",
                                page=_write_specifications))

    storeys = sorted(model.plan.storeys, key=lambda s: s.elevation.meters)
    floor_pages = [(f"A-{101 + i:03d}", storey.tag) for i, storey in enumerate(storeys)
                   if any(wall.storey == storey.tag for wall in model.walls)]
    for number, storey in floor_pages:
        sheets.append(SheetSpec(number, f"{storey.title()} floor plan",
                                scene=partial(build_floorplan, storey=storey),
                                north_arrow=True))

    sheets.append(SheetSpec(f"A-{101 + len(floor_pages):03d}", "Roof plan",
                            scene=build_roof_plan, north_arrow=True))
    # Elevations BEFORE sections: the type digit is the order (2 then 3), and the set was
    # emitting A-301 first. A reviewer works outside-in — what the building looks like, then
    # what it is cut open to show — and the numbering already said so.
    for number, facing in (("A-201", "north"), ("A-202", "south"),
                           ("A-203", "east"), ("A-204", "west")):
        sheets.append(SheetSpec(number, f"{facing.title()} exterior elevation",
                                scene=partial(build_elevation, facing=facing)))

    sheets.append(SheetSpec("A-301", "Building section", scene=build_center_section))
    # Authored SECTION slices join the A-301 series right after the auto centre section —
    # one sheet per authored cut, in authoring order (→ Permit-ready plan set Phase 6).
    sections = [item for item in model.plan.elements_of_kind("Slice")
                if item.kind.value == "section"]
    for index, view in enumerate(sections, start=1):
        sheets.append(SheetSpec(f"A-301.{index}", view.title or view.tag,
                                scene=partial(build_section, view=view)))

    # The 5 series, not the 4. NCS 4 is LARGE-SCALE VIEWS — an enlarged plan of a kitchen or
    # a stair at 1/2" = 1'-0", the same drawing type as the plan it comes from. A junction
    # cut at 1-1/2" = 1'-0" is a DETAIL and belongs in 5. This set has no large-scale views,
    # so the 4 series is simply absent, which is what a non-consecutive sequence is for.
    authored_details = [item for item in model.plan.elements_of_kind("Slice")
                        if item.kind.value == "detail"]
    next_detail = 501
    for detail in authored_details:
        sheets.append(SheetSpec(f"A-{next_detail}", detail.title or detail.tag,
                                scene=partial(build_authored_detail_scene, view=detail)))
        next_detail += 1

    # Derived transition details — one per distinct bound condition key, sorted by key,
    # continuing the A-4xx block after any authored details (→ 11b transition details).
    for derived in derive_detail_slices(model):
        tr = derived.transition
        starred = bool(tr.stars(derived.key)) if tr is not None else False
        # NUMBERED BEFORE FILTERED. ``FIRST_DETAIL_SHEET`` numbers every derived detail,
        # so a detail's number is the same in the permit set and the full set — a callout
        # on A-101 pointing at A-517 must not move because a sheet ahead of it dropped.
        sheets.append(SheetSpec(f"A-{next_detail}", _derived_detail_title(derived),
                                scene=partial(_derived_detail_scene, derived=derived),
                                sets=BOTH_SETS if starred else FULL_ONLY))
        next_detail += 1

    # A-601 used to be doors, windows AND fixtures on one sheet. They are three schedules
    # with three readers — a door supplier, a glazing supplier, and whoever is setting
    # plumbing — and NCS gives each its own sheet in the 6 series.
    sheets.append(SheetSpec("A-601", "Door schedule",
                            page=partial(_write_opening_schedule, kinds="door")))
    sheets.append(SheetSpec("A-602", "Window schedule",
                            page=partial(_write_opening_schedule, kinds="window")))
    sheets.append(SheetSpec("A-603", "Room finish schedule",
                            page=_write_room_finish_schedule, sets=FULL_ONLY))

    plumbing_storeys = [s.tag for s in storeys if has_plumbing_content(model, s.tag)]
    for index, storey_tag in enumerate(plumbing_storeys, start=1):
        # Full only. The Saint Paul DSI new-construction checklist asks for fixtures on
        # the floor plans and lists no separate P drawings; 1-2 family plumbing is exempt
        # from MN 4714 plan review. `[print] permit_add = ["P-1"]` restores them.
        sheets.append(SheetSpec(f"P-{100 + index}", f"Plumbing plan — {storey_tag}",
                                scene=partial(build_plumbing_plan, storey=storey_tag),
                                sets=FULL_ONLY))

    # P-2xx: the drainage plans, one per storey with stormwater content — the same
    # second-series-per-trade convention the lighting sheets use against E-10x. Gutters,
    # leaders, tile, trenches and pits are a different installer (and inspection) from the
    # sanitary/domestic rough-in on P-10x, and merging them buries the buried work.
    drainage_storeys = [s.tag for s in storeys if has_drainage_content(model, s.tag)]
    for index, storey_tag in enumerate(drainage_storeys, start=1):
        # Full only: the grading and discharge story a reviewer wants belongs on C-101.
        sheets.append(SheetSpec(f"P-{200 + index}", f"Drainage plan — {storey_tag}",
                                scene=partial(build_drainage_plan, storey=storey_tag),
                                north_arrow=True, sets=FULL_ONLY))

    hvac_storeys = [s.tag for s in storeys if has_hvac_content(model, s.tag)]
    for index, storey_tag in enumerate(hvac_storeys, start=1):
        sheets.append(SheetSpec(f"M-{100 + index}", f"HVAC plan — {storey_tag}",
                                scene=partial(build_hvac_plan, storey=storey_tag)))

    electrical_storeys = [s.tag for s in storeys if has_electrical_content(model, s.tag)]
    for index, storey_tag in enumerate(electrical_storeys, start=1):
        # Full only, same reason as P-1xx: electrical is permitted by the State Board of
        # Electricity, not by DSI, and the checklist names no E drawings.
        sheets.append(SheetSpec(f"E-{100 + index}", f"Electrical plan — {storey_tag}",
                                scene=partial(build_electrical_plan, storey=storey_tag),
                                sets=FULL_ONLY))

    # E-2xx: the lighting plans, one per storey that has luminaires. A separate series
    # from the E-10x power sheets on purpose — an electrician wiring devices and a reader
    # checking what hangs over the dining table want two different drawings, and merging
    # them produces a sheet too dense to be either.
    lighting_storeys = [s.tag for s in storeys if has_lighting_content(model, s.tag)]
    for index, storey_tag in enumerate(lighting_storeys, start=1):
        sheets.append(SheetSpec(f"E-{200 + index}", f"Lighting plan — {storey_tag}",
                                scene=partial(build_lighting_plan, storey=storey_tag),
                                sets=FULL_ONLY))

    if model.plan.library.circuits:
        sheets.append(SheetSpec("E-601", "Panel schedule / service load",
                                page=_write_panel_schedule))

    if lighting_storeys:
        sheets.append(SheetSpec("E-602", "Luminaire schedule / lighting controls",
                                page=_write_luminaire_schedule, portrait=True,
                                sets=FULL_ONLY))

    if _has_data_content(model):
        sheets.append(SheetSpec("E-603", "Data / low-voltage schedule",
                                page=_write_data_schedule, sets=FULL_ONLY))

    return [replace(sheet, paper=paper) for sheet in sheets
            if in_set(sheet, resolve_set_name(sets, details), preferences)]


def _storey_elevation(model: ResolvedModel, storey_tag: str) -> float:
    storey = next((s for s in model.plan.storeys if s.tag == storey_tag), None)
    return storey.elevation.meters if storey is not None else 0.0


def write_permit_set(model: ResolvedModel, output: Path,
                     preferences: Preferences | None = None,
                     profile: JurisdictionProfile | None = None,
                     details: str | None = None,
                     paper: tuple[float, float] = LEDGER,
                     house_dir: Path | None = None,
                     sets: str = FULL_SET,
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
    sheets = build_sheet_index(model, preferences, profile, details=details,
                               paper=paper, house_dir=house_dir, sets=sets)
    index = [(sheet.number, sheet.title) for sheet in sheets]
    # ``set_paper`` is how the table pages learn the paper: they compose their own figures
    # inside ``schedules/`` against a preset name, and this is the only place that knows
    # which paper the *set* is on (→ sheet_writer.schedule_sheet).
    with PdfPages(output) as pdf, set_paper(paper), set_seal_block(_seal_block(profile, house_dir)):
        for sheet in sheets:
            if sheet.number == "G-001":
                _write_cover(pdf, model, index, profile, preferences)
            elif sheet.page is not None:
                sheet.page(pdf, model, sheet.number, sheet.title)
            elif sheet.scene is not None:
                fig = compose_sheet(sheet.scene(model), sheet, model, size=sheet.size)
                pdf.savefig(fig)
                _close(fig)
    return output, {"index": index}


def _seal_block(profile: JurisdictionProfile, house_dir: Path | None) -> SealBlock:
    """The seal cell every S-sheet and the cover carry.

    The four lines print RULED AND BLANK unless this set went out past ``--sealed``, which
    is read off the issue stamp rather than passed down a second time: ``cmd_sheets`` only
    appends ``· SEALED`` after its own final gate opened, so the stamp and the seal cell
    read one decision and cannot disagree — the invariant the stamp already holds.

    A name comes from ``engineering.toml``, which this engine reads and never writes. With
    no register, or none this house declares, the lines stay blank: a filled NAME line is a
    claim about a human act, and only a human may make it.
    """
    from typehaus.emit.draw.title_block import _ISSUE

    block = SealBlock(certification=profile.seal_certification)
    if " · SEALED" not in _ISSUE.get() or house_dir is None:
        return block
    from typehaus.engineering.register import load_register

    signoffs = load_register(house_dir).signoffs
    if not signoffs:
        return block
    # The first signoff is the one the structural set rests on. A second sealer covers other
    # items and is named on S-603, where there is room to say what each one covers.
    first = signoffs[0]
    return replace(block, credit=first.credit(), engineer=first.engineer,
                   license=first.license, sealed_on=first.sealed_on.isoformat())


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


def _has_engineered_items(model: ResolvedModel, house_dir: Path | None) -> bool:
    """Whether any check in this house delegates to the engineering register.

    Asked by running the registry, not by enumerating the suite: which requirements a house
    puts outside the prescriptive path is a conclusion the checks reach, and a second
    enumeration here would be that judgement written twice.
    """
    from typehaus.checks import run_from_model

    report = run_from_model(model, [], house_dir)
    return any(finding.engineering_item for finding in report.findings)
