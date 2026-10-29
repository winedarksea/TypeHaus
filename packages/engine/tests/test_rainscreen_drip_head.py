"""The starter's fiber-cement rainscreen heads take the generic Z drip flashing.

``resolve/opening_head_drip.py`` sweeps it from the cladding Material's kit, the head strip
closes the cavity's foot 1/4" clear of it, ``integrity.rainscreen_cavity`` grades both, and
the take-off bills it by the foot.
"""

from __future__ import annotations

from copy import copy
from dataclasses import replace

import pytest

from typehaus.checks.integrity import rainscreen_cavity
from typehaus.quantities import inch
from typehaus.resolve.opening_head_drip import DRIP_HEAD_PRODUCT
from typehaus.resolve.rainscreen_strips import STRIP_PRODUCT
from typehaus.takeoff.cladding_trim import cladding_trim_takeoff

_HEADS = 9  # eight windows and the front door


@pytest.fixture(scope="module")
def starter_model(starter_dir):
    from typehaus.resolve import resolve
    from typehaus.source import load_plan

    model, _ = resolve(load_plan(starter_dir).plan)
    return model


def test_every_starter_head_is_flashed_strip_closed_and_graded(starter_model):
    model = starter_model
    heads = {s.host_ref for s in model.solids if s.product == DRIP_HEAD_PRODUCT}
    assert len(heads) == _HEADS
    assert {s.host_ref for s in model.solids if s.product == STRIP_PRODUCT
            and "-HEADSTRIP-" in s.tag} == heads
    # The legacy unbilled drip is replaced, not doubled.
    assert not [s for s in model.solids if s.host_ref in heads
                and s.category == "opening_head_flashing"]
    findings = rainscreen_cavity._heads(model)
    assert [f.result.name for f in findings] == ["PASS"], findings
    rows = [r for r in cladding_trim_takeoff(model) if r["part"] == DRIP_HEAD_PRODUCT]
    assert len(rows) == 1 and rows[0]["unit"] == "LF"
    assert rows[0]["length_ft"] == pytest.approx(sum(
        s.trim_length_m for s in model.solids if s.product == DRIP_HEAD_PRODUCT) / 0.3048,
        abs=0.01)
    assert not [r for r in cladding_trim_takeoff(model) if r["count"] == 0]


def _lowered(solid, dz):
    mesh = replace(solid.body_mesh, positions=tuple(
        (x, y, z - dz) for x, y, z in solid.body_mesh.positions))
    return replace(solid, body_mesh=mesh)


@pytest.mark.parametrize("case, needle", [
    ("no strip", "opens its voids to insects"),
    ("strip on the flashing", "under the 0.25 in its maker asks"),
    ("no strip-in", "not lapped under the WRB"),
    ("short", "does not run past the casing"),
])
def test_drip_head_grade_fails(starter_model, case, needle):
    model = copy(starter_model)
    host = "WIN-101"
    if case == "no strip":
        model.solids = [s for s in model.solids
                        if not (s.host_ref == host and s.product == STRIP_PRODUCT)]
    elif case == "strip on the flashing":
        model.solids = [_lowered(s, inch(0.25).meters)
                        if s.host_ref == host and s.product == STRIP_PRODUCT else s
                        for s in model.solids]
    elif case == "no strip-in":
        model.solids = [s for s in model.solids if not (
            s.host_ref == host and s.category == "opening_flashing_membrane")]
    else:  # slid 2" along the wall: one end no longer passes the casing
        (x0, y0), (x1, y1) = model.wall(next(o.host_wall for o in model.openings
                                             if o.tag == host)).axis
        run = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        dx, dy = (inch(2).meters * (x1 - x0) / run, inch(2).meters * (y1 - y0) / run)
        model.solids = [replace(s, body_mesh=replace(s.body_mesh, positions=tuple(
            (x + dx, y + dy, z) for x, y, z in s.body_mesh.positions)))
            if s.host_ref == host and s.product == DRIP_HEAD_PRODUCT else s
            for s in model.solids]
    failures = [f for f in rainscreen_cavity._heads(model) if f.result.name == "FAIL"]
    assert [f.element_tags for f in failures] == [(host,)], failures
    assert needle in failures[0].message
