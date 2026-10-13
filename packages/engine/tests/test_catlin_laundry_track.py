"""Laundry placement, service clearances, and task sightlines in the real house."""

from types import SimpleNamespace

import pytest
from shapely.geometry import LineString, Point, Polygon, box

from typehaus.checks.mep.framing_envelope import band_over, legs, member_footprint, z_overlap
from typehaus.checks.mep.pockets import _pocket_bands
from typehaus.model.placeable_symbols import place_local
from typehaus.model.placeable_symbols._track_lighting import head_direction, head_lens
from typehaus.takeoff.lighting import light_run_takeoff, lighting_controls

INCH = 0.0254


def _objects(model):
    return {o.tag: o for o in model.canvas_objects}


def _overlap(a0, a1, b0, b1):
    return min(a1, b1) - max(a0, b0) > 1e-7


def test_rail_is_flush_and_supply_is_accessible_on_the_laundry_wall(catlin_model_ro):
    objects = _objects(catlin_model_ro)
    track, supply = objects["ED-M-LAUNDRY-TRACK"], objects["ED-M-LAUNDRY-PSU"]
    assert track.uid == "QTM000SAAA"
    assert track.position == pytest.approx((130.7 * INCH, 258 * INCH))
    assert track.body_z1_m == pytest.approx(108 * INCH)
    assert supply.body_z0_m == pytest.approx(84 * INCH)
    assert supply.position[1] == pytest.approx(257 * INCH)
    assert supply.attachment_wall == "W-M-BA2E" and supply.attachment_face == "left"
    assert supply.body_z0_m > objects["FX-M-LAUNDRY"].body_z1_m
    assert supply.body_z1_m < track.body_z0_m
    # The cover faces the laundry aisle; the enclosure remains north of the machine face.
    assert min(y for _, y in supply.footprint) > 249 * INCH
    feed = next(c for c in catlin_model_ro.conduits if c.tag == "CR-M-LAUNDRY-24V")
    assert feed.storey == "main" and feed.service == "power_24"
    assert feed.path[-1] == pytest.approx((112.7 * INCH, 258 * INCH))
    row = next(r for r in lighting_controls(catlin_model_ro) if r["tag"] == track.tag)
    assert row["circuit"] == "CKT-LT-MAIN" and row["switches"] == ["ED-M-LAUNDRY-SW"]
    psu = next(r for r in light_run_takeoff(catlin_model_ro)["supplies"] if r["psu"] == supply.tag)
    assert psu["connected_watts"] == 22 and psu["required_watts"] == 27.5 and psu["adequate"]


def test_track_and_supply_clear_bodies_walls_pocket_and_ceiling_services(catlin_model_ro):
    model = catlin_model_ro
    objects = _objects(model)
    installed = (objects["ED-M-LAUNDRY-TRACK"], objects["ED-M-LAUNDRY-PSU"])
    envelopes = legs(model)
    for item in installed:
        footprint = Polygon(item.footprint)
        for tag in ("FX-M-LAUNDRY", "FX-M-LAUNDRY-SINK", "FURN-M-LAUNDRY-RACK"):
            other = objects[tag]
            assert not (footprint.intersection(Polygon(other.footprint)).area > 1e-8
                        and _overlap(item.body_z0_m, item.body_z1_m,
                                     other.body_z0_m, other.body_z1_m)), (item.tag, tag)
        for wall in model.walls:
            if wall.storey != "main" or not _overlap(item.body_z0_m, item.body_z1_m,
                                                     wall.z0_m, wall.z1_m):
                continue
            assert all(footprint.intersection(Polygon(layer.polygon)).area < 1e-8
                       for layer in wall.layers), (item.tag, wall.tag)
        for leg in envelopes:
            if leg.tag == "CR-M-LAUNDRY-24V":
                continue  # this feed intentionally terminates at both components
            band = band_over(leg, footprint)
            assert band is None or z_overlap(leg, band, item.body_z0_m, item.body_z1_m) <= 1e-7, \
                (item.tag, leg.tag)
    for member in model.all_members():
        solid = member_footprint(member)
        if solid is None:
            continue
        polygon, z0, z1 = solid
        for item in installed:
            assert not (_overlap(z0, z1, item.body_z0_m, item.body_z1_m)
                        and polygon.intersection(Polygon(item.footprint)).area > 1e-8), \
                (item.tag, member.tag)
    bands = list(_pocket_bands(SimpleNamespace(model=model, plan=model.plan)))
    laundry = [b for b in bands if b[0].tag == "D-M-LAUN"]
    assert laundry
    assert all(not Polygon(item.footprint).intersects(band)
               or not _overlap(item.body_z0_m, item.body_z1_m, *height)
               for item in installed for _, _, band, height in laundry)


@pytest.mark.parametrize("deployed", [False, True])
def test_both_optical_axes_reach_tasks_with_rack_stowed_or_deployed(catlin_model_ro, deployed):
    model = catlin_model_ro
    objects = _objects(model)
    item = objects["ED-M-LAUNDRY-TRACK"]
    spec = next(t.track_lighting for t in model.plan.library.electrical_device_types
                if t.tag == item.type_ref)
    assert spec.channel == 1
    tower, sink, rack = (objects[t] for t in
                         ("FX-M-LAUNDRY", "FX-M-LAUNDRY-SINK", "FURN-M-LAUNDRY-RACK"))
    targets = ((115.83 * INCH, max(y for _, y in tower.footprint),
                (tower.body_z0_m + tower.body_z1_m) / 2),
               (145.55 * INCH, 240 * INCH, sink.body_z0_m + 34 * INCH))
    rack_bounds = Polygon(rack.footprint).bounds
    rack_body = (box(rack_bounds[0] - 16 * INCH, rack_bounds[1],
                     rack_bounds[2], rack_bounds[3]) if deployed else Polygon(rack.footprint))
    for head, target in zip(spec.heads, targets, strict=True):
        local = head_lens(spec, head)
        xy = place_local([local[:2]], item.position, item.rotation_degrees)[0]
        lens = (*xy, item.body_z1_m + local[2])
        direction = head_direction(head)
        distance = (target[2] - lens[2]) / direction[2]
        assert tuple(lens[i] + distance * direction[i] for i in range(3)) \
            == pytest.approx(target, abs=0.01 * INCH)
        for polygon, z0, z1 in ((Polygon(tower.footprint), tower.body_z0_m, tower.body_z1_m),
                                (rack_body, rack.body_z0_m, rack.body_z1_m)):
            # Clip the axis exactly to the obstruction's height band, excluding the task face.
            ts = sorted(((z0 - lens[2]) / (target[2] - lens[2]),
                         (z1 - lens[2]) / (target[2] - lens[2])))
            low, high = max(0, ts[0]), min(1 - 1e-4, ts[1])
            if low >= high:
                continue
            points = [tuple(lens[i] + t * (target[i] - lens[i]) for i in (0, 1))
                      for t in (low, high)]
            axis = LineString(points) if points[0] != points[1] else Point(points[0])
            assert not axis.intersects(polygon)


def test_ifc_preserves_the_fixture_identity_and_configured_hardware(catlin_ifc_path):
    import ifcopenshell
    from ifcopenshell.util.element import get_psets

    f = ifcopenshell.open(str(catlin_ifc_path))
    item = next(e for e in f.by_type("IfcLightFixture") if e.Name == "ED-M-LAUNDRY-TRACK")
    assert get_psets(item)["TypeHaus_Identity"]["uid"] == "QTM000SAAA"
    lighting = get_psets(item)["TypeHaus_Lighting"]
    assert lighting["track_system"] == "magnetic_24v" and lighting["head_count"] == 2
    assert lighting["rail_product"] == "PROD-PUREEDGE-TS24M-2C-4FT-WH"
    assert lighting["stock_rail_m"] == pytest.approx(48 * INCH)
    assert lighting["installed_rail_m"] == pytest.approx(36 * INCH)
