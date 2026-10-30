"""A fixture connection is a 3D endpoint of a serving run on the declared system."""

from types import SimpleNamespace

import pytest

from typehaus.checks.mep.fixture_ports import fixture_port_connection
from typehaus.checks.registry import Preferences
from typehaus.findings import Result
from typehaus.model import Fixture, FixtureType, Library, Mount, PortCertainty, Service, ServicePort, deg, inch, pt
from typehaus.resolve.mep_sleeves import _expected_drain_point, expected_port_point


@pytest.fixture
def connection():
    fixture = Fixture(tag="FX", type_ref="TYPE", position=pt(inch(100), inch(200)), rotation=deg(90))
    port = ServicePort(tag="DRAIN", service=Service.DRAIN,
                       position=(inch(2), inch(10), inch(20)), certainty=PortCertainty.EXACT)
    fixture_type = FixtureType(tag="TYPE", name="Test vanity", footprint=(inch(24), inch(18)),
                               height=inch(40), ports=(port,))
    library = Library(fixture_types=(fixture_type,))
    plan = SimpleNamespace(library=library, by_tag=lambda tag: fixture,
                           elements_of_kind=lambda kind: (fixture,),
                           storeys=(SimpleNamespace(tag="main", elevation=inch(120)),),
                           storey_elements=lambda tag: (fixture,))
    model = SimpleNamespace(plan=plan, canvas_objects=[], wall=lambda tag: None, pipe_runs=[])
    run = SimpleNamespace(tag="RUN", serves=("FX",), system="drain",
                          path=((inch(90).meters, inch(202).meters), (0, 0)),
                          z_m=(inch(140).meters, 0))
    model.pipe_runs.append(run)
    return SimpleNamespace(plan=plan, model=model, preferences=Preferences()), fixture, fixture_type, run


def test_floor_type_port_is_rotated_without_snapping_to_a_wall(connection):
    ctx, fixture, _, _ = connection
    assert _expected_drain_point(ctx.model, fixture.tag) == pytest.approx((90*.0254, 202*.0254))


def test_authored_outlet_wins_over_port(connection):
    ctx, fixture, _, _ = connection
    object.__setattr__(fixture, "drain_position", pt(inch(10), inch(20)))
    assert _expected_drain_point(ctx.model, fixture.tag) == fixture.drain_position.xy_m


@pytest.mark.parametrize("mount_in, expected_in", [(None, 20), (8, 28)])
def test_port_z_is_relative_to_storey_and_mount_base(connection, mount_in, expected_in):
    ctx, fixture, fixture_type, _ = connection
    object.__setattr__(fixture_type, "mount", Mount(elevation=inch(mount_in) if mount_in else None))
    assert expected_port_point(ctx.model, fixture.tag, Service.DRAIN)[2] == pytest.approx(expected_in*.0254)


def test_exact_connection_passes_across_storey_datums(connection):
    ctx, *_ = connection
    assert [f.result for f in fixture_port_connection(ctx)] == [Result.PASS]


@pytest.mark.parametrize("fault", ["plan", "elevation", "no_elevation", "interior_vertex"])
def test_exact_port_requires_an_endpoint_in_plan_and_z(connection, fault):
    ctx, _, _, run = connection
    if fault == "plan":
        run.path = ((inch(92).meters, inch(202).meters), (0, 0))
    elif fault == "elevation":
        run.z_m = (inch(145).meters, 0)
    elif fault == "no_elevation":
        run.z_m = ()
    else:
        run.path = ((0, 0), run.path[0], (1, 1))
        run.z_m = (0, run.z_m[0], 0)
    findings = fixture_port_connection(ctx)
    assert findings[0].result is Result.FAIL
    assert "endpoint" in findings[0].message


def test_approximate_station_cannot_establish_an_exact_connection(connection):
    ctx, _, fixture_type, _ = connection
    port = fixture_type.ports[0].model_copy(update={"certainty": PortCertainty.APPROXIMATE})
    object.__setattr__(fixture_type, "ports", (port,))
    assert fixture_port_connection(ctx)[0].result is Result.UNKNOWN


def test_missing_service_is_left_to_supply_coverage(connection):
    ctx, _, _, run = connection
    run.system = "water_hot"
    assert fixture_port_connection(ctx)[0].result is Result.NOT_APPLICABLE


def test_authored_drain_drift_is_reported_even_without_a_run(connection):
    ctx, fixture, _, _ = connection
    object.__setattr__(fixture, "drain_position", pt(inch(100), inch(202)))
    ctx.model.pipe_runs.clear()
    findings = fixture_port_connection(ctx)
    assert findings[0].result is Result.FAIL
    assert "drifts" in findings[0].message


def test_resolved_finished_floor_is_included_in_storey_relative_port_z(connection):
    ctx, fixture, _, run = connection
    ctx.model.canvas_objects = [SimpleNamespace(
        uid=fixture.uid, tag=fixture.tag, position=fixture.position.xy_m,
        rotation_degrees=90, storey="main", z_m=inch(121.5).meters,
    )]
    assert expected_port_point(ctx.model, fixture.tag, Service.DRAIN)[2] == pytest.approx(
        inch(21.5).meters)
    run.z_m = (inch(141.5).meters, 0)
    assert fixture_port_connection(ctx)[0].result is Result.PASS


def test_part_quantity_counts_in_addition_to_primary_fixture():
    from typehaus.model import Library, Product, ProductPart
    from typehaus.takeoff.placeables import placeables_takeoff

    fixture_type = FixtureType(
        tag="DOUBLE", name="Double bowl assembly", footprint=(inch(60), inch(18)),
        height=inch(40), parts=(ProductPart(role="faucet", product_ref="MIXER", quantity=2),),
    )
    objects = [SimpleNamespace(tag=f"FX-{i}", type_ref="DOUBLE", kind="Fixture",
                               domain="plumbing", storey="main") for i in range(3)]
    model = SimpleNamespace(canvas_objects=objects, plan=SimpleNamespace(
        library=Library(fixture_types=(fixture_type,), products=(Product(tag="MIXER", brand="Test"),))))
    rows = {row["type"]: row for row in placeables_takeoff(model)}
    assert rows["DOUBLE"]["count"] == 3
    assert rows["MIXER"]["count"] == 6
    assert rows["MIXER"]["roles"] == ["faucet"]
