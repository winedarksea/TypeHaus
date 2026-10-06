"""A rated lateral plate needs two wood attachment faces and blocking up to the deck."""

from dataclasses import replace

import pytest

from typehaus import Connector, ConnectorKind, PlanModel, Project, Site, ft, pt
from typehaus.engineering.collector_attachment import collector_attachment_missing
from typehaus.quantities import M_PER_IN
from typehaus.resolve.connector_geometry.mesh import transform_mesh
from typehaus.resolve.connector_geometry.placement import solid_with_body
from typehaus.resolve.connector_geometry.ties import tie_mesh
from typehaus.resolve.model import FramedMember, ResolvedModel, ResolvedRoof, ResolvedSolid


@pytest.fixture
def collector_model():
    plan = PlanModel(project=Project(
        name="collector", project_uuid="00000000-0000-4000-8000-000000000001",
        site=Site(lat=0, lon=0, elevation=ft(0))))
    half_width = 2.75 * M_PER_IN
    beam = ResolvedSolid(
        uid="beam", tag="BM", storey="main", category="beam",
        outline=[(-half_width, 0), (half_width, 0), (half_width, 2), (-half_width, 2)],
        z0_m=-12 * M_PER_IN, z1_m=0)
    block = FramedMember(
        parent_uid="roof", child_key="eave-block", category="blocking", profile="5.5x13.25",
        p0=(0, 0), p1=(0, 2), z0_m=0, z1_m=13.25 * M_PER_IN, length_m=2)
    roof = ResolvedRoof(
        uid="roof", tag="RF", storey="main", form="shed",
        footprint=[(-2, 0), (2, 0), (2, 2), (-2, 2)],
        eave_z_m=0.24, ridge_z_m=0.36, ridge_direction="y", assembly="roof",
        surface_area_m2=8, members=(block,))
    clip = Connector(tag="CN", kind=ConnectorKind.TENSION_TIE,
                     position=pt(ft(0), ft(1 / 0.3048)), elevation=ft(0),
                     size="LTP4", axis="y", connects=("RF", "BM"))
    plate = solid_with_body(
        ResolvedSolid(uid="plate", tag="CN", storey="main", category="connector",
                      outline=[], z0_m=0, z1_m=0, product="LTP4"),
        transform_mesh(tie_mesh("LTP4"), origin_m=(half_width, 1, 0),
                       x_axis=(0, 1, 0), y_axis=(-1, 0, 0)))
    return ResolvedModel(plan=plan, solids=[beam, plate], roofs=[roof]), clip


def test_blocking_and_plate_share_both_attachment_faces(collector_model):
    model, clip = collector_model
    assert not collector_attachment_missing(model, "RF", "BM", [clip])


@pytest.mark.parametrize("problem", ["absent", "short", "narrow", "raised", "misses_end"])
def test_missing_or_misplaced_blocking_cannot_credit_a_rated_plate(collector_model, problem):
    model, clip = collector_model
    roof = model.roofs[0]
    block = roof.members[0]
    changes = {
        "short": {"z1_m": 0.15},
        "narrow": {"profile": "2x12"},
        "raised": {"z0_m": M_PER_IN},
        "misses_end": {"p1": (0, 1.01), "length_m": 1.01},
    }
    model.roofs[0] = replace(roof, members=(() if problem == "absent" else (
        replace(block, **changes[problem]),)))
    missing = collector_attachment_missing(model, "RF", "BM", [clip])
    assert len(missing) == 1
    assert "CN: eave blocking" in missing[0]


def test_a_plate_above_the_header_cannot_credit_otherwise_valid_blocking(collector_model):
    model, clip = collector_model
    plate = model.solids[1]
    model.solids[1] = solid_with_body(
        plate, transform_mesh(plate.body_mesh, origin_m=(0, 0, 0.1)))
    assert collector_attachment_missing(model, "RF", "BM", [clip])
