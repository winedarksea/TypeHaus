"""The router grades a new I-joist hole against the authored holes in the same joist.

``houses/catlin/notes/framing_bore_limits.md`` §11: ESR-1153 Table A fn 1, clear distance
between holes >= 2 x the largest hole, the drilled hole OD + 1/4". ``PR-B-CW-SAUNA`` (1/2"
PEX, hole 0.875") crosses FS-M-WEST at x = 206.5"; a second 1/2" line needs 2 x 0.875 =
1.75" clear, i.e. 1.75 + 0.875 = 2.625" centre to centre. Both probes sit outside the 6"
support zone (213.25 - 205.0 - 0.4375 = 7.81"), so only the spacing differs."""

from __future__ import annotations

from typehaus.quantities import M_PER_IN
from typehaus.routing.members import Penetrations, _ijoist_bores_ok

PEX_HALF_OD_M = 0.625 * M_PER_IN


def _floor(model, touch=frozenset()):
    pen = Penetrations(model, (190 * M_PER_IN, 0.0, 215 * M_PER_IN, 430 * M_PER_IN),
                       PEX_HALF_OD_M / 2.0, touch=touch)
    return next(f for f in pen.floors if f.tag == "FS-M-WEST")


def _sauna_joist(model):
    floor = _floor(model)
    index = next(i for i, holes in enumerate(floor.holes)
                 if any(abs(s / M_PER_IN - 206.5) < 0.1 for s, _r in holes))
    return floor, index


def test_a_hole_too_near_an_authored_one_is_refused(catlin_model_ro):
    floor, i = _sauna_joist(catlin_model_ro)
    station = 206.5 * M_PER_IN
    assert not _ijoist_bores_ok(floor, [i], station - 1.5 * M_PER_IN, PEX_HALF_OD_M)  # 0.625"
    assert _ijoist_bores_ok(floor, [i], station - 3.0 * M_PER_IN, PEX_HALF_OD_M)  # 2.125"


def test_a_run_being_replaced_is_no_neighbour(catlin_model_ro):
    floor, i = _sauna_joist(catlin_model_ro)
    clear = _floor(catlin_model_ro, touch=frozenset({"PR-B-CW-SAUNA"}))
    others = [s for s, _r in clear.holes[i] if abs(s / M_PER_IN - 206.5) < 0.1]
    assert len(clear.holes[i]) == len(floor.holes[i]) - 1 and not others
