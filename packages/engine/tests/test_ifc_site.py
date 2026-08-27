"""IFC site emission — parcel representation + utility proxies (→ Permit-ready Phase 4)."""

from __future__ import annotations

from pathlib import Path

import pytest



def test_ifc_site_has_representation_and_pset(catlin_ifc_path: Path):
    ifcopenshell = pytest.importorskip("ifcopenshell")

    f = ifcopenshell.open(str(catlin_ifc_path))

    sites = f.by_type("IfcSite")
    assert len(sites) == 1
    assert sites[0].Representation is not None

    props = {}
    for rel in sites[0].IsDefinedBy or ():
        pset = rel.RelatingPropertyDefinition
        if pset.is_a("IfcPropertySet") and pset.Name == "TypeHaus_Site":
            props = {p.Name: p.NominalValue.wrappedValue for p in pset.HasProperties}
    assert "parcel_area_m2" in props
    assert props["parcel_area_m2"] > 0


def test_ifc_has_utility_proxies(catlin_model_ro, catlin_ifc_path: Path):
    ifcopenshell = pytest.importorskip("ifcopenshell")

    f = ifcopenshell.open(str(catlin_ifc_path))

    proxies = [p for p in f.by_type("IfcBuildingElementProxy")
              if (p.Name or "").startswith("UTIL-")]
    assert len(proxies) == len(catlin_model_ro.plan.project.site.utilities)


def test_the_site_sheet_hangs_below_grade_rather_than_standing_on_it(catlin_model_ro,
                                                                    catlin_ifc_path: Path):
    """The IFC switch-over's blessed diff: soil is what is *under* the grade plane.

    The pad used to be extruded 5cm upward from grade, so the ground Revit received sat 5cm
    above the ground the viewer drew and every slab-on-grade stood proud of its own site.
    """
    ifcopenshell = pytest.importorskip("ifcopenshell")
    from typehaus.resolve.geometry_build import EARTH_SHEET_THICKNESS_M
    from typehaus.resolve.site_earth import site_grade_elevation_m

    site = ifcopenshell.open(str(catlin_ifc_path)).by_type("IfcSite")[0]
    solid = site.Representation.Representations[0].Items[0]
    grade = site_grade_elevation_m(catlin_model_ro)
    assert solid.Depth == pytest.approx(EARTH_SHEET_THICKNESS_M, abs=1e-9)
    assert solid.Position.Location.Coordinates[2] == pytest.approx(
        grade - EARTH_SHEET_THICKNESS_M, abs=1e-9)
    # Still cut by everything excavated out of it, or the sheet runs through the basement.
    assert solid.SweptArea.is_a("IfcArbitraryProfileDefWithVoids")


def test_a_subfloor_deck_reaches_the_ifc_export(catlin_model_ro, catlin_ifc_path: Path):
    """Blessed diff: no emitter drew a deck, so a floor exported as joists under nothing."""
    ifcopenshell = pytest.importorskip("ifcopenshell")

    decked = [floor for floor in catlin_model_ro.floors if floor.deck_outline]
    assert decked, "the catlin house has floor systems with a subfloor"
    f = ifcopenshell.open(str(catlin_ifc_path))
    decks = {slab.Name for slab in f.by_type("IfcSlab") if slab.Name.endswith("/deck")}
    assert decks == {f"{floor.tag}/deck" for floor in decked}
    for slab in (item for item in f.by_type("IfcSlab") if item.Name.endswith("/deck")):
        assert slab.PredefinedType == "FLOOR"
        assert slab.Representation is not None
