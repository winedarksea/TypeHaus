"""FXU24 outdoor drawing dimensions and their connection to Catlin's existing stand."""

import numpy as np
import pytest
from shapely.geometry import Polygon

from typehaus.library.hvac_equipment import GREE_FLEXX_ULTRA_24_AH, GREE_FLEXX_ULTRA_24_OD
from typehaus.model.placeable_symbols import model_parts, place_local
from typehaus.quantities import M_PER_IN
from typehaus.resolve.mep_ports import placed_ports

PRODUCT = GREE_FLEXX_ULTRA_24_OD


@pytest.fixture(scope="module")
def outdoor_parts():
    return model_parts(PRODUCT.model_representation.symbol,
                       *(value.meters for value in (*PRODUCT.footprint, PRODUCT.height)))


def test_published_cabinet_and_projecting_foot_envelopes(outdoor_parts):
    cabinet, = [part for part in outdoor_parts if part.get("role") == "flexx-od:cabinet"]
    assert np.asarray(cabinet["size"])[:2] / M_PER_IN == pytest.approx((39, 14.5625))
    assert (cabinet["center"][2] + cabinet["size"][2] / 2) / M_PER_IN == pytest.approx(37.8125)
    feet = [part for part in outdoor_parts if part.get("role") == "flexx-od:foot"]
    assert len(feet) == 2
    assert [part["size"][1] / M_PER_IN for part in feet] == pytest.approx([16.8125] * 2)
    assert all(part["center"][2] - part["size"][2] / 2 == pytest.approx(0) for part in feet)
    assert len(outdoor_parts) < 30
    triangles = sum(len(part["mesh"]["triangles"]) if "mesh" in part else 12
                    for part in outdoor_parts)
    assert triangles < 3000


def test_fixing_markers_land_over_the_existing_stand_legs(catlin_model_ro, outdoor_parts):
    obj = next(obj for obj in catlin_model_ro.canvas_objects if obj.tag == "EQ-M-HP1-OD")
    local = [part["center"][:2] for part in outdoor_parts
             if part.get("role") == "flexx-od:fixing-marker"]
    assert len(local) == 4
    assert (max(x for x, _ in local) - min(x for x, _ in local)) / M_PER_IN == pytest.approx(29.75)
    depth_pitch = (max(y for _, y in local) - min(y for _, y in local)) / M_PER_IN
    assert depth_pitch == pytest.approx(15.5625)
    world = sorted(place_local(local, obj.position, obj.rotation_degrees))
    legs = sorted((Polygon(solid.outline).centroid.x, Polygon(solid.outline).centroid.y)
                  for solid in catlin_model_ro.solids
                  if solid.tag.startswith("PT-M-HP1-L"))
    assert np.asarray(world) == pytest.approx(np.asarray(legs))


def test_refrigerant_sizes_match_the_indoor_unit_without_claiming_exact_stations(outdoor_parts):
    ports = {port.tag: port for port in PRODUCT.ports}
    indoor = {port.tag: port for port in GREE_FLEXX_ULTRA_24_AH.ports}
    assert set(ports) == {"power", "control", "liquid", "vapor"}
    assert all(not port.is_exact() and port.notes for port in ports.values())
    for tag, diameter in (("liquid", 0.375), ("vapor", 0.75)):
        assert ports[tag].service == indoor[tag].service
        assert ports[tag].connection_size.inches == pytest.approx(diameter)
        assert ports[tag].connection_size == indoor[tag].connection_size
    markers = {part.get("role"): part for part in outdoor_parts}
    for tag, port in ports.items():
        part = markers["flexx-od:" + tag]
        x, y, z = (value.meters for value in port.position)
        assert part["center"][0] + part["size"][0] / 2 == pytest.approx(x)
        assert part["center"][1:] == pytest.approx((y, z))


def test_north_facing_unit_has_west_side_connections_and_front_fan(catlin_model_ro, outdoor_parts):
    obj = next(obj for obj in catlin_model_ro.canvas_objects if obj.tag == "EQ-M-HP1-OD")
    ports = [port for port in placed_ports(catlin_model_ro) if port.equipment_tag == obj.tag]
    assert all(port.direction == pytest.approx((-1, 0, 0)) for port in ports)
    assert all(port.x_m < obj.position[0] for port in ports)
    fan, = [part for part in outdoor_parts if part.get("role") == "flexx-od:fan-recess"]
    fan_xy, = place_local([fan["center"][:2]], obj.position, obj.rotation_degrees)
    assert fan_xy[1] > obj.position[1]
    assert len(obj.recommended_clearances) == 4
    service = obj.recommended_clearances[0]
    assert max(x for x, _ in service) == pytest.approx(min(x for x, _ in obj.footprint))
    assert (max(x for x, _ in service) - min(x for x, _ in service)) / M_PER_IN == pytest.approx(12)


def test_round_guard_and_ports_have_closed_outward_meshes(outdoor_parts):
    for part in outdoor_parts:
        if "mesh" not in part:
            continue
        mesh = part["mesh"]
        points = np.asarray(mesh["positions"])
        corners = points[np.asarray(mesh["triangles"])]
        cross = np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0])
        assert np.all(np.linalg.norm(cross, axis=1) > 0)
        assert np.linalg.norm(np.asarray(mesh["normals"]), axis=1) == pytest.approx(1)
        assert np.sum(np.einsum("ij,ij->i", corners[:, 0],
                                np.cross(corners[:, 1], corners[:, 2]))) > 0
