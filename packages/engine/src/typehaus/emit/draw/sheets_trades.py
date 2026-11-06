"""The P/M/E trade sheets of ``build_sheet_index`` (split out of ``sheets.py``)."""
from __future__ import annotations

from typehaus.emit.draw.datum import at_level
from typehaus.emit.draw.drainageplan import build_drainage_plan, has_drainage_content
from typehaus.emit.draw.electricalplan import build_electrical_plan, has_electrical_content
from typehaus.emit.draw.hvacplan import build_hvac_plan, has_hvac_content
from typehaus.emit.draw.lightingplan import build_lighting_plan, has_lighting_content
from typehaus.emit.draw.plumbingplan import build_plumbing_plan, has_plumbing_content
from typehaus.emit.draw.schedules import (
    _has_data_content,
    _write_data_schedule,
    _write_luminaire_schedule,
    _write_panel_schedule,
)
from typehaus.emit.draw.schedules.mechanical import (
    has_mechanical_schedule,
    mechanical_tables,
    write_mechanical_schedule,
)
from typehaus.emit.draw.schedules.paged_tables import page_count
from typehaus.emit.draw.sheet_sets import FULL_ONLY
from typehaus.emit.draw.sheet_spec import SheetSpec, _paged
from typehaus.resolve.model import ResolvedModel


def trade_sheets(model: ResolvedModel, level_tags: list[str],
                 at: dict[str, ResolvedModel], paper: tuple[float, float]) -> list[SheetSpec]:
    """P-1xx/P-2xx, M-1xx/M-601, E-1xx/E-2xx and E-60x, in set order."""
    sheets: list[SheetSpec] = []
    plumbing_storeys = [tag for tag in level_tags if has_plumbing_content(at[tag], tag)]
    for index, storey_tag in enumerate(plumbing_storeys, start=1):
        # Full only. The Saint Paul DSI new-construction checklist asks for fixtures on
        # the floor plans and lists no separate P drawings; 1-2 family plumbing is exempt
        # from MN 4714 plan review. `[print] permit_add = ["P-1"]` restores them.
        sheets.append(SheetSpec(f"P-{100 + index}", f"Plumbing plan — {storey_tag}",
                                scene=at_level(build_plumbing_plan, storey_tag),
                                sets=FULL_ONLY))

    # P-2xx: the drainage plans, one per storey with stormwater content — the same
    # second-series-per-trade convention the lighting sheets use against E-10x. Gutters,
    # leaders, tile, trenches and pits are a different installer (and inspection) from the
    # sanitary/domestic rough-in on P-10x, and merging them buries the buried work.
    drainage_storeys = [tag for tag in level_tags if has_drainage_content(at[tag], tag)]
    for index, storey_tag in enumerate(drainage_storeys, start=1):
        # Full only: the grading and discharge story a reviewer wants belongs on C-101.
        sheets.append(SheetSpec(f"P-{200 + index}", f"Drainage plan — {storey_tag}",
                                scene=at_level(build_drainage_plan, storey_tag),
                                north_arrow=True, sets=FULL_ONLY))

    hvac_storeys = [tag for tag in level_tags if has_hvac_content(at[tag], tag)]
    for index, storey_tag in enumerate(hvac_storeys, start=1):
        sheets.append(SheetSpec(f"M-{100 + index}", f"HVAC plan — {storey_tag}",
                                scene=at_level(build_hvac_plan, storey_tag)))
    if has_mechanical_schedule(model):
        # Duct construction + duct/terminal schedules (#114), paged like S-602.
        sheets.extend(_paged("M-601", "Duct and air terminal schedules",
                             write_mechanical_schedule,
                             page_count(mechanical_tables(model), paper)))

    electrical_storeys = [tag for tag in level_tags if has_electrical_content(at[tag], tag)]
    for index, storey_tag in enumerate(electrical_storeys, start=1):
        # Full only, same reason as P-1xx: electrical is permitted by the State Board of
        # Electricity, not by DSI, and the checklist names no E drawings.
        sheets.append(SheetSpec(f"E-{100 + index}", f"Electrical plan — {storey_tag}",
                                scene=at_level(build_electrical_plan, storey_tag),
                                sets=FULL_ONLY))

    # E-2xx: the lighting plans, one per storey that has luminaires. A separate series
    # from the E-10x power sheets on purpose — an electrician wiring devices and a reader
    # checking what hangs over the dining table want two different drawings, and merging
    # them produces a sheet too dense to be either.
    lighting_storeys = [tag for tag in level_tags if has_lighting_content(at[tag], tag)]
    for index, storey_tag in enumerate(lighting_storeys, start=1):
        sheets.append(SheetSpec(f"E-{200 + index}", f"Lighting plan — {storey_tag}",
                                scene=at_level(build_lighting_plan, storey_tag),
                                sets=FULL_ONLY))

    if model.plan.library.circuits:
        sheets.append(SheetSpec("E-601", "Panel schedule / service load",
                                page=_write_panel_schedule))

    if lighting_storeys:
        sheets.extend(_paged("E-602", "Luminaire schedule / lighting controls",
                             _write_luminaire_schedule, 2, portrait=True, sets=FULL_ONLY))

    if _has_data_content(model):
        sheets.append(SheetSpec("E-603", "Data / low-voltage schedule",
                                page=_write_data_schedule, sets=FULL_ONLY))

    return sheets
