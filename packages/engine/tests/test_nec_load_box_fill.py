"""2026 NEC 120.5(B), 120.7(C)(2), 120.11(A) in 120.6, and 314.16(B)/314.24(B) allowances
as `docs/nec-2026-paraphrase*.md` paraphrase them. Each test pins one rule's arithmetic."""

from __future__ import annotations

import pytest

from typehaus.checks.mep.electrical_boxes import egc_allowance, min_depth_in, required_volume_in3
from typehaus.model import (
    Building,
    Circuit,
    DeviceKind,
    ElectricalDevice,
    Equipment,
    EquipmentKind,
    EquipmentType,
    Library,
    LoadManagement,
    PlanModel,
    Project,
    Site,
    Storey,
    m,
    pt,
)
from typehaus.resolve import resolve
from typehaus.takeoff.service_load import round_amps, service_load_summary

_PANEL = ElectricalDevice(tag="ED-M-PANEL", kind=DeviceKind.PANEL, position=pt(m(0), m(0)))


def _model(library, devices=()):
    plan = PlanModel(
        project=Project(name="t", project_uuid="00000000-0000-0000-0000-000000000120",
                        building=Building(name="t"), site=Site(lat=0, lon=0, elevation=m(0))),
        storeys=(Storey(tag="main", elevation=m(0), default_ceiling_height=m(3)),),
        library=library, elements={"main": (_PANEL, *devices)})
    model, findings = resolve(plan)
    assert not [f for f in findings if f.severity.value == "error"]
    return model


def _ckt(tag, va, description):
    return Circuit(tag=tag, panel_ref="ED-M-PANEL", breaker_amps=20, poles=2, load_va=va,
                   description=description)


def _credit(lm, circuits, devices=(), types=()):
    library = Library(circuits=circuits, load_managements=(lm,), equipment_types=types)
    [credit] = service_load_summary(_model(library, devices))["load_management"]
    return credit


def test_120_5b_rounds_to_the_nearest_ampere_dropping_under_half():
    assert (round_amps(250.43), round_amps(250.5), round_amps(250.49)) == (250, 251, 250)


def test_120_6_takes_the_largest_members_motor_at_125_percent():
    pump = EquipmentType(tag="EQ-T-PUMP", name="pump", footprint=(m(.4), m(.3)), height=m(.3),
                         largest_motor_va=4000)
    pump_on_a = Equipment(tag="EQ-PUMP", kind=EquipmentKind.WATER_HEATER, position=pt(m(2), m(2)),
                          footprint=(m(.4), m(.3)), circuit="CKT-A", type_ref="EQ-T-PUMP")
    circuits = (_ckt("CKT-A", 5000, "Pump"), _ckt("CKT-B", 3000, "Kiln"))
    lm = LoadManagement(tag="LM-NC", managed_circuits=("CKT-A", "CKT-B"),
                        max_simultaneous_va=0, strategy="noncoincident", source="never together")
    credit = _credit(lm, circuits, (pump_on_a,), (pump,))
    assert credit["cap_va"] == 5000 + 0.25 * 4000 and credit["excess_va"] == 2000
    # A lone motor load lifts the count past the connected sum (a negative excess).
    lone = lm.model_copy(update={"managed_circuits": ("CKT-A",)})
    assert _credit(lone, circuits, (pump_on_a,), (pump,))["excess_va"] == -1000


def test_120_7c2_counts_controlled_loads_at_their_minimum_operating_current():
    circuits = (_ckt("CKT-A", 9000, "Kiln"), _ckt("CKT-B", 9000, "Welder"))
    lm = LoadManagement(tag="LM-PCS", managed_circuits=("CKT-A", "CKT-B"), strategy="pcs",
                        max_simultaneous_va=11520, listing="UL 3141 (synthetic)",
                        monitored_ocpd_amps=60, monitors_noncontrolled=True)
    refused = _credit(lm, circuits)
    assert not refused["credited"] and "120.7(C)(2)" in refused["refusal"]
    mixed = _credit(lm.model_copy(update={"min_operating_amps": 10.0}), circuits)
    assert mixed["credited"] and mixed["cap_va"] == 2400 and mixed["excess_va"] == 15600


def test_314_16b_clamps_support_fittings_and_egcs_past_four():
    base = required_volume_in3(12, 1, False, 1)  # 4 + 2 + 1 = 7 at 2.25
    assert base == pytest.approx(15.75)
    assert required_volume_in3(12, 1, False, 1, clamps=True, support_fittings=1) == (
        pytest.approx(base + 2 * 2.25))
    assert (egc_allowance(4), egc_allowance(6)) == (1.0, 1.5)


@pytest.mark.parametrize(("gauge", "projection", "depth"), [
    (14, None, 15 / 16), (14, 1.5, 15 / 16), (14, 2.0, 2.25),
    (12, 1.0, 1 + 3 / 16), (12, 1.25, 1.5), (8, 1.5, 2 + 1 / 16)])
def test_314_24b_depth_with_the_rear_projection_add_on(gauge, projection, depth):
    assert min_depth_in(gauge, projection) == pytest.approx(depth)
