"""A landing deeper than R311.7.6's 36", run to the wall behind it (catlin, 2026-09-24).

Two engine readings this leans on:

* ``bearing._best_host_wall`` measures its reach from the wall's RESOLVED faces. W-B-N2 and
  W-M-N2 are face-aligned, so their axis is the outside face; read as a centreline it put a
  joist flush on the inside face 8" away and posted the corner instead of hanging it.
* R311.7.2 grades a landing over its required 36" only (``walkline.headroom_stations``); runs
  over the excess depth are an ADVISORY on the PASS, not a FAIL.
"""

from __future__ import annotations

import math

import pytest

from typehaus.checks.code.mn_residential.stairs import stair_headroom
from typehaus.findings import Result
from typehaus.resolve.stairs.walkline import (
    LANDING_MIN_DEPTH_M,
    flight_stations,
    headroom_stations,
)

_INCH = 0.0254


def _stair(model, tag):
    return next(stair for stair in model.stairs if stair.tag == tag)


@pytest.mark.parametrize(("tag", "wall", "connection"), [
    ("ST-B2M", "W-B-N2", "concrete-wall-hanger:W-B-N2"),
    ("ST-M2S", "W-M-N2", "framed-wall-ledger:W-M-N2"),
])
def test_the_far_landing_joists_bear_on_the_north_wall(catlin_model, tag, wall, connection):
    stair = _stair(catlin_model, tag)
    far_y = max(m.p1[1] for m in stair.members if m.category == "landing")
    far = [m for m in stair.members if m.category == "landing_framing"
           and m.child_key.startswith("landing-joist-") and abs(m.p0[1] - far_y) < 1e-6]
    assert len(far) == 2, "one far edge joist per half-landing"
    assert {m.connection for m in far} == {connection}
    # Flush: the joist's face is on the wall's inside face.
    host = next(w for w in catlin_model.walls if w.tag == wall)
    inside = min(p[1] for layer in host.depth_layers() for p in layer.polygon)
    assert far_y + 0.75 * _INCH == pytest.approx(inside, abs=0.01 * _INCH)
    # So nothing is posted at the north corners.
    assert not [m for m in stair.members
                if m.child_key.startswith("landing-post-") and m.p0[1] > far_y - 0.1]


def test_headroom_grades_each_landing_over_its_required_depth_only(catlin_model):
    stair = _stair(catlin_model, "ST-B2M")
    full, graded = flight_stations(stair), headroom_stations(stair)
    for key in ("landing-lower", "landing-upper"):
        (a0, _, _), (a1, _, _) = full[key]
        (g0, _, _), (g1, _, _) = graded[key]
        assert math.dist(a0, a1) > LANDING_MIN_DEPTH_M + 0.3  # 50 7/8" authored
        assert g0 == a0
        assert math.dist(g0, g1) == pytest.approx(LANDING_MIN_DEPTH_M)
    assert {k: v for k, v in graded.items() if not k.startswith("landing")} == \
        {k: v for k, v in full.items() if not k.startswith("landing")}


def test_runs_over_the_excess_landing_are_an_advisory_not_a_fail(catlin_ctx):
    finding = next(f for f in stair_headroom(catlin_ctx) if f.message.startswith("ST-B2M"))
    assert finding.result is Result.PASS
    assert "ADVISORY" in finding.message
    for run in ("CD-B-GARAGE", "PR-B-CW-TRUNK", "PR-B-KITCH-DRAIN"):
        assert run in finding.message
