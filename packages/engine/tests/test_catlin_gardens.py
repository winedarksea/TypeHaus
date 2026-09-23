"""catlin's gardens reproduce their four hand-worked notes.

notes/rain_garden_sizing.md, notes/sidewalk_layout.md, notes/grid_garden.md and
notes/espalier_trellis.md. Every number asserted here is worked by hand there.
"""

from __future__ import annotations

from collections import Counter

import pytest
from _helpers import check_context

from typehaus.findings import Result
from typehaus.resolve.rain_garden import ponding_volume_m3
from typehaus.resolve.roof_catchment import roof_catchments
from typehaus.takeoff.drainage import drainage_takeoff
from typehaus.takeoff.planting import planting_takeoff

_SF = 1 / 0.3048 ** 2
_CF = 35.3146667


def test_rain_garden_catchment_and_volume(catlin_model_ro) -> None:
    catchment = roof_catchments(catlin_model_ro)
    assert catchment.by_leader["TR-G-LEADER-W"] * _SF == pytest.approx(338.6, abs=0.2)
    assert catchment.by_leader["TR-RF-LEADER-W"] * _SF == pytest.approx(692.2, abs=0.2)
    # The canopy's west half reaches no leader that names it.
    uncounted = {(tag, side): area * _SF for tag, side, area in catchment.uncounted}
    assert uncounted[("RF-BW-CANOPY", "west")] == pytest.approx(80.0, abs=0.2)
    basin = catlin_model_ro.plan.by_tag("RG-W-BASIN")
    assert ponding_volume_m3(basin) * _CF == pytest.approx(88.5, abs=0.05)


def test_rain_garden_and_extension_quantities(catlin_model_ro) -> None:
    rows = {r["category"]: r for r in drainage_takeoff(catlin_model_ro)
            if r["category"] in ("leader_extension", "rain_garden_media", "rain_garden_stone")}
    assert rows["rain_garden_media"]["aggregate_cubic_yards"] == pytest.approx(6.48, abs=0.01)
    assert rows["rain_garden_stone"]["aggregate_cubic_yards"] == pytest.approx(3.24, abs=0.01)
    assert rows["leader_extension"]["length_ft"] == pytest.approx(28.5, abs=0.1)


def test_garden_checks_read_as_the_note_says(catlin_model_ro) -> None:
    from typehaus.checks.code.site_utilities import utility_clearance
    from typehaus.checks.mep.landscape_drainage import (
        infiltration_setback,
        leader_extension_fall,
        rain_garden_capacity,
    )

    ctx = check_context(model=catlin_model_ro)
    capacity = rain_garden_capacity(ctx)
    assert any(f.result is Result.PASS and "88.5 cf against 85.9 cf" in f.message
               for f in capacity)
    setbacks = infiltration_setback(ctx)
    assert any(f.result is Result.PASS and "10.5 ft" in f.message for f in setbacks)
    assert sum(f.result is Result.UNKNOWN for f in setbacks) == 2   # garage, lot line
    assert {f.result for f in leader_extension_fall(ctx)} == {Result.PASS}
    assert {f.result for f in utility_clearance(ctx)} == {Result.PASS}


def test_sidewalk_quantities(catlin_model_ro) -> None:
    from typehaus.takeoff.bom import bill_of_materials

    bom = bill_of_materials(catlin_model_ro)
    walk = next(r for r in bom["structural_solids"] if r.get("assembly") == "SIDEWALK_FRC_CLASS5")
    assert walk["count"] == 5
    assert walk["plan_area_sqft"] == pytest.approx(558.8, abs=0.2)
    assert walk["volume_cubic_yards"] == pytest.approx(6.90, abs=0.01)
    base = next(r for r in bom["envelope_layers"] if r["material"] == "mndot-class-5-base")
    assert base["net_area_sqft"] == pytest.approx(558.8, abs=0.2)
    pockets = Counter(e.tag.split("-")[2][0] for e in catlin_model_ro.plan.all_elements()
                      if e.tag.startswith("FO-WK-"))
    assert pockets == {"A": 6, "B": 12, "D": 9}


def test_every_pocket_is_on_the_grid(catlin_model_ro) -> None:
    """No hand-placed void: every pocket is on its leg's pocket line, clear of the edges.

    A leader-foot pocket used to be appended off-grid; on leg D it sat in the 36" walking
    band with 1.6" of concrete to the slab edge (notes/sidewalk_layout.md §3).
    """
    from shapely.geometry import Point, Polygon

    plan = catlin_model_ro.plan
    # Each leg's pocket line(s): the coordinate every pocket on that slab must share.
    lines = {"SL-WK-A": ("y", (68.9983, 73.3317)), "SL-WK-B": ("x", (31.7783, 36.1117)),
             "SL-WK-D": ("x", (40.3683,))}
    for slab_tag, (axis, values) in lines.items():
        slab = plan.by_tag(slab_tag)
        ring = Polygon([p.xy_m for p in slab.outline])
        centres = []
        for tag in slab.openings:
            opening = plan.by_tag(tag)
            c = Polygon([p.xy_m for p in opening.outline]).centroid
            centres.append(c)
            on = (c.y if axis == "y" else c.x) / 0.3048
            assert min(abs(on - v) for v in values) < 1e-3, f"{tag} is off {slab_tag}'s line"
            edge = ring.exterior.distance(Point(c.x, c.y)) / 0.3048 * 12 - 8.0
            assert edge >= 11.9, f"{tag} leaves {edge:.2f}in of concrete to {slab_tag}'s edge"
        for i, a in enumerate(centres):
            for b in centres[i + 1:]:
                assert a.distance(b) / 0.3048 >= 2.0, f"two {slab_tag} pockets are under 2' apart"


def test_the_walk_turns_the_corner_under_open_concrete(catlin_model_ro) -> None:
    """Leg A's pocket rows cross leg B's whole width; nothing may stand in B's walk.

    Leg A is anchored to the corner for this (notes/sidewalk_layout.md §3) — its stations
    are leg B's own pocket columns. Centred at 4'-0" it put a void in the turn.
    """
    from shapely.geometry import Polygon

    plan = catlin_model_ro.plan
    a, b = plan.by_tag("SL-WK-A"), plan.by_tag("SL-WK-B")
    bx0 = min(p.xy_m[0] for p in b.outline) / 0.3048
    lane = (bx0 + 1.0 + 16.0 / 12, bx0 + 1.0 + 16.0 / 12 + 3.0)      # B's 36" walk, in x
    stations = set()
    for tag in a.openings:
        c = Polygon([p.xy_m for p in plan.by_tag(tag).outline]).centroid
        x = c.x / 0.3048
        stations.add(round(x, 3))
        assert x + 8.0 / 12 <= lane[0] + 1e-6 or x - 8.0 / 12 >= lane[1] - 1e-6, (
            f"{tag} stands in leg B's walking lane")
    columns = {round(bx0 + 20.0 / 12, 3), round(bx0 + 72.0 / 12, 3)}
    assert columns <= stations, "leg A's stations must carry leg B's pocket columns"


def test_planting_counts(catlin_model_ro) -> None:
    rows = {r["item"]: r["quantity"] for r in planting_takeoff(catlin_model_ro)}
    assert rows == {
        "PT-SCH-JAZZ": 392, "PT-COR-MOONBEAM": 33, "PT-SED-ANGELINA": 6,
        "PT-HEU-CARAMEL": 5, "PT-PAN-OCTSKY": 10,
        "PT-PAN-NORTHWIND": 10, "PT-IRI-VERS": 3, "PT-ASC-INCA": 2,
        "PT-CAL-NEPETA": 7, "PT-ALL-MILLENIUM": 7, "PT-SPO-TARA": 7, "PT-SAL-PURP": 6,
        "PT-MAL-HONEYCRISP": 1, "PT-MAL-ZESTAR": 1, "PT-MAL-HARALSON": 1,
        "trellis-post:4x4:kdat": 5, "trellis-wire:12.5 ga high-tensile galvanized": 76.0,
    }
    assert len(catlin_model_ro.plants) == 491
