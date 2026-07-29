"""Declared permit-submittal gate (M3 WP3.8).

The checklist itself is *not* here: it is declared by the jurisdiction profile
(:mod:`typehaus.checks.jurisdiction`), and this module only turns registry results into it.
While the list lived here it drifted from the registry — two registered R401.3 checks were
on no line of it — and a second jurisdiction would have meant an `if profile == ...` here.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.checks.jurisdiction import JurisdictionProfile
from typehaus.checks.registry import CheckReport
from typehaus.findings import Finding, Result, Severity


@dataclass(frozen=True)
class PermitChecklistItem:
    """One transparent, narrowly-scoped permit-submittal requirement."""

    label: str
    result: Result
    detail: str
    check_ids: tuple[str, ...]


@dataclass(frozen=True)
class PermitChecklist:
    """The gate intentionally covers only checks this engine actually evaluates."""

    profile_name: str
    items: tuple[PermitChecklistItem, ...]

    @property
    def ok(self) -> bool:
        return all(item.result is Result.PASS for item in self.items)


def evaluate_permit_checklist(report: CheckReport,
                              profile: JurisdictionProfile | str) -> PermitChecklist:
    """Turn the registry results into the profile's gate without hiding unknowns.

    Advisory, building-science, and engineered-header results stay in the full report but
    do not make a false claim that a prescriptive permit review evaluated them.

    ``profile`` accepts a name for callers that still pass one; the profile object is the
    real input, since it carries the checklist.

    Note that :attr:`PermitChecklist.ok` is strict — an UNKNOWN blocks, because "we could not
    evaluate this" is not a permit-ready answer. The checks-as-tests plugin deliberately
    takes the looser view (UNKNOWN passes) for the day-to-day inner loop; see its docstring.
    """
    if isinstance(profile, str):
        from typehaus.checks.code.mn_residential.profile import get_profile

        profile = get_profile(profile)
    items = [_item_from_findings(spec.label, spec.check_ids, report.findings)
             for spec in profile.permit_items]
    items.append(_integrity_item(report.findings))
    return PermitChecklist(profile_name=profile.name, items=tuple(items))


def _item_from_findings(label: str, check_ids: tuple[str, ...], findings: list[Finding]) -> PermitChecklistItem:
    matched = [finding for finding in findings if finding.check_id in check_ids]
    failed = [finding for finding in matched if finding.result is Result.FAIL]
    unknown = [finding for finding in matched if finding.result is Result.UNKNOWN]
    if failed:
        return PermitChecklistItem(label, Result.FAIL, failed[0].message, check_ids)
    if unknown:
        return PermitChecklistItem(label, Result.UNKNOWN, unknown[0].message, check_ids)
    if not matched:
        return PermitChecklistItem(label, Result.UNKNOWN, "no evaluable model input", check_ids)
    return PermitChecklistItem(label, Result.PASS, f"{len(matched)} evaluated result(s) pass", check_ids)


def _integrity_item(findings: list[Finding]) -> PermitChecklistItem:
    relevant = [finding for finding in findings
                if finding.severity is Severity.ERROR
                or finding.check_id == "integrity.condition_coverage"]
    if relevant:
        return PermitChecklistItem(
            "Resolved-model and transition integrity", Result.FAIL, relevant[0].message,
            ("integrity.*",),
        )
    return PermitChecklistItem(
        "Resolved-model and transition integrity", Result.PASS,
        "no blocking model errors or uncovered boundary conditions", ("integrity.*",),
    )
