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
    "INTERCONNECTION_100PCT": "705.12(B)(1)", "INTERCONNECTION_120PCT": "705.12(B)(2)(a)",
    "INTERCONNECTION_LABEL": "705.12(B)(2)(b)", "LIMITED_ENERGY_SEPARATION": "722.15(A)",
    "RAPID_SHUTDOWN_INITIATION": "690.12(C)", "PCS_CONTROL_SETTING": "120.7(B)",
    "EVSE_LOAD": "120.57", "SERVICE_SPD": "230.67", "SERVICE_DISCONNECT_OUTDOOR": "230.70(A)(1)",
    "OUTBUILDING_SUPPLIES": "225.30", "OUTBUILDING_DISCONNECT": "225.31",
    "EMERGENCY_DISCONNECT": "225.41", "SLEEVE_BONDING": "250.86 Ex. 2",
    "AMPACITY_TABLE": "Table 310.16",
    "DWELLING_SERVICE_CONDUCTORS": "310.12(A)", "DWELLING_FEEDER_CONDUCTORS": "310.12(B)",
    "BOX_FILL": "314.16(B)", "CONDUCTOR_VOLUME_TABLE": "Table 314.16(B)(4)",
    "BOX_DEPTH": "314.24(B)", "BOX_FLUSH_SETBACK": "314.20", "BOX_COVER": "314.25",
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
    assert "41.7A source" in f.message and f.result.value == "pass"


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
