"""The wet/humid-room rules — the shared concept, exercised on synthetic rooms.

Four checks and one enum, all keyed on ``Room.humidity_class`` rather than on an occupancy
or a tag, which is the point of the axis: a house with no wet room sees no findings, and a
plant room, a sauna and a shower reach the same rules by different routes.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from typehaus.checks.building_science.glaser import dew_point_f
from typehaus.checks.building_science.humid_room import (
    glazing_dew_point,
    humid_room_finish,
    humid_room_liner,
    humid_room_pressure,
)
from typehaus.findings import Result
from typehaus.model.assembly import Assembly, Layer
from typehaus.model.materials import Material
from typehaus.model.enums import (
    ControlLayer,
    DuctSystem,
    HumidityClass,
    LayerFunction,
    Occupancy,
)
from typehaus.model.mep import Register
from typehaus.model.spatial import Room
from typehaus.model.types import WindowType
from typehaus.quantities import ft, inch, pt, u_us
from typehaus.resolve.model import ResolvedOpening, ResolvedRoom


CLASS_I = Material(tag="membrane", name="Class I membrane", r_per_inch=0.0,
                   vapor_permeance_perms=0.05)
CLASS_III = Material(tag="paint", name="Latex paint", r_per_inch=0.0,
                     vapor_permeance_perms=5.0)
GWB = Material(tag="gwb", name='5/8" gypsum board', r_per_inch=0.9, perm_rating=18.8,
               gypsum_type="regular")
PVC = Material(tag="pvc-panel", name="PVC panel", r_per_inch=1.0)
SPF = Material(tag="spf", name="SPF", r_per_inch=1.24, perm_rating=2.9)


def _layer(name, material, function, control=frozenset(), thickness=inch(0.5)):
    return Layer(name=name, material_ref=material, thickness=thickness,
                 function=function, control=set(control))


def _assembly(tag, layers):
    return Assembly(tag=tag, layers=tuple(layers))


_LINED = _assembly("HUMID", [
    _layer("pvc-panel", "pvc-panel", LayerFunction.FINISH),
    _layer("humid-membrane", "membrane", LayerFunction.MEMBRANE,
           {ControlLayer.VAPOR, ControlLayer.AIR}, inch(0.04)),
    _layer("stud", "spf", LayerFunction.STRUCTURE, thickness=inch(5.5)),
])
_UNLINED = _assembly("PLAIN", [
    _layer("paint", "paint", LayerFunction.FINISH, {ControlLayer.VAPOR}, inch(0.01)),
    _layer("gwb-int", "gwb", LayerFunction.FINISH, thickness=inch(0.625)),
    _layer("stud", "spf", LayerFunction.STRUCTURE, thickness=inch(5.5)),
])
# Air-tight and vapour-tight are not the same claim: a layer that says only VAPOR is not a
# control layer for a room whose moisture moves by air transport.
_VAPOR_ONLY = _assembly("VAPOR_ONLY", [
    _layer("humid-membrane", "membrane", LayerFunction.MEMBRANE, {ControlLayer.VAPOR},
           inch(0.04)),
    _layer("stud", "spf", LayerFunction.STRUCTURE, thickness=inch(5.5)),
])
# Declared as the control layer but only Class III — the failure that a "we sealed it" claim
# hides, and the reason the check reads the permeance instead of trusting `control`.
_TOO_OPEN = _assembly("TOO_OPEN", [
    _layer("humid-membrane", "paint", LayerFunction.MEMBRANE,
           {ControlLayer.VAPOR, ControlLayer.AIR}, inch(0.04)),
    _layer("stud", "spf", LayerFunction.STRUCTURE, thickness=inch(5.5)),
])
_ASSEMBLIES = {a.tag: a for a in (_LINED, _UNLINED, _VAPOR_ONLY, _TOO_OPEN)}
_MATERIALS = {m.tag: m for m in (CLASS_I, CLASS_III, GWB, PVC, SPF)}


def _wall(tag, assembly, axis=((0.0, 0.0), (4.0, 0.0))):
    return SimpleNamespace(tag=tag, storey="main", assembly=assembly, axis=axis,
                           thickness_m=0.15, element_kind="Wall", interior_room="RM-X")


def _ctx(*, assembly="HUMID", humidity=HumidityClass.HUMID, registers=(),
         windows=(), openings=(), design_rh=None, design_temp=None,
         design_temp_heating=-15.0):
    room = Room(uid="R000000001", tag="RM-X", seed=pt(ft(1), ft(1)),
                occupancy=Occupancy.LIVING, humidity_class=humidity,
                design_relative_humidity=design_rh, design_temperature_f=design_temp)
    wall = _wall("W-X", assembly)
    elements = [room, wall, *registers]
    library = SimpleNamespace(
        resolve_assembly=_ASSEMBLIES.get,
        material=_MATERIALS.get,
        window_types=list(windows),
    )
    site = SimpleNamespace(
        design_temp_heating=(None if design_temp_heating is None
                             else SimpleNamespace(fahrenheit=design_temp_heating)))
    plan = SimpleNamespace(
        storeys=[SimpleNamespace(tag="main")],
        storey_elements=lambda tag: elements if tag == "main" else [],
        all_elements=lambda: iter(elements),
        library=library,
        project=SimpleNamespace(site=site),
    )
    resolved_room = ResolvedRoom(
        uid="R000000001", tag="RM-X", storey="main", occupancy="living",
        conditioned=True, clear_face=[(0.0, 0.0), (4.0, 0.0), (4.0, 4.0), (0.0, 4.0)],
        area_m2=16.0, floor_finish=None)
    model = SimpleNamespace(walls=[wall], rooms=[resolved_room], ceilings=[],
                            openings=list(openings), plan=plan)
    return SimpleNamespace(
        plan=plan, model=model,
        preferences=SimpleNamespace(interior_setpoint_f=70.0,
                                    interior_relative_humidity=0.35,
                                    monthly_interior_relative_humidity=0.35,
                                    exterior_relative_humidity=0.80),
    )


# --- the axis itself ----------------------------------------------------------------

def test_a_normal_room_fires_none_of_these_rules():
    """The whole point of a separate axis: an ordinary house sees nothing at all."""
    ctx = _ctx(assembly="PLAIN", humidity=HumidityClass.NORMAL)
    assert humid_room_liner(ctx) == []
    assert humid_room_finish(ctx) == []
    assert humid_room_pressure(ctx) == []
    assert glazing_dew_point(ctx) == []


def test_the_class_supplies_a_design_rh_and_an_override_beats_it():
    normal = Room(uid="R000000002", tag="RM-N", seed=pt(ft(1), ft(1)),
                  occupancy=Occupancy.LIVING)
    wet = normal.model_copy(update={"humidity_class": HumidityClass.WET})
    humid = normal.model_copy(update={"humidity_class": HumidityClass.HUMID})
    override = humid.model_copy(update={"design_relative_humidity": 0.60})
    assert normal.interior_design_relative_humidity is None
    assert wet.interior_design_relative_humidity == pytest.approx(0.55)
    assert humid.interior_design_relative_humidity == pytest.approx(0.70)
    assert override.interior_design_relative_humidity == pytest.approx(0.60)


# --- building_science.humid_room_liner ------------------------------------------------

def test_a_class_i_air_and_vapour_layer_inboard_of_the_core_passes():
    findings = humid_room_liner(_ctx(assembly="HUMID"))
    assert [f.result for f in findings] == [Result.PASS]
    assert "Class I at 0.050 perm" in findings[0].message


def test_no_control_layer_at_all_fails():
    findings = humid_room_liner(_ctx(assembly="PLAIN"))
    assert [f.result for f in findings] == [Result.FAIL]
    assert "no room-side air+vapour control layer" in findings[0].message


def test_vapour_control_without_air_control_is_not_a_control_layer():
    """Air transport moves one to two orders of magnitude more moisture than diffusion, so
    a vapour-tight layer with air leaking past it controls nothing."""
    findings = humid_room_liner(_ctx(assembly="VAPOR_ONLY"))
    assert [f.result for f in findings] == [Result.FAIL]


def test_a_declared_control_layer_that_is_only_class_iii_fails_on_its_permeance():
    findings = humid_room_liner(_ctx(assembly="TOO_OPEN"))
    assert [f.result for f in findings] == [Result.FAIL]
    assert "Class I" in findings[0].message


# --- building_science.humid_room_finish -----------------------------------------------

def test_paper_faced_gypsum_on_the_room_face_fails():
    findings = humid_room_finish(_ctx(assembly="PLAIN"))
    assert [f.result for f in findings] == [Result.FAIL]
    assert "gwb" in findings[0].message


def test_a_non_cellulose_room_face_passes():
    findings = humid_room_finish(_ctx(assembly="HUMID"))
    assert [f.result for f in findings] == [Result.PASS]


# --- building_science.glazing_dew_point -----------------------------------------------

def _window(tag, u_factor):
    return WindowType(tag=tag, width=inch(30), height=ft(4), u_factor=u_us(u_factor))


def _opening(tag, type_ref):
    return ResolvedOpening(uid=f"O{tag}", tag=tag, host_wall="W-X", type_ref=type_ref,
                           width_m=0.762, height_m=1.219, sill_m=0.8,
                           center_along_m=2.0, kind="window", is_door=False)


def test_the_dew_point_of_the_room_is_what_the_glass_is_graded_against():
    """75 F / 70% RH is 64.4 F, and the room states both numbers because dew point needs
    both — a room held warmer *and* wetter than the house cannot state only one."""
    assert dew_point_f(75.0, 0.70) == pytest.approx(64.55, abs=0.1)
    assert dew_point_f(70.0, 0.35) == pytest.approx(41.09, abs=0.1)


def test_a_u_025_unit_condenses_and_a_u_014_twin_does_not():
    ordinary = _window("WT-3048", 0.25)
    high_performance = _window("WT-3048-HP", 0.14)
    ctx = _ctx(design_temp=75.0, windows=(ordinary, high_performance),
               openings=(_opening("WIN-A", "WT-3048"), _opening("WIN-B", "WT-3048-HP")))
    by_tag = {f.element_tags[0]: f for f in glazing_dew_point(ctx)}
    assert by_tag["WIN-A"].result is Result.FAIL
    assert "condenses" in by_tag["WIN-A"].message
    assert by_tag["WIN-B"].result is Result.PASS
    # Centre of glass is the optimistic plane, and the finding has to say so — the frame
    # and the edge run 5-8 F colder and no U-factor knows that.
    assert "frame and edge run" in by_tag["WIN-B"].message


def test_a_missing_u_factor_or_design_temperature_is_unknown_not_a_pass():
    no_u = WindowType(tag="WT-NONE", width=inch(30), height=ft(4))
    ctx = _ctx(design_temp=75.0, windows=(no_u,), openings=(_opening("WIN-C", "WT-NONE"),))
    assert [f.result for f in glazing_dew_point(ctx)] == [Result.UNKNOWN]

    ctx = _ctx(design_temp=75.0, design_temp_heating=None,
               windows=(_window("WT-3048", 0.25),),
               openings=(_opening("WIN-D", "WT-3048"),))
    assert [f.result for f in glazing_dew_point(ctx)] == [Result.UNKNOWN]


# --- mep.humid_room_pressure ------------------------------------------------------------

def _register(tag, kind):
    return Register(uid=f"T{abs(hash(tag)) % 10**9:09d}", tag=tag, kind=kind,
                    position=pt(ft(1), ft(1)), room="RM-X")


def test_supply_with_no_matched_extract_fails():
    ctx = _ctx(registers=(_register("REG-SUP", DuctSystem.SUPPLY),))
    findings = humid_room_pressure(ctx)
    assert [f.result for f in findings] == [Result.FAIL]
    assert "pressurises" in findings[0].message


def test_supply_plus_extract_passes():
    ctx = _ctx(registers=(_register("REG-SUP", DuctSystem.SUPPLY),
                          _register("REG-EXH", DuctSystem.EXHAUST)))
    assert [f.result for f in humid_room_pressure(ctx)] == [Result.PASS]


def test_extract_only_passes_because_it_cannot_pressurise_itself():
    ctx = _ctx(registers=(_register("REG-EXH", DuctSystem.EXHAUST),))
    assert [f.result for f in humid_room_pressure(ctx)] == [Result.PASS]


def test_no_terminal_at_all_is_unknown():
    assert [f.result for f in humid_room_pressure(_ctx())] == [Result.UNKNOWN]


def test_an_intermittently_wet_room_is_not_graded_on_pressure():
    """A sauna is turned over between sessions and is not held at a pressure at all."""
    ctx = _ctx(humidity=HumidityClass.WET,
               registers=(_register("REG-SUP", DuctSystem.SUPPLY),))
    assert humid_room_pressure(ctx) == []
