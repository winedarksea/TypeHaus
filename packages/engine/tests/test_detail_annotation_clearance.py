"""A detail's continuity tags and keyed bubbles stay off each other and off the dimensions.

The exterior-door opening is the case that exposed it: its tags were pinned to the opening's
mid-height (air), printed over the head's truss/flashing, and its bubbles' leaders crossed.
"""

from __future__ import annotations

from shapely.geometry import LineString
from shapely.geometry import box as shapely_box

from typehaus.emit.draw.annotate import leader_box
from typehaus.emit.draw.annotation_layout_detail import CLAIM_ANCHOR
from typehaus.emit.draw.scene import ArchDimension, Leader

_DOOR = "opening_perimeter:door:EXT_2X6_BOARD_BATTEN"


def _claims(scene):
    return [n for n in scene.nodes
            if isinstance(n, Leader) and getattr(n.anchor, "name", "") == CLAIM_ANCHOR]


def test_the_door_tags_sit_at_the_head_clear_of_the_dimension(catlin_details):
    _, scene, _ = catlin_details[_DOOR]
    dims = [n for n in scene.nodes if isinstance(n, ArchDimension)]
    claims = _claims(scene)
    assert claims
    head_z = max(max(d.p0[1], d.p1[1]) for d in dims)
    for claim in claims:
        assert claim.to[1] >= head_z, "a continuity tag points into the void between jambs"
        shape = shapely_box(*leader_box(claim, scene.frame.scale))
        assert not any(shape.intersects(LineString((d.p0, d.p1))) for d in dims)


def test_the_door_bubble_leaders_do_not_cross(catlin_details):
    _, scene, _ = catlin_details[_DOOR]
    leaders = [n for n in scene.nodes if isinstance(n, Leader) and not n.text]
    assert len(leaders) >= 3
    for i, a in enumerate(leaders):
        for b in leaders[i + 1:]:
            assert not LineString((a.at, a.to)).intersects(LineString((b.at, b.to)))
