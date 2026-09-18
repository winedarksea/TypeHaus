"""``mep.drain_inlet_spacing`` — and what an honest UNKNOWN looks like.

catlin's ``mep_drainage.py`` claims the attic branch and the suite WC branch are "two inlets
on one barrel, not a double fitting at one point". They land 2½" apart. Nothing tested the
claim, and nothing CAN settle it: every ``center_to_face_in`` in ``library/fittings.py`` is
``None`` with a ``data_note`` saying no manufacturer submittal has been read.

So these pin two things, and the second is the important one: that the pair is found, and
that the verdict never hardens into a FAIL on a dimension the engine invented.
"""

from __future__ import annotations

import pytest

from typehaus.checks.mep.drain_inlet_spacing import (
    INLET_SCREEN_DIAMETERS,
    drain_inlet_spacing,
)

pytestmark = pytest.mark.slow


def test_catlin_names_the_suite_stack_inlets_and_the_datum_it_lacks(catlin_ctx) -> None:
    findings = drain_inlet_spacing(catlin_ctx)
    named = [f for f in findings
             if "PR-A-STUBATH-DRAIN" in f.element_tags
             and "PR-M-S-SUITE-WC-DRAIN" in f.element_tags]
    assert len(named) == 1, "the pair the authored comment makes a claim about"
    finding = named[0]
    assert finding.result.value == "unknown"
    assert '2.50" apart' in finding.message
    assert "center_to_face_in" in finding.message
    assert "PR-M-S-SUITE-DRAIN" in finding.element_tags, "the barrel is named too"


def test_it_is_NEVER_a_fail(catlin_ctx) -> None:
    """Whether two wyes fit 2½" apart is a question about laying length, and the catalog
    records none. The engine can say that it cannot say. Inventing a dimension to turn this
    into a FAIL would be worse than the silence it replaces."""
    assert not [f for f in drain_inlet_spacing(catlin_ctx) if f.result.value == "fail"]


def test_the_screen_is_a_stated_convention_not_a_read_dimension() -> None:
    """Three barrel diameters clears a full-sweep fitting body on the larger pipe — the same
    convention ``run_interference.JOINT_REACH_FACTOR`` states, and for the same reason."""
    from typehaus.checks.mep.run_interference import JOINT_REACH_FACTOR

    assert INLET_SCREEN_DIAMETERS == JOINT_REACH_FACTOR == 3.0


def test_inlets_further_apart_than_the_screen_raise_no_question(catlin_ctx) -> None:
    """A stack with branches a foot apart is ordinary work and must not be reported."""
    from typehaus.checks.mep.drain_inlet_spacing import _barrels, _inlets_on

    for tag, point, z0_m, z1_m, diameter_m in _barrels(catlin_ctx):
        inlets = sorted(_inlets_on(catlin_ctx, tag, point, z0_m, z1_m))
        wide = [(a, b) for a, b in zip(inlets[:-1], inlets[1:], strict=False)
                if b[0] - a[0] > INLET_SCREEN_DIAMETERS * diameter_m]
        for (_low_z, low_tag), (_high_z, high_tag) in wide:
            assert not [f for f in drain_inlet_spacing(catlin_ctx)
                        if low_tag in f.element_tags and high_tag in f.element_tags]
