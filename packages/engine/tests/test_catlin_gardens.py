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
    assert walk["plan_area_sqft"] == pytest.approx(557.4, abs=0.2)
    assert walk["volume_cubic_yards"] == pytest.approx(6.88, abs=0.01)
    base = next(r for r in bom["envelope_layers"] if r["material"] == "mndot-class-5-base")
    assert base["net_area_sqft"] == pytest.approx(557.4, abs=0.2)
    pockets = Counter(e.tag.split("-")[2][0] for e in catlin_model_ro.plan.all_elements()
                      if e.tag.startswith("FO-WK-"))
    assert pockets == {"A": 6, "B": 12, "D": 10}


def test_planting_counts(catlin_model_ro) -> None:
    rows = {r["item"]: r["quantity"] for r in planting_takeoff(catlin_model_ro)}
    assert rows == {
        "PT-SCH-JAZZ": 230, "PT-COR-MOONBEAM": 18, "PT-SED-ANGELINA": 3,
        "PT-HEU-CARAMEL": 3, "PT-CAR-VULP": 20, "PT-IRI-VERS": 3, "PT-ASC-INCA": 2,
        "PT-CAL-NEPETA": 7, "PT-ALL-MILLENIUM": 7, "PT-SPO-TARA": 7, "PT-SAL-PURP": 7,
        "PT-MAL-HONEYCRISP": 1, "PT-MAL-ZESTAR": 1, "PT-MAL-HARALSON": 1,
        "trellis-post:4x4:kdat": 5, "trellis-wire:12.5 ga high-tensile galvanized": 76.0,
    }
    assert len(catlin_model_ro.plants) == 310
