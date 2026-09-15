"""``mep.drain_tie_in`` — a branch has to land ON the pipe it joins, not under it.

The failure this replaces was silent: ``drain_tie_ins`` dropped a rejected arrival, the run
left the load graph, and ``mep.pipe_sizing`` sized the pipe downstream for a load with
rooms missing from it — with no finding anywhere in the report.
"""

from __future__ import annotations

from _helpers import check_context

from typehaus.checks.mep.drain_tie_in import drain_tie_in
from typehaus.findings import Result, Severity
from typehaus.quantities import M_PER_IN
from typehaus.resolve.mep_queries import accumulated_serves
from typehaus.resolve.mep_tie_ins import drain_tie_in_records, drain_tie_ins

_CID = "mep.drain_tie_in"


def _drains(model):
    return [r for r in model.pipe_runs if r.system == "drain"]


def test_catlin_is_clean(catlin_plan, catlin_model_ro) -> None:
    findings = drain_tie_in(check_context(plan=catlin_plan, model=catlin_model_ro))
    fails = [f for f in findings if f.result is Result.FAIL]
    assert not fails, [f.message for f in fails]
    assert len(findings) == 29


def test_the_five_that_tie_into_nothing_are_not_graded(catlin_model_ro) -> None:
    """Two sleeves, a receptor and two air gaps are terminations, not rejected junctions —
    reporting them would be reporting the building for being a building."""
    records = drain_tie_in_records(_drains(catlin_model_ro))
    orphans = {tie.child for tie in records if tie.parent is None}
    assert orphans == {
        "PR-B-MAIN-DRAIN", "PR-B-ERV-COND", "PR-B-WH-TPR", "PR-M-DRYER-COND",
        "PR-SG-ARCH-OVERFLOW",
    }
    assert all(tie.drop_m is None for tie in records if tie.parent is None)


def test_the_projection_is_faithful(catlin_model_ro) -> None:
    """``drain_tie_ins`` keeps its signature and its answer; only the rejections escape."""
    drains = _drains(catlin_model_ro)
    records = drain_tie_in_records(drains)
    assert drain_tie_ins(drains) == {t.child: t.parent for t in records
                                     if t.accepted and t.parent is not None}


def test_the_epsilon_is_a_thirty_second_not_zero(catlin_plan, catlin_model_ro) -> None:
    """**The assertion that stops a float from becoming a finding.**

    ``PR-B-SAUNA-FD-DROP`` arrives -0.00025" below its collector. That is the last bit of
    the interpolation, not geometry, and grading at ``< 0`` would report it.
    """
    records = {t.child: t for t in drain_tie_in_records(_drains(catlin_model_ro))}
    drop_in = records["PR-B-SAUNA-FD-DROP"].drop_m / M_PER_IN
    assert -1.0 / 32.0 < drop_in < 0.0, drop_in

    findings = drain_tie_in(check_context(plan=catlin_plan, model=catlin_model_ro))
    finding = next(f for f in findings if "PR-B-SAUNA-FD-DROP" in f.element_tags)
    assert finding.result is Result.PASS
    assert "on its centreline" in finding.message


def test_a_regressed_tie_in_makes_the_rollup_shrink(catlin_plan, catlin_model_ro) -> None:
    """**The assertion that ties this check to the defect it exists to prevent.**

    Drop a branch below its collector and the fixtures upstream of it stop counting toward
    the collector's load. That is the silent under-sizing; the FAIL is what makes it loud,
    and the message has to name the load that went missing.
    """
    import copy

    model = copy.copy(catlin_model_ro)
    runs = list(model.pipe_runs)
    index, child = next((i, r) for i, r in enumerate(runs)
                        if r.tag == "PR-B-BATH-DRAIN")
    sunk = copy.copy(child)
    # 6" under the main it joins — well past the 1" the load rollup tolerates.
    object.__setattr__(sunk, "z_m", [*child.z_m[:-1], child.z_m[-1] - 6 * M_PER_IN])
    runs[index] = sunk
    object.__setattr__(model, "pipe_runs", tuple(runs))

    before = accumulated_serves(_drains(catlin_model_ro))["PR-B-MAIN-DRAIN"]
    after = accumulated_serves(_drains(model))["PR-B-MAIN-DRAIN"]
    assert set(after) < set(before), "the rollup must SHRINK when a tie-in is rejected"
    lost = set(before) - set(after)
    assert lost

    findings = drain_tie_in(check_context(plan=catlin_plan, model=model))
    fail = next(f for f in findings
                if "PR-B-BATH-DRAIN" in f.element_tags and f.result is Result.FAIL)
    assert fail.severity is Severity.ERROR
    assert "BELOW its centreline" in fail.message
    assert "mep.pipe_sizing" in fail.message
    # The fixtures that fell off the rollup are named, not merely counted.
    for tag in lost:
        assert tag in fail.message, tag


def test_an_accepted_but_low_entry_is_an_advisory_fail(
        catlin_plan, catlin_model_ro) -> None:
    """One id, mixed severity — the ``mep.wet_wall_occupancy`` precedent. It flows and the
    rollup keeps it, so it must not carry ERROR and trip the permit gate."""
    import copy

    model = copy.copy(catlin_model_ro)
    runs = list(model.pipe_runs)
    index, child = next((i, r) for i, r in enumerate(runs) if r.tag == "PR-B-BATH-DRAIN")
    sunk = copy.copy(child)
    # A quarter inch under: inside the 1" the rollup tolerates, so still accepted.
    object.__setattr__(sunk, "z_m", [*child.z_m[:-1], child.z_m[-1] - 0.25 * M_PER_IN])
    runs[index] = sunk
    object.__setattr__(model, "pipe_runs", tuple(runs))

    assert "PR-B-BATH-DRAIN" in drain_tie_ins(_drains(model)), "must still tie in"
    findings = drain_tie_in(check_context(plan=catlin_plan, model=model))
    finding = next(f for f in findings if "PR-B-BATH-DRAIN" in f.element_tags)
    assert finding.result is Result.FAIL
    assert finding.severity is Severity.WARN
    assert "below its centreline" in finding.message


def test_no_drains_is_not_applicable(catlin_plan, catlin_model_ro) -> None:
    """N/A is earned from positive evidence of absence."""
    import copy

    model = copy.copy(catlin_model_ro)
    object.__setattr__(model, "pipe_runs",
                       tuple(r for r in model.pipe_runs if r.system != "drain"))
    findings = drain_tie_in(check_context(plan=catlin_plan, model=model))
    assert len(findings) == 1
    assert findings[0].result is Result.NOT_APPLICABLE


def test_it_cites_chapter_4714_not_the_irc(catlin_plan, catlin_model_ro) -> None:
    findings = drain_tie_in(check_context(plan=catlin_plan, model=catlin_model_ro))
    for finding in findings:
        assert finding.code_ref == "MN Plumbing Code (ch. 4714) 706.3"


def test_it_joins_the_existing_permit_item_rather_than_adding_one() -> None:
    """One edit, not three: a new label would need a staging entry and a
    ``MAX_NON_BLOCKING_ITEMS`` bump — a ratchet moving the wrong way for no gain."""
    from typehaus.checks.code.mn_residential.profile import get_profile

    profile = get_profile("mn-2020")
    items = [i for i in profile.permit_items if _CID in i.check_ids]
    assert len(items) == 1
    assert items[0].label == "Plumbing drain slope and offsets"
    assert items[0].blocking
    assert "mep.drain_slope" in items[0].check_ids
