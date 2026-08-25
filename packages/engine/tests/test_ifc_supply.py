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


import pytest



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


def test_the_waste_side_is_systems_now_sanitary_vent_and_radon(catlin_model, catlin_ifc):
    """The deferral this test used to pin is closed: every drain run belongs to a SEWAGE
    system (IFC4's sanitary drainage — the enum has no SANITARY member), every vent run to
    a VENT system, and the radon riser to its own USERDEFINED/RADON system rather than
    being folded into the plumbing vents it must never connect to."""
    for predefined, key in (("SEWAGE", "drain"), ("VENT", "vent")):
        system = _system(catlin_ifc, predefined)
        members = _members(catlin_ifc, system)
        assert members, f"{predefined} groups nothing"
        assert {_pset(m, "TypeHaus_Pipe").get("system") for m in members
                if m.is_a("IfcPipeSegment")} == {key}
        expected_segments = sum(
            max(len(run.path) - 1, 0) for run in catlin_model.pipe_runs if run.system == key)
        emitted = [m for m in members if m.is_a("IfcPipeSegment")]
        assert 0 < len(emitted) <= expected_segments
    # A radon *pipe run* would get its own USERDEFINED/RADON system rather than being
    # folded into VENT (a soil-gas riser must never read as connected to the plumbing
    # vents). Catlin's radon is a VentRun riser — solids, not a PipeRun — so the mapping is
    # asserted on the table and the absence of a hollow system is asserted on the file.
    from typehaus.emit.ifc.emitter import _PIPE_SYSTEM_OBJECT_TYPES, _PIPE_SYSTEM_TYPES

    assert _PIPE_SYSTEM_TYPES["radon"] == ("RadonVent", "USERDEFINED")
    assert _PIPE_SYSTEM_OBJECT_TYPES["radon"] == "RADON"
    assert not any(run.system == "radon" for run in catlin_model.pipe_runs), \
        "fixture drift: catlin now authors a radon PipeRun — assert its system here"
    assert not [s for s in catlin_ifc.by_type("IfcDistributionSystem")
                if s.Name == "RadonVent"], "an empty system must not be emitted"
    # Rainwater stays a non-system among the pipe runs on purpose: the stormwater solids
    # (gutter, leader, tile) already group under STORMWATER.
    assert not [s for s in catlin_ifc.by_type("IfcDistributionSystem")
                if s.PredefinedType == "RAINWATER"]


def test_every_authored_pipe_run_lands_in_exactly_one_system(catlin_model, catlin_ifc):
    """The grouping loop used to ``.get(run.system, []).extend(...)`` — a silent discard
    that kept 26 of catlin's runs unsystemed. Every emitted segment must now belong to
    exactly one distribution system."""
    systems = [s for s in catlin_ifc.by_type("IfcDistributionSystem")]
    owner_count: dict = {}
    for system in systems:
        for member in _members(catlin_ifc, system):
            if member.is_a("IfcPipeSegment") and _pset(member, "TypeHaus_Pipe"):
                owner_count[member.Name] = owner_count.get(member.Name, 0) + 1
    run_tags = {run.tag for run in catlin_model.pipe_runs}
    orphaned = [tag for tag in run_tags
                if not any(name.startswith(f"{tag}/") for name in owner_count)]
    assert not orphaned, f"authored runs in no system: {sorted(orphaned)}"
    doubles = {name: n for name, n in owner_count.items() if n > 1}
    assert not doubles, f"segments grouped twice: {doubles}"


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


def test_a_routed_run_exports_once_and_never_as_a_footing(catlin_model, catlin_ifc):
    """The same trap this file was written for, one family over: a *run's own tube*.

    A pipe or raceway exports as the segments it is (``_emit_pipe_run``/``emit_conduits``),
    and its swept ``ResolvedSolid`` is how glTF and the viewer draw it — not a second IFC
    element. ``ROUTED_RUN_CATEGORIES`` has no ``_SOLID_IFC_CLASS`` row, so the generic loop
    exported every run a second time as a concrete footing: 68 of catlin's 239.
    """
    from typehaus.emit.trades import ROUTED_RUN_CATEGORIES

    run_solids = [s for s in catlin_model.solids
                  if (s.category or "").lower() in ROUTED_RUN_CATEGORIES]
    assert len(run_solids) > 50, "the reference house should be full of routed runs"
    footing_names = {element.Name for element in catlin_ifc.by_type("IfcFooting")}
    assert not (footing_names & {s.tag for s in run_solids})


def test_every_routed_run_category_is_declared(catlin_model):
    """``ROUTED_RUN_CATEGORIES`` is assembled from the enums; this is the check that the
    categories ``resolve/mep.py`` actually mints are the ones it names."""
    from typehaus.emit.trades import ROUTED_RUN_CATEGORIES

    minted = {(s.category or "").lower() for s in catlin_model.solids if s.sweep is not None}
    assert minted - {"railing"} <= ROUTED_RUN_CATEGORIES


def test_the_runs_are_still_in_the_file_as_segments(catlin_model, catlin_ifc):
    """Skipping the solid must not take the run with it: one ``IfcPipeSegment`` per leg."""
    segments = [s for s in catlin_ifc.by_type("IfcPipeSegment") if "/" in (s.Name or "")]
    named = {(s.Name or "").split("/")[0] for s in segments}
    for run in catlin_model.pipe_runs:
        assert run.tag in named, f"{run.tag} lost its segments"
