"""Check orchestration: load preferences, build a CheckContext, run the registry (→ 12)."""

from __future__ import annotations

from pathlib import Path

try:  # tomllib is stdlib on 3.11+; fall back to tomli on older interpreters
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]

from typehaus.checks.code.mn_residential.profile import DEFAULT_PROFILE_NAME, get_profile
from typehaus.checks.jurisdiction import JurisdictionProfile
from typehaus.checks.registry import (
    CheckContext,
    CheckReport,
    FramingPreferences,
    MepPreferences,
    PlumbingPreferences,
    Preferences,
    ReferenceUnderlay,
    StructuralPreferences,
    Tier,
    run_checks,
)
from typehaus.checks.soil import site_soil_class
from typehaus.engineering import (
    EngineeringContext,
    EngineeringRegister,
    EngineeringResults,
    load_register,
)
from typehaus.findings import Finding
from typehaus.model.plan import PlanModel
from typehaus.resolve import ResolvedModel, resolve


def load_preferences(house_dir: Path) -> Preferences:
    path = house_dir / "preferences.toml"
    if not path.exists():
        return Preferences()
    data = tomllib.loads(path.read_text())
    project = data.get("project", {})
    env = data.get("envelope", {})
    framing = data.get("framing", {})
    plumbing = data.get("plumbing", {})
    structural = data.get("structural", {})
    underlays = tuple(ReferenceUnderlay(
        path=item["path"], storey=item["storey"],
        origin_x_m=float(item.get("origin_x_m", 0.0)),
        origin_y_m=float(item.get("origin_y_m", 0.0)),
        width_m=float(item["width_m"]), height_m=float(item["height_m"]),
        rotation_deg=float(item.get("rotation_deg", 0.0)),
        opacity=float(item.get("opacity", 0.25)),
    ) for item in data.get("underlay", ()))
    mep = data.get("mep", {})
    suppressed = frozenset(data.get("checks", {}).get("suppress", []))
    return Preferences(
        wall_r=env.get("wall_r"), roof_r=env.get("roof_r"),
        window_u=env.get("window_u"), ach50=env.get("ach50"),
        cfm50=env.get("cfm50"),
        infiltration_n_factor=env.get("infiltration_n_factor", 18.0),
        interior_setpoint_f=env.get("interior_setpoint_f", 70.0),
        interior_relative_humidity=env.get("interior_relative_humidity", 0.35),
        monthly_interior_relative_humidity=env.get(
            "monthly_interior_relative_humidity", 0.35),
        exterior_relative_humidity=env.get("exterior_relative_humidity", 0.80),
        south_wwr_threshold=env.get("south_wwr_threshold", 0.40),
        adequate_overhang_ft=env.get("adequate_overhang_ft", 2.0),
        cooling_solar_gain_btu_per_hour_ft2=env.get(
            "cooling_solar_gain_btu_per_hour_ft2", 164.0
        ),
        framing=FramingPreferences(
            module_in=framing.get("module_in", 16.0),
            corner=framing.get("corner", "3-stud"),
            max_window_ro_unbroken_in=framing.get("max_window_ro_unbroken_in", 14.0),
            max_window_ro_nonbearing_in=framing.get("max_window_ro_nonbearing_in", 30.0),
            max_window_ro_bearing_in=framing.get("max_window_ro_bearing_in", 27.0),
            interference_tolerance_in=framing.get("interference_tolerance_in", 0.25),
        ),
        plumbing=PlumbingPreferences(
            drain_stack_required_structure_in=plumbing.get(
                "drain_stack_required_structure_in", 5.5),
            visible_basement_material=plumbing.get("visible_basement_material"),
            visible_basement_finish=plumbing.get("visible_basement_finish"),
        ),
        mep=MepPreferences(
            max_run_developed_over_straight=mep.get(
                "max_run_developed_over_straight", 2.5),
            min_graded_run_ft=mep.get("min_graded_run_ft", 20.0),
        ),
        structural=StructuralPreferences(
            max_guard_dead_load_on_wood_plf=structural.get(
                "max_guard_dead_load_on_wood_plf", 50.0),
        ),
        underlays=underlays,
        suppressed=suppressed,
        jurisdiction=project.get("jurisdiction"),
    )


def resolve_profile(preferences: Preferences,
                    explicit: str | None = None) -> JurisdictionProfile:
    """Pick the jurisdiction, in precedence order: explicit flag > preferences.toml > default.

    This lets a house state its own jurisdiction via ``preferences.toml``'s ``jurisdiction``
    key, which ``haus new`` already writes, without needing an explicit flag at every call
    site.
    """
    name = explicit or preferences.jurisdiction or DEFAULT_PROFILE_NAME
    return get_profile(name)


def build_engineering(model: ResolvedModel, prefs: Preferences, house_dir: Path | None,
                      soil_class: str | None = None) -> tuple[EngineeringResults,
                                                              EngineeringRegister]:
    """The suite's result map and the house's seal register, for one CheckContext.

    One construction point, called from both context builders below, so ``haus check``,
    ``run_from_model`` (the cover sheet's caller) and the pytest plugin cannot disagree
    about whether a house has engineering in it — the exact class of divergence that once
    had A-000 lettering "NOT READY" over a set ``haus print`` had just certified.

    The results map is lazy: constructing it computes nothing.
    """
    results = EngineeringResults(
        EngineeringContext(plan=model.plan, model=model, preferences=prefs,
                           soil_class=soil_class))
    return results, load_register(house_dir)


def build_context(plan: PlanModel, house_dir: Path | None = None,
                  profile: str | None = None) -> tuple[CheckContext, list[Finding]]:
    model, resolve_findings = resolve(plan)
    prefs = load_preferences(house_dir) if house_dir else Preferences()
    jurisdiction = resolve_profile(prefs, profile)
    # `site_soil_class`, not `jurisdiction.soil_class`: the site's own soils report wins over
    # the profile's presumptive regional figure, and the engineering suite must read the
    # same order the checks do or a wall could be screened against one class and graded
    # against another.
    engineering, register = build_engineering(model, prefs, house_dir,
                                              site_soil_class(plan, jurisdiction))
    ctx = CheckContext(
        plan=plan, model=model, preferences=prefs,
        profile=jurisdiction, resolve_findings=resolve_findings,
        engineering=engineering, engineering_register=register,
    )
    return ctx, resolve_findings


def run(plan: PlanModel, house_dir: Path | None = None, profile: str | None = None,
        tier: Tier | None = None) -> CheckReport:
    ctx, _ = build_context(plan, house_dir, profile)
    return run_checks(ctx, tier)


def run_from_model(model: ResolvedModel, resolve_findings: list[Finding],
                   house_dir: Path | None = None, profile: str | None = None,
                   tier: Tier | None = None,
                   preferences: Preferences | None = None) -> CheckReport:
    """Run the registry against an already-resolved model.

    ``preferences`` wins over ``house_dir`` for callers that have already loaded them and
    hold no directory. The cover sheet is exactly that caller, and passing neither is what
    made it disagree with the gate: an empty ``Preferences()`` hides ``[envelope].ach50``,
    so A-000 lettered "NOT READY" over a set ``haus print`` had just certified — the one
    sheet whose whole job is to state the verdict, stating a different one.
    """
    prefs = preferences or (load_preferences(house_dir) if house_dir else Preferences())
    jurisdiction = resolve_profile(prefs, profile)
    engineering, register = build_engineering(model, prefs, house_dir,
                                              site_soil_class(model.plan, jurisdiction))
    ctx = CheckContext(plan=model.plan, model=model, preferences=prefs,
                       profile=jurisdiction,
                       resolve_findings=resolve_findings,
                       engineering=engineering, engineering_register=register)
    return run_checks(ctx, tier)
