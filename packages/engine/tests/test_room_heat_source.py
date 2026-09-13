"""``mep.room_heat_source`` against its hand-worked oracle.

``houses/catlin/notes/room_heat_loss_baths.md`` is the independent pass: Schluter's own
delivered-output relation, the two rooms' geometry, and the comparison against each room's
design load, worked before the check was encoded. The numbers below are read off that note.

The subject is narrow and deliberately so: a conditioned room whose ONLY heat is a radiant
floor. A room the ducted system or a head reaches belongs to ``mep.heating_capacity``, and a
room heated through a doorway is not something this model can see at all.
"""

from __future__ import annotations

import pytest
from _helpers import CATLIN, check_context

from typehaus.checks.mep.room_heat import room_heat_source
from typehaus.findings import Result

#: Note §2. Schluter publishes delivered output as Q = 8.92 * dT^1.1 W/m2. At the
#: recommended 84 F floor over a 72 F room, dT = 12 F = 6.667 C.
_DELIVERED_BTUH_PER_FT2 = 22.8
_W_TO_BTUH = 3.412141633


def _preferences():
    """The HOUSE's own preferences, not ``Preferences()``.

    The default carries no blower-door ach50, so ``estimate_block_load`` omits the
    infiltration term and names it in ``unknown_inputs`` — which this check correctly
    reports as UNKNOWN and which would mask every arithmetic assertion below. Catlin
    authors one; the oracle is worked against the real house.
    """
    from typehaus.checks.run import load_preferences

    return load_preferences(CATLIN)


def _findings(model_or_plan, *, plan=False):
    ctx = (check_context(plan=model_or_plan, preferences=_preferences()) if plan
           else check_context(model=model_or_plan, preferences=_preferences()))
    return room_heat_source(ctx)


def _by_room(model, *, plan=False):
    return {f.element_tags[0] if f.element_tags else f.message.split(":")[0].strip(): f
            for f in _findings(model, plan=plan)}


# --- 1. the arithmetic, by hand -----------------------------------------------------------

def test_schluters_relation_gives_22_8_at_the_design_point_and_18_6_at_the_example() -> None:
    """Note §2, and this is the whole correction BLD-08 asked for.

    18.6 Btu/h/ft2 is Schluter's **82 F example**, which this house quoted in two files as if
    it were the design point; BLD-08's own "25 to 30" is a guess at the other end. Both fall
    out of the same published relation read at different stations.
    """
    def delivered(floor_f: float, operative_f: float) -> float:
        delta_c = (floor_f - operative_f) * 5.0 / 9.0
        return 8.92 * delta_c ** 1.1 * _W_TO_BTUH / 10.7639

    assert delivered(84.0, 72.0) == pytest.approx(22.8, abs=0.05)
    assert delivered(82.0, 72.0) == pytest.approx(18.6, abs=0.15)


def test_the_delivered_figure_is_capped_by_both_area_and_wattage() -> None:
    """Note §2: ``min(heated area x 22.8, nameplate watts x 3.412)``.

    The floor cannot deliver more than the cable draws, and cannot deliver the cable's whole
    draw over more floor than is heated. In BOTH of Catlin's rooms the AREA term binds, which
    is the finding of §4: a bigger cable buys nothing.
    """
    # FH-M-BATH2: 17.52 ft2 polygon, DHEHK12016 at 203 W.
    assert min(17.52 * _DELIVERED_BTUH_PER_FT2, 203 * _W_TO_BTUH) == pytest.approx(399, abs=1)
    assert pytest.approx(693, abs=1) == 203 * _W_TO_BTUH, \
        "the cable draws more than it delivers"
    # FH-S-BATH1: 27.31 ft2, DHEHK12027 at 338 W.
    assert min(27.31 * _DELIVERED_BTUH_PER_FT2, 338 * _W_TO_BTUH) == pytest.approx(623, abs=1)


def test_covering_bath2s_load_would_need_area_the_room_does_not_have() -> None:
    """Note §4. 673 Btu/h at 22.8 wants 29.5 ft2 of heated floor in a 74.4 ft2 room whose
    vanity, water closet, shower pan and tub deck take the difference."""
    assert pytest.approx(29.5, abs=0.2) == 673.0 / _DELIVERED_BTUH_PER_FT2


# --- 2. the live house ---------------------------------------------------------------------

def test_both_bath_zones_state_the_corrected_delivered_output(catlin_plan) -> None:
    from typehaus.model.floors import FloorHeat

    zones = {e.tag: e for e in catlin_plan.all_elements()
             if isinstance(e, FloorHeat)}
    assert zones["FH-M-BATH2"].delivered_btuh_per_ft2 == pytest.approx(22.8)
    assert zones["FH-S-BATH1"].delivered_btuh_per_ft2 == pytest.approx(22.8)
    # The dining zone is supplemental in a room with a head in it, so what it DELIVERS is
    # not the question — the zone's margin is. Never defaulted.
    assert zones["FH-M-DINING"].delivered_btuh_per_ft2 is None


def test_bath1_carries_its_room_and_bath2_does_not(catlin_model_ro) -> None:
    """Note §4's table: 623 against 591 (PASS), and 399 against 673 (41% short)."""
    rows = _by_room(catlin_model_ro)
    assert rows["RM-S-BATH1"].result is Result.PASS
    assert "delivers 623 Btu/h against a 591 Btu/h design load" in rows["RM-S-BATH1"].message

    bath2 = rows["RM-M-BATH2"]
    assert "delivers 399 Btu/h against a 673 Btu/h design load" in bath2.message
    assert "274 Btu/h (41%) short" in bath2.message


def test_the_shortfall_is_unknown_because_a_room_scoped_load_is_approximate(
        catlin_model_ro) -> None:
    """Note §5. Envelope area is attributed by plan overlap, air-side terms by share of
    conditioned volume, and there are no room-level internal gains — all of which over-state
    a small interior bathroom on continuous extract. Turning that into a FAIL would turn an
    approximation into a verdict."""
    bath2 = _by_room(catlin_model_ro)["RM-M-BATH2"]
    assert bath2.result is Result.UNKNOWN
    assert "approximate by design" in bath2.message


def test_a_bathroom_carries_no_code_ref_and_says_why(catlin_model_ro) -> None:
    """R202 defines habitable space and its very next sentence excludes bathrooms and toilet
    rooms, so R303.10 does not reach either of these rooms. Citing it would be wrong; saying
    nothing would leave a reader assuming it was checked."""
    for tag in ("RM-M-BATH2", "RM-S-BATH1"):
        finding = _by_room(catlin_model_ro)[tag]
        assert finding.code_ref is None, tag
        assert "R202 excludes a bathroom" in finding.message, tag


def test_a_room_the_system_reaches_passes_without_any_temperature_arithmetic(
        catlin_model_ro) -> None:
    """``RM-M-LIVING`` has ``FH-M-DINING`` in it AND ``EQ-M-HP2-LIVING`` hanging on its wall.
    The delivered output of a modulating inverter head is not a model fact — it depends on
    the supply temperature it happens to be running at — so the honest statement is that the
    room is served, and the sizing question is the zone's."""
    living = _by_room(catlin_model_ro)["RM-M-LIVING"]
    assert living.result is Result.PASS
    assert "mep.heating_capacity" in living.message


def test_catlin_reports_no_fail_from_this_check(catlin_model_ro) -> None:
    findings = _findings(catlin_model_ro)
    assert [f.message for f in findings if f.result is Result.FAIL] == []
    assert len(findings) == 3, "three radiant zones, three findings"


# --- 3. the FAIL and UNKNOWN branches, synthetically ----------------------------------------

def _retype_zone(plan, tag, **update):
    """``plan`` with one ``FloorHeat`` element's fields replaced."""
    from typehaus.model.floors import FloorHeat

    elements = {
        storey: tuple(e.model_copy(update=update)
                      if isinstance(e, FloorHeat) and e.tag == tag else e
                      for e in group)
        for storey, group in plan.elements.items()}
    return plan.model_copy(update={"elements": elements})


def test_halving_the_delivered_output_widens_the_shortfall(catlin_plan) -> None:
    """The plan's synthetic FAIL fixture. Catlin is held to 0 FAIL, so the branch that
    reports a materially worse room is demonstrated on a mutated copy — and the verdict is
    still UNKNOWN, because the same approximation argument holds however wide the gap."""
    plan = _retype_zone(catlin_plan, "FH-S-BATH1", delivered_btuh_per_ft2=11.4)
    rows = _by_room(plan, plan=True)
    assert rows["RM-S-BATH1"].result is Result.UNKNOWN
    assert "311 Btu/h" in rows["RM-S-BATH1"].message


def test_a_zone_that_delivers_nothing_at_all_is_the_fail_branch(catlin_plan) -> None:
    """The one case that needs no load and no approximation: the room's sole heat source
    makes no heat. Not a thin margin — an unheated room."""
    plan = _retype_zone(catlin_plan, "FH-S-BATH1",
                        delivered_btuh_per_ft2=0.0, watts=0.0)
    finding = _by_room(plan, plan=True)["RM-S-BATH1"]
    assert finding.result is Result.FAIL
    assert "delivers nothing" in finding.message


def test_a_zone_with_no_delivered_output_is_unknown_not_zero(catlin_plan) -> None:
    """What a heated floor DELIVERS is not derivable from what its cable DRAWS, so an
    unstated output is a gap. Never a zero: a mat nobody characterised is not a mat that
    makes no heat."""
    plan = _retype_zone(catlin_plan, "FH-S-BATH1", delivered_btuh_per_ft2=None)
    finding = _by_room(plan, plan=True)["RM-S-BATH1"]
    assert finding.result is Result.UNKNOWN
    assert "states no delivered_btuh_per_ft2" in finding.message


def test_a_plan_with_no_radiant_zone_earns_not_applicable(catlin_plan) -> None:
    """N/A from positive evidence — every conditioned room walked, not one carries a zone —
    never an empty list."""
    from typehaus.model.floors import FloorHeat

    elements = {storey: tuple(e for e in group if not isinstance(e, FloorHeat))
                for storey, group in catlin_plan.elements.items()}
    plan = catlin_plan.model_copy(update={"elements": elements})
    findings = _findings(plan, plan=True)
    assert [f.result for f in findings] == [Result.NOT_APPLICABLE]


def test_a_load_resting_on_unstated_inputs_is_unknown(catlin_model_ro) -> None:
    """The default ``Preferences()`` carries no blower-door result, so the block load omits
    its infiltration term and says so. A verdict resting on a load that is missing a term is
    UNKNOWN, not a pass on the terms that happened to resolve."""
    from typehaus.checks.registry import Preferences

    rows = {f.element_tags[0] if f.element_tags else "": f
            for f in room_heat_source(check_context(model=catlin_model_ro,
                                                    preferences=Preferences()))}
    bath1 = rows["RM-S-BATH1"]
    assert bath1.result is Result.UNKNOWN
    assert "ach50" in bath1.message
