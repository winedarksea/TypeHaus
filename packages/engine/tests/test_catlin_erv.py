"""The Catlin ERV as a system: the terminal set, the risers, the outdoor side.

The 2026-08-25 pass replaced a *furnace*-shaped ventilator — nine rectangular trunks, a
placeholder machine, no outdoor side at all — with a Broan B210E75RT on a semi-rigid radial
install. These are the facts that pass had to establish and that a later edit must not
quietly undo.
"""

from __future__ import annotations

import pytest

from _helpers import check_context

from typehaus.checks.mep.erv_terminals import erv_outdoor_terminals
from typehaus.findings import Result
from typehaus.model.enums import DuctSystem
from typehaus.quantities import M_PER_IN

_FT = 0.3048


# --- the machine -------------------------------------------------------------------------

def test_the_erv_is_the_broan_and_carries_the_cold_recovery_figure(catlin_plan) -> None:
    """SRE 0.65, not 0.75 and not 0.81. This is a -15 F design house, so the -13 F certified
    figure is the honest one for the block load — a *worse* number on purpose, and the
    ventilation term moved with it."""
    types = {t.tag: t for t in catlin_plan.library.equipment_types}
    assert "EQ-T-ERV" not in types, "the placeholder type must not come back"
    broan = types["EQ-T-BROAN-B210E75RT"]
    assert broan.sensible_recovery_effectiveness == pytest.approx(0.65)
    assert broan.ventilation_cfm == pytest.approx(210)
    assert broan.product_ref == "PROD-BROAN-B210E75RT"
    assert "TODO" not in (broan.source or "")


def test_the_erv_has_four_ports_including_the_outdoor_pair(catlin_plan) -> None:
    """An ERV with no intake and no discharge is not modeled, and until ``Service`` learned
    OUTDOOR_AIR/EXHAUST_AIR it could not be — plan/electrical.py said so in a comment."""
    from typehaus.model.enums import Service

    broan = next(t for t in catlin_plan.library.equipment_types
                 if t.tag == "EQ-T-BROAN-B210E75RT")
    services = {p.service for p in broan.ports}
    assert {Service.SUPPLY_AIR, Service.RETURN_AIR,
            Service.OUTDOOR_AIR, Service.EXHAUST_AIR} <= services


def test_the_erv_names_a_condensate_drain(catlin_plan) -> None:
    """A cold-climate core makes water. It had nowhere to put it."""
    erv = next(e for e in catlin_plan.all_elements() if e.tag == "EQ-B-ERV")
    assert erv.pan_drain_ref == "PR-B-ERV-COND"
    assert erv.uid == "CEE016AAAA", "the uid is the IFC GlobalId and must survive a retype"


# --- the terminal set ----------------------------------------------------------------------

def test_the_two_deleted_terminals_stay_deleted(catlin_plan) -> None:
    """REG-S-RET2 (the suite extract) and DU-M-ERV-RET (the last rectangular trunk). The
    suite keeps its System 1 supply — that is a conditioned-air terminal, untouched — and
    RM-S-SUITEBATH's REG-S-EXH3 carries the room through the door undercut."""
    tags = {e.tag for e in catlin_plan.all_elements()}
    assert "REG-S-RET2" not in tags
    assert "REG-S-HP-SUITE" in tags


def test_every_rectangular_erv_trunk_is_gone(catlin_plan) -> None:
    tags = {e.tag for e in catlin_plan.all_elements()}
    retired = {"DU-M-ERV-RET", "DU-M1-ERV-SUP", "DU-M1-ERV-RET", "DU-B-ERV-SUP",
               "DU-B-ERV-RET", "DU-B-ERV-BATH", "DU-B-SAUNA-SUP", "DU-S-BATH1-EXH",
               "DU-A-ERV-RET", "DU-S-PLANT-EXH"}
    assert not (retired & tags), sorted(retired & tags)


def test_the_play_rooms_fresh_supply_survives_and_moved(catlin_plan) -> None:
    """Deleting REG-B-SUP2 is a hard ``code.R303_1_light_and_ventilation`` FAIL: RM-B-PLAY-N
    is 324 sf of windowless MEDIA space legal only under R303.1 Exception 1, whose second
    half requires a fresh-air supply *to that room*. It was re-sited, not dropped — the play
    room's whole ceiling is SL-M-DECK's solid concrete, so every foot of that run is
    surface-mounted and the west edge is eight feet cheaper than (27', 27')."""
    reg = next(e for e in catlin_plan.all_elements() if e.tag == "REG-B-SUP2")
    x, y = reg.position.xy_m
    assert x / _FT == pytest.approx(19.0, abs=0.01)
    assert y / _FT == pytest.approx(26.0, abs=0.01)
    assert reg.duct_ref == "DU-B-ERV-R-PLAY"


def test_the_workshop_terminal_is_a_bench_hood_at_bench_height(catlin_plan) -> None:
    """A 7" diffuser at 8'-0" does not capture solder fume, it dilutes it into the room and
    then extracts the dilution. 5'-6" is 24" over the 34" bench tops."""
    reg = next(e for e in catlin_plan.all_elements() if e.tag == "REG-B-RET1")
    assert reg.type_ref == "REG-T-ERV-BENCH-HOOD"
    assert reg.mount.elevation.meters / _FT == pytest.approx(5.5, abs=0.01)
    assert reg.kind is DuctSystem.RETURN  # light fumes, heat worth recovering, not a booth


def test_every_ventilation_terminal_states_a_design_cfm(catlin_plan) -> None:
    """``code.R303_3_local_exhaust`` reads this off each bath terminal, and UNKNOWN is not a
    pass there. A transfer louver is the one exception: it moves air on pressure difference
    alone and is balanced to nothing."""
    missing = [e.tag for e in catlin_plan.all_elements()
               if e.element_kind == "Register"
               and e.kind not in (DuctSystem.TRANSFER,)
               and e.duct_ref is not None
               and e.duct_ref.startswith(("DU-B-ERV-", "DU-M-ERV-", "DU-A-ERV-"))
               and e.design_cfm is None]
    assert not missing, missing


# --- the risers and the outdoor side -------------------------------------------------------

def test_all_four_risers_share_the_one_chase(catlin_model) -> None:
    """The radon/plumbing chase at (1', 34'-6") is the house's only continuous
    basement-to-attic shaft, and the four ERV risers are measured into it rather than
    assumed into it — see the arithmetic in plan/mep_erv.py."""
    risers = {d.tag: d for d in catlin_model.ducts
              if d.tag in ("DU-ERV-RISER-SUP", "DU-ERV-RISER-EXH", "DU-ERV-OA", "DU-ERV-EA")}
    assert len(risers) == 4
    for tag, duct in risers.items():
        xs = [x / _FT for x, _ in duct.path]
        ys = [y / _FT for _, y in duct.path]
        assert min(xs) < 3.0, tag  # every one passes through the chase's west end
        assert max(ys) > 33.0, tag
        assert duct.diameter_m / M_PER_IN == pytest.approx(6.0), tag
        # Both legs of the outdoor pair carry outdoor-temperature air through conditioned
        # space; an uninsulated one sweats all winter.
        assert duct.insulation, tag


def test_the_outdoor_pair_is_vapour_sealed_and_the_distribution_pair_is_not(catlin_model) -> None:
    by_tag = {d.tag: d for d in catlin_model.ducts}
    assert "vapour-sealed" in by_tag["DU-ERV-OA"].insulation
    assert "vapour-sealed" in by_tag["DU-ERV-EA"].insulation
    assert "vapour-sealed" not in by_tag["DU-ERV-RISER-SUP"].insulation


def test_the_intake_is_its_own_duct_system(catlin_model) -> None:
    """Filed as SUPPLY it would be counted as conditioned air delivered to a room by every
    ventilation check in the house."""
    oa = [d for d in catlin_model.ducts if d.system == DuctSystem.OUTDOOR_AIR.value]
    assert [d.tag for d in oa] == ["DU-ERV-OA"]


def test_the_hoods_clear_the_code_separations(catlin_plan, catlin_model) -> None:
    """IRC M1602.2 / ASHRAE 62.2 §6.8 want 10 ft intake-to-exhaust, 3 ft from a plumbing vent
    or a dryer, and enough height to clear drifted snow. RM-M-MECH is 5'-11" x 2'-7", so no
    pair of hoods near the shaft can make the ten feet; the north gable can."""
    findings = erv_outdoor_terminals(check_context(catlin_plan, catlin_model))
    assert findings
    assert not [f for f in findings if f.result is not Result.PASS], \
        [f.message for f in findings if f.result is not Result.PASS]


def test_the_hoods_are_mirrored_about_the_ridge(catlin_plan) -> None:
    """A gable reads symmetric about x=18'-0" before it answers to anything below it — the
    facade rule in houses/catlin/CLAUDE.md, and nothing but this test enforces it for the
    two hoods."""
    hoods = {e.tag: e.position.xy_m[0] / _FT for e in catlin_plan.all_elements()
             if e.tag in ("EQ-A-ERV-HOOD-OA", "EQ-A-ERV-HOOD-EA")}
    assert len(hoods) == 2
    assert sum(hoods.values()) == pytest.approx(36.0, abs=0.01)


# --- the mixing box --------------------------------------------------------------------

def test_the_mixing_box_is_in_the_soffit_and_north_of_the_strip_heater(catlin_model) -> None:
    """The plan wanted it directly behind REG-S-HP-RET at (20'-8", 9'-8"). It does not go
    there: reading south to north, SF-S-DUCT's cavity is the air handler's case to 9'-7" and
    the strip heater's plate to 10'-8". `mep.duct_soffit_occupancy` is what decided this,
    which is the whole reason the check was built before the ERV was authored."""
    box = next(o for o in catlin_model.canvas_objects if o.tag == "EQ-S-ERV-MIX")
    strip = next(o for o in catlin_model.canvas_objects if o.tag == "EQ-S-HP1-STRIP")
    assert min(y for _, y in box.footprint) >= max(y for _, y in strip.footprint)


def test_the_fresh_feed_drops_into_the_soffit(catlin_model) -> None:
    """The last of plans/TODO.md's three undrawn verticals. It used to tap a joist-bay trunk
    that no longer exists, and its rise was undrawn because ``DuctRun`` had no elevation."""
    feed = next(d for d in catlin_model.ducts if d.tag == "DU-S-ERV-HP-FEED")
    assert feed.uid == "CSDV02AAAA"
    # Two drawn drops, 24 7/8" in total: the attic deck down into the FS-ATTIC bay, and the
    # bay down through the second-storey ceiling onto EQ-S-ERV-MIX inside SF-S-DUCT.
    fall_in = (max(feed.z_m) - min(feed.z_m)) / M_PER_IN
    assert fall_in == pytest.approx(24.875, abs=0.01)
