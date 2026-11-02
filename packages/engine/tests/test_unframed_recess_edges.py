"""A finish relief may reach a wall end without weakening the framed-opening rule."""
from types import SimpleNamespace

import pytest

from typehaus.checks.integrity.checks import opening_fits_host


@pytest.mark.parametrize("right_edge,depth,framed,passes", [
    (3.0, 0.02, False, True),
    (3.01, 0.02, False, False),
    (3.0, 0.02, True, False),
    (3.0, None, True, False),
    (2.9, None, True, True),
])
def test_only_unframed_blind_recesses_can_terminate_at_the_host_end(
    right_edge, depth, framed, passes,
):
    opening = SimpleNamespace(
        tag="RELIEF", host_wall="W", center_along_m=right_edge - 0.1, width_m=0.2,
        frame_start_support_wall=None, frame_end_support_wall=None,
        depth_m=depth, framing_required=framed, pocket_run_m=0,
    )
    wall = SimpleNamespace(axis=((0, 0), (3, 0)))
    model = SimpleNamespace(openings=[opening], wall=lambda tag: wall)
    findings = opening_fits_host(SimpleNamespace(model=model, plan=None))
    assert (not findings) is passes
