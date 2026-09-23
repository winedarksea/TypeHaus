"""Plan dimension strings at a constant paper spacing, with no text over text.

The ledger A-101/A-102 printed at 3/32" while their tiers were spaced in model inches for
3/16", and the interior chain's strings printed through each other and onto the wall hatch.
These pin the NCS numbers the tiers are now laid out to, the rule that a crowded chain
never reuses a stagger row, and that a sheet reserves room for its tiers when it picks a
scale.
"""

from __future__ import annotations

import pytest

from typehaus.emit.draw.annotate import DODGE_GAP_PT, text_extent
from typehaus.emit.draw.dimension_rows import (
    STAGGER_ROWS,
    TIER_FIRST_IN,
    TIER_GAP_IN,
    dimension_band_in,
    dimension_offsets,
    row_pitch_in,
    tier_offsets,
)
from typehaus.emit.draw.floorplan import build_floorplan
from typehaus.emit.draw.floorplan_sheet import framed_floorplan
from typehaus.emit.draw.paper import ARCH_D
from typehaus.emit.draw.pdf_writer import _feet_inches
from typehaus.emit.draw.scene import ArchDimension
from typehaus.emit.draw.typography import model_in_per_pt

SCALES = (0.09375, 0.1875, 0.25)


def _intervals(spans, labels, results, scale, height_pt):
    """(row offset, lo, hi) of each label along its chain, model inches."""
    per_pt = model_in_per_pt(scale)
    out, along = [], 0.0
    for span, label, (offset, shift) in zip(spans, labels, results, strict=True):
        centre = along + span / 2.0 + shift
        half = (text_extent(label, height_pt)[0] * per_pt + DODGE_GAP_PT * per_pt) / 2.0
        out.append((offset, centre - half, centre + half))
        along += span
    return out


@pytest.mark.parametrize("scale", SCALES)
def test_tiers_sit_at_the_ncs_paper_distances(scale):
    facade, interior, overall = (value * scale / 12.0 for value in tier_offsets(scale))
    stack = (STAGGER_ROWS - 1) * row_pitch_in()
    assert facade == pytest.approx(TIER_FIRST_IN) and TIER_FIRST_IN >= 9 / 16
    assert interior - (facade + stack) == pytest.approx(TIER_GAP_IN) and TIER_GAP_IN >= 3 / 8
    assert overall - (interior + stack) == pytest.approx(TIER_GAP_IN)


@pytest.mark.parametrize("scale", SCALES)
def test_a_crowded_chain_never_reuses_a_row_or_prints_text_over_text(scale):
    spans = [6.0] * 12 + [48.0, 3.0, 5.0, 120.0]
    labels = [_feet_inches(span) for span in spans]
    results = dimension_offsets(spans, labels, -40.0, scale)
    pitch = row_pitch_in() * 12.0 / scale
    rows = {round((abs(offset) - 40.0) / pitch) for offset, _shift in results}
    assert rows <= set(range(STAGGER_ROWS)), rows
    assert any(shift for _offset, shift in results), "twelve 6\" segments must overflow"
    boxes = _intervals(spans, labels, results, scale, 9.5)
    for index, (row, lo, hi) in enumerate(boxes):
        for other_row, other_lo, other_hi in boxes[index + 1:]:
            if other_row == row:
                assert hi <= other_lo + 1e-9 or other_hi <= lo + 1e-9, (row, lo, hi)


def _label_boxes(scene, scale):
    """Estimated printed box of every dimension string, model inches, by orientation."""
    per_pt = model_in_per_pt(scale)
    out = {"h": [], "v": []}
    for node in scene.nodes:
        if not isinstance(node, ArchDimension):
            continue
        (x0, y0), (x1, y1) = node.p0, node.p1
        width_pt, height_pt = text_extent(node.text or _feet_inches(abs(x1 - x0) + abs(y1 - y0)),
                                          node.height_pt)
        width, height = width_pt * per_pt, height_pt * per_pt
        if abs(x1 - x0) >= abs(y1 - y0):
            cx, y = (x0 + x1) / 2 + node.text_along, y0 + node.offset
            out["h"].append((cx - width / 2, y, cx + width / 2, y + height))
        else:
            x, cy = x0 + node.offset, (y0 + y1) / 2 + node.text_along
            out["v"].append((x - height, cy - width / 2, x, cy + width / 2))
    return out


@pytest.mark.parametrize("scale", (0.09375, 0.25))
def test_no_two_dimension_strings_on_the_main_plan_overlap(catlin_model_ro, scale):
    from typehaus.emit.draw.datum import model_at_level

    scene = build_floorplan(model_at_level(catlin_model_ro, "main"), "main",
                            dimension_scale=scale)
    tolerance = 1e-6
    for boxes in _label_boxes(scene, scale).values():
        for index, (a0, b0, a1, b1) in enumerate(boxes):
            for c0, d0, c1, d1 in boxes[index + 1:]:
                overlap = (a0 < c1 - tolerance and c0 < a1 - tolerance
                           and b0 < d1 - tolerance and d0 < b1 - tolerance)
                assert not overlap, ((a0, b0, a1, b1), (c0, d0, c1, d1))


def test_the_sheet_reserves_the_band_and_spaces_the_tiers_at_its_own_scale(catlin_model_ro):
    scene = framed_floorplan(catlin_model_ro, "main", ARCH_D)
    frame = scene.frame
    assert frame is not None and frame.scale == pytest.approx(0.25), frame.scale_label
    facade = min(abs(n.offset) for n in scene.nodes if isinstance(n, ArchDimension))
    assert facade == pytest.approx(tier_offsets(0.25)[0])


def test_the_band_is_deepest_where_the_three_tiers_and_outboard_text_sit():
    west, east, south, north = dimension_band_in()
    assert west > south > north > east > TIER_FIRST_IN
