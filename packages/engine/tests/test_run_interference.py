"""``mep.run_interference`` — two runs may not occupy the same space.

The predicate is envelope against envelope, and the three exemptions are earned from the
model rather than from a naming convention. These pin the exemptions, because an
interference check that is too eager is one people switch off.
"""

from __future__ import annotations

import pytest

from typehaus.checks.mep.run_interference import TOUCH_TOLERANCE_M, run_interference
from typehaus.resolve.mep_envelopes import run_envelope, runs_are_joined

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
    building — 100-odd of them on catlin."""
    from typehaus.resolve.mep_queries import schematic_conduits

    gaps = schematic_conduits(catlin_ctx.model)
    assert gaps, "catlin authors no ConduitRun.elevations yet"
    findings = run_interference(catlin_ctx)
    unknowns = [f for f in findings if f.result.value == "unknown"]
    assert unknowns, "the gap is reported, not swallowed"
    assert all(tag not in f.element_tags
               for f in findings if f.result.value == "fail"
               for tag in gaps)


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
    (point, z), = joints
    assert point == (0.0, 0.0) and z == pytest.approx(2.0)
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
    """The measurement this whole change was made for: a 3" drain 2.21" inside another 3"
    drain, two feet from the stack head they share. Invisible while the exemption was a
    single bool for the pair."""
    message = next(
        (f.message for f in run_interference(catlin_ctx)
         if f.result.value == "fail"
         and "PR-A-STUBATH-DRAIN" in f.element_tags
         and "PR-M-S-SUITE-WC-DRAIN" in f.element_tags), None)
    assert message is not None, "the crossing at the suite stack head is reported"
    assert '2.21" of overlap in plan' in message
    assert '5.00" of elevation' in message
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
