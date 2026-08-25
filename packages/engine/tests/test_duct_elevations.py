"""``DuctRun`` carries the pipe stack: elevations, a swept solid, a developed length.

Until 2026-08-25 a duct had no elevation field at all, so a four-storey ERV existed only as
plan polylines that teleported between floors — no vertical leg was drawn anywhere, ducts
emitted no 3D solids, and ``duct_takeoff`` billed plan length, which measures a riser as the
zero length it projects to. The field set is ``PipeRun``'s, the solver is ``PipeRun``'s (with
the check-id prefix as a parameter), and the sweep kernel is the shared one.

These tests pin the four things that made the move worth doing, plus the one invariant that
made it safe: a duct that authors no elevation resolves exactly where it always did.
"""

from __future__ import annotations

import math

import pytest

from typehaus.findings import Result
from typehaus.model.enums import DuctSystem
from typehaus.model.mep import DuctRun
from typehaus.quantities import ft, inch, pt
from typehaus.resolve.mep_ducts import _duct_section
from typehaus.resolve.mep_slope import _pipe_vertex_z

_M_PER_IN = inch(1).meters


def _duct(**kw) -> DuctRun:
    defaults = dict(uid="AAAAAAAAAA", tag="DU-T", system=DuctSystem.SUPPLY,
                    diameter=inch(6), path=(pt(ft(0), ft(0)), pt(ft(10), ft(0))))
    defaults.update(kw)
    return DuctRun(**defaults)


def _solve(run: DuctRun, datum: float = 0.0):
    return _pipe_vertex_z(run, [p.xy_m for p in run.path], datum, prefix="duct")


# --- the solver is the pipe solver, and it says "duct" -----------------------------------

def test_a_riser_is_a_repeated_plan_point_at_two_elevations() -> None:
    """The whole idiom, and the reason no new concept was needed for a four-storey ERV."""
    run = _duct(path=(pt(ft(1), ft(34)), pt(ft(1), ft(34))),
                elevations=(inch(-19.4375), inch(244)))
    z, findings = _solve(run)
    assert not findings
    assert z[0] == pytest.approx(-19.4375 * _M_PER_IN)
    assert z[1] == pytest.approx(244 * _M_PER_IN)


def test_an_unauthored_elevation_falls_at_the_authored_grade() -> None:
    run = _duct(path=(pt(ft(0), ft(0)), pt(ft(10), ft(0)), pt(ft(20), ft(0))),
                elevations=(ft(0), None, ft(-0.5)), slope_in_per_ft=0.3)
    z, findings = _solve(run)
    assert not findings
    assert z[1] == pytest.approx(-0.3 * 10 * _M_PER_IN, abs=1e-12)


def test_a_mismatched_elevation_count_reports_against_the_DUCT_check_id() -> None:
    """The one plumbing-specific thing left in the solver was the check id, so it is a
    parameter. A duct that miscounts its inverts must not be reported as a pipe run."""
    run = _duct(path=(pt(ft(0), ft(0)), pt(ft(10), ft(0))), elevations=(ft(0),))
    z, findings = _solve(run)
    assert z is None
    assert [f.check_id for f in findings] == ["integrity.duct_run_elevations"]
    assert findings[0].result is Result.FAIL
    assert "duct run DU-T" in findings[0].message


def test_a_vertical_leg_with_an_unauthored_end_is_an_error_not_a_guess() -> None:
    run = _duct(path=(pt(ft(0), ft(0)), pt(ft(0), ft(0))),
                elevations=(ft(0), None), slope_in_per_ft=0.3)
    z, findings = _solve(run)
    assert z is None
    assert findings[0].check_id == "integrity.duct_run_slope"


# --- section: round or rectangular, never both and never neither -------------------------

def test_a_round_duct_reports_its_diameter_as_both_plan_dimensions() -> None:
    """Every consumer that measures a duct against a bay or a soffit is asking how much room
    it takes up, and a 6" round takes 6" either way. The diameter rides alongside for the
    two that need to know it is round: the sweep profile and the take-off key."""
    section, findings = _duct_section(_duct(diameter=inch(6)))
    assert not findings
    width, depth, diameter = section
    assert width == depth == diameter == pytest.approx(6 * _M_PER_IN)


def test_a_rectangular_duct_carries_no_diameter() -> None:
    section, findings = _duct_section(
        _duct(diameter=None, width=inch(14), depth=inch(8)))
    assert not findings
    width, depth, diameter = section
    assert diameter is None
    assert (width, depth) == (pytest.approx(14 * _M_PER_IN), pytest.approx(8 * _M_PER_IN))


def test_stating_both_sections_is_an_error() -> None:
    section, findings = _duct_section(_duct(diameter=inch(6), width=inch(14)))
    assert section is None
    assert findings[0].check_id == "integrity.duct_run_section"


def test_stating_no_section_is_an_error() -> None:
    section, findings = _duct_section(_duct(diameter=None))
    assert section is None
    assert findings[0].check_id == "integrity.duct_run_section"


# --- what the reference house gained -----------------------------------------------------

def test_catlin_ducts_all_resolve_a_z_per_vertex(catlin_model) -> None:
    """Never None, even where nothing is authored: the resolver derives one z from the
    soffit, the joist bay or the storey datum, so no consumer re-derives it (and no consumer
    re-derives it *differently* — that derivation used to live in the IFC emitter alone,
    which is why nothing else could draw a duct)."""
    for duct in catlin_model.ducts:
        assert len(duct.z_m) == len(duct.path), duct.tag


def test_catlin_ducts_are_swept_solids(catlin_model) -> None:
    """A duct is one mitred tube, the way a pipe is — not the nothing it used to be."""
    swept = {s.tag[:-4] for s in catlin_model.solids
             if s.category.startswith("duct_") and s.sweep is not None}
    assert swept == {d.tag for d in catlin_model.ducts}


def test_a_drawn_riser_bills_more_than_its_plan_projection(catlin_model) -> None:
    """``DU-ERV-RISER-SUP`` is one plan point at two elevations: its plan length is zero and
    its developed length is the whole basement-to-attic rise. Billing the former is exactly
    what ``duct_takeoff`` did before this."""
    riser = next(d for d in catlin_model.ducts if d.tag == "DU-ERV-RISER-SUP")
    plan = sum(math.dist(a, b) for a, b in zip(riser.path, riser.path[1:]))
    assert plan == pytest.approx(0.0, abs=1e-9)
    assert riser.length_m > 6.0  # ~21'-11" of rise


def test_every_catlin_duct_solid_is_a_declared_routed_run_category(catlin_model) -> None:
    """The "68 of catlin's 239 footings were pipe" guard, one trade over: a run already
    exports as a real ``IfcDuctSegment``, so the IFC emitter must skip its solid in the
    generic loop — and it skips exactly ``ROUTED_RUN_CATEGORIES``."""
    from typehaus.emit.trades import ROUTED_RUN_CATEGORIES, solid_trade

    minted = {s.category for s in catlin_model.solids if s.category.startswith("duct_")}
    assert minted
    assert minted <= ROUTED_RUN_CATEGORIES
    assert {solid_trade(c) for c in minted} == {"mechanical"}
