"""Drainage plan builder (P-2xx) and the C-101 stormwater overlay.

The stormwater family had a BOM section and a real IFC system and no drawing at all: the
buried tile, the drywells and the leaders lived only in 3D. These pin the new per-storey
P-2xx sheets and the site-plan overlay that shows where the roof water goes once it leaves
the building.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.emit.draw.drainageplan import build_drainage_plan, has_drainage_content
from typehaus.emit.draw.scene import Polyline
from typehaus.emit.draw.siteplan import build_site_plan
from typehaus.emit.trades import DRAINAGE_CATEGORIES
from typehaus.resolve import resolve
from typehaus.source import load_plan

CATLIN_DIR = Path(__file__).resolve().parents[3] / "houses" / "catlin"


@pytest.fixture(scope="module")
def catlin_model():
    result = load_plan(CATLIN_DIR)
    model, findings = resolve(result.plan)
    errors = [f for f in findings if f.severity.value == "error"]
    assert not errors, errors
    return model


def test_the_gate_opens_only_where_stormwater_lives(catlin_model):
    gated = {s.tag for s in catlin_model.plan.storeys
             if has_drainage_content(catlin_model, s.tag)}
    with_solids = {solid.storey for solid in catlin_model.solids
                   if (solid.category or "").lower() in DRAINAGE_CATEGORIES}
    with_derived = {roof.storey for roof in catlin_model.roofs
                    if any(m.category == "gutter" for m in roof.members)}
    assert gated == with_solids | with_derived
    assert gated, "fixture regression: the Catlin house lost its drainage"


def test_the_plan_draws_every_drainage_solid_on_its_storey(catlin_model):
    for storey in sorted({s.tag for s in catlin_model.plan.storeys
                          if has_drainage_content(catlin_model, s.tag)}):
        scene = build_drainage_plan(catlin_model, storey)
        drawn = {node.tag for node in scene.nodes
                 if isinstance(node, Polyline) and node.layer.startswith("P-STRM")}
        expected = {solid.tag for solid in catlin_model.solids
                    if solid.storey == storey
                    and (solid.category or "").lower() in DRAINAGE_CATEGORIES}
        assert expected <= drawn, sorted(expected - drawn)


def test_buried_work_draws_dashed_and_hung_work_solid(catlin_model):
    """A dashed line is the drawing's way of saying "you cannot see this after backfill" —
    tile and trench must never print like a gutter someone can point at."""
    storeys = [s.tag for s in catlin_model.plan.storeys
               if has_drainage_content(catlin_model, s.tag)]
    linetypes: dict = {}
    for storey in storeys:
        for node in build_drainage_plan(catlin_model, storey).nodes:
            if isinstance(node, Polyline) and node.layer.startswith("P-STRM"):
                linetypes.setdefault(node.layer, set()).add(node.linetype)
    assert linetypes.get("P-STRM-TILE", set()) <= {"DASHED"}
    assert "CONTINUOUS" in linetypes.get("P-STRM-GUTR", set())


def test_the_derived_eave_gutter_reaches_a_sheet(catlin_model):
    """The garage roof derives its own channel; it is aluminium somebody installs, and it
    was on no drawing. One band per run — three parallel lines read as three gutters."""
    garage = build_drainage_plan(catlin_model, "garage")
    derived = [node for node in garage.nodes if isinstance(node, Polyline)
               and node.tag and node.tag.startswith("RF-GARAGE:")]
    assert derived
    assert all(node.tag.endswith("-bottom") for node in derived)


def test_the_site_plan_carries_the_stormwater_overlay(catlin_model):
    scene = build_site_plan(catlin_model)
    overlay = [node for node in scene.nodes
               if isinstance(node, Polyline) and node.layer == "C-STRM-DRAN"]
    assert overlay, "C-101 must show where the roof water goes"
    tags = {node.tag for node in overlay}
    drywells = {solid.tag for solid in catlin_model.solids if solid.category == "drywell"}
    assert drywells and drywells <= tags


def test_drainage_sheets_join_the_index_in_the_p200_series(catlin_model):
    from typehaus.emit.draw.sheets import build_sheet_index

    sheets = {s.number: s for s in build_sheet_index(catlin_model)}
    numbers = [n for n in sheets if n.startswith("P-2")]
    assert numbers, "the drainage plans must reach the permit set"
    expected = sum(1 for s in catlin_model.plan.storeys
                   if has_drainage_content(catlin_model, s.tag))
    assert len(numbers) == expected
    assert "P-201" in sheets and sheets["P-201"].title.startswith("Drainage plan")
    assert sheets["P-201"].north_arrow
