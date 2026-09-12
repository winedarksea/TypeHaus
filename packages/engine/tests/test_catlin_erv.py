"""The Catlin ERV as a system: the terminal set, the risers, the outdoor side.

This pass replaced a *furnace*-shaped ventilator — nine rectangular trunks, a
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
    or a dryer, and enough height to clear drifted snow.

    The pair makes it at the NW chase by VERTICAL separation. ``erv_outdoor_terminals``
    measures a 3-D distance."""
    findings = erv_outdoor_terminals(check_context(catlin_plan, catlin_model))
    assert findings
    assert not [f for f in findings if f.result is not Result.PASS], \
        [f.message for f in findings if f.result is not Result.PASS]


def test_the_hoods_are_stacked_with_the_discharge_on_top(catlin_plan) -> None:
    """The rule that governs the pair, replacing the north-gable mirror.

    This test used to assert ``x(OA) + x(EA) == 36.0`` — the gable's mirror about the ridge.
    The hoods left the gable because ``DU-ERV-EA``'s horizontal leg ran through the rough
    openings of both gable windows; the mirror was a facade rule, not a code rule, and it
    does not apply to a pair that is no longer on a gable.

    What replaces it is the arrangement that makes the pair legal without ten feet of facade:
    both on the west wall at the NW chase, EXHAUST ABOVE INTAKE. Two independent things want
    that order. An exhaust plume rises, so an intake under it is the safe one. And IRC M1506.3
    waives the 10 ft separation entirely "where the exhaust opening is located not less than
    3 feet above the air intake opening" — the engine does not implement that exception, and
    this pair does not need it (13'-0" of rise clears the 10 ft on 3-D distance alone), but
    the ORDER is what the code blesses and reversing it would be wrong on both counts.

    Both must also stay south of ``TR-RF-LEADER-W``, the roof leader on this facade at
    y=35'-6", and clear of the second-storey chase notch's +19'-0" cap.

    ** THE x IT PINS MOVED ON 2026-09-11, AND THE OLD VALUE WAS THE BUG. ** It used to
    require x = +0'-6" "at the wall". +6" is the middle of the stud cavity: W-M-W1B and
    W-S-W1B resolve their outdoor face at x = -0'-7 1/4" (PBR-26 cladding over an outer
    girt, a vent gap and 4" of foam), so both hoods stood a foot INSIDE the house and this
    test held them there. ``Equipment.footprint`` is a plan rectangle centred on
    ``position``, so a 12" hood box with its back plate flat on the cladding centres at
    -7 1/4" - 6" = **-1'-1 1/4"**. That is the number pinned now, and it is pinned as a
    NEGATIVE — a positive x on either of these is the gable/cavity regression this test
    exists to catch.
    """
    hoods = {e.tag: e for e in catlin_plan.all_elements()
             if e.tag in ("EQ-M-ERV-HOOD-OA", "EQ-S-ERV-HOOD-EA")}
    assert set(hoods) == {"EQ-M-ERV-HOOD-OA", "EQ-S-ERV-HOOD-EA"}

    # Storey-relative mounts on datums 0'-0" and +10'-0": +4'-0" and +17'-0" absolute.
    intake_z = hoods["EQ-M-ERV-HOOD-OA"].mount.elevation.meters / _FT
    exhaust_z = 10.0 + hoods["EQ-S-ERV-HOOD-EA"].mount.elevation.meters / _FT
    assert intake_z == pytest.approx(4.0, abs=0.01)
    assert exhaust_z == pytest.approx(17.0, abs=0.01)
    assert exhaust_z - intake_z >= 3.0, "IRC M1506.3 wants the exhaust >= 3 ft over the intake"

    for tag, hood in hoods.items():
        x, y = (v / _FT for v in hood.position.xy_m)
        # The west facade at the chase, not the north gable: x is at the wall, y is in the
        # chase band. If either drifts back onto the gable this reads it immediately.
        assert x == pytest.approx(-13.25 / 12.0, abs=0.01), tag
        assert 33.0 < y < 35.5, f"{tag} must stay south of the roof leader at y=35'-6\""


# --- the mixing box --------------------------------------------------------------------

def test_the_mixing_box_is_upstream_of_the_coil_and_the_strip_heater(catlin_model) -> None:
    """** THIS TEST ONCE ASSERTED THE DEFECT, AND THE REVERSAL IS THE POINT. **

    It used to require the mixing box NORTH of the strip heater, because that is where
    `mep.duct_soffit_occupancy` had pushed it: reading south to north, SF-S-DUCT's cavity
    was the air handler's case to 9'-7", the return grille at 9'-8", the strip heater's
    plate to 10'-8", and the box at 11'-4". That is a packing outcome, and packing is not
    an airflow argument — it put 100 cfm of -15 F design outdoor air, half the house's
    fresh air, DOWNSTREAM of both the coil and the 2 kW strip heater, where it reaches the
    rooms untempered.

    ** AND THE GEOMETRY INVERTED AGAIN ON 2026-09-04, WITHOUT THE ORDER CHANGING. ** The
    machine moved to the north end of the storey and the trunk now runs SOUTH, so the
    cabinet's discharge is its south face and the strip heater sits south of it, where it
    used to sit north. The mixing box — a full return PLENUM since later the same day, and
    REG-S-HP-RET opens into its underside — is south of the cabinet too. Both are, and that
    is the point: on this side of the machine the return and the supply run SIDE BY SIDE in
    two lanes, not one behind the other, so "which is upstream" is no longer a question
    about y at all.

    What still has to hold, and is asserted here:

    * both the plenum and the strip are wholly SOUTH of the cabinet — the plenum because it
      feeds the return face, the strip because it sits in the discharge;
    * they are in DIFFERENT LANES across the box, with the hanger gap between them. If they
      ever shared a lane, return air and 4.6 kW of supply-side heat would be in one duct,
      and `mep.duct_soffit_occupancy` would say so — but only because of this separation,
      which is a siting decision rather than a check's doing."""
    box = next(o for o in catlin_model.canvas_objects if o.tag == "EQ-S-ERV-MIX")
    handler = next(o for o in catlin_model.canvas_objects if o.tag == "EQ-S-HP1-AH")
    strip = next(o for o in catlin_model.canvas_objects if o.tag == "EQ-S-HP1-STRIP")
    # The strip's north edge is flush ON the cabinet's discharge face, so this pair is
    # tangent to the micrometre and compares with a tolerance rather than exactly.
    tol = 1e-9
    assert max(y for _, y in box.footprint) <= min(y for _, y in handler.footprint) + tol
    assert max(y for _, y in strip.footprint) <= min(y for _, y in handler.footprint) + tol
    # Side by side, and clear of one another: the plenum takes the east lane, the strip the
    # centre, with more than the 2" hanger gap between them.
    box_west = min(x for x, _ in box.footprint)
    strip_east = max(x for x, _ in strip.footprint)
    assert box_west > strip_east
    assert (box_west - strip_east) / M_PER_IN > 2.0

    # And the room-air inlet is INSIDE the plenum, which is the whole 2026-09-04 fix: the
    # grille used to lap the plenum, the return duct and 120 in2 of bare soffit cavity at
    # once, and a return drawing part of its face out of a framed cavity is IMC 601.5's
    # building-cavity-as-plenum. Nothing in this engine grades that, so it is pinned here.
    grille = next(o for o in catlin_model.canvas_objects if o.tag == "REG-S-HP-RET")
    for axis in (0, 1):
        assert min(p[axis] for p in grille.footprint) >= min(p[axis] for p in box.footprint) - tol
        assert max(p[axis] for p in grille.footprint) <= max(p[axis] for p in box.footprint) + tol
    # And it is in the box the machine is in, not the trunk's.
    plan_refs = {el.tag: getattr(el, "soffit_ref", None)
                 for el in catlin_model.plan.all_elements()}
    assert plan_refs["EQ-S-ERV-MIX"] == "SF-S-HP1"


def test_the_fresh_feed_drops_into_the_soffit(catlin_model) -> None:
    """The last of plans/TODO.md's three undrawn verticals. It used to tap a joist-bay trunk
    that no longer exists, and its rise was undrawn because ``DuctRun`` had no elevation."""
    feed = next(d for d in catlin_model.ducts if d.tag == "DU-S-ERV-HP-FEED")
    assert feed.uid == "CSDV02AAAA"
    # Two drawn drops, 28 7/8" in total: the attic deck down into the FS-ATTIC bay, and the
    # bay down through the second-storey ceiling onto EQ-S-ERV-MIX inside SF-S-HP1.
    # The second drop is 21" for the FLEXX Ultra cabinet, whose cavity floor came down with
    # it. The tail sits 6" above that floor, which is the invariant; the fall is the
    # consequence.
    fall_in = (max(feed.z_m) - min(feed.z_m)) / M_PER_IN
    assert fall_in == pytest.approx(28.875, abs=0.01)
