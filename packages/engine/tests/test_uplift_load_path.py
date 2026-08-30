"""The uplift load-path check (checks/structural/uplift_path.py).

The check's job is to be loud about a joint with no hardware, and its risk is being loud
about a joint that HAS hardware in a form it did not think to look for. Every false positive
it shipped with was of that kind, and each has a test here:

* a joist framed flush into its beam is connected by a **hanger**, not a tie;
* a cast column on a cast footing is connected by **reinforcement**, which this model does
  not carry, so the joint is not gradeable rather than broken;
* a beam bearing on a concrete column is connected by an authored **hurricane tie**, not
  only by the strap the derived rule would use;
* a post that never declares what it stands on is a **modelling gap**, not a break.

Those are why catlin reports 0 FAIL under this check, and why that number is worth pinning:
the reference house is held to a clean report by ``scripts/verify.sh``, so a regression in
any of the four takes the whole gate down with it.
"""

from __future__ import annotations

import pytest
from _helpers import check_context

from typehaus.checks.registry import Tier, registered
from typehaus.checks.structural.uplift_path import uplift_path_coverage
from typehaus.findings import Result


@pytest.fixture(scope="module")
def ctx(catlin_plan):
    return check_context(catlin_plan, profile=None)


@pytest.fixture(scope="module")
def findings(ctx):
    return uplift_path_coverage(ctx)


def test_the_check_is_registered_in_the_structural_tier() -> None:
    assert "structural.uplift_path_coverage" in {cid for cid, _ in registered(Tier.STRUCTURAL)}


def test_catlin_reports_no_break_in_the_load_path(findings) -> None:
    """The gate. ``scripts/verify.sh`` holds catlin to 0 FAIL across every check."""
    broken = [f.message for f in findings if f.result is Result.FAIL]
    assert not broken, broken


def test_a_covered_link_passes_and_says_where_the_capacity_question_went(findings) -> None:
    """Inverted on 2026-08-30, and the inversion is the point of the rename.

    This asserted that no link is EVER a PASS, on the reasoning that hardware being present
    is a different claim from the joint being adequate, and that a PASS would retire a
    question an engineer still has to answer (#64). The reasoning was right and the
    mechanism was wrong: it put that question at the end of 59 identical rows — the shape a
    reader scans past — and it spent the UNKNOWN column, which is supposed to mean "a real
    input is missing", on a scope disclaimer.

    The rule is now named ``structural.uplift_path_coverage``, so a covered joint is an
    honest PASS of the rule that actually ran, and every one of those PASSes still names
    where the capacity question lives. The test below is what keeps it from being retired.
    """
    assert findings
    covered = [f for f in findings if f.result is Result.PASS]
    assert covered
    assert all("[advisory, not engineering]" in f.message for f in findings)
    for finding in covered:
        assert "CAPACITY is not graded here" in finding.message
        assert "lateral_uplift/<roof>" in finding.message


def test_the_capacity_question_is_a_named_item_not_a_retired_one(ctx) -> None:
    """#64's concern, kept: folding coverage into a PASS must not retire the question.

    It is not retired; it is hoisted. One ENGINEERED item per roof, which a signoff in
    engineering.toml has to cover and which `haus engineering` lists until somebody does —
    two rows a reviewer must act on, rather than 59 they scroll past.
    """
    from typehaus.checks.structural.uplift_path import uplift_capacity_items
    from typehaus.findings import Authority

    items = uplift_capacity_items(ctx)
    assert {f.engineering_item for f in items} == {"lateral_uplift/RF-HOUSE",
                                                   "lateral_uplift/RF-GARAGE"}
    assert all(f.authority is Authority.ENGINEERED for f in items)
    # Still blocking, exactly as the UNKNOWNs it replaced were. Adopting the register moved
    # no gate; it only gave the outstanding work a name.
    assert all(f.result is Result.UNKNOWN for f in items)


def test_both_roofs_are_covered_at_their_bearings(findings) -> None:
    covered = {f.element_tags[0]: f for f in findings if f.result is Result.PASS}
    for roof in ("RF-HOUSE", "RF-GARAGE"):
        assert "derived uplift ties" in covered[roof].message, roof


def test_a_flush_framed_deck_is_covered_by_its_hangers(findings) -> None:
    """FS-BW-FLOOR's four 2x8 joists sit IN their beams, so no tie can be derived for them.

    Before hangers counted, this floor was the check's loudest false positive: every one of
    its joist ends carries a LUS hanger and the report called it a break in the load path.
    """
    deck = next(f for f in findings if f.element_tags[:1] == ("FS-BW-FLOOR",))
    assert deck.result is Result.PASS
    assert "hangers" in deck.message


def test_a_cast_column_is_not_evaluable_rather_than_broken(findings) -> None:
    """A concrete column on a concrete footing is doweled; there is no connector to miss.

    Grading it against a wood post base reported a break at a joint that has none — and
    handed the reader an ABU that does not fit a 12" round pour.

    There are SIX of these, not the two the sunken garden's columns make: the four breezeway
    sonotube piers are the same joint. The message has to say two things and the assertions
    pin both — that the connection is a doweled lap, and that the steel making it is inside
    the column's own $/cy rate rather than missing from the order. A reader who takes
    "carries no rebar" as "unpriced scope" goes looking for money that is already there.
    """
    for column in ("PT-SG-COL", "PT-SG-FCOL", "PR-BW-1", "PR-BW-4"):
        finding = next(f for f in findings
                       if f.element_tags[:1] == (column,)
                       and "outside what a connector-coverage rule governs" in f.message)
        # N/A since 2026-08-30, not UNKNOWN, and it is earned: the joint is a doweled lap
        # into the column's own cage, so it has no connector by design and never will. A
        # connector-coverage rule does not govern it — a verdict about the building rather
        # than a confession that an input is missing. `Link.not_governed` is the field that
        # keeps this apart from `not_evaluable`, which is still UNKNOWN (see the undeclared
        # -bearing test below).
        assert finding.result is Result.NOT_APPLICABLE
        assert "doweled lap" in finding.message, column
        assert "$/cy rate" in finding.message, column


def test_the_stairwell_posts_are_graded_now_that_they_declare_a_bearing(findings) -> None:
    """These were the check's three un-gradeable posts until 2026-08-28.

    All three always stood on something — the slab under the two columns, W-B-CN under the
    landing block — and their own comment said so in prose while ``supported_by`` sat empty.
    Filling it in is what closed the item, and it split the three two ways: the columns take
    a derived ABU44, the 13 7/16" block takes nothing because it is not a column.
    """
    graded = {f.element_tags[0]: f for f in findings}
    for column in ("P-M-STRWELL-S", "P-M-STRWELL-N"):
        assert "derived standoff post base" in graded[column].message, column
        assert graded[column].result is Result.PASS
    block = graded["P-M-STRLAND-SE"]
    assert block.result is Result.PASS
    assert "squash block" in block.message
    assert "post base" not in block.message, \
        "a block bears; buying it a base is the error blocking_max_height_ft prevents"
    assert not [f for f in findings if "declares no `supported_by`" in f.message], \
        "nothing in catlin is un-gradeable for want of a bearing any more"


def test_an_undeclared_bearing_is_still_reported_as_un_gradeable(ctx) -> None:
    """The tri-state branch must stay alive now that no real post exercises it.

    Closing the last un-gradeable post in the house left this code path with no witness, and
    an untested branch is one refactor from reporting a modelling gap as a FAIL — which
    would exit ``haus check`` 1 over an omission, the exact thing the tri-state is for (#32).
    So strip the bearing back off one post and confirm the branch still answers.
    """
    from typehaus.model.structure import Post

    posts = [e for e in ctx.plan.all_elements()
             if isinstance(e, Post) and e.tag == "P-M-STRWELL-S"]
    stripped = posts[0].model_copy(update={"supported_by": None})
    by_tag = {e.tag: e for e in ctx.plan.all_elements()}
    by_tag["P-M-STRWELL-S"] = stripped

    class _Plan:
        def __init__(self, real):
            self._real = real

        def all_elements(self):
            return list(by_tag.values())

        def __getattr__(self, name):
            return getattr(self._real, name)

    gapped = type(ctx)(plan=_Plan(ctx.plan), model=ctx.model, preferences=ctx.preferences,
                       profile=ctx.profile, resolve_findings=ctx.resolve_findings)
    finding = next(f for f in uplift_path_coverage(gapped)
                   if f.element_tags[:1] == ("P-M-STRWELL-S",))
    # Still UNKNOWN, and this is the line that shows the N/A above was earned rather than
    # applied to everything the rule cannot grade: a post that never says what it stands on
    # is a hole in the model somebody can fill, not a joint outside the rule's scope.
    assert finding.result is Result.UNKNOWN, "a modelling gap is never a FAIL"
    assert "declares no `supported_by`" in finding.message


def test_an_authored_hurricane_tie_connects_a_beam_to_its_column(findings) -> None:
    """``CN-SG-TIE-COL`` / ``CN-SG-TIE-FCOL`` are the uplift connection at the two columns.

    They are HURRICANE_TIE, not HOLD_DOWN. A check that only recognised straps and caps
    reported all four of these beam ends as breaks while the plan had already modelled them.
    """
    for beam, column in (("BM-SG-BKW", "PT-SG-COL"), ("BM-SG-BKE", "PT-SG-COL"),
                         ("BM-SG-FRW", "PT-SG-FCOL"), ("BM-SG-FRE", "PT-SG-FCOL")):
        finding = next(f for f in findings if f.element_tags == (beam, column))
        assert finding.result is Result.PASS
        assert "an authored strap or cap" in finding.message


def test_an_authored_strap_is_not_credited_to_a_neighbouring_beam(findings) -> None:
    """The breezeway straps its two ROOF beams to PT-BW-1..4; the FLOOR beams are separate.

    Matching an authored connector on either tag alone handed ``CN-BW-KBS-*`` to
    ``BM-BW-FW``/``FE``, which land on the same four posts and carry none of those straps.
    That is why the guard keys on the tag PAIR, and why the four floor-beam joints must read
    as *derived* rather than authored.
    """
    for beam in ("BM-BW-RW", "BM-BW-RE"):
        roof = [f for f in findings if f.element_tags[:1] == (beam,)]
        assert roof and all("an authored strap or cap" in f.message for f in roof)
    for beam in ("BM-BW-FW", "BM-BW-FE"):
        floor = [f for f in findings if f.element_tags[:1] == (beam,)]
        assert floor and all("a derived KBS1Z strap" in f.message for f in floor)


def test_the_sill_and_the_stacked_walls_are_both_reported(findings) -> None:
    """Links 3 and 4 — the two joints between a wall and whatever is under it."""
    messages = [f.message for f in findings]
    assert any("MASA mudsill anchors" in m for m in messages)
    assert any("CS16 strapping" in m for m in messages)


def test_a_broken_joint_really_does_fail(ctx) -> None:
    """The check must still bite. Strip catlin's roof of its bearing declaration and it does.

    Without this, every assertion above is satisfied by a check that returns UNKNOWN for
    everything, and the file would pass while grading nothing.
    """
    roof = next(e for e in ctx.plan.all_elements() if e.tag == "RF-HOUSE")
    stripped = roof.model_copy(update={"bearing_refs": ()})
    by_tag = {e.tag: e for e in ctx.plan.all_elements()}
    by_tag["RF-HOUSE"] = stripped

    class _Plan:
        """The real plan, with ``all_elements`` swapped. Everything else delegates.

        A hand-rolled stand-in is not enough here: ``_is_concrete`` reaches through the plan
        to the assembly library to tell a cast column from a wood post, and a stub without
        one made the check raise instead of grading.
        """

        def __init__(self, real):
            self._real = real

        def all_elements(self):
            return list(by_tag.values())

        def __getattr__(self, name):
            return getattr(self._real, name)

    broken_ctx = type(ctx)(plan=_Plan(ctx.plan), model=ctx.model,
                           preferences=ctx.preferences, profile=ctx.profile,
                           resolve_findings=ctx.resolve_findings)
    failed = [f for f in uplift_path_coverage(broken_ctx) if f.result is Result.FAIL]
    assert [f for f in failed if "RF-HOUSE" in f.element_tags], \
        "a roof that declares no bearing has no derivable tie and must FAIL"
