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

#: The shaft's CLEAR extent, measured off the resolved wall layers rather than off a room
#: polygon — ``resolve/rooms.py`` insets only by the lining and these walls are
#: ``face("sheathing-ext")``, so a room-polygon reading counts 6" of exterior stud as shaft.
#: x 0'-6 5/8"..2'-6 5/8" by y 33'-3 1/4"..35'-5 3/8": 24" wide by 26 1/8" deep.
_SHAFT_X = (6.625, 30.625)
_SHAFT_Y = (399.25, 425.375)


def test_every_riser_stands_INSIDE_the_chase_with_its_whole_envelope(catlin_model) -> None:
    """Replaced on 2026-09-15, because the test this supersedes never tested the chase.

    It asserted ``min(xs) < 3.0 and max(ys) > 33.0`` — "some vertex of this run is west of
    3 ft and some vertex is north of 33 ft". That is satisfied by anything that touches the
    north-west corner of the house, it says nothing about the 24" shaft, and it passed
    throughout the period when ``DU-ERV-RISER-SUP`` stood **4 5/8" outside the shaft's west
    face, in an exterior stud cavity**, and when ``DU-S-ERV-HP-FEED`` and
    ``DU-ERV-RISER-EXH`` shared 4" of plan on 2" centres.

    What is asserted now is the thing that has to be true to build it: every riser's whole
    ENVELOPE — centreline plus radius, not the centreline — lies inside the measured clear
    extent, and no two of them overlap in plan unless they are the same air path meeting at
    a joint.

    ** THE SET IS THREE, NOT FOUR, SINCE 2026-09-15. ** ``DU-ERV-OA`` left this shaft when
    its hood moved to the north wall. It runs main -> basement only and never needed a
    continuous basement-to-attic route; it was in the shaft solely because its hood was on the
    WEST facade with the shaft in between. Its riser now stands in the open closet at
    x=3'-4", which is what let it go to 8" — an 8" envelope overran the shaft's east face.
    ``test_the_intake_riser_is_out_of_the_chase_and_in_the_closet`` below pins that.
    """
    risers = {d.tag: d for d in catlin_model.ducts
              if d.tag in ("DU-ERV-RISER-SUP", "DU-ERV-RISER-EXH", "DU-ERV-EA")}
    assert len(risers) == 3

    bands: dict[str, tuple[float, float, float, float]] = {}
    for tag, duct in risers.items():
        radius = duct.diameter_m / M_PER_IN / 2.0
        assert duct.insulation, tag  # outdoor-temperature air through conditioned space
        for index in range(len(duct.path) - 1):
            a, b = duct.path[index], duct.path[index + 1]
            if abs(a[0] - b[0]) > 1e-9 or abs(a[1] - b[1]) > 1e-9:
                continue  # not the vertical segment
            x, y = a[0] / M_PER_IN, a[1] / M_PER_IN
            if not (_SHAFT_Y[0] - 8 < y < _SHAFT_Y[1] + 8):
                continue  # a vertical leg somewhere else in the house
            lo, hi = x - radius, x + radius
            assert _SHAFT_X[0] - 1e-6 <= lo and hi <= _SHAFT_X[1] + 1e-6, (
                f"{tag} spans x {lo:.3f}..{hi:.3f}, outside the shaft's "
                f"{_SHAFT_X[0]}..{_SHAFT_X[1]}")
            assert _SHAFT_Y[0] - 1e-6 <= y - radius and y + radius <= _SHAFT_Y[1] + 1e-6, tag
            bands[tag] = (lo, hi, y - radius, y + radius)
            break
    assert set(bands) == set(risers), sorted(set(risers) - set(bands))

    # No two risers share plan, unless they are the same air path meeting at a joint.
    # DU-S-ERV-HP-FEED comes OFF DU-ERV-RISER-SUP's head and is not in this set.
    for one_tag, (x0, x1, y0, y1) in bands.items():
        for other_tag, (u0, u1, v0, v1) in bands.items():
            if one_tag >= other_tag:
                continue
            assert not (x0 < u1 and x1 > u0 and y0 < v1 and y1 > v0), (
                f"{one_tag} and {other_tag} overlap in plan")


#: RM-M-MECH's clear, read off the resolved wall LAYERS the same way ``_SHAFT_X`` is:
#: x 0'-0 5/8"..5'-11 3/8" by y 33'-6 3/8"..35'-5 3/8".
_CLOSET_X = (0.625, 71.375)


def test_the_intake_riser_is_out_of_the_chase_and_in_the_closet(catlin_model) -> None:
    """``DU-ERV-OA``'s riser is in RM-M-MECH, EAST of the shaft, and that is what bought 8".

    Three separate things have to hold and each was measured:

    * its envelope is wholly outside ``_SHAFT_X`` — otherwise it is back in the four-in-a-
      shaft problem that no ordering of risers packs out of;
    * its envelope is wholly inside the closet's own clear, so it is not in a wall cavity —
      the defect ``DU-ERV-RISER-SUP`` carried for months;
    * it is 8". At 6" this assertion would still pass and the static budget would be 0.10 in.
      worse, so the diameter is pinned here too rather than only in the sizes test.
    """
    oa = next(d for d in catlin_model.ducts if d.tag == "DU-ERV-OA")
    assert oa.diameter_m == pytest.approx(8 * M_PER_IN)
    radius = oa.diameter_m / M_PER_IN / 2.0

    verticals = [a for a, b in zip(oa.path, oa.path[1:])
                 if abs(a[0] - b[0]) < 1e-9 and abs(a[1] - b[1]) < 1e-9]
    # Two: the storey drop at x=3'-4" and the short fall onto the machine's port at x=3'-8".
    assert len(verticals) == 2, [v[0] / M_PER_IN for v in verticals]
    for vertex in verticals:
        x = vertex[0] / M_PER_IN
        lo, hi = x - radius, x + radius
        assert lo > _SHAFT_X[1], f"DU-ERV-OA spans x {lo:.3f}..{hi:.3f}, back inside the shaft"
        assert _CLOSET_X[0] <= lo and hi <= _CLOSET_X[1], (
            f"DU-ERV-OA spans x {lo:.3f}..{hi:.3f}, outside RM-M-MECH's "
            f"{_CLOSET_X[0]}..{_CLOSET_X[1]}")


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
    stacked at one corner, EXHAUST ABOVE INTAKE. Two independent things want that order. An
    exhaust plume rises, so an intake under it is the safe one. And IRC M1506.3 waives the
    10 ft separation entirely "where the exhaust opening is located not less than 3 feet above
    the air intake opening" — the engine does not implement that exception, and this pair does
    not need it (12'-0" of rise clears the 10 ft on 3-D distance alone, 12'-2" between the two
    boxes), but the ORDER is what the code blesses and reversing it would be wrong on both
    counts.

    ** THEY MOVED OFF THE WEST FACADE TO THE NORTH WALL ON 2026-09-15. ** Off the west wall
    each run had to sweep the NW chase to reach its hood, and the two sweeps carried twelve
    measured interpenetrations between them. Out the north wall each leaves at its own
    station. The intake rose +4'-0" -> +5'-0" at the same time, and that foot is NEC 110.26:
    ``ED-M-HP3-DISC`` is on this wall and its working space runs to the top of the can at
    +4'-3 1/2", so a 12" hood box centred on +4'-0" sat inside it.

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
    assert intake_z == pytest.approx(5.0, abs=0.01)
    assert exhaust_z == pytest.approx(17.0, abs=0.01)
    assert exhaust_z - intake_z >= 3.0, "IRC M1506.3 wants the exhaust >= 3 ft over the intake"
    # NEC 110.26 over ED-M-HP3-DISC: the can is 9 1/2" tall on a +3'-6" base, so its working
    # space tops at +4'-3 1/2" and a 12" box has to start above that.
    assert intake_z - 0.5 >= 4.0 + 3.5 / 12.0, "the intake box is inside the disconnect's space"

    for tag, hood in hoods.items():
        x, y = (v / _FT for v in hood.position.xy_m)
        # The NORTH wall, not the west facade and not the north gable: y is outboard of the
        # cladding at 36'-7 1/4", x is inside the house's width. A negative x on either of
        # these is the old west-facade station; a y near 36'-0" is the stud-cavity bug.
        assert y == pytest.approx(445.25 / 12.0, abs=0.01), tag
        assert 0.0 < x < 6.0, f"{tag} must stand on W-M-N3B / W-S-N3B, which end at x=6'-0\""


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


# --- the 2026-09-12 standard-parts redesign (plans/buildability.md BLD-08) -----------------

def test_every_radial_is_four_inch_galvanized_and_there_are_twenty_three(catlin_model) -> None:
    """The whole BLD-08 distribution decision, in one assertion.

    The 75 mm semi-rigid tube had three US sellers and no Minnesota dealer, so it is gone;
    the home-run TOPOLOGY is untouched. 4" and not 3" is a CATALOGUE decision — 3" pipe and
    collars are stocked, 3" dampers and grilles are not.
    """
    radials = [d for d in catlin_model.ducts
               if d.tag.startswith(("DU-B-ERV-R-", "DU-M-ERV-R-", "DU-A-ERV-R-"))]
    assert len(radials) == 23, sorted(d.tag for d in radials)
    for duct in radials:
        assert duct.diameter_m == pytest.approx(4 * M_PER_IN), duct.tag
        assert duct.material == "galvanized", duct.tag


def test_every_trunk_riser_and_outdoor_leg_is_galvanized_at_its_stated_size(catlin_model) -> None:
    """Six inches everywhere except BOTH outdoor legs, which are eight as of 2026-09-15.

    Broan's manual asks for an 8" trunk above 200 cfm with long runs, and
    ``notes/erv_static_budget.md`` §7 priced that upsize as a fallback for months rather than
    building it. Both halves were bought in one day and for different reasons:

    * ``DU-ERV-EA`` first, because drawing the attic extract feed honestly — the riser had
      been reading as connected only because its head sat within the 3" joint tolerance of a
      bath radial — put 0.056 in. w.g. back on the extract column and took the delivered
      figure to 202 cfm, BELOW MN 1322 R403.5's 205. The term falls 0.1666 -> 0.0437.
    * ``DU-ERV-OA`` second, and it had been blocked on geometry rather than money: at its old
      chase station an 8" envelope overran the shaft's east face by an inch. Moving its hood
      to the north wall took the riser out of the chase entirely and the block with it. The
      term falls 0.1318 -> 0.0315, which is the single largest saving in the note.

    Area goes as d² while friction goes as V², which is why a 6" -> 8" step takes roughly
    three quarters off a term even against a slightly higher friction factor.
    """
    by_tag = {d.tag: d for d in catlin_model.ducts}
    for tag in ("DU-ERV-RISER-SUP", "DU-ERV-RISER-EXH", "DU-B-ERV-SUP-TRUNK",
                "DU-B-ERV-RET-TRUNK", "DU-S-ERV-HP-FEED"):
        assert by_tag[tag].diameter_m == pytest.approx(6 * M_PER_IN), tag
        assert by_tag[tag].material == "galvanized", tag
    for tag in ("DU-ERV-OA", "DU-ERV-EA"):
        assert by_tag[tag].diameter_m == pytest.approx(8 * M_PER_IN), tag
        assert by_tag[tag].material == "galvanized", tag


def test_no_run_in_the_house_is_semi_rigid_any_more(catlin_model) -> None:
    """``DUCT-T-SEMIRIGID-4`` stays in the catalog for the first run that needs a flexible
    leg through a truss web, and for ``notes/erv_static_budget.md`` §6's comparison — but
    nothing names it today, and a stray one would price and resist differently."""
    assert [d.tag for d in catlin_model.ducts if d.material == "semi_rigid"] == []


def test_every_plenum_states_its_port_count_and_its_port_size(catlin_plan) -> None:
    """``duct_ports`` is what turns ``plan/mep_erv_l2.py``'s "full at 10 of 10" from prose into
    a verdict. ``port_diameter`` is what keeps the 6" trunk collar out of the census."""
    types = {t.tag: t for t in catlin_plan.library.equipment_types}
    for tag, ports in (("EQ-T-ERV-MANIFOLD-6", 6), ("EQ-T-ERV-MANIFOLD-6-EXH", 6),
                       ("EQ-T-ERV-MANIFOLD-10", 10)):
        assert types[tag].duct_ports == ports, tag
        assert types[tag].port_diameter.meters == pytest.approx(4 * M_PER_IN), tag
        assert types[tag].static_loss_pa_at_cfm, tag
    # A hood is a one-port fitting and says so — it carries DUCT_MANIFOLD only because the
    # enum has no HOOD kind, and a second duct landing on one would be a real defect.
    for tag in ("EQ-T-ERV-HOOD-6", "EQ-T-ERV-HOOD-6-EXH"):
        assert types[tag].duct_ports == 1, tag
        assert types[tag].port_diameter.meters == pytest.approx(6 * M_PER_IN), tag


def test_the_port_census_is_clean_and_the_level_two_extract_is_full(catlin_model) -> None:
    """``EQ-M-ERV-MAN-EXH`` at 10 of 10 is the claim every "where could a new terminal go"
    argument in ``plan/mep_erv_l2.py`` leans on. It is graded now, and it BLOCKS."""
    from typehaus.checks.mep.erv_manifold_ports import erv_manifold_ports

    findings = erv_manifold_ports(check_context(model=catlin_model))
    assert [f.message for f in findings if f.result is Result.FAIL] == []
    full = next(f for f in findings if "EQ-M-ERV-MAN-EXH" in f.message)
    assert "10 of 10 x 4\" ports used, full" in full.message


def test_the_duct_product_catalog_is_keyed_like_the_price_rows(catlin_plan) -> None:
    """``DuctProductType`` joins on (material, nominal diameter) — the same pair
    ``prices.toml``'s ``[ducts]`` qualifies on — so a run that prices as 4" galvanized cannot
    resist as something else."""
    rows = {(r.material, round(r.nominal_diameter.meters / M_PER_IN, 1)): r
            for r in catlin_plan.library.duct_product_types}
    assert ("galvanized", 4.0) in rows
    assert ("galvanized", 6.0) in rows
    # The physics is the engine's; these coefficients are ASHRAE reads the house owns.
    assert rows[("galvanized", 4.0)].roughness_m == pytest.approx(0.0000914)
    assert rows[("galvanized", 4.0)].bend_equivalent_length.meters == pytest.approx(30 * M_PER_IN)
    # Flex is three times the roughness and is named by no run — kept so the note's
    # rigid-versus-flex comparison reads off typed data.
    assert rows[("flex", 6.0)].roughness_m > 10 * rows[("galvanized", 6.0)].roughness_m
