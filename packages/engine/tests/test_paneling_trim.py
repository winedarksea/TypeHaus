"""Finish-run continuity and opening clipping without loading a whole house."""
from dataclasses import replace

import pytest
from shapely.geometry import Polygon, box

from typehaus import BoardAndBatten, inch
from typehaus.resolve.model import ResolvedPaneling
from typehaus.resolve.paneling_trim import _frame, _joins, _layout, _rectangles

_IN = 0.0254


@pytest.fixture
def spec():
    return BoardAndBatten(material_ref="painted-poplar", thickness=inch(0.75),
                          batten_width=inch(2.5), rail_width=inch(3.5),
                          target_spacing=inch(16), base_height=inch(3.5))


def _band(start, end):
    ring = ((start, 0), (end, 0), (end, 0.25 * _IN), (start, 0.25 * _IN))
    return ResolvedPaneling(
        uid=str(start), tag="paneling", storey="main", room="bedroom", wall_tag=str(start),
        material_ref="mdf", area_m2=(end - start) * 72 * _IN,
        band_z0_m=0, band_z1_m=72 * _IN, run_m=end - start,
        replaces_wall_finish=False, outline=ring, z0_m=0, z1_m=72 * _IN,
        thickness_m=0.25 * _IN, pieces=((ring, 0, 72 * _IN),))


def test_wall_split_does_not_change_cut_boards_or_geometry(spec):
    whole = _band(0, 100 * _IN)
    split = [_band(0, 37 * _IN), _band(37 * _IN, 100 * _IN)]
    frame = _frame(whole)
    one = _layout([whole], spec, *frame)
    two = _layout(split, spec, *frame)
    assert one == two
    # Even a model split narrower than a stile cannot alter the physical cut list.
    tiny_split = [_band(0, _IN), _band(_IN, 100 * _IN)]
    assert _layout(tiny_split, spec, *frame) == one
    assert _joins(split[1], split[:1], *frame)
    assert not _joins(_band(101 * _IN, 130 * _IN), [whole], *frame)


def test_opening_clips_the_trim_and_never_adds_a_board_through_a_door(spec):
    band = _band(0, 100 * _IN)
    # The opening spans the middle full-height batten, stopping below the top rail.
    left = _band(0, 42 * _IN).outline
    right = _band(58 * _IN, 100 * _IN).outline
    band = replace(band, pieces=((left, 0, 72 * _IN), (right, 0, 72 * _IN)))
    boards = _layout([band], spec, *_frame(band))
    opening = box(42 * _IN, 0, 58 * _IN, 72 * _IN)
    for board in boards:
        xs = [x for x, _ in board.outline]
        face = box(min(xs), board.z0_m, max(xs), board.z1_m)
        assert face.intersection(opening).area < 1e-10
        assert Polygon(board.outline).area == pytest.approx(
            (max(xs) - min(xs)) * spec.thickness.meters)


def test_rectangular_cut_partition_handles_an_internal_opening_and_boundary_contacts():
    field = box(0, 0, 10, 10).difference(box(3, 3, 7, 7))
    rectangles = _rectangles(field)
    assert sum(box(*bounds).area for bounds in rectangles) == pytest.approx(field.area)
    assert _rectangles(box(0, 0, 1, 1).intersection(box(1, 0, 2, 1))) == []
