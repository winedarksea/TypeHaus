"""A sleeve through a FRAMED exterior wall: catlin's SP-S-BALC-HYD, the balcony hydrant's
barrel through W-S-S1. It spans the sheathing and everything outboard of it, carries its
seal and annulus insulation, and ``mep.exterior_hydrant_protection`` grades both."""

from __future__ import annotations

import pytest
from _helpers import check_context

from typehaus.checks.mep.plumbing import exterior_hydrant_protection
from typehaus.findings import Result
from typehaus.quantities import M_PER_IN
from typehaus.resolve import resolve
from typehaus.takeoff.mep import sleeve_takeoff

_TAG = "SP-S-BALC-HYD"


def _sleeve(model):
    return next(s for s in model.sleeves if s.tag == _TAG)


def test_the_sleeve_spans_the_sheathing_to_the_cladding_face(catlin_model_ro):
    sleeve = _sleeve(catlin_model_ro)
    assert sleeve.host_category == "framed_wall"
    assert sleeve.seal and sleeve.insulation
    assert sleeve.offset_m == pytest.approx(0.0, abs=1e-6)  # on the barrel's own line
    # W-S-S1: cladding face -7 1/4", sheathing inner face +1/2". Studs and liner unsleeved.
    assert sleeve.length_m / M_PER_IN == pytest.approx(7.75, abs=0.01)
    ys = [y / M_PER_IN for solid in catlin_model_ro.solids
          if solid.tag.startswith(f"{_TAG}-B") for _x, y in solid.outline]
    assert min(ys) == pytest.approx(-7.25, abs=0.01)
    assert max(ys) == pytest.approx(0.5, abs=0.01)


def test_cast_sleeves_keep_their_concrete_hosts(catlin_model_ro):
    cast = [s for s in catlin_model_ro.sleeves if s.tag != _TAG]
    assert cast and all(s.host_category != "framed_wall" for s in cast)
    assert all(s.seal is None and s.length_m is None for s in cast)


def test_the_takeoff_bills_the_bore_not_the_wall_height(catlin_model_ro):
    row = next(r for r in sleeve_takeoff(catlin_model_ro) if _TAG in r["tags"])
    assert row["sleeve_diameter_in"] == 2.5
    assert row["total_length_ft"] < 10.0 * row["count"]  # a 10' wall would bill 10' each


def test_hydrant_protection_names_the_sleeve(catlin_plan, catlin_model_ro):
    findings = exterior_hydrant_protection(check_context(catlin_plan, catlin_model_ro))
    balcony = [f for f in findings if f.element_tags[0] == "FX-S-BALC-HYD"]
    assert [f.result for f in balcony] == [Result.PASS]
    assert f"sleeved by {_TAG}" in balcony[0].message


@pytest.mark.parametrize("field", ["seal", "insulation"])
def test_a_sleeve_that_states_no_seal_or_insulation_fails(catlin_plan, field):
    sleeve = catlin_plan.by_tag(_TAG)
    bare = sleeve.model_copy(update={field: None})
    kept = [e for e in catlin_plan.storey_elements("second") if e.tag != _TAG]
    plan = catlin_plan.with_elements("second", (*kept, bare))
    model, _ = resolve(plan)
    failed = [f for f in exterior_hydrant_protection(check_context(plan, model))
              if f.result is Result.FAIL]
    assert [f.element_tags for f in failed] == [("FX-S-BALC-HYD", _TAG)]
    assert f"states no {field}" in failed[0].message
