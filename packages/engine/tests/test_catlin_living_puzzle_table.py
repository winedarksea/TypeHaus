"""The stowed puzzle table fits the sitting circle without consuming access zones."""

import pytest
from shapely.geometry import Polygon

from typehaus.quantities import inch
from typehaus.takeoff.placeables import placeables_takeoff

TABLE_TAG = "FURN-M-PUZZLE-COFFEE-TABLE"


def test_puzzle_table_dimensions_storage_and_takeoff(catlin_model_ro):
    table = next(item for item in catlin_model_ro.canvas_objects if item.tag == TABLE_TAG)
    west, south, east, north = Polygon(table.footprint).bounds
    assert (east - west, north - south) == pytest.approx(
        (inch(23.8).meters, inch(44.5).meters))
    assert table.body_z1_m - table.body_z0_m == pytest.approx(inch(18.3).meters)
    catalog_type = next(item for item in catlin_model_ro.plan.library.furniture_types
                        if item.tag == table.type_ref)
    assert catalog_type.storage
    assert "23.6" in catalog_type.source
    assert "puzzle tray stowed underneath" in catalog_type.source
    assert catalog_type.product_ref in {
        product.tag for product in catlin_model_ro.plan.library.products}
    row = next(row for row in placeables_takeoff(catlin_model_ro)
               if row["type"] == table.type_ref)
    assert row["count"] == 1
    assert row["tags"] == [TABLE_TAG]


def test_puzzle_table_keeps_seated_access_and_clearance_zones(catlin_model_ro):
    objects = {item.tag: item for item in catlin_model_ro.canvas_objects}
    table = objects[TABLE_TAG]
    table_polygon = Polygon(table.footprint)
    assert table.room == "RM-M-LIVING"
    sofa = objects["FURN-M-SOFA"]
    assert table_polygon.distance(Polygon(sofa.footprint)) == pytest.approx(inch(18).meters)
    assert table.position[1] == pytest.approx(sofa.position[1])
    for tag in ("FURN-M-ARMCHAIR-N", "FURN-M-ARMCHAIR-S"):
        assert table_polygon.distance(Polygon(objects[tag].footprint)) >= inch(14).meters
    for other in objects.values():
        if other.storey != table.storey or other.tag == TABLE_TAG:
            continue
        if other.body_z0_m < table.body_z1_m and other.body_z1_m > table.body_z0_m:
            assert table_polygon.intersection(Polygon(other.footprint)).area < 1e-8, other.tag
        for zone in (*other.required_clearances, *other.recommended_clearances):
            assert table_polygon.intersection(Polygon(zone)).area < 1e-8, other.tag
