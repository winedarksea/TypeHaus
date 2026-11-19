"""Radiant heater shape, installation clearance and actual bracket support."""

from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest

from typehaus.checks.advisory.backing import wall_backing_bearing
from typehaus.checks.advisory.backing_fixings import wall_fixing_support
from typehaus.model.placeable_symbols import model_parts

INCH_M = 0.0254
HEATER_TAG = "EQ-G-HEATER"


def test_radiant_bar_has_an_open_tilted_reflector_and_rear_standoff():
    parts = model_parts("infrared-heater", 34.6 * INCH_M, 14 * INCH_M, 8 * INCH_M)
    back = parts[0]
    assert back["size"][0] / INCH_M == pytest.approx(34.6)
    assert back["size"][2] / INCH_M == pytest.approx((7.69 + 0.08) / np.sqrt(2))
    # The visible tube runs level, inside a tray rather than on an opaque box face.
    tube, = [part for part in parts if part["color"] == "brass"]
    assert tube["size"][0] / INCH_M == pytest.approx(30)
    tube_normals = np.asarray(tube["mesh"]["normals"])
    assert any(np.allclose(normal, (0, -1 / np.sqrt(2), -1 / np.sqrt(2)))
               for normal in tube_normals)
    housing_rear = max(part["center"][1] + part["size"][1] / 2
                       for part in parts if "mesh" in part)
    assert (7 * INCH_M - housing_rear) / INCH_M == pytest.approx(6)
    wall_plates = [part for part in parts if part["shape"] == "box"
                   and part["size"][2] == pytest.approx(3 * INCH_M)]
    assert len(wall_plates) == 2
    assert sorted(part["center"][0] / INCH_M for part in wall_plates) == pytest.approx(
        [-5.95, 5.95])


def test_installed_heater_clears_ceiling_and_workbench(catlin_model_ro):
    model = catlin_model_ro
    objects = {obj.tag: obj for obj in model.canvas_objects}
    heater = objects[HEATER_TAG]
    bench = objects["FURN-G-WORKBENCH"]
    wall = next(wall for wall in model.walls if wall.tag == heater.attachment_wall)
    product = next(row for row in model.plan.library.equipment_types
                   if row.tag == heater.type_ref)
    assert heater.mount.elevation.meters / INCH_M == pytest.approx(96)
    # 96" AFF where it hangs: the floor falls 1/8"/ft to the door (decision #138), so the
    # body stands that much nearer the plate than the 18" it had over the door-line floor.
    slab = next(s for s in model.solids if s.tag == "SL-G-FLOOR")
    rise = slab.top_at(*heater.position) - slab.z1_m
    assert (wall.z1_m - heater.body_z1_m) / INCH_M == pytest.approx(18 - rise / INCH_M)
    assert heater.body_z0_m - bench.body_z1_m >= 39.4 * INCH_M
    assert heater.position[1] == pytest.approx(bench.position[1], abs=1e-5)
    assert product.resistance_heating_btuh == 5118
    assert product.supplemental_heat
    circuit = next(row for row in model.plan.library.circuits if row.tag == heater.circuit)
    assert circuit.load_va == 1500 and circuit.breaker_amps == 20 and circuit.gfci
    outlet = model.plan.by_tag("ED-G-HEATER-RC")
    assert outlet.circuit == circuit.tag
    assert outlet.mount.elevation.meters == pytest.approx(90 * INCH_M)
    assert sorted(x.meters / INCH_M for x, _ in product.wall_fixing_points) == pytest.approx(
        [-6.5, -5.4, 5.4, 6.5])
    assert not next(room for room in model.rooms if room.tag == heater.room).conditioned


@pytest.mark.parametrize("remove_backing", [False, True])
def test_all_four_equipment_fixings_require_the_emitted_blocks(catlin_model_ro, remove_backing):
    model = catlin_model_ro
    heater = next(obj for obj in model.canvas_objects if obj.tag == HEATER_TAG)
    wall = next(wall for wall in model.walls if wall.tag == heater.attachment_wall)
    if remove_backing:
        wall = replace(wall, members=tuple(member for member in wall.members
                                           if not member.child_key.startswith("backing-")))
    context = SimpleNamespace(plan=model.plan,
                              model=SimpleNamespace(canvas_objects=(heater,), walls=(wall,)))
    findings = wall_fixing_support(context)
    assert len(findings) == 4
    assert all(finding.result.value == ("fail" if remove_backing else "pass")
               for finding in findings), findings
    if not remove_backing:
        assert all("backing-" in finding.message for finding in findings)
        bearing = wall_backing_bearing(context)
        assert len(bearing) == 1 and bearing[0].result.value == "pass", bearing
