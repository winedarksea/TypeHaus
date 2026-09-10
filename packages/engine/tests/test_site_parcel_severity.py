"""``code.site_parcel_is_surveyed`` is red but not a blocker (→ checks/code/site.py).

A declared placeholder parcel is a FAIL — the lot lines on C-101 were drawn, not measured,
and that has to read red. It is not an ERROR: the permit checklist declares the line
``blocking=False``, because a certified survey is a separate submittal on a surveyor's
schedule rather than a defect in the modelled building. These pin both halves, because
either one drifting alone re-creates the bug: ERROR severity gated ``--exit-on error`` on
an item the profile had deliberately opened.
"""

from __future__ import annotations

from test_site_checks import _model_with_site

from typehaus.checks import run_from_model
from typehaus.checks.registry import Tier
from typehaus.findings import Result, Severity

_CID = "code.site_parcel_is_surveyed"


def _verdicts(catlin_model, **site_updates):
    model = _model_with_site(catlin_model, **site_updates)
    report = run_from_model(model, [], tier=Tier.CODE)
    return [f for f in report.findings if f.check_id == _CID]


def test_a_placeholder_parcel_is_a_warn_severity_fail(catlin_model) -> None:
    findings = _verdicts(catlin_model, parcel_basis="placeholder")
    assert findings
    for finding in findings:
        assert finding.result is Result.FAIL
        assert finding.severity is Severity.WARN


def test_catlin_carries_no_error_severity_parcel_finding(catlin_model) -> None:
    """catlin's own site is the placeholder case, unmodified."""
    report = run_from_model(catlin_model, [], tier=Tier.CODE)
    matched = [f for f in report.findings if f.check_id == _CID]
    assert matched and all(f.severity is Severity.WARN for f in matched)


def test_the_permit_line_is_non_blocking_and_the_integrity_line_is_not_holding_it(
        catlin_model) -> None:
    """The two halves of "red but not a blocker", asserted where the gate reads them."""
    from typehaus.checks.permit import evaluate_permit_checklist

    report = run_from_model(catlin_model, [], tier=Tier.CODE)
    checklist = evaluate_permit_checklist(report, "mn-2024")
    parcel = [item for item in checklist.items if _CID in item.check_ids]
    assert parcel and not any(item.blocking for item in parcel)
    integrity = [item for item in checklist.items if "integrity.*" in item.check_ids]
    assert integrity
    assert not any("PLACEHOLDER" in (item.detail or "") for item in integrity)
