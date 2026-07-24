"""Framing bearing-stack fix + model-wide interference guard (plan: framing
interference warning + deck bearing-stack fix).

- unit: ``member_footprint`` returns a thickness-wide ring + z-band per member kind.
- integration: the resolved catlin deck stacks post → beam → joist, and the outer
  joist spans cantilever 6" past the outer beams.
- regression: ``structural.member_interference`` reports zero findings from the deck
  bearing stack once the arithmetic is correct.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.checks import build_context
from typehaus.checks.structural.interference import member_interference
from typehaus.quantities import inch
from typehaus.resolve import resolve
from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import FramedMember
from typehaus.source import load_plan

CATLIN_DIR = Path(__file__).resolve().parents[3] / "houses" / "catlin"

_DECK_PREFIXES = ("SGFS", "BM-SG", "FS-SG", "PT-SG")


def _ring_extent(ring):
    xs = [x for x, _ in ring]
    ys = [y for _, y in ring]
    return max(xs) - min(xs), max(ys) - min(ys)


# --------------------------------------------------------------------------- unit
def test_member_footprint_horizontal_is_thickness_wide():
    cs = cross_section("2x8")
    # A 2x8 joist running along +x from (0,0) to (3,0).
    m = FramedMember("F", "joist", "joist", "2x8", (0.0, 0.0), (3.0, 0.0),
                     z0_m=-cs.depth_m, z1_m=0.0, length_m=3.0)
    ring, z_lo, z_hi = member_footprint(m)
    dx, dy = _ring_extent(ring)
    assert dx == pytest.approx(3.0, abs=1e-6)          # along the span
    assert dy == pytest.approx(cs.width_m, abs=1e-6)   # thickness, not depth
    assert (z_lo, z_hi) == pytest.approx((-cs.depth_m, 0.0))


def test_member_footprint_vertical_is_width_by_depth():
    cs = cross_section("6x6")
    # A vertical 6x6 post oriented along +y.
    m = FramedMember("F", "post", "column", "6x6", (0.0, 0.0), (0.0, 0.0),
                     z0_m=0.0, z1_m=2.4, length_m=2.4, orient=(0.0, 1.0))
    ring, z_lo, z_hi = member_footprint(m)
    dx, dy = _ring_extent(ring)
    assert dx == pytest.approx(cs.width_m, abs=1e-6)
    assert dy == pytest.approx(cs.depth_m, abs=1e-6)
    assert (z_lo, z_hi) == pytest.approx((0.0, 2.4))


def test_member_footprint_raked_member_spans_min_max_z():
    m = FramedMember("F", "rafter", "rafter", "2x8", (0.0, 0.0), (4.0, 0.0),
                     z0_m=1.0, z1_m=1.2, length_m=4.0, z0_end_m=2.5, z1_end_m=2.7)
    _ring, z_lo, z_hi = member_footprint(m)
    assert z_lo == pytest.approx(1.0)
    assert z_hi == pytest.approx(2.7)


# -------------------------------------------------------------------- integration
@pytest.fixture(scope="module")
def catlin_model():
    result = load_plan(CATLIN_DIR)
    model, findings = resolve(result.plan)
    errors = [f for f in findings if f.severity.value == "error"]
    assert not errors, [f.message for f in errors]
    return model


def test_deck_stacks_post_beam_joist(catlin_model):
    tol = inch(0.25).meters
    solids = {s.tag: s for s in catlin_model.solids}
    post, beam = solids["PT-SG-BF1"], solids["BM-SG-BLW"]
    deck = next(f for f in catlin_model.floors if f.tag == "FS-SG-DECK")
    joist = next(m for m in deck.members if m.category == "joist")
    assert abs(post.z1_m - beam.z0_m) < tol   # post top meets beam soffit
    assert abs(beam.z1_m - joist.z0_m) < tol  # beam top meets joist underside


def test_outer_joist_spans_cantilever_six_inches(catlin_model):
    # Three beams 10' o.c. -> two 10' spans, each cantilevered 6" past the outer beam.
    deck = next(f for f in catlin_model.floors if f.tag == "FS-SG-DECK")
    spans = {round(m.length_m, 3) for m in deck.members if m.category == "joist"}
    expected = round(inch(120).meters + inch(6).meters, 3)
    assert spans == {expected}


# --------------------------------------------------------------------- regression
def test_deck_bearing_stack_has_no_interference():
    ctx, _ = build_context(load_plan(CATLIN_DIR).plan, CATLIN_DIR)
    deck_findings = [
        f for f in member_interference(ctx)
        if any(t.startswith(_DECK_PREFIXES) for t in f.element_tags)
    ]
    assert not deck_findings, [f.message for f in deck_findings]


def test_catlin_framing_interference_stays_near_zero():
    """Guards the ~2662 -> 0 cleanup (correct stud orientation, slope-aware z, intended
    corner/tee/bearing/stair joints). A small ceiling keeps it robust to model tweaks."""
    ctx, _ = build_context(load_plan(CATLIN_DIR).plan, CATLIN_DIR)
    findings = member_interference(ctx)
    assert len(findings) <= 5, [f.message for f in findings]


def test_check_still_flags_a_genuine_overlap():
    """The many intended-joint clears must not neuter the check: two beams sharing the
    same volume, away from any wall junction, is a real clash and must still report."""
    from types import SimpleNamespace

    a = FramedMember("B1", "beam", "beam", "2x10", (0.0, 0.0), (3.0, 0.0),
                     z0_m=0.0, z1_m=0.24, length_m=3.0)
    b = FramedMember("B2", "beam", "beam", "2x10", (0.5, 0.0), (3.5, 0.0),
                     z0_m=0.1, z1_m=0.34, length_m=3.0)
    model = SimpleNamespace(all_members=lambda: [a, b], solids=(), junctions=())
    prefs = SimpleNamespace(framing=SimpleNamespace(interference_tolerance_in=0.25))
    ctx = SimpleNamespace(model=model, preferences=prefs)
    assert member_interference(ctx)
