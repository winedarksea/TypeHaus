"""``resolve/rebar`` against ``houses/catlin/notes/rebar_layout_basis.md`` §2–§4.

Three elements laid out bar for bar by hand before the layout code existed: the FT-SG-S mat,
the W-SG-S stem (verticals, two-face horizontals with laps and corner hooks, footing
dowels) and the PT-SG-COL cage. Counts are exact; lengths match the note to 0.01".
"""

from __future__ import annotations

import pytest

from typehaus.model.rebar import BARS

_IN = 0.0254


def _set(model, tag):
    found = [s for s in model.rebar if s.host_tag == tag]
    assert len(found) == 1, tag
    return found[0]


def _role(model, tag, role):
    return [b for b in _set(model, tag).bars if b.role == role]


def _lb(bars) -> float:
    return sum(b.cut_length_m / 0.3048 * BARS[b.bar].weight_plf for b in bars)


def test_ft_sg_s_mat(catlin_model_ro) -> None:
    """§2: 21 + 21 bars of #5 at 78", 6 of #4 at 234", no laps or hooks."""
    m = catlin_model_ro
    for role, count, length_in, lb in (("bottom-x", 21, 78.0, 142.37),
                                       ("top-x", 21, 78.0, 142.37),
                                       ("bottom-y", 6, 234.0, 78.16)):
        bars = _role(m, "FT-SG-S", role)
        assert len(bars) == count, role
        for b in bars:
            assert b.placed_length_m / _IN == pytest.approx(length_in, abs=0.01)
            assert b.lap_length_m == 0.0 and b.hook_length_m == 0.0
        assert _lb(bars) == pytest.approx(lb, abs=0.01)
    soffit = next(s for s in m.solids if s.tag == "FT-SG-S").z0_m
    heights = {r: (_role(m, "FT-SG-S", r)[0].path[0][2] - soffit) / _IN
               for r in ("bottom-x", "bottom-y", "top-x")}
    assert heights == pytest.approx({"bottom-x": 3.3125, "bottom-y": 3.875, "top-x": 8.6875},
                                    abs=0.001)


def test_w_sg_s_verticals(catlin_model_ro) -> None:
    """§3: 25 #6 at 103.4375", on the retained face 2.625" inside it."""
    bars = _role(catlin_model_ro, "W-SG-S", "vertical")
    assert len(bars) == 25
    assert all(b.placed_length_m / _IN == pytest.approx(103.4375, abs=0.01) for b in bars)
    assert _lb(bars) == pytest.approx(323.67, abs=0.01)
    wall = catlin_model_ro.wall("W-SG-S")
    t = (bars[0].path[0][1] - wall.axis[0][1]) / _IN
    assert t == pytest.approx(-2.625, abs=0.001)


def test_w_sg_s_horizontals(catlin_model_ro) -> None:
    """§3: 16 runs of 2 equal-cut pieces, laps and hooks exactly as tabulated."""
    bars = _role(catlin_model_ro, "W-SG-S", "horizontal")
    assert len(bars) == 32
    assert all(b.pieces == 2 and len(b.hook_kinds) == 1 for b in bars)
    firsts = sorted((round(b.placed_length_m / _IN, 3), round(b.lap_length_m / _IN, 3),
                     round(b.cut_length_m / _IN, 3)) for b in bars if b.piece == 1)
    assert firsts == sorted([(107.969, 22.062, 136.78)] + [(104.66, 28.68, 140.089)] * 7
                            + [(103.219, 22.062, 132.03)] + [(99.91, 28.68, 135.339)] * 7)
    seconds = sorted(round(b.placed_length_m / _IN, 3) for b in bars if b.piece == 2)
    assert seconds == sorted([130.031] + [133.34] * 7 + [125.281] + [128.59] * 7)
    assert sum(b.cut_length_m for b in bars) / _IN == pytest.approx(4393.612, abs=0.01)
    assert _lb(bars) == pytest.approx(244.58, abs=0.01)


def test_w_sg_s_dowels(catlin_model_ro) -> None:
    """§3: 25 #6 L-dowels, 8.625" embedded, 33.093" lap, 10.123" foot."""
    bars = _role(catlin_model_ro, "W-SG-S", "dowels")
    assert len(bars) == 25
    for b in bars:
        assert b.placed_length_m / _IN == pytest.approx(8.625, abs=0.001)
        assert b.lap_length_m / _IN == pytest.approx(33.093, abs=0.001)
        assert b.hook_length_m / _IN == pytest.approx(10.123, abs=0.001)
    assert _lb(bars) == pytest.approx(162.22, abs=0.01)


def test_pt_sg_col_cage(catlin_model_ro) -> None:
    """§4: 4 #5 at 116.9375"; 13 circular #3 ties, 23.955" placed + 14.168" hooks."""
    verts = _role(catlin_model_ro, "PT-SG-COL", "vertical")
    ties = _role(catlin_model_ro, "PT-SG-COL", "ties")
    assert len(verts) == 4 and len(ties) == 13
    assert all(b.placed_length_m / _IN == pytest.approx(116.9375, abs=0.01) for b in verts)
    assert _lb(verts) == pytest.approx(40.66, abs=0.01)
    for tie in ties:
        assert tie.closed
        assert tie.placed_length_m / _IN == pytest.approx(23.955, abs=0.001)
        assert tie.hook_length_m / _IN == pytest.approx(14.168, abs=0.001)
    assert _lb(ties) == pytest.approx(15.53, abs=0.01)
    assert not _role(catlin_model_ro, "PT-SG-COL", "dowels")
