"""The truss criteria schedule against ``notes/canopy_truss_criteria.md`` (hand-worked)."""

from __future__ import annotations

import pytest


@pytest.fixture(scope="module")
def block(catlin_ctx):
    from typehaus.emit.draw.schedules.truss_criteria import truss_criteria_block

    return "\n".join(truss_criteria_block(catlin_ctx.model, catlin_ctx.preferences))


def test_roof_reactions_follow_the_drift_triangle(block) -> None:
    """§1: 1,464 / 2,353 / 2,052 lb on the canopy trusses; garage truss-000 1,916 lb."""
    for text in ("truss-000 1,464 lb; truss-001 2,353 lb; truss-002 2,052 lb",
                 "truss-000 1,916 lb; truss-001 1,681 lb"):
        assert text in block


def test_uplift_is_specified_and_the_nail_is_on_the_schedule(block) -> None:
    assert "MAX NET UPLIFT 450 LB PER HEEL AT BM-BW-RW, BM-BW-RE" in block
    assert "H2.5ASS 700 LB, 0.64" in block and "SSA8D stainless ring-shank" in block
    assert "H2.5A 615 LB, 0.73" in block
    assert "N-S 752 LB AXIAL" in block


def test_floor_orders_carry_their_applied_loads(block) -> None:
    """§2: line 316 per-ply West 118 / East 190; J12's line 272 east max 2,327 of 3,500."""
    assert "PER PLY ADDS 118 LB WEST, 190 LB EAST; MAX 753 / 826 LB" in block
    assert "MAX 1,236 / 2,327 LB" in block
    assert "CLOSED - MAX 2,327 LB AGAINST THE MAKER'S PUBLISHED 3,500 LB" in block


def test_the_two_statuses_never_merge(block) -> None:
    assert block.count("SUPPORTING STRUCTURE") == 4 and block.count("COMPONENT: OPEN") == 4


def test_supporting_structure_closes_and_the_component_stays_open(catlin_ctx) -> None:
    """Decisions 20 and 24: the specified heel ties PASS, the supplier's design is UNKNOWN, and
    RF-GARAGE's uplift is the R802.11 read (178 lb against 615), not an engineered item."""
    from typehaus.checks.structural.truss_reactions import truss_reactions
    from typehaus.checks.structural.uplift_path import uplift_capacity_items

    truss = truss_reactions(catlin_ctx)
    passed = [f for f in truss if f.result.name == "PASS"]
    assert len(passed) == 4 and all("supporting structure" in f.message for f in passed)
    unknown = [f for f in truss if f.result.name == "UNKNOWN"]
    assert len(unknown) == 2 and all("NOT YET CONFIRMED" in f.message for f in unknown)
    uplift = [f for f in uplift_capacity_items(catlin_ctx) if "RF-GARAGE" in f.element_tags]
    assert any(f.result.name == "PASS" and "178 lb" in f.message for f in uplift)
