"""``integrity.edge_run_host`` — the trim run's host_ref, which nothing else reads.

``resolve/accessories.py`` builds every edge run from its own ``path`` and
``top_elevation``. ``host_ref`` is never opened, so it can name a retired element or one on
the far side of the building and the run still draws, bills and passes.

These tests are driven off the reference house rather than a synthetic plan, because the
whole difficulty of this check is the three legitimate families that a naive "the run sits
on its host's top" rule fails — a tilted beam, a roof with no solid, and a gutter deliberately
3" below its fascia. Those exist in catlin and are awkward to fake convincingly.
"""

from __future__ import annotations

import pytest

from typehaus.checks import run_from_model
from typehaus.checks.integrity.edge_run_host import _RUN_KINDS, _top_range
from typehaus.findings import Result
from typehaus.quantities import M_PER_IN

_CHECK_ID = "integrity.edge_run_host"


@pytest.fixture(scope="module")
def findings(catlin_model_ro):
    return [f for f in run_from_model(catlin_model_ro, [], only=_CHECK_ID).findings
            if f.check_id == _CHECK_ID]


def test_the_run_kinds_are_every_edge_run_subclass() -> None:
    """The list is named, not discovered, so a new trim family is a deliberate decision to
    cover. This is the lint that makes that safe rather than merely tidy."""
    from typehaus.model.trim import _EdgeRun

    def subclasses(cls):
        for sub in cls.__subclasses__():
            yield sub.__name__
            yield from subclasses(sub)

    assert set(_RUN_KINDS) == set(subclasses(_EdgeRun))


def test_catlin_has_no_stale_host_reference(findings) -> None:
    """No FAIL: every hosted run in the reference house follows what it names."""
    assert not [f for f in findings if f.result is Result.FAIL], [
        f.message for f in findings if f.result is Result.FAIL]


def test_a_floor_system_host_is_unknown_and_says_why(findings) -> None:
    """FS-SG-DECK and FS-SG-PORCH resolve to no solid AND a zero-point outline.

    Three runs name them. Silently skipping those would make the check quietly narrower
    than it reads — the honest answer is that the model cannot say, and the missing
    geometry is a real finding about the model either way.
    """
    unknowns = [f for f in findings if f.result is Result.UNKNOWN]
    assert {f.element_tags[0] for f in unknowns} == {
        "TR-SG-FASCIA", "TR-SG-SLOT", "TR-SG-WRB-FLASH"}
    assert all("resolves to no solid" in f.message for f in unknowns)


def test_a_tilted_beam_is_graded_over_its_range_not_its_box(catlin_model_ro) -> None:
    """The false FAIL the obvious rule produces, pinned as numbers.

    BM-SG-BLW carries top_rise_end, so its solid is swept and the bounding z1_m is the HIGH
    end. A flat _EdgeRun at the LOW end (TR-SG-CAP-BLW, until the balcony caps were dropped
    2026-09-16) is where it belongs, and against the box that was a 2.4" false FAIL.
    """
    beam = next(s for s in catlin_model_ro.solids if s.tag == "BM-SG-BLW")
    low, high = _top_range(beam)
    assert high == pytest.approx(beam.z1_m)
    assert (high - low) / M_PER_IN == pytest.approx(2.42, abs=0.05)


def _catlin_with_a_cap_on(catlin_plan, host: str, top_in: float):
    """Catlin plus one cap flashing laid along ``host``'s axis at ``top_in`` inches.

    Built rather than read: the porch beams whose caps this test used to grade were
    retired with the centre support line (2026-09), and no level beam in the house carries
    a hosted run any more. The ledger BM-SG-LDGW is level and still there.
    """
    from typehaus.model import inch
    from typehaus.model.trim import Flashing

    beam = catlin_plan.by_tag(host)
    storey = next(tag for tag, items in catlin_plan.elements.items()
                  if any(getattr(e, "tag", None) == host for e in items))
    start, end = (catlin_plan.by_tag(beam.start_node), catlin_plan.by_tag(beam.end_node))
    cap = Flashing(uid="TRCAPTEST1", tag="TR-TEST-CAP", host_ref=host,
                   path=(start.position, end.position),
                   top_elevation=inch(top_in), depth=inch(4), thickness=inch(1))
    return catlin_plan.with_elements(storey, (*catlin_plan.elements[storey], cap))


def test_a_level_beam_still_gets_a_tight_test(catlin_plan, catlin_model_ro) -> None:
    """The range only opens by however far the host is out of level.

    BM-SG-LDGW is level, so its range collapses to a single value and a cap on it has to
    match exactly — the tilt allowance is not a blanket loosening. A cap at the ledger top
    passes; the same cap 2" up (past the 1" drafting slop) FAILs.
    """
    from typehaus.resolve import resolve

    beam = next(s for s in catlin_model_ro.solids if s.tag == "BM-SG-LDGW")
    low, high = _top_range(beam)
    assert low == pytest.approx(high)

    def verdicts(top_in: float):
        model, resolve_findings = resolve(_catlin_with_a_cap_on(
            catlin_plan, "BM-SG-LDGW", top_in))
        return [f.result for f in run_from_model(model, resolve_findings, only=_CHECK_ID).findings
                if f.check_id == _CHECK_ID and "TR-TEST-CAP" in f.element_tags]

    on_top = high / M_PER_IN
    assert Result.FAIL not in verdicts(on_top)
    assert verdicts(on_top + 2.0) == [Result.FAIL]


def test_the_gutter_hangs_below_its_fascia_and_that_is_not_a_defect(findings) -> None:
    """TR-SG-GUTTER names TR-SG-FASCIA and is authored 3" below it, on purpose.

    An _EdgeRun host is graded in plan only for exactly this reason. A rule that compared
    elevations would report the one thing a gutter is supposed to do.
    """
    assert not [f for f in findings
                if f.result is Result.FAIL and "TR-SG-GUTTER" in f.element_tags]


def _one_flashing_plan(host_ref: str | None):
    """The smallest plan that carries one hosted trim run and nothing else.

    Built rather than borrowed from catlin: the reference model is a session-scoped
    read-only fixture, and a test that mutated it would leak into whatever module ran next.
    """
    import uuid

    from typehaus.model import (
        Building, Library, PlanModel, Project, Site, Storey, degF, ft, inch, pt,
    )
    from typehaus.model.trim import Flashing

    project = Project(
        name="Trim", project_uuid=uuid.UUID("00000000-0000-4000-8000-0000000000d2"),
        site=Site(lat=44.9, lon=-93.2, elevation=ft(830), design_temp_heating=degF(-15),
                  design_temp_cooling=degF(90)), building=Building(name="Trim"))
    run = Flashing(uid="TRIM000001", tag="TR-TEST", host_ref=host_ref,
                   path=(pt(ft(0), ft(0)), pt(ft(10), ft(0))),
                   top_elevation=ft(10), depth=inch(4), thickness=inch(1))
    plan = PlanModel(project=project, library=Library(),
                     storeys=(Storey(uid="STMAIN0001", tag="main", elevation=ft(0),
                                     default_ceiling_height=ft(9)),))
    return plan.with_elements("main", (run,))


def _verdicts(host_ref: str | None):
    from typehaus.resolve import resolve

    model, resolve_findings = resolve(_one_flashing_plan(host_ref))
    return [f for f in run_from_model(model, resolve_findings, only=_CHECK_ID).findings
            if f.check_id == _CHECK_ID]


def test_a_dangling_host_ref_fails() -> None:
    """The defect the check exists for: host_ref naming something that is not there.

    Nothing else in the engine reads the field, so this is the only thing standing between
    a retired tag and a run that goes on silently claiming to trim it.
    """
    findings = _verdicts("BM-RETIRED")
    assert [f.result for f in findings] == [Result.FAIL]
    assert "BM-RETIRED" in findings[0].message
    assert "does not exist" in findings[0].message


def test_a_run_naming_no_host_is_out_of_subject() -> None:
    """Nine of catlin's 29 runs name nothing — the corner flashings and the garage stem
    strips. A run with no host claims nothing, so it is out of subject rather than a gap,
    and with no hosted run anywhere the check earns N/A instead of returning []."""
    findings = _verdicts(None)
    assert [f.result for f in findings] == [Result.NOT_APPLICABLE]
