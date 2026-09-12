"""Engineered-header consumption: Door.header_spec / DoorType.header_spec → LVL members.

An authored spec like ``'2-ply 14" LVL'`` must replace the prescriptive table's header
with a multi-ply LVL member whose profile string parses structurally (plies, ply width,
depth); a spec the parser cannot read must fall back to the table rather than silently
sizing a header off a typo. The Door instance's spec wins over its DoorType's.
"""

from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest

from typehaus.model import (
    Assembly, Building, Library, Material, Node, PlanModel, Project, Site, Storey, Wall,
    degF, ft, inch, pt,
)
from typehaus.model.assembly import FramingSpec, Layer
from typehaus.model.elements import Door
from typehaus.model.enums import DoorOperation, LayerFunction
from typehaus.model.refs import from_node
from typehaus.model.types import DoorType
from typehaus.resolve import resolve
from typehaus.resolve.framing.openings import WallOpening
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.framing.solver import frame_wall
from typehaus.resolve.framing.tables import header_profile_from_spec
from typehaus.resolve.model import ResolvedWall


# ------------------------------------------------------------------ the spec parser
def test_header_spec_parses_to_a_structural_lvl_profile():
    assert header_profile_from_spec('2-ply 14" LVL') == "2-1.75x14 LVL"
    assert header_profile_from_spec("3-ply 11.875 in LVL") == "3-1.75x11.875 LVL"
    assert header_profile_from_spec("2-PLY 16 LVL") == "2-1.75x16 LVL"
    section = cross_section("2-1.75x14 LVL")
    assert section.plies == 2
    assert section.width_m == pytest.approx(inch(3.5).meters)
    assert section.depth_m == pytest.approx(inch(14).meters)


def test_unrecognized_header_spec_parses_to_none():
    assert header_profile_from_spec("a big beam") is None
    assert header_profile_from_spec('2x 14" LVL') is None
    assert header_profile_from_spec('2-ply 14" glulam') is None


# ------------------------------------------------------------------ solver unit level
def _wall_and_plan() -> tuple[SimpleNamespace, ResolvedWall]:
    layer = Layer(name="stud", material_ref="spf", thickness=inch(5.5),
                  function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6"))
    plan = SimpleNamespace(
        library=SimpleNamespace(resolve_assembly=lambda tag: SimpleNamespace(layers=(layer,)))
    )
    rw = ResolvedWall(
        uid="W1", tag="W-TEST", storey="MAIN", assembly="TEST_ASM",
        axis=((0.0, 0.0), (6.0, 0.0)), layers=(), z0_m=0.0, z1_m=2.7,
    )
    return plan, rw


def _door(header_spec: str | None) -> WallOpening:
    return WallOpening(center_m=3.0, width_m=inch(36).meters, height_m=inch(80).meters,
                       sill_m=0.0, is_door=True, header_spec=header_spec)


def test_header_spec_replaces_the_table_sized_header():
    plan, rw = _wall_and_plan()
    members = frame_wall(plan, rw, openings=[_door('2-ply 14" LVL')])
    header = next(m for m in members if m.category == "header")
    assert header.profile == "2-1.75x14 LVL"
    assert header.z1_m - header.z0_m == pytest.approx(inch(14).meters)
    assert cross_section(header.profile).plies == 2


def test_without_a_spec_the_prescriptive_table_still_sizes_the_header():
    plan, rw = _wall_and_plan()
    members = frame_wall(plan, rw, openings=[_door(None)])
    header = next(m for m in members if m.category == "header")
    assert header.profile == "2-2x8"  # a 3 ft door on the R602.7 table


def test_an_unparseable_spec_falls_back_to_the_table():
    plan, rw = _wall_and_plan()
    members = frame_wall(plan, rw, openings=[_door("two of the big ones")])
    header = next(m for m in members if m.category == "header")
    assert header.profile == "2-2x8"


# ------------------------------------------------------------------ plan integration
def _door_plan(type_spec: str | None, door_spec: str | None) -> PlanModel:
    """A bare 20x14 box with one 3 ft door on W-1, header specs as given."""
    ext = Assembly(tag="EXT", layers=(
        Layer(name="stud", material_ref="wood", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6")),
    ))
    project = Project(
        name="Header", project_uuid=uuid.UUID("00000000-0000-4000-8000-0000000000d5"),
        site=Site(lat=44.9, lon=-93.2, elevation=ft(830), design_temp_heating=degF(-15),
                  design_temp_cooling=degF(90)), building=Building(name="Header"))
    main = Storey(uid="STMAIN00D5", tag="main", elevation=ft(0),
                  default_ceiling_height=ft(9))
    nodes = tuple(
        Node(uid=f"ND5{i:07d}", tag=f"N-{i}", position=position)
        for i, position in enumerate((
            pt(ft(0), ft(0)), pt(ft(20), ft(0)), pt(ft(20), ft(14)), pt(ft(0), ft(14)),
        ), 1))
    walls = tuple(
        Wall(uid=f"WD5{i:07d}", tag=f"W-{i}", start_node=f"N-{start}",
             end_node=f"N-{end}", assembly="EXT", top=ft(9))
        for i, (start, end) in enumerate(((1, 2), (2, 3), (3, 4), (4, 1)), 1))
    door = Door(uid="DD50000001", tag="D-1", host="W-1", type_ref="DT-36",
                position=from_node("N-1", ft(8)), header_spec=door_spec)
    plan = PlanModel(project=project, library=Library(
        materials=(Material(tag="wood", name="Wood", r_per_inch=1.25),),
        assemblies=(ext,),
        door_types=(DoorType(tag="DT-36", width=ft(3), height=ft(6, 8),
                             header_spec=type_spec),)), storeys=(main,))
    return plan.with_elements("main", (*nodes, *walls, door))


def _resolved_header(plan: PlanModel):
    model, findings = resolve(plan)
    assert not [f for f in findings if f.severity.value == "error"], (
        [f.message for f in findings])
    wall = next(w for w in model.walls if w.tag == "W-1")
    return next(m for m in wall.members if m.category == "header")


def test_door_type_header_spec_reaches_the_framing_solver():
    header = _resolved_header(_door_plan('2-ply 14" LVL', None))
    assert header.profile == "2-1.75x14 LVL"
    assert header.z1_m - header.z0_m == pytest.approx(inch(14).meters)


def test_door_instance_header_spec_wins_over_its_type():
    header = _resolved_header(_door_plan('2-ply 14" LVL', '3-ply 16" LVL'))
    assert header.profile == "3-1.75x16 LVL"
    assert cross_section(header.profile).plies == 3


def test_no_spec_anywhere_keeps_the_table_header():
    header = _resolved_header(_door_plan(None, None))
    assert header.profile == "2-2x8"


# ------------------------------------------------------------------ head cripples
# Doors must get head cripples too: a garage overhead door needs its 18" of wall — and
# 16 ft of double top plate — backed above the header. The head family depends only on
# the arithmetic gap between the header top and the plate underside, never on the
# operation.
def _head_cripples(members):
    return sorted((m for m in members if m.child_key.startswith("cripple-head-")),
                  key=lambda m: m.child_key)


def _plate_underside(rw) -> float:
    """Wall top less the double top plate — what a vertical member's top lands on."""
    return rw.z1_m - 2 * inch(1.5).meters


def test_a_door_below_the_plate_line_gets_head_cripples():
    plan, rw = _wall_and_plan()
    members = frame_wall(plan, rw, openings=[_door(None)])
    cripples = _head_cripples(members)
    assert cripples, "a 6'-8\" door in a 9 ft wall has 16\" of wall above its header"
    header = next(m for m in members if m.category == "header")
    for cripple in cripples:
        assert cripple.category == "cripple"
        assert cripple.profile == "2x6"  # the wall's own member, so the price key
        #                                  stays the bare "2x6" the BOM already lists
        assert cripple.z0_m == pytest.approx(header.z1_m)
        assert cripple.z1_m == pytest.approx(_plate_underside(rw))
    # 16" o.c. across a 36" rough opening leaves exactly the two interior stations.
    stations = [m.p0[0] for m in cripples]
    assert len(stations) == 2
    assert stations[1] - stations[0] == pytest.approx(inch(16).meters)


def test_a_header_running_to_the_plate_line_gets_none():
    plan, rw = _wall_and_plan()
    # A door tall enough that its header top lands on the plate underside: no gap, so no
    # cripples — by the same arithmetic, not by a door/window test.
    depth = cross_section("2-2x8").depth_m
    tall = WallOpening(center_m=3.0, width_m=inch(36).meters,
                       height_m=_plate_underside(rw) - depth, sill_m=0.0, is_door=True)
    assert _head_cripples(frame_wall(plan, rw, openings=[tall])) == []


def test_a_sliver_gap_above_the_header_is_not_framed():
    plan, rw = _wall_and_plan()
    depth = cross_section("2-2x8").depth_m
    # 1" of wall above the header is an offcut, not a stud.
    sliver = WallOpening(center_m=3.0, width_m=inch(36).meters,
                         height_m=_plate_underside(rw) - depth - inch(1).meters,
                         sill_m=0.0, is_door=True)
    assert _head_cripples(frame_wall(plan, rw, openings=[sliver])) == []


def test_overhead_door_head_cripples_bear_on_the_track_backing():
    plan, rw = _wall_and_plan()
    overhead = WallOpening(center_m=3.0, width_m=ft(9).meters, height_m=ft(7).meters,
                           sill_m=0.0, is_door=True, operation=DoorOperation.OVERHEAD)
    members = frame_wall(plan, rw, openings=[overhead])
    backing = next(m for m in members if m.category == "blocking"
                   and m.child_key.startswith("trackbacking-"))
    header = next(m for m in members if m.category == "header")
    assert backing.z0_m == pytest.approx(header.z1_m)
    cripples = _head_cripples(members)
    assert cripples
    for cripple in cripples:
        # On the nailer, not through it: starting at the header top would bury 1.5" of
        # every cripple inside the blocking.
        assert cripple.z0_m == pytest.approx(backing.z1_m)
        assert cripple.z1_m == pytest.approx(_plate_underside(rw))


# --- the CHECK, not the framing: a wide opening is a published-table read ----------------
#
# `structural.header_prescriptive` used to hand every opening past IRC R602.7's 8' table to
# the engineering register. Since 2026-09-11 it does not: the beam supplier publishes a
# header schedule, reading a row is a prescriptive act, and the row is authored on the Door
# as a `PublishedSpan`. These pin the three states that matter — read, absent, and drifted.


class _PlanWithDoor:
    """catlin's plan with D-G-OVERHEAD's authored row edited or removed.

    A stand-in rather than a ``model_copy``: ``PlanModel.elements`` is a dict keyed by kind
    with a cached tag index, and the check reads exactly one thing off the plan for this
    opening. Rebuilding the model would test the copy more than the check.
    """

    def __init__(self, plan, door):
        self._plan = plan
        self._door = door
        self.project = plan.project
        self.library = plan.library

    def by_tag(self, tag):
        return self._door if tag == "D-G-OVERHEAD" else self._plan.by_tag(tag)


def _header_finding(catlin_model, **update):
    from typehaus.checks.registry import CheckContext, Preferences
    from typehaus.checks.structural.checks import header_within_prescriptive

    plan = catlin_model.plan
    door = plan.by_tag("D-G-OVERHEAD")
    assert door is not None and door.published_span is not None
    if update.pop("_drop_row", False):
        door = door.model_copy(update={"published_span": None})
    elif update:
        door = door.model_copy(update={
            "published_span": door.published_span.model_copy(update=update)})
    ctx = CheckContext(plan=_PlanWithDoor(plan, door), model=catlin_model,
                       preferences=Preferences(), profile=None)
    findings = header_within_prescriptive(ctx)
    return next(f for f in findings if "D-G-OVERHEAD" in f.element_tags)


def test_the_overhead_door_header_is_a_prescriptive_table_read(catlin_model) -> None:
    """A 16' rough opening, headed with a 2-ply 14" LVL, answered by TJ-9000's own row."""
    from typehaus.findings import Authority, Result

    finding = _header_finding(catlin_model)
    assert finding.result is Result.PASS
    assert finding.authority is Authority.PRESCRIPTIVE
    assert finding.engineering_item is None
    assert "TJ-9000" in finding.message
    assert "16.00'" in finding.message and "16.25'" in finding.message
    # The conditions the row assumes and this engine does not check are printed, or the
    # PASS is a claim rather than a read.
    assert "GABLE END" in finding.message


def test_no_authored_row_is_unknown_with_the_hint(catlin_model) -> None:
    from typehaus.findings import Authority, Result

    finding = _header_finding(catlin_model, _drop_row=True)
    assert finding.result is Result.UNKNOWN
    assert finding.authority is Authority.PRESCRIPTIVE
    assert "no published table row is authored" in finding.message
    assert "published_span" in (finding.fix_hint or "")


def test_a_row_for_a_different_beam_stops_describing_the_opening(catlin_model) -> None:
    """Retype the header and the quotation is about some other member. UNKNOWN, not PASS."""
    from typehaus.findings import Result

    finding = _header_finding(catlin_model, member='2-ply 11.875" LVL')
    assert finding.result is Result.UNKNOWN
    assert "no longer describes this member" in finding.message


def test_an_opening_wider_than_its_row_fails(catlin_model) -> None:
    from typehaus.quantities import ft
    from typehaus.findings import Result

    finding = _header_finding(catlin_model, span=ft(12))
    assert finding.result is Result.FAIL
    assert "past the 12.00'" in finding.message
