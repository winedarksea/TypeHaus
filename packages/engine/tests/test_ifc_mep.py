"""IFC MEP emission — pipe segments + sleeve proxies (→ Permit-ready plan set Phase 2)."""

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
    assert len(terminals) == 6  # REGISTERS in houses/catlin/plan/mep.py


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
