"""The block load's two air-side terms: blower-door infiltration and ERV ventilation.

Known-answer arithmetic (1.08 · CFM · ΔT, with CFMnat = CFM50 / N from the LBL model) plus
the tri-state contract: an unauthored input is *named* in ``unknown_inputs`` and its term is
dropped, never replaced by a leakage or recovery rule of thumb.
"""

from __future__ import annotations

import pytest

from typehaus.checks.registry import Preferences
from typehaus.energy import estimate_block_load
from typehaus.model import (
    Assembly,
    Building,
    CavityFill,
    Equipment,
    EquipmentKind,
    EquipmentType,
    Layer,
    LayerFunction,
    Library,
    Material,
    Node,
    Occupancy,
    PlanModel,
    Project,
    Room,
    Site,
    Storey,
    Wall,
    degF,
    ft,
    inch,
    pt,
)
from typehaus.resolve import resolve

_AIR = 1.08
_SETPOINT_F = 70.0
_DESIGN_F = -15.0
_HEATING_DELTA = _SETPOINT_F - _DESIGN_F  # 85 F
_M3_TO_FT3 = 35.31466672148859

_MATERIALS = (
    Material(tag="gwb", name="Gypsum board", r_per_inch=0.9, perm_rating=18.8),
    Material(tag="spf", name="SPF framing", r_per_inch=1.25, perm_rating=2.9),
    Material(tag="wool", name="Mineral wool", r_per_inch=4.2, perm_rating=116.0),
    Material(tag="ply", name="Structural plywood", r_per_inch=1.25, perm_rating=0.30),
)

_ASSEMBLY = Assembly(tag="EXT", layers=(
    Layer(name="gwb", material_ref="gwb", thickness=inch(0.625),
          function=LayerFunction.FINISH),
    Layer(name="stud", material_ref="spf", thickness=inch(5.5),
          function=LayerFunction.STRUCTURE, cavity=CavityFill(material_ref="wool")),
    Layer(name="sheathing", material_ref="ply", thickness=inch(0.5),
          function=LayerFunction.SHEATHING),
    Layer(name="siding", material_ref="ply", thickness=inch(0.5),
          function=LayerFunction.CLADDING),
))


def _plan(equipment_types=(), equipment=()) -> PlanModel:
    """One clad 20'x14' room, 9' ceiling — enough envelope to have a volume."""
    library = Library(materials=_MATERIALS, assemblies=(_ASSEMBLY,),
                      equipment_types=tuple(equipment_types))
    project = Project(name="AIR", project_uuid="00000000-0000-4000-8000-0000000000a1",
                      site=Site(lat=44.9, lon=-93.2, elevation=ft(830),
                                design_temp_heating=degF(_DESIGN_F),
                                design_temp_cooling=degF(90)),
                      building=Building(name="AIR"))
    storeys = (Storey(uid="ST00000a01", tag="main", elevation=ft(0),
                      default_ceiling_height=ft(9)),)
    plan = PlanModel(project=project, library=library, storeys=storeys)
    nodes = tuple(
        Node(uid=f"N100000{i:03d}", tag=f"N-{i}", position=position)
        for i, position in enumerate((
            pt(ft(0), ft(0)), pt(ft(20), ft(0)), pt(ft(20), ft(14)), pt(ft(0), ft(14)),
        ), 1))
    walls = tuple(
        Wall(uid=f"W100000{i:03d}", tag=f"W-{i}", start_node=f"N-{start}",
             end_node=f"N-{end}", assembly="EXT", top=ft(9))
        for i, (start, end) in enumerate(((1, 2), (2, 3), (3, 4), (4, 1)), 1))
    room = Room(uid="RM00000a01", tag="RM-MAIN", seed=pt(ft(10), ft(7)),
                occupancy=Occupancy.LIVING)
    return plan.with_elements("main", (*nodes, *walls, room, *equipment))


def _resolved(plan: PlanModel):
    model, findings = resolve(plan)
    assert not [f for f in findings if f.severity.value == "error"], findings
    return model


def _volume_ft3(model) -> float:
    room = next(room for room in model.rooms if room.tag == "RM-MAIN")
    return room.area_m2 * ft(9).meters * _M3_TO_FT3


# --- infiltration ---------------------------------------------------------------------

def test_cfm50_gives_the_lbl_known_answer() -> None:
    """CFM50 is the measurement, so it needs no volume at all: 1080/18 = 60 CFMnat."""
    model = _resolved(_plan())
    report = estimate_block_load(
        model, Preferences(cfm50=1080.0, infiltration_n_factor=18.0,
                           interior_setpoint_f=_SETPOINT_F, window_u=0.25))
    assert report.infiltration_btu_per_hour == pytest.approx(_AIR * 60.0 * _HEATING_DELTA)
    assert not any("ach50" in item for item in report.unknown_inputs)


def test_ach50_is_normalized_through_the_conditioned_volume() -> None:
    model = _resolved(_plan())
    prefs = Preferences(ach50=1.0, infiltration_n_factor=18.0,
                        interior_setpoint_f=_SETPOINT_F, window_u=0.25)
    report = estimate_block_load(model, prefs)
    expected_cfm = (1.0 * _volume_ft3(model) / 60.0) / 18.0
    assert report.infiltration_btu_per_hour == pytest.approx(
        _AIR * expected_cfm * _HEATING_DELTA)


def test_cfm50_wins_over_ach50_when_both_are_authored() -> None:
    """A blower-door CFM50 is the reading; the ACH50 beside it is derived from it."""
    model = _resolved(_plan())
    report = estimate_block_load(
        model, Preferences(cfm50=1080.0, ach50=99.0, infiltration_n_factor=18.0,
                           interior_setpoint_f=_SETPOINT_F, window_u=0.25))
    assert report.infiltration_btu_per_hour == pytest.approx(_AIR * 60.0 * _HEATING_DELTA)


def test_n_factor_divides_the_blower_door_result() -> None:
    model = _resolved(_plan())
    base = Preferences(cfm50=1080.0, interior_setpoint_f=_SETPOINT_F, window_u=0.25)
    tight = estimate_block_load(model, Preferences(**{**vars(base), "infiltration_n_factor": 24.0}))
    loose = estimate_block_load(model, Preferences(**{**vars(base), "infiltration_n_factor": 12.0}))
    assert loose.infiltration_btu_per_hour == pytest.approx(
        2.0 * tight.infiltration_btu_per_hour)


def test_no_blower_door_result_is_unknown_not_zero_leakage() -> None:
    model = _resolved(_plan())
    report = estimate_block_load(
        model, Preferences(interior_setpoint_f=_SETPOINT_F, window_u=0.25))
    assert report.infiltration_btu_per_hour == 0.0
    assert any("ach50/cfm50" in item for item in report.unknown_inputs)


def test_infiltration_is_included_in_the_heating_load() -> None:
    """The term is reported separately *and* summed — not one or the other."""
    model = _resolved(_plan())
    base = Preferences(interior_setpoint_f=_SETPOINT_F, window_u=0.25)
    with_air = Preferences(cfm50=1080.0, infiltration_n_factor=18.0,
                           interior_setpoint_f=_SETPOINT_F, window_u=0.25)
    envelope_only = estimate_block_load(model, base).heating_load_btu_per_hour
    total = estimate_block_load(model, with_air)
    assert total.heating_load_btu_per_hour == pytest.approx(
        envelope_only + total.infiltration_btu_per_hour)


# --- ventilation ----------------------------------------------------------------------

def _erv(**kwargs) -> tuple:
    equipment_type = EquipmentType(tag="EQ-T-ERV", name="ERV",
                                   footprint=(inch(24), inch(24)), height=inch(30),
                                   **kwargs)
    unit = Equipment(uid="EQ00000a01", tag="EQ-ERV", kind=EquipmentKind.ERV,
                     position=pt(ft(10), ft(7)), footprint=(inch(24), inch(24)),
                     type_ref="EQ-T-ERV")
    return (equipment_type,), (unit,)


def test_ventilation_is_airflow_net_of_sensible_recovery() -> None:
    types, units = _erv(ventilation_cfm=200.0, sensible_recovery_effectiveness=0.75)
    model = _resolved(_plan(types, units))
    report = estimate_block_load(
        model, Preferences(interior_setpoint_f=_SETPOINT_F, window_u=0.25))
    # 200 cfm at 75% recovery leaves 50 cfm to temper.
    assert report.ventilation_btu_per_hour == pytest.approx(_AIR * 50.0 * _HEATING_DELTA)


def test_perfect_recovery_leaves_no_ventilation_load() -> None:
    types, units = _erv(ventilation_cfm=200.0, sensible_recovery_effectiveness=1.0)
    model = _resolved(_plan(types, units))
    report = estimate_block_load(
        model, Preferences(interior_setpoint_f=_SETPOINT_F, window_u=0.25))
    assert report.ventilation_btu_per_hour == pytest.approx(0.0)


def test_erv_without_a_datasheet_is_unknown_not_zero() -> None:
    types, units = _erv(ventilation_cfm=200.0)  # no recovery effectiveness
    model = _resolved(_plan(types, units))
    report = estimate_block_load(
        model, Preferences(interior_setpoint_f=_SETPOINT_F, window_u=0.25))
    assert report.ventilation_btu_per_hour == 0.0
    assert any("sensible_recovery_effectiveness" in item
               for item in report.unknown_inputs)


def test_a_house_with_no_erv_moves_no_ventilation_air_and_says_nothing() -> None:
    """No ventilation equipment authored is a *fact read off the model*, not a gap: there is
    no mechanical ventilation load, and naming one would put an UNKNOWN on every house that
    ventilates by opening a window."""
    model = _resolved(_plan())
    report = estimate_block_load(
        model, Preferences(cfm50=1080.0, interior_setpoint_f=_SETPOINT_F, window_u=0.25))
    assert report.ventilation_btu_per_hour == 0.0
    assert not any("ventilation" in item for item in report.unknown_inputs)


# --- room scoping ---------------------------------------------------------------------

def test_room_scoping_of_the_only_room_reproduces_the_whole_house() -> None:
    """One room *is* the house, so scoping to it must not change the answer — the volume
    share is 1.0 and every envelope plane is wholly its own."""
    types, units = _erv(ventilation_cfm=200.0, sensible_recovery_effectiveness=0.75)
    model = _resolved(_plan(types, units))
    prefs = Preferences(cfm50=1080.0, infiltration_n_factor=18.0,
                       interior_setpoint_f=_SETPOINT_F, window_u=0.25)
    whole = estimate_block_load(model, prefs)
    scoped = estimate_block_load(model, prefs, rooms=frozenset({"RM-MAIN"}))
    assert scoped.infiltration_btu_per_hour == pytest.approx(
        whole.infiltration_btu_per_hour)
    assert scoped.ventilation_btu_per_hour == pytest.approx(
        whole.ventilation_btu_per_hour)
    assert scoped.heating_load_btu_per_hour == pytest.approx(
        whole.heating_load_btu_per_hour, rel=0.02)


def test_a_room_outside_the_model_scopes_to_nothing_rather_than_everything() -> None:
    model = _resolved(_plan())
    report = estimate_block_load(
        model, Preferences(cfm50=1080.0, interior_setpoint_f=_SETPOINT_F, window_u=0.25),
        rooms=frozenset({"RM-DOES-NOT-EXIST"}))
    assert report.heating_load_btu_per_hour == pytest.approx(0.0)
