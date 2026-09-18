"""Phase 8: the routing space as four classes, each naming the action it implies.

What is pinned here is the vocabulary and its honesty — that green is *derived* rather than
asserted, that a relaxation never recolours anything, and that the picture and the printout
read the same classification. The geometry underneath is ``obstacles``', already covered.
"""

from __future__ import annotations

import pytest

from typehaus.routing.cost import RouteCost
from typehaus.routing.obstacles import HardPrism, SoftPrism
from typehaus.routing.space import RoutingSpace
from typehaus.routing.space_view import (
    CLASS_GRAY,
    CLASS_GREEN,
    CLASS_ORANGE,
    CLASS_RED,
    clear_at,
    regions_at,
    space_view,
    summary,
)


def _space(hard=(), soft=()) -> RoutingSpace:
    return RoutingSpace(radius_m=0.05, clearance_m=0.0, cost=RouteCost(), hard=list(hard),
                        soft=list(soft), corridors=[], bbox=(0.0, 0.0, 10.0, 10.0),
                        storeys=("basement",))


def _hard(tag: str, kind: str, bounds=(1.0, 1.0, 2.0, 2.0), z=(0.0, 1.0)) -> HardPrism:
    from shapely.geometry import box

    return HardPrism(tag=tag, kind=kind, footprint=box(*bounds), z0_m=z[0], z1_m=z[1])


def test_the_class_is_read_off_the_kind_and_never_off_the_tag() -> None:
    """A tag is a name somebody chose; a kind is what the resolver built.

    The mapping is ``diagnostics.mobility_of`` — the same one the refusals use. A view that
    classified a lane differently from the refusal about that lane would be worse than none.
    """
    space = _space(hard=[
        _hard("PR-LOOKS-LIKE-A-RUN", "concrete"),
        _hard("W-LOOKS-LIKE-A-WALL", "run", bounds=(3.0, 3.0, 4.0, 4.0)),
        _hard("X-AVOIDED", "avoid", bounds=(5.0, 5.0, 6.0, 6.0)),
    ])
    by_tag = {r.tag: r.klass for r in regions_at(space, 0.5)}
    assert by_tag["PR-LOOKS-LIKE-A-RUN"] == CLASS_RED
    assert by_tag["W-LOOKS-LIKE-A-WALL"] == CLASS_ORANGE
    assert by_tag["X-AVOIDED"] == CLASS_GRAY


def test_the_callers_own_avoid_is_gray_and_not_red() -> None:
    """"You told me not to" and "it is concrete" are not the same answer."""
    region = regions_at(_space(hard=[_hard("X", "avoid")]), 0.5)[0]
    assert region.klass == CLASS_GRAY
    assert "--avoid the caller named" in region.action


def test_every_class_names_an_action_rather_than_a_verdict() -> None:
    space = _space(hard=[_hard("A", "concrete"), _hard("B", "run", (3.0, 3.0, 4.0, 4.0)),
                         _hard("C", "avoid", (5.0, 5.0, 6.0, 6.0))])
    regions = regions_at(space, 0.5)
    for region in regions:
        assert region.action and "blocked" not in region.action.lower()
    assert any("haus route --run B" in r.action for r in regions)


def test_nothing_from_another_level_is_projected_onto_this_one() -> None:
    """A region drawn where the obstacle is not is the error the per-level lattice fixed."""
    space = _space(hard=[_hard("HIGH", "concrete", z=(3.0, 4.0))])
    assert regions_at(space, 0.5) == []
    assert [r.tag for r in regions_at(space, 3.5)] == ["HIGH"]


def test_a_run_is_one_region_and_not_one_per_leg() -> None:
    """A reader asked what is in the way wants to be told "this duct" once."""
    space = _space(hard=[_hard("DU-A", "run", (1.0, 1.0, 2.0, 2.0)),
                         _hard("DU-A", "run", (2.0, 1.0, 3.0, 2.0)),
                         _hard("DU-A", "run", (3.0, 1.0, 4.0, 2.0))])
    regions = regions_at(space, 0.5)
    assert len(regions) == 1
    assert regions[0].footprint.area == pytest.approx(3.0)


def test_green_is_what_is_left_and_cannot_claim_a_taken_lane() -> None:
    """Derived by subtraction, which is the whole of its honesty."""
    space = _space(hard=[_hard("A", "concrete", (0.0, 0.0, 10.0, 5.0))])
    regions = regions_at(space, 0.5)
    green = clear_at(space, 0.5, regions)
    assert green is not None
    assert green.klass == CLASS_GREEN
    # The bbox is 100 m2 and half of it is taken.
    assert green.footprint.area == pytest.approx(50.0, abs=1e-6)


def test_a_level_with_no_room_at_all_reports_no_green_rather_than_an_empty_one() -> None:
    space = _space(hard=[_hard("A", "concrete", (0.0, 0.0, 10.0, 10.0))])
    assert clear_at(space, 0.5, regions_at(space, 0.5)) is None


def test_a_movable_blocker_stays_orange_and_the_space_under_it_is_not_recoloured() -> None:
    """Diagnostic relaxation never turns an unresolved collision green.

    A counterfactual prices what lifting a run would open; this draws the run as orange with
    the lift named, and leaves the space exactly as it is. Drawing the relaxed world would
    be drawing a house nobody has.
    """
    space = _space(hard=[_hard("PR-A", "run", (0.0, 0.0, 10.0, 5.0))])
    regions = regions_at(space, 0.5)
    assert regions[0].klass == CLASS_ORANGE
    assert "neither is a claim that it may move" in regions[0].action
    green = clear_at(space, 0.5, regions)
    assert green is not None and green.footprint.area == pytest.approx(50.0, abs=1e-6)


def test_a_priced_region_is_orange_because_it_is_a_price_and_not_a_refusal() -> None:
    from shapely.geometry import box

    space = _space(soft=[SoftPrism(tag="RM-KITCH", kind="room", footprint=box(1, 1, 2, 2),
                                   z0_m=0.0, z1_m=1.0, occupancy="finished")])
    region = regions_at(space, 0.5)[0]
    assert region.klass == CLASS_ORANGE
    assert "priced, not prohibited" in region.action


def test_the_summary_counts_what_the_regions_say_and_the_payload_round_trips() -> None:
    space = _space(hard=[_hard("A", "concrete"), _hard("B", "run", (3.0, 3.0, 4.0, 4.0))])
    regions = space_view(space, [0.5])
    counts = summary(regions)["by_class"]
    assert counts[CLASS_RED]["count"] == 1
    assert counts[CLASS_ORANGE]["count"] == 1
    assert counts[CLASS_GREEN]["count"] == 1
    payload = regions[0].payload()
    assert payload["class"] == CLASS_RED
    assert payload["geometry"]["type"] in {"Polygon", "MultiPolygon"}


# --- the drawing -------------------------------------------------------------------------

def test_the_overlay_lands_in_the_shared_review_layer_stack() -> None:
    """One vocabulary: the Z-ROUT layers collapse into the ``routing`` review group."""
    from typehaus.emit.draw.review_layers import ROUTING, layer_for
    from typehaus.emit.draw.routing_overlay import LAYER_BY_CLASS, review_group

    assert review_group() == ROUTING
    for layer in LAYER_BY_CLASS.values():
        assert layer_for(layer) == ROUTING


def test_every_class_the_view_produces_has_a_drawing_for_it() -> None:
    """A class with no layer is silently skipped by ``overlay_nodes`` — so there must be
    none. Two vocabularies of four words is one place for them to drift."""
    from typehaus.emit.draw.routing_overlay import LAYER_BY_CLASS, PATTERN_BY_CLASS

    classes = {CLASS_GREEN, CLASS_ORANGE, CLASS_RED, CLASS_GRAY}
    assert set(LAYER_BY_CLASS) == classes
    assert set(PATTERN_BY_CLASS) == classes


def test_the_overlay_svg_groups_by_class_under_one_routing_group() -> None:
    from typehaus.emit.draw.routing_overlay import overlay_svg

    space = _space(hard=[_hard("A", "concrete"), _hard("B", "run", (3.0, 3.0, 4.0, 4.0))])
    body = overlay_svg(space_view(space, [0.5]), space.bbox, level_m=0.5)
    assert '<g id="routing">' in body
    assert '<g id="Z-ROUT-BLOK"' in body
    assert "<title>A</title>" in body
    # Green is written first so it paints underneath the refusals.
    assert body.index("Z-ROUT-CLER") < body.index("Z-ROUT-BLOK")


def test_emit_does_not_reach_for_the_routing_package() -> None:
    """The leaf rule, asserted at the one place it would be tempting to break.

    A drawing that could run a search would be a drawing whose content moved when a cost
    weight moved. The regions are a parameter; the CLI hands them over.
    """
    import pathlib

    source = (pathlib.Path(__file__).resolve().parents[1] / "src" / "typehaus" / "emit"
              / "draw" / "routing_overlay.py").read_text()
    assert "typehaus.routing" not in source
