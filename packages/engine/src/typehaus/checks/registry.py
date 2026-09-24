"""Checks registry — one registry, two invokers (pytest plugin + `haus check`, → 12).

A check is a pure function ``(CheckContext) -> list[Finding]`` registered via decorator
under a tier. Rule *results* are tri-state (#32): findings carry PASS/FAIL/UNKNOWN and
UNKNOWN is counted in its own column, never folded into passes.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from contextvars import ContextVar
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TypeVar

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
    # "3-stud" | "4-stud" | "california" — the live vocabulary
    # ``Wall.corner_style_start/end`` and ``FramingSpec.corner_style`` speak;
    # "three-stud" is never read anywhere.
    # ``structural.corner_style_matches_preference`` is what compares this field against
    # the framing solver's own vocabulary.
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

    # --- mep.run_in_finished_volume (checks/mep/routing_ceiling.py) ---
    #: How far below a room's finished ceiling a run's outside surface has to hang before it
    #: is a finding. Catlin's ceilings resolve 5/8"-3/4" of lining, so anything under about
    #: three inches is the pipe grazing the plane it is furred to — real, and a dimension to
    #: check rather than a route to redraw. The defects this was written for measure 5.7",
    #: 8.1" and 33".
    ceiling_intrusion_in: float = 3.0
    #: Below this length a crossing is a corner clip of a room polygon rather than a run
    #: through the room — the same reasoning, and the same number, as ``MIN_SPAN_FT`` in
    #: ``mep.run_over_void``. A riser is exempt from it: its plan piece is a point, so it is
    #: graded on the feet of *height* it stands in the room instead.
    min_ceiling_exposure_ft: float = 0.5
    #: How close a terminal leg's own end vertex must land to something in the room before it
    #: reads as the connection to that thing rather than transit through the room. See
    #: ``routing_ceiling._terminates_in_room``.
    terminal_grace_in: float = 24.0
    #: The head a run must keep in a room whose ``Room.exposed_services`` declares its
    #: ceiling deliberately open. Declaring a room exposed retires the ceiling-plane
    #: comparison for it; it does NOT retire the question of whether somebody walks into the
    #: pipe, and nothing else in the engine asks that one — ``code.R305_ceiling_height``
    #: measures the STRUCTURE overhead and has never looked at a service run.
    #:
    #: 6'-8" is Minn. R. 1309.0305 R305.1.1's floor for the non-habitable parts of a
    #: basement, which is where exposed service ceilings actually live, and it is used here
    #: as a buildability line rather than as a code verdict: this check is ADVISORY and
    #: cites nothing. Measured off the storey datum, which is top-of-joists — a finished
    #: floor sits above it, so the number is read slightly conservatively on purpose.
    exposed_service_headroom_ft: float = 80.0 / 12.0

    # --- checks/mep/drain_geometry.py ---
    #: How far a drained fixture's derived drain point may sit from the nearest polyline of a
    #: run that names it in ``serves``. Catlin's measured distribution is bimodal with a clean
    #: hole in it: fixtures a branch actually reaches sit at 0"-8", the ones with no branch
    #: drawn at all at 15.6" and up. A foot sits in the gap with about 50% margin either side.
    fixture_drain_reach_in: float = 12.0
    #: The steepest a non-vertical drain segment may fall. 12"/ft is 45 degrees — the
    #: steepest fitting on the truck — so past this the geometry is not a fitting at all.
    max_drain_offset_slope_in_per_ft: float = 12.0
    #: How far a non-vertical drain segment may fall in total. Beyond this it is a drop drawn
    #: as a slant. Graded in conjunction with the slope, never alone: neither term separates
    #: the defect from a legitimate 45-degree offset by itself.
    max_drain_offset_fall_in: float = 18.0
    #: How much grade a drain must hold **over** the code minimum before its margin stops
    #: being a finding. ``mep.drain_slope_margin``'s line, and **it is not a code number** —
    #: the code's number is 1/4"/ft and ``resolve/mep_slope.py`` owns it. This is the
    #: buildability fact beside it.
    #:
    #: 1/16"/ft is a quarter inch spread over the four feet a rigid standoff is stepped at,
    #: which is BLD-05's own finding #2: the trade method is standoffs stepped about a whole
    #: inch every four feet, and the plumber's tolerance is one-directional *toward more
    #: pitch*. A run at exactly the minimum has nowhere to absorb that, and the model could
    #: not say so — it passed as cleanly as a run at three times the grade.
    #:
    #: A house with no head left may author 0.0 with the argument beside it; catlin does,
    #: and every PASS still prints its margin, which is most of the check's value.
    min_drain_slope_margin_in_per_ft: float = 0.0625

    # --- mep.riser_through_deck (checks/mep/riser_through_deck.py) ---
    #: The largest hole a trade DRILLS through a deck rather than frames. Past it the deck
    #: has to be cut and headed, which is a drawing — a ``FloorOpening`` — and not something
    #: an installer decides on the day.
    #:
    #: 2" is the trade line and not a code one: a 2" hole saw goes through a joist or a rim
    #: on site, and a 3" one is a cut member. The check reports a riser bigger than this and
    #: clear of every member as a FAIL ("framed, not drilled") and a smaller one as UNKNOWN,
    #: because whether a 1 1/4" raceway may share a bay with an I-joist's web is a question
    #: ``member_window.basis`` answers and this number does not.
    max_undrawn_deck_hole_in: float = 2.0

    # --- [mep.routing] (typehaus/routing/cost.py) ---
    #: The raw ``[mep.routing]`` table, carried as a **dict** and not as a ``RouteCost``.
    #: These are the router's weights, and ``checks`` may not import ``routing`` — the leaf
    #: rule is about direction, and a check that could reach a router would be a check
    #: gradeable against its own optimiser. So the table is carried verbatim and
    #: ``routing/cost.cost_from_preferences`` turns it into weights at the one place the two
    #: packages meet, which is ``cli/cmd_route.py`` and nowhere else. Nothing in ``checks``
    #: reads it.
    routing: dict = field(default_factory=dict)


@dataclass
class StructuralPreferences:
    """House-level allowances the structural advisories grade against, not code minima."""

    # What a support may carry from a guard standing on it before the guard is too heavy for
    # ordinary wood framing. A guard's dead load is derived from its own assembly, so this is
    # the only number in that rule — roughly what a heavy wood guard with 6x6 posts weighs per
    # foot of run, which is the load a deck rim designed to R507's 40 psf live + 10 psf dead
    # was drawn expecting. A grouted-CMU-and-brick parapet is eight times it.
    max_guard_dead_load_on_wood_plf: float = 50.0
    #: The same allowance for a MASONRY WALL standing in a floor deck
    #: (``structural.through_deck_clearance``) — a sibling of the key above, not a stretch of
    #: it. The number happens to be the same and the rule is not: that one's docstring is
    #: about guards and its figure is a guard's figure, and a house that raised it for a
    #: heavy parapet would silently license a brick pier bearing on plywood.
    max_masonry_dead_load_on_wood_plf: float = 50.0
    #: How much air a floor sheet must leave round a wall passing through it, inches. A
    #: *verdict* threshold, which is why it is here and ``through_deck._SHEET_CLEARANCE_M``
    #: — the saw cut itself — is not. Catlin governs at 5/8" against this 1/2", and that 5/8"
    #: is residue of a 44 1/4" panel on a 16" module rather than a chosen margin: read a
    #: future FAIL here as information about a widening, not as a threshold to raise.
    min_through_deck_clearance_in: float = 0.5
    #: Design snow, psf, for a beam carrying a ROOF (``engineering/roof_beam.py``). Authored
    #: because the engine derives NO part of it: drift, unbalanced and sliding magnitudes are
    #: computed nowhere in this codebase, and the north entry canopy's governing case is a
    #: roof-step drift off the house gable. ``None`` is an INCOMPLETE naming this key, never
    #: a default — a defaulted design load publishes a ratio against a number nobody chose.
    roof_beam_snow_psf: float | None = None
    #: Dead load, psf, on the same beam: roofing, deck, framing and its own weight.
    roof_beam_dead_psf: float = 10.0
    #: Design snow, psf, on an exterior DECK (not a roof). R507's tables are 40 psf live with
    #: snow not concurrent, so this only decides whether they cover the deck at all.
    #: ``None``: snow is not examined, and ``structural.deck_joist_span`` says so.
    deck_snow_psf: float | None = None
    #: Width of that roof-step drift, ft (ASCE 7 §7.7.1, w = 4 h_d), measured from the far
    #: edge of the roof the beams carry. Where it outruns that roof, the trusses of the roof
    #: beyond it inside the width are drift trusses too (``structural.truss_reactions``).
    #: ``None``: the reach is unknown and a neighbouring trussed roof is held to it whole.
    roof_beam_drift_width_ft: float | None = None
    #: Modulus of subgrade reaction under a retaining wall's mat, pci, and the same number
    #: lying on its side for the buried face. **Only the analytical SHELL export reads
    #: these** (``analytical/shells.py``): a shell model of a retaining wall is a wall on
    #: springs, and a spring needs a stiffness that a bearing capacity cannot supply.
    #:
    #: ``None`` is the shipped state and the correct one. A subgrade modulus is a
    #: geotechnical measurement, not a table lookup — IBC Table 1806.2 publishes an
    #: allowable bearing PRESSURE and says nothing about how far the soil moves under it —
    #: so the engine refuses rather than defaulting, and the refusal is printed in the
    #: export's own gap register. This is the same ``BasedValue`` refusal
    #: ``engineering/sunken_garden/inputs`` applies to the courtyard's coupled model,
    #: reaching the project graph.
    soil_vertical_subgrade_pci: float | None = None
    soil_horizontal_subgrade_pci: float | None = None
    #: Where those two came from, named the way a seal names its source. Required with
    #: them: a stiffness with no basis is a number somebody typed.
    soil_subgrade_basis: str = ""


@dataclass(frozen=True)
class PrintPreferences:
    """``[print]`` from ``preferences.toml`` — what the composed set says about itself.

    The engine never asserts an issue status a person did not authorize, so ``issue`` is
    ``None`` by default and ``cli/cmd_sheets`` falls back to the honest engine defaults.
    ``permit_add`` / ``permit_drop`` are sheet-number *prefixes* that force a sheet into or
    out of the permit set — the one-line escape hatch for a reviewer who wants the E-1xx
    power plans back.
    """

    issue: str | None = None
    permit_add: tuple[str, ...] = ()
    permit_drop: tuple[str, ...] = ()


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

    # (``wall_r`` / ``roof_r`` were here and were read by NOTHING — no check, no sheet, no
    # emitter — so both houses' ``[envelope]`` entries were decorative. Deleted 2026-09-18.
    # A prescriptive requirement is the engine's (``checks.code.mn_energy``) and an as-built
    # R-value is the assembly's; a preference had nothing to say between them.)
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
    # LBL infiltration model divisor: CFMnat = CFM50 / N. ``None`` means the house has not
    # stated one and it is DERIVED from the LBL table below — base x height x shielding —
    # which is what the table is: N is not one number, and the flat 18.0 this defaulted to
    # was the two-storey-normal-shelter cell read as though it were the whole table.
    infiltration_n_factor: float | None = None
    # Storeys the LBL height correction is read at: 1, 1.5, 2 or 3. Authored, not counted
    # off the model — "how many storeys" in the LBL sense is above-grade conditioned height
    # over the leakage plane, and a storey list that holds a basement, an attic pocket and a
    # detached garage on the house's own keys cannot answer it. ``None`` names the gap.
    infiltration_storeys: float | None = None
    interior_setpoint_f: float = 70.0
    # Manual J's cooling indoor design condition. It was ``interior_setpoint_f`` for both
    # seasons, which made catlin's cooling ΔT 20 °F where Manual J's is 15 — nobody holds a
    # house at 70 °F in July, and a 33% overstated ΔT reaches every cooling component line.
    cooling_setpoint_f: float = 75.0
    interior_relative_humidity: float = 0.35
    exterior_relative_humidity: float = 0.80
    # Interior winter design RH for the monthly (ISO 13788-style) condensation gate.
    # Kept separate from ``interior_relative_humidity`` (the 99% design-hour cold-snap
    # screen) so a humidified house can raise the seasonal gate without moving the screen;
    # the default matches the screen's winter design RH rather than inventing a new figure.
    monthly_interior_relative_humidity: float = 0.35
    south_wwr_threshold: float = 0.40
    adequate_overhang_ft: float = 2.0
    # (``cooling_solar_gain_btu_per_hour_ft2`` was here: a single peak irradiance the block
    # load multiplied an orientation weight by. Deleted 2026-09-18 with the hourly method —
    # the ASHRAE clear-sky model derives the irradiance at each hour for each orientation,
    # so one number for all four at once has nothing left to say. No house authored it.)
    framing: FramingPreferences = field(default_factory=FramingPreferences)
    plumbing: PlumbingPreferences = field(default_factory=PlumbingPreferences)
    mep: MepPreferences = field(default_factory=MepPreferences)
    structural: StructuralPreferences = field(default_factory=StructuralPreferences)
    underlays: tuple[ReferenceUnderlay, ...] = ()
    print_options: PrintPreferences = field(default_factory=PrintPreferences)
    #: ``[checks] suppress`` from the house's ``preferences.toml``. Two forms, and the second
    #: is the one that makes the list usable without blinding a check:
    #:
    #: * ``"check.id"``            — drop every finding that check makes. A blunt instrument:
    #:   it takes the check's UNKNOWNs and its PASSes with it, so a house that silences a rule
    #:   this way stops being told anything by it at all.
    #: * ``"check.id:ELEMENT-TAG"`` — drop that check's findings **on that one element**.
    #:   For the case a check cannot see: a finding that is real, was looked at, and was
    #:   decided against for a reason the model does not carry. ``D-G-OVERHEAD`` is off the
    #:   stud module and moving it drags the ICF stem gap on its offset, and with
    #:   that the stem segments, their footings and a buried service sleeve; that is a
    #:   building decision the check cannot see, and the right place to record it is beside
    #:   the reason, in the house's own file.
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

        Deliberately not a 3-tuple: a form that falls through to ``else: p += 1`` would
        silently count every ``NOT_APPLICABLE`` as a pass — the exact sin #32 exists to
        forbid — without a single test failing. A tally that names its buckets cannot
        acquire that bug when a member is added.
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


_T = TypeVar("_T")
#: A scratch dict that lives for exactly one ``run_checks`` call — see :func:`shared`.
_RUN_SCOPE: ContextVar[dict[Any, Any] | None] = ContextVar("_RUN_SCOPE", default=None)


def shared(ctx: CheckContext, key: str, fn: Callable[[], _T]) -> _T:
    """``fn()``, computed once per ``run_checks`` call for this ``ctx``; outside one, just ``fn()``.

    Deliberately not cached on the model or the context: tests mutate and ``copy.copy``
    those, and a stale derived value there would silently change a verdict. Within one run
    nothing mutates underneath it. ``fn`` must return something its callers only read.
    """
    scope = _RUN_SCOPE.get()
    if scope is None:
        return fn()
    slot = (id(ctx), key)
    if slot not in scope:
        scope[slot] = fn()
    return scope[slot]


def run_checks(ctx: CheckContext, tier: Tier | None = None, *,
               only: str | Iterable[str] | None = None) -> CheckReport:
    """Run every registered check (of the given tier) plus resolve-time findings.

    ``only`` restricts the run to those *registered* ids (``ran`` says which ran). An id not
    registered in the tier raises: a typo would otherwise make an absence assertion pass.
    """
    checks = registered(tier)
    if only is not None:
        wanted = {only} if isinstance(only, str) else set(only)
        unknown = wanted - {check_id for check_id, _fn in checks}
        if unknown:
            raise ValueError(f"only= names unregistered check ids: {sorted(unknown)}")
        checks = [pair for pair in checks if pair[0] in wanted]
    findings: list[Finding] = list(ctx.resolve_findings)
    ran: list[str] = []
    token = _RUN_SCOPE.set({})
    try:
        for check_id, fn in checks:
            ran.append(check_id)
            for finding in fn(ctx):
                if _suppressed(finding, ctx.preferences.suppressed):
                    continue
                findings.append(finding)
    finally:
        _RUN_SCOPE.reset(token)
    return CheckReport(findings=findings, ran=tuple(ran),
                       engineering=ctx.engineering,
                       engineering_register=ctx.engineering_register)
