"""Unit fixtures for ``resolve/rebar``: the cases catlin does not exercise.

An opening splitting bars, a raked top, a slab void, a circular tie's billed perimeter, and a
run split across stock. Each builds the smallest host the layout will accept.
"""

from __future__ import annotations

import math
from types import SimpleNamespace

import pytest

from typehaus import BarSpec, ReinforcementSpec, inch
from typehaus.resolve.model import ResolvedLayer, ResolvedSolid, ResolvedWall
from typehaus.resolve.rebar import detailing as det
from typehaus.resolve.rebar.cages import lay_column
from typehaus.resolve.rebar.mats import lay_mat
from typehaus.resolve.rebar.stock import Sink
from typehaus.resolve.rebar.walls import lay_wall

_IN = 0.0254


def _sink(stock_in: float = 240.0) -> Sink:
    return Sink("H", "", 4000.0, "B", stock_in * _IN)


def _wall(length_in=120.0, top_in=96.0, top0=None, top1=None) -> ResolvedWall:
    L, t = length_in * _IN, 4 * _IN
    ring = ((0.0, -t), (L, -t), (L, t), (0.0, t))
    concrete = ResolvedLayer("concrete", "concrete", "structure", 8 * _IN, ring)
    return ResolvedWall(uid="u", tag="W", storey="s", assembly="A", axis=((0.0, 0.0), (L, 0.0)),
                        layers=(concrete,), z0_m=0.0, z1_m=top_in * _IN, is_foundation=True,
                        top_z0_m=top0, top_z1_m=top1)


def _spec(*bars) -> ReinforcementSpec:
    return ReinforcementSpec(bars=bars, cover=inch(2))


def test_an_opening_splits_the_verticals_that_cross_it() -> None:
    sink = _sink()
    wall = _wall()
    opening = SimpleNamespace(host_wall="W", width_m=36 * _IN, height_m=36 * _IN,
                              sill_m=30 * _IN, center_along_m=60 * _IN)
    lay_wall(sink, _spec(BarSpec(role="vertical", bar=4, spacing=inch(12))), wall, 2 * _IN,
             (opening,), (None, None))
    xs = sorted({round(b.path[0][0] / _IN, 3) for b in sink.bars})
    split = [x for x in xs if 40 <= x <= 80]  # within the opening ± cover
    assert split
    for x in split:
        pieces = [b for b in sink.bars if round(b.path[0][0] / _IN, 3) == x]
        assert len(pieces) == 2
        below, above = sorted(pieces, key=lambda b: b.path[0][2])
        assert below.path[1][2] / _IN == pytest.approx(28.0)
        assert above.path[0][2] / _IN == pytest.approx(68.0)


def test_a_raked_top_shortens_verticals_and_horizontals() -> None:
    sink = _sink()
    wall = _wall(top_in=96.0, top0=48 * _IN, top1=96 * _IN)
    lay_wall(sink, _spec(BarSpec(role="vertical", bar=4, spacing=inch(12)),
                         BarSpec(role="horizontal", bar=4, spacing=inch(12))),
             wall, 2 * _IN, (), (None, None))
    verts = sorted((b for b in sink.bars if b.role == "vertical"), key=lambda b: b.path[0][0])
    assert verts[0].path[1][2] < verts[-1].path[1][2]
    for b in verts:
        x = b.path[0][0] / _IN
        assert b.path[1][2] / _IN == pytest.approx(48 + 48 * x / 120 - 2, abs=1e-6)
    top_row = max((b for b in sink.bars if b.role == "horizontal"), key=lambda b: b.path[0][2])
    z = top_row.path[0][2] / _IN
    start = min(top_row.path[0][0], top_row.path[1][0]) / _IN
    assert 48 + 48 * start / 120 == pytest.approx(z + 2, abs=1e-6)


def test_a_slab_void_splits_the_mat() -> None:
    sink = _sink()
    outline = ((0.0, 0.0), (120 * _IN, 0.0), (120 * _IN, 120 * _IN), (0.0, 120 * _IN))
    void = ((48 * _IN, 48 * _IN), (72 * _IN, 48 * _IN), (72 * _IN, 72 * _IN), (48 * _IN, 72 * _IN))
    slab = ResolvedSolid(uid="u", tag="S", storey="s", category="slab", outline=outline,
                         z0_m=0.0, z1_m=6 * _IN, voids=(void,))
    lay_mat(sink, _spec(BarSpec(role="bottom-x", bar=4, spacing=inch(12))), slab, 2 * _IN)
    through_void = [b for b in sink.bars if 46 < b.path[0][1] / _IN < 74]
    assert through_void and len(through_void) % 2 == 0
    for b in through_void:
        xs = sorted((b.path[0][0] / _IN, b.path[1][0] / _IN))
        assert xs[1] <= 46.0 + 1e-6 or xs[0] >= 74.0 - 1e-6


def test_a_circular_tie_bills_two_pi_r_plus_hooks_and_overlap() -> None:
    sink = _sink()
    r = 6 * _IN
    ring = tuple((r * math.cos(2 * math.pi * k / 16), r * math.sin(2 * math.pi * k / 16))
                 for k in range(16))
    column = ResolvedSolid(uid="u", tag="C", storey="s", category="column", outline=ring,
                           z0_m=0.0, z1_m=40 * _IN)
    lay_column(sink, _spec(BarSpec(role="ties", bar=3, spacing=inch(10))), column, 2 * _IN)
    ties = [b for b in sink.bars if b.role == "ties"]
    assert len(ties) == 4  # 5" .. 35", ceil(30/10) + 1
    tie = ties[0]
    assert tie.closed
    assert tie.placed_length_m / _IN == pytest.approx(2 * math.pi * (6 - 2 - 0.1875))
    assert tie.hook_length_m / _IN == pytest.approx(
        2 * det.hook_allowance_in(3, "tie135") + det.CIRCULAR_TIE_OVERLAP_IN)


def test_a_run_over_stock_is_lapped_into_equal_pieces() -> None:
    sink = _sink(stock_in=240.0)
    entry = BarSpec(role="bottom-x", bar=5, spacing=inch(12))
    sink.straight(entry, (0.0, 0.0, 0.0), (500 * _IN, 0.0, 0.0))
    lap = det.tension_lap_in(5, 4000, "B")
    assert len(sink.bars) == math.ceil((500 - lap) / (240 - lap))
    cuts = [b.cut_length_m / _IN for b in sink.bars]
    assert max(cuts) <= 240.0 + 1e-9
    assert cuts == pytest.approx([cuts[0]] * len(cuts))
    assert sum(b.placed_length_m for b in sink.bars) / _IN == pytest.approx(500.0)
    assert sum(cuts) == pytest.approx(500.0 + (len(cuts) - 1) * lap)
    assert sink.bars[-1].lap_length_m == 0.0
