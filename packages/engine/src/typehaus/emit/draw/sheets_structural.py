"""The S-1xx..S-6xx structural sheets of ``build_sheet_index`` (split out of ``sheets.py``).

S-001 is not here: its cross-references read the finished set, so ``sheets.py`` splices it in.
"""
from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from typehaus.emit.draw.bracedwallplan import (
    build_braced_wall_plan,
    has_braced_wall_content,
)
from typehaus.emit.draw.datum import at_level
from typehaus.emit.draw.foundationplan import build_foundation_plan, has_foundation_content
from typehaus.emit.draw.framingplan import build_framing_plan
from typehaus.emit.draw.roofframingplan import build_roof_framing_plan
from typehaus.emit.draw.schedule_plan_sheet import schedule_plan_sheet
from typehaus.emit.draw.schedules import (
    _write_engineering_register,
    _write_framing_bom,
    _write_hardware_schedule,
)
from typehaus.emit.draw.schedules.paged_tables import page_count
from typehaus.emit.draw.schedules.structural import framing_bom_tables, hardware_tables
from typehaus.emit.draw.sheet_sets import FULL_ONLY
from typehaus.emit.draw.sheet_spec import (
    SheetSpec,
    _has_engineered_items,
    _paged,
    _storey_elevation,
)
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff import hardware_takeoff

if TYPE_CHECKING:
    from typehaus.checks.jurisdiction import JurisdictionProfile
    from typehaus.checks.registry import CheckReport, Preferences


def structural_sheets(model: ResolvedModel, level_tags: list[str],
                      at: dict[str, ResolvedModel], paper: tuple[float, float],
                      house_dir: Path | None, report: CheckReport | None, *,
                      profile: JurisdictionProfile | None,
                      preferences: Preferences | None = None) -> list[SheetSpec]:
    """S-100 foundation through S-603 engineering register, in set order."""
    sheets: list[SheetSpec] = []
    if has_foundation_content(model):
        sheets.append(SheetSpec("S-100", "Foundation plan",
                                scene=schedule_plan_sheet(build_foundation_plan,
                                                          profile=profile),
                                north_arrow=True))

    # S-101.n — ONE SHEET PER STOREY, not one per ``ResolvedFloor``. Catlin's main floor is
    # six framed bays, which used to be six sheets of one floor; a reviewer holding six
    # sheets of one floor cannot see the floor, and no sheet in that pile could show a beam
    # two bays share. ``framed_levels`` assigns the marks storey-wide, which is what makes
    # the merge honest rather than a collage.
    framed_storeys = [tag for tag in level_tags
                      if any(floor.storey == tag for floor in at[tag].floors)]
    for index, storey_tag in enumerate(framed_storeys, start=1):
        number = "S-101" if len(framed_storeys) == 1 else f"S-101.{index}"
        sheets.append(SheetSpec(number, f"Framing plan — {storey_tag}",
                                scene=schedule_plan_sheet(build_framing_plan, storey_tag),
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
                                scene=schedule_plan_sheet(build_roof_framing_plan,
                                                          roof_tag=roof.tag,
                                                          preferences=preferences),
                                north_arrow=True))

    # S-103.n — the braced wall plan, one per storey that has a braced wall line. MNSPECT
    # requires it per floor and runs a discrete braced-wall inspection against it. It stays
    # its own sheet rather than folding into S-101: braced-wall content exists on the
    # basement and the garage where no framed deck does, and S-101 is now the densest sheet
    # in the set.
    braced_storeys = [tag for tag in level_tags
                      if has_braced_wall_content(at[tag], tag)]
    for index, storey_tag in enumerate(braced_storeys, start=1):
        number = "S-103" if len(braced_storeys) == 1 else f"S-103.{index}"
        sheets.append(SheetSpec(number, f"Braced wall plan — {storey_tag}",
                                scene=at_level(build_braced_wall_plan, storey_tag),
                                north_arrow=True, keywords={"storey": storey_tag}))

    from typehaus.emit.draw.winder_detail import build_winder_detail

    for index, stair in enumerate((s for s in model.stairs if s.winder_turn is not None), 1):
        sheets.append(SheetSpec(f"S-501.{index}", f"{stair.tag} winder geometry and framing",
                                scene=partial(build_winder_detail, stair_tag=stair.tag)))

    if model.all_members():
        # Full only: a bill of materials is a builder's document, not a plan check's.
        # S-602 stays in the permit set (the framing inspection is run against it) and so
        # does S-603 (it says which items rest on a seal).
        sheets.extend(_paged("S-601", "Framing schedule / bill of materials",
                             _write_framing_bom,
                             page_count(framing_bom_tables(model), paper), sets=FULL_ONLY))

    # One PageFn emits one page, or the cover's index would drift from the set; a schedule
    # that outgrows its sheet continues on S-602.1, S-602.2 … (``_paged``).
    if hardware_takeoff(model):
        sheets.extend(_paged("S-602", "Connection hardware schedule", _write_hardware_schedule,
                             page_count(hardware_tables(model), paper)))

    # S-603 only where the house actually has engineering in it. A set answered entirely by
    # prescriptive tables gets no page saying so — an empty register reads as an omission,
    # and the cover already states the checklist verdict for that case.
    if _has_engineered_items(model, house_dir, report):
        sheets.append(SheetSpec("S-603", "Engineering register",
                                page=partial(_write_engineering_register,
                                             house_dir=house_dir)))

    return sheets
