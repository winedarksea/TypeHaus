"""``mep.pocket_occupancy`` — a pocket is a hole in a wall, not a hole in a storey.

The check tested plan geometry alone, which is right for the thing it was written for (a
box or a pipe inside the leaf's travel) and wrong one floor up: ``D-M-LAUN``'s pocket runs
under the suite bathroom, so a second-storey lavatory branch in the floor trusses 32" over
the leaf read as occupying it. The elevation band is what separates the two.
"""

from __future__ import annotations

import dataclasses

import pytest

from typehaus.checks import run_from_model
from typehaus.checks.mep.pockets import _POCKET_HEAD_TRACK_M, _pocket_bands
from typehaus.checks.registry import Tier, registered
from typehaus.findings import Result


@pytest.fixture(scope="module")
def findings(catlin_model_ro):
    report = run_from_model(catlin_model_ro, [], tier=Tier.CODE, only="mep.pocket_occupancy")
    return [f for f in report.findings if f.check_id == "mep.pocket_occupancy"]


def test_the_check_is_registered() -> None:
    assert "mep.pocket_occupancy" in {cid for cid, _ in registered(Tier.CODE)}


def test_catlin_has_nothing_in_a_pocket(findings) -> None:
    assert findings
    fails = [f for f in findings if f.result is Result.FAIL]
    assert not fails, [f.message for f in fails]


def test_the_band_stops_just_above_the_leaf(catlin_model_ro) -> None:
    """The z band is the leaf's own travel, not the wall. ``D-M-LAUN`` is an 80" door on a
    wall based at the main floor, so the cavity ends a head track over 80" — not at
    ``W-M-HS4``'s 120" top, which is where a wall-shaped band would put it."""
    class _Ctx:
        model = catlin_model_ro
        plan = catlin_model_ro.plan

    bands = {(op.tag, wall): (low, high)
             for op, wall, _poly, (low, high) in _pocket_bands(_Ctx())}
    low, high = bands[("D-M-LAUN", "W-M-HS4")]
    assert low == pytest.approx(0.0, abs=1e-9)
    assert high == pytest.approx(80 * 0.0254 + _POCKET_HEAD_TRACK_M, abs=1e-9)


def test_laundry_pocket_follows_the_aligned_stud_cavity(catlin_model_ro) -> None:
    """The authored node line stays put while the built 2x4 wall moves north an inch."""
    from typehaus.emit.ifc.architectural import _opening_segment
    from typehaus.model.enums import DoorOperation
    from typehaus.resolve.geometry import opening_center
    from typehaus.resolve.geometry_openings import opening_parts

    class _Ctx:
        model = catlin_model_ro
        plan = catlin_model_ro.plan

    wall = catlin_model_ro.wall("W-M-HS3")
    door = next(op for op in catlin_model_ro.openings if op.tag == "D-M-LAUN")
    band = next(poly for op, tag, poly, _z in _pocket_bands(_Ctx())
                if op.tag == door.tag and tag == wall.tag)
    structure = next(layer for layer in wall.layers if layer.function == "structure")
    structure_center_y = (min(y for _x, y in structure.polygon)
                          + max(y for _x, y in structure.polygon)) / 2
    north_faces = [max(y for layer in catlin_model_ro.wall(tag).layers
                       if layer.material_ref == "gwb"
                       for _x, y in layer.polygon)
                   for tag in ("W-M-HS2", "W-M-HS3", "W-M-HS4")]
    assert north_faces == pytest.approx([271.375 * 0.0254] * 3)
    assert structure_center_y - wall.axis[0][1] == pytest.approx(0.0254)
    assert opening_center(wall, door)[1] == pytest.approx(structure_center_y)
    assert band.centroid.y == pytest.approx(structure_center_y)
    leaf = next(part for part in opening_parts(wall, door, DoorOperation.POCKET)
                if part.key == "leaf")
    assert sum(y for _x, y in leaf.solids[0].ring) / 4 == pytest.approx(structure_center_y)
    first_jamb, second_jamb, _depth = _opening_segment(wall, door)
    assert first_jamb[1] == pytest.approx(structure_center_y)
    assert second_jamb[1] == pytest.approx(structure_center_y)


def test_a_pipe_over_the_head_track_is_not_in_the_pocket(catlin_model) -> None:
    """``PR-M-S-SUITE-LAV-DRAIN`` crosses ``D-M-LAUN``'s pocket squarely in plan and clears
    it by 32" in elevation. Drop that run to the leaf's own height and the finding comes
    back — same plan geometry, so it is the z term and nothing else deciding it."""
    original = next(r for r in catlin_model.pipe_runs
                    if r.tag == "PR-M-S-SUITE-LAV-DRAIN")
    assert not _fails(catlin_model)

    dropped = dataclasses.replace(original, z_m=tuple(40 * 0.0254 for _ in original.z_m))
    model = dataclasses.replace(
        catlin_model,
        pipe_runs=tuple(dropped if r.tag == original.tag else r
                        for r in catlin_model.pipe_runs))
    fails = _fails(model)
    assert [f.element_tags for f in fails] == [("D-M-LAUN", "W-M-HS4",
                                                "PR-M-S-SUITE-LAV-DRAIN")]


def test_the_gym_duct_must_clear_the_bath_pocket(catlin_model) -> None:
    """The 4" radial crosses the hall pocket above its head track."""
    original = next(duct for duct in catlin_model.ducts if duct.tag == "DU-B-ERV-R-GYM")
    assert not _fails(catlin_model)
    lowered = dataclasses.replace(
        original, z_m=tuple(z - 4.5 * 0.0254 if index in (4, 5, 6) else z
                               for index, z in enumerate(original.z_m)))
    model = dataclasses.replace(
        catlin_model,
        ducts=tuple(lowered if duct.tag == original.tag else duct
                    for duct in catlin_model.ducts))
    assert ("D-B-BATH", "W-B-HALL-W", "DU-B-ERV-R-GYM") in [
        finding.element_tags for finding in _fails(model)]


def _fails(model):
    return [f for f in run_from_model(model, [], tier=Tier.CODE,
                                      only="mep.pocket_occupancy").findings
            if f.check_id == "mep.pocket_occupancy" and f.result is Result.FAIL]
