"""The printed 2026 NEC as paraphrased in docs/nec-2026-paraphrase.md: numbering, 210, 705.

One test per graded rule. The load calculation (120.6, 120.82) is in test_nec_120_82.py.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from shapely.geometry import Point, box

from typehaus.checks import run_from_model
from typehaus.checks.registry import Tier
from typehaus.model import (
    Building,
    Circuit,
    DeviceKind,
    ElectricalDevice,
    ElectricalDeviceType,
    Library,
    PlanModel,
    Project,
    Service,
    ServicePort,
    Site,
    Storey,
    m,
    pt,
)
from typehaus.model.nec import NEC, UNCONFIRMED, cite, mark
from typehaus.resolve import resolve

# --- numbering, as printed ------------------------------------------------------------

_PRINTED = {
    "NONCOINCIDENT_UNLIKELY": "120.6(1)", "NONCOINCIDENT_LISTED": "120.6(2)",
    "OPTIONAL_APPLICABILITY": "120.82(A)", "OPTIONAL_SMALL_APPLIANCE": "120.82(B)(2)",
    "OPTIONAL_COOLING": "120.82(C)(1)", "OPTIONAL_HEAT_PUMP": "120.82(C)(2)",
    "OPTIONAL_HEAT_PUMP_SUPPLEMENTAL": "120.82(C)(3)", "OPTIONAL_RESISTANCE_FEW": "120.82(C)(4)",
    "OPTIONAL_RESISTANCE_MANY": "120.82(C)(5)", "OPTIONAL_EVSE": "120.82(D)",
    "MULTIWIRE_DISCONNECT": "210.7",
    "GFCI_BATHROOM": "210.8(A)(1)", "GFCI_GARAGE": "210.8(A)(2)",
    "GFCI_ACCESSORY_BUILDING": "210.8(A)(3)", "GFCI_OUTDOORS": "210.8(A)(4)",
    "GFCI_BASEMENT": "210.8(A)(6)", "GFCI_KITCHEN": "210.8(A)(7)", "GFCI_SINK": "210.8(A)(9)",
    "GFCI_TUB_SHOWER": "210.8(A)(11)", "GFCI_LAUNDRY": "210.8(A)(12)",
    "GFCI_SUMP": "210.8(D)(6)", "GFCI_DISHWASHER": "210.8(D)(7)", "GFCI_RANGE": "210.8(D)(8)",
    "GFCI_WALL_OVEN": "210.8(D)(9)", "GFCI_COOKTOP": "210.8(D)(10)",
    "GFCI_DRYER": "210.8(D)(11)", "GFCI_MICROWAVE": "210.8(D)(12)",
    "GFCI_OUTDOOR_OUTLETS": "210.8(F)", "BATHROOM_BRANCH": "210.11(C)(3)",
    "AFCI_DWELLING": "210.12(B)", "WALL_SPACE_FIXED_CABINETS": "210.52(A)(2)(1)",
    "FLOOR_RECEPTACLE": "210.52(A)(3)", "WALL_COUNTERTOP": "210.52(C)(1)",
    "ISLAND_PROVISION": "210.52(C)(2)", "COUNTERTOP_RECEPTACLE_LOCATION": "210.52(C)(3)",
    "BELOW_COUNTERTOP": "210.52(C)(4)", "BATHROOM_RECEPTACLE": "210.52(D)",
    "BALCONY_RECEPTACLE": "210.52(E)(3)", "LAUNDRY_RECEPTACLE": "210.52(F)",
    "GARAGE_RECEPTACLE": "210.52(G)(1)", "SERVICE_GROUNDING": "250.24",
    "GEC_SIZE": "250.66", "INTERSYSTEM_BONDING": "250.94", "WATER_PIPE_BOND": "250.104(A)",
    "LIGHTNING_BOND": "250.106", "FLOOR_BOX": "314.27(C)",
    "BURIAL_COVER": "300.7(A)", "EMERGING_FROM_GRADE": "300.7(D)(1)",
    "CORROSION_IN_EARTH": "300.8(A)(3)", "DAMAGE_ROOF_DECKING": "300.6(E)",
    "RACEWAY_CONDENSATION": "300.9(A)", "OTHER_PLENUMS": "300.25(C)",
    "INTERCONNECTION_100PCT": "705.12(B)(1)", "INTERCONNECTION_120PCT": "705.12(B)(2)(a)",
    "INTERCONNECTION_LABEL": "705.12(B)(2)(b)", "LIMITED_ENERGY_SEPARATION": "722.15(A)",
    "RAPID_SHUTDOWN_INITIATION": "690.12(C)", "PCS_CONTROL_SETTING": "120.7(B)",
    "EVSE_LOAD": "120.57", "SERVICE_SPD": "230.67", "SERVICE_DISCONNECT_OUTDOOR": "230.70(A)(1)",
    "OUTBUILDING_SUPPLIES": "225.30", "OUTBUILDING_DISCONNECT": "225.31",
    "EMERGENCY_DISCONNECT": "225.41", "SLEEVE_BONDING": "250.86 Ex. 2",
    "AMPACITY_TABLE": "Table 310.16", "EVSE_CIRCUIT": "625.40", "EVSE_CONTINUOUS": "625.41",
    "EVSE_DISCONNECT": "625.43(C)", "EVSE_RECEPTACLE_GFCI": "625.54",
    "STANDARD_OCPD": "240.6(A)", "WORKING_ILLUMINATION": "110.26(D)",
    "HVAC_LISTING": "440.2(A)", "HVAC_NAMEPLATE": "440.4(B)",
    "HVAC_BATH_ZONE": "440.8", "HVAC_DISCONNECT_ENCLOSURE": "440.11",
    "HVAC_DISCONNECT_RATING": "440.12(A)(1)", "HVAC_DISCONNECT": "440.14",
    "HVAC_MAX_OCPD": "440.22", "HVAC_CONDUCTORS": "440.32",
    "HVAC_COMBINATION_CONDUCTORS": "440.35",
    "SPACE_HEAT_CONTINUOUS": "424.5", "SPACE_HEAT_OUTLETS": "424.4(B)",
    "SPACE_HEAT_GFCI": "424.45(E)", "SPACE_HEAT_DISCONNECT": "424.19",
    "SPACE_HEAT_LABEL": "424.47", "SPACE_HEAT_WALLS": "424.48",
    "BRANCH_CONDUCTOR_LOAD": "210.19(A)(1)", "BRANCH_RANGE": "210.19(C)",
    "BRANCH_OCPD_LOAD": "210.20(A)", "SINGLE_RECEPTACLE": "210.21(B)(1)",
    "HVAC_RECEPTACLE": "210.63(A)", "BATH_LUMINAIRE_ZONE": "410.10(D)(1)",
    "BATH_LUMINAIRE_DAMP": "410.10(D)(2)", "PADDLE_FAN_BATH_ZONE": "422.18(B)",
    "STORAGE_WATER_HEATER": "422.13",
    "SWITCH_HEIGHT": "404.10(A)(2)", "SWITCH_BACKFEED_SIGN": "404.8(C)",
    "SWITCH_TUB_SHOWER": "404.6(C)",
    "BATH_ZONE": "406.9(C)(1)", "WET_RECEPTACLE": "406.9(B)(1)",
    "CONTROLLED_RECEPTACLE": "406.11(D)", "PUSH_IN_TERMINALS": "406.10(3)",
    "RECEPTACLE_REPLACEMENT": "406.12(D)", "CIRCUIT_DIRECTORY": "408.4(A)",
    "SWITCHBOARD_SCCR": "408.6",
    "ESS_LISTING": "706.2", "ESS_DISCONNECT": "706.15", "ESS_EMERGENCY_SHUTDOWN": "706.15(B)",
    "BATTERY_DISCONNECT": "480.7(A)", "BATTERY_EMERGENCY_DISCONNECT": "480.7(B)",
    "DWELLING_SERVICE_CONDUCTORS": "310.12(A)", "DWELLING_FEEDER_CONDUCTORS": "310.12(B)",
    "BOX_FILL": "314.16(B)", "CONDUCTOR_VOLUME_TABLE": "Table 314.16(B)(4)",
    "BOX_DEPTH": "314.24(B)", "BOX_FLUSH_SETBACK": "314.20", "BOX_COVER": "314.25",
    "PV_GROUNDING": "690.47(A)", "PV_EGC_SIZE": "690.45", "PV_ARC_FAULT": "690.11",
    "PV_DISCONNECT": "690.13", "PV_ISOLATING": "690.15", "RAPID_SHUTDOWN": "690.12",
    "RAPID_SHUTDOWN_OUTSIDE": "690.12(B)(1)", "RAPID_SHUTDOWN_ARRAY": "690.12(B)(2)",
    "RAPID_SHUTDOWN_DWELLING": "690.12(C)(1)(b)", "RAPID_SHUTDOWN_BUILDING_LABEL": "690.12(D)",
    "RAPID_SHUTDOWN_SWITCH_LABEL": "690.12(D)(2)", "INTERCONNECTION": "705.12",
    "INTERCONNECTION_FEEDER": "705.12(A)", "INTERCONNECTION_SUM": "705.12(B)(3)",
    "SOURCE_PLAQUE": "705.10", "SUPPLY_SIDE_OCPD": "705.11(C)(1)",
    "SOURCE_DISCONNECT": "705.20", "SOURCE_DISCONNECT_TYPE": "705.20(C)",
    "SOURCE_DISCONNECT_WARNING": "705.20(F)", "DC_POLARITY_MARKING": "705.25(B)",
    "STANDALONE_PLAQUE": "710.10", "PV_BATHROOM": "690.4(D)",
    "PV_MAX_VOLTAGE_DWELLING": "690.7(2)", "PV_VOLTAGE_COEFFICIENT": "690.7(A)(1)",
    "PV_VOLTAGE_TABLE": "Table 690.7(A)", "PV_VOLTAGE_LABEL": "690.7(D)",
    "PV_SOURCE_CURRENT": "690.8(A)(1)(a)", "PV_OCPD_RATING": "690.9(B)",
    "PV_OCPD_MARKING": "690.9(D)", "PV_ISOLATING_DEVICE": "690.15(B)",
    "PV_EQUIPMENT_DISCONNECT": "690.15(C)", "PV_DISCONNECT_LOCATION": "690.15(D)",
    "PV_DC_WIRING_BUILDING": "690.31(D)(1)", "PV_DC_MARKING": "690.31(D)(2)",
    "PV_CONNECTORS": "690.33(C)", "PV_GFDI": "690.41(B)", "SOURCE_OUTPUT_CURRENT": "705.28(A)",
    "SOURCE_CONDUCTOR": "705.28(B)", "SOURCE_OCPD": "705.30(B)",
    "SOURCE_BACKFEED_BREAKER": "705.30(D)", "SOURCE_HOLD_DOWN": "705.30(E)",
    "EGC_SIZE": "250.122", "EGC_TABLE": "Table 250.122", "EGC_UPSIZED": "250.122(D)",
    "EGC_ALUMINUM": "250.120(B)",
}


@pytest.mark.parametrize(("name", "section"), sorted(_PRINTED.items()))
def test_section_numbers_match_the_printed_code(name, section):
    assert getattr(NEC, name) == section


def test_every_cited_row_is_read_so_no_caveat_prints():
    assert frozenset() == UNCONFIRMED
    assert mark(NEC.GFCI_SINK) == "210.8(A)(9)" and cite(NEC.GEC_SIZE) == "NEC 250.66"


# --- 210.8(A): which locations, and which fixtures reach ------------------------------

def test_210_8_a_occupancies_and_210_12_b_rooms():
    from typehaus.checks.mep.electrical_code import _AFCI_OCCUPANCIES, _GFCI_OCCUPANCIES
    from typehaus.model.enums import Occupancy as O

    gfci = {k: v.split(" ")[0] for k, v in _GFCI_OCCUPANCIES.items()}
    assert gfci == {O.BATHROOM.value: NEC.GFCI_BATHROOM, O.GARAGE.value: NEC.GFCI_GARAGE,
                    O.KITCHEN.value: NEC.GFCI_KITCHEN, O.LAUNDRY.value: NEC.GFCI_LAUNDRY}
    listed = {O.KITCHEN, O.LIVING, O.DINING, O.BEDROOM, O.HALLWAY, O.LAUNDRY, O.MEDIA,
              O.STORAGE}  # STORAGE stands in for closets
    assert {o.value for o in listed} <= _AFCI_OCCUPANCIES
    assert not {O.BATHROOM.value, O.GARAGE.value} & _AFCI_OCCUPANCIES


@pytest.mark.parametrize(("symbol", "basin", "kind"), [
    ("lavatory", True, "sink"), ("kitchen-sink", False, "sink"),
    ("laundry-sink", False, "sink"), ("tub", False, "bathing"),
    ("shower-neo-angle", False, "bathing"), ("kohler-underscore-6032", False, "bathing"),
    ("toilet", False, None), ("floor-drain", False, None), (None, None, "sink"),
])
def test_210_8_a9_sinks_and_a11_tubs_but_not_toilets(symbol, basin, kind):
    from typehaus.checks.mep.electrical_code import _fixture_reach_kind

    assert _fixture_reach_kind(SimpleNamespace(plan_symbol=symbol, basin=basin)) == kind


def _reason(sinks, occupancy="office", below=False):
    from typehaus.checks.mep.electrical_code import _why_gfci_required

    room = SimpleNamespace(occupancy=occupancy, storey="main", tag="RM")
    return _why_gfci_required(None, None, room, Point(0, 0), sinks, {"main": below}, None)


def test_210_8_six_feet_from_the_bowl_or_the_tub_edge():
    near, far = box(1.7, 0, 2.2, 0.5), box(1.9, 0, 2.4, 0.5)  # 1.70 m vs 1.90 m from (0,0)
    assert NEC.GFCI_SINK in _reason([(near, "sink")])
    assert _reason([(far, "sink")]) is None
    assert NEC.GFCI_TUB_SHOWER in _reason([(near, "bathing")])
    assert _reason([], below=True).startswith(NEC.GFCI_BASEMENT)
    assert _reason([], occupancy="bathroom").startswith(NEC.GFCI_BATHROOM)


# --- 210.52 lead-in: what may count as a required receptacle --------------------------

def test_210_52_switched_or_high_receptacles_do_not_count():
    from typehaus.checks.mep.electrical import _counts_toward_210_52

    ctx = SimpleNamespace(plan=SimpleNamespace(library=SimpleNamespace(
        electrical_device_types=())))

    def device(inches, switched=()):
        return SimpleNamespace(kind=DeviceKind.RECEPTACLE, type_ref=None,
                               controlled_by=switched,
                               mount=SimpleNamespace(elevation=m(inches * 0.0254)))
    assert _counts_toward_210_52(ctx, device(66))
    assert not _counts_toward_210_52(ctx, device(67))
    assert _counts_toward_210_52(ctx, device(72), height_limit=False)  # (E)'s own 6 1/2 ft
    assert not _counts_toward_210_52(ctx, device(16, switched=("ED-SW",)))


def test_210_52_e3_reaches_decks_within_4_in_of_the_dwelling(catlin_model_ro):
    report = run_from_model(catlin_model_ro, [], tier=Tier.CODE,
                            only="code.NEC_210_52_E3_balcony_receptacles")
    graded = {f.message.split(" ")[0]: f for f in report.findings
              if f.check_id == "code.NEC_210_52_E3_balcony_receptacles"}
    # The court stands 5 in. off the house, but its decks reach within 4 in.
    assert {"FS-SG-PORCH", "FS-SG-BALCONY"} <= set(graded)
    assert all(f.result.value == "pass" for f in graded.values())


def test_230_70_a1_catlins_meter_main_is_outdoors(catlin_model_ro):
    report = run_from_model(catlin_model_ro, [], tier=Tier.ADVISORY,
                            only="electrical.service_disconnect_location")
    [finding] = [f for f in report.findings
                 if f.check_id == "electrical.service_disconnect_location"]
    assert finding.result.value == "pass" and "ED-M-METER" in finding.message


# --- 705.12(B) ------------------------------------------------------------------------

_PORT = ServicePort(tag="p", service=Service.POWER_240, position=(m(0), m(0), m(0)))


def _interconnection(main, bus, breaker, inverter_kw=None):
    from typehaus.model import Equipment, EquipmentKind, EquipmentType

    panel_type = ElectricalDeviceType(tag="ED-T-PNL", name="Panel", footprint=(m(.5), m(.1)),
                                      height=m(1), spaces=42, bus_amps=bus,
                                      service_amps=main, ports=(_PORT,))
    devices = [ElectricalDevice(tag="ED-M-PANEL", kind=DeviceKind.PANEL,
                                position=pt(m(0), m(0)), type_ref="ED-T-PNL")]
    eq_types = ()
    if inverter_kw:
        eq_types = (EquipmentType(tag="EQ-T-INV", name="inv", footprint=(m(.5), m(.2)),
                                  height=m(.7), inverter_kw_continuous=inverter_kw),)
        devices.append(Equipment(tag="EQ-INV", kind=EquipmentKind.INVERTER,
                                 position=pt(m(3), m(3)), footprint=(m(.5), m(.2)),
                                 type_ref="EQ-T-INV", circuit="CKT-PV"))
    circuits = (Circuit(tag="CKT-PV", panel_ref="ED-M-PANEL", breaker_amps=breaker, poles=2,
                        source=True, description="source"),)
    plan = PlanModel(
        project=Project(name="t", project_uuid="00000000-0000-0000-0000-000000000705",
                        building=Building(name="t"), site=Site(lat=0, lon=0, elevation=m(0))),
        storeys=(Storey(tag="main", elevation=m(0), default_ceiling_height=m(3)),),
        library=Library(circuits=circuits, electrical_device_types=(panel_type,),
                        equipment_types=eq_types),
        elements={"main": tuple(devices)})
    model, _ = resolve(plan)
    report = run_from_model(model, [], tier=Tier.CODE, only="code.NEC_705_12_interconnection")
    [finding] = [f for f in report.findings if f.check_id == "code.NEC_705_12_interconnection"]
    return finding


def test_705_12_b1_needs_no_placement():
    f = _interconnection(main=175, bus=225, breaker=40)
    assert f.result.value == "pass" and NEC.INTERCONNECTION_100PCT in f.message


def test_705_12_b2a_120_percent_with_opposite_end_and_label():
    f = _interconnection(main=200, bus=225, breaker=50)
    assert f.result.value == "pass" and NEC.INTERCONNECTION_120PCT in f.message
    assert "opposite end" in f.message and NEC.INTERCONNECTION_LABEL in f.message
    assert _interconnection(main=225, bus=225, breaker=60).result.value == "fail"


def test_705_12_uses_125_percent_of_inverter_output_not_the_breaker():
    f = _interconnection(main=200, bus=225, breaker=60, inverter_kw=8.0)  # 33.3 A out
    assert "41.25A source" in f.message and f.result.value == "pass"  # 33.3 A rounds to 33


# --- Table 310.16 / 310.12(A) (printed 2026-11-14) ---------------------------------------

# Table 310.12(A), service rating -> (copper, aluminum), read from the printed table.
_T310_12A = {100: ("4", "2"), 110: ("3", "1"), 125: ("2", "1/0"), 150: ("1", "2/0"),
             175: ("1/0", "3/0"), 200: ("2/0", "4/0"), 225: ("3/0", "250"),
             250: ("4/0", "300"), 300: ("250", "350"), 350: ("350", "500"),
             400: ("400", "600")}


def test_table_310_16_spot_values():
    from typehaus.model.ampacity import ampacity

    assert [ampacity("cu", s, 60) for s in ("14", "12", "10", "6")] == [15, 20, 30, 55]
    assert (ampacity("cu", "4/0", 75), ampacity("cu", "300", 75)) == (230, 285)
    assert (ampacity("al", "4/0", 75), ampacity("al", "400", 75)) == (180, 270)
    assert (ampacity("cu", "12", 90), ampacity("al", "600", 90)) == (30, 385)


@pytest.mark.parametrize(("rating", "conductors"), sorted(_T310_12A.items()))
def test_310_12a_is_the_83_percent_rule_over_table_310_16(rating, conductors):
    """Two printed tables agree: Table 310.12(A) is the smallest 75 degC conductor at 83%."""
    from typehaus.model.ampacity import dwelling_service_conductor

    assert (dwelling_service_conductor(rating, "cu"),
            dwelling_service_conductor(rating, "al")) == conductors


def test_catlins_320a_service_sits_between_rows():
    from typehaus.model.ampacity import dwelling_service_conductor

    assert dwelling_service_conductor(320, "cu") == "300"   # 285 A vs 265.6 A needed
    assert dwelling_service_conductor(320, "al") == "400"   # 270 A


def test_nm_ampacity_adjusts_from_90c_and_caps_at_60c():
    """334.80(A) with Table 310.15(C)(1): 12 AWG x 4 conductors is 30 x 0.8 = 24, capped at 20."""
    from typehaus.model.ampacity import adjustment_factor, nm_ampacity

    assert [adjustment_factor(n) for n in (3, 4, 7, 10, 21, 31, 41)] == [
        1.0, 0.8, 0.7, 0.5, 0.45, 0.4, 0.35]
    assert (nm_ampacity("12", 4), nm_ampacity("14", 4), nm_ampacity("12", 10)) == (20, 15, 15)


def test_nm_sleeves_still_cover_their_breakers(catlin_model_ro):
    report = run_from_model(catlin_model_ro, [], tier=Tier.ADVISORY,
                            only="electrical.nm_sleeve_ampacity")
    found = [f for f in report.findings if f.check_id == "electrical.nm_sleeve_ampacity"]
    assert len(found) == 12 and all(f.result.value == "pass" for f in found)
    assert any("80%" in f.message and "20 A" in f.message for f in found)


def test_feeder_behind_a_200a_main_is_240_4b_permitted():
    """4/0 Al is 180 A at 75 degC; Table 240.6(A) has no 180 A and 200 A next, under 800 A."""
    from typehaus.model.ampacity import STANDARD_OCPD_A, ampacity, next_standard_rating

    amps = ampacity("al", "4/0", 75)
    assert amps == 180 and amps not in STANDARD_OCPD_A
    assert next_standard_rating(amps) == 200 <= 800
    assert STANDARD_OCPD_A[0] == 10 and STANDARD_OCPD_A[-1] == 6000


def test_catlins_ev_circuit_is_individual_and_at_125_percent(catlin_model_ro):
    report = run_from_model(catlin_model_ro, [], tier=Tier.ADVISORY,
                            only="electrical.evse_circuit")
    found = [f for f in report.findings if f.check_id == "electrical.evse_circuit"
             and "CKT-EV-1450" in f.message]
    by = {f.result.value for f in found}
    assert "fail" not in by and "pass" in by
    assert any("50.0 A against a 50 A breaker" in f.message for f in found)
    assert any(f.result.value == "not_applicable" for f in found)   # 625.54: hardwired


def test_catlins_heat_pump_disconnects_are_in_plan_sight(catlin_model_ro):
    report = run_from_model(catlin_model_ro, [], tier=Tier.ADVISORY,
                            only="electrical.hvac_disconnect")
    found = [f for f in report.findings if f.check_id == "electrical.hvac_disconnect"]
    by = {f.element_tags[0]: f.result.value for f in found}
    assert by == {"EQ-M-HP1-OD": "pass", "EQ-M-HP2-OD": "pass", "EQ-M-HP3-OD": "pass",
                  "EQ-S-HP1-AH": "unknown"}


def test_catlins_space_heat_circuits_carry_125_percent_and_gfci(catlin_model_ro):
    report = run_from_model(catlin_model_ro, [], tier=Tier.ADVISORY,
                            only="electrical.space_heat_circuit")
    found = [f for f in report.findings if f.check_id == "electrical.space_heat_circuit"]
    assert len(found) == 8 and all(f.result.value == "pass" for f in found)
    assert sum("GFCI" in f.message for f in found) == 2   # both floor-heat cables


def test_bath_zone_reports_the_bask_outlet_and_never_fails(catlin_model_ro):
    report = run_from_model(catlin_model_ro, [], tier=Tier.ADVISORY,
                            only="electrical.bath_receptacle_zone")
    found = [f for f in report.findings if f.check_id == "electrical.bath_receptacle_zone"]
    assert found and all(f.result.value == "unknown" for f in found)
    assert any("ED-M-BATH2-TUB-RC" in f.message for f in found)


def test_no_heat_pump_unit_is_in_a_bath_zone(catlin_model_ro):
    report = run_from_model(catlin_model_ro, [], tier=Tier.ADVISORY,
                            only="electrical.bath_hvac_zone")
    found = [f for f in report.findings if f.check_id == "electrical.bath_hvac_zone"]
    assert [f.result.value for f in found] == ["pass"]


# --- 210.19-210.21, 210.63, 410.10(D), 422.13, 422.18(B) (docs/nec-2026-paraphrase-210-422-410.md)

def test_210_20_a_125_percent_constants_and_the_range_floor():
    from typehaus.checks.mep import electrical_circuit_sizing as sizing
    from typehaus.checks.mep.electrical_hvac_receptacle import HVAC_RECEPTACLE_REACH_M

    assert sizing.CONTINUOUS_FACTOR == 1.25
    assert (sizing.RANGE_MIN_VA, sizing.RANGE_MIN_AMPS) == (8750.0, 40)   # 210.19(C)
    assert sizing.STORAGE_HEATER_CONTINUOUS_MAX_GAL == 120.0   # 422.13: 450 L
    assert abs(HVAC_RECEPTACLE_REACH_M - 7.62) < 1e-9   # 210.63: 25 ft = 7.5 m printed
    assert [sizing._receptacle_amps(n) for n in ("5-15R", "14-30R", "L5-30R", None)] \
        == [15, 30, 30, None]


def test_catlins_storage_water_heater_is_a_continuous_load(catlin_model_ro):
    report = run_from_model(catlin_model_ro, [], tier=Tier.ADVISORY,
                            only="electrical.continuous_load_circuit")
    found = [f for f in report.findings if f.check_id == "electrical.continuous_load_circuit"]
    assert not any(f.result.value == "fail" for f in found)
    assert any("422.13" in f.message and "15.0 A against a 15 A" in f.message for f in found)
    unknown = {t for f in found if f.result.value == "unknown" for t in f.element_tags}
    assert {"CKT-SPA", "CKT-WORKSHOP-240"} <= unknown   # continuity is not stated


def test_catlins_single_receptacles_meet_their_circuits(catlin_model_ro):
    report = run_from_model(catlin_model_ro, [], tier=Tier.ADVISORY,
                            only="electrical.single_receptacle_rating")
    found = [f for f in report.findings if f.check_id == "electrical.single_receptacle_rating"]
    assert found and {f.result.value for f in found} == {"pass"}


def test_catlins_hvac_units_each_have_a_servicing_receptacle(catlin_model_ro):
    report = run_from_model(catlin_model_ro, [], tier=Tier.ADVISORY,
                            only="electrical.hvac_service_receptacle")
    found = [f for f in report.findings if f.check_id == "electrical.hvac_service_receptacle"]
    assert len(found) == 11 and {f.result.value for f in found} == {"pass"}  # 8 HVAC, 3 fridges
    assert all("outdoors" in f.message for f in found if f.element_tags[0].endswith("-OD"))


def test_catlins_laundry_track_is_behind_a_wall_from_the_hall_bath_tub(catlin_model_ro):
    report = run_from_model(catlin_model_ro, [], tier=Tier.ADVISORY,
                            only="electrical.bath_luminaire_zone")
    found = [f for f in report.findings if f.check_id == "electrical.bath_luminaire_zone"]
    assert [(f.result.value, f.element_tags) for f in found] == [
        ("pass", ("ED-M-LAUNDRY-TRACK", "FX-M-BATH2-TUB"))]   # another room: out of the zone


# --- Article 300 (renumbered in 2026; docs/nec-2026-paraphrase-300.md) -------------------------


def test_article_300_numbers_and_table_300_7_a_cells():
    from typehaus.model import burial
    from typehaus.model.burial import (
        TABLE_300_7_A,
        circuit_columns,
        cover_in,
        min_cover_in,
        shallowest_in,
    )
    from typehaus.model.nec import NEC

    assert (NEC.PHYSICAL_DAMAGE, NEC.UNDERGROUND, NEC.FIRESTOPPING, NEC.RACEWAY_BENDS) == (
        "300.6", "300.7", "300.23", "300.24")
    C, L = burial.BurialColumn, burial.BurialLocation
    assert NEC.BURIAL_TABLE == "Table 300.7(A)" and NEC.RACEWAY_SEALS == "300.7(G)"
    assert [min_cover_in(L.ALL_OTHER, c) for c in C] == [24, 6, 18, 12, 6]
    assert [min_cover_in(L.TRENCH_UNDER_CONCRETE, c) for c in C] == [18, 6, 12, 6, 6]
    assert [min_cover_in(L.UNDER_BUILDING, c) for c in C] == [0] * 5
    assert [min_cover_in(L.UNDER_SLAB, c, in_raceway=False) for c in C] == [18, 4, 4, 6, 6]
    assert [min_cover_in(L.UNDER_SLAB, c) for c in C] == [18, 4, 4, 4, 4]
    assert [min_cover_in(L.UNDER_ROAD, c) for c in C] == [24] * 5
    assert [min_cover_in(L.DWELLING_DRIVEWAY, c) for c in C] == [18, 18, 18, 12, 18]
    assert [min_cover_in(L.AIRPORT, c) for c in C] == [18] * 5
    assert len(TABLE_300_7_A) == 7 and all(len(row) == 5 for row in TABLE_300_7_A.values())
    # Note 4: a 120 V, 20 A GFCI circuit in EMT takes Column 4's 12 in.; 240 V stays at 18.
    gfci = circuit_columns("emt", volts=120, amps=20, gfci=True)
    assert shallowest_in(L.ALL_OTHER, gfci) == (12, C.RESIDENTIAL_GFCI)
    assert shallowest_in(L.ALL_OTHER, circuit_columns("emt", volts=240, amps=50, gfci=True)) \
        == (18, C.RACEWAY)
    # Note 1: from the top of the run to the top of the cover.
    assert cover_in(-1.2, -0.85) == pytest.approx(0.35 / 0.0254)


def test_catlins_buried_ev_and_v2h_legs_miss_18_in_under_the_walk(catlin_model_ro):
    report = run_from_model(catlin_model_ro, [], tier=Tier.ADVISORY, only="mep.conduit_burial")
    found = {f.element_tags[0]: f for f in report.findings
             if f.check_id == "mep.conduit_burial" and f.element_tags}
    for tag, cover in (("CD-B-GAP-EV", "14.2"), ("CD-B-V2H-GAP", "13.8")):
        assert found[tag].result.value == "advisory" and f"cover {cover} in." in found[tag].message
        assert "Column 3" in found[tag].message and "6 in. the slab row needs" in found[tag].message
    assert found["CD-B-SPA"].result.value == "unknown"


# --- Table 250.122 and Table 690.7(A), as printed 2026-11-14 ---------------------------

def test_table_250_122_cells():
    from typehaus.model.ampacity import egc_minimum, size_at_least

    assert [egc_minimum(a, "cu") for a in (15, 20, 25, 60, 61, 200, 400, 6000)] == [
        "14", "12", "10", "10", "8", "6", "3", "800"]
    assert [egc_minimum(a, "al") for a in (15, 25, 100, 600, 3000)] == [
        "12", "8", "6", "2/0", "600"]
    assert size_at_least("1/0", "8") and not size_at_least("12", "10")


def test_table_690_7_a_cells_and_the_catlin_cross_check():
    from typehaus.model.pv_voltage import max_source_voltage, voc_factor

    assert [voc_factor(t) for t in (24, 20, 19, 0, -1, -26, -30, -31, -40)] == [
        1.02, 1.02, 1.04, 1.10, 1.12, 1.21, 1.21, 1.23, 1.25]
    # Nine 37.67 V modules at -30 degC: 410.2 V by the table, 383.8 V by the coefficient.
    assert round(max_source_voltage(37.67, 9, -30), 1) == 410.2
