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
class FramingPreferences:
    """Module and opening rules that keep framing, panels, and openings coordinated."""

    module_in: float = 16.0
    corner: str = "three-stud"
    max_window_ro_unbroken_in: float = 14.0
    max_window_ro_nonbearing_in: float = 30.0
    max_window_ro_bearing_in: float = 27.0


@dataclass
class PlumbingPreferences:
    """Planning allowances for advisory service checks, not plumbing sizing."""

    drain_stack_required_structure_in: float = 5.5


@dataclass(frozen=True)
class ReferenceUnderlay:
    """A view-only calibrated reference image; never emitted as building geometry."""

    path: str
    storey: str
    origin_x_m: float = 0.0
    origin_y_m: float = 0.0
    width_m: float = 1.0
    height_m: float = 1.0
    rotation_deg: float = 0.0
    opacity: float = 0.25


@dataclass
class Preferences:
    """`preferences.toml` values the warn-tier checks consume (→ 12)."""

    wall_r: float | None = None
    roof_r: float | None = None
    window_u: float | None = None
    ach50: float | None = None
    interior_setpoint_f: float = 70.0
    interior_relative_humidity: float = 0.35
    exterior_relative_humidity: float = 0.80
    south_wwr_threshold: float = 0.40
    adequate_overhang_ft: float = 2.0
    cooling_solar_gain_btu_per_hour_ft2: float = 164.0
    framing: FramingPreferences = field(default_factory=FramingPreferences)
    plumbing: PlumbingPreferences = field(default_factory=PlumbingPreferences)
    underlays: tuple[ReferenceUnderlay, ...] = ()
    suppressed: frozenset[str] = frozenset()


@dataclass
class JurisdictionProfile:
    """A versioned code profile (→ 12 §checks/code). M1 ships a minimal MN stub."""

    name: str
    edition: str
    effective_date: str
    irc_base: str
    coverage_statement: str
    frost_depth_in: float | None = None


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
