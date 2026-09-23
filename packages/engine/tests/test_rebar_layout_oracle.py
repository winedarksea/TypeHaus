"""``resolve/rebar`` against ``houses/catlin/notes/rebar_layout_basis.md`` §2–§4.

Three elements laid out bar for bar by hand before the layout code existed: the FT-SG-S mat,
the W-SG-S stem (verticals continuous from the footing, two-face horizontals and their corner
bars) and the PT-SG-COL cage. Counts are exact; lengths match the note to 0.01".

** THE COURT NARROWED TO 17'-0" ON 2026-09-22 ** and the note has not followed: §2/§3 are
worked for a 240" axis and FT-SG-S/W-SG-S are 216" now. The same arithmetic, re-run at 216",
is inlined in each docstring below. PT-SG-COL retired with the court's centre line, so §4 is
laid on a stand-in built from the note's own inputs.
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
    """§2 at 216" x 100" (the 4'-4" toe, 2026-09-22): bar region 94" x 210".
    bottom-x @ 9": ceil((210 - 0.625)/9) + 1 = 25 #5 at 94" (2,350" = 195.83' = 204.25 lb);
    top-x @ 12": ceil((210 - 0.625)/12) + 1 = 19 #5 at 94" (1,786" = 148.83' = 155.23 lb);
    y: ceil((94 - 0.5)/18) + 1 = 7 #4 at 210" (1,470" = 122.5' = 81.83 lb). No laps or
    hooks."""
    m = catlin_model_ro
    for role, count, length_in, lb in (("bottom-x", 25, 94.0, 204.25),
                                       ("top-x", 19, 94.0, 155.23),
                                       ("bottom-y", 7, 210.0, 81.83)):
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
    """§3 at 216": centres [0.625, 215.375], ceil(214.75/7) + 1 = 32 #5 continuous from the
    footing, 114.0" + a 8.436" foot (cut 122.436 x 32 = 3,917.95" = 340.54 lb), 2.6875"
    inside the retained face, 7.875" of the 7.115" ldh embedded."""
    bars = _role(catlin_model_ro, "W-SG-S", "vertical")
    assert len(bars) == 32
    for b in bars:
        assert b.placed_length_m / _IN == pytest.approx(114.0, abs=0.01)
        assert b.hook_length_m / _IN == pytest.approx(8.436, abs=0.001)
        assert b.lap_length_m == 0.0 and b.hook_kinds == ("std90",)
        assert b.embedment_m / _IN == pytest.approx(7.875, abs=0.001)
        assert b.development_m / _IN == pytest.approx(7.115, abs=0.001)
    assert _lb(bars) == pytest.approx(340.54, abs=0.01)
    wall = catlin_model_ro.wall("W-SG-S")
    t = (bars[0].path[1][1] - wall.axis[0][1]) / _IN
    assert t == pytest.approx(-2.6875, abs=0.001)
    assert not _role(catlin_model_ro, "W-SG-S", "dowels")


def test_w_sg_s_horizontals(catlin_model_ro) -> None:
    """§3 at 216": 16 straight one-piece rows — exterior s [0.875, 215.125] = 214.25",
    interior [5.75, 210.25] = 204.5" — and 16 SW corner bars of 6.0" placed + 60.0" lap.
    8 x 214.25 + 8 x 204.5 + 16 x 66 = 4,406.0" = 367.17' = 245.27 lb."""
    bars = _role(catlin_model_ro, "W-SG-S", "horizontal")
    assert len(bars) == 32
    assert all(b.pieces == 1 and not b.hook_kinds for b in bars)
    straight = sorted(round(b.placed_length_m / _IN, 3) for b in bars if len(b.path) == 2)
    assert straight == [204.5] * 8 + [214.25] * 8
    corners = [b for b in bars if len(b.path) == 3]
    assert len(corners) == 16
    for b in corners:
        assert b.placed_length_m / _IN == pytest.approx(6.0, abs=0.001)
        assert b.lap_length_m / _IN == pytest.approx(60.0, abs=0.001)
    assert sum(b.cut_length_m for b in bars) / _IN == pytest.approx(4406.0, abs=0.01)
    assert _lb(bars) == pytest.approx(245.27, abs=0.01)


def _retired_column_cage():
    """§4's inputs, laid by ``lay_column`` directly: PT-SG-COL retired 2026-09-22.

    12" round (a 24-gon, as a resolved round post is), 120.9375" tall, cover 2",
    ``(4) #5`` + ``#3 @ 10"``, 5,000 psi, galvanized A767, 40' stock, class B laps.
    """
    import math
    from types import SimpleNamespace

    from typehaus.model.rebar import BarSpec, ReinforcementSpec
    from typehaus.quantities import inch
    from typehaus.resolve.rebar.cages import lay_column
    from typehaus.resolve.rebar.stock import Sink

    spec = ReinforcementSpec(bars=(BarSpec(role="vertical", bar=5, count=4),
                                   BarSpec(role="ties", bar=3, spacing=inch(10.0))),
                             cover=inch(2.0), lap_class="B")
    r = 6.0 * _IN
    solid = SimpleNamespace(
        outline=[(r * math.cos(math.pi * k / 12), r * math.sin(math.pi * k / 12))
                 for k in range(24)],
        z0_m=0.0, z1_m=120.9375 * _IN)
    sink = Sink("PT-SG-COL", "hdg-a767", 5000.0, "B", 480.0 * _IN)
    lay_column(sink, spec, solid, 2.0 * _IN)
    return sink.bars


def test_pt_sg_col_cage() -> None:
    """§4: 4 #5 at 116.9375"; 13 circular #3 ties, 23.955" placed + 15.185" A767 hooks."""
    bars = _retired_column_cage()
    verts = [b for b in bars if b.role == "vertical"]
    ties = [b for b in bars if b.role == "ties"]
    assert len(verts) == 4 and len(ties) == 13
    assert all(b.placed_length_m / _IN == pytest.approx(116.9375, abs=0.01) for b in verts)
    assert _lb(verts) == pytest.approx(40.66, abs=0.01)
    for tie in ties:
        assert tie.closed
        assert tie.placed_length_m / _IN == pytest.approx(23.955, abs=0.001)
        assert tie.hook_length_m / _IN == pytest.approx(15.185, abs=0.001)
    assert _lb(ties) == pytest.approx(15.94, abs=0.01)
    assert not [b for b in bars if b.role == "dowels"]
