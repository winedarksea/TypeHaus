"""Window.header_spec / Window.published_span: an LVL over a window, read off a table.

A window within R602.7's 8' is sized by the table unless it authors both an LVL spec and
the manufacturer's row that sizes it; then `structural.header_prescriptive` grades the row.
"""

from __future__ import annotations

import uuid

import pytest

from typehaus.checks.registry import CheckContext, Preferences
from typehaus.checks.structural.checks import header_within_prescriptive
from typehaus.findings import Authority, Result
from typehaus.model import (
    Assembly, Building, Library, Material, Node, PlanModel, Project, Site, Storey, Wall,
    degF, ft, inch, pt,
)
from typehaus.model.assembly import FramingSpec, Layer
from typehaus.model.elements import Window
from typehaus.model.enums import LayerFunction
from typehaus.model.refs import PublishedSpan, from_node
from typehaus.model.types import WindowType
from typehaus.resolve import resolve
from typehaus.resolve.framing.profiles import cross_section

_ROW = PublishedSpan(
    source="Test header guide", table="roof + floor, 36' width: 2-ply 9-1/4\" LVL",
    member='2-ply 9.25" LVL', span=ft(6, 0), condition="test row", load_psf=60.0)


def _plan(spec: str | None, row: PublishedSpan | None) -> PlanModel:
    """A bare 20x14 box with one 63" window on W-1."""
    ext = Assembly(tag="EXT", layers=(
        Layer(name="stud", material_ref="wood", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6")),
    ))
    project = Project(
        name="WinHeader", project_uuid=uuid.UUID("00000000-0000-4000-8000-0000000000e6"),
        site=Site(lat=44.9, lon=-93.2, elevation=ft(830), design_temp_heating=degF(-15),
                  design_temp_cooling=degF(90), ground_snow_load_psf=50.0),
        building=Building(name="WinHeader"))
    main = Storey(uid="STMAIN00E6", tag="main", elevation=ft(0),
                  default_ceiling_height=ft(9))
    nodes = tuple(
        Node(uid=f"NE6{i:07d}", tag=f"N-{i}", position=position)
        for i, position in enumerate((
            pt(ft(0), ft(0)), pt(ft(20), ft(0)), pt(ft(20), ft(14)), pt(ft(0), ft(14)),
        ), 1))
    walls = tuple(
        Wall(uid=f"WE6{i:07d}", tag=f"W-{i}", start_node=f"N-{start}",
             end_node=f"N-{end}", assembly="EXT", top=ft(9))
        for i, (start, end) in enumerate(((1, 2), (2, 3), (3, 4), (4, 1)), 1))
    window = Window(uid="WE60000001", tag="WIN-1", host="W-1", type_ref="WT-63",
                    position=from_node("N-1", ft(8)), sill_height=ft(2, 10),
                    header_spec=spec, published_span=row)
    plan = PlanModel(project=project, library=Library(
        materials=(Material(tag="wood", name="Wood", r_per_inch=1.25),),
        assemblies=(ext,),
        window_types=(WindowType(tag="WT-63", width=inch(63), height=inch(48)),)),
        storeys=(main,))
    return plan.with_elements("main", (*nodes, *walls, window))


def _resolve(plan: PlanModel):
    model, findings = resolve(plan)
    assert not [f for f in findings if f.severity.value == "error"], (
        [f.message for f in findings])
    return model


def _header(plan: PlanModel):
    wall = next(w for w in _resolve(plan).walls if w.tag == "W-1")
    return next(m for m in wall.members if m.category == "header")


def _finding(plan: PlanModel):
    ctx = CheckContext(plan=plan, model=_resolve(plan), preferences=Preferences(),
                       profile=None)
    return [f for f in header_within_prescriptive(ctx) if "WIN-1" in f.element_tags]


def test_window_header_spec_reaches_the_framing_solver():
    header = _header(_plan('2-ply 9.25" LVL', _ROW))
    assert header.profile == "2-1.75x9.25 LVL"
    assert header.z1_m - header.z0_m == pytest.approx(inch(9.25).meters)
    assert cross_section(header.profile).plies == 2


def test_a_window_without_a_spec_keeps_the_table_header():
    assert "LVL" not in _header(_plan(None, None)).profile


def test_a_row_that_covers_the_opening_passes_prescriptively():
    (finding,) = _finding(_plan('2-ply 9.25" LVL', _ROW))
    assert finding.result is Result.PASS
    assert finding.authority is Authority.PRESCRIPTIVE
    assert finding.engineering_item is None


def test_a_row_shorter_than_the_opening_fails():
    short = _ROW.model_copy(update={"span": ft(4, 0)})
    (finding,) = _finding(_plan('2-ply 9.25" LVL', short))
    assert finding.result is Result.FAIL


def test_a_row_for_another_member_is_unknown():
    (finding,) = _finding(_plan('2-ply 11.875" LVL', _ROW))
    assert finding.result is Result.UNKNOWN


@pytest.mark.parametrize(("spec", "row"), [(None, None), ('2-ply 9.25" LVL', None),
                                          (None, _ROW)])
def test_a_window_authoring_less_than_both_is_left_to_r602_7(spec, row):
    assert _finding(_plan(spec, row)) == []
