"""Framing bearing-stack fix + model-wide interference guard (plan: framing
interference warning + deck bearing-stack fix).

- unit: ``member_footprint`` returns a thickness-wide ring + z-band per member kind.
- integration: the resolved catlin deck stacks post → beam → joist, and the outer
  joist spans cantilever 6" past the outer beams.
- regression: ``structural.member_interference`` reports zero findings from the deck
  bearing stack once the arithmetic is correct.
"""

from __future__ import annotations


import pytest

from typehaus.checks import build_context
from typehaus.checks.structural.interference import member_interference
from typehaus.quantities import inch
from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import FramedMember
from typehaus.source import load_plan
from _helpers import CATLIN as CATLIN_DIR


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


def test_stair_support_framing_reports_no_interference():
    """The landing posts, winder newel/carriages and turn header must be *joints*, not
    clashes. Sharper than the global ceiling below: it cannot be satisfied by the check
    happening to stay under five findings elsewhere."""
    ctx, _ = build_context(load_plan(CATLIN_DIR).plan, CATLIN_DIR)
    # A member's label is "{parent_uid}:{child_key}", so match the stair's uid.
    stair_uids = {stair.uid for stair in ctx.model.stairs}
    stair_findings = [f for f in member_interference(ctx)
                      if any(t.split(":")[0] in stair_uids for t in f.element_tags)]
    assert not stair_findings, [f.message for f in stair_findings]


def test_balcony_knee_braces_are_not_a_clash():
    """The braces leave the post *face* and stop at the soffit, so nothing overlaps.

    Both ends are where a clash would come from: an end buried in the 6x6 shares more plan
    area than the tolerance allows (and sits too far inside the column for the butt-joint
    exemption), and a brace run past the soffit would share volume with the member it braces.
    """
    ctx, _ = build_context(load_plan(CATLIN_DIR).plan, CATLIN_DIR)
    brace_findings = [f for f in member_interference(ctx)
                      if any("KB-SG" in tag or "GIRT" in tag for tag in f.element_tags)]
    assert not brace_findings, [f.message for f in brace_findings]


def test_catlin_framing_interference_stays_near_zero():
    """Guards the ~2662 -> 0 cleanup (correct stud orientation, slope-aware z, intended
    corner/tee/bearing/stair joints), then the centreline exclusion-band fix that took the
    last two same-wall stud/king clashes to zero. A small ceiling keeps it robust to
    model tweaks."""
    ctx, _ = build_context(load_plan(CATLIN_DIR).plan, CATLIN_DIR)
    findings = member_interference(ctx)
    assert len(findings) <= 2, [f.message for f in findings]


def test_tudor_posts_within_their_wall_are_not_a_clash():
    """The suite's four elm timbers stand in W-S-W3's stud line (``Post.within_wall``):
    the framer cuts the plates and studs around them, so their shared volume with that
    one wall's framing is the cut, not an elevation bug. The clearance is authored —
    remove ``within_wall`` and the same posts report against all three plates."""
    ctx, _ = build_context(load_plan(CATLIN_DIR).plan, CATLIN_DIR)
    tudor = [f for f in member_interference(ctx)
             if any("TUDOR" in tag for tag in f.element_tags)]
    assert not tudor, [f.message for f in tudor]


# A window opening's own framing pack, by child-key prefix ("king-0-l0", "header-0", …).
_OPENING_FRAMING_KEYS = ("king-", "jack-", "header-", "sill-")


def test_catlin_window_member_overlaps_pinned_at_four():
    """The 4 residual window/member overlaps, pinned (plans/TODO.md "Windows: 8 residual").

    Measured with the junction-proximity clear disabled — the honest metric the TODO
    records, since every one of these sits at a junction and would otherwise be silently
    cleared. The TODO's prose summarised them as 4 at two L corners + 4 at one T; the walls
    have moved since and the measured composition today is:

    - 2 at one T: CSW148's king stud against the neighbouring walls' end studs
      (CSW145:stud-008, CSW146:stud-000) — the jamb sits at the junction.
    - 1 at an L corner: CMW103:stud-008 against CMW104:king-0-l0 — the neighbouring
      wall's 1.5" stud/plate elevation mismatch.
    - 1 raked: CSW141:king-0-r0 against the stair soffit's bottom plate
      (CSF601AAAA:soffit-plate-bottom-e).

    That T was 6 until 2026-08-22, when O-S-VANITY (CSW148's only opening) moved from 3" to
    4 5/8" off N-S-V1: at 3" its whole jamb pack — king, jack and header — stood inside the
    corner square the 8" sound wall grew on 2026-08-21, and the opening's first inch was
    being cut out of framing rather than out of the wall. Clear of the square, only the king
    still meets the neighbours' end studs, which is the ordinary T geometry.

    The count is the regression guard (historic: 138 -> 8 -> 4); the docstring is the map
    for whoever moves it."""
    ctx, _ = build_context(load_plan(CATLIN_DIR).plan, CATLIN_DIR)
    ctx.model.junctions = []  # disable the junction-proximity clear
    window_findings = [
        f for f in member_interference(ctx)
        if any(t.split(":")[-1].startswith(_OPENING_FRAMING_KEYS)
               for t in f.element_tags)
    ]
    assert len(window_findings) == 4, sorted(
        f.element_tags for f in window_findings)


def _stair_beside_wall_member(kind: str):
    """A stringer running along a wall member of ``kind``, sharing its volume.

    The overlap is the D3 offset every stair member on catlin has against the wall beside
    it: stair framing is laid out to the host wall's *axis*, so it sits inside the stud
    cavity. ``_STAIR_SUPPORT`` clears that for studs, plates and headers; ``sill`` — the
    bottom of a rough opening, the same wall framing on the same centreline — was missing
    from the set, so a flight running past a window would have reported. No catlin wall
    beside a stair hosts an opening, which is exactly why the gap was invisible here.
    """
    from types import SimpleNamespace

    stringer = FramedMember("ST-1", "stringer-0", "stringer", "2x12", (0.0, 0.0), (3.0, 0.0),
                            z0_m=0.9, z1_m=1.2, length_m=3.0)
    wall_member = FramedMember("W-1", kind, kind, "2x6", (0.02, 0.0), (2.0, 0.0),
                               z0_m=1.0, z1_m=1.14, length_m=2.0)
    model = SimpleNamespace(all_members=lambda: [stringer, wall_member], solids=(),
                            junctions=())
    prefs = SimpleNamespace(framing=SimpleNamespace(interference_tolerance_in=0.25))
    return SimpleNamespace(model=model, preferences=prefs)


def test_stair_past_a_rough_opening_sill_is_not_a_clash():
    """Regression for the missing ``sill`` entry in ``_STAIR_SUPPORT``."""
    from typehaus.checks.structural.interference import _STAIR_SUPPORT

    assert "sill" in _STAIR_SUPPORT
    assert not member_interference(_stair_beside_wall_member("sill"))
    # Same geometry, same wall: the neighbouring stud and header were always cleared, so
    # the sill was the odd one out rather than the fixture being too permissive.
    for cleared in ("stud", "header", "king"):
        assert not member_interference(_stair_beside_wall_member(cleared)), cleared


def test_a_stringer_buried_in_a_beam_is_still_a_clash():
    """The ``sill`` clearance must not neuter the rule: a stringer sharing volume with a
    beam is a genuine elevation bug and still reports."""
    assert member_interference(_stair_beside_wall_member("beam"))


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


def _flush_candidates(joist_kind: str):
    """A deck member of ``joist_kind`` hung flush in its own pinned beam."""
    from shapely.geometry import box

    from typehaus.checks.structural.interference import _Candidate

    joist = _Candidate("FS-1:joist-000", box(0.0, 0.0, 3.0, 0.04), 0.0, 0.184,
                       seg=((0.0, 0.02), (3.0, 0.02)), kind=joist_kind, parent="FS-1")
    beam = _Candidate("BM-1", box(-0.1, -0.05, 3.1, 0.02), 0.0, 0.184,
                      seg=((-0.1, 0.0), (3.1, 0.0)), kind="beam", parent="BM-1")
    return joist, beam


def test_a_sistered_ply_hangs_flush_where_its_joist_does():
    """A reinforcing ply is the same stock in the same hanger as the line it doubles.

    ``_flush_framed_pairs`` keys on the *floor system*, so both plies of a reinforced line
    belong to the same authored pair — but the resolver gives the extra plies category
    ``sister_joist``, which the kind test used to exclude. On catlin that is PT-SG-BR2's
    3-ply cluster against the two flush front beams: two findings for a joinery detail the
    single-ply line beside it is already cleared for.
    """
    from typehaus.checks.structural.interference import _flush_framed_into_beam

    pairs = {("FS-1", "BM-1")}
    for kind in ("joist", "sister_joist"):
        joist, beam = _flush_candidates(kind)
        assert _flush_framed_into_beam(joist, beam, pairs), kind
        assert _flush_framed_into_beam(beam, joist, pairs), kind  # order-independent
    # Still authored, never guessed: an unpinned beam (absent from the pair set) reports.
    joist, beam = _flush_candidates("sister_joist")
    assert not _flush_framed_into_beam(joist, beam, set())
