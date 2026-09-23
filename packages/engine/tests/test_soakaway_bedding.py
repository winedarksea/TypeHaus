"""A bedding's soakaway course: stone below the drained section that floods, and is never frost.

``z0_m`` keeps meaning the drained section's bottom — what ``structural.frost_depth`` reads —
so a consumer that misses the course fails safe; everything that measures STONE reads
``stone_z0_m``.
"""

from __future__ import annotations

import copy
import dataclasses

import pytest
from _soakaway_plan import PAD_BOTTOM_FT, plain_bed, soak_bed, soak_plan

from typehaus.findings import Result
from typehaus.quantities import inch
from typehaus.resolve import resolve
from typehaus.resolve.bedding_soakaway import soakaway_findings

_IN = 0.0254
_CID = "integrity.footing_bedding_soakaway"


@pytest.fixture(scope="module")
def soak_model(catlin_plan):
    model, findings = resolve(soak_plan(catlin_plan))
    errors = [f for f in findings if f.severity.value == "error"]
    assert not errors, [f.message for f in errors]
    return model


def _bed(model, tag):
    return next(b for b in model.footing_beddings if b.tag == tag)


def test_the_course_hangs_below_the_drained_section(soak_model):
    bed = _bed(soak_model, "FB-TEST-SOAK")
    pad_bottom = PAD_BOTTOM_FT * 0.3048
    assert bed.z1_m == pytest.approx(pad_bottom)
    assert bed.z0_m == pytest.approx(pad_bottom - 24 * _IN), "z0 is still the drained section"
    assert bed.soakaway_z0_m == pytest.approx(pad_bottom - 36 * _IN)
    assert bed.stone_z0_m == bed.soakaway_z0_m
    assert bed.void_ratio == 0.40 and bed.infiltration_in_per_hr == 0.06
    plain = _bed(soak_model, "FB-TEST-PLAIN")
    assert plain.soakaway_z0_m is None and plain.stone_z0_m == plain.z0_m


def test_the_tile_stays_in_the_drained_section(soak_model):
    """The pipe is where it physically is: on the drained section's floor, not the course's."""
    bed = _bed(soak_model, "FB-TEST-SOAK")
    tile = [s for s in soak_model.solids if s.tag.startswith("FB-TEST-SOAK-DT")]
    assert tile
    assert min(s.z0_m for s in tile) >= bed.z0_m - 1e-6


@pytest.mark.parametrize(("bed", "fragment"), [
    (soak_bed(soakaway_depth=inch(0)), "must be > 0"),
    (plain_bed(overflow_ref="daylight"), "no soakaway_depth"),
    (plain_bed(inlet_refs=("FD-X",)), "no soakaway_depth"),
    (plain_bed(drain_tile_spec=soak_bed().drain_tile_spec), "has no soakaway course"),
    (soak_bed(drain_tile_spec=plain_bed().drain_tile_spec), "its own course"),
])
def test_a_course_that_is_not_one_is_an_error(bed, fragment):
    found = soakaway_findings(bed)
    assert found and all(f.check_id == _CID for f in found)
    assert any(fragment in f.message for f in found), [f.message for f in found]
    assert not soakaway_findings(soak_bed()) and not soakaway_findings(plain_bed())


def test_the_error_reaches_the_resolver(catlin_plan):
    _, findings = resolve(soak_plan(catlin_plan, soak=soak_bed(soakaway_depth=inch(-1))))
    assert any(f.check_id == _CID and f.severity.value == "error" for f in findings)


def test_the_course_is_billed_as_stone(soak_model):
    from typehaus.takeoff.sitework import footing_bedding_takeoff

    row = next(r for r in footing_bedding_takeoff(soak_model) if "FB-TEST-SOAK" in r["tags"])
    assert row["tags"] == ["FB-TEST-SOAK"], "a 'soakaway' tile is its own delivery row"
    area_sf = 16.0
    assert row["volume_cubic_yards"] == pytest.approx(area_sf * 3.0 / 27.0, abs=0.01)
    # Fabric lines the bottom and the full 36" of cut face.
    assert row["geotextile_sqft"] == pytest.approx(area_sf + 16.0 * 3.0, abs=0.2)


def test_the_two_beds_are_one_body_of_stone(soak_model):
    from typehaus.resolve.drainage_network import stone_bodies

    assert stone_bodies(soak_model)["FB-TEST-PLAIN"] == {"FB-TEST-SOAK", "FB-TEST-PLAIN"}


def test_the_course_is_never_frost_section(catlin_model):
    """30" of drained section plus a 12" course does NOT pass a 42" frost depth.

    FT-SG-S has nothing but its section (see ``test_frost_depth_excavation``). Cut the
    drained section short of frost and hang a course under it that would reach: the check
    must not count the course, because stone that floods is not ASCE 32's drained layer.
    """
    from test_frost_depth_excavation import _frost_by_tag

    model = copy.copy(catlin_model)
    court_floor = next(s for s in catlin_model.solids if s.tag == "SL-SG-FLOOR").z1_m

    def shorten(bed):
        if bed.host != "FT-SG-S":
            return bed
        z0 = court_floor - 36 * _IN
        return dataclasses.replace(bed, z0_m=z0, soakaway_z0_m=z0 - 12 * _IN)

    model.footing_beddings = [shorten(b) for b in catlin_model.footing_beddings]
    finding = _frost_by_tag(model)["FT-SG-S"]
    assert "ASCE 32" not in finding.message
    assert finding.result is not Result.PASS, finding.message
