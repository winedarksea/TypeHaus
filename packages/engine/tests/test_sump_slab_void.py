"""A sump pit is a hole in its slab, and a horizontal cast sleeve is one solid (2026-09-24)."""

from __future__ import annotations

import copy
import dataclasses

from shapely.geometry import Polygon

from typehaus.resolve.mep_concrete import concrete_crossings


def test_a_horizontal_sleeve_is_one_swept_solid(catlin_model_ro):
    horizontal = [s for s in catlin_model_ro.sleeves
                  if s.axis == "horizontal" and s.center_z_m is not None]
    assert horizontal
    for sleeve in horizontal:
        solids = [s for s in catlin_model_ro.solids
                  if s.category == "pipe_sleeve" and s.tag.startswith(sleeve.tag)]
        assert len(solids) == 1, (sleeve.tag, [s.tag for s in solids])
        assert solids[0].tag == sleeve.tag and solids[0].sweep is not None
        assert len(solids[0].sweep.path) == 2


def test_a_sump_voids_its_host_slab(catlin_model_ro):
    pit = next(s for s in catlin_model_ro.solids if s.tag == "SM-B-RADON")
    hole = Polygon(pit.outline)
    for solid in catlin_model_ro.solids:
        if solid.tag == "SL-B-FLOOR" or solid.tag.startswith("SL-B-FLOOR:"):
            assert any(Polygon(v).equals_exact(hole, 1e-9) for v in solid.voids), solid.tag


def test_a_run_inside_a_slab_void_is_not_a_crossing(catlin_model):
    def radon_leg(model):
        return [c for c in concrete_crossings(model) if c["run"] == "PR-B-RADON-LEG"]

    assert radon_leg(catlin_model) == []
    # Fill the hole back in and the same pipe is a slab crossing.
    filled = copy.copy(catlin_model)
    filled.solids = [dataclasses.replace(s, voids=()) if s.tag == "SL-B-FLOOR" else s
                     for s in catlin_model.solids]
    assert [c["host"] for c in radon_leg(filled)] == ["SL-B-FLOOR"]
