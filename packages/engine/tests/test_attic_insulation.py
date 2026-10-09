"""The garage's blown fill is cut to the roof it lies under (resolve/attic_insulation.py)."""

from __future__ import annotations

import pytest

from typehaus.quantities import M_PER_IN
from typehaus.resolve.attic_insulation import VENT_SPACE_M
from typehaus.resolve.roof_geometry import roof_height_at, roof_slope_factor
from typehaus.resolve.sweep import leg_frame


def test_the_garage_blow_tapers_under_a_standard_heel(catlin_model_ro):
    solid = next(s for s in catlin_model_ro.solids if s.tag == "INSUL-CEIL-RM-GARAGE-1")
    roof = next(r for r in catlin_model_ro.roofs if r.tag == "RF-GARAGE")
    assert solid.sweep is not None, "a flat prism pokes through the top chords at the eave"
    depths = [v for _u, v in solid.sweep.profile]
    assert max(depths) == pytest.approx(14.5 * M_PER_IN), "the field keeps its settled depth"
    start, end = solid.sweep.path[0], solid.sweep.path[-1]
    right, _up = leg_frame(tuple(b - a for a, b in zip(start, end, strict=True)))
    gap = VENT_SPACE_M * roof_slope_factor(roof)
    edges = []
    for u, v in solid.sweep.profile:
        if v <= 0.0:
            continue
        xy = (start[0] + right[0] * u, start[1] + right[1] * u)
        # R806.3: a vent space between the fill and the deck, everywhere.
        assert start[2] + v <= roof_height_at(roof, xy) - gap + 1e-6
        edges.append((abs(u), v))
    # At the wall's inside face the blow is the heel's depth, not the field's.
    assert max(edges)[1] < 9.0 * M_PER_IN
