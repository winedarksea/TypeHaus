"""Domestic water in IFC: two systems, and typed devices rather than proxies.

The stormwater family got real IFC classes and one ``IfcDistributionSystem`` first
(``test_ifc_drainage.py``); the supply side had neither. Every hot and cold run exported as
loose ``IfcPipeSegment``s belonging to nothing, and the devices on them did not export at
all, because until ``PipeAccessory`` existed there were none to export.

Two systems rather than one: hot and cold are separate systems in every tool that reads
this file, and the things that distinguish them — insulation, a mixing valve, a
recirculation loop — belong to one of them and not the other.

The trap this file exists to catch is the ``IfcFooting`` fallback. ``_SOLID_IFC_CLASS`` has
no row for any ``PIPE_ACCESSORY_CATEGORIES`` member on purpose — the dedicated emitter owns
them — so if the generic solid loop ever stops skipping them, every shutoff in the house
silently becomes a concrete footing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.resolve import resolve
from typehaus.source import load_plan

CATLIN_DIR = Path(__file__).resolve().parents[3] / "houses" / "catlin"


@pytest.fixture(scope="module")
def catlin_model():
    result = load_plan(CATLIN_DIR)
    model, findings = resolve(result.plan)
    errors = [f for f in findings if f.severity.value == "error"]
    assert not errors, errors
    return model


@pytest.fixture(scope="module")
def catlin_ifc(catlin_model, tmp_path_factory):
    ifcopenshell = pytest.importorskip("ifcopenshell")
    from typehaus.emit.ifc.emitter import emit_ifc

    out = emit_ifc(catlin_model, tmp_path_factory.mktemp("ifc") / "model.ifc")
    return ifcopenshell.open(str(out))


def _system(f, predefined: str):
    systems = [s for s in f.by_type("IfcDistributionSystem")
               if s.PredefinedType == predefined]
    assert len(systems) == 1, f"expected exactly one {predefined} system, got {systems}"
    return systems[0]


def _members(f, system) -> list:
    return [member for rel in f.by_type("IfcRelAssignsToGroup")
            if rel.RelatingGroup == system
            for member in rel.RelatedObjects]


def _pset(entity, name: str) -> dict:
    for definition in entity.IsDefinedBy or ():
        rel = getattr(definition, "RelatingPropertyDefinition", None)
        if rel is not None and rel.is_a("IfcPropertySet") and rel.Name == name:
            return {p.Name: p.NominalValue.wrappedValue for p in rel.HasProperties}
    return {}


def test_hot_and_cold_are_two_systems(catlin_ifc):
    cold = _system(catlin_ifc, "DOMESTICCOLDWATER")
    hot = _system(catlin_ifc, "DOMESTICHOTWATER")
    assert cold.Name == "DomesticColdWater"
    assert hot.Name == "DomesticHotWater"
    assert _members(catlin_ifc, cold) and _members(catlin_ifc, hot)


def test_each_system_owns_exactly_its_own_temperature(catlin_model, catlin_ifc):
    """A hot segment in the cold system is the failure mode a single merged system hides."""
    for predefined, key in (("DOMESTICCOLDWATER", "water_cold"),
                            ("DOMESTICHOTWATER", "water_hot")):
        system = _system(catlin_ifc, predefined)
        members = _members(catlin_ifc, system)
        systems = set()
        for member in members:
            if member.is_a("IfcPipeSegment"):
                systems.add(_pset(member, "TypeHaus_Pipe").get("system"))
            else:
                systems.add(_pset(member, "TypeHaus_PipeAccessory").get("system"))
        assert systems == {key}, f"{predefined} carries foreign members: {systems}"

        expected_segments = sum(
            max(len(run.path) - 1, 0) for run in catlin_model.pipe_runs if run.system == key)
        emitted = [m for m in members if m.is_a("IfcPipeSegment")]
        assert 0 < len(emitted) <= expected_segments


def test_drain_and_vent_runs_still_belong_to_no_system(catlin_ifc):
    """SANITARY/RAINWATER are deliberately deferred (plans/TODO.md). This asserts the
    deferral rather than leaving it as an absence nobody notices — the waste stack must not
    have quietly been swept into a domestic-water group."""
    for predefined in ("SANITARY", "RAINWATER", "VENT"):
        assert not [s for s in catlin_ifc.by_type("IfcDistributionSystem")
                    if s.PredefinedType == predefined]


def test_every_accessory_is_a_typed_device_and_never_a_footing(catlin_model, catlin_ifc):
    """The ``_SOLID_IFC_CLASS`` fallback wart: a category with no row becomes IfcFooting."""
    assert catlin_model.pipe_accessories, \
        "fixture regression: the Catlin house lost its supply devices"
    footing_tags = {e.Name for e in catlin_ifc.by_type("IfcFooting")}
    by_tag = {}
    for cls in ("IfcValve", "IfcPipeFitting"):
        for entity in catlin_ifc.by_type(cls):
            if _pset(entity, "TypeHaus_PipeAccessory"):
                by_tag[entity.Name] = entity
    for accessory in catlin_model.pipe_accessories:
        assert accessory.tag not in footing_tags, \
            f"{accessory.tag} exported as a concrete footing"
        assert accessory.tag in by_tag, f"{accessory.tag} reached no typed IFC device"


def test_each_accessory_kind_gets_the_right_valve_type(catlin_model, catlin_ifc):
    from typehaus.emit.ifc.emitter import _ACCESSORY_IFC_CLASS

    entities = {}
    for cls in ("IfcValve", "IfcPipeFitting"):
        for entity in catlin_ifc.by_type(cls):
            if _pset(entity, "TypeHaus_PipeAccessory"):
                entities[entity.Name] = entity
    seen = set()
    for accessory in catlin_model.pipe_accessories:
        expected_class, expected_type = _ACCESSORY_IFC_CLASS[accessory.kind]
        entity = entities[accessory.tag]
        assert entity.is_a(expected_class)
        assert entity.PredefinedType == expected_type
        seen.add(accessory.kind)
    # A shutoff and a backflow preventer must not collapse to one PredefinedType — the whole
    # point of the table is that an inspector's schedule can tell them apart.
    assert len({_ACCESSORY_IFC_CLASS[k] for k in seen}) > 1


def test_a_run_carries_its_material_finish_and_insulation_into_the_file(catlin_model,
                                                                       catlin_ifc):
    insulated = next((r for r in catlin_model.pipe_runs if r.insulation), None)
    assert insulated is not None, "fixture regression: no run authors insulation"
    segment = next(s for s in catlin_ifc.by_type("IfcPipeSegment")
                   if s.Name.startswith(f"{insulated.tag}/"))
    assert _pset(segment, "TypeHaus_Pipe")["insulation"] == insulated.insulation

    lacquered = next((r for r in catlin_model.pipe_runs if r.finish), None)
    assert lacquered is not None, "fixture regression: no run authors a finish"
    segment = next(s for s in catlin_ifc.by_type("IfcPipeSegment")
                   if s.Name.startswith(f"{lacquered.tag}/"))
    pset = _pset(segment, "TypeHaus_Pipe")
    assert (pset["material"], pset["finish"]) == (lacquered.material, lacquered.finish)
