"""annotate.py — shared label layout: wrap, stacked column, deterministic dodge.

Everything here is in **points** now, because lettering is a printed size. ``place_column``
and ``dodge`` still *place* in model inches — that is where the drawing is — but what they
reserve room for is a label of a fixed printed height, converted through the sheet's scale.
``scale=None`` is the frameless convention (``LEGACY_IN_PER_PT``), which is what these tests
use: it reproduces the pre-paper-space numbers exactly, so the geometry assertions below are
the same ones they always were.
"""

from __future__ import annotations

from typehaus.emit.draw.annotate import (
    LEADER_WRAP_COLUMNS,
    LEGACY_IN_PER_PT,
    LabelSpec,
    dodge,
    label_box,
    leader_box,
    place_column,
    text_extent,
    wrap_label,
)

#: The ladder's authored 2.6" rung and 1.6" lettering, said in the unit they now live in.
RUNG_PT = 2.6 / LEGACY_IN_PER_PT
LADDER_PT = 1.6 / LEGACY_IN_PER_PT


def _overlaps(a, b) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def test_wrap_label_wraps_long_leader_text_at_40_columns():
    text = "air continuity — sheathing-ext → sheathing-ext"
    wrapped = wrap_label(text)
    lines = wrapped.split("\n")
    assert len(lines) > 1, "45+ char callouts must wrap"
    assert all(len(line) <= LEADER_WRAP_COLUMNS for line in lines)
    assert wrapped.replace("\n", " ") == text, "wrapping only moves whitespace"


def test_wrap_label_leaves_short_text_alone():
    assert wrap_label("stud 5.5\"") == 'stud 5.5"'


def test_text_extent_uses_longest_line_and_line_count():
    w1, h1 = text_extent("abcd", 2.0)
    w2, h2 = text_extent("abcd\nab", 2.0)
    assert w1 == w2, "width comes from the longest line"
    assert h2 == 2 * h1, "height grows per line"


def test_text_extent_is_paper_and_label_box_is_the_model():
    """The seam. An extent is what a label *prints* as; a box is where it lands.

    Reservation equals reality only because the second is the first converted through one
    scale, and that is the only place the two units meet.
    """
    from typehaus.emit.draw.annotate import model_in_per_pt

    width_pt, _height_pt = text_extent("abcd", 7.0)
    u0, _z0, u1, _z1 = label_box((0.0, 0.0), "abcd", 7.0, "left")
    assert u1 - u0 == width_pt * LEGACY_IN_PER_PT
    # And with a real sheet, the same 7 pt label is about half as wide in the model.
    framed = label_box((0.0, 0.0), "abcd", 7.0, "left", scale=1.5)
    assert framed[2] - framed[0] == width_pt * model_in_per_pt(1.5)
    assert framed[2] - framed[0] < (u1 - u0) * 0.6


def test_place_column_is_a_uniform_ladder_for_single_line_labels():
    entries = [LabelSpec(text=f"layer-{i}", target=(10.0 + i, 0.0)) for i in range(4)]
    placed = place_column(entries, x=-5.0, z_top=100.0, step_pt=RUNG_PT, height_pt=LADDER_PT)
    zs = [p.at[1] for p in placed]
    steps = [zs[i] - zs[i + 1] for i in range(len(zs) - 1)]
    assert all(abs(s - 2.6) < 1e-9 for s in steps), "uniform rung spacing"
    assert all(not _overlaps(a.box, b.box)
               for i, a in enumerate(placed) for b in placed[i + 1:])


def test_place_column_grows_rows_to_fit_wrapped_text():
    tall = LabelSpec(text="one\ntwo\nthree\nfour")
    entries = [tall, LabelSpec(text="next")]
    placed = place_column(entries, x=0.0, z_top=50.0, step_pt=RUNG_PT, height_pt=LADDER_PT)
    assert not _overlaps(placed[0].box, placed[1].box), \
        "a multi-line row must push the next row past its own extent"


def test_dodge_pushes_overlapping_boxes_down_and_is_deterministic():
    a = place_column([LabelSpec(text="aaaa")], x=0.0, z_top=10.0, step_pt=RUNG_PT)[0]
    b = place_column([LabelSpec(text="bbbb")], x=1.0, z_top=10.5, step_pt=RUNG_PT)[0]
    assert _overlaps(a.box, b.box)
    out1 = dodge([a, b])
    out2 = dodge([a, b])
    assert out1 == out2, "dodge is deterministic"
    assert not _overlaps(out1[0].box, out1[1].box)
    # order preserved; only anchors/boxes move, and only downward
    assert out1[0].spec.text == "aaaa" and out1[1].spec.text == "bbbb"
    assert min(out1[0].at[1], out1[1].at[1]) < min(a.at[1], b.at[1])


def test_dodge_ignores_horizontally_separated_boxes():
    a = place_column([LabelSpec(text="left")], x=0.0, z_top=10.0, step_pt=RUNG_PT)[0]
    b = place_column([LabelSpec(text="right")], x=100.0, z_top=10.0, step_pt=RUNG_PT)[0]
    out = dodge([a, b])
    assert out == [a, b], "no overlap in u → nothing moves"


def test_dodge_respects_fixed_obstacles():
    lab = place_column([LabelSpec(text="mmmm")], x=0.0, z_top=10.0, step_pt=RUNG_PT)[0]
    (moved,) = dodge([lab], fixed=(lab.box,))
    assert not _overlaps(moved.box, lab.box), "pushed below the fixed obstacle"
    assert moved.at[1] < lab.at[1]


def test_leader_box_matches_label_box_alignment():
    from typehaus.emit.draw.scene import Leader, NamedPoint

    # text left of its target grows leftward (pdf_writer._leader_align convention)
    node = Leader(anchor=NamedPoint(xy=(50.0, 5.0)), at=(10.0, 5.0), to=(50.0, 5.0),
                  text="abc")
    assert leader_box(node) == label_box((10.0, 5.0), "abc", LADDER_PT, "right")
    # text right of its target grows rightward
    node = Leader(anchor=NamedPoint(xy=(0.0, 5.0)), at=(10.0, 5.0), to=(0.0, 5.0),
                  text="abc")
    assert leader_box(node) == label_box((10.0, 5.0), "abc", LADDER_PT, "left")
