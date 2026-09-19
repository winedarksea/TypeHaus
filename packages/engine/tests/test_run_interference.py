"""``mep.run_interference`` — two runs may not occupy the same space.

The predicate is envelope against envelope, and the three exemptions are earned from the
model rather than from a naming convention. These pin the exemptions, because an
interference check that is too eager is one people switch off.
"""

from __future__ import annotations

import pytest

from typehaus.checks.mep.run_interference import TOUCH_TOLERANCE_M, run_interference
from typehaus.resolve.mep_envelopes import (
    JOINT_BAND_PAD_M,
    run_envelope,
    runs_are_joined,
)

pytestmark = pytest.mark.slow


def _track(path, z):
    return (tuple(path), tuple(z))


def test_a_run_that_ENDS_on_another_is_a_fitting_and_not_a_clash() -> None:
    """A wye, a tee, an elbow, a riser into a trunk. Only an END counts — two runs crossing
    mid-span are two runs crossing, and that is the case this check exists to report."""
    trunk = _track([(0.0, 0.0), (5.0, 0.0)], [2.0, 2.0])
    branch = _track([(2.5, 3.0), (2.5, 0.0)], [2.0, 2.0])
    assert runs_are_joined(trunk, branch) is True

    crossing = _track([(2.5, 3.0), (2.5, -3.0)], [2.0, 2.0])
    assert runs_are_joined(trunk, crossing) is False


def test_an_envelope_is_one_prism_per_segment_over_its_own_z_range() -> None:
    """The defect this replaces: a branch that drops six feet at one end used to block a
    full-height wall along its whole length, which is how a clear lane came back as
    "every lane is blocked"."""
    envelope = run_envelope(
        "pipe", "PR-X",
        [(0.0, 0.0), (0.0, 0.0), (4.0, 0.0)], [3.0, 0.5, 0.5],
        (0.05, 0.05, None))
    assert len(envelope.prisms) == 2
    riser, flat = envelope.prisms
    assert riser.z1_m - riser.z0_m == pytest.approx(2.5 + 2 * 0.05)
    assert flat.z1_m - flat.z0_m == pytest.approx(2 * 0.05)


def test_an_insulation_spec_with_no_thickness_is_a_gap_and_not_a_guess() -> None:
    """An R-value is a thermal claim and an envelope is a dimensional one."""
    bare = run_envelope("duct", "DU-X", [(0.0, 0.0), (2.0, 0.0)], [2.0, 2.0],
                        (0.1, 0.1, "R-8 wrap"))
    assert any("states no thickness" in gap for gap in bare.gaps)
    lagged = run_envelope("pipe", "PR-X", [(0.0, 0.0), (2.0, 0.0)], [2.0, 2.0],
                          (0.05, 0.05, '1" fiberglass sleeve'))
    assert not lagged.gaps
    assert lagged.prisms[0].z1_m - 2.0 == pytest.approx(0.05 + 0.0254)


def test_a_schematic_raceway_is_disclosed_and_never_graded(catlin_ctx) -> None:
    """Two end elevations say nothing about the six feet between. Grading that against the
    "rises at its last point" convention reports clashes with a drawing rather than with a
    building.

    **Catlin has none left.** All seventeen raceways authored ``ConduitRun.elevations`` on
    2026-09-19 (E7), so the disclosure has nothing to disclose here and the runs are graded
    where they are. The mechanism is pinned on a model built for it instead, so the day a
    house authors a schematic raceway again the guarantee still holds."""
    from typehaus.resolve.mep_queries import schematic_conduits

    assert schematic_conduits(catlin_ctx.model) == (), \
        "every catlin raceway states a per-vertex profile"
    assert not [f for f in run_interference(catlin_ctx)
                if f.result.value == "unknown"], "nothing left to disclose"


def test_a_schematic_raceway_IS_still_recognised_where_one_exists() -> None:
    """The mechanism, not the house: a raceway whose z count does not match its vertex
    count is a reconstruction, and ``run_interference`` drops it from the pair loop and
    names it as a coverage gap instead. Catlin has none left; the guarantee has not moved."""
    from types import SimpleNamespace

    from typehaus.resolve.mep_queries import schematic_conduits

    placed = SimpleNamespace(tag="CD-PLACED", path=((0.0, 0.0), (1.0, 0.0)),
                             z_m=(1.0, 1.0))
    schematic = SimpleNamespace(tag="CD-SCHEMATIC", path=((0.0, 0.0), (1.0, 0.0)),
                                z_m=None)
    short = SimpleNamespace(tag="CD-SHORT", path=((0.0, 0.0), (1.0, 0.0), (2.0, 0.0)),
                            z_m=(1.0, 1.0))
    model = SimpleNamespace(conduits=[placed, schematic, short])
    assert schematic_conduits(model) == ("CD-SCHEMATIC", "CD-SHORT")


def test_the_touch_tolerance_is_the_grid_this_repo_authors_on() -> None:
    """Two runs drawn to touch are drawn to touch. A sixteenth of an inch."""
    assert TOUCH_TOLERANCE_M == pytest.approx(0.0015875)


def test_the_joint_exemption_is_LOCAL_to_the_joint_and_not_a_pardon_for_the_pair() -> None:
    """A pair jointed at one end used to be exempt everywhere, because the exemption was a
    single bool for the pair. Two runs joined at one end and crossing at the other are one
    fitting and one clash, and only the clash is reported."""
    from typehaus.resolve.mep_envelopes import run_joints

    trunk = _track([(0.0, 0.0), (0.0, 6.0)], [2.0, 2.0])
    # Ends ON the trunk at (0, 0), doubles back and crosses it again three metres north.
    branch = _track([(0.0, 0.0), (2.0, 0.0), (2.0, 3.0), (-1.0, 3.0)], [2.0, 2.0, 2.0, 2.0])
    joints = run_joints(trunk, branch)
    assert len(joints) == 1
    (point, low, high), = joints
    assert point == (0.0, 0.0)
    # A BAND, not the vertex: both runs are level at 2.0 here, so the intersection of their
    # two adjacent-segment ranges is the point 2.0, padded by JOINT_BAND_PAD_M either way.
    assert low == pytest.approx(2.0 - JOINT_BAND_PAD_M)
    assert high == pytest.approx(2.0 + JOINT_BAND_PAD_M)
    assert runs_are_joined(trunk, branch) is True

    findings = _findings_for({"PR-TRUNK": trunk, "PR-BRANCH": branch},
                             {"PR-TRUNK": (0.05, 0.05, None), "PR-BRANCH": (0.05, 0.05, None)})
    fails = [f for f in findings if f.result.value == "fail"]
    assert len(fails) == 1
    # The crossing, three metres from the joint — not the joint itself.
    assert "leg 3 of PR-BRANCH" in fails[0].message or "leg 2 of PR-TRUNK" in fails[0].message


def test_a_joint_is_pardoned_within_a_fittings_reach_and_no_further() -> None:
    """A joint is a point and a fitting is a body, so some reach is owed. The reach is a
    STATED convention — three times the larger half-section — because the catalog records no
    laying length; it is not a dimension read off a submittal."""
    from typehaus.checks.mep.run_interference import JOINT_REACH_FACTOR

    assert JOINT_REACH_FACTOR == 3.0
    trunk = _track([(0.0, 0.0), (0.0, 6.0)], [2.0, 2.0])
    # Ends on the trunk, runs east, and comes back to graze it 0.1 m north — inside reach.
    near = _track([(0.0, 0.0), (0.5, 0.0), (0.5, 0.1), (-0.06, 0.1)], [2.0] * 4)
    sections = {"PR-TRUNK": (0.05, 0.05, None), "PR-NEAR": (0.05, 0.05, None)}
    fails = [f for f in _findings_for({"PR-TRUNK": trunk, "PR-NEAR": near}, sections)
             if f.result.value == "fail"]
    assert not fails, "0.1 m is inside 3 x 0.05 m of the joint — that is the fitting"


def test_catlin_reports_the_suite_stack_head_crossing(catlin_ctx) -> None:
    """The measurement this whole change was made for: two 3" drains essentially on top of
    each other, two feet from the stack head they share. Invisible while the exemption was
    a single bool for the pair.

    **Re-measured by hand on 2026-09-19**, when the reading stopped being prism-against-
    prism. The old pair of numbers — 2.21" in plan, 5.00" in elevation — were read off two
    BANDED boxes, and 5.00" was never reachable: these are 3" DWV, 3.50" outside, so two of
    them share at most 3.50" of elevation even drawn concentric. What is there is a single
    station where the two centrelines are 0.86" apart in plan and 0.9" apart in z, which
    puts 2.64" of each pipe inside the other on both axes.
    """
    message = next(
        (f.message for f in run_interference(catlin_ctx)
         if f.result.value == "fail"
         and "PR-A-STUBATH-DRAIN" in f.element_tags
         and "PR-M-S-SUITE-WC-DRAIN" in f.element_tags), None)
    assert message is not None, "the crossing at the suite stack head is reported"
    assert '2.64" inside each other in plan' in message
    assert '2.64" in elevation' in message
    # Both centrelines, at the station — the two numbers a plan file authors.
    assert "runs at 9'-7.3\"" in message and "at 9'-6.4\"" in message
    # Leg for leg, as it was measured by hand. The legs are named in PAIR order, which the
    # message did not do: it hung the first run's leg number off the second run's name.
    assert "leg 3 of PR-A-STUBATH-DRAIN" in message
    assert "leg 2 of PR-M-S-SUITE-WC-DRAIN" in message


def _findings_for(tracks, sections):
    """Run the check over a hand-built pair of tracks, with nothing else in the model."""
    from types import SimpleNamespace

    from typehaus.checks.mep import run_interference as module

    model = SimpleNamespace(plan=SimpleNamespace(all_elements=lambda: ()),
                            walls=[], openings=[])
    ctx = SimpleNamespace(model=model)
    envelopes = [run_envelope("pipe", tag, path, z, sections[tag])
                 for tag, (path, z) in tracks.items()]
    import typehaus.resolve.mep_envelopes as env
    import typehaus.resolve.mep_queries as queries

    old_env, old_sections, old_gaps = env.envelopes, env.run_sections, queries.schematic_conduits
    old_lines = env.run_polylines
    try:
        env.envelopes = lambda _model, **_kw: envelopes
        env.run_sections = lambda _model: sections
        env.run_polylines = lambda _model: [("pipe", tag, path, z)
                                            for tag, (path, z) in tracks.items()]
        queries.schematic_conduits = lambda _model: ()
        return module.run_interference(ctx)
    finally:
        env.envelopes, env.run_sections, env.run_polylines = old_env, old_sections, old_lines
        queries.schematic_conduits = old_gaps


# --------------------------------------------------------------------------------------
# E1 / E2 — the band stops being the verdict (2026-09-19). Hand-checks, pinned.
# --------------------------------------------------------------------------------------


def _seg(a, b, za, zb, half=0.05):
    from typehaus.resolve.mep_clearance import Segment

    return Segment(tag="X", index=0, a=a, b=b, za=za, zb=zb,
                   half_w_m=half, half_d_m=half)


def test_a_falling_leg_that_clears_at_the_crossing_is_not_a_clash() -> None:
    """The twenty-five. ``PR-B-KITCH-DRAIN``'s sixth leg falls 13.6" over its length and
    passes 4.26" under ``DU-B-ERV-RET-TRUNK``. Banded over its whole fall it reads as a box
    that swallows the duct; measured at the station where they cross it is four inches of
    daylight.

    Same numbers here in metres: a leg falling 0.35 m across a level run, clearing it by
    0.108 m (4.26") where they actually meet."""
    from typehaus.resolve.mep_clearance import segment_clearance

    falling = _seg((0.0, 0.0), (4.0, 0.0), 2.30, 1.95)
    level = _seg((2.0, -1.0), (2.0, 1.0), 1.9168, 1.9168)
    # PRISM AGAINST PRISM THEY OVERLAP, which is the whole complaint: the falling leg bands
    # 1.90 .. 2.35 over its entire length and the level run bands 1.8668 .. 1.9668.
    assert min(2.35, 1.9668) - max(1.90, 1.8668) > 0
    # MEASURED AT THE CROSSING they miss: the falling leg is at 2.125 there, the level run
    # at 1.9168, and 0.2082 m of centreline gap less 0.10 m of combined half-section is
    # 0.1082 m — 4.26" of daylight.
    assert (2.125 - 1.9168) - 0.10 == pytest.approx(0.1082, abs=1e-4)
    assert segment_clearance(falling, level) is None


def test_a_riser_through_a_level_run_is_still_a_clash() -> None:
    """The other half of the same sentence: a riser really does occupy its whole fall at one
    plan point, so banding it states where it is rather than claiming where it is not."""
    from typehaus.resolve.mep_clearance import segment_clearance

    riser = _seg((2.0, 0.0), (2.0, 0.0), 0.0, 3.0)
    level = _seg((0.0, 0.0), (4.0, 0.0), 1.5, 1.5)
    contact = segment_clearance(riser, level)
    assert contact is not None
    assert contact.score_m == pytest.approx(0.10)  # dead centre, both half-sections
    assert contact.point == pytest.approx((2.0, 0.0))


def test_a_riser_teeing_into_a_horizontal_is_jointed_at_the_TEE() -> None:
    """E2. The riser's own vertex is at the BOTTOM of its drop; the joint is where it lands.

    Four of catlin's 146 were this: a joint recorded ten feet below the fitting it names, so
    the z test refused it and the crossing at the tee reported as a clash. The band is the
    intersection of the riser's own segment range with the matched horizontal's."""
    from typehaus.resolve.mep_envelopes import run_joints

    trunk = _track([(0.0, 0.0), (5.0, 0.0)], [3.0, 3.0])
    riser = _track([(2.5, 0.0), (2.5, 0.0)], [3.0, 0.0])
    (point, low, high), = run_joints(trunk, riser)
    assert point == (2.5, 0.0)
    # The riser spans 0..3 and the trunk sits at 3. The INTERSECTION is 3 — the tee — and
    # not the union, which would pardon every contact those two have in three vertical
    # metres.
    assert low == pytest.approx(3.0 - JOINT_BAND_PAD_M)
    assert high == pytest.approx(3.0 + JOINT_BAND_PAD_M)


def test_a_joint_pardons_its_own_LOBE_and_not_a_sliver_at_its_edge() -> None:
    """A tee's two envelopes overlap in one connected stretch either side of the fitting.
    Carving a fixed reach out of the middle of that stretch leaves slivers at both ends, and
    a sliver of the fitting is not a second defect."""
    from typehaus.resolve.mep_clearance import segment_clearance

    # A branch running INTO a trunk, ending on it: one lobe, centred on the joint.
    branch = _seg((2.5, 2.0), (2.5, 0.0), 1.0, 1.0)
    trunk = _seg((0.0, 0.0), (5.0, 0.0), 1.0, 1.0)
    joints = (((2.5, 0.0), 0.9, 1.1),)
    assert segment_clearance(branch, trunk, joints=joints, joint_reach_m=0.15) is None
    # The lobe is 0.10 m of overlap either side of the joint and the reach is 0.15 m, so a
    # station-by-station carve would have pardoned the middle and reported both ends.
    assert segment_clearance(branch, trunk) is not None, "without the joint it is a contact"
    # A joint somewhere ELSE pardons nothing: the exemption is local, which is the sentence
    # the whole three-tuple exists to make.
    elsewhere = (((2.5, 9.0), 0.9, 1.1),)
    assert segment_clearance(branch, trunk, joints=elsewhere, joint_reach_m=0.15) is not None
