"""Authored drainage elements, and the checks that hold their references to real things.

Drainage used to be asserted in prose. Two of the Catlin gutters sloped "to the east
downspout" while no such leader existed anywhere in the plan; the pit outside the garage was
a deepened footing bedding, so its excavation perimeter billed as drain tile that is not
there. This file covers the elements that replaced those stand-ins and the two advisory
checks that make the same mistake catchable next time.
"""

from __future__ import annotations


import pytest

from _helpers import check_context

from typehaus.checks.mep.drainage import discharge_consistency, downspout_ref
from typehaus.checks.registry import CheckContext
from typehaus.findings import Result
from typehaus.model.structure import Drywell, FrenchDrain
from typehaus.model.trim import Downspout, Gutter
from typehaus.quantities import ft, inch, pt
from typehaus.resolve import resolve

_M_TO_FT = 3.280839895



def _context(plan, model) -> CheckContext:
    return check_context(plan, model)


def _failures(findings) -> list:
    return [f for f in findings if f.result is Result.FAIL]


# --- the elements -------------------------------------------------------------------------

def test_every_authored_gutter_falls_to_a_leader_that_exists(catlin_plan, catlin_model):
    """The regression the whole phase is for. TR-RF-GUTTER-W/E, the garage eave gutter and
    TR-SG-GUTTER all named a downspout in prose; two of those leaders were never authored."""
    findings = downspout_ref(_context(catlin_plan, catlin_model))
    assert not _failures(findings), [f.message for f in _failures(findings)]

    leaders = {element.tag for storey in catlin_plan.storeys
               for element in catlin_plan.storey_elements(storey.tag)
               if isinstance(element, Downspout)}
    assert {"TR-RF-LEADER-W", "TR-RF-LEADER-E",
            "TR-G-LEADER-E", "TR-SG-LEADER-SE"} <= leaders


def test_the_garage_leader_takes_its_water_from_the_resolved_trough(catlin_model):
    """TR-G-LEADER-E's elevation is pinned rather than derived, because the EaveGutter above
    it deliberately is not: the raised-heel truss lifts the deck plane during the envelope
    stage. This is the tie that catches the pin drifting off the channel it drains."""
    roof = next(r for r in catlin_model.roofs if r.tag == "RF-GARAGE")
    floor = next(m for m in roof.members
                 if m.category == "gutter" and m.child_key.endswith("-bottom"))
    leader = next(s for s in catlin_model.solids if s.tag == "TR-G-LEADER-E")
    assert floor.z0_m <= leader.z1_m <= floor.z1_m, \
        "the leader's outlet must sit in the trough floor, not above or below it"
    grade_m = catlin_model.plan.project.site.grade.meters
    assert grade_m < leader.z0_m < grade_m + 0.5, \
        "and run down to a splash block just above the apron — measured from grade, which "\
        "the garage stands on and which is 2'-6\" below the house datum since 2026-08-18"


def test_the_balcony_leader_drops_the_full_storey_into_the_garden(catlin_model):
    leader = next(s for s in catlin_model.solids if s.tag == "TR-SG-LEADER-SE")
    gutter_bands = [s for s in catlin_model.solids
                    if s.tag.startswith("TR-SG-GUTTER-") and s.category == "gutter"]
    assert gutter_bands
    assert leader.z1_m <= min(band.z1_m for band in gutter_bands)
    assert leader.z0_m < 0.0, "it discharges down in the sunken garden, not at main level"


def test_the_hydrant_pit_is_a_drywell_and_no_longer_bills_phantom_tile(catlin_model):
    """As a FootingBedding the pit's perimeter counted as perimeter drain tile — tile that
    is not there and that nobody installs around a soakaway."""
    well = next(s for s in catlin_model.solids if s.tag == "DRW-G-HYDRANT")
    assert well.category == "drywell"
    assert not [b for b in catlin_model.footing_beddings if "HYDRANT" in b.tag]
    assert not [s for s in catlin_model.solids
                if s.category == "drain_tile" and "HYDRANT" in s.tag]


def test_the_garden_drywell_sits_below_the_bearing_bed_it_is_not_part_of(catlin_model):
    """The 42" of aggregate under the garden footings is a *bearing* course that happens to
    drain. The soakaway is a separate, deeper hole beneath it — and the garden needs one,
    because its floor is 9' down with no downhill side for anything to daylight to."""
    well = next(s for s in catlin_model.solids if s.tag == "DRW-SG-MAIN")
    assert well.category == "drywell"
    beds = [b for b in catlin_model.footing_beddings if b.host.startswith("FT-SG-")]
    assert beds
    bed_bottom = min(bed.z0_m for bed in beds)
    assert well.z1_m == pytest.approx(bed_bottom, abs=0.01), \
        "the well's top of stone meets the underside of the bearing bed — they stack"
    assert well.z0_m < bed_bottom, "and the well itself is below it, not part of it"
    assert (well.z1_m - well.z0_m) * _M_TO_FT == pytest.approx(6.0, abs=0.01)

    # The garden's tile falls to the well, not to a daylight outlet it does not have.
    assert {bed.drain_tile_spec.discharge for bed in beds} == {"DRW-SG-MAIN"}
    plan_well = catlin_model.plan.by_tag("DRW-SG-MAIN")
    assert "TR-SG-LEADER-SE" in plan_well.inlet_refs


def test_the_radon_sump_carries_its_pump(catlin_plan):
    sump = catlin_plan.by_tag("SM-B-RADON")
    assert sump.pump is not None
    assert sump.pump.circuit_ref == "CKT-SUMP"
    assert sump.pump.discharge == "daylight"


# --- the resolver, on elements the Catlin house does not author yet ------------------------

def _minimal_plan_with(catlin_plan, element, storey: str = "basement"):
    """The Catlin plan with one extra element spliced onto a storey.

    Cheaper and more honest than a synthetic plan: FrenchDrain and Drywell resolve against
    site grade and the storey table, and a hand-built two-wall fixture would not have either.
    """
    return catlin_plan.with_elements(
        storey, (*catlin_plan.storey_elements(storey), element))


def test_a_french_drain_resolves_a_trench_and_the_tile_inside_it(catlin_plan):
    from typehaus.model.structure import DrainTile

    run = FrenchDrain(
        uid="TSTFD00001", tag="FD-TEST", path=(pt(ft(60), ft(10)), pt(ft(60), ft(40))),
        invert=ft(-4), trench_width=inch(18), trench_depth=inch(24),
        tile=DrainTile(diameter=inch(4), discharge="daylight"))
    model, findings = resolve(_minimal_plan_with(catlin_plan, run))
    assert not [f for f in findings if f.severity.value == "error"]

    trench = [s for s in model.solids if s.category == "french_drain"]
    assert len(trench) == 1
    assert (trench[0].z1_m - trench[0].z0_m) == pytest.approx(inch(24).meters)
    # The pipe is not the trench: it is the product inside it, billed and drawn separately.
    tile = [s for s in model.solids if s.tag.startswith("FD-TEST-DT-")]
    assert tile and all(s.category == "drain_tile" for s in tile)
    assert min(s.z0_m for s in tile) > trench[0].z0_m, "the tile floats on bedding stone"


def test_an_open_french_drain_run_does_not_close_back_on_itself(catlin_plan):
    """A bedding's ring closes; an interceptor run ends where it discharges. Closing it
    would bill a phantom segment straight back across the yard."""
    from typehaus.model.structure import DrainTile

    run = FrenchDrain(
        uid="TSTFD00002", tag="FD-OPEN",
        path=(pt(ft(60), ft(10)), pt(ft(70), ft(10)), pt(ft(70), ft(30))),
        invert=ft(-4), trench_width=inch(18), trench_depth=inch(24),
        tile=DrainTile(diameter=inch(4)))
    model, _ = resolve(_minimal_plan_with(catlin_plan, run))
    assert len([s for s in model.solids if s.tag.startswith("FD-OPEN-DT-")]) == 2


def test_a_drywell_is_dug_from_grade_not_from_its_storey_datum(catlin_plan):
    """Authored on the basement storey, a soakaway outside the building would otherwise
    start at the basement floor and hang in the excavation."""
    well = Drywell(uid="TSTDW00001", tag="DRW-TEST", position=pt(ft(70), ft(70)),
                   diameter=ft(4), depth=ft(4))
    model, _ = resolve(_minimal_plan_with(catlin_plan, well))
    solid = next(s for s in model.solids if s.tag == "DRW-TEST")
    grade = model.plan.project.site.grade.meters
    assert solid.z1_m == pytest.approx(grade)
    assert (solid.z1_m - solid.z0_m) == pytest.approx(ft(4).meters)


# --- the checks ----------------------------------------------------------------------------

def test_a_gutter_that_names_a_missing_leader_fails_the_check(catlin_plan, catlin_model):
    gutter = Gutter(
        uid="TSTGT00001", tag="TR-TEST-GUTTER",
        path=(pt(ft(60), ft(10)), pt(ft(70), ft(10))), top_elevation=ft(9),
        depth=inch(5), thickness=inch(5), material="aluminum",
        downspout_ref="TR-NO-SUCH-LEADER")
    plan = _minimal_plan_with(catlin_plan, gutter, storey="main")
    model, _ = resolve(plan)
    failures = _failures(downspout_ref(_context(plan, model)))
    assert [f for f in failures if "TR-TEST-GUTTER" in f.element_tags]


def test_a_slope_note_naming_a_downspout_with_no_ref_fails(catlin_plan):
    """The exact shape of the original bug: the claim lived in prose only."""
    gutter = Gutter(
        uid="TSTGT00002", tag="TR-PROSE-GUTTER",
        path=(pt(ft(60), ft(10)), pt(ft(70), ft(10))), top_elevation=ft(9),
        depth=inch(5), thickness=inch(5), material="aluminum",
        slope="1/16 in/ft to the east downspout")
    plan = _minimal_plan_with(catlin_plan, gutter, storey="main")
    model, _ = resolve(plan)
    failures = _failures(downspout_ref(_context(plan, model)))
    assert [f for f in failures if "TR-PROSE-GUTTER" in f.element_tags]


def test_catlin_discharges_all_resolve(catlin_plan, catlin_model):
    findings = discharge_consistency(_context(catlin_plan, catlin_model))
    assert not _failures(findings), [f.message for f in _failures(findings)]


def test_a_pump_on_a_circuit_the_panel_does_not_carry_fails(catlin_plan):
    from typehaus.model.mep import SumpPump

    sump = catlin_plan.by_tag("SM-B-RADON")
    patched = sump.model_copy(update={
        "pump": SumpPump(discharge="daylight", circuit_ref="CKT-NOT-A-CIRCUIT")})
    plan = catlin_plan.with_elements(
        "basement", (patched if e is sump else e
                     for e in catlin_plan.storey_elements("basement")))
    model, _ = resolve(plan)
    failures = _failures(discharge_consistency(_context(plan, model)))
    assert [f for f in failures if "CKT-NOT-A-CIRCUIT" in f.message]
