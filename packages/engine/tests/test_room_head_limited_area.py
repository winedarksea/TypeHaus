"""A room a roof rakes into reports two areas, and the second one is the honest one.

``ResolvedRoom.area_m2`` is the floor: what gets sheathed, finished and heated. Under a
6:12 attic roof that is not the same fact as "how big is this room" — catlin's storage
pocket is 134 sf of deck with 5'-3" of head at its very best point, and every dashboard,
plan label and digest used to call the whole of it usable space.
"""

from typehaus.resolve.roof_geometry import (
    MIN_COUNTABLE_HEAD_M,
    roof_headroom_areas,
    roof_headroom_region,
)
from typehaus.server.space_summary import build_space_summary

SF_PER_M2 = 10.7639


def _room(model, tag):
    return next(r for r in model.rooms if r.tag == tag)


def test_flat_ceilinged_rooms_lose_nothing(catlin_model_ro):
    """Every room not under a rake keeps its full floor area — this is not a global haircut."""
    for room in catlin_model_ro.rooms:
        if room.storey == "attic":
            continue
        assert room.head_limited_area_m2 == room.area_m2, room.tag


def test_attic_pocket_is_not_134_square_feet(catlin_model_ro):
    """RM-A-POCKET: 134 sf of floor, and essentially none of it stand-up space.

    The roof underside runs from 3" over the deck at the west wall to 5'-3" at the room's
    east edge, so only a sliver of it clears 5'-0". The number that matters is that this is
    a rounding error against 134, not that it is exactly 6.
    """
    pocket = _room(catlin_model_ro, "RM-A-POCKET")
    assert pocket.area_m2 * SF_PER_M2 == __import__("pytest").approx(134.2, abs=0.5)
    assert pocket.head_limited_area_m2 * SF_PER_M2 < 10.0


def test_habitable_attic_rooms_are_head_limited_too(catlin_model_ro):
    """The studio and the study lose the rake as well — under half of each has 5'-0"."""
    for tag in ("RM-A-STUDIO", "RM-A-STUDY", "RM-A-EAST-UNFIN"):
        room = _room(catlin_model_ro, tag)
        assert 0.35 < room.head_limited_area_m2 / room.area_m2 < 0.55, tag
    # The stub bath sits close enough to the ridge to clear 5'-0" everywhere.
    bath = _room(catlin_model_ro, "RM-A-STUBATH")
    assert bath.head_limited_area_m2 == bath.area_m2


def test_head_is_measured_to_the_underside_not_the_deck(catlin_model_ro):
    """The rafter depth is taken off, so the reported area is the smaller, honest one.

    ``roof_headroom_areas`` grades against the roof PLANE — the deck top — which is what
    ``code.R305_ceiling_height`` still does and reads generous by a rafter depth. The room
    area must not inherit that generosity.
    """
    model = catlin_model_ro
    pocket = _room(model, "RM-A-POCKET")
    roof = next(r for r in model.roofs if r.tag == "RF-HOUSE")
    attic = next(s for s in model.plan.storeys if s.tag == "attic")
    _, to_deck = roof_headroom_areas(
        pocket.clear_face, roof, attic.elevation.meters, MIN_COUNTABLE_HEAD_M)
    assert to_deck > pocket.head_limited_area_m2


def test_summary_reconciles_usable_and_low_head(catlin_model_ro):
    """``usable_sf + low_head_sf`` is the modeled floor, and conditioned_sf keeps all of it."""
    summary = build_space_summary(catlin_model_ro)
    attic = next(row for row in summary["storeys"] if row["storey"] == "attic")
    assert attic["low_head_sf"] > 600.0
    assert round(attic["usable_sf"] + attic["low_head_sf"], 0) == round(
        attic["conditioned_sf"], 0)


def test_headroom_region_is_all_or_nothing_at_the_extremes(catlin_model_ro):
    """A threshold below the eave qualifies everywhere; one over the ridge qualifies nowhere."""
    roof = next(r for r in catlin_model_ro.roofs if r.tag == "RF-HOUSE")
    base = roof.eave_z_m
    assert not roof_headroom_region(roof, base, -1.0).is_empty
    assert roof_headroom_region(roof, base, roof.ridge_z_m - base + 1.0).is_empty
