"""The wall-only exception for a non-walkable pocket beside a stair well."""

from __future__ import annotations

from types import SimpleNamespace

from typehaus.findings import Result
from typehaus.model.floors import FloorOpeningEdgeInterval, FloorOpeningPocketClosure
from typehaus.quantities import inch, pt
from typehaus.resolve.floor_opening_pockets import (
    pocket_closure_intervals,
    resolve_floor_opening_pockets,
)


def _closure(*, opening_ref="FO-STAIR"):
    return FloorOpeningPocketClosure(
        uid="PC00000001",
        tag="PC-STAIR",
        opening_ref=opening_ref,
        edge_interval=FloorOpeningEdgeInterval(edge="north", start=inch(0), end=inch(48)),
        wall_refs=("W-RETURN-W", "W-REAR", "W-RETURN-E"),
        pocket_outline=(pt(inch(0), inch(0)), pt(inch(48), inch(0)), pt(inch(48), inch(12))),
        source="Study bookcase pocket is enclosed by the rear partition and both returns.",
    )


def test_invalid_opening_never_resolves_into_guard_credit():
    closure = _closure(opening_ref="NO-SUCH-OPENING")
    plan = SimpleNamespace(elements={"attic": (closure,)}, all_elements=lambda: iter((closure,)))
    model = SimpleNamespace(floors=[], walls=[], floor_opening_pocket_closures=[])

    findings = resolve_floor_opening_pockets(plan, model)

    assert [finding.result for finding in findings] == [Result.FAIL]
    assert "not a FloorOpening" in findings[0].message
    assert model.floor_opening_pocket_closures == []


def test_only_resolved_wall_pockets_offer_an_edge_interval():
    model = SimpleNamespace(
        floor_opening_pocket_closures=(
            SimpleNamespace(
                opening_ref="FO-STAIR", edge="north", start_m=0.2, end_m=1.6, tag="PC-STAIR"
            ),
        )
    )

    assert pocket_closure_intervals(model, "FO-STAIR", "north", 1.0) == ((0.2, 1.0, "PC-STAIR"),)
    assert pocket_closure_intervals(model, "FO-STAIR", "south", 1.0) == ()


def test_pocket_closure_is_a_registered_dialect_constructor():
    from typehaus.model.registry import constructor_names

    assert "FloorOpeningPocketClosure" in constructor_names()
