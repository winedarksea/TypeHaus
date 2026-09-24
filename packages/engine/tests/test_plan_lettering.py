"""Plan lettering at the NCS 3/32" floor, masonry openings to their edges, planter captions.

TODO: "Plan lettering other than dimensions", "Openings in the basement's concrete walls",
"The OPEN TO BELOW terrace labels on A-102".
"""

from __future__ import annotations

from typehaus.emit.draw import build_floorplan
from typehaus.emit.draw._shared import _facade_stations, is_masonry_host
from typehaus.emit.draw.callouts import callout_nodes
from typehaus.emit.draw.datum import model_at_level
from typehaus.emit.draw.keyed_notes import bubble_nodes
from typehaus.emit.draw.plan_labels import ROOM_LAYER
from typehaus.emit.draw.plan_marks import MARK_LAYER
from typehaus.emit.draw.scene import Text
from typehaus.emit.draw.typography import DIM_STRING_PT, ROOM_NAME_PT, TAG_PT
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedLayer, ResolvedOpening, ResolvedWall


def _texts(scene, layer=None):
    return [n for n in scene.nodes if isinstance(n, Text) and (layer is None or n.layer == layer)]


def test_tags_bubbles_and_room_blocks_are_at_least_3_32(catlin_model):
    assert TAG_PT >= DIM_STRING_PT and ROOM_NAME_PT > TAG_PT
    scene = build_floorplan(catlin_model, "main")
    rooms = _texts(scene, ROOM_LAYER)
    marks = _texts(scene, MARK_LAYER)
    assert rooms and marks
    assert min(t.height_pt for t in rooms + marks) >= DIM_STRING_PT
    assert max(t.height_pt for t in rooms) == ROOM_NAME_PT
    bubbles = [n for n in callout_nodes((0.0, 0.0), "1", "A-501")
               + bubble_nodes("K1", (0.0, 0.0)) if isinstance(n, Text)]
    assert all(t.height_pt >= DIM_STRING_PT for t in bubbles)


def test_flatwork_and_its_pockets_draw_on_the_site_plan_not_the_floor_plan(catlin_model):
    """Walks and the drive are site work. On A-101 the drive set the sheet extent and
    dropped it to 3/16"; on C-101 every slab and all 18 pockets are drawn."""
    from typehaus.emit.draw.siteplan import build_site_plan

    flatwork = {"SL-WK-A", "SL-WK-B", "SL-WK-C", "SL-WK-D", "SL-DW-DRIVE"}
    plan = build_floorplan(model_at_level(catlin_model, "main"), "main", dimension_scale=0.25)
    plan_tags = {getattr(n, "tag", None) for n in plan.nodes}
    assert not plan_tags & flatwork
    assert not {t for t in plan_tags if t and t.startswith("FO-WK-")}
    assert "PLANTER" not in [t.content for t in _texts(plan, "A-ANNO-TEXT")]
    site_tags = [getattr(n, "tag", None) for n in build_site_plan(catlin_model).nodes]
    assert flatwork <= set(site_tags)
    assert sum(1 for t in site_tags if t and t.startswith("FO-WK-")) == 18


def _wall(material: str) -> ResolvedWall:
    layer = ResolvedLayer(name="core", material_ref=material, function="structure",
                          thickness_m=0.2, polygon=())
    return ResolvedWall(uid="W", tag="W-1", storey="b", assembly="A",
                        axis=((0.0, 0.0), (6.0, 0.0)), layers=(layer,), z0_m=0.0, z1_m=2.4)


class _Model:
    def __init__(self, wall):
        self.openings = [ResolvedOpening(
            uid="O", tag="O-1", host_wall=wall.tag, type_ref=None, width_m=36 * M_PER_IN,
            height_m=1.0, sill_m=1.0, center_along_m=3.0, kind="window", is_door=False)]
        self._wall = wall

    def wall(self, tag):
        return self._wall


def test_a_concrete_wall_opening_is_dimensioned_to_its_edges():
    half = 18 * M_PER_IN
    concrete, framed = _wall("concrete"), _wall("spf")
    assert is_masonry_host(concrete) and not is_masonry_host(framed)
    stations = _facade_stations([concrete], _Model(concrete), 0, 1, 0.0, 0.0, 6.0)
    assert [round(s, 6) for s in stations] == [0.0, round(3.0 - half, 6),
                                               round(3.0 + half, 6), 6.0]
    assert _facade_stations([framed], _Model(framed), 0, 1, 0.0, 0.0, 6.0) == [0.0, 3.0, 6.0]
