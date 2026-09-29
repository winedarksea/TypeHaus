"""Tread depth and nosings measured off the built stair (notes/stair_nosing_basis.md)."""

from dataclasses import replace
from types import SimpleNamespace

import pytest
from _helpers import check_context

from typehaus.checks.code.mn_residential.stair_arrival import stair_head_landing
from typehaus.checks.code.mn_residential.stair_nosings import runs, tread_depth
from typehaus.findings import Result

_IN = 0.0254


def _stair(model, tag):
    return next(stair for stair in model.stairs if stair.tag == tag)


@pytest.mark.parametrize(("tag", "depth", "count", "projection", "noses"), [
    ("ST-B2M", 10.0, 12, 1.0, 14), ("ST-M2S", 10.0, 14, 1.0, 16),
    ("ST-S2A", 10.0, 12, 1.0, 13), ("ST-G-SERVICE", 11.0, 4, 0.0, 4),
    ("ST-SG-PORCH", 11.0, 4, 0.0, 4)])
def test_hand_numbers(catlin_model_ro, tag, depth, count, projection, noses):
    """§3: every straight tread one going deep, the last to its landing or floor nosing."""
    measured = runs(_stair(catlin_model_ro, tag))
    depths = [d for run, _ in measured for d in run]
    projections = [p for _, run in measured for p in run]
    assert len(depths) == count and len(projections) == noses
    assert all(d / _IN == pytest.approx(depth, abs=1e-3) for d in depths)
    assert all(p / _IN == pytest.approx(projection, abs=1e-3) for p in projections)


def test_catlin_passes(catlin_model_ro):
    findings = tread_depth(check_context(model=catlin_model_ro))
    assert findings and all(f.result in (Result.PASS, Result.NOT_APPLICABLE)
                            for f in findings), [f.message for f in findings]


def _with_stair(model, stair):
    return replace(model, stairs=[stair if s.tag == stair.tag else s for s in model.stairs])


def test_a_head_riser_in_front_of_its_framing_fails(catlin_model_ro):
    """§2: the board stood 3/4" toward the flight, and the last tread came out 9 1/4"."""
    stair = _stair(catlin_model_ro, "ST-S2A")
    head = max((m for m in stair.members if m.category == "riser"), key=lambda m: m.z1_m)
    ux, uy = head.orient
    moved = replace(head, p0=(head.p0[0] - ux * 0.75 * _IN, head.p0[1] - uy * 0.75 * _IN),
                    p1=(head.p1[0] - ux * 0.75 * _IN, head.p1[1] - uy * 0.75 * _IN))
    parts = tuple(replace(p, outline=tuple((x - ux * 0.75 * _IN, y - uy * 0.75 * _IN)
                                           for x, y in p.outline))
                  if p.key == "stairhead:nosing" else p for p in stair.finish_parts)
    broken = replace(stair, finish_parts=parts, members=tuple(
        moved if m is head else m for m in stair.members))
    [finding] = [f for f in tread_depth(check_context(
        model=_with_stair(catlin_model_ro, broken))) if "ST-S2A" in f.element_tags]
    assert finding.result is Result.FAIL and "9.250" in finding.message


def test_a_landing_edge_without_its_nosing_fails(catlin_model_ro):
    """Drop the landing lip and the last lower tread runs to the riser face: 11" vs 10"."""
    stair = _stair(catlin_model_ro, "ST-M2S")
    bare = replace(stair, finish_parts=tuple(
        p for p in stair.finish_parts if p.key != "landing-lower:nosing"))
    [finding] = [f for f in tread_depth(check_context(
        model=_with_stair(catlin_model_ro, bare))) if "ST-M2S" in f.element_tags]
    assert finding.result is Result.FAIL and "R311.7.5.2.1" in finding.message


def test_catlin_stairheads_have_36_inches(catlin_model_ro):
    findings = stair_head_landing(check_context(model=catlin_model_ro))
    passed = {f.message.split()[0] for f in findings if f.result is Result.PASS}
    assert passed == {"ST-B2M", "ST-M2S", "ST-S2A"}, [f.message for f in findings]


def test_a_wall_in_the_head_landing_fails(catlin_model_ro):
    """§4: a wall 30" past ST-S2A's top nosing is inside R311.7.6's 36"."""
    x0 = (270.375 - 30) * _IN
    ring = [(x0, 60 * _IN), (x0 - 4 * _IN, 60 * _IN), (x0 - 4 * _IN, 110 * _IN),
            (x0, 110 * _IN)]
    wall = SimpleNamespace(tag="W-TEST", z0_m=20 * 12 * _IN, z1_m=28 * 12 * _IN,
                           layers=[SimpleNamespace(polygon=ring)])
    model = replace(catlin_model_ro, walls=[*catlin_model_ro.walls, wall])
    [finding] = [f for f in stair_head_landing(check_context(model=model))
                 if "ST-S2A" in f.element_tags]
    assert finding.result is Result.FAIL and "W-TEST" in finding.message
