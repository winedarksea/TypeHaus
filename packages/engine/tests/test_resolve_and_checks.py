"""WP1.4/1.5/1.8 tests — resolve the starter + broken fixtures fail with one finding each."""

from __future__ import annotations

from pathlib import Path

from typehaus.checks import run
from typehaus.model import (
    Assembly,
    FramingSpec,
    Layer,
    LayerFunction,
    Library,
    Material,
    Node,
    Occupancy,
    PlanModel,
    Room,
    Storey,
    Wall,
    Window,
    WindowType,
    centered,
    ft,
    inch,
    pt,
)
from typehaus.resolve import resolve
from typehaus.source import load_plan
from _helpers import STARTER



def _lib() -> Library:
    return Library(
        materials=(Material(tag="spf", name="SPF", r_per_inch=1.25),
                   Material(tag="gwb", name="GWB", r_per_inch=0.9)),
        assemblies=(Assembly(tag="EXT", layers=(
            Layer(name="stud", material_ref="spf", thickness=inch(5.5),
                  function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6")),),
            default_lining=(Layer(name="gwb", material_ref="gwb", thickness=inch(0.625),
                                  function=LayerFunction.FINISH),)),),
    )


def _rect_plan(project) -> PlanModel:
    storey = Storey(uid="ST00000001", tag="s1", elevation=ft(0),
                    default_ceiling_height=ft(9))
    nodes = [Node(uid=f"N{i:09d}", tag=f"N-{i}", position=p) for i, p in enumerate(
        [pt(ft(0), ft(0)), pt(ft(20), ft(0)), pt(ft(20), ft(14)), pt(ft(0), ft(14))], 1)]
    walls = [Wall(uid=f"W{i:09d}", tag=f"W-{i}", start_node=f"N-{a}", end_node=f"N-{b}",
                  assembly="EXT", top=ft(9))
             for i, (a, b) in enumerate([(1, 2), (2, 3), (3, 4), (4, 1)], 1)]
    room = Room(uid="RM00000001", tag="RM-1", seed=pt(ft(10), ft(7)),
                occupancy=Occupancy.LIVING)
    return (PlanModel(project=project, library=_lib(), storeys=(storey,))
            .with_elements("s1", [*nodes, *walls, room]))


def test_starter_resolves_clean(project) -> None:
    result = load_plan(STARTER)
    assert result.ok, [f.render() for f in result.findings]
    model, findings = resolve(result.plan)
    assert not findings
    assert len(model.rooms) == 2
    assert model.stack_edges, "two identical storeys must derive a wall-line stack"
    assert any(c.kind.value == "storey_stack" for c in model.conditions)


def test_rect_room_area(project) -> None:
    model, findings = resolve(_rect_plan(project))
    assert not findings
    (room,) = model.rooms
    assert 260 < room.area_m2 * 10.7639 < 280  # ~20x14=280, less lining inset


def test_gap_node_one_finding(project) -> None:
    plan = _rect_plan(project)
    # Drop one wall to open the loop.
    els = [e for e in plan.storey_elements("s1") if e.tag != "W-4"]
    plan = plan.with_elements("s1", els)
    _, findings = resolve(plan)
    gaps = [f for f in findings if f.check_id == "integrity.wall_loop_open"]
    assert len(gaps) == 2  # both nodes of the removed wall become single-edge


def test_orphan_opening_one_finding(project) -> None:
    plan = _rect_plan(project)
    els = list(plan.storey_elements("s1"))
    els.append(Window(uid="WN00000001", tag="WIN-x", host="W-999", type_ref="WT",
                      position=centered(), sill_height=ft(2)))
    plan = plan.with_elements("s1", els)
    _, findings = resolve(plan)
    orphans = [f for f in findings if f.check_id == "integrity.orphan_opening"]
    assert len(orphans) == 1
    assert orphans[0].element_tags == ("WIN-x",)


def test_missing_assembly_one_finding(project) -> None:
    plan = _rect_plan(project)
    els = list(plan.storey_elements("s1"))
    els[4] = els[4].model_copy(update={"assembly": "NOPE"})  # W-1 -> unknown assembly
    plan = plan.with_elements("s1", els)
    report = run(plan)
    missing = [f for f in report.findings if f.check_id == "integrity.wall_assembly"]
    assert len(missing) == 1


def test_tri_state_counts(project) -> None:
    report = run(_rect_plan(project))
    p, f, u = report.counts()
    assert p + f + u == len(report.findings)
    # The fixture is a bare rectangle of walls, not a house: its minimal "EXT" assembly
    # (R-8, → _lib()) is not a code-compliant wall, it models no Alarm anywhere, and its
    # single room has no windows. All three CODE rules below are working correctly on a
    # fixture that was never meant to pass them. What this test actually asserts is that
    # *resolve* produced nothing broken.
    fixture_gaps = {"code.energy_prescriptive", "code.R314_alarm_every_storey",
                    "code.R303_1_light_and_ventilation"}
    non_energy_errors = [e for e in report.errors if e.check_id not in fixture_gaps]
    assert not non_energy_errors
