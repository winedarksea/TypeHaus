"""Closed risers and ``code.R311_7_5_1_open_risers`` against catlin's flights.

Reproduces ``houses/catlin/notes/stair_riser_basis.md`` §3–§4, and first asks whether the
rule catches what it exists for: every flight as it was, open.
"""

from __future__ import annotations

from dataclasses import replace

import pytest
from _helpers import check_context

from typehaus.checks.code.mn_residential.open_risers import CHECK_ID, open_risers, steps
from typehaus.findings import Result
from typehaus.takeoff.hardwood import hardwood_takeoff

_IN = 0.0254
_FLIGHTS = ["ST-B2M", "ST-M2S", "ST-S2A", "ST-G-SERVICE", "ST-SG-PORCH"]


def _stair(model, tag):
    return next(stair for stair in model.stairs if stair.tag == tag)


def _opened(stair):
    return replace(stair, members=tuple(m for m in stair.members if m.category != "riser"))


def test_catlin_closes_every_riser(catlin_model_ro):
    findings = open_risers(check_context(model=catlin_model_ro))
    assert findings and all(f.result is Result.PASS for f in findings), [
        f.message for f in findings if f.result is not Result.PASS]


@pytest.mark.parametrize(("tag", "count", "opening_in", "top_in", "over_30"), [
    ("ST-B2M", 15, 5.86, 108.9, 11), ("ST-M2S", 16, 5.78, 118.76, 12),
    ("ST-S2A", 16, 5.75, 118.25, 12), ("ST-G-SERVICE", 5, 5.30, 32.5, 1),
    ("ST-SG-PORCH", 5, 5.10, 31.5, 1)])
def test_hand_numbers_open(catlin_model_ro, tag, count, opening_in, top_in, over_30):
    """§3: each flight's openings as it stood, with no riser boards."""
    flight = steps(_opened(_stair(catlin_model_ro, tag)))
    assert len(flight) == count
    assert not any(closed for *_, closed in flight)
    assert max(top - lo for lo, top, _, _ in flight) / _IN == pytest.approx(opening_in,
                                                                            abs=0.01)
    assert max(above for *_, above, _ in flight) / _IN == pytest.approx(top_in, abs=0.1)
    assert sum(above > 30 * _IN for *_, above, _ in flight) == over_30


@pytest.mark.parametrize("tag", _FLIGHTS)
def test_an_open_flight_fails(catlin_model_ro, tag):
    model = replace(catlin_model_ro, stairs=[
        _opened(s) if s.tag == tag else s for s in catlin_model_ro.stairs])
    [finding] = [f for f in open_risers(check_context(model=model))
                 if tag in f.element_tags]
    assert finding.check_id == CHECK_ID and finding.result is Result.FAIL


@pytest.mark.parametrize(("tag", "material", "heights"), [
    ("ST-B2M", "plywood-subfloor", {5.862}), ("ST-M2S", "oak-riser", {5.782}),
    ("ST-S2A", "oak-riser", {5.75}), ("ST-G-SERVICE", "kdat", {5.3})])
def test_riser_boards(catlin_model_ro, tag, material, heights):
    """§4: every step carries a 3/4" board of the flight's riser stock."""
    stair = _stair(catlin_model_ro, tag)
    risers = [m for m in stair.members if m.category == "riser"]
    assert len(risers) == len(steps(stair))
    assert {m.material for m in risers} == {material}
    assert {round((m.z1_m - m.z0_m) / _IN, 3) for m in risers} == heights
    assert {m.profile.split("x")[0] for m in risers} == {"0.750"}


def test_oak_risers_are_milled(catlin_model_ro):
    rows = [r for r in hardwood_takeoff(catlin_model_ro) if r["use"] == "stair riser"]
    assert sum(r["pieces"] for r in rows) == 32
    assert {r["nominal_stock"] for r in rows} == {"4/4"}
    assert {r["layup"] for r in rows} == {"one board"}
