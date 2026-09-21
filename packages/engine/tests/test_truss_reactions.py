"""``structural.truss_reactions`` — a fabricator's published reactions, and the chain below.

Graded against catlin's own two trussed roofs, with rows quoted onto a copy of the roof
element: the guards are the substance (a quote on ground snow alone must not read as a PASS
under a roof-step drift), and the connector read is ``published``'s own.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from typehaus.checks.structural.truss_reactions import truss_reactions
from typehaus.findings import Result
from typehaus.model import PublishedCapacity, PublishedReaction


@pytest.fixture(scope="module")
def ctx(catlin_ctx):
    return catlin_ctx


def _heel(capacity: float = 900.0) -> PublishedCapacity:
    return PublishedCapacity(source="Simpson C-C-2024 p. 330", table="H2.5A, uplift 160",
                             member="H2.5A", capacity_lb=capacity,
                             condition="SPF, 10d nails as scheduled")


def _row(**over) -> PublishedReaction:
    fields = dict(source="Fabricator job 0000 rev A (sealed)", table="B1 north heel",
                  member="T1", uplift_lb=640.0, condition="as scheduled",
                  ground_snow_psf=50.0, drift_psf=50.3, wind_speed_mph=115.0,
                  exposure="B", connector=_heel())
    fields.update(over)
    return PublishedReaction(**fields)


def _with_rows(ctx, tag: str, *rows: PublishedReaction):
    element = ctx.plan.by_tag(tag).model_copy(update={"published_reactions": rows})

    class _Plan:
        def __getattr__(self, name):
            return getattr(ctx.plan, name)

        def by_tag(self, wanted):
            return element if wanted == tag else ctx.plan.by_tag(wanted)

    return SimpleNamespace(plan=_Plan(), model=ctx.model, preferences=ctx.preferences,
                           engineering=ctx.engineering)


def _finding(ctx, tag):
    return next(f for f in truss_reactions(ctx) if tag in f.element_tags)


def test_catlin_authors_no_reaction_and_is_unknown(ctx) -> None:
    findings = truss_reactions(ctx)
    assert {f.result for f in findings} == {Result.UNKNOWN}
    assert {f.element_tags for f in findings} == {("RF-BW-CANOPY",), ("RF-GARAGE",)}
    assert not any(f.engineering_item for f in findings)


def test_a_covered_heel_passes_and_names_no_item(ctx) -> None:
    finding = _finding(_with_rows(ctx, "RF-BW-CANOPY", _row()), "RF-BW-CANOPY")
    assert finding.result is Result.PASS, finding.message
    assert finding.engineering_item is None


def test_an_undersized_heel_connector_fails(ctx) -> None:
    finding = _finding(_with_rows(ctx, "RF-BW-CANOPY", _row(connector=_heel(500.0))),
                       "RF-BW-CANOPY")
    assert finding.result is Result.FAIL


def test_a_quote_on_ground_snow_alone_is_refused_under_the_drift(ctx) -> None:
    finding = _finding(_with_rows(ctx, "RF-BW-CANOPY", _row(drift_psf=None)),
                       "RF-BW-CANOPY")
    assert finding.result is Result.UNKNOWN
    assert "ordinary trusses" in finding.message


def test_the_garage_is_not_held_to_the_canopy_drift_guard(ctx) -> None:
    # No roof_beam record covers RF-GARAGE, so the model states no drift for it to demand.
    finding = _finding(_with_rows(ctx, "RF-GARAGE", _row(drift_psf=None)), "RF-GARAGE")
    assert finding.result is Result.PASS, finding.message


@pytest.mark.parametrize("over, words", [
    ({"ground_snow_psf": 40.0}, "40 psf ground snow"),
    ({"ground_snow_psf": None}, "states no ground snow"),
    ({"wind_speed_mph": 105.0}, "105 mph"),
    ({"wind_speed_mph": None}, "no wind basis"),
    ({"exposure": "C"}, "Exposure C"),
])
def test_a_row_run_at_a_milder_basis_is_refused(ctx, over, words) -> None:
    finding = _finding(_with_rows(ctx, "RF-BW-CANOPY", _row(**over)), "RF-BW-CANOPY")
    assert finding.result is Result.UNKNOWN
    assert words in finding.message


def test_a_row_with_no_connector_is_unknown_with_the_hint(ctx) -> None:
    finding = _finding(_with_rows(ctx, "RF-BW-CANOPY", _row(connector=None)),
                       "RF-BW-CANOPY")
    assert finding.result is Result.UNKNOWN
    assert "PublishedReaction.connector" in (finding.fix_hint or "")


def test_the_row_round_trips() -> None:
    row = _row()
    assert PublishedReaction.model_validate(row.model_dump()) == row
