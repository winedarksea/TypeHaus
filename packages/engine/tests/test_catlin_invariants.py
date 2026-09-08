"""Catlin's stated house facts, turned into assertions.

``houses/catlin/CLAUDE.md`` §"House facts that must stay true" is a list of invariants the
plan is *supposed* to hold, and one of them says so out loud: "The breezeway follows the
doors, and **nothing enforces that but this line**." That is exactly the failure mode this
house has already had — the mudroom conversion pushed ``D-M-ENTRY`` 4'-0" east and the
shelter stood 3'-6" off its own door for four days, until an unrelated landing check
happened to notice. A prose invariant that only a code check can catch by accident is not
enforced; this module is where those lines stop being prose.
"""

from __future__ import annotations

import pytest

FT = 0.3048
INCH = 0.0254

# The two doors the breezeway exists to connect, and the enclosure that must stay centred
# between them. `params/breezeway.py` derives its glazing from _GLAZING_CENTER_X = 8.0 ft;
# this test never reads that constant — it re-derives the answer from the doors, which is
# the whole point.
ENTRY_DOOR = "D-M-ENTRY"
SERVICE_DOOR = "D-G-SERVICE"
BREEZEWAY_GLAZING = ("GL-BW-WALL-W", "GL-BW-WALL-E")


def _opening_world_center(model, tag: str) -> tuple[float, float]:
    """A door's centre in the project frame, from its host wall's axis."""
    opening = next(o for o in model.openings if o.tag == tag)
    wall = next(w for w in model.walls if w.tag == opening.host_wall)
    (x0, y0), (x1, y1) = wall.axis
    length = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    t = opening.center_along_m / length
    return x0 + (x1 - x0) * t, y0 + (y1 - y0) * t


def _solid_x_span(model, tag: str) -> tuple[float, float]:
    solid = next(s for s in model.solids if s.tag == tag)
    xs = [p[0] for p in solid.outline]
    return min(xs), max(xs)


@pytest.mark.xfail(strict=True, reason=(
    "DELIBERATE AND OPEN since 2026-09-07. The garage was centred on the house ridge and "
    "D-G-SERVICE travelled with its wall to a centre of 10 ft; D-M-ENTRY is pinned at 8 ft "
    "by the W-M-STRW bearing tee 6 in off its jamb and could not follow. The breezeway is "
    "left untouched at _GLAZING_CENTER_X = 8.0 by owner decision - centre the garage, look "
    "at it, adjust the breezeway after. code.R311_3_exterior_landing FAILs on D-G-SERVICE "
    "for the same reason and is the finding that tracks it. STRICT on purpose: when the "
    "breezeway is re-centred this test must go green and this marker must come off in the "
    "same edit. See notes/garage_orientation_lot.md section 6.1."))
def test_breezeway_stays_centred_between_the_two_doors_it_shelters(catlin_model):
    """The invariant `houses/catlin/CLAUDE.md` says nothing enforces.

    Tolerance is 1/2", not zero: the enclosure is a literal 4'-0" of polycarbonate and the
    doors are 1'-6" apart in x, so the centre is a derived midpoint, not a snapped one.
    Half an inch is far tighter than the 3'-6" miss this is here to catch and still leaves
    room for a deliberate inch of re-centring.

    ** IT IS XFAIL TODAY, AND THE ASSERTION BELOW IS UNCHANGED ON PURPOSE. ** The doors are
    2'-0" apart in x rather than concentric, so their midpoint is x=9'-0" against the
    glazing's 8'-0". Nothing here was loosened to accommodate that — the miss is exactly the
    kind this test exists to catch, and the marker records that it is known rather than
    unnoticed.
    """
    entry_x, _ = _opening_world_center(catlin_model, ENTRY_DOOR)
    service_x, _ = _opening_world_center(catlin_model, SERVICE_DOOR)
    doors_midpoint = (entry_x + service_x) / 2.0

    spans = [_solid_x_span(catlin_model, tag) for tag in BREEZEWAY_GLAZING]
    glazing_center = (min(s[0] for s in spans) + max(s[1] for s in spans)) / 2.0

    assert glazing_center == pytest.approx(doors_midpoint, abs=0.5 * INCH), (
        f"the breezeway is centred at x={glazing_center / FT:.3f}' but "
        f"{ENTRY_DOOR}/{SERVICE_DOOR} are centred at x={doors_midpoint / FT:.3f}' — "
        f"move _GLAZING_CENTER_X in params/breezeway.py to follow the doors"
    )


def test_breezeway_is_the_briefs_literal_four_feet(catlin_model):
    """Three sheets, one cut: the 4'-0" glazed dimension is the brief, not a preference.

    Measured panel-centre to panel-centre, which is the glazing line the module authors
    (`_GLAZING_X0`/`_GLAZING_X1`); outer face to outer face is that plus one sheet
    thickness, and picking the wrong one of the two is its own small trap.

    Paired with the test above on purpose — "centred" and "4 feet wide" are one invariant
    in two halves, and satisfying either alone is how the enclosure drifted last time.
    """
    centers = []
    for tag in BREEZEWAY_GLAZING:
        lo, hi = _solid_x_span(catlin_model, tag)
        centers.append((lo + hi) / 2.0)
    assert max(centers) - min(centers) == pytest.approx(4.0 * FT, abs=0.5 * INCH)


def test_both_breezeway_doors_open_onto_the_deck_at_the_same_level(catlin_model):
    """`D-G-SERVICE` carries the same negative sill as `D-G-OVERHEAD` so both doors land
    at 0'-0" on the shared deck — the 22" step at the garage was resolved by gapping the ICF
    stem to a grade beam, and a future stem edit must not silently undo it."""
    storey_z = {s.tag: s.elevation.meters for s in catlin_model.plan.storeys}
    levels = {}
    for tag in (ENTRY_DOOR, SERVICE_DOOR):
        opening = next(o for o in catlin_model.openings if o.tag == tag)
        wall = next(w for w in catlin_model.walls if w.tag == opening.host_wall)
        levels[tag] = storey_z[wall.storey] + opening.sill_m
    assert levels[ENTRY_DOOR] == pytest.approx(levels[SERVICE_DOOR], abs=0.5 * INCH), levels


# --- the flood threshold at the sunken-garden door ----------------------------
PATIO_DOOR = "D-B-PATIO"
GARDEN_FLOOR = "SL-SG-FLOOR"
# ** THE LANDING IS THE COURT FLOOR AGAIN (2026-09-05). ** It was SL-SG-FLOOR, then
# SL-SG-STOOP for two days, and is SL-SG-FLOOR once more. The court dropped 7 1/4" on
# 2026-09-03 for a flood step, which left the threshold 14 1/2" over the floor in front of
# it — past R311.3's allowance with no landing — so a 23.7 sf block of the old flush floor
# (SL-SG-STOOP) was left standing where the door needed it. `court_step_down_in` went back
# to 0 on 2026-09-05, the whole 532 sf court is that plane again, and the stoop was retired
# as redundant. The step from the threshold has been the SAME 7 1/4" throughout all three
# arrangements — it is the curb, and the curb never moved.
PATIO_LANDING = "SL-SG-FLOOR"
# checks/code/mn_residential/egress.py::_MAX_NONREQUIRED_STEP_DOWN. Restated rather than
# imported on purpose: this test is a statement about the HOUSE, and it must fail if the
# engine's constant moves under it rather than move with it.
MAX_NONREQUIRED_STEP_DOWN_IN = 7.75


def test_the_patio_door_keeps_its_seven_inch_flood_threshold(catlin_model):
    """`D-B-PATIO` stands 7 1/4" above the basement floor, and nothing else says so.

    The sunken garden is a walled well with a drywell at the bottom and one door out of the
    basement into it. The threshold is flood resistance: a blocked outlet, a cloudburst, or a
    spring thaw ponding against the house, and it is the only thing between that and the
    finished basement. It used to be one keyword in plan/storeys/basement.py —
    `sill_height=inch(7)` — carried in a comment and asserted by nothing, so any edit that
    retyped the door or rebuilt the wall could have dropped it to the floor silently.

    Derived from the resolved model rather than read off the source: `sill_height` reads
    `inch(0)` in the plan, and the built threshold is still 7 1/4" because the door's host
    wall is the framed walkout now and its base is the top of a 7 1/4" concrete curb — the
    threshold is built rather than authored, and it is a quarter inch higher than the raw
    `inch(7)` sill would suggest because 7 1/4" is the actual width of a 2x8. Reading the
    source would call that a regression; reading the model calls it what it is.
    """
    door = next(o for o in catlin_model.openings if o.tag == PATIO_DOOR)
    wall = next(w for w in catlin_model.walls if w.tag == door.host_wall)
    floor = next(s for s in catlin_model.solids if s.tag == "SL-B-FLOOR")

    threshold = wall.z0_m + door.sill_m
    assert threshold - floor.z1_m == pytest.approx(7.25 * INCH, abs=0.05 * INCH), (
        f"{PATIO_DOOR} stands {(threshold - floor.z1_m) / INCH:.2f}\" above SL-B-FLOOR; "
        "the sunken garden's flood threshold is 7 1/4\" (plan/storeys/basement.py)"
    )


def test_the_flood_threshold_stays_under_one_riser_of_step_down(catlin_model):
    """...and the threshold cannot grow, because R311.3.1 is half an inch away.

    `code.R311_3_exterior_landing` allows a non-required exterior door 7.75" — one riser —
    down to its landing. The flood threshold IS that step. At 7 1/4" — the curb, up from a
    7" authored sill — it passes with 1/2" to spare; at 8" it FAILS, and the
    failure would read as a landing problem rather than as the threshold decision it is.
    That half inch is the whole remaining budget, and it is why the curb is one board deep
    and not two.
    This is the pin that makes raising the threshold a conscious trade rather than a
    surprise, and the reason the two live in one test file.

    **The landing is the court floor again since 2026-09-05.** SL-SG-STOOP is retired and
    `court_step_down_in` is back to 0, so the court is one 532 sf surface flush with the
    basement floor plane and this 7 1/4" curb is the ONLY riser between it and the house.

    The second assertion changed sides with it, and deliberately. It used to demand a
    further 7 1/4" riser from landing to court — the flood step — and now demands the
    opposite: that the court and the landing are the SAME plane. The flood reservoir is not
    gone, but it is now 7 1/4" deep rather than 14 1/2", and the curb is the whole dam. That
    was an owner's decision taken on a stated trade (about 3.4x -> 1.7x a 100-year 24-hour
    rain with the drywell fully failed), and this is where it is pinned: if the court ever
    drifts BELOW this plane again the step exceeds one riser and R311.3 fails, and if it
    drifts above, the dam is gone entirely.
    """
    door = next(o for o in catlin_model.openings if o.tag == PATIO_DOOR)
    wall = next(w for w in catlin_model.walls if w.tag == door.host_wall)
    landing = next(s for s in catlin_model.solids if s.tag == PATIO_LANDING)
    garden = next(s for s in catlin_model.solids if s.tag == GARDEN_FLOOR)

    step_down = (wall.z0_m + door.sill_m) - landing.z1_m
    assert 0.0 <= step_down / INCH <= MAX_NONREQUIRED_STEP_DOWN_IN, (
        f"{PATIO_DOOR} steps {step_down / INCH:.2f}\" down to {PATIO_LANDING}; "
        f"R311.3.1 allows {MAX_NONREQUIRED_STEP_DOWN_IN}\" for a door that is not the "
        "required egress door"
    )
    # And the court IS the landing: one surface, no second riser anywhere in it.
    assert (landing.z1_m - garden.z1_m) / INCH == pytest.approx(0.0, abs=0.05), (
        f"{PATIO_LANDING} stands {(landing.z1_m - garden.z1_m) / INCH:.2f}\" over "
        f"{GARDEN_FLOOR}; the court is one plane and the 7 1/4\" curb is the whole flood "
        "dam (params/sunken_garden.SPEC.court_step_down_in, back to 0 on 2026-09-05)"
    )


def test_the_landing_check_measures_the_step_the_curb_actually_makes(catlin_plan):
    """`code.R311_3_exterior_landing` must SEE the curb the test above measures.

    It did not. The check read `storey.elevation + sill_m`, but `sill_m` is stated up from
    the host wall's framing base (`ResolvedWall.base_ref_z_m`), and W-B-S3-FR stands on the
    7 1/4" garden curb (`Wall.base_elevation`). So the one door in this house with a raised
    threshold was reported as landing "0.0\" below the threshold" — flush — and the entire
    flood-threshold decision above was invisible to the check that owns R311.3.1's
    allowance. It was invisible in both directions: a court floor dropped another riser
    would still have read 0.0\". The test above pins the geometry; this one pins that the
    check can see it.
    """
    from typehaus.checks import build_context
    from typehaus.checks.code.mn_residential.egress import exterior_door_landing

    ctx, _findings = build_context(catlin_plan)
    finding = next(f for f in exterior_door_landing(ctx) if PATIO_DOOR in f.message)

    door = next(o for o in ctx.model.openings if o.tag == PATIO_DOOR)
    wall = next(w for w in ctx.model.walls if w.tag == door.host_wall)
    landing = next(s for s in ctx.model.solids if s.tag == PATIO_LANDING)
    expected = ((wall.base_ref_z_m + door.sill_m) - landing.z1_m) / INCH

    assert expected > 1.0, "the curb is the point of this test; it has gone flush"
    assert f"{expected:.1f}\"" in finding.message, finding.message


def test_the_patio_door_swings_clear_of_the_landing_it_steps_down_to(catlin_model_ro):
    """D-B-PATIO must swing IN, and it is R311.3.2 that says so — not taste.

    The curb makes this door a 7 1/4" step down to the court, which is legal only under
    R311.3.2's one-riser allowance, and that allowance is conditioned on the door not
    swinging over the landing being measured. A leaf sweeping south into the court sweeps
    over exactly that landing, which drops the limit to 1 1/2" and makes the 7 1/4" step
    illegal — so the swing and the flood threshold are one decision, not two.

    `code.R311_3_exterior_landing` tests this now, but the check can only fail the house
    after the fact; this pins the intent at the door where someone would flip it back.
    """
    door = next(o for o in catlin_model_ro.openings if o.tag == PATIO_DOOR)
    wall = next(w for w in catlin_model_ro.walls if w.tag == door.host_wall)

    assert door.swing_clearance, f"{PATIO_DOOR} resolved no leaf sweep to test"
    (sx, sy), (ex, ey) = wall.axis
    ux, uy = ex - sx, ey - sy
    run = (ux ** 2 + uy ** 2) ** 0.5
    nx, ny = -uy / run, ux / run
    side = sum((px - sx) * nx + (py - sy) * ny
               for px, py in door.swing_clearance) / len(door.swing_clearance)

    garden = next(s for s in catlin_model_ro.solids if s.tag == GARDEN_FLOOR)
    court = sum(p[1] for p in garden.outline) / len(garden.outline)
    court_side = (court - sy) * ny

    assert side * court_side < 0.0, (
        f"{PATIO_DOOR} swings toward the court it steps down into; R311.3.2's one-riser "
        "allowance needs the leaf clear of its landing (drop `flip_swing`)"
    )


# The three exterior French pairs, and the room each one lights. Every one of them is a
# DT-EXT-FRENCH60 — 5'-0" x 6'-8" = 33.33 sf of glazed fenestration (IRC R202), which
# reached no glazing number in the engine at all until 2026-09-06.
FRENCH_DOORS = {"D-B-PATIO": "RM-B-GYM", "D-M-BALC": "RM-M-LIVING",
                "D-S-DECK-E": "RM-S-STUDY2"}
FRENCH_DOOR_SF = 33.33


def test_the_french_doors_count_as_glazing_in_the_rooms_they_light(catlin_plan,
                                                                  catlin_model_ro):
    """Each exterior French pair is glazing, and lands in exactly one room's total.

    The failure this pins is silent and it lasted: ``room_windows`` skipped every door, so
    ``RM-B-GYM`` read 0.0 sf of glazing and passed R303.1 on Exception 1's electric-light
    substitute while standing behind a 33 sf glass wall onto the sunken garden.
    """
    from typehaus.resolve.room_openings import room_glazed_doors

    found = {room.tag: [d.tag for d in room_glazed_doors(catlin_plan, catlin_model_ro, room)]
             for room in catlin_model_ro.rooms}
    for door, room_tag in FRENCH_DOORS.items():
        assert found.get(room_tag) == [door], f"{door} should be {room_tag}'s glazing"
        room = next(r for r in catlin_model_ro.rooms if r.tag == room_tag)
        assert room.glazed_area_m2 * 10.7639104167 >= FRENCH_DOOR_SF
    # ...and every other room is left alone: no door is credited twice, and the two glazed
    # INTERIOR leaves (D-M-STUDY, D-S-PLANT) are borrowed light, not light to the outdoors.
    assert not [tag for tag, doors in found.items() if doors and tag not in FRENCH_DOORS.values()]


def test_the_glazed_interior_leaves_are_not_daylight(catlin_model_ro):
    """`RM-M-STUDY`'s door is glazed and its room still reads 0.0 sf — deliberately."""
    study = next(r for r in catlin_model_ro.rooms if r.tag == "RM-M-STUDY")
    assert study.glazed_area_m2 == pytest.approx(0.0)
