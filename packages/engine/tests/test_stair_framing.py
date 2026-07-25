"""Stair framing regression coverage (raked stringers, split-landing platforms, well
partition, concrete-wall hangers — plan: "stairs aren't framed properly").

Guards the U-stair rebuild: no coincident members, split-landing riser budget
(lower treads · landing · landing+riser · upper treads · arrival), raked stringers that
never read as floor-to-floor prisms, a framed well partition, deduplicated landing-platform
joists, and hanger bands that bear at the landing rather than the arrival deck.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from typehaus.quantities import ft, inch
from typehaus.resolve import resolve
from typehaus.resolve.framing.profiles import cross_section
from typehaus.source import load_plan

CATLIN_DIR = Path(__file__).resolve().parents[3] / "houses" / "catlin"


@pytest.fixture(scope="module")
def catlin_model():
    result = load_plan(CATLIN_DIR)
    assert result.plan is not None, [f.message for f in result.findings]
    model, findings = resolve(result.plan)
    errors = [f for f in findings if f.severity.value == "error"]
    assert not errors, [f.message for f in errors]
    return model


@pytest.fixture(scope="module")
def basement_stair(catlin_model):
    return next(stair for stair in catlin_model.stairs if stair.tag == "ST-B2M")


def _subfloor(catlin_model, stair) -> float:
    storey = catlin_model.plan.storey(stair.storey)
    assert storey is not None
    return storey.elevation.meters


def _landing_zone(stair) -> tuple[float, float]:
    """ST-B2M's landing zone in the run direction: the last landing_depth of the run."""
    ys = [point[1] for point in stair.outline]
    return max(ys) - ft(4).meters, max(ys)


# ------------------------------------------------------------------ 1. no coincidences
def test_no_two_stair_members_are_coincident(catlin_model):
    """Kills both historical coincidence bugs: the byte-identical step-between-landings /
    landing-upper pair, and the min()-clamped duplicate landing joists."""
    for stair in catlin_model.stairs:
        seen = {}
        for member in stair.members:
            key = (member.p0, member.p1, round(member.z0_m, 6), round(member.z1_m, 6))
            assert key not in seen, (
                f"{stair.tag}: {member.child_key} coincides with {seen[key]}")
            seen[key] = member.child_key


# ----------------------------------------------------------------- 2. U riser budget
def test_u_stair_landings_split_one_riser_apart_inside_the_landing_zone(
        catlin_model, basement_stair):
    stair = basement_stair
    riser = stair.riser_height_m
    subfloor = _subfloor(catlin_model, stair)
    members = {member.child_key: member for member in stair.members}
    lower, upper = members["landing-lower"], members["landing-upper"]
    lower_treads = (stair.riser_count - 3 + 1) // 2
    assert lower.z0_m == pytest.approx(subfloor + riser * (lower_treads + 1))
    assert upper.z0_m - lower.z0_m == pytest.approx(riser)
    zone_lo, zone_hi = _landing_zone(stair)
    for landing in (lower, upper):
        for point in (landing.p0, landing.p1):
            assert zone_lo - 1e-6 <= point[1] <= zone_hi + 1e-6, landing.child_key
    # The step between the landings IS the riser between them — no separate member.
    assert "step-between-landings" not in members
    # Top upper tread ends one riser below the arrival deck.
    arrival = subfloor + riser * stair.riser_count
    top_tread = max((m for m in stair.members if m.child_key.startswith("tread-upper-")),
                    key=lambda m: m.z0_m)
    assert top_tread.z0_m == pytest.approx(arrival - riser)


# ---------------------------------------------------------------- 3. raked stringers
def test_stringers_are_raked_and_never_drop_below_the_subfloor(catlin_model):
    for stair in catlin_model.stairs:
        subfloor = _subfloor(catlin_model, stair)
        stringers = [m for m in stair.members if m.category == "stringer"]
        assert stringers, stair.tag
        for stringer in stringers:
            assert stringer.z0_end_m is not None and stringer.z1_end_m is not None, (
                f"{stair.tag}:{stringer.child_key} is not raked")
            low = min(stringer.z0_m, stringer.z1_m, stringer.z0_end_m, stringer.z1_end_m)
            assert low >= subfloor - 1e-9, f"{stair.tag}:{stringer.child_key}"
            # A raked stringer is never a full-height prism over its run.
            span = max(stringer.z1_m, stringer.z1_end_m) - min(stringer.z0_m,
                                                               stringer.z0_end_m)
            rise = stair.riser_height_m * stair.riser_count
            assert (max(stringer.z1_m - stringer.z0_m,
                        stringer.z1_end_m - stringer.z0_end_m) < rise - 1e-6), (
                f"{stair.tag}:{stringer.child_key} reads as a floor-to-floor prism")
            assert span <= rise + 1e-6


def test_lower_flight_stringers_top_out_at_the_landing_bearing(catlin_model,
                                                               basement_stair):
    stair = basement_stair
    subfloor = _subfloor(catlin_model, stair)
    lower_treads = (stair.riser_count - 3 + 1) // 2
    landing_z = subfloor + stair.riser_height_m * (lower_treads + 1)
    for stringer in (m for m in stair.members
                     if m.child_key.startswith("stringer-lower-")):
        assert stringer.z1_end_m == pytest.approx(landing_z)


# ----------------------------------------------------------------- 4. well partition
def test_well_partition_is_framed_between_subfloor_and_arrival(catlin_model,
                                                               basement_stair):
    stair = basement_stair
    subfloor = _subfloor(catlin_model, stair)
    arrival = subfloor + stair.riser_height_m * stair.riser_count
    partition = [m for m in stair.members if m.category == "partition"]
    keys = {m.child_key for m in partition}
    assert "well-partition-plate-bottom" in keys and "well-partition-plate-top" in keys
    studs = [m for m in partition if m.child_key.startswith("well-partition-stud-")]
    assert len(studs) >= 2
    for member in partition:
        assert member.z0_m >= subfloor - 1e-9, member.child_key
        assert member.z1_m <= arrival + 1e-9, member.child_key
    for stud in studs:
        assert stud.p0 == stud.p1 and stud.orient is not None, stud.child_key
    # The old single full-height box is gone.
    assert "well-partition" not in {m.child_key for m in stair.members}


# --------------------------------------------------------------- 5. landing platforms
def test_landing_platforms_have_unique_joists_edge_joists_deck_and_rims(basement_stair):
    stair = basement_stair
    depth = ft(4).meters
    for name in ("lower", "upper"):
        deck = next(m for m in stair.members if m.child_key == f"landing-{name}")
        assert deck.profile.startswith("deck ")
        joists = [m for m in stair.members
                  if m.child_key.startswith(f"landing-joist-{name}-")]
        positions = sorted(round(joist.p0[1], 6) for joist in joists)
        assert len(positions) == len(set(positions)), f"duplicate {name} landing joists"
        span_lo = min(positions)
        offsets = [position - span_lo for position in positions]
        assert offsets[0] == pytest.approx(0.0)
        assert offsets[-1] == pytest.approx(depth)
        spacings = [b - a for a, b in zip(offsets, offsets[1:])]
        assert all(spacing <= inch(16).meters + 1e-9 for spacing in spacings)
        rims = [m for m in stair.members if m.child_key.startswith(f"landing-rim-{name}-")]
        assert len(rims) == 2
        for rim in rims:
            assert rim.z1_m == pytest.approx(deck.z0_m)  # framing tops at the deck


# ------------------------------------------------------------ 6. concrete-wall hangers
def test_basement_lower_hanger_bears_at_the_landing(catlin_model, basement_stair):
    stair = basement_stair
    lower_hangers = [m for m in stair.members
                     if m.category == "hanger"
                     and "stringer-lower" in m.child_key]
    assert lower_hangers
    for hanger in lower_hangers:
        assert hanger.connection is not None
        assert hanger.connection.startswith("concrete-wall-hanger:")
        assert hanger.z1_end_m == pytest.approx(-1.372, abs=0.01)
    # The annotated stringer carries the same connection tag.
    tagged = [m for m in stair.members if m.category == "stringer"
              and m.connection is not None]
    assert any("stringer-lower" in m.child_key for m in tagged)


# ------------------------------------------------------------------- 7. cross-sections
def test_stair_profiles_parse_to_explicit_cross_sections():
    hanger = cross_section("hanger")
    assert (hanger.width_m, hanger.depth_m) == (
        pytest.approx(inch(1.5).meters), pytest.approx(inch(8.0).meters))
    tapered = cross_section("tapered tread")
    assert (tapered.width_m, tapered.depth_m) == (
        pytest.approx(inch(1.5).meters), pytest.approx(inch(11.25).meters))
    deck = cross_section("deck 42x1.5")
    assert (deck.width_m, deck.depth_m) == (
        pytest.approx(inch(42).meters), pytest.approx(inch(1.5).meters))
    post = cross_section("4x4")
    assert (post.width_m, post.depth_m) == (
        pytest.approx(inch(3.5).meters), pytest.approx(inch(3.5).meters))


def test_riser_walk_is_continuous_one_riser_steps(catlin_model, basement_stair):
    """Walking the flight bottom-to-top hits every riser exactly once: treads, lower
    landing, upper landing, upper treads, arrival — no 2-riser jump anywhere."""
    stair = basement_stair
    subfloor = _subfloor(catlin_model, stair)
    walk = sorted(m.z0_m for m in stair.members
                  if m.category == "tread" or m.child_key in ("landing-lower",
                                                              "landing-upper"))
    arrival = subfloor + stair.riser_height_m * stair.riser_count
    walk.append(arrival)
    previous = subfloor
    for elevation in walk:
        assert elevation - previous == pytest.approx(stair.riser_height_m, abs=1e-6)
        previous = elevation
    assert math.isclose(previous, arrival, abs_tol=1e-9)
