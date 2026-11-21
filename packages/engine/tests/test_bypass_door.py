"""D-M-MUDC on its Johnson 138F set: the RO it publishes and the parts it draws."""

from __future__ import annotations

import pytest

from typehaus.resolve.geometry_ir import GPrism
from typehaus.server.model_json_catalog import catalog_json

_IN = 0.0254


def _along_and_normal(model, opening):
    from typehaus.resolve.geometry import opening_center, wall_frame

    wall = model.wall(opening.host_wall)
    _, (ux, uy), (nx, ny), _ = wall_frame(wall)
    cx, cy = opening_center(wall, opening)

    def project(solid):
        pts = solid.ring
        along = [(x - cx) * ux + (y - cy) * uy for x, y in pts]
        across = [(x - cx) * nx + (y - cy) * ny for x, y in pts]
        return (min(along), max(along)), sum(across) / len(across)

    return project


def test_bypass_set_sizes_its_opening_and_draws_two_lanes(catlin_model_ro):
    model = catlin_model_ro
    opening = next(o for o in model.openings if o.tag == "D-M-MUDC")
    sizing = opening.sizing
    # 2W - 1" finished + 1" jamb a side; leaf + 2 3/8" + 1" head jamb over the floor build-up.
    assert sizing.rough_w_m / _IN == pytest.approx(49.0)
    assert (sizing.rough_h_m - sizing.floor_finish_m) / _IN == pytest.approx(80 + 2.375 + 1)

    parts = {p.key: p for p in model.geometry.by_uid(opening.uid).parts}
    assert {"bypass_track", "bypass_guide", "bypass_pull"} <= parts.keys()
    assert parts["bypass_track"].catalog.name == "PROD-JOHNSON-138F482D"
    project = _along_and_normal(model, opening)
    leaves = sorted((project(s) for s in parts["leaf"].solids if isinstance(s, GPrism)))
    assert len(leaves) == 2
    (a0, a1), lane_a = leaves[0]
    (b0, b1), lane_b = leaves[1]
    assert (a1 - b0) / _IN == pytest.approx(1.0)  # they lap 1" at the centre
    assert abs(lane_a - lane_b) / _IN == pytest.approx(1.6875)
    bottom = min(s.z0_m for s in parts["leaf"].solids)
    assert (bottom - opening.bypass_door.finished_floor_z_m) / _IN == pytest.approx(0.375)


def test_interior_door_type_serves_its_product_core_and_undercut(catlin_model_ro):
    types = {t["tag"]: t for t in catalog_json(catlin_model_ro, None, None)["catalog"]
             ["door_types"]}
    bed = types["DT-INT-SWING30-PRIV"]
    assert bed["product_ref"] == "PROD-STEVES-FLUSH-HC-PREHUNG"
    assert bed["core"] == "hollow"
    assert bed["undercut_m"] / _IN == pytest.approx(0.75)
    assert types["DT-INT-BYPASS48"]["bypass_door"]["overlap_m"] / _IN == pytest.approx(1.0)
