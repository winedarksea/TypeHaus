"""IFC MEP emission — pipe segments + sleeve proxies (→ Permit-ready plan set Phase 2)."""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.resolve import resolve
from typehaus.source import load_plan
from typehaus.diff import ChangeKind, build_report
from typehaus.diff.ifc_adapter import baseline_elems, external_elems
from typehaus.model import (Building, ElectricalDevice, ElectricalDeviceType, Equipment, EquipmentKind,
                            EquipmentType, Library, PlanModel, Project, Register, RegisterType, Service,
                            ServicePort, Site, Storey, DeviceKind, m, pt)

CATLIN_DIR = Path(__file__).resolve().parents[3] / "houses" / "catlin"


@pytest.fixture(scope="module")
def catlin_model():
    result = load_plan(CATLIN_DIR)
    model, findings = resolve(result.plan)
    errors = [f for f in findings if f.severity.value == "error"]
    assert not errors, errors
    return model


def test_ifc_has_pipe_segments_and_sleeve_proxies(catlin_model, tmp_path: Path):
    ifcopenshell = pytest.importorskip("ifcopenshell")
    from typehaus.emit.ifc.emitter import emit_ifc

    out = emit_ifc(catlin_model, tmp_path / "model.ifc")
    f = ifcopenshell.open(str(out))

    pipes = f.by_type("IfcPipeSegment")
    total_segments = sum(len(run.path) - 1 for run in catlin_model.pipe_runs)
    assert len(pipes) == total_segments
    assert all(p.GlobalId for p in pipes)

    proxies = f.by_type("IfcBuildingElementProxy")
    sleeve_tags = {s.tag for s in catlin_model.sleeves}
    proxy_names = {p.Name for p in proxies}
    assert sleeve_tags <= proxy_names


def test_ifc_has_duct_segments_and_air_terminals(catlin_model, tmp_path: Path):
    ifcopenshell = pytest.importorskip("ifcopenshell")
    from typehaus.emit.ifc.emitter import emit_ifc

    out = emit_ifc(catlin_model, tmp_path / "model2.ifc")
    f = ifcopenshell.open(str(out))

    ducts = f.by_type("IfcDuctSegment")
    total_segments = sum(len(duct.path) - 1 for duct in catlin_model.ducts)
    assert len(ducts) == total_segments
    assert all(d.GlobalId for d in ducts)

    terminals = f.by_type("IfcAirTerminal")
    assert len(terminals) == 7  # REGISTERS in houses/catlin/plan/mep.py


def test_ifc_has_footing_bedding_proxies(catlin_model, tmp_path: Path):
    ifcopenshell = pytest.importorskip("ifcopenshell")
    from typehaus.emit.ifc.emitter import emit_ifc

    out = emit_ifc(catlin_model, tmp_path / "model3.ifc")
    f = ifcopenshell.open(str(out))

    proxies = f.by_type("IfcBuildingElementProxy")
    bedding_tags = {fb.tag for fb in catlin_model.footing_beddings}
    assert bedding_tags
    proxy_names = {p.Name for p in proxies}
    assert bedding_tags <= proxy_names

    proxy = next(p for p in proxies if p.Name == "FB-B-S1")
    pset = next(rel.RelatingPropertyDefinition for rel in proxy.IsDefinedBy
               if rel.RelatingPropertyDefinition.Name == "TypeHaus_FootingBedding")
    props = {prop.Name: prop.NominalValue.wrappedValue for prop in pset.HasProperties}
    assert "#57" in props["aggregate"]
    assert props["geotextile"] is True


def test_catalog_typed_mep_placeables_get_ifc_types_and_stable_ports(tmp_path: Path):
    ifcopenshell = pytest.importorskip("ifcopenshell")
    from typehaus.emit.ifc.emitter import emit_ifc

    port = ServicePort(tag="power", service=Service.POWER_120, position=(m(0), m(0), m(0)))
    plan = PlanModel(
        project=Project(name="test", project_uuid="00000000-0000-0000-0000-000000000001",
                        building=Building(name="test"), site=Site(lat=0, lon=0, elevation=m(0))),
        storeys=(Storey(tag="main", elevation=m(0), default_ceiling_height=m(3)),),
        library=Library(
            register_types=(RegisterType(tag="REG-T", name="Supply", footprint=(m(.3), m(.1)), height=m(.05)),),
            equipment_types=(EquipmentType(tag="EQ-T", name="Furnace", footprint=(m(.6), m(.7)), height=m(1),
                                            ports=(port,)),),
            electrical_device_types=(ElectricalDeviceType(tag="ED-T", name="Outlet", footprint=(m(.1), m(.1)),
                                                           height=m(.05), ports=(port,)),),
        ),
        elements={"main": (
            Register(tag="REG-1", kind="supply", position=pt(m(0), m(0)), type_ref="REG-T"),
            Equipment(tag="EQ-1", kind=EquipmentKind.FURNACE, position=pt(m(1), m(0)),
                      footprint=(m(.6), m(.7)), type_ref="EQ-T"),
            ElectricalDevice(tag="ED-1", kind=DeviceKind.RECEPTACLE, position=pt(m(2), m(0)), type_ref="ED-T"),
        )},
    )
    model, findings = resolve(plan)
    assert not [item for item in findings if item.severity.value == "error"]
    f = ifcopenshell.open(str(emit_ifc(model, tmp_path / "typed-mep.ifc")))
    products = [*f.by_type("IfcAirTerminal"), *f.by_type("IfcBuildingElementProxy"), *f.by_type("IfcOutlet")]
    for name in ("REG-1", "EQ-1", "ED-1"):
        occurrence = next(item for item in products if item.Name == name)
        assert occurrence.IsTypedBy
    ports = f.by_type("IfcDistributionPort")
    assert {item.Name for item in ports} == {"power"}
    assert len(ports) == 2 and all(item.GlobalId for item in ports)
    report = build_report(baseline_elems(model), external_elems(tmp_path / "typed-mep.ifc"))
    assert not [change for change in report.substantive() if change.kind is ChangeKind.ATTR_CHANGED]
