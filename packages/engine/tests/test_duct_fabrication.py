"""A duct run is drawn as straight stretches and elbows (``resolve/duct_fabrication``)."""

from __future__ import annotations

import math
from types import SimpleNamespace

import pytest

import typehaus.resolve  # noqa: F401 - import order: resolve before the library catalog
from typehaus.model.ducts import DuctElbowRow, RectElbowRow
from typehaus.quantities import M_PER_IN, inch
from typehaus.resolve.duct_fabrication import fabricate_run
from typehaus.resolve.mep import _emit_run_solids
from typehaus.resolve.mep_fittings import FAMILY_DUCT, polyline_fittings
from typehaus.resolve.sweep import leg_frame, rect_profile, round_profile, sweep_legs

STANDARD = SimpleNamespace(
    elbows=[DuctElbowRow(diameter=inch(6), product_ref="EL-6", kind="stamped",
                         angles=(90.0,), radius_diameters=1.0)],
    rect_elbow=RectElbowRow(radius_ratio=1.0))


def _pieces(points, *, diameter=None, width=0.0, depth=0.0, standard=STANDARD):
    model = SimpleNamespace(solids=[])
    profile = (round_profile(diameter / 2.0, 12) if diameter
               else rect_profile(width, depth))
    _emit_run_solids(model, "RUNUID", "DU-T", "L1", [p[:2] for p in points],
                     [p[2] for p in points], profile, "duct_supply")
    duct = SimpleNamespace(tag="DU-T", uid="RUNUID", diameter_m=diameter,
                           path=[p[:2] for p in points], z_m=[p[2] for p in points])
    records = polyline_fittings(
        "DU-T", FAMILY_DUCT, "supply", points, diameter or max(width, depth),
        rectangular=diameter is None, duct_standard=standard, order_size="x",
        section=None if diameter else (width, depth))
    return fabricate_run(model, duct, model.solids[0], records, standard, (), set())


def _ring_gap(a, b) -> float:
    return max(min(math.dist(p, q) for q in b) for p in a)


def _assert_continuous(pieces) -> None:
    """Every piece's legs mitre closed, and each piece's end ring is the next one's start."""
    for piece in pieces:
        legs = sweep_legs(piece.sweep)
        for (_, end), (start, _) in zip(legs, legs[1:], strict=False):
            assert _ring_gap(end, start) < 1e-9
    ordered = sorted(pieces, key=lambda p: (p.sweep.path[0][0], p.sweep.path[0][2]))
    for a, b in zip(ordered, ordered[1:], strict=False):
        assert math.dist(a.sweep.path[-1], b.sweep.path[0]) < 1e-9
        assert _ring_gap(sweep_legs(a.sweep)[-1][1], sweep_legs(b.sweep)[0][0]) < 1e-9


def test_round_plan_elbow_is_an_arc_between_two_stretches():
    d = inch(6).meters
    pieces = _pieces([(0.0, 0.0, 3.0), (2.0, 0.0, 3.0), (2.0, 2.0, 3.0)], diameter=d)
    assert [p.uid for p in pieces] == ["RUNUID-run", "RUNUID-elbow-01", "RUNUID-run-2"]
    assert {p.tag for p in pieces} == {"DU-T-RUN"}
    assert {p.host_ref for p in pieces} == {"DU-T"}
    assert {p.group for p in pieces} == {"DU-T"}
    assert not any(p.derived for p in pieces)
    elbow = pieces[1].sweep.path
    r = d  # radius_diameters 1.0 x 6", set back R tan(45) = R
    assert elbow[0] == pytest.approx((2.0 - r, 0.0, 3.0))
    assert elbow[-1] == pytest.approx((2.0, r, 3.0))
    assert pieces[0].sweep.path[-1] == pytest.approx(elbow[0])
    assert pieces[2].sweep.path[0] == pytest.approx(elbow[-1])
    assert len(elbow) == 8  # 90 / 15 = six chords between the two tangent stubs
    centre = (2.0 - r, r)
    for corner in elbow[1:-1]:
        assert math.dist(corner[:2], centre) == pytest.approx(r / math.cos(math.radians(7.5)))
    _assert_continuous(pieces)


def test_rect_riser_elbow_carries_its_section_unrolled():
    w, h = 12 * M_PER_IN, 8 * M_PER_IN
    pieces = _pieces([(0.0, 0.0, 3.0), (2.0, 0.0, 3.0), (2.0, 0.0, 5.0)], width=w, depth=h)
    assert [p.uid for p in pieces] == ["RUNUID-run", "RUNUID-elbow-01", "RUNUID-run-2"]
    elbow, riser = pieces[1].sweep, pieces[2].sweep
    # A turn into a rise is in the depth's plane: R = r/W 1.0 x 8".
    assert elbow.path[0] == pytest.approx((2.0 - h, 0.0, 3.0))
    assert elbow.path[-1] == pytest.approx((2.0, 0.0, 3.0 + h))
    assert pieces[0].sweep.vertical_up is None  # level: nothing to carry
    assert riser.vertical_up == pytest.approx((-1.0, 0.0, 0.0))
    assert elbow.vertical_up == pytest.approx((-1.0, 0.0, 0.0))
    right, _ = leg_frame((0.0, 0.0, 1.0), riser.vertical_up)
    assert right == pytest.approx((0.0, 1.0, 0.0))  # the 12" side stays across the run
    _assert_continuous(pieces)


def test_a_turn_with_no_part_keeps_its_butt():
    w, h = 12 * M_PER_IN, 8 * M_PER_IN
    no_rect = SimpleNamespace(elbows=[], rect_elbow=None)
    pieces = _pieces([(0.0, 0.0, 3.0), (2.0, 0.0, 3.0), (2.0, 2.0, 3.0)], width=w, depth=h,
                     standard=no_rect)
    assert [p.uid for p in pieces] == ["RUNUID-run"]
    assert len(pieces[0].sweep.path) == 3 and pieces[0].host_ref == "DU-T"
