"""WP7 — IFC openings: IfcOpeningElement voids + IfcWindow/IfcDoor fillings, GUID round-trip."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest

from typehaus.diff import build_report
from typehaus.diff.ifc_adapter import baseline_elems, external_elems
from typehaus.emit.ifc import emit_ifc
from typehaus.model.ids import derive_guid

pytest.importorskip("ifcopenshell")


@pytest.fixture(scope="module")
def catlin_ifc(catlin_model, tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("ifc") / "catlin.ifc"
    emit_ifc(catlin_model, out, lod="core")
    return out


def test_every_opening_emits_a_void_and_a_filling(catlin_model, catlin_ifc):
    import ifcopenshell

    f = ifcopenshell.open(str(catlin_ifc))
    n = len(catlin_model.openings)
    assert n > 0
    windows = f.by_type("IfcWindow")
    doors = f.by_type("IfcDoor")
    filled = [opening for opening in catlin_model.openings if opening.kind != "rough_opening"]
    assert len(windows) + len(doors) == len(filled)
    # Every opening voids its host; only installed products receive filling relationships.
    assert len(f.by_type("IfcOpeningElement")) == n
    assert len(f.by_type("IfcRelVoidsElement")) == n
    assert len(f.by_type("IfcRelFillsElement")) == len(filled)
    # doors vs windows follow the resolved is_door flag
    assert len(doors) == sum(1 for o in catlin_model.openings if o.is_door)


def test_filling_guid_matches_diff_adapter_prediction(catlin_model, catlin_ifc):
    import ifcopenshell

    f = ifcopenshell.open(str(catlin_ifc))
    emitted = {p.GlobalId for p in f.by_type("IfcWindow") + f.by_type("IfcDoor")}
    puid = catlin_model.plan.project.project_uuid
    for opening in catlin_model.openings:
        if opening.kind == "rough_opening":
            continue
        assert derive_guid(puid, opening.uid) in emitted


def test_opening_occurrences_are_assigned_to_stable_product_types(catlin_model, catlin_ifc):
    import ifcopenshell

    f = ifcopenshell.open(str(catlin_ifc))
    typed_occurrences = {occurrence.GlobalId for relation in f.by_type("IfcRelDefinesByType")
                         for occurrence in relation.RelatedObjects}
    expected = {derive_guid(catlin_model.plan.project.project_uuid, opening.uid)
                for opening in catlin_model.openings if opening.type_ref is not None}
    assert expected <= typed_occurrences
    assert len(f.by_type("IfcDoorType")) == len(catlin_model.plan.library.door_types)
    assert len(f.by_type("IfcWindowType")) == len(catlin_model.plan.library.window_types)


def test_openings_survive_the_self_diff_by_global_id(catlin_model, catlin_ifc):
    # A self-export must have no reconciliation work: geometry, type, and identity all round
    # trip through IFC instead of merely avoiding add/delete matches by GlobalId.
    report = build_report(baseline_elems(catlin_model), external_elems(catlin_ifc))
    assert report.substantive() == []


def test_rough_opening_emits_only_the_wall_void(catlin_model, tmp_path):
    import ifcopenshell

    model = deepcopy(catlin_model)
    source = model.openings[0]
    model.openings[0] = replace(source, kind="rough_opening", is_door=False, type_ref=None)
    out = tmp_path / "rough-opening.ifc"
    emit_ifc(model, out, lod="core")

    f = ifcopenshell.open(str(out))
    assert len(f.by_type("IfcOpeningElement")) == len(model.openings)
    filled = [opening for opening in model.openings if opening.kind != "rough_opening"]
    assert len(f.by_type("IfcWindow")) + len(f.by_type("IfcDoor")) == len(filled)
    assert len(f.by_type("IfcRelFillsElement")) == len(filled)


def test_arched_voids_use_vertical_curved_profiles(catlin_model, catlin_ifc):
    """The brick veneer's two segmental reveals — the stricter case, because its circle
    centre sits below the springline rather than on it."""
    import ifcopenshell

    f = ifcopenshell.open(str(catlin_ifc))
    arches = {opening.Name: opening for opening in f.by_type("IfcOpeningElement")
              if opening.Name.startswith("AO-B-BRICK-")}
    assert set(arches) == {"AO-B-BRICK-WIN/void", "AO-B-BRICK-DOOR/void"}
    for opening in arches.values():
        solid = opening.Representation.Representations[0].Items[0]
        assert solid.is_a("IfcExtrudedAreaSolid")
        assert solid.SweptArea.is_a("IfcArbitraryClosedProfileDef")
        outer_curve = solid.SweptArea.OuterCurve
        assert outer_curve.is_a("IfcCompositeCurve")
        arch = outer_curve.Segments[2].ParentCurve
        assert arch.is_a("IfcTrimmedCurve")
        assert arch.BasisCurve.is_a("IfcCircle")
        # Segmental: radius = (half_span^2 + rise^2) / (2 * rise), well past the half-span.
        assert arch.BasisCurve.Radius > 0.0
        assert solid.Position.Axis.DirectionRatios[2] == pytest.approx(0.0)
        assert solid.ExtrudedDirection.DirectionRatios == (0.0, 0.0, 1.0)
    # The void is cut through the wythe it is a reveal in, not the wall behind it.
    veneer = next(w for w in catlin_model.walls if w.tag == "W-B-BRICK")
    for opening in arches.values():
        solid = opening.Representation.Representations[0].Items[0]
        assert solid.Depth == pytest.approx(veneer.thickness_m)


def test_door_types_export_their_authored_operation(catlin_model, catlin_ifc):
    """Without OperationType every door reads as a plain swing in the receiving app."""
    import ifcopenshell

    from typehaus.model.enums import DoorOperation

    f = ifcopenshell.open(str(catlin_ifc))
    operations = {door_type.Name: door_type.OperationType
                  for door_type in f.by_type("IfcDoorType")}
    assert operations["DT-EXT-OVERHEAD192"] == "ROLLINGUP"  # IFC4 has no OVERHEAD_DOOR term
    assert operations["DT-INT-BIFOLD60"] == "FOLDING_TO_LEFT"
    assert operations["DT-EXT-FRENCH60"] == "DOUBLE_DOOR_SINGLE_SWING"
    assert operations["DT-EXT-SLIDE60"] == "SLIDING_TO_LEFT"
    assert operations["DT-EXT-SWING36"] == "SINGLE_SWING_LEFT"
    assert all(door_type.PredefinedType == "DOOR"
               for door_type in f.by_type("IfcDoorType"))
    # Every authored operation must be a member of the closed enum the mapping is keyed on,
    # so a new operation fails here rather than silently at export in front of an architect.
    authored = {door_type.operation for door_type in catlin_model.plan.library.door_types}
    assert authored <= set(DoorOperation)
