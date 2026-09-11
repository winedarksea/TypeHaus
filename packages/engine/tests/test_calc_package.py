"""``haus calcs`` — the calculation package, and the oracle lint behind it.

Assertion-based rather than golden, following ``test_hardwood_takeoff.py`` and the CSV
exports: a legitimate model change must not churn a stored fixture, because a package
whose test has to be re-blessed every time a wall moves is a package nobody re-blesses
carefully.

The two assertions doing unusual work:

* :func:`test_every_registered_kind_names_an_oracle_note_that_exists` is the root
  ``CLAUDE.md`` rule — "a calc that only agrees with itself is not verified" — made
  mechanical. It is the one test here that can fail because of something outside this
  feature, and that is deliberate: a new calc module with no hand-worked note behind it
  should not reach main.
* :func:`test_the_fingerprint_on_a_sheet_is_the_one_the_cli_prints` pins the thing that
  makes the package usable for sealing at all. A PE pins the fingerprint the package shows
  them; if that string is not what ``haus engineering --fingerprint`` computes, every seal
  in the house is pinned to nothing.
"""

from __future__ import annotations

from datetime import date

import pytest
from _helpers import CATLIN, REPO_ROOT

from typehaus.engineering import registered_kinds
from typehaus.engineering.fingerprint import fingerprint
from typehaus.engineering.item import Status
from typehaus.engineering.registry import oracles_for
from typehaus.takeoff.calc_package import PackageInputs, calc_package
from typehaus.takeoff.calc_sheet import sheet_filename

#: Every section a finished sheet carries, in order. A sheet missing one of these is not a
#: calculation sheet — it is a table with a title.
SECTIONS = (
    "## 1. Scope",
    "## 2. References",
    "## 3. Given",
    "## 4. Analysis",
    "## 5. Result",
    "## 6. Assumptions and exclusions",
    "## 7. Open inputs",
    "## 8. Independent check",
    "## 9. What this sheet does not cover",
)


@pytest.fixture(scope="module")
def catlin_engineering(catlin_plan):
    """The catlin context, its item list and its records — the emitter's whole input.

    The item list is derived exactly as ``cli/cmd_calcs.py`` derives it (the checks'
    conclusion, unioned with the kinds that enumerate their own keys), because a test that
    enumerated it some other way would be testing a package nobody generates.
    """
    from typehaus.checks import build_context, evaluate_permit_checklist, run_checks

    ctx, _ = build_context(catlin_plan, CATLIN)
    report = run_checks(ctx)
    named = {f.engineering_item for f in report.findings if f.engineering_item}
    item_ids = tuple(sorted(named | set(ctx.engineering)))
    checklist = evaluate_permit_checklist(report, ctx.profile)
    return ctx, item_ids, checklist


@pytest.fixture(scope="module")
def package(catlin_engineering):
    ctx, item_ids, checklist = catlin_engineering
    return calc_package(PackageInputs(
        house="catlin", model=ctx.model, item_ids=item_ids, results=ctx.engineering,
        register=ctx.engineering_register, generated=date(2026, 1, 1).isoformat(),
        engine_version="test", content_hash="deadbeefdeadbeef",
        profile_name=ctx.profile.name, checklist=checklist))


# --- the oracle lint (Phase 1d) ----------------------------------------------------------

def test_every_registered_kind_names_an_oracle_note_that_exists():
    """Every engineering kind is checked by a note, and every note named is on disk.

    Both halves matter. A kind with no oracle is a calculation that only agrees with
    itself. A kind naming a note that was renamed or deleted is worse — the package prints
    a reference a reviewer then cannot open, which reads as verification and is not.
    """
    notes_dir = CATLIN / "notes"
    missing_oracle = [kind for kind in registered_kinds() if not oracles_for(kind)]
    assert not missing_oracle, (
        f"these engineering kinds name no independently hand-worked note: "
        f"{missing_oracle}. Add one with `oracled_by(KIND, Oracle(note=...))`.")

    missing_files = sorted({
        oracle.note for kind in registered_kinds() for oracle in oracles_for(kind)
        if not (notes_dir / oracle.note).exists()})
    assert not missing_files, f"oracle notes named by a calc but absent on disk: {missing_files}"

    missing_tests = sorted({
        oracle.test for kind in registered_kinds() for oracle in oracles_for(kind)
        if oracle.test and not (REPO_ROOT / "packages" / "engine" / oracle.test).exists()})
    assert not missing_tests, f"oracle tests named by a calc but absent: {missing_tests}"


def test_a_record_carries_the_oracle_of_its_kind(catlin_engineering):
    """The stamp is applied to the records, not merely declared beside them.

    ``EngineeringResults._run`` puts the kind's oracle onto every record it produces, which
    is what keeps a calc module from having to thread the field through five constructors
    and forgetting one of them.
    """
    ctx, item_ids, _ = catlin_engineering
    unoracled = [i for i in item_ids if not ctx.engineering[i].oracle]
    assert not unoracled, unoracled


def test_the_nine_deferred_items_name_a_designer_of_record(catlin_engineering):
    """The items that exist by accident now exist on purpose.

    ``header/D-G-OVERHEAD``, ``lateral_uplift/RF-*`` and ``rafter/RF-*`` are computed by
    nothing and must stay that way; what changed is that each says *who* designs it. The
    summary must not fall back to the generic "no calculation is registered" sentence,
    which names nobody.
    """
    from typehaus.engineering.deferred import DEFERRALS

    ctx, item_ids, _ = catlin_engineering
    deferred = [ctx.engineering[i] for i in item_ids
                if ctx.engineering[i].status is Status.NO_CALC]
    # Seven since 2026-09-10: RF-BW-CANOPY, the north entry canopy, is three 24' gable
    # trusses -- a catalog component, deferred to the fabricator on exactly the same footing
    # as RF-GARAGE's. Its DRIFT case is what the fabricator must be told (see
    # notes/north_entry_piers.md §3 and preferences.toml [structural] roof_beam_snow_psf);
    # a quote against "50 psf ground snow" prices ordinary trusses.
    # Nine since 2026-09-11: `column_support/W-SG-W1` and `-E1` are the two wall tops
    # carrying the balcony's four fixed-base cast columns. Their base moments are computed
    # ON THE COLUMN by `deck_post` and land on concrete nothing in this engine grades —
    # the wall is answered prescriptively by a table with no surcharge column, and
    # `spread_footing` skips a shared wall footing. Named rather than silently absorbed.
    assert {r.item_id for r in deferred} == {
        "column_support/W-SG-E1", "column_support/W-SG-W1",
        "header/D-G-OVERHEAD",
        "lateral_uplift/RF-BW-CANOPY", "lateral_uplift/RF-GARAGE", "lateral_uplift/RF-HOUSE",
        "rafter/RF-BW-CANOPY", "rafter/RF-GARAGE", "rafter/RF-HOUSE"}
    for record in deferred:
        assert record.kind in DEFERRALS, record.item_id
        assert "no calculation is registered for this kind" not in record.summary
        assert DEFERRALS[record.kind].designer
        assert DEFERRALS[record.kind].deliverable
        assert DEFERRALS[record.kind].unblocks


# --- the package (Phase 2) ---------------------------------------------------------------

def test_every_item_gets_exactly_one_sheet_and_the_index_lists_it(package, catlin_engineering):
    _ctx, item_ids, _ = catlin_engineering
    sheets = {name for name in package if name.startswith("calcs/")}
    assert sheets == {f"calcs/{sheet_filename(i)}" for i in item_ids}
    assert len(sheets) == len(item_ids)
    readme = package["README.md"]
    for name in sorted(sheets):
        assert f"`{name}`" in readme, f"{name} is not listed in the index"


def test_the_front_matter_is_complete(package):
    assert set(package) >= {
        "README.md", "00-cover.md", "01-design-criteria.md", "02-item-register.md",
        "03-open-items.md", "04-assumptions.md"}
    assert "NOT FOR CONSTRUCTION" in package["00-cover.md"]
    assert "deadbeefdeadbeef" in package["00-cover.md"], "the model content hash is the "\
        "only thing on the cover that says which model this is a calculation for"


def test_every_sheet_carries_all_nine_sections(package):
    for name, text in package.items():
        if not name.startswith("calcs/"):
            continue
        for section in SECTIONS:
            assert section in text, f"{name} is missing {section}"
        assert text.index(SECTIONS[0]) < text.index(SECTIONS[-1]), name


def test_every_citation_on_a_record_reaches_its_references(package, catlin_engineering):
    """A citation a limit state rests on and the sheet does not print is a number the
    reviewer cannot place."""
    ctx, item_ids, _ = catlin_engineering
    for item in item_ids:
        record = ctx.engineering[item]
        text = package[f"calcs/{sheet_filename(item)}"]
        references = text.split("## 3. Given")[0]
        for state in record.limit_states:
            assert state.citation in references, f"{item}: {state.citation!r} missing"
        if record.basis:
            assert record.basis in references, item


def test_the_fingerprint_on_a_sheet_is_the_one_the_cli_prints(package, catlin_engineering):
    ctx, item_ids, _ = catlin_engineering
    for item in item_ids:
        record = ctx.engineering[item]
        text = package[f"calcs/{sheet_filename(item)}"]
        if record.status is Status.NO_CALC:
            # Nothing to hash, and the sheet has to say so rather than print a digest of
            # an empty input set that a seal could then be pinned against.
            assert "no inputs to fingerprint" in text, item
        else:
            assert f"`{fingerprint(record)}`" in text, item


def test_unfinished_items_reach_the_open_register_with_their_missing_text(
        package, catlin_engineering):
    ctx, item_ids, _ = catlin_engineering
    page = package["03-open-items.md"]
    for item in item_ids:
        record = ctx.engineering[item]
        if record.status in (Status.INCOMPLETE, Status.NO_CALC, Status.OVER):
            assert f"`{item}`" in page, item
        for text in record.missing:
            assert text in page, item


def test_the_negative_citation_survives_into_the_package(package):
    """``ESR-4729 does not cover this wall`` is the most load-bearing sentence in the
    board-and-batten note: it is why the panel item is open at all. A package that dropped
    it would read as though nobody had looked."""
    everything = "\n".join(package.values())
    assert "board-batten-24" in everything
    assert "published by no manufacturer at any spacing" in everything


def test_the_design_criteria_are_derived_and_not_typed(package):
    criteria = package["01-design-criteria.md"]
    for expected in ("V_ult", "115", "Exposure category", "B", "Risk category",
                     "p_g, ground snow load", "50", "GM", "0.85"):
        assert expected in criteria, expected


def test_the_package_is_byte_deterministic(catlin_engineering):
    ctx, item_ids, checklist = catlin_engineering

    def once():
        return calc_package(PackageInputs(
            house="catlin", model=ctx.model, item_ids=item_ids, results=ctx.engineering,
            register=ctx.engineering_register, generated="2026-01-01",
            engine_version="test", content_hash="deadbeefdeadbeef",
            profile_name=ctx.profile.name, checklist=checklist))

    assert once() == once()


def test_one_item_still_gets_the_front_matter(catlin_engineering):
    """``--item`` narrows the sheets and not the package. A single sheet with no criteria
    page behind it is not checkable."""
    ctx, item_ids, checklist = catlin_engineering
    only = "retaining_wall/W-SG-E2"
    files = calc_package(PackageInputs(
        house="catlin", model=ctx.model, item_ids=item_ids, results=ctx.engineering,
        register=ctx.engineering_register, generated="2026-01-01",
        profile_name=ctx.profile.name, checklist=checklist), only=only)
    assert [n for n in files if n.startswith("calcs/")] == [f"calcs/{sheet_filename(only)}"]
    assert "01-design-criteria.md" in files


# --- the seal gate (Phase 5a) -------------------------------------------------------------

def test_print_sealed_exits_one_while_nothing_is_sealed():
    """``--sealed`` was declared and never read.

    Until this was wired the flag silently printed an *unsealed* set — the drawings looked
    identical, and the one gate the submittal flag exists to hold was open. catlin carries
    no ``engineering.toml``, so every engineered line is unsealed and the command must
    refuse; the draft print below is what still has to work, because holding the printer
    hostage until a PE signs would make the engine useless for the months before one does.
    """
    from typer.testing import CliRunner

    from typehaus.cli.app import app

    runner = CliRunner()
    sealed = runner.invoke(app, ["print", str(CATLIN), "--sealed", "--fmt", "dxf"])
    assert sealed.exit_code == 1, sealed.output
    assert "sealed print blocked" in sealed.output
    assert "engineering --fingerprint" in sealed.output, (
        "the refusal has to say how to pin a seal, or it is a dead end")


def test_the_draft_gate_is_unmoved_by_the_seal_gate(catlin_engineering):
    """catlin reaches draft and does not reach sealed. Both halves are the point."""
    _ctx, _items, checklist = catlin_engineering
    assert checklist.ok, "the draft gate must stay open — catlin is held to a clean report"
    assert not checklist.sealed
    assert checklist.unsealed
