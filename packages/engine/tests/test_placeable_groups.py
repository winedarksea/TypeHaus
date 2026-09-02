"""Furniture groups: a table's chairs occupy its clearance, an unrelated object encroaches.

``ClearanceZone.occupant_types`` is the only authored input — the group itself is recovered
from geometry (→ resolve/placeable_groups), so a house source file never has to spell out
which chairs belong to which table.
"""

from __future__ import annotations

from typehaus.model import (
    Building,
    ClearancePolicy,
    ClearanceZone,
    Footprint2D,
    Furniture,
    FurnitureType,
    Library,
    Mount,
    MountKind,
    PlanModel,
    Project,
    Site,
    Storey,
    m,
    pt,
)
from typehaus.resolve import resolve

_CHAIR_TYPE_TAG = "F-CHAIR"
_SOFA_TYPE_TAG = "F-SOFA"
_CONFLICT_CHECK_ID = "integrity.placeable_recommended_clearance_conflict"

# A 4m x 4m chair-use zone around a 2m x 2m table: an object 1.4m off centre stands in it.
_ZONE_HALF_EXTENT_M = 2.0
_OCCUPANT_OFFSET_M = 1.4


def _square(half_extent: float) -> Footprint2D:
    return Footprint2D(points=(pt(m(-half_extent), m(-half_extent)),
                               pt(m(half_extent), m(-half_extent)),
                               pt(m(half_extent), m(half_extent)),
                               pt(m(-half_extent), m(half_extent))))


def _dining_set_plan(*placed: Furniture,
                     policy: ClearancePolicy = ClearancePolicy.RECOMMENDED) -> PlanModel:
    table = FurnitureType(
        tag="F-TABLE", name="Table", footprint=(m(2), m(2)), height=m(0.75),
        clearances=(ClearanceZone(footprint=_square(_ZONE_HALF_EXTENT_M),
                                  purpose="chair-use zone", policy=policy,
                                  occupant_types=(_CHAIR_TYPE_TAG,)),),
    )
    chair = FurnitureType(tag=_CHAIR_TYPE_TAG, name="Chair", footprint=(m(0.5), m(0.5)),
                          height=m(1))
    sofa = FurnitureType(tag=_SOFA_TYPE_TAG, name="Sofa", footprint=(m(0.5), m(0.5)), height=m(1))
    return PlanModel(
        project=Project(name="test", project_uuid="00000000-0000-0000-0000-000000000042",
                        building=Building(name="test"),
                        site=Site(lat=0, lon=0, elevation=m(0))),
        storeys=(Storey(tag="main", elevation=m(0), default_ceiling_height=m(3)),),
        library=Library(furniture_types=(table, chair, sofa)),
        elements={"main": (
            Furniture(uid="table-1", tag="TABLE", type_ref="F-TABLE", position=pt(m(0), m(0))),
            *placed,
        )},
    )


def _conflicts(findings) -> list[tuple[str, ...]]:
    return [finding.element_tags for finding in findings
            if finding.check_id == _CONFLICT_CHECK_ID]


def test_chairs_tucked_at_a_table_form_one_group_and_report_no_conflict() -> None:
    plan = _dining_set_plan(
        Furniture(uid="chair-1", tag="CHAIR-W", type_ref=_CHAIR_TYPE_TAG,
                  position=pt(m(-_OCCUPANT_OFFSET_M), m(0))),
        Furniture(uid="chair-2", tag="CHAIR-E", type_ref=_CHAIR_TYPE_TAG,
                  position=pt(m(_OCCUPANT_OFFSET_M), m(0))),
    )
    model, findings = resolve(plan)

    groups = {item.tag: item.placement_group for item in model.canvas_objects}
    assert groups == {"TABLE": "TABLE", "CHAIR-W": "TABLE", "CHAIR-E": "TABLE"}
    assert _conflicts(findings) == []


def test_an_unrelated_object_in_the_same_zone_still_reports() -> None:
    plan = _dining_set_plan(
        Furniture(uid="chair-1", tag="CHAIR-W", type_ref=_CHAIR_TYPE_TAG,
                  position=pt(m(-_OCCUPANT_OFFSET_M), m(0))),
        Furniture(uid="sofa-1", tag="SOFA", type_ref=_SOFA_TYPE_TAG,
                  position=pt(m(_OCCUPANT_OFFSET_M), m(0))),
    )
    model, findings = resolve(plan)

    assert next(item for item in model.canvas_objects if item.tag == "SOFA").placement_group is None
    assert _conflicts(findings) == [("TABLE", "SOFA")]


def test_a_lone_table_is_not_a_group_of_one() -> None:
    """Marking an unaccompanied anchor would tell a UI there is a set to drag when there is not."""
    model, findings = resolve(_dining_set_plan())

    assert [item.placement_group for item in model.canvas_objects] == [None]
    assert _conflicts(findings) == []


def test_grouping_never_silences_a_required_clearance() -> None:
    """A code minimum is not "for" whatever stands in it, so no arrangement may exempt it."""
    plan = _dining_set_plan(
        Furniture(uid="chair-1", tag="CHAIR-W", type_ref=_CHAIR_TYPE_TAG,
                  position=pt(m(-_OCCUPANT_OFFSET_M), m(0))),
        policy=ClearancePolicy.REQUIRED,
    )
    model, findings = resolve(plan)

    assert all(item.placement_group is None for item in model.canvas_objects)
    assert [finding.element_tags for finding in findings
            if finding.check_id == "integrity.placeable_required_clearance_conflict"] \
        == [("TABLE", "CHAIR-W")]


def test_every_clearance_zone_is_compared_not_just_the_first() -> None:
    """Regression: the peer scan must compare every clearance zone, not just the first."""
    two_zone_type = FurnitureType(
        tag="F-BED", name="Bed", footprint=(m(1.5), m(2)), height=m(0.6),
        clearances=(
            ClearanceZone(footprint=Footprint2D(points=(pt(m(-1.5), m(-1)), pt(m(-0.75), m(-1)),
                                                        pt(m(-0.75), m(1)), pt(m(-1.5), m(1)))),
                          purpose="left side access"),
            ClearanceZone(footprint=Footprint2D(points=(pt(m(0.75), m(-1)), pt(m(1.5), m(-1)),
                                                        pt(m(1.5), m(1)), pt(m(0.75), m(1)))),
                          purpose="right side access"),
        ),
    )
    obstacle = FurnitureType(tag="F-BOX", name="Box", footprint=(m(0.4), m(0.4)), height=m(0.4))
    plan = PlanModel(
        project=Project(name="test", project_uuid="00000000-0000-0000-0000-000000000043",
                        building=Building(name="test"),
                        site=Site(lat=0, lon=0, elevation=m(0))),
        storeys=(Storey(tag="main", elevation=m(0), default_ceiling_height=m(3)),),
        library=Library(furniture_types=(two_zone_type, obstacle)),
        elements={"main": (
            Furniture(uid="bed-1", tag="BED", type_ref="F-BED", position=pt(m(0), m(0))),
            # Only in the *second* zone, which the exhausted generator never reached.
            Furniture(uid="box-1", tag="BOX", type_ref="F-BOX", position=pt(m(1.1), m(0))),
        )},
    )
    _, findings = resolve(plan)

    assert _conflicts(findings) == [("BED", "BOX")]


def test_a_pendant_over_the_table_it_lights_is_not_in_the_table_s_zone() -> None:
    """A ``surround_zone`` is authored as the whole enlarged rectangle, so the owner's own
    footprint is part of it on paper. It is not part of it in fact: nothing standing where
    the table stands is encroaching on the margin *around* the table, and a pendant hung over
    it — the catlin ED-M-DINING-PEND case — sits entirely inside that footprint."""
    pendant = FurnitureType(tag="F-PENDANT", name="Pendant", footprint=(m(0.45), m(0.45)),
                            height=m(1))
    plan = _dining_set_plan(
        Furniture(uid="pendant-1", tag="PENDANT", type_ref="F-PENDANT",
                  position=pt(m(0), m(0)),
                  mount=Mount(kind=MountKind.CEILING, drop=m(1.3))),
    )
    plan = plan.model_copy(update={"library": plan.library.model_copy(update={
        "furniture_types": plan.library.furniture_types + (pendant,)})})
    _, findings = resolve(plan)

    assert _conflicts(findings) == []
