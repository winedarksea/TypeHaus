"""Checks registry — one registry, two invokers (pytest plugin + `haus check`, → 12).

A check is a pure function ``(CheckContext) -> list[Finding]`` registered via decorator
under a tier. Rule *results* are tri-state (#32): findings carry PASS/FAIL/UNKNOWN and
UNKNOWN is counted in its own column, never folded into passes.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import Enum

# JurisdictionProfile lived here before it grew into its own module; it is still imported
# from this one by existing call sites, so the name stays bound here deliberately.
from typehaus.checks.jurisdiction import JurisdictionProfile, PermitItemSpec  # noqa: F401
from typehaus.engineering.item import EngineeringRecord
from typehaus.engineering.register import EngineeringRegister
from typehaus.engineering.registry import NO_ENGINEERING
from typehaus.findings import Authority, Finding, Result, Severity
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
    # "3-stud" | "4-stud" — the live vocabulary ``Wall.corner_style_start/end`` and
    # ``FramingSpec.corner_style`` speak; "three-stud" was never read by anything, since
    # nothing here compared this field to the framing solver's own vocabulary at all
    # (2026-08-25, ``structural.corner_style_matches_preference`` is the first thing that
    # does).
    corner: str = "3-stud"
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
class MepPreferences:
    """House allowances for the routing advisories — judgement, not code."""

    #: ``mep.run_route_efficiency``'s line. A run whose developed length is more than this
    #: many times the straight-line 3D distance between its own two ends is detouring, and
    #: worth a look. 2.5 is not a standard; it is where catlin's own distribution sits with
    #: margin (worst qualifying run 2.41), which is the only honest basis for a number nobody
    #: publishes. Raise it deliberately and say why.
    max_run_developed_over_straight: float = 2.5
    #: Below this a run is too short for the ratio to mean anything — see
    #: ``checks/mep/routing.py``.
    min_graded_run_ft: float = 20.0


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
    mep: MepPreferences = field(default_factory=MepPreferences)
    structural: StructuralPreferences = field(default_factory=StructuralPreferences)
    underlays: tuple[ReferenceUnderlay, ...] = ()
    #: ``[checks] suppress`` from the house's ``preferences.toml``. Two forms, and the second
    #: is the one that makes the list usable without blinding a check:
    #:
    #: * ``"check.id"``            — drop every finding that check makes. A blunt instrument:
    #:   it takes the check's UNKNOWNs and its PASSes with it, so a house that silences a rule
    #:   this way stops being told anything by it at all.
    #: * ``"check.id:ELEMENT-TAG"`` — drop that check's findings **on that one element**.
    #:   For the case a check cannot see: a finding that is real, was looked at, and was
    #:   decided against for a reason the model does not carry. ``D-G-OVERHEAD`` is off the
    #:   stud module by 8" and moving it re-cuts the garage's brick wainscot into two unequal
    #:   piers; that is a facade decision, and the right place to record it is beside the
    #:   reason, in the house's own file.
    #:
    #: An entry of the second form never hides another element's finding, so the check goes on
    #: grading the other twenty doors exactly as before.
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
    #: The engineering suite's results, keyed ``<kind>/<element-tag>``. Lazily memoising,
    #: so ``haus check --tier code`` never pays to design a retaining wall; every lookup
    #: succeeds, returning a NO_CALC record where nothing is registered. Built in
    #: ``checks/run.py::build_context`` so ``run``, ``run_from_model`` and the pytest
    #: plugin share one construction point. Defaults to an empty map for the handful of
    #: test fixtures that build a context by hand.
    engineering: Mapping[str, EngineeringRecord] = field(default_factory=lambda: NO_ENGINEERING)
    #: The house's ``engineering.toml``. Absent file -> empty register, never an error.
    engineering_register: EngineeringRegister = field(default_factory=EngineeringRegister)


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


@dataclass(frozen=True)
class ResultTally:
    """One bucket per :class:`Result`, plus how many findings rest on engineered design.

    ``engineered`` cuts across the others rather than partitioning them — it is an
    :class:`Authority`, not a verdict — so it is *not* included in :attr:`total`.
    """

    passed: int = 0
    failed: int = 0
    unknown: int = 0
    not_applicable: int = 0
    engineered: int = 0

    @property
    def total(self) -> int:
        """Encoded rules that produced a verdict. ``engineered`` is orthogonal, not a bucket."""
        return self.passed + self.failed + self.unknown + self.not_applicable


@dataclass
class CheckReport:
    findings: list[Finding]
    # The check ids that actually ran. A check emitting zero findings is otherwise
    # indistinguishable from one that never ran at all, so no coverage claim built on
    # `findings` alone can be honest (→ checks/jurisdiction.py).
    ran: tuple[str, ...] = ()
    # Carried through from the context so the *final* permit gate can be evaluated from a
    # report alone. A finding says "this rests on engineered design"; only the register can
    # say whether a PE has sealed it and whether that seal still matches the model, and a
    # caller holding a report and no context (the cover sheet is exactly that caller) would
    # otherwise have to rebuild the whole world to ask.
    engineering: Mapping[str, EngineeringRecord] = field(default_factory=lambda: NO_ENGINEERING)
    engineering_register: EngineeringRegister = field(default_factory=EngineeringRegister)

    def counts(self) -> ResultTally:
        """Rule-result counts (#32), one bucket per :class:`Result` member.

        Deliberately *not* a 3-tuple any more. The old form ended in ``else: p += 1``,
        which would have silently counted every ``NOT_APPLICABLE`` as a pass — the exact
        sin #32 exists to forbid — and would have done so without a single test failing.
        A tally that names its buckets cannot acquire that bug when a member is added.
        """
        tally = {result: 0 for result in Result}
        engineered = 0
        for finding in self.findings:
            tally[finding.result] += 1
            if finding.authority is Authority.ENGINEERED:
                engineered += 1
        return ResultTally(
            passed=tally[Result.PASS],
            failed=tally[Result.FAIL],
            unknown=tally[Result.UNKNOWN],
            not_applicable=tally[Result.NOT_APPLICABLE],
            engineered=engineered,
        )

    @property
    def errors(self) -> list[Finding]:
        return [x for x in self.findings if x.severity is Severity.ERROR]

    @property
    def ok(self) -> bool:
        return not self.errors


def _suppressed(finding: Finding, suppressed: frozenset[str]) -> bool:
    """Whether the house has asked for this finding to be dropped — see ``Preferences``."""
    if finding.check_id in suppressed:
        return True
    return any(f"{finding.check_id}:{tag}" in suppressed for tag in finding.element_tags)


def run_checks(ctx: CheckContext, tier: Tier | None = None) -> CheckReport:
    """Run every registered check (of the given tier) plus resolve-time findings."""
    findings: list[Finding] = list(ctx.resolve_findings)
    ran: list[str] = []
    for check_id, fn in registered(tier):
        ran.append(check_id)
        for finding in fn(ctx):
            if _suppressed(finding, ctx.preferences.suppressed):
                continue
            findings.append(finding)
    return CheckReport(findings=findings, ran=tuple(ran),
                       engineering=ctx.engineering,
                       engineering_register=ctx.engineering_register)
