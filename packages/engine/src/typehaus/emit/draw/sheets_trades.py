"""The P/M/E trade sheets of ``build_sheet_index`` (split out of ``sheets.py``)."""
from __future__ import annotations

from functools import partial

from typehaus.emit.draw.datum import at_level
from typehaus.emit.draw.drainageplan import build_drainage_plan, has_drainage_content
from typehaus.emit.draw.electricalplan import build_electrical_plan, has_electrical_content
from typehaus.emit.draw.hvacplan import build_hvac_plan, has_hvac_content
from typehaus.emit.draw.lightingplan import build_lighting_plan, has_lighting_content
from typehaus.emit.draw.paper import paper_for
from typehaus.emit.draw.plan_enlarged import enlarged_groups, enlarged_plan_sheet, enlarged_title
from typehaus.emit.draw.plumbingplan import build_plumbing_plan, has_plumbing_content
from typehaus.emit.draw.schedules import (
    _has_data_content,
    _write_data_schedule,
    _write_luminaire_schedule,
    _write_panel_schedule,
)
from typehaus.emit.draw.schedules.electrical import control_tables
from typehaus.emit.draw.schedules.electrical_labels import (
    has_label_schedule,
    label_tables,
    write_label_schedule,
)
from typehaus.emit.draw.schedules.grounding import (
    grounding_tables,
    has_grounding_schedule,
    write_grounding_schedule,
)
from typehaus.emit.draw.schedules.mechanical import (
    has_mechanical_schedule,
    mechanical_tables,
    write_mechanical_schedule,
)
from typehaus.emit.draw.schedules.paged_tables import page_count
from typehaus.emit.draw.schedules.plumbing import (
    has_plumbing_schedule,
    plumbing_tables,
    write_plumbing_schedule,
)
from typehaus.emit.draw.sheet_sets import FULL_ONLY
from typehaus.emit.draw.sheet_spec import SheetSpec, _paged
from typehaus.emit.draw.trade_frame import trade_plan_sheet
from typehaus.resolve.model import ResolvedModel


def trade_sheets(model: ResolvedModel, level_tags: list[str],
                 at: dict[str, ResolvedModel], paper: tuple[float, float]) -> list[SheetSpec]:
    """P-1xx/P-2xx/P-401/P-601, M-1xx/M-601, E-1xx/E-2xx and E-60x, in set order."""
    sheets: list[SheetSpec] = []
    plumbing_storeys = [tag for tag in level_tags if has_plumbing_content(at[tag], tag)]
    for index, storey_tag in enumerate(plumbing_storeys, start=1):
        # Full only. The Saint Paul DSI new-construction checklist asks for fixtures on
        # the floor plans and lists no separate P drawings; 1-2 family plumbing is exempt
        # from MN 4714 plan review. `[print] permit_add = ["P-1"]` restores them.
        sheets.append(SheetSpec(f"P-{100 + index}", f"Plumbing plan — {storey_tag}",
                                scene=trade_plan_sheet(build_plumbing_plan, storey_tag),
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
    # P-401: the mechanical rooms' plumbing at 1/2" (M2-106): the HW header and its lanes
    # overprint at the P-101 scale. A-402 is the same crop of the HVAC plan.
    groups = enlarged_groups(model, frozenset({"mechanical"}), paper) if plumbing_storeys else []
    for index, group in enumerate(groups, start=1):
        sheets.append(SheetSpec("P-401" if len(groups) == 1 else f"P-401.{index}",
                                enlarged_title("plumbing", group), north_arrow=True,
                                scene=partial(enlarged_plan_sheet, group=group,
                                              build=build_plumbing_plan),
                                sets=FULL_ONLY))
    if has_plumbing_schedule(model):
        # Stub heights off the fixture ports, and the lagged runs' insulation (M2-105).
        sheets.extend(_paged("P-601", "Plumbing rough-in and pipe insulation schedules",
                             write_plumbing_schedule,
                             page_count(plumbing_tables(model), paper), sets=FULL_ONLY))

    hvac_storeys = [tag for tag in level_tags if has_hvac_content(at[tag], tag)]
    for index, storey_tag in enumerate(hvac_storeys, start=1):
        sheets.append(SheetSpec(f"M-{100 + index}", f"HVAC plan — {storey_tag}",
                                scene=trade_plan_sheet(build_hvac_plan, storey_tag)))
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
                                scene=trade_plan_sheet(build_electrical_plan, storey_tag),
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
                             _write_luminaire_schedule,
                             1 + page_count(control_tables(model), paper_for(paper, True)),
                             portrait=True, sets=FULL_ONLY))

    if _has_data_content(model):
        sheets.append(SheetSpec("E-603", "Data / low-voltage schedule",
                                page=_write_data_schedule, sets=FULL_ONLY))

    if has_grounding_schedule(model):
        # Electrodes, bonds and the install notes (#123), paged like M-601.
        sheets.extend(_paged("E-604", "Grounding and bonding schedules", write_grounding_schedule,
                             page_count(grounding_tables(model), paper), sets=FULL_ONLY))

    if has_label_schedule(model):
        # The derived NEC labels and plaques (→ resolve/electrical_labels.py).
        sheets.extend(_paged("E-605", "Electrical label schedule", write_label_schedule,
                             page_count(label_tables(model), paper), sets=FULL_ONLY))

    return sheets
