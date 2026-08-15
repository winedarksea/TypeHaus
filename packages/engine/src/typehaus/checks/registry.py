"""Checks registry — one registry, two invokers (pytest plugin + `haus check`, → 12).

A check is a pure function ``(CheckContext) -> list[Finding]`` registered via decorator
under a tier. Rule *results* are tri-state (#32): findings carry PASS/FAIL/UNKNOWN and
UNKNOWN is counted in its own column, never folded into passes.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum

# JurisdictionProfile lived here before it grew into its own module; it is still imported
# from this one by existing call sites, so the name stays bound here deliberately.
from typehaus.checks.jurisdiction import JurisdictionProfile, PermitItemSpec  # noqa: F401
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
    # z-overlap tolerance for the model-wide member-interference check: a bearing/
    # stacking joint clears this band; anything deeper is flagged.
    interference_tolerance_in: float = 0.25


@dataclass
class PlumbingPreferences:
    """Planning allowances for advisory service checks, not plumbing sizing."""

    drain_stack_required_structure_in: float = 5.5
    # The house's own rule for what visible supply pipe is made of. Not code — copper and
    # PEX are both listed for potable water everywhere in the house — but it is a rule the
    # model can hold to, which is the difference between a style decision and a memory.
    #
    # ``visible_basement_material`` is what a run gets where it is *seen*; the Catlin rule is
    # geometric rather than a tag list, so it survives a reroute: a basement supply run whose
    # ceiling is cast concrete is exposed and reads as finish, and one under a framed floor
    # will be covered. Change the deck to wood joists and the same rule stops applying to
    # everything under it, with nothing to edit.
    visible_basement_material: str | None = None
    visible_basement_finish: str | None = None


@dataclass
class StructuralPreferences:
    """House-level allowances the structural advisories grade against, not code minima."""

    # What a support may carry from a guard standing on it before the guard is too heavy for
    # ordinary wood framing. A guard's dead load is derived from its own assembly, so this is
    # the only number in that rule — roughly what a heavy wood guard with 6x6 posts weighs per
    # foot of run, which is the load a deck rim designed to R507's 40 psf live + 10 psf dead
    # was drawn expecting. A grouted-CMU-and-brick parapet is eight times it.
    max_guard_dead_load_on_wood_plf: float = 50.0


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
    # Blower-door result in CFM at 50 Pa. An alternative to ``ach50`` for the same fact —
    # a test report states CFM50 and the ACH50 is derived from it — and it wins when both
    # are authored, because it needs no volume estimate to be useful.
    cfm50: float | None = None
    # LBL infiltration model divisor: CFMnat = CFM50 / N. The default 18 is the LBL
    # single-family figure for a two-storey house in a sheltered, moderately windy climate
    # (the published range is roughly 14–24, tighter shelter and more storeys lowering it).
    # Authored per house because it is a climate/shelter judgement, not a measurement.
    infiltration_n_factor: float = 18.0
    interior_setpoint_f: float = 70.0
    interior_relative_humidity: float = 0.35
    exterior_relative_humidity: float = 0.80
    # Interior winter design RH for the monthly (ISO 13788-style) condensation gate.
    # Kept separate from ``interior_relative_humidity`` (the 99% design-hour cold-snap
    # screen) so a humidified house can raise the seasonal gate without moving the screen;
    # the default matches the screen's winter design RH rather than inventing a new figure.
    monthly_interior_relative_humidity: float = 0.35
    south_wwr_threshold: float = 0.40
    adequate_overhang_ft: float = 2.0
    cooling_solar_gain_btu_per_hour_ft2: float = 164.0
    framing: FramingPreferences = field(default_factory=FramingPreferences)
    plumbing: PlumbingPreferences = field(default_factory=PlumbingPreferences)
    structural: StructuralPreferences = field(default_factory=StructuralPreferences)
    underlays: tuple[ReferenceUnderlay, ...] = ()
    suppressed: frozenset[str] = frozenset()
    # `[project].jurisdiction` from preferences.toml: the house's own answer to "whose code
    # is this?". `None` means the house doesn't say, and the engine default applies.
    jurisdiction: str | None = None


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
    # The check ids that actually ran. A check emitting zero findings is otherwise
    # indistinguishable from one that never ran at all, so no coverage claim built on
    # `findings` alone can be honest (→ checks/jurisdiction.py).
    ran: tuple[str, ...] = ()

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
    ran: list[str] = []
    for check_id, fn in registered(tier):
        ran.append(check_id)
        for finding in fn(ctx):
            if finding.check_id in ctx.preferences.suppressed:
                continue
            findings.append(finding)
    return CheckReport(findings=findings, ran=tuple(ran))
