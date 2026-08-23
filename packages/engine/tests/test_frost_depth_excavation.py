"""Frost cover is measured from the *lowest adjacent* grade, not from one global plane.

``structural.frost_depth`` compared every footing in the model to ``Site.grade`` — a single
scalar — for as long as it existed. That reading cannot see an excavation, and the Catlin
house contains one: the sunken garden's floor is 6'-6" below the site grade plane, and the
strips along it carry 8" of cover while reporting a comfortable 7'-2" and passing.

These pin the three outcomes the check now distinguishes, the shelter that keeps it from
over-reaching inward, and ``Footing.assembly`` reaching the resolved solid.
"""

from __future__ import annotations

import pytest
from _helpers import CATLIN

from typehaus.checks.registry import Tier
from typehaus.findings import Result
from typehaus.resolve.site_earth import (
    heated_floor_footprint,
    local_grade_elevation_m,
    open_excavation_floors,
    site_grade_elevation_m,
)

CHECK_ID = "structural.frost_depth"


@pytest.fixture(scope="module")
def frost_by_tag(catlin_plan):
    """Every ``structural.frost_depth`` finding, indexed by the tag it names."""
    from typehaus.checks.run import run

    report = run(catlin_plan, CATLIN, tier=Tier.STRUCTURAL)
    out: dict[str, object] = {}
    for finding in report.findings:
        if finding.check_id != CHECK_ID:
            continue
        for tag in finding.element_tags:
            out.setdefault(tag, finding)
    return out


def test_the_sunken_garden_floor_is_an_open_excavation(catlin_model):
    """A below-grade slab with no conditioned room over it is open ground, not a floor."""
    floors = {tag: top for tag, _polygon, top in open_excavation_floors(catlin_model)}
    assert "SL-SG-FLOOR" in floors
    # ...and the basement slab, at the same elevation, is not: it is the floor of heated rooms.
    assert "SL-B-FLOOR" not in floors
    assert floors["SL-SG-FLOOR"] < site_grade_elevation_m(catlin_model)


def test_local_grade_drops_to_the_garden_floor_beside_it(catlin_model):
    """The south strip's grade is the garden floor, and it says which surface set it."""
    south = next(s for s in catlin_model.solids if s.tag == "FT-B-S2")
    garden = next(s for s in catlin_model.solids if s.tag == "SL-SG-FLOOR")
    grade_m, source = local_grade_elevation_m(
        catlin_model, south.outline, 42 * 0.0254,
        open_excavation_floors(catlin_model), heated_floor_footprint(catlin_model))
    assert source == "SL-SG-FLOOR"
    assert grade_m == pytest.approx(garden.z1_m)
    assert (grade_m - south.z0_m) / 0.0254 == pytest.approx(8.0, abs=0.5)


def test_an_interior_footing_under_a_heated_slab_keeps_the_site_grade(catlin_model):
    """FT-B-CS sits 10" north of the garden in plan and 9'-2" under a heated basement.

    A bare distance test reads that 10" and lowers its grade by 6'-6". It is an interior
    footing inside the heated envelope — "otherwise protected from frost", R403.1.4.1 —
    and the excavation is on the far side of an insulated foundation wall from it.
    """
    spine = next(s for s in catlin_model.solids if s.tag == "FT-B-CS")
    grade_m, source = local_grade_elevation_m(
        catlin_model, spine.outline, 42 * 0.0254,
        open_excavation_floors(catlin_model), heated_floor_footprint(catlin_model))
    assert source is None
    assert grade_m == pytest.approx(site_grade_elevation_m(catlin_model))


#: The four house footings the sunken garden reaches. FT-B-BRICK's plinth bottoms 2" ABOVE
#: the garden floor; the three south strips carry 8" of cover under it. All four reported a
#: comfortable 7'-2" and passed until the grade was derived per footing.
_BESIDE_THE_GARDEN = ("FT-B-BRICK", "FT-B-S1", "FT-B-S2", "FT-B-S3")


def test_the_south_strips_and_the_plinth_are_protected_not_deep(frost_by_tag):
    """They pass, and the reason they pass is the thing to pin.

    Not by depth — none of the four has anything like 42" of cover below the garden floor,
    and FT-B-BRICK has negative cover. They pass through IRC R403.3's frost-protected
    shallow-foundation path, on the horizontal wing insulation drawn under the garden slab
    beside them (``params/sunken_garden.FROST_WINGS``). A check that reported PASS here
    without naming those elements would be reporting the old answer by accident.
    """
    for tag in _BESIDE_THE_GARDEN:
        finding = frost_by_tag[tag]
        assert finding.result is Result.PASS, tag
        assert "R403.3" in finding.message, tag
        assert any(name.startswith("SL-SG-FROST-") for name in finding.element_tags), tag


def test_without_the_wing_insulation_the_same_four_footings_fail(catlin_plan, catlin_model):
    """The finding this check existed to be unable to make.

    Take the drawn wings away and nothing else changes: the same four footings, the same
    8" and -2" of cover, the same 42" requirement. They FAIL. That is the before-and-after
    the R403.3 band exists to move, and pinning both halves is what stops the local-grade
    derivation from silently reverting to the single global plane — which would pass them
    both ways round and prove nothing.
    """
    import copy

    from typehaus.checks import run_from_model

    stripped = copy.copy(catlin_model)
    stripped.solids = [s for s in catlin_model.solids
                       if not s.tag.startswith("SL-SG-FROST-")]
    report = run_from_model(stripped, [], tier=Tier.STRUCTURAL)
    by_tag = {}
    for finding in report.findings:
        if finding.check_id == CHECK_ID:
            for tag in finding.element_tags:
                by_tag.setdefault(tag, finding)
    for tag in _BESIDE_THE_GARDEN:
        assert by_tag[tag].result is Result.FAIL, tag
        assert "SL-SG-FLOOR" in by_tag[tag].message, tag


def test_the_gardens_own_retaining_footings_route_to_the_engineer(frost_by_tag):
    """A structure retaining the hole it stands in is R404.4, not a table — so UNKNOWN.

    FAIL would be the wrong verdict and the wrong instruction: these are already outside
    Table R404.1.2(8) in ``structural.foundation_unbalanced_fill`` for the same reason, and
    they go to the same consultant rather than getting 21" more concrete under them.
    """
    found = frost_by_tag
    for tag in ("FT-SG-W1", "FT-SG-W2", "FT-SG-E1", "FT-SG-E2", "FT-SG-S",
                "FT-SG-COL", "FT-SG-FCOL"):
        assert found[tag].result is Result.UNKNOWN, tag
        assert "R404.4" in found[tag].message


def test_footings_away_from_the_excavation_are_unmoved(frost_by_tag):
    """A strict refinement: nothing that used to pass on the global plane stops passing."""
    found = frost_by_tag
    for tag in ("FT-B-N1", "FT-B-W1", "FT-B-E1", "FT-GF-N", "PD-BW-1"):
        assert found[tag].result is Result.PASS, tag


def test_footing_assembly_reaches_the_resolved_solid(catlin_plan, catlin_model):
    """``Footing`` carried no assembly and no material at all until 2026-08-22.

    Every footing in every house therefore priced and scheduled as plain cast concrete out
    of the hardcoded category row, and an insulated footing form — the FPSF answer to a
    shallow-cover condition — was simply not expressible. The invariant: whatever a
    ``Footing`` names, its resolved solid carries, so ``structural_solids_takeoff`` groups
    it and ``[concrete]``'s qualified key can price it apart from the plain strips.
    """
    from typehaus.model.structure import Footing

    authored = {e.tag: e.assembly for e in catlin_plan.all_elements()
                if isinstance(e, Footing)}
    assert authored, "the catlin house has footings"
    resolved = {s.tag: s.assembly for s in catlin_model.solids if s.category == "footing"}
    assert {tag: resolved[tag] for tag in authored} == authored


def test_the_sheet_note_no_longer_claims_every_footing_bears_42_below_grade(catlin_model):
    """The blanket claim was false on the garden side; the number was not."""
    from typehaus.emit.draw.foundation_schedule import foundation_general_notes

    notes = " | ".join(foundation_general_notes(catlin_model))
    assert "LOWEST ADJACENT FINISHED GRADE" in notes
    assert "SL-SG-FLOOR" in notes
    assert 'FT-B-S2 (8" COVER)' in notes
