"""Catlin's court drainage after 2026-09-22: the soakaway course, AD-SG-COURT, and the sump's
pumped line into the west rain garden.

Reproduces ``houses/catlin/notes/court_soakaway_storage.md`` (§1-§5) off the model.
"""

from __future__ import annotations

import pytest
from _helpers import check_context
from shapely.geometry import Polygon
from shapely.ops import unary_union

from typehaus.findings import Result

_IN = 0.0254
_FT = 0.3048
_SF = _FT ** 2
_SOAKAWAY_BEDS = ("FB-SG-W2", "FB-SG-E2", "FB-SG-S", "FB-SG-ARCH")


@pytest.fixture(scope="module")
def ctx(catlin_model_ro):
    return check_context(model=catlin_model_ro)


def _findings(fn, ctx, tag):
    return [f for f in fn(ctx) if tag in f.element_tags]


def test_the_course_is_388_sf_with_the_laps_counted_once(catlin_model_ro):
    """§1: 432.67 sf of bed less 2 x 16.917 (the S corners) and 2 x 5.25 (the ARCH laps)."""
    beds = [b for b in catlin_model_ro.footing_beddings if b.tag in _SOAKAWAY_BEDS]
    assert sum(Polygon(b.outline).area for b in beds) / _SF == pytest.approx(432.67, abs=0.01)
    union = unary_union([Polygon(b.outline) for b in beds]).area / _SF
    assert union == pytest.approx(388.33, abs=0.01)
    for bed in beds:
        assert (bed.z0_m - bed.stone_z0_m) / _IN == pytest.approx(12.0)


def test_the_catchment_is_the_open_court_south_of_the_balcony(catlin_model_ro):
    """§2: 17.000 x 16.333 = 277.67 sf; 50 / 62.4 x 277.67 = 222.5 cf."""
    drain = catlin_model_ro.plan.by_tag("AD-SG-COURT")
    area = Polygon([p.xy_m for p in drain.catchment]).area / _SF
    assert area == pytest.approx(277.67, abs=0.01)
    assert 50 / 62.4 * area == pytest.approx(222.5, abs=0.05)


def test_storage_holds_the_melt(ctx):
    """§3-§4: 155.3 + 93.2 = 248.5 cf against 222.5 cf — PASS at 1.12, presumed rate."""
    from typehaus.checks.mep.soakaway_storage import soakaway_storage

    storage, lip = _findings(soakaway_storage, ctx, "FB-SG-ARCH")
    assert storage.result is Result.PASS, storage.message
    assert storage.message.startswith(
        "4-bed soakaway course holds 155 cf of voids (388 sf) + 93 cf infiltrated over 48 h "
        "(presumed rate) = 249 cf, against 222 cf of melt (50 psf over 278 sf of catchment "
        "via AD-SG-COURT)"), storage.message
    # §5: the relief lip sits inside the drained frost section, stated rather than hidden.
    assert lip.result is Result.UNKNOWN
    assert 'sits 36" above the drained section' in lip.message


def test_the_area_drain_lets_go_below_frost_in_the_strip_north_of_the_beam(catlin_model_ro):
    solids = {s.tag: s for s in catlin_model_ro.solids}
    basin, riser = solids["AD-SG-COURT"], solids["AD-SG-COURT-RISER"]
    beam = solids["W-SG-ARCH"]
    arch = next(b for b in catlin_model_ro.footing_beddings if b.tag == "FB-SG-ARCH")
    floor = solids["SL-SG-FLOOR"]
    assert basin.z1_m == pytest.approx(floor.z1_m), "the grate sits in the rim"
    beam_north = max(p[1] for p in beam.outline)
    assert (min(p[1] for p in basin.outline) - beam_north) / _IN == pytest.approx(1.0)
    ys = [p[1] for p in riser.outline]
    assert beam_north < min(ys) and max(ys) <= max(p[1] for p in arch.outline)
    assert riser.z0_m / _IN == pytest.approx(-163.4375)
    assert (floor.z1_m - riser.z0_m) / _IN == pytest.approx(42.0 + 12.0), "12\" below frost"


def test_the_grate_is_at_x_20_and_voids_the_rim(catlin_model_ro):
    """x=20': 2'-0" east of FD-SG-FIELD, 13'-0" from FD-SG-OVERFLOW; the basin cuts the slab."""
    plan = catlin_model_ro.plan
    x, _ = plan.by_tag("AD-SG-COURT").position.xy_m
    assert x / _FT == pytest.approx(20.0)
    assert (x - plan.by_tag("FD-SG-FIELD").path[0].xy_m[0]) / _FT == pytest.approx(2.0)
    assert (x - plan.by_tag("FD-SG-OVERFLOW").path[0].xy_m[0]) / _FT == pytest.approx(13.0)
    solids = {s.tag: s for s in catlin_model_ro.solids}
    basin = sorted(solids["AD-SG-COURT"].outline)
    assert basin in [sorted(v) for v in solids["SL-SG-FLOOR"].voids]


def test_the_pump_walks_to_the_rain_garden(catlin_model_ro, ctx):
    from typehaus.checks.mep.sump_discharge import pump_discharge
    from typehaus.resolve.drainage_network import EdgeKind, build_network

    network = build_network(catlin_model_ro.plan)
    reached, path, _ = network.reaches_disposal("SM-B-RADON", first_hop=EdgeKind.PRIMARY)
    assert reached and path == ["SM-B-RADON", "TR-RF-LEADER-W", "RG-W-BASIN"], path
    found = pump_discharge(ctx)
    assert [f.result for f in found] == [Result.PASS], [f.message for f in found]


def test_the_rain_garden_still_holds_its_roofs_and_names_the_pump(ctx):
    from typehaus.checks.mep.landscape_drainage import rain_garden_capacity

    found = _findings(rain_garden_capacity, ctx, "RG-W-BASIN")
    capacity = next(f for f in found if "ponds" in f.message)
    assert capacity.result is Result.PASS
    assert "100.3 cf against 92.6 cf" in capacity.message
    assert any(f.result is Result.UNKNOWN and "pumped water from SM-B-RADON" in f.message
               for f in found)


def test_the_sump_line_crosses_no_concrete(catlin_model_ro, ctx):
    from typehaus.checks.mep.run_interference import run_interference
    from typehaus.resolve.mep_concrete import concrete_crossings

    crossings = [c for c in concrete_crossings(catlin_model_ro)
                 if c["run"] == "PR-B-SUMP-DISCH"]
    # Out of the pit's lid and through the rim band over the pour (2026-09-24): no concrete.
    assert crossings == []
    assert not [f for f in run_interference(ctx)
                if "PR-B-SUMP-DISCH" in f.element_tags and f.result is Result.FAIL]
