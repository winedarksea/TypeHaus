"""The porch and garden have distinct light sources, controls and clear mounting paths."""

from __future__ import annotations

import math
import tomllib
from pathlib import Path

import pytest
from shapely.geometry import LineString, Point, Polygon

from typehaus.model.placeable_symbols import model_parts
from typehaus.model.placeable_symbols._flood_light import (
    FLOOD_BEAM_DEGREES,
    FLOOD_DOWNWARD_AIM_DEGREES,
    flood_head_direction,
    flood_lens_center,
)
from typehaus.takeoff.lighting import luminaire_schedule

FLOOD = "ED-M-PORCH-FLOOD"
PORCH_LIGHTS = ("ED-M-PORCH-FAN", "ED-M-STAIR-LT")


def _flood(model):
    item = next(obj for obj in model.canvas_objects if obj.tag == FLOOD)
    product = next(kind for kind in model.plan.library.electrical_device_types
                   if kind.tag == item.type_ref)
    return item, product


def test_porch_ambient_and_garden_utility_controls_are_independent(catlin_plan):
    flood = catlin_plan.by_tag(FLOOD)
    assert flood.uid == "QTM001EAAA"
    assert flood.controlled_by == ("ED-M-PORCH-FLOOD-SW",)
    assert flood.mount.kind.value == "ceiling"
    assert flood.mount.elevation is not None
    assert flood.location is None
    for tag in (FLOOD, *PORCH_LIGHTS):
        light = catlin_plan.by_tag(tag)
        assert light.circuit == "CKT-LT-MAIN"
        assert light.room is None
        assert catlin_plan.by_tag(light.controlled_by[0]).kind.value == "switch"
    for tag in PORCH_LIGHTS:
        assert catlin_plan.by_tag(tag).controlled_by == ("ED-M-PORCH-SW",)


def test_flood_box_is_on_blocking_beyond_the_porch_floor(catlin_model_ro):
    model = catlin_model_ro
    flood, product = _flood(model)
    balcony = next(floor for floor in model.floors if floor.tag == "FS-SG-DECK")
    porch = next(floor for floor in model.floors if floor.tag == "FS-SG-PORCH")
    assert flood.position[0] == pytest.approx(18 * 0.3048)
    assert not Polygon(porch.deck_outline).intersects(Polygon(flood.footprint))
    blocks = [member for member in balcony.members if member.category == "blocking"
              and LineString((member.p0, member.p1)).distance(Point(*flood.position)) < 1e-8]
    assert len(blocks) == 1, "the box needs a real support between the outer two joists"
    block = blocks[0]
    fraction = ((flood.position[1] - block.p0[1]) / (block.p1[1] - block.p0[1]))
    support_z = block.z0_m + fraction * ((block.z0_end_m or block.z0_m) - block.z0_m)
    assert flood.body_z1_m == pytest.approx(support_z)
    # The downward head, including visor, is below the fascia and the higher gutter.
    fascia = model.plan.by_tag("TR-SG-FASCIA")
    parts = model_parts(product.plan_symbol, *(d.meters for d in product.footprint),
                        product.height.meters)
    head_top = max(part["center"][2] + part["size"][2] / 2 for part in parts
                   if "mesh" in part and part["color"] != "metal-black") + flood.z_m
    assert head_top < fascia.top_elevation.meters - fascia.depth.meters


def test_flood_aim_reaches_the_open_garden_without_crossing_the_porch(catlin_model_ro):
    model = catlin_model_ro
    flood, product = _flood(model)
    local_lens = flood_lens_center(*(d.meters for d in product.footprint), product.height.meters)
    lens = (flood.position[0] + local_lens[0], flood.position[1] + local_lens[1],
            flood.z_m + local_lens[2])
    direction = flood_head_direction()
    garden = model.plan.by_tag("SL-SG-FIELD")
    distance = (garden.top_elevation.meters - lens[2]) / direction[2]
    target = tuple(lens[i] + distance * direction[i] for i in range(3))
    assert Polygon([p.xy_m for p in garden.outline]).contains(Point(*target[:2]))
    assert FLOOD_DOWNWARD_AIM_DEGREES - FLOOD_BEAM_DEGREES / 2 > 0
    for tag in ("FS-SG-PORCH", "FS-SG-DECK"):
        floor = next(f for f in model.floors if f.tag == tag)
        if lens[2] < floor.deck_z0_m:
            continue
        travel = (floor.deck_z1_m - lens[2]) / direction[2]
        if travel >= 0:
            crossing = Point(lens[0] + travel * direction[0], lens[1] + travel * direction[1])
            assert not Polygon(floor.deck_outline).covers(crossing), tag
    # At this mounting height a 25-degree spot would leave a small pool. The allowance's
    # wider beam reaches across the garden's 17-foot court at its central aiming distance.
    court = model.plan.by_tag("SL-SG-FLOOR")
    width = max(p.x.meters for p in court.outline) - min(p.x.meters for p in court.outline)
    assert 2 * distance * math.tan(math.radians(FLOOD_BEAM_DEGREES / 2)) > width


def test_garden_flood_is_scheduled_and_priced_once(catlin_model_ro):
    _, product = _flood(catlin_model_ro)
    row = next(row for row in luminaire_schedule(catlin_model_ro) if row["type"] == product.tag)
    assert row["count"] == 1 and row["mark"] == "S"
    assert product.wet_rated and product.full_cutoff
    assert (product.watts, product.lumens, product.cct_k) == (20, 1800, 3000)
    prices = tomllib.loads((Path(catlin_model_ro.plan.source_root) / "prices.toml").read_text())
    assert prices["placeables"][product.tag]["material"] == {"low": 80, "high": 250}
