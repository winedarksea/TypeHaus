"""IFC MEP emission — pipe segments + sleeve proxies (→ Permit-ready plan set Phase 2)."""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.resolve import resolve
from typehaus.diff import ChangeKind, build_report
from typehaus.diff.ifc_adapter import baseline_elems, external_elems
from typehaus.model import (Building, ElectricalDevice, ElectricalDeviceType, Equipment, EquipmentKind,
                            EquipmentType, Library, PlanModel, Project, Register, RegisterType, Service,
                            ServicePort, Site, Storey, DeviceKind, m, pt)


def test_ifc_has_pipe_segments_and_sleeve_proxies(catlin_model_ro, catlin_ifc_path: Path):
    ifcopenshell = pytest.importorskip("ifcopenshell")

    f = ifcopenshell.open(str(catlin_ifc_path))

    # Authored PipeRuns are the segments with no PredefinedType. Drainage now emits real
    # IfcPipeSegments too — a gutter is GUTTER, a leader RIGIDSEGMENT, buried tile
    # FLEXIBLESEGMENT (test_ifc_drainage.py) — so the count that identifies a routed run is
    # the untyped one, not every pipe segment in the file.
    pipes = [p for p in f.by_type("IfcPipeSegment")
             if p.PredefinedType in (None, "NOTDEFINED")]
    total_segments = sum(len(run.path) - 1 for run in catlin_model_ro.pipe_runs)
    assert len(pipes) == total_segments
    assert all(p.GlobalId for p in pipes)

    proxies = f.by_type("IfcBuildingElementProxy")
    sleeve_tags = {s.tag for s in catlin_model_ro.sleeves}
    proxy_names = {p.Name for p in proxies}
    assert sleeve_tags <= proxy_names


def test_ifc_has_duct_segments_and_air_terminals(catlin_model_ro, catlin_ifc_path: Path):
    ifcopenshell = pytest.importorskip("ifcopenshell")

    f = ifcopenshell.open(str(catlin_ifc_path))

    ducts = f.by_type("IfcDuctSegment")
    total_segments = sum(len(duct.path) - 1 for duct in catlin_model_ro.ducts)
    assert len(ducts) == total_segments
    assert all(d.GlobalId for d in ducts)

    terminals = f.by_type("IfcAirTerminal")
    expected = sum(1 for storey in catlin_model_ro.plan.storeys
                   for e in catlin_model_ro.plan.storey_elements(storey.tag)
                   if e.element_kind == "Register")
    assert len(terminals) == expected  # every authored Register, all four storeys


def test_ifc_has_footing_bedding_proxies(catlin_model_ro, catlin_ifc_path: Path):
    ifcopenshell = pytest.importorskip("ifcopenshell")

    f = ifcopenshell.open(str(catlin_ifc_path))

    proxies = f.by_type("IfcBuildingElementProxy")
    bedding_tags = {fb.tag for fb in catlin_model_ro.footing_beddings}
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
