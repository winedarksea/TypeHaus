"""Checks registry — one registry, two invokers (pytest plugin + `haus check`, → 12).

A check is a pure function ``(CheckContext) -> list[Finding]`` registered via decorator
under a tier. Rule *results* are tri-state (#32): findings carry PASS/FAIL/UNKNOWN and
UNKNOWN is counted in its own column, never folded into passes.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum

from typehaus.findings import Finding, Result, Severity
from typehaus.model.plan import PlanModel
from typehaus.resolve.model import ResolvedModel


class Tier(Enum):
    INTEGRITY = "integrity"
    CODE = "code"
    ADVISORY = "advisory"
    STRUCTURAL = "structural"
    BUILDING_SCIENCE = "building_science"


@dataclass
class Preferences:
    """`preferences.toml` values the warn-tier checks consume (→ 12)."""

    wall_r: float | None = None
    roof_r: float | None = None
    window_u: float | None = None
    ach50: float | None = None
    suppressed: frozenset[str] = frozenset()


@dataclass
class JurisdictionProfile:
    """A versioned code profile (→ 12 §checks/code). M1 ships a minimal MN stub."""

    name: str
    edition: str
    effective_date: str
    irc_base: str
    coverage_statement: str


@dataclass
class CheckContext:
    plan: PlanModel
    model: ResolvedModel
    preferences: Preferences
    profile: JurisdictionProfile
    resolve_findings: list[Finding] = field(default_factory=list)


CheckFn = Callable[[CheckContext], list[Finding]]
_REGISTRY: dict[Tier, list[tuple[str, CheckFn]]] = {t: [] for t in Tier}


def check(tier: Tier, check_id: str) -> Callable[[CheckFn], CheckFn]:
    def deco(fn: CheckFn) -> CheckFn:
        _REGISTRY[tier].append((check_id, fn))
        return fn

    return deco


def registered(tier: Tier | None = None) -> list[tuple[str, CheckFn]]:
    if tier is not None:
        return list(_REGISTRY[tier])
    return [pair for t in Tier for pair in _REGISTRY[t]]


@dataclass
class CheckReport:
    findings: list[Finding]

    def counts(self) -> tuple[int, int, int]:
        """(pass, fail, unknown) rule-result counts (#32 tri-state)."""
        p = f = u = 0
        for finding in self.findings:
            if finding.result is Result.UNKNOWN:
                u += 1
            elif finding.result is Result.FAIL:
                f += 1
            else:
                p += 1
        return p, f, u

    @property
    def errors(self) -> list[Finding]:
        return [x for x in self.findings if x.severity is Severity.ERROR]

    @property
    def ok(self) -> bool:
        return not self.errors


def run_checks(ctx: CheckContext, tier: Tier | None = None) -> CheckReport:
    """Run every registered check (of the given tier) plus resolve-time findings."""
    findings: list[Finding] = list(ctx.resolve_findings)
    for check_id, fn in registered(tier):
        for finding in fn(ctx):
            if finding.check_id in ctx.preferences.suppressed:
                continue
            findings.append(finding)
    return CheckReport(findings=findings)
