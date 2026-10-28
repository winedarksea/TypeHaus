"""Opening clearance uses complete bodies on the finish face, not just device centers."""

from dataclasses import replace
from math import hypot

import pytest

from typehaus.checks.mep.electrical_openings import wall_device_opening
from typehaus.checks.registry import CheckContext, JurisdictionProfile, Preferences
from typehaus.findings import Result, Severity
from typehaus.model import DeviceKind, ElectricalDevice, Mount, MountKind, PlanModel, m, pt
from typehaus.resolve.model import (
    ResolvedCanvasObject,
    ResolvedModel,
    ResolvedOpening,
    ResolvedWall,
)


@pytest.fixture
def context(project):
    plan = PlanModel(project=project, elements={"upper": (
        ElectricalDevice(tag="DEVICE", kind=DeviceKind.RECEPTACLE, position=pt(m(2), m(0.3)),
                         mount=Mount(kind=MountKind.WALL)),)})
    wall = ResolvedWall(uid="wall", tag="WALL", storey="upper", assembly="test",
                        axis=((0, 0), (5, 0)), layers=(), z0_m=2.5, z1_m=6,
                        plate_base_z_m=3)
    opening = ResolvedOpening(uid="door", tag="OPENING", host_wall="WALL", type_ref="test",
                              width_m=1, height_m=2, sill_m=0, center_along_m=2,
                              kind="door", is_door=True)
    body = ResolvedCanvasObject(
        uid="device", tag="DEVICE", storey="upper", domain="electrical",
        kind="ElectricalDevice", type_ref=None, room=None, position=(2, 0.3), z_m=3.4,
        rotation_degrees=0, footprint=((1.8, 0.2), (2.2, 0.2), (2.2, 0.4), (1.8, 0.4)),
        body_z0_m=3.4, body_z1_m=3.6, attachment_wall="WALL")
    model = ResolvedModel(plan=plan, walls=[wall], openings=[opening], canvas_objects=[body])
    return CheckContext(plan=plan, model=model, preferences=Preferences(),
                        profile=JurisdictionProfile("test", "test", "", "", ""))


@pytest.mark.parametrize("kind", [DeviceKind.RECEPTACLE, DeviceKind.SWITCH, DeviceKind.LIGHT])
def test_finish_face_devices_inside_door_fail(context, kind):
    element = context.plan.elements["upper"][0].model_copy(update={"kind": kind})
    context.plan = context.plan.with_elements("upper", (element,))
    finding, = wall_device_opening(context)
    assert finding.result == Result.FAIL
    assert finding.severity == Severity.WARN
    assert finding.element_tags == ("DEVICE", "OPENING", "WALL")


@pytest.mark.parametrize("station, expected", [(2.6, Result.FAIL), (2.7, Result.PASS)])
def test_body_edge_counts_even_when_center_is_outside(context, station, expected):
    body = context.model.canvas_objects[0]
    context.model.canvas_objects = [replace(
        body, position=(station, 0.3),
        footprint=tuple((x + station - 2, y) for x, y in body.footprint))]
    assert wall_device_opening(context)[0].result == expected


@pytest.mark.parametrize("axis", [((5, 0), (0, 0)), ((1, 2), (4, 6))])
def test_station_projection_follows_reversed_and_diagonal_walls(context, axis):
    (sx, sy), (ex, ey) = axis
    length = hypot(ex - sx, ey - sy)
    ux, uy = (ex - sx) / length, (ey - sy) / length
    body = context.model.canvas_objects[0]
    footprint = tuple((sx + ux * s - uy * n, sy + uy * s + ux * n)
                      for s, n in body.footprint)
    context.model.walls = [replace(context.model.walls[0], axis=axis)]
    context.model.canvas_objects = [replace(body, footprint=footprint)]
    assert wall_device_opening(context)[0].result == Result.FAIL


@pytest.mark.parametrize("bottom, top, expected", [
    (3.4, 3.6, Result.PASS),  # Below the sill.
    (4.4, 4.6, Result.FAIL),
    (5.0, 5.2, Result.PASS),  # Exact contact at the head is clear.
])
def test_window_height_uses_framing_datum_not_extended_wall_base(context, bottom, top, expected):
    context.model.openings = [replace(context.model.openings[0], kind="window", is_door=False,
                                      sill_m=1, height_m=1)]
    context.model.canvas_objects = [replace(context.model.canvas_objects[0],
                                            body_z0_m=bottom, body_z1_m=top)]
    assert wall_device_opening(context)[0].result == expected


@pytest.mark.parametrize("missing", ["body", "height", "footprint", "host", "wall", "axis"])
def test_unresolved_body_or_host_is_unknown(context, missing):
    body = context.model.canvas_objects[0]
    if missing == "body":
        context.model.canvas_objects = []
    elif missing == "height":
        context.model.canvas_objects = [replace(body, body_z1_m=None)]
    elif missing == "footprint":
        context.model.canvas_objects = [replace(body, footprint=())]
    elif missing == "host":
        context.model.canvas_objects = [replace(body, attachment_wall=None)]
    elif missing == "wall":
        context.model.walls = []
    else:
        context.model.walls = [replace(context.model.walls[0], axis=((0, 0), (0, 0)))]
    assert wall_device_opening(context)[0].result == Result.UNKNOWN


def test_curved_opening_is_not_graded_as_a_rectangle(context):
    context.model.openings = [replace(context.model.openings[0], arch_rise_m=0.5)]
    assert wall_device_opening(context)[0].result == Result.UNKNOWN


def test_invalid_opening_geometry_is_unknown(context):
    context.model.openings = [replace(context.model.openings[0], height_m=float("nan"))]
    assert wall_device_opening(context)[0].result == Result.UNKNOWN


@pytest.mark.parametrize("mount", [MountKind.FLOOR, MountKind.CEILING])
def test_non_wall_devices_are_not_applicable(context, mount):
    element = context.plan.elements["upper"][0].model_copy(update={"mount": Mount(kind=mount)})
    context.plan = context.plan.with_elements("upper", (element,))
    assert wall_device_opening(context)[0].result == Result.NOT_APPLICABLE


def test_openings_on_other_walls_do_not_conflict(context):
    context.model.openings = [replace(context.model.openings[0], host_wall="OTHER-WALL")]
    assert wall_device_opening(context)[0].result == Result.PASS
