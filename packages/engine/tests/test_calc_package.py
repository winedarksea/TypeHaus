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
from typehaus.findings import Result
from typehaus.takeoff.calc_family import family_filename
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

#: A FAMILY calculation's own order. The first two and the last three are deliberately the
#: same words as a sheet's — a reviewer moving between the calculation and the appendix
#: behind it should not be learning a second vocabulary — and the three in the middle are
#: what makes it a calculation over a family rather than over one member.
FAMILY_SECTIONS = (
    "## 1. Scope",
    "## 2. References",
    "## 3. Member schedule",
    "## 4. The calculation, worked at the governing member",
    "## 5. Result",
    "## 6. Assumptions and exclusions",
    "## 7. Open inputs",
    "## 8. Independent check",
    "## 9. What this calculation does not cover",
    "## 10. Per-member fingerprints",
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

    # A note that opens with a superseded banner is an archive. It still exists, so the
    # two checks above pass, and the package would print it as though it verified the calc.
    superseded = sorted({
        oracle.note for kind in registered_kinds() for oracle in oracles_for(kind)
        if "superseded" in "\n".join(
            (notes_dir / oracle.note).read_text(encoding="utf-8").splitlines()[:5]).lower()})
    assert not superseded, (
        f"these oracle notes are archived (a 'Superseded' banner in their first five "
        f"lines) and cannot verify a live calc: {superseded}")


def test_a_record_carries_the_oracle_of_its_kind(catlin_engineering):
    """The stamp is applied to the records, not merely declared beside them.

    ``EngineeringResults._run`` puts the kind's oracle onto every record it produces, which
    is what keeps a calc module from having to thread the field through five constructors
    and forgetting one of them.
    """
    ctx, item_ids, _ = catlin_engineering
    unoracled = [i for i in item_ids if not ctx.engineering[i].oracle]
    assert not unoracled, unoracled


def test_the_four_deferred_items_name_a_designer_of_record(catlin_engineering):
    """The items that exist by accident now exist on purpose.

    The two trussed roofs' ``rafter/*`` and the two ``column_support`` wall tops are
    computed by nothing and must stay that way; what changed is that each says *who*
    designs it. The summary must not fall back to the
    generic "no calculation is registered" sentence, which names nobody.
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
    # Seven since 2026-09-11, down from nine: `header/D-G-OVERHEAD` and `rafter/RF-HOUSE`
    # both LEFT the deferred lane. Neither was stamped — both turned out to be answered by
    # a manufacturer's published table (Weyerhaeuser's header schedule, and TJ-4000's
    # horizontal clear spans for the I-joist), and reading a published row is a prescriptive
    # act. They are graded by `checks/structural/published.py` against a `PublishedSpan`
    # authored on the element. The trussed roofs stay: no member exists for a table to
    # describe.
    # ** FOUR SINCE 2026-09-14, DOWN FROM SEVEN: the whole ``lateral_uplift`` kind went. **
    # It carried one item per roof and none of the three needed a seal. A rafter-framed roof
    # reads IRC Table R802.11 for the uplift demand and the connector's published allowable
    # for the capacity — two table reads compared, which is a prescriptive act on exactly
    # the footing the header and the I-joist span above took. A TRUSSED roof has no R802.11
    # row at all (the table is indexed by a span and spacing this engine cannot read off a
    # roof it did not frame) and folded into ``rafter/<tag>``, whose fabricator publishes the
    # uplift reactions as part of the component design they were already sealing. That
    # deferral's own `deliverable` now says so.
    # ** FOURTEEN SINCE 2026-09-14, UP FROM FOUR: the sunken garden's three silent gaps. **
    # None of the ten new items is new WORK — every one of them was already undesigned, and
    # every one was invisible, which reads exactly like a thing with no problem.
    #  - `veneer_beam/W-SG-BRKBM`: a cast beam carrying a masonry wythe. It had a screening
    #    calculation and no record, because that calculation is a free function writing a
    #    report — it reads no plan and nothing can be sealed against it. REGISTERED on
    #    2026-09-20 (`engineering/veneer_beam.py`); the masonry anchors it carried unnamed
    #    left with it as `veneer_anchor/W-B-BRICK`, their own deferral.
    #  - `thermal_break_transfer/DW-*`: left 2026-09-20 — computed as a reserve in
    #    `engineering/thermal_break.py`, INCOMPLETE until a measured soil modulus exists.
    #  - `tiered_retaining/W-RG-*`: the apron. `foundation_unbalanced_fill` reads PASS on it
    #    and that verdict is CORRECT — IRC R404.1.1 does not engage at 3'-4" — so the PASS is
    #    deliberately left alone. The defect was that nothing else then looked at a tiered
    #    segmental wall standing beside a ten-foot cut. COMPUTED since 2026-09-20
    #    (`engineering/segmental_wall.py`, OVER) and so off this list: five fewer.
    # `_retaining_walls` is deliberately NOT widened to reach the apron: an
    # isolated-cantilever record for a wall whose whole problem is that it is not isolated
    # would make the register less true.
    # ** TWENTY-SIX SINCE 2026-09-18, UP FROM FOURTEEN: what `column_base` left open. **
    # `engineering/column_base.py` grades the EMBEDMENT a fixed column base needs, which
    # was the assumption every `deck_post` record named and none graded. Grading it turned
    # three other assumptions from unmentioned into mentioned-and-still-ungraded, and an
    # assumption that has become visible belongs on a register rather than in a docstring.
    #  - `base_rotation/PT-BW-*`: the base is graded for STRENGTH (can the ground turn the
    #    shear around) and not for STIFFNESS. `deck_post`'s sway magnifier assumes a base
    #    that does not rotate; a real one does, and the split of moment between the buried
    #    shaft and the pad under it is the same question from the other side. Six items,
    #    one per column `column_base` grades — one set, one definition.
    #    ** LEFT 2026-09-20: `engineering/base_rotation.py` computes it, on a presumptive
    #    soil band, for these six and the balcony's four wall-borne columns. **
    #  - `column_head_joint/PT-*`: what a fixed-base column is fixed AGAINST at its head.
    #    catlin's canopy columns carry `BM-BW-RE` on a stainless standoff pack under an
    #    `HGAM10` gusset, a detail chosen for durability whose MOMENT transfer nobody has
    #    computed. Column shear and torsion ride with it. Ten items — every cast column
    #    that is a lateral system, the balcony's four included.
    # `column_support/W-SG-W1`/`-E1` LEFT on 2026-09-20: computed by
    # `engineering/column_support.py`, oracled by balcony_moment_columns.md §11.
    assert {r.item_id for r in deferred} == {
        # `base_rotation/*`, `column_head_joint/*` and `column_support/*` left on 2026-09-20:
        # each is a registered calculation now.
        "rafter/RF-BW-CANOPY", "rafter/RF-GARAGE",
        "veneer_anchor/W-B-BRICK"}
    for record in deferred:
        assert record.kind in DEFERRALS, record.item_id
        assert "no calculation is registered for this kind" not in record.summary
        assert DEFERRALS[record.kind].designer
        assert DEFERRALS[record.kind].deliverable
        assert DEFERRALS[record.kind].unblocks


# --- the package (Phase 2) ---------------------------------------------------------------

def test_every_item_gets_exactly_one_sheet_and_the_index_lists_it(package, catlin_engineering):
    """One appendix sheet per item, and one calculation per design FAMILY in front of it.

    The package led with one nine-section sheet per item until 2026-09-18 — twelve copies
    of ACI 318-19 §22.4.2.1 for twelve cast columns. The per-member data is all still here;
    it is behind the calculation that reads it, and the calculations are what the README
    indexes.
    """
    ctx, item_ids, _ = catlin_engineering
    sheets = {name for name in package if name.startswith("appendix/")}
    assert sheets == {f"appendix/{sheet_filename(i)}" for i in item_ids}
    assert len(sheets) == len(item_ids)

    kinds = {ctx.engineering[i].kind for i in item_ids}
    calculations = {name for name in package if name.startswith("calcs/")}
    assert calculations == {f"calcs/{family_filename(kind)}" for kind in kinds}
    readme = package["README.md"]
    for name in sorted(calculations):
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
        if not name.startswith("appendix/"):
            continue
        for section in SECTIONS:
            assert section in text, f"{name} is missing {section}"
        assert text.index(SECTIONS[0]) < text.index(SECTIONS[-1]), name


def test_every_family_calculation_carries_its_own_sections_in_order(package):
    """And a schedule with a row for every member, which is the point of the restructure."""
    calculations = [n for n in package if n.startswith("calcs/")]
    assert calculations, "the package has no family calculation"
    for name in calculations:
        text = package[name]
        positions = []
        for section in FAMILY_SECTIONS:
            assert section in text, f"{name} is missing {section}"
            positions.append(text.index(section))
        assert positions == sorted(positions), f"{name}'s sections are out of order"
        schedule = text.split("## 3. Member schedule")[1].split("## 4.")[0]
        assert "| Member |" in schedule
        assert "appendix/" in schedule, f"{name} does not point at its per-member data"


def test_every_citation_on_a_record_reaches_its_references(package, catlin_engineering):
    """A citation a limit state rests on and the sheet does not print is a number the
    reviewer cannot place."""
    ctx, item_ids, _ = catlin_engineering
    for item in item_ids:
        record = ctx.engineering[item]
        text = package[f"appendix/{sheet_filename(item)}"]
        references = text.split("## 3. Given")[0]
        for state in record.limit_states:
            assert state.citation in references, f"{item}: {state.citation!r} missing"
        if record.basis:
            assert record.basis in references, item


def test_the_fingerprint_on_a_sheet_is_the_one_the_cli_prints(package, catlin_engineering):
    ctx, item_ids, _ = catlin_engineering
    for item in item_ids:
        record = ctx.engineering[item]
        text = package[f"appendix/{sheet_filename(item)}"]
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


def test_the_manufacturers_own_exclusion_survives_into_the_package(package):
    """The most load-bearing sentence behind the cladding item is the panel maker's own.

    Metal Sales publishes a bending allowable and says in the same note that it "does not
    address web crippling, fasteners, support material" — which is why withdrawal is
    computed here from NDS rather than read from a table, and why a reviewer has to see
    that exclusion rather than take the 58 psf as the whole answer. A package that dropped
    it would read as though the published number covered the governing limit state."""
    everything = "\n".join(package.values())
    assert "board-batten-24" in everything
    assert "does not address web crippling, fasteners, support material" in everything


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
    assert ([n for n in files if n.startswith("appendix/")]
            == [f"appendix/{sheet_filename(only)}"])
    assert ([n for n in files if n.startswith("calcs/")]
            == [f"calcs/{family_filename('retaining_wall')}"]), \
        "narrowing to one item narrows its family calculation to that one member too"
    assert "01-design-criteria.md" in files


# --- the seal gate (Phase 5a) -------------------------------------------------------------

def test_print_sealed_exits_one_while_nothing_is_sealed(catlin_engineering):
    """``--sealed`` was declared and never read.

    Until this was wired the flag silently printed an *unsealed* set — the drawings looked
    identical, and the one gate the submittal flag exists to hold was open. catlin carries
    no ``engineering.toml``, so every engineered line is unsealed and the command must
    refuse; the draft print below is what still has to work, because holding the printer
    hostage until a PE signs would make the engine useless for the months before one does.

    ** THE DRAFT GATE CLOSED IN FRONT OF IT FROM 2026-09-18 TO 2026-09-20, AND THIS TEST
    NEARLY WENT VACUOUS BECAUSE OF IT. ** While catlin's column bases were open `haus print`
    refused before `--sealed` was ever consulted — correct ordering (there is no point asking
    for a stamp on a set that does not reach draft), and a refusal this test could have
    mistaken for its own subject. `notes/entry_column_base_fixity.md` §6a and §6e closed
    both bases, so the draft gate opens and the message asserted below is the SEALED one, on
    its own wording. That it says "sealed print blocked" and not "permit print blocked" is
    the assertion: it proves the second gate is what refused.
    """
    from typer.testing import CliRunner

    from typehaus.cli.app import app

    # ** AND IT CLOSED AGAIN ON 2026-09-20, for five named engineering lines (see the test
    # below), so the refusal here is the DRAFT gate's — correct ordering. The second gate's
    # own refusal is pinned at the checklist level below until catlin reaches draft again;
    # re-tighten this to "sealed print blocked" the day it does.
    runner = CliRunner()
    sealed = runner.invoke(app, ["print", str(CATLIN), "--sealed", "--fmt", "dxf"])
    assert sealed.exit_code == 1, sealed.output
    assert "print blocked" in sealed.output

    # The shared fixture's checklist, not a second full run of the house — see
    # `test_catlin_fixture_discipline`, which lints exactly that.
    _ctx, _items, checklist = catlin_engineering
    assert not checklist.sealed, "no engineering.toml exists, so nothing is sealed"
    assert checklist.unsealed


def test_the_two_gates_are_separate_and_catlin_reaches_neither(catlin_engineering):
    """The gates are independent, and catlin is the house that proves it by reaching one.

    It reached draft and not sealed until 2026-09-18, missed BOTH for two days while
    `engineering/column_base.py` graded an embedment its north entry did not have, and
    reaches draft again since 2026-09-20 — `notes/entry_column_base_fixity.md` §6a put the
    canopy pair on one plane at -10'-2" and §6e claimed §1806.3.4's doubling for the landing
    pair. **The blocked list is asserted EMPTY rather than deleted**, the way the FAIL sets in
    `test_lateral_racking.py` are: a blocking line silently going red is exactly what this
    assertion is here to notice.

    The separation is what the pair below pins: `sealed` is false for a reason that has
    nothing to do with any calculation — catlin carries no `engineering.toml` at all — so it
    stays false with every draft line green, and it would have stayed false with them red.

    ** AND MISSES DRAFT AGAIN SINCE 2026-09-20, ON FIVE NAMED LINES. ** Every deferred kind
    became a registered calculation and its line blocks; the five below are what those
    calculations found open on catlin (`haus engineering`). The set is pinned exactly, so a
    sixth line going red, or one of these closing unnoticed, fails here.
    """
    _ctx, _items, checklist = catlin_engineering
    blocked = [item.label for item in checklist.items
               if item.blocking and item.result not in (Result.PASS,
                                                        Result.NOT_APPLICABLE)]
    # 2026-09-21: the landing's tie to the garage stem closed the head-joint line and opened
    # its own (deck_tie/FS-BW-FLOOR OVER 1.82, notes/north_entry_piers.md §10).
    assert sorted(blocked) == sorted([
        "Fixed column base rotation (stiffness and sway)",
        "Deck lateral tie to a concrete wall",
        "Cast beam carrying a masonry veneer",
        "Structural ties across a thermal break",
        "Segmental gravity retaining walls (tiered)",
    ]), blocked
    assert not checklist.ok
    assert not checklist.sealed
    assert checklist.unsealed
    # Shut for its own reason: every engineered item is unsealed because the house carries
    # no register at all, which is true of the passing items as much as the failing one.
    assert len(checklist.unsealed) > 1
