"""``EquipmentKind.FAN`` and the fan-driven ``DuctSystem.TRANSFER`` run it drives.

A stall-drying or transfer fan moves room air through a duct of its own. It is not a
ventilator, so its run is TRANSFER, and unlike a passive louver its grilles name that run.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.checks import run_from_model
from typehaus.checks.registry import Tier
from typehaus.diff import build_report
from typehaus.diff.ifc_adapter import baseline_elems, external_elems
from typehaus.model import (
    Building,
    DuctRun,
    DuctSystem,
    Equipment,
    EquipmentKind,
    EquipmentType,
    Library,
    PlanModel,
    Project,
    Register,
    RegisterType,
    Site,
    Storey,
    m,
    pt,
)
from typehaus.resolve import resolve


def _plan(duct_ref: str = "DU-1") -> PlanModel:
    return PlanModel(
        project=Project(name="test", project_uuid="00000000-0000-0000-0000-000000000002",
                        building=Building(name="test"), site=Site(lat=0, lon=0, elevation=m(0))),
        storeys=(Storey(tag="main", elevation=m(0), default_ceiling_height=m(3)),),
        library=Library(
            register_types=(RegisterType(tag="REG-T", name="Grille", footprint=(m(.25), m(.25)),
                                         height=m(.05)),),
            equipment_types=(EquipmentType(tag="EQ-T-FAN", name="Inline fan",
                                           footprint=(m(.3), m(.3)), height=m(.25)),),
        ),
        elements={"main": (
            Equipment(uid="TSTFAN0001", tag="EQ-FAN", kind=EquipmentKind.FAN,
                      position=pt(m(0), m(0)), footprint=(m(.3), m(.3)), type_ref="EQ-T-FAN"),
            # Starts on the fan's east face, ends at the grille it feeds.
            DuctRun(uid="TSTFAN0002", tag="DU-1", system=DuctSystem.TRANSFER, diameter=m(.1),
                    path=(pt(m(.15), m(0)), pt(m(2), m(0))),
                    start_elevation=m(.12), end_elevation=m(.12)),
            Register(uid="TSTFAN0003", tag="REG-OUT", kind=DuctSystem.TRANSFER,
                     position=pt(m(2), m(0)), type_ref="REG-T", duct_ref=duct_ref),
        )},
    )


def _findings(model, check_id: str):
    report = run_from_model(model, [], tier=Tier.INTEGRITY, only=check_id)
    return [f for f in report.findings if f.check_id == check_id]


def test_fan_emits_as_ifc_fan_and_reads_back_unchanged(tmp_path: Path):
    ifcopenshell = pytest.importorskip("ifcopenshell")
    from typehaus.emit.ifc.emitter import emit_ifc

    model, _ = resolve(_plan())
    path = emit_ifc(model, tmp_path / "fan.ifc")
    f = ifcopenshell.open(str(path))
    assert [item.Name for item in f.by_type("IfcFan")] == ["EQ-FAN"]
    assert f.by_type("IfcFan")[0].IsTypedBy[0].RelatingType.is_a("IfcFanType")
    report = build_report(baseline_elems(model), external_elems(path))
    assert not [c for c in report.substantive() if "EQ-FAN" in str(c)]


def test_fan_is_inferred_from_its_product_words():
    from typehaus.source.macros_placeables import _infer_equipment_kind

    assert _infer_equipment_kind(_plan(), "EQ-T-FAN") is EquipmentKind.FAN


def test_a_fan_driven_transfer_run_lands_at_both_ends():
    model, _ = resolve(_plan())
    found = {f.message: f.result.value for f in _findings(model, "mep.duct_connectivity")}
    assert "fail" not in found.values(), found
    assert any("DU-1 start lands on EQ-FAN" in message for message in found)


def test_a_transfer_grille_naming_a_run_is_validated():
    model, _ = resolve(_plan())
    assert {f.result.value for f in _findings(model, "integrity.register_duct_ref")} == {"pass"}
    model, _ = resolve(_plan(duct_ref="DU-TYPO"))
    failed = [f for f in _findings(model, "integrity.register_duct_ref")
              if f.result.value == "fail"]
    assert [f.element_tags for f in failed] == [("REG-OUT",)]
