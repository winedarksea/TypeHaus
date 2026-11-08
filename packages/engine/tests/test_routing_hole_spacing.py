"""The router grades a new hole against the holes already there: authored runs and runs
laid earlier in the campaign (``routing/holes``), and a bearing-line box's window.

``houses/catlin/notes/framing_bore_limits.md`` §11: ESR-1153 Table A fn 1, clear distance
between holes >= 2 x the largest hole, the drilled hole OD + 1/4". ``PR-B-CW-SAUNA`` (1/2"
PEX, hole 0.875") crosses FS-M-WEST at x = 206.5"; a second 1/2" line needs 2 x 0.875 =
1.75" clear, i.e. 1.75 + 0.875 = 2.625" centre to centre. Both probes sit outside the 6"
support zone (213.25 - 205.0 - 0.4375 = 7.81"), so only the spacing differs.

FS-M-NE: ``PR-B-CW-TRUNK`` passes D pocket D11 of joist-0-009-0 (y = 300") at x = 357.6",
z = -8.8"; the triangle holds (360", -6") too, and takes one run (``mep.open_web_panel``).
Its bearing bay ``bearing-block-0-009`` is clear y = 301.75 .. 314.25", the block x = 215.25
.. 218.75", the box's top rail 1 1/2" under the deck at z = 0 (``mep.run_through_blocking``)."""

from __future__ import annotations

from typehaus.quantities import M_PER_IN
from typehaus.routing.bearing_bays import BearingBays
from typehaus.routing.holes import ijoist_bores_ok as _ijoist_bores_ok
from typehaus.routing.holes import run_lines
from typehaus.routing.members import Penetrations

PEX_HALF_OD_M = 0.625 * M_PER_IN


def _floor(model, touch=frozenset(), laid=()):
    pen = Penetrations(model, (190 * M_PER_IN, 0.0, 215 * M_PER_IN, 430 * M_PER_IN),
                       PEX_HALF_OD_M / 2.0, touch=touch, laid=laid)
    return next(f for f in pen.floors if f.tag == "FS-M-WEST")


def _sauna_joist(model, **kw):
    floor = _floor(model, **kw)
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


def test_a_run_laid_this_campaign_is_a_neighbour(catlin_model_ro):
    laid = [line for line in run_lines(catlin_model_ro, frozenset())
            if line[0] == "PR-B-CW-SAUNA"]
    floor, i = _sauna_joist(catlin_model_ro, touch=frozenset({"PR-B-CW-SAUNA"}), laid=laid)
    assert not _ijoist_bores_ok(floor, [i], (206.5 - 1.5) * M_PER_IN, PEX_HALF_OD_M)


def _p(x, y, z):
    return (x * M_PER_IN, y * M_PER_IN, z * M_PER_IN)


def test_a_d_pocket_takes_one_run(catlin_model_ro):
    def cuts(touch=frozenset()):
        pen = Penetrations(catlin_model_ro, (330 * M_PER_IN, 280 * M_PER_IN, 380 * M_PER_IN,
                                             320 * M_PER_IN), 0.4375 * M_PER_IN, touch=touch)
        return pen.cuts(_p(360, 296, -6), _p(360, 304, -6), "y")

    assert cuts() is None
    assert cuts(frozenset({"PR-B-CW-TRUNK"})) is not None


def test_a_bearing_box_passes_only_its_window(catlin_model_ro):
    bays = BearingBays(catlin_model_ro, (200 * M_PER_IN, 280 * M_PER_IN, 240 * M_PER_IN,
                                         330 * M_PER_IN), 0.4375 * M_PER_IN)

    def along(y, z):
        return bays.refusal("x", y * M_PER_IN, 200 * M_PER_IN, 230 * M_PER_IN, z * M_PER_IN)

    assert along(306, -6) is None
    assert along(302, -6) == "FS-M-NE bearing-block-0-009"  # its side into the joist face
    assert along(306, -1.75) is not None  # its crown over the top rail
    assert bays.refusal("y", 215 * M_PER_IN, 290 * M_PER_IN, 320 * M_PER_IN,
                        -6 * M_PER_IN) is not None  # riding the line through the block
