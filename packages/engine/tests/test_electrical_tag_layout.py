"""E-1xx device tags are laid out clear of each other and of device markers."""

from __future__ import annotations

from itertools import combinations

import pytest
from shapely.geometry import box

from typehaus.emit.draw.annotate import model_in_per_pt
from typehaus.emit.draw.annotation_layout import Candidate, annotation_polygon
from typehaus.emit.draw.annotation_scene import resolve_scene_annotations
from typehaus.emit.draw.electricalplan import build_electrical_plan
from typehaus.emit.draw.paper import ARCH_D
from typehaus.emit.draw.scene import Symbol, Text
from typehaus.emit.draw.sheet_writer import frame_for_scene, set_paper
from typehaus.emit.draw.trade_frame import trade_plan_sheet


@pytest.mark.parametrize("storey", ["basement", "main"])
def test_tags_do_not_overprint(catlin_model_ro, storey):
    with set_paper(ARCH_D):  # the 24x36 set the sheets are framed for
        scene = trade_plan_sheet(build_electrical_plan, storey)(catlin_model_ro)
    frame = scene.frame or frame_for_scene(scene, ARCH_D)
    scene = resolve_scene_annotations(scene.model_copy(update={"frame": frame}), frame)
    per_pt = model_in_per_pt(frame.scale)
    boxes = [annotation_polygon(Candidate(n.anchor, n.align, n.rotation), n.content,
                                n.height_pt, frame.scale)
             for n in scene.nodes if isinstance(n, Text) and n.height_pt]
    assert len(boxes) > 50
    assert not [1 for a, b in combinations(boxes, 2) if a.intersects(b)]
    markers = [n.insert for n in scene.nodes if isinstance(n, Symbol) and n.params.get("avoid_pt")]
    half = 3.0 * per_pt
    assert not [1 for (x, y) in markers for b in boxes
                if b.intersects(box(x - half, y - half, x + half, y + half))]
