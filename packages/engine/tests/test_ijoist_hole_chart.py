"""The I-joist hole ladder (decision #117), on houses/catlin/notes/framing_bore_limits.md §11."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from typehaus.resolve.mep_bores import joist_bore

_TJI = "11.875 TJI 230"
_CHARTS = Path(__file__).resolve().parents[3] / "houses/catlin/plan/framing_charts.py"


@pytest.fixture(scope="module")
def chart():
    spec = importlib.util.spec_from_file_location("catlin_framing_charts", _CHARTS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.TJI_230_HOLES


def _bore(chart, od, centre, **kw):
    return joist_bore(_TJI, od, chart=chart, edge_to_support_in=centre, **kw)


def test_ladder_picks_the_row_and_grades_the_edge(chart) -> None:
    # §11.1: a 1 1/2" vent (hole 2.15, 3" row, 18") at x=108 against the 117.25" plate face.
    fail = _bore(chart, 1.9, 117.25 - 108)
    assert fail.ok is False and "8.18" in fail.basis and "18.00" in fail.basis
    assert _bore(chart, 1.9, 117.25 - 90).ok is True
    # §11.3: 1 1/4" PEX (hole 1.625) takes the 2" row: 12.44" off the face passes, 3.44 fails.
    assert _bore(chart, 1.375, 213.25 - 200).ok is True
    assert _bore(chart, 1.375, 213.25 - 209).ok is False


def test_field_hole_zone_and_footnote_one_spacing(chart) -> None:
    # §11.5: a 3/4" PEX hole (1.125) is a field hole, 6" from the face.
    assert _bore(chart, 0.875, 12 - 6).ok is False
    assert _bore(chart, 0.875, 13 - 6).ok is True
    # §11.1: 6.11" clear of a 2.625" neighbour passes (5.25); 1.2" does not.
    assert _bore(chart, 1.9, 30, nearest_cut_in=6.11, nearest_diameter_in=2.625).ok is True
    tight = _bore(chart, 1.9, 30, nearest_cut_in=1.2, nearest_diameter_in=2.625)
    assert tight.ok is False and "5.25" in tight.basis


def test_over_the_ladder_drift_and_no_chart(chart) -> None:
    assert _bore(chart, 9.0, 100).ok is False  # over 8 7/8"
    assert _bore(chart, 1.9, None).ok is None  # cantilever: Table B not transcribed
    drifted = joist_bore("11.875 TJI 360", 1.9, chart=chart, edge_to_support_in=50)
    assert drifted.ok is None and "TJI 230" in drifted.basis
    refusal = joist_bore(_TJI, 1.9)
    assert refusal.ok is None and "fabricator's chart" in refusal.basis


def test_a_joist_cut_on_a_support_axis_measures_from_its_face(catlin_model_ro) -> None:
    """§11: the resolver cuts a joist at its support's AXIS, so the face is the far edge of
    the plate or flush beam under the end, never the member end itself."""
    from typehaus.quantities import M_PER_IN
    from typehaus.resolve.mep_crossings import floor_supports, support_faces

    attic = next(f for f in catlin_model_ro.floors if f.tag == "FS-ATTIC")
    supports = floor_supports(catlin_model_ro, attic)
    faces = {}
    for member in attic.members:
        if member.category == "joist" and round(member.p0[1] / M_PER_IN) in (304, 336, 352):
            lo, hi = support_faces(attic, member, supports)
            faces[(round(member.p0[1] / M_PER_IN), round(min(member.p0[0], member.p1[0])
                                                          / M_PER_IN))] = (lo, hi)
    # West of FO-A-HALL: hi end on BM-S-BATH-E (y 304) or W-S-BA-E1B's plate (y 336).
    assert faces[(304, 2)][1] / M_PER_IN == pytest.approx(117.375, abs=0.01)
    assert faces[(336, 2)][1] / M_PER_IN == pytest.approx(117.25, abs=0.01)
    # East of it: the lo end hangs on BM-S-HALL's east face, not at the 216" axis.
    assert faces[(352, 216)][0] / M_PER_IN == pytest.approx(218.625, abs=0.01)
