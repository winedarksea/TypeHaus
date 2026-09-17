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
