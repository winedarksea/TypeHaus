"""IFC site emission — parcel representation + utility proxies (→ Permit-ready Phase 4)."""

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


def test_ifc_site_has_representation_and_pset(catlin_model, tmp_path: Path):
    ifcopenshell = pytest.importorskip("ifcopenshell")
    from typehaus.emit.ifc.emitter import emit_ifc

    out = emit_ifc(catlin_model, tmp_path / "model.ifc")
    f = ifcopenshell.open(str(out))

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


def test_ifc_has_utility_proxies(catlin_model, tmp_path: Path):
    ifcopenshell = pytest.importorskip("ifcopenshell")
    from typehaus.emit.ifc.emitter import emit_ifc

    out = emit_ifc(catlin_model, tmp_path / "model2.ifc")
    f = ifcopenshell.open(str(out))

    proxies = [p for p in f.by_type("IfcBuildingElementProxy")
              if (p.Name or "").startswith("UTIL-")]
    assert len(proxies) == len(catlin_model.plan.project.site.utilities)
