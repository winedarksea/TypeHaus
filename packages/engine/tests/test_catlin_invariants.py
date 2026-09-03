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
# between them. `params/breezeway.py` derives its glazing from _GLAZING_CENTER_X = 7.25 ft;
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


def test_breezeway_stays_centred_between_the_two_doors_it_shelters(catlin_model):
    """The invariant `houses/catlin/CLAUDE.md` says nothing enforces.

    Tolerance is 1/2", not zero: the enclosure is a literal 4'-0" of polycarbonate and the
    doors are 1'-6" apart in x, so the centre is a derived midpoint, not a snapped one.
    Half an inch is far tighter than the 3'-6" miss this is here to catch and still leaves
    room for a deliberate inch of re-centring.
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
    down to its landing. The garden floor outside this door is flush with the basement slab
    and is the landing, so the flood threshold IS that step. At 7 1/4" — the curb, up from a
    7" authored sill — it passes with 1/2" to spare; at 8" it FAILS, and the
    failure would read as a landing problem rather than as the threshold decision it is.
    That half inch is the whole remaining budget, and it is why the curb is one board deep
    and not two.
    This is the pin that makes raising the threshold a conscious trade rather than a
    surprise, and the reason the two live in one test file.
    """
    door = next(o for o in catlin_model.openings if o.tag == PATIO_DOOR)
    wall = next(w for w in catlin_model.walls if w.tag == door.host_wall)
    garden = next(s for s in catlin_model.solids if s.tag == GARDEN_FLOOR)

    step_down = (wall.z0_m + door.sill_m) - garden.z1_m
    assert 0.0 <= step_down / INCH <= MAX_NONREQUIRED_STEP_DOWN_IN, (
        f"{PATIO_DOOR} steps {step_down / INCH:.2f}\" down to {GARDEN_FLOOR}; "
        f"R311.3.1 allows {MAX_NONREQUIRED_STEP_DOWN_IN}\" for a door that is not the "
        "required egress door"
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
    garden = next(s for s in ctx.model.solids if s.tag == GARDEN_FLOOR)
    expected = ((wall.base_ref_z_m + door.sill_m) - garden.z1_m) / INCH

    assert expected > 1.0, "the curb is the point of this test; it has gone flush"
    assert f"{expected:.1f}\"" in finding.message, finding.message
