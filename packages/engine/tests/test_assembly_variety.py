"""``advisory.assembly_variety``: one tag is one geometry stack (#70).

The rule the check enforces is the narrow half of decision #70 — two wall tags whose
resolved stacks differ only in which material fills a layer are one wall drawn twice, and
the difference belongs in ``Wall.layer_materials``. The rest of the check reports facts
(unreferenced tags, the histogram), so those are asserted as PASS findings, not failures.

catlin is the second fixture: after the consolidation batch it must carry no twin pair.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from typehaus.checks.advisory.assembly_variety import assembly_variety
from typehaus.findings import Result
from typehaus.model import (
    Assembly,
    Layer,
    LayerFunction,
    Library,
    Node,
    PlanModel,
    Point2D,
    Project,
    Site,
    Wall,
    ft,
    inch,
)
from typehaus.model import Building

HOUSE = Path(__file__).resolve().parents[3] / "houses" / "catlin"


def _stud(material: str) -> Layer:
    return Layer(name="stud", material_ref=material, thickness=inch(5.5),
                 function=LayerFunction.STRUCTURE)


def _plan(*assemblies: Assembly) -> PlanModel:
    walls = tuple(
        Wall(tag=f"W-{i}", start_node="N-A", end_node="N-B", assembly=assembly.tag)
        for i, assembly in enumerate(assemblies)
    )
    nodes = (Node(tag="N-A", position=Point2D(x=0.0, y=0.0)),
             Node(tag="N-B", position=Point2D(x=3.0, y=0.0)))
    project = Project(
        name="AV", project_uuid="00000000-0000-4000-8000-0000000000a7",
        site=Site(lat=44.9, lon=-93.2, elevation=ft(830)), building=Building(name="AV"))
    return PlanModel(
        project=project,
        library=Library(assemblies=assemblies),
        elements={"S": nodes + walls},
    )


def _findings(plan: PlanModel):
    return assembly_variety(SimpleNamespace(plan=plan))  # type: ignore[arg-type]


def _fails(findings):
    return [f for f in findings if f.result is Result.FAIL]


def test_two_material_only_twins_fire():
    """Same stack, different stud species — the MUDROOM/STAIRWALL case that started this."""
    fails = _fails(_findings(_plan(
        Assembly(tag="A_INT", layers=(_stud("spf"),)),
        Assembly(tag="B_INT", layers=(_stud("df-select-s4s"),)),
    )))
    assert len(fails) == 1
    assert "A_INT" in fails[0].message and "B_INT" in fails[0].message
    assert "Wall.layer_materials" in fails[0].message


def test_a_real_stack_difference_is_not_a_twin():
    """A leaf the other does not have is a different wall, and keeps its own tag."""
    gwb = Layer(name="gwb-x", material_ref="gwb-x", thickness=inch(0.625),
                function=LayerFunction.FINISH)
    assert _fails(_findings(_plan(
        Assembly(tag="A_INT", layers=(_stud("spf"),)),
        Assembly(tag="B_INT", layers=(_stud("spf"), gwb)),
    ))) == []


def test_a_variant_is_compared_as_the_wall_it_builds():
    """Resolution runs first, so a variant that resolves to a twin still fires."""
    from typehaus.model import Substitution, layers

    base = Assembly(tag="A_INT", layers=(_stud("spf"),))
    twin = Assembly(tag="B_INT", variant_of="A_INT", substitute=(
        Substitution(span=layers("stud", "stud"),
                     replacement=(_stud("df-select-s4s"),)),))
    assert len(_fails(_findings(_plan(base, twin)))) == 1


def test_the_histogram_and_the_unreferenced_list_are_notes_not_failures():
    orphan = Assembly(tag="ORPHAN", layers=(_stud("spf"),))
    plan = _plan(Assembly(tag="A_INT", layers=(_stud("spf"),)))
    plan = plan.model_copy(update={
        "library": plan.library.model_copy(
            update={"assemblies": (*plan.library.assemblies, orphan)})})
    notes = [f for f in _findings(plan) if f.result is Result.PASS]
    assert any("ORPHAN" in f.message for f in notes)
    assert any("1 wall assemblies across 1 walls" in f.message for f in notes)


def test_catlin_carries_no_material_only_twin():
    from typehaus.source.loader import load_plan

    assert _fails(_findings(load_plan(HOUSE).plan)) == []
