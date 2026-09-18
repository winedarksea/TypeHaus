"""A ConduitRun rises at its LAST point, so the checks must see a flat run plus a riser there.

Read as one sloped segment, CD-B-ATTIC-RISER climbed diagonally through RM-S-BATH1's air.
"""

from __future__ import annotations

from types import SimpleNamespace

from typehaus.checks.mep.routing_geometry import run_polylines


def _ctx(*conduits):
    # `plan` is read by `run_polylines` for the VentRun risers, which a conduit fixture has
    # none of — but the reading is real and the fake has to answer it.
    model = SimpleNamespace(pipe_runs=(), ducts=(), conduits=conduits,
                            plan=SimpleNamespace(all_elements=lambda: ()))
    return SimpleNamespace(model=model)


def test_a_rising_conduit_is_flat_then_vertical_at_its_last_point():
    run = SimpleNamespace(tag="CD", path=((0.0, 0.0), (1.0, 2.0)), z_start_m=-1.0, z_end_m=6.0)
    [(_kind, _tag, path, z)] = run_polylines(_ctx(run))
    assert path == ((0.0, 0.0), (1.0, 2.0), (1.0, 2.0))
    assert z == (-1.0, -1.0, 6.0)


def test_a_level_conduit_keeps_its_own_vertices():
    run = SimpleNamespace(tag="CD", path=((0.0, 0.0), (1.0, 2.0)), z_start_m=3.0, z_end_m=3.0)
    [(_kind, _tag, path, z)] = run_polylines(_ctx(run))
    assert path == ((0.0, 0.0), (1.0, 2.0)) and z == (3.0, 3.0)
