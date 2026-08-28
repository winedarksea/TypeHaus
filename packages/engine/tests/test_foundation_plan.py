"""Foundation plan builder — real S-100 (Permit-ready plan set Phase 1, → 20)."""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from typehaus.emit.draw.foundationplan import build_foundation_plan, has_foundation_content
from typehaus.emit.draw.scene import Leader, Polyline
from typehaus.resolve import resolve
from typehaus.source import load_plan
from typehaus.quantities import inch


@pytest.fixture(scope="module")
def starter_model(starter_dir: Path):
    result = load_plan(starter_dir)
    model, findings = resolve(result.plan)
    errors = [f for f in findings if f.severity.value == "error"]
    assert not errors, errors
    return model


def test_catlin_has_foundation_content(catlin_model):
    assert has_foundation_content(catlin_model)


def test_starter_has_no_foundation_content(starter_model):
    # Starter is a simple two-storey box with no FoundationWall/Footing/Pad/Slab —
    # S-100 must be omitted from the sheet index for it (build_sheet_index test covers that).
    assert not has_foundation_content(starter_model)


def test_foundation_plan_draws_basement_walls_and_slab(catlin_model):
    scene = build_foundation_plan(catlin_model)
    layers = scene.by_layer()
    assert "S-FNDN" in layers
    assert "A-SLAB" in layers
    slab_tags = {n.tag for n in layers["A-SLAB"] if isinstance(n, Polyline)}
    assert "SL-B-FLOOR" in slab_tags
    # Walls drawn are basement-storey, or the garage brick wainscot's veneer — never a
    # re-render of "main". The wainscot (W-G-BRICK-*, 2026-08-26) is filed on "garage" for
    # an unrelated reason (RM-GARAGE's conditioned=False, so it must not be mistaken for an
    # envelope wall between conditioned rooms — see houses/catlin/CLAUDE.md), but it is a
    # real `FoundationWall` with an absolute elevation, so `foundation_walls()` picks it up
    # by `is_foundation` regardless of storey and it legitimately belongs on S-100 too.
    wall_tags = {n.tag for n in layers["S-FNDN"] if isinstance(n, Polyline)}
    # W-B-CS was here until 2026-08-28, when it was framed — it is not a FoundationWall any
    # more and has no business on S-100's foundation layer. W-B-S2 replaces it: the sunken
    # garden's sauna curb, a real 7 1/4" pour on FT-B-S2.
    assert {"W-B-S1", "W-B-S2", "W-GF-N"} <= wall_tags
    assert all(catlin_model.wall(tag).storey in ("basement", "garage") for tag in wall_tags)


def test_foundation_plan_has_footing_leaders(catlin_model):
    scene = build_foundation_plan(catlin_model)
    leaders = [n for n in scene.nodes if isinstance(n, Leader)]
    assert leaders
    assert any("CONT. FTG." in leader.text for leader in leaders)


def test_catlin_house_footings_resolve_bedding(catlin_model):
    house_footings = {tag for tag in
                      (s.tag for s in catlin_model.solids if s.category == "footing")
                      if tag.startswith("FT-B-")}
    bedding_hosts = {fb.host for fb in catlin_model.footing_beddings}
    assert house_footings
    assert house_footings <= bedding_hosts


def test_footing_bedding_undercut_and_insulation(catlin_model):
    bedding = next(fb for fb in catlin_model.footing_beddings if fb.host == "FT-B-S1")
    assert bedding.z1_m > bedding.z0_m  # bed sits below the footing underside
    assert 0.15 < bedding.z1_m - bedding.z0_m < 0.22  # ~7" undercut
    assert bedding.geotextile and bedding.drain_tile
    assert bedding.perimeter_insulation_m is not None
    assert "#57" in bedding.aggregate


def test_sunken_garden_t_wall_footings_bear_on_42_inches_of_aggregate(catlin_model):
    garden_footings = {
        solid.tag for solid in catlin_model.solids
        if solid.category == "footing" and solid.tag.startswith("FT-SG-")
    }
    garden_bedding = {
        bedding.host: bedding
        for bedding in catlin_model.footing_beddings
        if bedding.host.startswith("FT-SG-")
    }

    assert garden_footings
    assert garden_footings == set(garden_bedding)
    for bedding in garden_bedding.values():
        assert bedding.z1_m - bedding.z0_m == pytest.approx(inch(42).meters)
        assert "#57" in bedding.aggregate


def test_bedding_drain_tile_resolves_as_a_ring_of_solids(catlin_model):
    """The tile was a geometry-less bool: billed by the foot, drawn in the wall detail, and
    invisible in 3D. It is derived from the bedding it runs in, like an eave's gutter members
    are derived from the eave, so its length is the bedding perimeter it follows."""
    bedding = next(fb for fb in catlin_model.footing_beddings if fb.host == "FT-B-S1")
    tile = [s for s in catlin_model.solids
            if s.category == "drain_tile" and s.tag.startswith(f"{bedding.tag}-DT-")]
    assert tile, "a bedding that runs tile must resolve one"

    ring = list(bedding.outline)
    perimeter = sum(math.dist(a, b) for a, b in zip(ring, ring[1:] + ring[:1]))
    # Each band is the run's own length; the ends butt rather than mitre, which is the same
    # simplification the take-off's perimeter measure makes.
    length = sum(max(_span(s.outline)) for s in tile)
    assert length == pytest.approx(perimeter, rel=0.05)

    spec = bedding.drain_tile_spec
    assert spec is not None and spec.diameter_m == pytest.approx(inch(4).meters)
    # The pipe floats on a course of bedding rather than sitting on the excavation floor.
    assert min(s.z0_m for s in tile) > bedding.z0_m
    assert max(s.z1_m for s in tile) < bedding.z1_m


def _span(outline) -> tuple[float, float]:
    xs = [x for x, _ in outline]
    ys = [y for _, y in outline]
    return (max(xs) - min(xs), max(ys) - min(ys))


def test_foundation_plan_has_footing_bedding_leader(catlin_model):
    scene = build_foundation_plan(catlin_model)
    leaders = [n for n in scene.nodes if isinstance(n, Leader)]
    assert any("WASHED CRUSHED STONE" in leader.text for leader in leaders)
    assert any("GEOTEXTILE" in leader.text for leader in leaders)


def test_starter_foundation_plan_is_empty(starter_model):
    scene = build_foundation_plan(starter_model)
    assert scene.nodes == ()


def test_footing_bedding_rejects_missing_host():
    from typehaus.model.structure import FootingBedding
    from typehaus.quantities import inch
    from typehaus.resolve.envelope import _resolve_footing_bedding
    from typehaus.resolve.model import ResolvedModel

    class _Plan:
        pass

    bedding = FootingBedding(uid="FB1", tag="FB-MISSING", host_ref="FT-NOPE",
                             undercut=inch(7))
    model = ResolvedModel(plan=_Plan())
    resolved, findings = _resolve_footing_bedding(model, bedding, "basement")
    assert resolved is None
    assert findings and findings[0].check_id == "integrity.footing_bedding_host"


def test_foundation_plan_dxf_round_trips(catlin_model, tmp_path: Path):
    import ezdxf

    from typehaus.emit.draw.dxf_writer import write_dxf

    scene = build_foundation_plan(catlin_model)
    path = write_dxf(scene, tmp_path / "foundation.dxf")
    doc = ezdxf.readfile(path)
    assert doc.units == 1
    names = {layer.dxf.name for layer in doc.layers}
    assert {"S-FNDN", "S-FNDN-FTNG", "A-SLAB"} <= names
