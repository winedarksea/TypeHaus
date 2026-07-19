"""Declared Minnesota residential permit-submittal gate (M3 WP3.8)."""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.checks.registry import CheckReport, Tier
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


_CODE_ITEMS = (
    ("Ceiling height / habitable attic", ("code.R305_ceiling_height",)),
    ("Sleeping-room emergency escape", ("code.R310_egress",)),
    ("Egress door clear width", ("code.R311_door_width",)),
    ("Smoke / CO alarm placement", ("code.R314_R315_alarms",)),
)


def evaluate_permit_checklist(report: CheckReport, profile_name: str) -> PermitChecklist:
    """Turn the registry results into a small gate without hiding unknowns.

    Advisory, building-science, and engineered-header results stay in the full report but
    do not make a false claim that a prescriptive permit review evaluated them.
    """
    items = [_item_from_findings(label, check_ids, report.findings)
             for label, check_ids in _CODE_ITEMS]
    items.append(_item_from_findings(
        "Foundation frost depth", ("structural.frost_depth",), report.findings,
    ))
    items.append(_item_from_findings(
        "I-joist span table", ("structural.ijoist_span",), report.findings,
    ))
    items.append(_item_from_findings(
        "Plumbing sleeve alignment", ("mep.sleeve_alignment",), report.findings,
    ))
    items.append(_item_from_findings(
        "Plumbing drain slope", ("mep.drain_slope",), report.findings,
    ))
    items.append(_item_from_findings(
        "Site setbacks", ("code.site_setback",), report.findings,
    ))
    items.append(_item_from_findings(
        "Energy prescriptive envelope", ("code.energy_prescriptive",), report.findings,
    ))
    items.append(_integrity_item(report.findings))
    return PermitChecklist(profile_name=profile_name, items=tuple(items))


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
