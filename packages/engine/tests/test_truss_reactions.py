"""``structural.truss_reactions`` — a fabricator's published reactions, and the chain below.

Graded against catlin's own two trussed roofs, with rows quoted onto a copy of the roof
element: the guards are the substance (a quote on ground snow alone must not read as a PASS
under a roof-step drift), and the connector read is ``published``'s own.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from typehaus.checks.structural.truss_reactions import drift_trusses, truss_reactions
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


def test_the_canopy_drift_reaches_the_garages_two_southern_trusses(ctx) -> None:
    """notes/north_entry_piers.md §3a: 9.8 ft from the canopy's south edge is 3.80 ft into
    RF-GARAGE, over truss-000 (y 43.281) and truss-001 (45.219); truss-002 (47.219) is out."""
    garage = next(r for r in ctx.model.roofs if r.tag == "RF-GARAGE")
    inside, why = drift_trusses(ctx, garage)
    assert inside == {"truss-000", "truss-001"}
    assert "RF-BW-CANOPY" in why and "3.80 ft" in why


@pytest.mark.parametrize("member, result", [
    ("truss-001", Result.UNKNOWN),   # a drift truss, quoted on ground snow alone
    ("T1", Result.UNKNOWN),          # a mark the model cannot place: held to the drift
    ("truss-005", Result.PASS),      # an ordinary truss needs no drift
])
def test_the_garage_drift_guard_is_per_truss(ctx, member, result) -> None:
    finding = _finding(_with_rows(ctx, "RF-GARAGE", _row(member=member, drift_psf=None)),
                       "RF-GARAGE")
    assert finding.result is result, finding.message
    if result is Result.UNKNOWN:
        assert "truss-000, truss-001 of RF-GARAGE are drift trusses" in finding.message


def test_with_no_drift_width_the_neighbour_is_held_whole(ctx) -> None:
    from dataclasses import replace

    prefs = replace(ctx.preferences, structural=replace(ctx.preferences.structural,
                                                         roof_beam_drift_width_ft=None))
    bare = SimpleNamespace(plan=ctx.plan, model=ctx.model, preferences=prefs,
                           engineering=ctx.engineering)
    garage = next(r for r in ctx.model.roofs if r.tag == "RF-GARAGE")
    inside, why = drift_trusses(bare, garage)
    assert len(inside) == 13 and "roof_beam_drift_width_ft" in why


def test_a_garage_drift_truss_quoted_with_the_drift_passes(ctx) -> None:
    finding = _finding(_with_rows(ctx, "RF-GARAGE", _row(member="truss-000")), "RF-GARAGE")
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
