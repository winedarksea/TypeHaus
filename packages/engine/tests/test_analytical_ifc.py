"""The IFC4 structural analysis view, against the hand-solvable portal frame.

The frame is the oracle for *what the graph says*; this file is the oracle for *what the
IFC says about it* — one analysis model, three members, four nodes, two fixed bases, a
released beam, and every action reaching a structural item. A load in the file that no
``IfcRelConnectsStructuralActivity`` connects is a load SAP2000 does not import, which is
the failure this suite exists to catch.
"""

from __future__ import annotations

import uuid
from dataclasses import replace
from pathlib import Path

import ifcopenshell
import ifcopenshell.util.element as ue
import ifcopenshell.validate
import pytest
from analytical_fixtures import DEAD_N_M, WIND_N, portal_frame

from typehaus.analytical.graph import Fixity, Support
from typehaus.emit.ifc.analytical import PSET_ANALYTICAL, write_standalone

PROJECT_UUID = uuid.uuid5(uuid.NAMESPACE_URL, "typehaus/test/analytical")


@pytest.fixture(scope="module")
def portal_ifc(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("analytical") / "portal.ifc"
    return write_standalone(portal_frame(), out, PROJECT_UUID)


@pytest.fixture(scope="module")
def portal(portal_ifc: Path):
    return ifcopenshell.open(str(portal_ifc))


def test_one_analysis_model_grouping_every_item(portal) -> None:
    models = portal.by_type("IfcStructuralAnalysisModel")
    assert len(models) == 1
    analysis = models[0]
    assert analysis.PredefinedType == "LOADING_3D"
    grouped = {obj for rel in analysis.IsGroupedBy for obj in rel.RelatedObjects}
    members = set(portal.by_type("IfcStructuralCurveMember"))
    connections = set(portal.by_type("IfcStructuralPointConnection"))
    assert members <= grouped and connections <= grouped
    assert analysis.ServicesBuildings, "the group must hang off the building"


def test_members_and_connections(portal) -> None:
    members = portal.by_type("IfcStructuralCurveMember")
    connections = portal.by_type("IfcStructuralPointConnection")
    assert len(members) == 3
    assert len(connections) == 4
    fixed = [c for c in connections if c.AppliedCondition is not None]
    assert len(fixed) == 2
    for connection in fixed:
        condition = connection.AppliedCondition
        assert condition.is_a("IfcBoundaryNodeCondition")
        assert all(getattr(condition, dof).wrappedValue is True for dof in (
            "TranslationalStiffnessX", "TranslationalStiffnessY",
            "TranslationalStiffnessZ", "RotationalStiffnessX",
            "RotationalStiffnessY", "RotationalStiffnessZ"))


def test_the_columns_are_rigid_and_the_beam_is_pin_joined(portal) -> None:
    by_name = {m.Name: m for m in portal.by_type("IfcStructuralCurveMember")}
    assert by_name["BM-1"].PredefinedType == "PIN_JOINED_MEMBER"
    assert by_name["PT-W"].PredefinedType == "RIGID_JOINED_MEMBER"
    # A column's local z cannot be its own axis, so it takes global X; the beam keeps Z.
    assert tuple(by_name["PT-W"].Axis.DirectionRatios) == (1.0, 0.0, 0.0)
    assert tuple(by_name["BM-1"].Axis.DirectionRatios) == (0.0, 0.0, 1.0)


def test_the_beam_ends_carry_their_moment_release(portal) -> None:
    beam = next(m for m in portal.by_type("IfcStructuralCurveMember") if m.Name == "BM-1")
    rels = [r for r in portal.by_type("IfcRelConnectsStructuralMember")
            if r.RelatingStructuralMember == beam]
    assert len(rels) == 2
    for rel in rels:
        condition = rel.AppliedCondition
        assert condition is not None, "a released end with no condition is a rigid end"
        assert condition.RotationalStiffnessX.wrappedValue is False
        assert condition.RotationalStiffnessY.wrappedValue is False
        assert condition.RotationalStiffnessZ.wrappedValue is False
        assert condition.TranslationalStiffnessZ.wrappedValue is True


def test_the_curve_members_carry_an_axis_polyline_in_metres(portal) -> None:
    beam = next(m for m in portal.by_type("IfcStructuralCurveMember") if m.Name == "BM-1")
    axis = next(r for r in beam.Representation.Representations
                if r.RepresentationIdentifier == "Axis")
    assert axis.RepresentationType == "Curve3D"
    polyline = axis.Items[0]
    assert polyline.is_a("IfcPolyline") and len(polyline.Points) == 2
    assert tuple(polyline.Points[0].Coordinates) == (0.0, 0.0, 3.0)
    assert tuple(polyline.Points[1].Coordinates) == (4.0, 0.0, 3.0)
    # And the IFC4 SAM's own topology beside it.
    edge = next(r for r in beam.Representation.Representations
                if r.is_a("IfcTopologyRepresentation"))
    assert edge.RepresentationType == "Edge"


def test_load_cases_and_their_actions(portal) -> None:
    cases = {c.Name: c for c in portal.by_type("IfcStructuralLoadCase")}
    assert set(cases) == {"dead", "wind"}
    assert (cases["dead"].ActionType, cases["dead"].ActionSource) == (
        "PERMANENT_G", "DEAD_LOAD_G")
    assert (cases["wind"].ActionType, cases["wind"].ActionSource) == (
        "VARIABLE_Q", "WIND_W")
    analysis = portal.by_type("IfcStructuralAnalysisModel")[0]
    assert set(analysis.LoadedBy) == set(cases.values())
    assert not analysis.HasResults

    linear = portal.by_type("IfcStructuralLinearAction")
    assert len(linear) == 1
    assert linear[0].AppliedLoad.LinearForceZ == pytest.approx(-DEAD_N_M)
    assert linear[0].GlobalOrLocal == "GLOBAL_COORDS"
    assert linear[0].ProjectedOrTrue == "TRUE_LENGTH"

    points = portal.by_type("IfcStructuralPointAction")
    assert len(points) == 2
    assert all(p.AppliedLoad.ForceX == pytest.approx(WIND_N) for p in points)


def test_every_action_reaches_a_structural_item(portal) -> None:
    actions = portal.by_type("IfcStructuralAction")
    assert actions
    connected = {rel.RelatedStructuralActivity
                 for rel in portal.by_type("IfcRelConnectsStructuralActivity")}
    assert set(actions) <= connected
    for rel in portal.by_type("IfcRelConnectsStructuralActivity"):
        assert rel.RelatingElement.is_a("IfcStructuralItem")


def test_the_units_cover_force_pressure_and_line_load(portal) -> None:
    units = portal.by_type("IfcUnitAssignment")[0].Units
    si = {u.UnitType for u in units if u.is_a("IfcSIUnit")}
    derived = {u.UnitType for u in units if u.is_a("IfcDerivedUnit")}
    assert {"FORCEUNIT", "PRESSUREUNIT", "MASSUNIT", "LENGTHUNIT"} <= si
    assert {"LINEARFORCEUNIT", "PLANARFORCEUNIT", "TORQUEUNIT"} <= derived


def test_members_carry_their_section_and_their_pset(portal) -> None:
    by_name = {m.Name: m for m in portal.by_type("IfcStructuralCurveMember")}
    beam_pset = ue.get_psets(by_name["BM-1"])[PSET_ANALYTICAL]
    assert beam_pset["category"] == "beam"
    assert beam_pset["releases"] == "moment released at i and j"
    assert "glulam" in beam_pset["e_basis"]
    column_pset = ue.get_psets(by_name["PT-W"])[PSET_ANALYTICAL]
    assert column_pset["item_ids"] == "deck_post/PT-W"
    assert column_pset["releases"] == "rigidly joined"

    # One profile set per distinct section, shared by the two identical columns.
    profile_sets = {ue.get_material(m) for m in by_name.values()}
    assert len(profile_sets) == 2
    assert ue.get_material(by_name["PT-W"]) == ue.get_material(by_name["PT-E"])
    assert by_name["BM-1"].HasAssociations


def test_a_partly_restrained_support_writes_its_own_rotations(tmp_path: Path) -> None:
    """A beam end pinned on a wall is held against roll and free in bending.

    ``Support.restrained_rotations()``, not the fixity: releasing the roll as well would
    make the node a mechanism, and the condition has to say which axis is which.
    """
    frame = portal_frame()
    supports = (Support("N-W-BASE", Fixity.PINNED, "test: seat holds it against roll",
                        rotations=(True, False, False)), frame.supports[1])
    model = replace(frame, supports=supports)
    out = write_standalone(model, tmp_path / "rolled.ifc", PROJECT_UUID)
    f = ifcopenshell.open(str(out))
    connection = next(c for c in f.by_type("IfcStructuralPointConnection")
                      if c.Name == "N-W-BASE")
    condition = connection.AppliedCondition
    assert condition.RotationalStiffnessX.wrappedValue is True
    assert condition.RotationalStiffnessY.wrappedValue is False
    assert condition.RotationalStiffnessZ.wrappedValue is False
    assert all(getattr(condition, dof).wrappedValue is True for dof in (
        "TranslationalStiffnessX", "TranslationalStiffnessY", "TranslationalStiffnessZ"))
    assert ue.get_psets(connection)[PSET_ANALYTICAL]["restrained_rotations"] == "X"


def test_the_supported_connections_state_their_basis(portal) -> None:
    fixed = [c for c in portal.by_type("IfcStructuralPointConnection")
             if c.AppliedCondition is not None]
    for connection in fixed:
        pset = ue.get_psets(connection)[PSET_ANALYTICAL]
        assert pset["fixity"] == "fixed"
        assert pset["basis"], "a claim with no basis is a claim nobody can disagree with"


def test_the_file_validates_against_the_express_rules(portal_ifc: Path) -> None:
    logger = ifcopenshell.validate.json_logger()
    ifcopenshell.validate.validate(str(portal_ifc), logger, express_rules=True)
    assert not logger.statements, logger.statements


def test_two_writes_are_byte_identical(tmp_path: Path) -> None:
    first = write_standalone(portal_frame(), tmp_path / "a.ifc", PROJECT_UUID)
    second = write_standalone(portal_frame(), tmp_path / "b.ifc", PROJECT_UUID)
    assert first.read_bytes() == second.read_bytes()
