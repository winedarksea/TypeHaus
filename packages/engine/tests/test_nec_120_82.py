"""2026 NEC 120.6 and 120.82 as the engine paraphrases them (read in the printed code
2026-11-13). The code text is not reproduced; each test pins one rule's arithmetic.

Synthetic plans carry no rooms or envelope, so (B)(1)'s VA/ft2 term is zero and every
number below is the rule under test alone.
"""

from __future__ import annotations

import pytest

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
    Site,
    Storey,
    m,
    pt,
)
from typehaus.model.nec import NEC
from typehaus.resolve import resolve
from typehaus.takeoff.service_load import general_demand_va, hvac_selection, service_load_summary

_PANEL = ElectricalDevice(tag="ED-M-PANEL", kind=DeviceKind.PANEL, position=pt(m(0), m(0)))


def _model(circuits=(), devices=(), library=None, types=()):
    library = library or Library(circuits=tuple(circuits), electrical_device_types=tuple(types))
    plan = PlanModel(
        project=Project(name="t", project_uuid="00000000-0000-0000-0000-000000000082",
                        building=Building(name="t"), site=Site(lat=0, lon=0, elevation=m(0))),
        storeys=(Storey(tag="main", elevation=m(0), default_ceiling_height=m(3)),),
        library=library, elements={"main": (_PANEL, *devices)})
    model, findings = resolve(plan)
    assert not [f for f in findings if f.severity.value == "error"]
    return model


def _ckt(tag, va, description, poles=2):
    return Circuit(tag=tag, panel_ref="ED-M-PANEL", breaker_amps=20, poles=poles,
                   load_va=va, description=description)


# --- (B): general loads --------------------------------------------------------------

@pytest.mark.parametrize(("general", "demand"), [(5000, 5000), (8000, 8000),
                                                 (20000, 8000 + 0.4 * 12000)])
def test_b_first_8kva_at_100_then_40_percent(general, demand):
    assert general_demand_va(general) == pytest.approx(demand)


def test_b2_counts_each_small_appliance_and_laundry_circuit_at_1500():
    circuits = [_ckt(f"CKT-SA{i}", 1500, f"Kitchen small-appliance {i}", poles=1)
                for i in range(3)] + [_ckt("CKT-LAU", 1500, "Laundry receptacle", poles=1)]
    s = service_load_summary(_model(circuits))
    assert (s["small_appliance_circuits"], s["laundry_circuits"]) == (3, 1)
    assert s["general_lighting_va"] == 4 * 1500


def test_b2_never_counts_fewer_than_the_210_11c_minimums_for_the_dwelling():
    s = service_load_summary(_model([_ckt("CKT-X", 0, "Spare")]))
    assert s["general_lighting_va"] == (2 + 1) * 1500


# --- (C): the largest of the selections ----------------------------------------------

@pytest.mark.parametrize(("units", "factor", "item"), [(3, 0.65, NEC.OPTIONAL_RESISTANCE_FEW),
                                                       (4, 0.40, NEC.OPTIONAL_RESISTANCE_MANY)])
def test_c4_c5_space_heating_by_separately_controlled_units(units, factor, item):
    circuits = [_ckt(f"CKT-FH{i}", 1000, "Radiant floor heat") for i in range(units)]
    s = service_load_summary(_model(circuits))
    assert s["hvac_va"] == pytest.approx(units * 1000 * factor)
    assert s["hvac_selection"] == item


def test_c_selects_rather_than_sums():
    # Heat pump 6,000 with a 4,000 kit vs 10 kW of resistance heat in four units.
    va, item = hvac_selection(cooling_va=2000, heat_pump_va=2000 + 0.65 * 4000,
                              supplemental=True, resistance_va=10000, resistance_units=4)
    assert (va, item) == (pytest.approx(4600), NEC.OPTIONAL_HEAT_PUMP_SUPPLEMENTAL)
    va, item = hvac_selection(cooling_va=3000, heat_pump_va=3000, supplemental=False,
                              resistance_va=0, resistance_units=0)
    assert (va, item) == (3000, NEC.OPTIONAL_HEAT_PUMP)


def _heat_pump_model(lockout: bool):
    from typehaus.model import Equipment, EquipmentKind, EquipmentType

    kit = EquipmentType(tag="EQ-T-KIT", name="kit", footprint=(m(.4), m(.3)), height=m(.3),
                        resistance_heating_btuh=4000 * 3.412)
    def unit(tag, kind, x, circuit, **kw):
        return Equipment(tag=tag, kind=kind, position=pt(m(x), m(3)),
                         footprint=(m(.5), m(.5)), circuit=circuit, **kw)
    devices = (
        unit("EQ-OD", EquipmentKind.HEAT_PUMP, 2, "CKT-OD"),
        unit("EQ-AH", EquipmentKind.DUCTED_AIR_HANDLER, 4, "CKT-AH", outdoor_ref="EQ-OD"),
        unit("EQ-KIT", EquipmentKind.SPACE_HEATER, 6, "CKT-AH", type_ref="EQ-T-KIT",
             blower_interlock_ref="EQ-AH",
             compressor_lockout_ref="EQ-OD" if lockout else None),
    )
    circuits = (_ckt("CKT-OD", 5000, "Heat pump outdoor"),
                _ckt("CKT-AH", 4700, "Air handler + 4 kW kit"))
    return _model(devices=devices,
                  library=Library(circuits=circuits, equipment_types=(kit,)))


def test_c3_compressor_plus_65_percent_of_the_kit():
    s = service_load_summary(_heat_pump_model(lockout=False))
    assert s["heat_pump_va"] == 5000 + 700 + 0.65 * 4000
    assert s["cooling_va"] == 5700
    assert (s["hvac_va"], s["hvac_selection"]) == (8300, NEC.OPTIONAL_HEAT_PUMP_SUPPLEMENTAL)


def test_c3_a_locked_out_compressor_leaves_heating_but_still_cools():
    s = service_load_summary(_heat_pump_model(lockout=True))
    assert s["heat_pump_va"] == 700 + 0.65 * 4000
    assert (s["hvac_va"], s["hvac_selection"]) == (5700, NEC.OPTIONAL_COOLING)


# --- (D), (A) ------------------------------------------------------------------------

def test_d_evse_at_100_percent_outside_the_40_percent_remainder():
    s = service_load_summary(_model([_ckt("CKT-EV", 9600, "EV charging")]))
    assert s["ev_va"] == 9600
    assert s["demand_va"] == 4500 + 9600


def test_120_57_evse_without_a_nameplate_counts_7200():
    s = service_load_summary(_model([Circuit(tag="CKT-EV", panel_ref="ED-M-PANEL", poles=2,
                                             breaker_amps=40, description="EV charging")]))
    assert s["ev_va"] == 7200 and s["ev_default_circuits"] == ["CKT-EV"]
    # An authored nameplate below 7,200 is kept: the printed rule is no "larger of".
    s = service_load_summary(_model([_ckt("CKT-EV", 3800, "EV charging")]))
    assert s["ev_va"] == 3800 and not s["ev_default_circuits"]


def test_a_optional_method_needs_100_amp_service_conductors():
    meter_type = ElectricalDeviceType(tag="ED-T-MTR", name="meter", footprint=(m(.3), m(.1)),
                                      height=m(.4), service_amps=60, ports=())
    meter = ElectricalDevice(tag="ED-M-MTR", kind=DeviceKind.METER, position=pt(m(1), m(0)),
                             type_ref="ED-T-MTR")
    model = _model([_ckt("CKT-X", 1000, "Kiln")], devices=(meter,), types=(meter_type,))
    assert service_load_summary(model)["optional_method_applies"] is False
    report = run_from_model(model, [], tier=Tier.ADVISORY, only="electrical.service_load")
    [finding] = [f for f in report.findings if f.check_id == "electrical.service_load"]
    assert finding.result.value == "unknown" and "120.82(A)" in finding.message


# --- 120.6 ---------------------------------------------------------------------------

def _noncoincident(cap, listing=""):
    from typehaus.model import LoadManagement

    circuits = (_ckt("CKT-A", 3000, "Kiln"), _ckt("CKT-B", 5000, "Welder"))
    lm = LoadManagement(tag="LM-NC", managed_circuits=("CKT-A", "CKT-B"),
                        max_simultaneous_va=cap, strategy="noncoincident",
                        source="" if listing else "never run together", listing=listing)
    return _model(library=Library(circuits=circuits, load_managements=(lm,)))


def test_120_6_counts_the_group_at_its_single_largest_load():
    [credit] = service_load_summary(_noncoincident(cap=1000))["load_management"]
    assert credit["cap_va"] == 5000 and credit["excess_va"] == 3000
    # An authored ceiling above the largest is kept.
    [credit] = service_load_summary(_noncoincident(cap=6000))["load_management"]
    assert credit["excess_va"] == 2000


def test_120_6_item_by_basis():
    for listing, item in (("", NEC.NONCOINCIDENT_UNLIKELY),
                          ("UL 916 (synthetic)", NEC.NONCOINCIDENT_LISTED)):
        report = run_from_model(_noncoincident(cap=1000, listing=listing), [],
                                tier=Tier.ADVISORY, only="electrical.service_load")
        assert any(item in f.message for f in report.findings), [
            f.message for f in report.findings]


def test_120_7b_pcs_setting_over_80_percent_of_the_monitored_ocpd_earns_nothing():
    from typehaus.model import LoadManagement

    circuits = (_ckt("CKT-A", 9000, "Kiln"), _ckt("CKT-B", 9000, "Welder"))

    def credit(setting):
        lm = LoadManagement(tag="LM-PCS", managed_circuits=("CKT-A", "CKT-B"), strategy="pcs",
                            max_simultaneous_va=setting, listing="UL 3141 (synthetic)",
                            monitored_ocpd_amps=60)
        [c] = service_load_summary(_model(library=Library(
            circuits=circuits, load_managements=(lm,))))["load_management"]
        return c

    assert credit(11520)["credited"]  # 80% of 60 A at 240 V
    refused = credit(11600)
    assert not refused["credited"] and "120.7(B)" in refused["refusal"]
