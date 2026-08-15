"""The conformance gate on the artifact that leaves the building.

Two things were missing. First, IFC validation ran in exactly one place — a catlin test, at
framed LOD — so ``model_core.ifc``, the *handoff* artifact a receiving tool actually opens,
was never validated at all. Second, every IFC test in this suite guards with
``pytest.importorskip("ifcopenshell")``, so a broken install turns the whole IFC surface
green by skipping it. This module imports ifcopenshell unconditionally: no ifcopenshell, no
green build.

The IDS baseline (``tests/data/baseline.ids``) pins the structure a receiving tool needs —
spatial spine present and named, walls named and contained in a storey. It is deliberately a
floor, not a ceiling: ratchet it richer as the emitter earns it.
"""

from __future__ import annotations

from pathlib import Path

import ifcopenshell
import ifcopenshell.validate
import pytest
from ifctester import ids, reporter

from typehaus.emit.ifc import emit_ifc
from typehaus.resolve import resolve
from typehaus.source import load_plan
from _helpers import HOUSES

BASELINE_IDS = Path(__file__).resolve().parent / "data" / "baseline.ids"

# (house, LOD). `core` is the handoff LOD — the one that was never validated.
COMBINATIONS = [("starter", "core"), ("starter", "framed"),
                ("catlin", "core"), ("catlin", "framed")]


@pytest.fixture(scope="session")
def built_ifc(request, tmp_path_factory) -> Path:
    """Build one IFC per (house, LOD), once per session: four full builds is the CI budget."""
    house, lod = request.param
    out = tmp_path_factory.mktemp(f"ifc-{house}-{lod}") / f"{house}-{lod}.ifc"
    result = load_plan(HOUSES / house)
    assert result.plan is not None, [f.message for f in result.findings]
    model, _findings = resolve(result.plan)
    return emit_ifc(model, out, lod=lod)


def _ids_ok(path: Path) -> tuple[bool, list[str]]:
    specs = ids.open(str(BASELINE_IDS))
    specs.validate(ifcopenshell.open(str(path)))
    failures: list[str] = []
    for spec in specs.specifications:
        if spec.status is False:
            failed = [f"{r.__class__.__name__}" for r in spec.requirements
                      if getattr(r, "status", True) is False]
            failures.append(f"{spec.name}: {failed}")
    # Keep the json reporter in the loop so a reporter-side breakage surfaces here rather
    # than the first time someone asks for a report.
    reporter.Json(specs).report()
    return not failures, failures


@pytest.mark.parametrize("built_ifc", COMBINATIONS, indirect=True,
                         ids=[f"{house}-{lod}" for house, lod in COMBINATIONS])
def test_ifc_passes_express_rule_validation(built_ifc: Path) -> None:
    assert built_ifc.exists() and built_ifc.stat().st_size > 0
    logger = ifcopenshell.validate.json_logger()
    ifcopenshell.validate.validate(str(built_ifc), logger, express_rules=True)
    assert not logger.statements, logger.statements


@pytest.mark.parametrize("built_ifc", COMBINATIONS, indirect=True,
                         ids=[f"{house}-{lod}" for house, lod in COMBINATIONS])
def test_ifc_meets_the_ids_handoff_baseline(built_ifc: Path) -> None:
    ok, failures = _ids_ok(built_ifc)
    assert ok, failures


def test_the_baseline_is_a_valid_ids_document() -> None:
    """A malformed baseline would pass every model vacuously."""
    specs = ids.open(str(BASELINE_IDS))
    assert specs.specifications
    assert all(spec.requirements for spec in specs.specifications)


# --- the optional construction schedule ----------------------------------------------------
#
# Gated behind `emit_ifc(..., sequence=True)` / `haus build --with-schedule`, so it needs its
# own build: the four combinations above deliberately exercise the lean permit file, which is
# what a plan reviewer opens.

@pytest.fixture(scope="module")
def scheduled_ifc(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("ifc-schedule") / "catlin-schedule.ifc"
    house = HOUSES / "catlin"
    result = load_plan(house)
    assert result.plan is not None, [f.message for f in result.findings]
    model, _findings = resolve(result.plan)
    return emit_ifc(model, out, lod="core", sequence=True, house_dir=house)


def test_the_scheduled_ifc_still_passes_express_rules(scheduled_ifc: Path) -> None:
    """Cost and task entities are the newest thing in the file and the easiest to get
    structurally wrong — an IfcTask missing its nesting opens as an empty schedule rather
    than as an error, which is why this is validated and not merely eyeballed."""
    logger = ifcopenshell.validate.json_logger()
    ifcopenshell.validate.validate(str(scheduled_ifc), logger, express_rules=True)
    assert not logger.statements, logger.statements


def test_the_scheduled_ifc_still_meets_the_handoff_baseline(scheduled_ifc: Path) -> None:
    ok, failures = _ids_ok(scheduled_ifc)
    assert ok, failures


def test_the_schedule_carries_tasks_costs_and_their_order(scheduled_ifc: Path) -> None:
    model = ifcopenshell.open(str(scheduled_ifc))
    tasks = model.by_type("IfcTask")
    assert len(model.by_type("IfcWorkPlan")) == 1
    assert len(model.by_type("IfcWorkSchedule")) == 1
    assert tasks and len(model.by_type("IfcCostItem")) == len(tasks)
    # The order is the authored CONSTRUCTION_SEQUENCE, expressed as real relationships
    # rather than only as a name a reader would have to sort alphabetically.
    assert model.by_type("IfcRelSequence")
    assert all(rel.SequenceType == "FINISH_START" for rel in model.by_type("IfcRelSequence"))


def test_no_task_claims_a_duration_the_model_cannot_know(scheduled_ifc: Path) -> None:
    """Durations, crew sizes and dates are deliberately absent. A fabricated duration is
    worse than an absent one: it is the number the whole schedule then gets built on."""
    model = ifcopenshell.open(str(scheduled_ifc))
    assert not model.by_type("IfcTaskTime")
    assert all(task.TaskTime is None for task in model.by_type("IfcTask"))


def test_tasks_are_linked_to_the_products_they_cover(scheduled_ifc: Path) -> None:
    model = ifcopenshell.open(str(scheduled_ifc))
    linked = model.by_type("IfcRelAssignsToProcess")
    assert linked
    assert sum(len(rel.RelatedObjects) for rel in linked) > 100


def test_the_default_ifc_carries_no_schedule(built_ifc: Path) -> None:
    """The permit file stays lean — that is the whole reason the emitter is gated."""
    model = ifcopenshell.open(str(built_ifc))
    assert not model.by_type("IfcTask")
    assert not model.by_type("IfcCostSchedule")


test_the_default_ifc_carries_no_schedule = pytest.mark.parametrize(
    "built_ifc", COMBINATIONS, indirect=True,
    ids=[f"{house}-{lod}" for house, lod in COMBINATIONS])(
        test_the_default_ifc_carries_no_schedule)
