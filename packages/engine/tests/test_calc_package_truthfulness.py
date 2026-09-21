"""The package has to say what is actually true about itself.

Finding 9 of the 2026-09-18 engineering gap review: the bundle claimed a completeness it
does not have, told a reviewer that work which IS theirs is not, asserted one design method
for a package that uses two, and was silent about the one fact that decides whether the
review unblocks anything. Each assertion here pins one of those sentences.
"""

from __future__ import annotations

import pytest
from _helpers import CATLIN

from typehaus.engineering.item import Scope, Status


@pytest.fixture(scope="module")
def catlin_engineering(catlin_ctx):
    """``(ctx, item_ids, checklist)`` — derived exactly as ``cli/cmd_calcs.py`` derives it.

    Built on the shared ``catlin_ctx`` rather than a fresh load, which
    ``test_catlin_fixture_discipline`` lints for.
    """
    from typehaus.checks import evaluate_permit_checklist, run_checks

    report = run_checks(catlin_ctx)
    named = {f.engineering_item for f in report.findings if f.engineering_item}
    item_ids = tuple(sorted(named | set(catlin_ctx.engineering)))
    return catlin_ctx, item_ids, evaluate_permit_checklist(report, catlin_ctx.profile)


def _inputs(ctx, item_ids, checklist):
    """The emitter's whole input, spelled once — ``cli/cmd_calcs.py``'s own shape."""
    from typehaus.takeoff.calc_package import PackageInputs

    return PackageInputs(
        house="catlin", model=ctx.model, item_ids=item_ids, results=ctx.engineering,
        register=ctx.engineering_register, generated="2026-09-18",
        engine_version="test", content_hash="deadbeefdeadbeef",
        profile_name=ctx.profile.name, checklist=checklist)


def test_a_screening_record_says_so_in_its_header_and_its_exclusions(catlin_ctx) -> None:
    """``Status.OK`` and "nothing missing" are different claims, and the sheet made both.

    ``OK`` means every limit state the module ENUMERATED is under 1. Every sheet's own §9
    has always said that the ones it did not enumerate are neither evaluated nor implied to
    pass — so the header and the footer of one page disagreed. ``Scope`` is the fourth axis
    that carries the difference, the way ``Freshness`` already carries the professional one.
    """
    from typehaus.engineering import EngineeringRegister
    from typehaus.takeoff.calc_sheet import render_sheet

    record = catlin_ctx.engineering["retaining_wall/W-SG-E2"]
    assert record.status is Status.OK
    assert record.scope is Scope.SCREENING, (
        "a module that has not thought about its coverage is screening, and the default "
        "must say so rather than claiming completeness by silence")

    sheet = render_sheet(record, EngineeringRegister(), generated="2026-09-18",
                         house="catlin")
    assert "**Coverage:** SCREENING" in sheet
    assert "the header's *Local status* is a statement about the graded ones only" in sheet


def test_a_deferred_record_is_external_and_not_merely_screening(catlin_ctx) -> None:
    """Three states, and the third is not a weaker second. An item somebody else designs is
    not a narrow calculation — it is no calculation, and the axis says which."""
    record = catlin_ctx.engineering["rafter/RF-GARAGE"]
    assert record.status is Status.NO_CALC
    assert record.scope is Scope.EXTERNAL


def test_the_scope_axis_is_not_in_the_fingerprint(catlin_ctx) -> None:
    """Re-classifying a module's coverage must not stale a seal over arithmetic that did
    not move — the same rule ``oracle`` follows, and for the same reason."""
    from dataclasses import replace

    from typehaus.engineering import fingerprint

    record = catlin_ctx.engineering["retaining_wall/W-SG-E2"]
    assert fingerprint(replace(record, scope=Scope.COMPLETE)) == fingerprint(record)


def test_the_readme_states_where_the_permit_gate_stands(catlin_engineering) -> None:
    """``checklist`` was a parameter of ``pe_readme`` from the day it was written and was
    read nowhere, so the page a reviewer opens first was silent on the one fact that says
    whether this review unblocks anything.

    catlin's gate is SHUT again since 2026-09-20 — five engineering lines the newly
    registered calculations left open — so the house exercises that branch and the OPEN one
    is exercised below on a stub. Both are asserted, because a bundle whose README said the
    wrong one would mislead the reviewer about the only fact they opened it for.
    """
    from typehaus.takeoff.handoff import pe_readme

    ctx, item_ids, checklist = catlin_engineering
    readme = pe_readme(house="catlin", generated="2026-09-20", engine_version="0",
                       content_hash="abc", records=[ctx.engineering[i] for i in item_ids],
                       notes=[], checklist=checklist, has_pdf=False)
    assert "## Where the permit gate stands" in readme
    assert "The draft gate is SHUT" in readme
    assert "The draft gate is OPEN." not in readme
    assert "Segmental gravity retaining walls (tiered)" in readme


def test_the_readme_names_every_open_blocking_item_when_the_gate_is_shut() -> None:
    """The SHUT branch on a stub, beside the OPEN one catlin no longer reaches.

    A reviewer opening a SHUT bundle has to be told which lines are shut and that a stamp
    will not open them — the gate is about this engine's own arithmetic. Held on a stub
    rather than deleted with the house that used to exercise it: the wording is the whole
    point of the block, and a branch nobody runs is a branch that rots.
    """
    from types import SimpleNamespace

    from typehaus.findings import Result
    from typehaus.takeoff.handoff import _gate_block

    items = [
        SimpleNamespace(blocking=True, result=Result.PASS, label="Fine", detail="—"),
        SimpleNamespace(blocking=True, result=Result.UNKNOWN,
                        label="Fixed column base embedment", detail="a judgement is missing"),
        SimpleNamespace(blocking=False, result=Result.FAIL, label="Advisory", detail="—"),
    ]
    block = "\n".join(_gate_block(
        SimpleNamespace(items=items, profile_name="mn-2020")))
    assert "**The draft gate is SHUT**, on 1 of 2 blocking" in block
    assert "Fixed column base embedment" in block and "a judgement is missing" in block
    assert "Advisory" not in block, "the staging lane is the engine's coverage, not the house's"
    assert "a stamp on this bundle does not open them" in block

    # And the OPEN branch, which catlin does not reach since 2026-09-20.
    passing = [SimpleNamespace(blocking=True, result=Result.PASS, label="Fine", detail="—")]
    opened = "\n".join(_gate_block(SimpleNamespace(items=passing, profile_name="mn-2020")))
    assert "**The draft gate is OPEN.**" in opened
    assert "What is left is the seal itself" in opened


def test_the_readme_claims_no_completeness_and_hands_back_the_deferrals(
        catlin_engineering) -> None:
    """The two sentences that were false, asserted as gone rather than merely rewritten.

    "with nothing missing" was contradicted by every sheet's §9; "DEFERRED and are not
    yours" was contradicted by `03-open-items.md`'s own designer column on 12 of catlin's
    items, which name the structural engineer of record — the person reading the page.
    """
    from typehaus.takeoff.handoff import pe_readme

    ctx, item_ids, checklist = catlin_engineering
    readme = pe_readme(house="catlin", generated="2026-09-18", engine_version="0",
                       content_hash="abc", records=[ctx.engineering[i] for i in item_ids],
                       notes=[], checklist=checklist, has_pdf=False)
    assert "with nothing missing" not in readme
    assert "are not yours" not in readme
    assert "**Some of them are yours.**" in readme
    assert "screening" in readme


def test_the_criteria_page_states_a_design_method_per_kind(catlin_engineering) -> None:
    """One package, two methods. "Every capacity cited in this package is an ASD allowable"
    sat on the cover of a package whose every concrete item is LRFD — a reviewer taking it
    at face value compares a strength capacity against a service demand."""
    from typehaus.takeoff.calc_criteria import _criteria as design_criteria

    ctx, item_ids, checklist = catlin_engineering
    page = design_criteria(_inputs(ctx, item_ids, checklist))

    assert "every capacity cited in this package is an ASD allowable" not in page
    assert "Design method" in page
    assert "LRFD (ACI 318-19 strength design" in page
    assert "**The design method is per kind, and this package uses both.**" in page


def test_the_criteria_page_prints_the_design_snow_beside_the_ground_snow(
        catlin_engineering) -> None:
    """``_snow_block`` printed ``p_g`` and nothing else, on a house whose governing case is
    an authored drift the engine derives no part of. 50 psf on the cover beside records
    computed at 73.7 invites exactly one conclusion, and it is the wrong one."""
    from typehaus.takeoff.calc_criteria import _criteria as design_criteria

    ctx, item_ids, checklist = catlin_engineering
    page = design_criteria(_inputs(ctx, item_ids, checklist))

    assert "p_g, ground snow load" in page
    assert "Design roof snow, as computed" in page
    assert "73.7" in page
    assert "**The design snow is not p_g" in page


def test_the_format_doc_no_longer_carries_a_stale_deferral_count() -> None:
    """A number about ONE HOUSE written into the format's specification went stale four
    times. The doc says so and points at the CLI, which is generated and always right."""
    doc = (CATLIN.parents[1] / "docs" / "calc-package-format.md").read_text()
    assert "05-scope-of-review.md" in doc
    assert "Seven items in catlin" not in doc
    assert "An exact count does not belong in this document" in doc
    assert "structural engineer of record" in doc


@pytest.mark.parametrize("page", ["00-cover.md", "01-design-criteria.md",
                                  "02-item-register.md", "03-open-items.md",
                                  "04-assumptions.md", "05-scope-of-review.md"])
def test_every_front_matter_page_the_doc_lists_is_actually_written(page, catlin_engineering
                                                                   ) -> None:
    """The doc's file listing omitted `05-scope-of-review.md`, which the package has been
    writing for as long as the listing has been wrong."""
    from typehaus.takeoff.calc_package import calc_package

    ctx, item_ids, checklist = catlin_engineering
    files = calc_package(_inputs(ctx, item_ids, checklist))
    assert page in files
