"""Drainage in IFC: real entity classes, and one stormwater system that owns them.

Every drainage solid used to export as an ``IfcBuildingElementProxy`` — or worse, as the
``IfcFooting`` fallback for any category the emitter's table had forgotten — so a gutter, the
leader under it, the perimeter tile and the sump pit arrived in Revit as four unrelated
objects that happened to sit near each other. IFC4 has homes for all of them, and a
``IfcDistributionSystem`` with ``PredefinedType=STORMWATER`` is what a BIM tool reads as a
system rather than as a naming convention.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.emit.trades import DRAINAGE_CATEGORIES
from typehaus.resolve import resolve
from typehaus.source import load_plan
from _helpers import CATLIN as CATLIN_DIR



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


def _drainage_solids(model) -> list:
    return [s for s in model.solids if (s.category or "").lower() in DRAINAGE_CATEGORIES]


def _system(f):
    systems = [s for s in f.by_type("IfcDistributionSystem")
               if s.PredefinedType == "STORMWATER"]
    assert len(systems) == 1, "the building drains through exactly one stormwater system"
    return systems[0]


def _members(f, system) -> list:
    return [member for rel in f.by_type("IfcRelAssignsToGroup")
            if rel.RelatingGroup == system
            for member in rel.RelatedObjects]


def test_one_stormwater_system_owns_every_drainage_element(catlin_model, catlin_ifc):
    system = _system(catlin_ifc)
    member_names = {member.Name for member in _members(catlin_ifc, system)}
    expected = {solid.tag for solid in _drainage_solids(catlin_model)}
    assert expected, "fixture regression: the Catlin house lost its drainage"
    assert expected <= member_names, sorted(expected - member_names)


def test_the_system_serves_the_building(catlin_ifc):
    """Without IfcRelServicesBuildings the system floats: an importer walking the spatial
    tree to find a building's services never reaches it."""
    system = _system(catlin_ifc)
    served = [rel for rel in catlin_ifc.by_type("IfcRelServicesBuildings")
              if rel.RelatingSystem == system]
    assert served, "the stormwater system must declare the building it serves"
    assert all(building.is_a("IfcBuilding")
               for rel in served for building in rel.RelatedBuildings)


@pytest.mark.parametrize("category,ifc_class,predefined_type", [
    # What the water runs through, by how it is made: a hung channel, a rigid leader, and
    # buried flexible tile are three different products and three different enum members.
    ("gutter", "IfcPipeSegment", "GUTTER"),
    ("downspout", "IfcPipeSegment", "RIGIDSEGMENT"),
    ("drain_tile", "IfcPipeSegment", "FLEXIBLESEGMENT"),
    # What it collects in. The pit was an IfcTank, which is a vessel that stores a fluid on
    # purpose — a sump is a chamber the water passes through.
    ("sump", "IfcDistributionChamberElement", "SUMP"),
])
def test_each_drainage_category_exports_as_its_own_ifc_entity(
        catlin_model, catlin_ifc, category, ifc_class, predefined_type):
    tags = {solid.tag for solid in catlin_model.solids if solid.category == category}
    if not tags:
        pytest.skip(f"the Catlin house authors no {category}")
    by_name = {element.Name: element for element in catlin_ifc.by_type(ifc_class)}
    assert tags <= set(by_name), sorted(tags - set(by_name))
    for tag in tags:
        assert by_name[tag].PredefinedType == predefined_type


def test_no_drainage_element_lands_on_the_footing_fallback(catlin_model, catlin_ifc):
    """The unmapped-category fallback is ``IfcFooting``, so a category the table forgets is
    silently exported as a pour. That is how the drain tile would have arrived."""
    drainage_tags = {solid.tag for solid in _drainage_solids(catlin_model)}
    footing_names = {element.Name for element in catlin_ifc.by_type("IfcFooting")}
    assert not (drainage_tags & footing_names)
