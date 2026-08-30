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


#: The five garden footings that carry the retaining walls. Their concrete stops 21" below
#: the court floor and the 42" aggregate section under it is what reaches frost depth.
_THE_RETAINING_WALL_FOOTINGS = ("FT-SG-W1", "FT-SG-W2", "FT-SG-E1", "FT-SG-E2", "FT-SG-S")

#: The two that stand under a ``Post``, not a ``FoundationWall``. Belled to frost depth on
#: 2026-08-29 (→ houses/catlin/params/sunken_garden.py), so unlike the five above they now
#: pass on plain cover and lean on no section at all.
_THE_FREESTANDING_COLUMN_PADS = ("FT-SG-COL", "FT-SG-FCOL")

#: The garden's own seven.
_THE_GARDENS_OWN = _THE_RETAINING_WALL_FOOTINGS + _THE_FREESTANDING_COLUMN_PADS


def test_the_retaining_wall_footings_pass_on_the_aggregate_section(frost_by_tag):
    """They pass, and — as with the R403.3 wings — the reason is the thing to pin.

    Not by depth: none of the five has more than 21" of concrete cover below the court
    floor. They pass because the 42" compacted washed-stone section they bear on is
    declared non-frost-susceptible and is drained, so its thickness counts toward the
    design frost depth (ASCE 32, listed as a frost-protection method by IRC R403.1.4.1).
    Asserting only ``PASS`` here would go green again the moment the check started
    measuring the wrong thing, so the section and the citation are asserted too.

    All seven of the garden's footings read UNKNOWN until 2026-08-29, on the reading that a
    footing standing inside the excavation is retaining it. That was true of these five and
    irrelevant: the frost protection was already modelled and simply was not being counted.
    """
    found = frost_by_tag
    for tag in _THE_RETAINING_WALL_FOOTINGS:
        finding = found[tag]
        assert finding.result is Result.PASS, (tag, finding.message)
        assert "ASCE 32" in finding.message, tag
        assert "IRC R403.1.4.1" in finding.message, tag
        assert any(name.startswith("FB-SG-") for name in finding.element_tags), tag


def test_the_belled_column_piers_pass_on_cover_and_not_on_the_section(frost_by_tag):
    """The two pads are the case that stopped needing the argument.

    They were 12"-deep spread bells passing on 54" of stone under them. On 2026-08-29 the
    owner chose to auger them to frost depth instead — the bell moved down, the sonotube
    above it grew, and each now has a full 42" of cover in its own right. So they must land
    in the plain "at least 42 inches below their lowest adjacent grade" bucket and must NOT
    cite the soil-replacement branch: a pier that reaches frost depth does not need ASCE 32,
    and printing the citation anyway would overstate what the drawing is relying on.
    """
    for tag in _THE_FREESTANDING_COLUMN_PADS:
        finding = frost_by_tag[tag]
        assert finding.result is Result.PASS, (tag, finding.message)
        assert "ASCE 32" not in finding.message, tag
        assert "at least" in finding.message, (tag, finding.message)


def test_a_freestanding_column_pad_is_not_called_a_retaining_structure(frost_by_tag):
    """R404.4 is about a structure holding up the hole it sits in. A spread bell under a
    freestanding porch column sits in the open court at 100% overlap and holds nothing
    back — the geometric "stands inside the excavation" test could not tell the two apart,
    and called both retaining. What the footing is authored to be *under* can: these two
    name ``Post`` elements, the other five name ``FoundationWall``s.
    """
    for tag in _THE_FREESTANDING_COLUMN_PADS:
        message = frost_by_tag[tag].message
        assert "R404.4" not in message, tag
        assert "retaining" not in message, tag


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


def _frost_by_tag(model):
    """``structural.frost_depth`` findings from a hand-altered model, indexed by tag."""
    from typehaus.checks import run_from_model

    report = run_from_model(model, [], tier=Tier.STRUCTURAL)
    out: dict[str, object] = {}
    for finding in report.findings:
        if finding.check_id == CHECK_ID:
            for tag in finding.element_tags:
                out.setdefault(tag, finding)
    return out


def _garden_beddings(catlin_model, edit):
    """The catlin model with ``edit`` applied to every sunken-garden bedding record."""
    import copy

    model = copy.copy(catlin_model)
    model.footing_beddings = [edit(bed) if bed.host.startswith("FT-SG-") else bed
                              for bed in catlin_model.footing_beddings]
    return model


def test_the_aggregate_section_only_counts_when_drained_deep_and_declared(catlin_model):
    """The falsifiable half of the soil-replacement branch.

    ASCE 32 counts a *well-drained*, *non-frost-susceptible* layer, and counts the depth it
    actually reaches. Take away any one of the three and the section stops counting: an
    undrained bed is not what the standard describes, a 12" bed does not reach a 42" frost
    depth, and an unstated gradation is not a claim at all (``None`` is not ``True`` —
    every bedding in every other house leaves it unset, and none of them may quietly start
    passing on stone nobody has graded).
    """
    import dataclasses

    undrained = _garden_beddings(
        catlin_model, lambda bed: dataclasses.replace(
            bed, non_frost_susceptible=True, drain_tile=False))
    shallow = _garden_beddings(
        catlin_model, lambda bed: dataclasses.replace(
            bed, non_frost_susceptible=True, z0_m=bed.z1_m - 12 * 0.0254))
    unstated = _garden_beddings(
        catlin_model, lambda bed: dataclasses.replace(bed, non_frost_susceptible=None))

    for label, model in (("undrained", undrained), ("too shallow", shallow),
                         ("unstated", unstated)):
        found = _frost_by_tag(model)
        for tag in _THE_RETAINING_WALL_FOOTINGS:
            assert "ASCE 32" not in found[tag].message, (label, tag)
            # And the five, which have no other protection to fall back on, go back to
            # UNKNOWN — the honest answer for a retaining structure inside its own hole
            # whose one counted frost measure has just been taken away. Not FAIL: the check
            # does not get to call an engineered wall non-compliant, only unevaluated.
            assert found[tag].result is Result.UNKNOWN, (label, tag)
            assert "R404.4" in found[tag].message, (label, tag)


def test_the_declared_section_is_what_moves_the_verdict(catlin_model):
    """The before-and-after, on one model: strip only the declaration and FT-SG-FCOL flips.

    This is the pair that stops the branch from being unfalsifiable — if the check passed
    these footings for some other reason, clearing the flag would not change the answer.

    The subject is a wall footing, and it has to be. The column pads were the probe until
    2026-08-29; belling them to frost depth gave them cover of their own, so clearing the
    flag now leaves them PASS — which is correct, and useless as a control. ``FT-SG-S`` is
    the far side of the court, out of reach of every R403.3 wing, and has nothing but its
    section.
    """
    import dataclasses

    assert _frost_by_tag(catlin_model)["FT-SG-S"].result is Result.PASS
    cleared = _garden_beddings(
        catlin_model, lambda bed: dataclasses.replace(bed, non_frost_susceptible=None))
    assert _frost_by_tag(cleared)["FT-SG-S"].result is Result.UNKNOWN
