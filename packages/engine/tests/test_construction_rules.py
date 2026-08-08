"""ConstructionRule application pass (#45): authored returns -> geometry + BOM + overlay.

The four Catlin returns (CR-CONC-TO-FRAMED-SILL, CR-SAUNA-LINER-RETURN,
CR-FOUNDATION-FOAM-RETURN, CR-PORCH-MASONRY-RETURN) are authored on
``PlanModel.construction_rules`` and were, before this pass, consumed by nothing. These
tests assert each now emits a resolved return and a take-off row, and carries the overlay
metadata a detail recipe binds to — without touching framing members.

A return is documentation + take-off, *not* render geometry: a correctly-placed return
duplicates the mitred layer polygon its host wall already draws, so the pass emits no
``ResolvedSolid``. (It used to, and those prisms rendered as gray fins floating off the
house in 3D and as phantom concrete rectangles in every building section.)
"""

from __future__ import annotations

import pytest
from shapely.geometry import Polygon

from typehaus.takeoff import construction_returns_takeoff


_RULE_TAGS = {
    "CR-CONC-TO-FRAMED-SILL",
    "CR-SAUNA-LINER-RETURN",
    "CR-FOUNDATION-FOAM-RETURN",
    "CR-PORCH-MASONRY-RETURN",
    "CR-DECK-ON-CONCRETE-SILL",
    "CR-LIVING-CEIL-RC",
}


def test_all_authored_returns_are_emitted(catlin_model) -> None:
    """Every authored ConstructionRule produces at least one resolved return."""
    emitted = {ret.tag for ret in catlin_model.construction_returns}
    assert _RULE_TAGS <= emitted, _RULE_TAGS - emitted


def test_every_authored_predicate_has_a_finder(catlin_model) -> None:
    """A rule whose ``applies_to`` no finder answers is inert: the pass skips it, the return
    never exists, and nothing in the build says so. The registry is the contract."""
    from typehaus.resolve.construction import _FINDERS

    predicates = {rule.applies_to for rule in catlin_model.plan.library.construction_rules}
    assert predicates <= set(_FINDERS), predicates - set(_FINDERS)


def test_returns_carry_valid_quantity_geometry(catlin_model) -> None:
    """Each return has a real (positive-area, valid) plan polygon and a z extent — the
    quantity the take-off and the overlay recipe measure."""
    for ret in catlin_model.construction_returns:
        poly = Polygon(ret.outline)
        assert poly.is_valid and poly.area > 0.0, ret.tag
        assert ret.z1_m > ret.z0_m, ret.tag


def test_returns_emit_no_solids(catlin_model) -> None:
    """Regression guard: no return may reach ``model.solids``.

    A solid here duplicated geometry the host wall already draws (z-fighting in 3D) and put
    49 phantom concrete rectangles on layer S-FNDN in every section and detail sheet. Both
    the uid and the old ``return:`` category prefix are checked, so neither route comes back.
    """
    return_uids = {ret.uid for ret in catlin_model.construction_returns}
    assert return_uids  # the guard is only meaningful if returns exist at all
    assert not [s for s in catlin_model.solids if s.uid in return_uids]
    assert not [s for s in catlin_model.solids if s.category.startswith("return:")]


def test_returns_contribute_takeoff_rows(catlin_model) -> None:
    """Each return's take-off category bills a BOM row with a positive count and length."""
    rows = construction_returns_takeoff(catlin_model)
    categories = {row["category"] for row in rows}
    assert {"pt-sill-plate", "sauna-liner-return", "foundation-foam-return",
            "masonry-corner-return", "resilient-channel"} <= categories, categories
    for row in rows:
        assert row["count"] >= 1
        assert row["length_ft"] > 0.0
    # Rows reconcile 1:1 with the resolved returns.
    assert sum(row["count"] for row in rows) == len(catlin_model.construction_returns)


def test_sill_plate_is_pt_bearing_and_carries_overlay_metadata(catlin_model) -> None:
    """The concrete-to-framed sill is a PT bearing plate landing on the concrete top, with
    the lap/sealant/element-tag data an overlay recipe needs."""
    sills = [r for r in catlin_model.construction_returns
             if r.tag == "CR-CONC-TO-FRAMED-SILL"]
    assert sills
    for sill in sills:
        assert sill.kind == "bearing_plate"
        assert sill.material_ref == "spf"
        assert sill.lap_m > 0.0
        assert sill.sealant is not None
        assert len(sill.element_tags) >= 2  # the concrete wall + the framed wall
        assert sill.condition_key and sill.condition_key.startswith("wall_foundation:")


def test_sauna_liner_return_declares_air_vapor_continuity(catlin_model) -> None:
    """The sauna hot-side liner return carries the vapour/air continuity claim (it is the
    control layer that must wrap onto the concrete, not merely butt)."""
    liners = [r for r in catlin_model.construction_returns
              if r.tag == "CR-SAUNA-LINER-RETURN"]
    assert liners
    assert all(r.air_vapor_continuity and r.returning_layer == "foil-polyiso"
               for r in liners)


def test_foundation_foam_return_is_thermal(catlin_model) -> None:
    """The exterior foundation foam return maintains thermal continuity around the corner."""
    foam = [r for r in catlin_model.construction_returns
            if r.tag == "CR-FOUNDATION-FOAM-RETURN"]
    assert foam
    assert all(r.thermal_continuity for r in foam)
    assert all(r.material_ref in ("xps", "icf-eps") for r in foam)


# --- floor system landing on a concrete wall ----------------------------------
# The sill under a *deck* is the same physical return one element down: the porch's PT 2x8
# joists land on the 16" arched front wall, and a flat-laid PT 2x4 on that wall's 3.5"
# bearing ledge is what they land on. A flat plate is not something a Beam can express, so
# it is a construction return like the framed-wall sill above.
#
# The rule is authored on the house (houses/catlin/plan/assemblies.py CR-DECK-ON-CONCRETE-SILL),
# so this reads the real model rather than injecting the rule into a copy of the library.
_FLOOR_SILL_TAG = "CR-DECK-ON-CONCRETE-SILL"


def test_a_deck_bearing_on_concrete_bills_a_flat_sill_plate(catlin_model) -> None:
    """FS-SG-PORCH names W-SG-ARCH in its ``joists.bearing_refs``, so the rule finds it."""
    sills = [r for r in catlin_model.construction_returns if r.tag == _FLOOR_SILL_TAG]
    assert len(sills) == 1
    sill = sills[0]
    assert sill.kind == "bearing_plate"
    assert sill.material_ref == "spf"
    assert set(sill.element_tags) == {"W-SG-ARCH", "FS-SG-PORCH"}
    assert sill.condition_key.startswith("floor_foundation:")
    # Laid flat: the 3.5" face bears, the 1.5" dimension is the build-up.
    assert sill.thickness_m == pytest.approx(3.5 * 0.0254)
    assert sill.lap_m == pytest.approx(1.5 * 0.0254)
    # The bearing run is the wall clipped to the deck it carries — 19' of plate, not the
    # 20' the wall's axis runs between side-wall axes.
    assert sill.length_m == pytest.approx(19 * 0.3048)
    # Top at the joist soffit (one 2x8 depth below the 0' porch datum), not on the wall top.
    assert sill.z1_m == pytest.approx(-7.25 * 0.0254)
    assert sill.z0_m == pytest.approx(sill.z1_m - sill.lap_m)
    # It sits on the wall's north (deck-side) 3.5" ledge, not down the middle of the pier.
    assert max(y for _, y in sill.outline) == pytest.approx(-8.8333 * 0.3048, abs=1e-3)


def test_the_deck_sill_bills_as_pt_sill_plate(catlin_model) -> None:
    rows = [row for row in construction_returns_takeoff(catlin_model)
            if row["category"] == "pt-sill-plate"]
    assert rows
    assert sum(row["length_ft"] for row in rows) > 19.0  # the wall sills plus the deck's


# --- resilient channel under a ceiling ----------------------------------------
# The living room's ceiling gypsum hangs on channel instead of straight off FS-SECOND's
# I-joists, so footfall from the bedrooms above does not arrive as impact noise. It is the
# one return billed from an *area*: the runs cross the joists at 16" o.c., so the total run
# is the ceiling field over that spacing (the same derivation radiant-wire length uses).
# The rule is scoped to RM-M-LIVING — the rest of that deck's ceiling is screwed direct.
_RC_TAG = "CR-LIVING-CEIL-RC"
_RC_SPACING_M = 16 * 0.0254


def _rc(model):
    rcs = [r for r in model.construction_returns if r.tag == _RC_TAG]
    assert len(rcs) == 1, rcs
    return rcs[0]


def _living_room(model):
    return next(r for r in model.rooms if r.tag == "RM-M-LIVING")


def _stair_hole(model) -> Polygon:
    opening = next(element for element in model.plan.all_elements()
                   if getattr(element, "tag", None) == "FO-S-STAIR")
    return Polygon([point.xy_m for point in opening.outline])


def test_the_ceiling_channel_is_scoped_to_one_room(catlin_model) -> None:
    """FS-SECOND decks the whole storey; the channel covers one room of it. The field is
    the room's clear face itself — the same polygon the rooms stage publishes, re-derived
    here because this pass runs long before that stage fills ``model.rooms``."""
    rc = _rc(catlin_model)
    assert rc.kind == "furring"
    assert rc.takeoff_category == "resilient-channel"
    assert set(rc.element_tags) == {"FS-SECOND", "RM-M-LIVING"}
    assert rc.returning_layer == "gwb"  # the membrane it carries, authored on the deck
    assert Polygon(rc.outline).area == pytest.approx(_living_room(catlin_model).area_m2)
    # A field, not a junction lap: there is no boundary condition for an overlay to join on.
    assert rc.condition_key is None


def test_the_ceiling_channel_leaves_the_stair_well_out(catlin_model) -> None:
    """No ceiling hangs under FO-S-STAIR, so no channel is ordered for it — ~70 sqft of
    RM-M-LIVING, 9% of the room and 9% of the channel. The well falls *inside* the room, so
    it is a hole: it comes off the billed quantity, which the outline ring cannot show."""
    rc = _rc(catlin_model)
    room = Polygon(_living_room(catlin_model).clear_face)
    hole = _stair_hole(catlin_model)
    assert hole.intersection(room).area > 5.0  # the guard only bites if they overlap
    assert rc.length_m * _RC_SPACING_M == pytest.approx(room.difference(hole).area)
    assert rc.length_m < Polygon(rc.outline).area / _RC_SPACING_M


def test_the_ceiling_channel_length_is_its_field_over_the_spacing(catlin_model) -> None:
    """Runs cross the joists at the authored o.c., so the lineal quantity is area/spacing —
    ~525 LF for a 700 sqft ceiling at 16"."""
    rc = _rc(catlin_model)
    assert rc.lap_m == pytest.approx(_RC_SPACING_M)
    room = Polygon(_living_room(catlin_model).clear_face)
    field = room.difference(_stair_hole(catlin_model))
    assert rc.length_m == pytest.approx(field.area / _RC_SPACING_M)
    assert rc.length_m / 0.3048 == pytest.approx(524.0, abs=2.0)


def test_the_ceiling_channel_hangs_below_the_joist_soffit(catlin_model) -> None:
    """Under the deck, not in it: the 1/2" band tops out at the joist soffit, one 11-7/8"
    I-joist below the second-storey datum, which is where the gypsum then starts."""
    rc = _rc(catlin_model)
    assert rc.z1_m == pytest.approx(10 * 0.3048 - 11.875 * 0.0254)
    assert rc.z0_m == pytest.approx(rc.z1_m - 0.5 * 0.0254)
    assert rc.thickness_m == pytest.approx(0.5 * 0.0254)


def test_the_ceiling_channel_bills_lineal_feet_of_steel(catlin_model) -> None:
    """It is steel by the foot, not gypsum by the sheet — its own BOM row, beside (not
    inside) the ``sheet_goods`` row FS-SECOND's ``ceiling_below`` bills."""
    rows = [row for row in construction_returns_takeoff(catlin_model)
            if row["category"] == "resilient-channel"]
    assert len(rows) == 1
    assert rows[0]["material"] == "galv-steel"
    assert rows[0]["count"] == 1
    assert rows[0]["length_ft"] == pytest.approx(_rc(catlin_model).length_m / 0.3048, abs=0.1)


def test_a_ceiling_channel_rule_naming_no_room_is_inert(catlin_model) -> None:
    """A stale ``scope_ref`` (a room renamed out from under the rule) must emit nothing —
    not crash, and above all not silently fall back to billing the whole deck."""
    from typehaus.model.assembly import ConstructionRule
    from typehaus.quantities import inch
    from typehaus.resolve.construction import _find_ceiling_channel

    rule = ConstructionRule(tag="CR-STALE", applies_to="floor:ceiling_channel",
                            kind="furring", dimension=inch(16),
                            takeoff_category="resilient-channel",
                            scope_ref="RM-M-NO-SUCH-ROOM")
    assert list(_find_ceiling_channel(catlin_model, rule)) == []


def test_an_unscoped_ceiling_channel_rule_needs_an_authored_deck_outline(catlin_model) -> None:
    """Documented limitation: an unscoped rule bills the deck's own ``outline``, and the
    pass runs before the framing stage that would otherwise derive one. FS-SECOND authors
    no outline, so an unscoped rule finds nothing here — scope it, or author the outline."""
    from typehaus.model.assembly import ConstructionRule
    from typehaus.quantities import inch
    from typehaus.resolve.construction import _find_ceiling_channel

    rule = ConstructionRule(tag="CR-WHOLE-DECK", applies_to="floor:ceiling_channel",
                            kind="furring", dimension=inch(16),
                            takeoff_category="resilient-channel")
    assert list(_find_ceiling_channel(catlin_model, rule)) == []
