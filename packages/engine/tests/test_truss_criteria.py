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
    assert "H2.5ASS, SPF COLUMN 615 LB WITH ALL TRUSS NAILS LANDING (0.73)" in block
    assert "SSA8D stainless ring-shank" in block
    # Simpson fn. 14: design 289 against the 260 lb three-nail row is 1.11 on the canopy.
    assert "DESIGN UPLIFT 289 LB AGAINST THE THREE-NAIL 2x4 CHORD ROW 260 LB" in block
    assert "1.11, SO THE HEEL STANDS ONLY WITH ALL FIVE TRUSS NAILS LANDING" in block
    assert "DESIGN UPLIFT 178 LB AGAINST THE THREE-NAIL 2x4 CHORD ROW 260 LB" in block
    assert "CLOSED EITHER WAY" in block
    assert "CLOSED ONLY IF THE HEEL CONDITION ABOVE IS CONFIRMED" in block
    # The truss's own chord bearing is the supplier's, said aloud with the number it accepts.
    assert "CHORD BEARING ON BM-BW-RW: THE SUPPLIER CHECKS THE TRUSS CHORD'S OWN FC-PERP" in block
    assert "AT MAX 2,353 LB, 1.5 IN CHORD ON 5.5 IN OF BEARING = 285 PSI" in block
    assert "N-S 764 LB AXIAL" in block


def test_floor_orders_carry_their_applied_loads(block) -> None:
    """§2: line 316 per-ply West 118 / East 190; J12's line 272 east max 2,327 of 3,500."""
    assert "PER PLY ADDS 118 LB WEST, 190 LB EAST; MAX 753 / 826 LB" in block
    assert "MAX 1,236 / 2,327 LB" in block
    assert "CLOSED - MAX 2,327 LB AGAINST THE MAKER'S PUBLISHED 3,500 LB" in block


def test_the_two_statuses_never_merge(block) -> None:
    assert block.count("SUPPORTING STRUCTURE") == 4 and block.count("COMPONENT: OPEN") == 4


def test_supporting_structure_closes_and_the_component_stays_open(catlin_ctx) -> None:
    """Decisions 20 and 24: RF-GARAGE's heel closes on its R802.11 178 lb even at the three-nail
    row; the canopy's 289 lb does NOT (260 lb, fn. 14) and stays UNKNOWN until the heel nailing is
    confirmed, never a PASS at the specified 450 lb. The supplier's design is UNKNOWN on both."""
    from typehaus.checks.structural.truss_reactions import truss_reactions
    from typehaus.checks.structural.uplift_path import uplift_capacity_items

    truss = truss_reactions(catlin_ctx)
    passed = [f for f in truss if f.result.name == "PASS"]
    assert len(passed) == 2 and all(f.element_tags == ("RF-GARAGE",) for f in passed)
    unknown = [f for f in truss if f.result.name == "UNKNOWN"]
    open_heel = [f for f in unknown if "NOT CLOSED until the heel condition" in f.message]
    assert len(open_heel) == 2 and all(f.element_tags == ("RF-BW-CANOPY",) for f in open_heel)
    assert all("1.11" in f.message and "SPF column" in f.message for f in open_heel)
    assert len([f for f in unknown if "NOT YET CONFIRMED" in f.message]) == 2
    uplift = [f for f in uplift_capacity_items(catlin_ctx) if "RF-GARAGE" in f.element_tags]
    assert any(f.result.name == "PASS" and "178 lb" in f.message for f in uplift)
