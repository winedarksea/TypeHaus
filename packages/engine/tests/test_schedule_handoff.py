"""The handoff list, against the reference house — counts that must match their sources.

Every item here is a claim about catlin, and the value of the file is that each assertion
re-derives the number from the *other* side: the sleeve count from ``model.sleeves``, the
RO count from ``model.openings``, the hold-down count from the takeoff row it was split out
of. A handoff list that only agreed with itself would not be a check on anything.
"""

from __future__ import annotations

from typehaus.schedule.handoff import handoff_items
from typehaus.schedule.model import Visit
from typehaus.schedule.roof_penetrations import roof_penetrations


def _visit(trade, tags=()):
    return Visit(slug=f"task/{trade}/building", id="x", package=f"task/{trade}/building",
                 label="", trade=trade, storey="building", element_tags=tuple(tags))


def test_the_pour_lists_every_cast_in_sleeve(catlin_model_ro) -> None:
    items = handoff_items(catlin_model_ro, _visit("concrete"))
    sleeves = [item for item in items if item.id.startswith("sleeves:")]
    assert sum(item.count for item in sleeves) == len(catlin_model_ro.sleeves)
    assert all(item.sheet_ref == "S-100" for item in sleeves)


def test_every_sleeve_item_names_its_own_elements(catlin_model_ro) -> None:
    items = [i for i in handoff_items(catlin_model_ro, _visit("concrete"))
             if i.id.startswith("sleeves:")]
    for item in items:
        assert len(item.element_tags) == item.count


def test_the_mudsill_item_says_it_has_no_positions(catlin_model_ro) -> None:
    items = {i.id: i for i in handoff_items(catlin_model_ro, _visit("concrete"))}
    anchors = items.get("mudsill_anchors")
    assert anchors is not None and anchors.count
    assert "NOT a set of positions" in anchors.derived
    assert not anchors.element_tags


def test_the_holdown_count_matches_the_takeoff_row(catlin_model_ro) -> None:
    from typehaus.takeoff.anchors import strap_holdown_rows
    from typehaus.takeoff.hardware_config import DEFAULT_HARDWARE_TAKEOFF_CONFIG as CONFIG

    rows = strap_holdown_rows(catlin_model_ro, CONFIG.sill_plate_anchors,
                              CONFIG.sill_plate_takeoff_category)
    items = {i.id: i for i in handoff_items(catlin_model_ro, _visit("concrete"))}
    if not rows:
        assert "holdowns" not in items
        return
    assert items["holdowns"].count == rows[0]["count"]


def test_the_rough_opening_schedule_covers_every_opening(catlin_model_ro) -> None:
    items = [i for i in handoff_items(catlin_model_ro, _visit("framing"))
             if i.id.startswith("rough_openings:")]
    assert sum(item.count for item in items) == len(catlin_model_ro.openings)
    assert all("ARE the rough opening" in item.derived for item in items)


def test_the_window_order_rides_the_openings_visit(catlin_model_ro) -> None:
    items = {i.id: i for i in handoff_items(catlin_model_ro, _visit("openings"))}
    assert items["window_order"].count == len(catlin_model_ro.openings)
    assert items["window_order"].sheet_ref == "A-602"


def test_nothing_penetrates_catlins_roof_and_the_evidence_says_why(catlin_model_ro) -> None:
    found, evidence = roof_penetrations(catlin_model_ro)
    assert found == []
    assert "exits through a wall" in evidence or "no pipe, duct" in evidence
    item = [i for i in handoff_items(catlin_model_ro, _visit("roof"))
            if i.id == "roof_penetrations"]
    assert item and item[0].count == 0
    assert "stop" in item[0].label


def test_the_braced_wall_item_says_the_panels_are_not_modelled(catlin_model_ro) -> None:
    items = [i for i in handoff_items(catlin_model_ro, _visit("framing"))
             if i.id.startswith("braced_walls:")]
    assert items, "catlin has braced wall lines"
    assert all("not modelled at all" in item.derived for item in items)


def test_each_trade_only_sees_its_own_items(catlin_model_ro) -> None:
    concrete = {i.id for i in handoff_items(catlin_model_ro, _visit("concrete"))}
    openings = {i.id for i in handoff_items(catlin_model_ro, _visit("openings"))}
    assert not any(i.startswith("sleeves:") for i in openings)
    assert "window_order" not in concrete


def test_a_visits_tag_scope_narrows_its_handoff_list(catlin_model_ro) -> None:
    """Two arrivals in one trade must not hand each other the other's list."""
    every = [i for i in handoff_items(catlin_model_ro, _visit("concrete"))
             if i.id.startswith("sleeves:")]
    if len(every) < 2:
        return
    scoped = _visit("concrete", tags=every[0].scope)
    got = [i for i in handoff_items(catlin_model_ro, scoped)
           if i.id.startswith("sleeves:")]
    assert [i.id for i in got] == [every[0].id]


def test_an_unknown_trade_gets_an_empty_list(catlin_model_ro) -> None:
    assert handoff_items(catlin_model_ro, _visit("furniture")) == []
