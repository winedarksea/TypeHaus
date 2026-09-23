"""A deck hung on ledgers bolted to two walls (``Beam.ledger_on``, ``structural.deck_ledger``).

The ledger is a Beam authored flush with the joist tops, so ``joints/hung.py`` derives the
hangers with no new logic. It is continuously supported: no beam span, post or footing
applies, and the attachment is graded by its own check.
"""

from __future__ import annotations

import pytest
from _helpers import check_context
from _ledger_fixture import plan

from typehaus.checks.structural.deck import (
    deck_beam_cantilever,
    deck_beam_span,
    deck_footing_size,
    deck_joist_span,
    deck_post_size,
)
from typehaus.checks.structural.deck_ledger import deck_ledger
from typehaus.findings import Result
from typehaus.hardware.catalog import allowable_for_model, hardware_by_model
from typehaus.hardware.config import HangerDetectionRules
from typehaus.joints.authored import hanger_part, hanger_specs
from typehaus.joints.hung import hung_connections
from typehaus.model.refs import PublishedSpan
from typehaus.quantities import ft, inch


@pytest.fixture(scope="module")
def ctx():
    return check_context(plan())


def _by_tag(findings, tag):
    return next(f for f in findings if tag in f.element_tags)


def test_every_joist_hangs_on_a_ledger_in_a_zmax_2x12_hanger(ctx):
    hung = hung_connections(ctx.model, HangerDetectionRules())
    assert {h.carrier_tag for h in hung} == {"BM-LW", "BM-LE"}
    assert len(hung) == 22  # 11 joists at 12" over 10', both ends
    assert all(h.carrier_treated for h in hung)
    parts = {hanger_part(h, hanger_specs(ctx.model))[2] for h in hung}
    assert parts == {"LUS210Z"}
    record = hardware_by_model("LUS210Z")
    assert record is not None and record.model == "LUS210Z"
    assert allowable_for_model("LUS210Z").download_lb == 1340.0


def test_the_joist_is_cut_to_the_ledger_face_and_spans_face_to_face(ctx):
    finding = deck_joist_span(ctx)[0]
    assert finding.result is Result.PASS
    # 18'-6" between wall axes, less two 6" half-walls and two 1 1/2" ledgers
    assert "span 17.25'" in finding.message


def test_a_ledger_is_not_a_beam_post_or_footing(ctx):
    assert not deck_beam_cantilever(ctx)
    for check in (deck_beam_span, deck_post_size, deck_footing_size):
        (finding,) = check(ctx)
        assert finding.result is Result.NOT_APPLICABLE, finding.message
        assert "hangs on ledgers" in finding.message


def test_on_concrete_the_spacing_is_the_anchor_makers_and_says_so(ctx):
    findings = deck_ledger(ctx)
    assert len(findings) == 2
    assert all(f.result is Result.UNKNOWN for f in findings)
    assert "manufacturer's recommendations" in findings[0].message


def test_on_a_wood_band_the_dca6_table_grades_the_spacing():
    ok = deck_ledger(check_context(plan(wood=True, fastener="1/2 through-bolt",
                                        spacing_in=16.0), profile=None))
    assert all(f.result is Result.PASS for f in ok), [f.message for f in ok]
    assert "19\" o.c." in ok[0].message  # through-bolts, 18' row
    lag = deck_ledger(check_context(plan(wood=True, fastener="1/2 lag", spacing_in=16.0),
                                    profile=None))
    assert all(f.result is Result.FAIL for f in lag)  # 18" gap vs 10" for lags


def test_no_anchors_fails():
    finding = _by_tag(deck_ledger(check_context(plan(spacing_in=None), profile=None)), "BM-LW")
    assert finding.result is Result.FAIL
    assert "no anchors" in finding.message


def test_an_untreated_ledger_fails():
    untreated = plan(assembly="BEAM_SPF", ledger="2x12")
    finding = _by_tag(deck_ledger(check_context(untreated, profile=None)), "BM-LW")
    assert finding.result is Result.FAIL
    assert "not preservative-treated" in finding.message


def test_a_ledger_off_the_face_fails():
    finding = _by_tag(deck_ledger(check_context(plan(gap_in=1.0), profile=None)), "BM-LW")
    assert finding.result is Result.FAIL
    assert "off W-W's face" in finding.message


def test_a_ledger_naming_no_wall_fails():
    finding = _by_tag(deck_ledger(check_context(plan(ledger_on_w="BM-LE"), profile=None)),
                      "BM-LW")
    assert finding.result is Result.FAIL
    assert "not a wall" in finding.message


def _row(member="THD50600H6SS"):
    return PublishedSpan(source="Simpson L-A-THDSSLDGR23", table="up to 18 ft: 19 in",
                         member=member, span=inch(19), carried_span=ft(18), load_psf=50.0,
                         treatment="treated", condition="fn 1-4")


def test_on_concrete_a_manufacturers_row_grades_the_spacing():
    ok = deck_ledger(check_context(plan(fastener="THD50600H6SS", published=_row()),
                                   profile=None))
    assert all(f.result is Result.PASS for f in ok), [f.message for f in ok]
    wide = deck_ledger(check_context(plan(fastener="THD50600H6SS", spacing_in=24.0,
                                          published=_row()), profile=None))
    assert all(f.result is Result.FAIL for f in wide), [f.message for f in wide]


def test_a_row_for_another_anchor_is_refused():
    findings = deck_ledger(check_context(plan(fastener="1/2 adhesive anchor",
                                              published=_row()), profile=None))
    assert all(f.result is Result.UNKNOWN for f in findings)
    assert "THD50600H6SS" in findings[0].message


def test_catlin_porch_ledgers_pass_on_simpsons_thdss_row(catlin_ctx):
    """Both porch ledgers sit on the court walls' faces, treated, with Type 316 Titen HDs at
    16" o.c. against L-A-THDSSLDGR23's 19" row for joists up to 18'."""
    findings = {f.element_tags[0]: f for f in deck_ledger(catlin_ctx)}
    assert set(findings) == {"BM-SG-LDGW", "BM-SG-LDGE"}
    for finding in findings.values():
        assert finding.result is Result.PASS, finding.message
        assert "L-A-THDSSLDGR23" in finding.message and "1.33' <= 1.58'" in finding.message


def test_a_plan_with_no_ledger_is_not_applicable():
    from typehaus.checks.structural import deck_ledger as module

    ctx = check_context(plan())
    original = module._ledgers
    module._ledgers = lambda _ctx: []
    try:
        (finding,) = deck_ledger(ctx)
    finally:
        module._ledgers = original
    assert finding.result is Result.NOT_APPLICABLE


def test_ledger_anchors_are_not_sill_anchorage(ctx):
    """S-100's sill schedule takes authored cast-in bolts first and derived mudsill anchors
    otherwise; a ledger's anchors are neither, and must not displace the mudsill rows."""
    from typehaus.emit.draw.foundation_schedule import _anchor_bolt_rows

    assert _anchor_bolt_rows(ctx.model) == []
