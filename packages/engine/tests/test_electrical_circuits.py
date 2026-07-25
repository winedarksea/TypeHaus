"""Circuit model + ``electrical.circuit_refs`` + service-entrance device kinds (WS1)."""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.checks import run_from_model
from typehaus.checks.registry import Tier
from typehaus.model import (Building, Circuit, DeviceKind, ElectricalDevice, ElectricalDeviceType,
                            Library, PlanModel, Project, Service, ServicePort, Site, Storey, m, pt)
from typehaus.resolve import resolve


def _plan(circuits=(), devices=(), types=()):
    return PlanModel(
        project=Project(name="test", project_uuid="00000000-0000-0000-0000-000000000002",
                        building=Building(name="test"), site=Site(lat=0, lon=0, elevation=m(0))),
        storeys=(Storey(tag="main", elevation=m(0), default_ceiling_height=m(3)),),
        library=Library(circuits=tuple(circuits), electrical_device_types=tuple(types)),
        elements={"main": tuple(devices)},
    )


def _findings(plan, check_id):
    model, findings = resolve(plan)
    assert not [f for f in findings if f.severity.value == "error"]
    report = run_from_model(model, [], tier=Tier.ADVISORY)
    return [f for f in report.findings if f.check_id == check_id]


_PANEL = ElectricalDevice(tag="ED-M-PANEL", kind=DeviceKind.PANEL, position=pt(m(0), m(0)))
_PORT_120 = ServicePort(tag="power", service=Service.POWER_120, position=(m(0), m(0), m(0)))
_PORT_240 = ServicePort(tag="power240", service=Service.POWER_240, position=(m(0), m(0), m(0)))


def test_circuit_refs_unknown_without_circuits():
    findings = _findings(_plan(devices=(_PANEL,)), "electrical.circuit_refs")
    assert [f.result.value for f in findings] == ["unknown"]


def test_circuit_refs_pass_when_everything_reconciles():
    plan = _plan(
        circuits=(Circuit(tag="CKT-01", panel_ref="ED-M-PANEL", breaker_amps=20),),
        types=(ElectricalDeviceType(tag="ED-T", name="Outlet", footprint=(m(.1), m(.1)),
                                    height=m(.05), ports=(_PORT_120,)),),
        devices=(_PANEL, ElectricalDevice(tag="ED-M-RC1", kind=DeviceKind.RECEPTACLE,
                                          position=pt(m(1), m(0)), type_ref="ED-T",
                                          circuit="CKT-01")),
    )
    findings = _findings(plan, "electrical.circuit_refs")
    assert [f.result.value for f in findings] == ["pass"]


def test_circuit_refs_flags_dangling_reference_and_missing_panel():
    plan = _plan(
        circuits=(Circuit(tag="CKT-01", panel_ref="ED-M-NOPE", breaker_amps=20),),
        devices=(_PANEL, ElectricalDevice(tag="ED-M-RC1", kind=DeviceKind.RECEPTACLE,
                                          position=pt(m(1), m(0)), circuit="CKT-99")),
    )
    findings = _findings(plan, "electrical.circuit_refs")
    messages = " | ".join(f.message for f in findings if f.result.value == "fail")
    assert "missing panel ED-M-NOPE" in messages
    assert "unknown circuit CKT-99" in messages


def test_circuit_refs_flags_pole_port_mismatch():
    plan = _plan(
        circuits=(Circuit(tag="CKT-EV", panel_ref="ED-M-PANEL", breaker_amps=50, poles=2),),
        types=(ElectricalDeviceType(tag="ED-T-120", name="Outlet", footprint=(m(.1), m(.1)),
                                    height=m(.05), ports=(_PORT_120,)),),
        devices=(_PANEL, ElectricalDevice(tag="ED-M-RC1", kind=DeviceKind.RECEPTACLE,
                                          position=pt(m(1), m(0)), type_ref="ED-T-120",
                                          circuit="CKT-EV")),
    )
    findings = _findings(plan, "electrical.circuit_refs")
    fails = [f for f in findings if f.result.value == "fail"]
    assert fails and "no power_240 port" in fails[0].message


def test_dual_port_type_satisfies_either_pole_count():
    """The two-gang 5-20R/6-20R precedent: a type with both ports passes on any circuit."""
    dual = ElectricalDeviceType(tag="ED-T-DUAL", name="Kettle outlet", footprint=(m(.1), m(.1)),
                                height=m(.05), ports=(_PORT_120, _PORT_240))
    plan = _plan(
        circuits=(Circuit(tag="CKT-A", panel_ref="ED-M-PANEL", breaker_amps=20, poles=2),),
        types=(dual,),
        devices=(_PANEL, ElectricalDevice(tag="ED-M-KET", kind=DeviceKind.RECEPTACLE_240,
                                          position=pt(m(1), m(0)), type_ref="ED-T-DUAL",
                                          circuit="CKT-A")),
    )
    findings = _findings(plan, "electrical.circuit_refs")
    assert [f.result.value for f in findings] == ["pass"]


def test_service_entrance_device_kinds_get_dedicated_ifc_classes(tmp_path: Path):
    """junction_box/meter/disconnect must not fall through to IfcBuildingElementProxy —
    and the diff adapter must read the same classes back (clean round-trip)."""
    ifcopenshell = pytest.importorskip("ifcopenshell")
    from typehaus.diff import build_report
    from typehaus.diff.ifc_adapter import baseline_elems, external_elems
    from typehaus.emit.ifc.emitter import emit_ifc

    plan = _plan(devices=(
        ElectricalDevice(uid="TESTJB0001", tag="ED-M-JB", kind=DeviceKind.JUNCTION_BOX,
                         position=pt(m(0), m(0))),
        ElectricalDevice(uid="TESTMT0001", tag="ED-M-METER", kind=DeviceKind.METER,
                         position=pt(m(1), m(0))),
        ElectricalDevice(uid="TESTDS0001", tag="ED-M-DISC", kind=DeviceKind.DISCONNECT,
                         position=pt(m(2), m(0))),
    ))
    model, findings = resolve(plan)
    assert not [f for f in findings if f.severity.value == "error"]
    f = ifcopenshell.open(str(emit_ifc(model, tmp_path / "kinds.ifc")))
    assert {p.Name for p in f.by_type("IfcJunctionBox")} == {"ED-M-JB"}
    assert {p.Name for p in f.by_type("IfcFlowMeter")} == {"ED-M-METER"}
    assert {p.Name for p in f.by_type("IfcSwitchingDevice")} == {"ED-M-DISC"}
    report = build_report(baseline_elems(model), external_elems(tmp_path / "kinds.ifc"))
    assert not report.substantive(), [
        (change.kind, change.tag) for change in report.substantive()]


def test_circuit_is_schedule_data_not_geometry():
    """A Circuit never enters storey element lists; it lives in Library.circuits."""
    circuit = Circuit(tag="CKT-01", panel_ref="ED-B-PANEL", breaker_amps=20, backup=True)
    assert circuit.poles == 1 and circuit.backup and not circuit.gfci
    library = Library(circuits=(circuit,))
    assert library.circuits[0].tag == "CKT-01"
