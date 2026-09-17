"""Unit fixtures for ``resolve/rebar``: the cases catlin does not exercise.

An opening splitting bars, a raked top, a slab void, a circular tie's billed perimeter, a run
split across stock (and its staggered neighbour), corner bars at an L, a mat stopping at an
earlier pour and a vertical hooked into the pour below. Each builds the smallest host the
layout will accept.
"""

from __future__ import annotations

import math
from types import SimpleNamespace

import pytest

from typehaus import BarSpec, ReinforcementSpec, inch
from typehaus.resolve.model import ResolvedLayer, ResolvedSolid, ResolvedWall
from typehaus.resolve.rebar import detailing as det
from typehaus.resolve.rebar.cages import lay_column
from typehaus.resolve.rebar.junctions import lay_junction_bars
from typehaus.resolve.rebar.mats import lay_mat
from typehaus.resolve.rebar.stock import Sink
from typehaus.resolve.rebar.walls import WallBase, lay_wall

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
             (opening,))
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
             wall, 2 * _IN, ())
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
        2 * det.hook_allowance_in(3, "tie135") + det.CIRCULAR_TIE_OVERLAP_IN)  # black bar


def test_a_run_over_stock_is_lapped_into_equal_pieces() -> None:
    sink = _sink(stock_in=240.0)
    entry = BarSpec(role="bottom-x", bar=5, spacing=inch(12))
    sink.straight(entry, (0.0, 0.0, 0.0), (500 * _IN, 0.0, 0.0))  # run 1: not staggered
    lap = det.tension_lap_in(5, 4000, "B")
    assert len(sink.bars) == math.ceil((500 - lap) / (240 - lap))
    cuts = [b.cut_length_m / _IN for b in sink.bars]
    assert max(cuts) <= 240.0 + 1e-9
    assert cuts == pytest.approx([cuts[0]] * len(cuts))
    assert sum(b.placed_length_m for b in sink.bars) / _IN == pytest.approx(500.0)
    assert sum(cuts) == pytest.approx(500.0 + (len(cuts) - 1) * lap)
    assert sink.bars[-1].lap_length_m == 0.0


def test_every_other_run_staggers_its_splices_by_half_a_pitch() -> None:
    sink = _sink(stock_in=240.0)
    entry = BarSpec(role="bottom-x", bar=5, spacing=inch(12))
    sink.straight(entry, (0.0, 0.0, 0.0), (500 * _IN, 0.0, 0.0))
    first = len(sink.bars)
    sink.straight(entry, (0.0, 1.0, 0.0), (500 * _IN, 1.0, 0.0))
    second = sink.bars[first:]
    assert len(second) == first + 1
    lap = det.tension_lap_in(5, 4000, "B")
    cuts = [b.cut_length_m / _IN for b in second]
    assert max(cuts) <= 240.0 + 1e-9
    assert sum(b.placed_length_m for b in second) / _IN == pytest.approx(500.0)
    starts_a = sorted(round(min(b.path[0][0], b.path[-1][0]) / _IN, 3) for b in sink.bars[:first])
    starts_b = sorted(round(min(b.path[0][0], b.path[-1][0]) / _IN, 3) for b in second)
    pitch = (500 - lap) / first
    assert starts_b[1] == pytest.approx(starts_a[1] - pitch / 2, abs=0.01)


def _l_walls():
    """Two 8" walls meeting at an L at the origin: A runs +x, B runs +y."""
    t, L = 4 * _IN, 120 * _IN
    a_ring = ((-t, -t), (L, -t), (L, t), (t, t))
    b_ring = ((-t, -t), (t, t), (t, L), (-t, L))
    walls = []
    for tag, axis, ring in (("A", ((0.0, 0.0), (L, 0.0)), a_ring),
                            ("B", ((0.0, 0.0), (0.0, L)), b_ring)):
        layer = ResolvedLayer("concrete", "concrete", "structure", 8 * _IN, ring)
        walls.append(ResolvedWall(uid=tag, tag=tag, storey="s", assembly="X", axis=axis,
                                  layers=(layer,), z0_m=0.0, z1_m=48 * _IN,
                                  is_foundation=True))
    return walls


def test_an_l_corner_gets_one_lapped_corner_bar_per_row_per_face() -> None:
    walls = _l_walls()
    spec = _spec(BarSpec(role="horizontal", bar=4, spacing=inch(16), layers=2))
    sinks, steel = {}, {}
    for w in walls:
        sinks[w.tag] = Sink(w.tag, "", 4000.0, "B", 480 * _IN, wall=True)
        steel[w.tag] = lay_wall(sinks[w.tag], spec, w, 2 * _IN, ())
    inc = [SimpleNamespace(wall_tag="A", direction=(1.0, 0.0), z0_m=0.0, z1_m=48 * _IN),
           SimpleNamespace(wall_tag="B", direction=(0.0, 1.0), z0_m=0.0, z1_m=48 * _IN)]
    junction = SimpleNamespace(node_tag="N", point=(0.0, 0.0), incidents=inc, through_walls=())
    rows = len({round(b.path[0][2], 6) for b in sinks["A"].bars})
    before = len(sinks["A"].bars)
    lay_junction_bars([junction], steel, sinks)
    corners = sinks["A"].bars[before:]
    assert len(corners) == 2 * rows  # owned by A, the first tag
    assert all(len(b.path) == 2 for b in sinks["B"].bars)
    for bar in corners:
        assert len(bar.path) == 3 and bar.hook_length_m == 0.0
        # One wall lap each leg: IRC's 30", or class B top-cast (32.07") above 12".
        top_cast = bar.path[1][2] > 12 * _IN
        assert bar.lap_length_m == pytest.approx(2 * sinks["A"].lap_m(4, top_cast=top_cast))
        (x0, y0, _), (cx, cy, _), (x1, y1, _) = bar.path
        assert abs(cy - y0) < 1e-9 and abs(cx - x1) < 1e-9  # one leg along A, one along B
        assert (x0 - cx) / _IN > 30.0 and (y1 - cy) / _IN > 30.0
    assert all(not b.hook_kinds for b in sinks["A"].bars + sinks["B"].bars)


def test_a_later_mat_stops_at_an_earlier_pours_concrete() -> None:
    sink = _sink()
    outline = ((0.0, 0.0), (120 * _IN, 0.0), (120 * _IN, 48 * _IN), (0.0, 48 * _IN))
    earlier = ((96 * _IN, 0.0), (144 * _IN, 0.0), (144 * _IN, 48 * _IN), (96 * _IN, 48 * _IN))
    pad = ResolvedSolid(uid="u", tag="P", storey="s", category="pad", outline=outline,
                        z0_m=0.0, z1_m=12 * _IN)
    lay_mat(sink, _spec(BarSpec(role="bottom-x", bar=4, spacing=inch(12))), pad, 2 * _IN,
            earlier=(earlier,))
    assert sink.bars
    assert max(max(p[0] for p in b.path) for b in sink.bars) / _IN == pytest.approx(96.0)


def test_a_hooked_vertical_runs_from_the_pour_below_and_records_its_anchorage() -> None:
    sink = _sink()
    base = WallBase(top=0.0, rest=-8 * _IN)
    entry = BarSpec(role="vertical", bar=5, spacing=inch(12), face="exterior", hooks=("start",))
    lay_wall(sink, _spec(entry), _wall(), 2 * _IN, (), base)
    for bar in sink.bars:
        assert bar.hook_kinds == ("std90",) and len(bar.path) == 3
        assert bar.path[1][2] / _IN == pytest.approx(-8 + 0.3125)
        assert bar.embedment_m / _IN == pytest.approx(8.0)
        assert bar.development_m / _IN == pytest.approx(
            det.hooked_development_in(5, 4000, confined_spacing=True, side_cover_ok=True))
        assert abs(bar.path[0][2] - bar.path[1][2]) < 1e-9  # the foot is level
