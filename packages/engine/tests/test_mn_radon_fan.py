"""MN 1303.2402 subp. 6 (the fan's circuit) and 5.D (its 24" x 3 ft space) on catlin."""

from __future__ import annotations

from typehaus.checks.code.mn_residential.radon import radon_control_system
from typehaus.checks.code.mn_residential.radon_fan import (
    fan_power_finding,
    fan_space_findings,
)
from typehaus.findings import Result
from typehaus.quantities import inch
from typehaus.resolve.vent_termination import exterior_riser_point


def _stack(ctx, **update):
    return ctx.plan.by_tag("VR-M-STACK").model_copy(update=update)


def test_a_box_that_is_merely_near_is_not_a_fan_circuit(catlin_ctx) -> None:
    unnamed = _stack(catlin_ctx, fan_power_ref=None)
    found = fan_power_finding(catlin_ctx, unnamed, exterior_riser_point(unnamed))
    assert found.result is Result.UNKNOWN and "ED-A-PV-JB" in found.message
    # No circuit, then a PV source feed: neither powers a fan.
    for ref in ("ED-A-PV-SPD", "ED-A-PV-JB"):
        riser = _stack(catlin_ctx, fan_power_ref=ref)
        found = fan_power_finding(catlin_ctx, riser, exterior_riser_point(riser))
        assert found.result is Result.FAIL, (ref, found.message)


def test_a_pipe_inside_the_fan_circle_fails_5d(catlin_ctx) -> None:
    """At 8" c-c the radon leg's 24" circle takes in the vent leg beside it."""
    tight = _stack(catlin_ctx, exit_bundle_spacing=inch(-8))
    found = [f for f in fan_space_findings(catlin_ctx, tight) if f.result is Result.FAIL]
    assert found and "VR-M-STACK-vent" in found[0].message


def test_catlin_passes_both_fan_subparts(catlin_ctx) -> None:
    found = radon_control_system(catlin_ctx)
    assert {f.result for f in found} == {Result.PASS}, [f.message for f in found]
    messages = " ".join(f.message for f in found)
    assert "ED-A-RADON-JB powers VR-M-STACK's future fan on CKT-RC-ATTIC" in messages
    assert "clear cylinder from 23'-10.0\"" in messages
