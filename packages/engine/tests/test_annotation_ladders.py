"""Authored ladder spacing must follow paper scale without moving arrow targets."""

from __future__ import annotations

import pytest

from typehaus.emit.draw.annotate import model_in_per_pt, text_extent
from typehaus.emit.draw.annotation_ladders import LadderRequest, resolve_ladders
from typehaus.emit.draw.annotation_layout import Viewport
from typehaus.emit.draw.scene import Leader, NamedPoint, SceneBuilder


@pytest.mark.parametrize("scale", [0.1875, 0.375])
def test_ladder_reflow_preserves_order_targets_and_printed_clearance(scale):
    builder = SceneBuilder(name="crowded-layers", units="in")
    for index in range(12):
        target = (20, 100 - index * 2)
        node = Leader(anchor=NamedPoint(xy=target), at=(10, target[1]), to=target,
                      text=f"Layer {index}\nRequired thickness", height_pt=7)
        builder.add(node)
        builder.add_annotation_request(LadderRequest(str(index), node))
    original = builder.build()
    viewport = Viewport((-200, -200, 200, 200))
    result = resolve_ladders(original, viewport, scale)
    assert result == resolve_ladders(original, viewport, scale)
    assert not result.annotation_diagnostics
    assert [node.to for node in result.nodes] == [node.to for node in original.nodes]
    assert [node.text for node in result.nodes] == [node.text for node in original.nodes]
    height = text_extent(original.nodes[0].text, 7)[1] * model_in_per_pt(scale)
    for upper, lower in zip(result.nodes, result.nodes[1:], strict=False):
        assert upper.at[1] - lower.at[1] > height
    assert result.nodes[-1].at[1] - height / 2 > viewport.bounds[1]


def test_impossible_ladder_reports_overflow_without_losing_text():
    builder = SceneBuilder(name="overflow", units="in")
    for index in range(8):
        target = (10, index)
        node = Leader(anchor=NamedPoint(xy=target), at=(0, index), to=target,
                      text="REQUIRED NOTE", height_pt=7)
        builder.add(node)
        builder.add_annotation_request(LadderRequest(str(index), node))
    result = resolve_ladders(builder.build(), Viewport((-10, -10, 10, 10)), 0.1875)
    assert len(result.nodes) == 8
    assert result.annotation_diagnostics
