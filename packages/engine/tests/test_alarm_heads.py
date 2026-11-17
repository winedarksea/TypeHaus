"""Alarm heads: one resolved body (resolve/alarm_heads.py) read by the GLB, the IFC and the BOM."""

from __future__ import annotations

from collections import Counter

import pytest


def test_every_alarm_head_reaches_the_glb_as_its_resolved_body(catlin_model_ro):
    from typehaus.emit.gltf.emitter import emit_gltf_dict

    heads = {h.uid: h for h in catlin_model_ro.alarm_heads}
    assert len(heads) == 30 and all(h.body is not None for h in heads.values())
    doc = emit_gltf_dict(catlin_model_ro, "core")
    doc = doc[0] if isinstance(doc, tuple) else doc
    nodes = [n for n in doc["nodes"] if (n.get("extras") or {}).get("kind") == "alarm"]
    assert {n["extras"]["uid"] for n in nodes} == set(heads)


def test_alarm_heads_export_as_typed_ifc_sensors(catlin_model_ro):
    ifcopenshell = pytest.importorskip("ifcopenshell")  # noqa: F841
    from typehaus.emit.ifc import lowlevel as ll
    from typehaus.emit.ifc.alarms import emit_alarms

    f = ll.new_file("test")
    project = ll.create_entity(f, "IfcProject", name="t")
    ll.assign_project_units(f)
    body = ll.add_context(f)
    building = ll.create_entity(f, "IfcBuilding", name="b")
    ll.aggregate(f, project, [building])
    storeys = {s.tag: ll.create_entity(f, "IfcBuildingStorey", name=s.tag)
               for s in catlin_model_ro.plan.storeys}
    ll.aggregate(f, building, list(storeys.values()))
    emit_alarms(f, body, catlin_model_ro, storeys, catlin_model_ro.plan.project.project_uuid)
    ll.flush_containers(f)
    sensors = {s.Name: s for s in f.by_type("IfcSensor")}
    assert len(sensors) == 30
    assert all(s.ContainedInStructure for s in sensors.values())
    leak_type = sensors["AL-B-WH-LEAK"].IsTypedBy[0].RelatingType
    assert leak_type.PredefinedType == "MOISTURESENSOR"
    assert "SNZB-05P" in leak_type.Name
    assert (sensors["AL-G-HEAT"].IsTypedBy[0].RelatingType.PredefinedType == "HEATSENSOR")


def test_typed_alarms_bill_by_count(catlin_model_ro):
    from typehaus.takeoff.placeables import placeables_takeoff

    counts: Counter[str] = Counter()
    for row in placeables_takeoff(catlin_model_ro):
        counts[row["type"]] += row["count"]
    assert counts["ED-T-LEAK-SNZB05P"] == 16
    assert counts["ED-T-ALARM-COMBO-KIDDE"] == 10
    assert counts["ED-T-FREEZE-ARRE"] == 1
