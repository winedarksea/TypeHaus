"""Floor-opening edge framing (plans/TODO.md "Stair framing follow-ups", defect 1).

Two defects lived side by side in ``resolve/floors.py``:

* the doubled trimmer pair was emitted twice at *identical* endpoints, so the second ply
  was invisible geometry — it rendered, measured and clashed as one member, not two; and
* an opening header was emitted as a single ply of the deck's own ``JoistSpec.member``,
  which is neither doubled nor sized: catlin's 3'-4" attic header and its 11'-0" stair
  header were the same unsized I-joist ply.

These lock the fix, plus the advisory that says so when a header outruns the prescriptive
table rather than letting the drawn member imply a prescriptive answer.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.checks import build_context
from typehaus.checks.structural.checks import floor_opening_header_within_prescriptive
from typehaus.findings import Result
from typehaus.quantities import ft, inch
from typehaus.resolve import resolve
from typehaus.resolve.floors import opening_header_profile
from typehaus.resolve.framing.profiles import cross_section
from typehaus.source import load_plan

CATLIN_DIR = Path(__file__).resolve().parents[3] / "houses" / "catlin"


@pytest.fixture(scope="module")
def catlin_model():
    result = load_plan(CATLIN_DIR)
    model, findings = resolve(result.plan)
    errors = [finding for finding in findings if finding.severity.value == "error"]
    assert not errors, [finding.message for finding in errors]
    return model


def _members(model, category):
    return [member for floor in model.floors for member in floor.members
            if member.category == category]


def _endpoints(member):
    return (round(member.p0[0], 6), round(member.p0[1], 6),
            round(member.p1[0], 6), round(member.p1[1], 6))


# ------------------------------------------------------------------ trimmer plies
def test_trimmer_plies_are_not_coincident(catlin_model):
    trimmers = _members(catlin_model, "trimmer")
    assert trimmers, "catlin frames stair openings in both wood decks"
    assert len({_endpoints(member) for member in trimmers}) == len(trimmers)


def test_trimmer_plies_lie_face_to_face_outboard_of_the_opening(catlin_model):
    """Ply 0 keeps the authored opening line (the header ends bear on it); ply 1 steps
    exactly one ply thickness *away* from the hole, which is where the second trimmer of
    a doubled pair goes."""
    trimmers = {member.child_key: member for member in _members(catlin_model, "trimmer")}
    pairs = {key[: -len("-0")] for key in trimmers if key.endswith("-0")}
    assert pairs
    for prefix in pairs:
        first, second = trimmers[f"{prefix}-0"], trimmers[f"{prefix}-1"]
        thickness = cross_section(first.profile).width_m
        gap = max(abs(second.p0[0] - first.p0[0]), abs(second.p0[1] - first.p0[1]))
        assert gap == pytest.approx(thickness, abs=1e-9), prefix
        # Same run, same z band — a ply, not a different member.
        assert second.length_m == pytest.approx(first.length_m)
        assert (second.z0_m, second.z1_m) == pytest.approx((first.z0_m, first.z1_m))


# ------------------------------------------------------------------ header sizing
def test_opening_headers_are_multi_ply_and_deck_deep(catlin_model):
    headers = _members(catlin_model, "header")
    assert headers
    for floor in catlin_model.floors:
        joist = next((member for member in floor.members if member.category == "joist"), None)
        if joist is None:
            continue
        band_depth = cross_section(joist.profile).depth_m
        for header in (m for m in floor.members if m.category == "header"):
            section = cross_section(header.profile)
            assert section.plies >= 2, header.child_key
            # Flush in the joist band, so the cut joists hang off it at their own depth.
            assert section.depth_m == pytest.approx(band_depth), header.child_key


def test_header_ply_count_tracks_the_span(catlin_model):
    """The stair well and the attic well used to draw the identical single ply."""
    band = cross_section("11.875 I-joist").depth_m
    short = cross_section(opening_header_profile(ft(3, 4).meters, band))
    long = cross_section(opening_header_profile(ft(11).meters, band))
    assert short.plies == 2
    assert long.plies > short.plies
    assert short.depth_m == pytest.approx(band) and long.depth_m == pytest.approx(band)


def test_beyond_prescriptive_header_is_reported(catlin_model):
    """An 11'-0" floor-opening header is an engineered beam; the drawing set has to say
    so, which ``structural.header_prescriptive`` only ever did for *wall* openings."""
    ctx, _ = build_context(load_plan(CATLIN_DIR).plan, CATLIN_DIR)
    findings = floor_opening_header_within_prescriptive(ctx)
    failures = [finding for finding in findings if finding.result is Result.FAIL]
    assert failures, "catlin's FO-S-STAIR header spans 11'"
    assert all(finding.severity.value == "warn" for finding in findings)
    for header in _members(catlin_model, "header"):
        if header.length_m / inch(12).meters <= 8.0 + 1e-9:
            assert not any(header.child_key in finding.message for finding in failures)
