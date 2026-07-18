"""Check orchestration: load preferences, build a CheckContext, run the registry (→ 12)."""

from __future__ import annotations

from pathlib import Path

try:  # tomllib is stdlib on 3.11+; fall back to tomli on older interpreters
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]

from typehaus.checks.code.mn_residential.profile import get_profile
from typehaus.checks.registry import (
    CheckContext,
    CheckReport,
    Preferences,
    Tier,
    run_checks,
)
from typehaus.findings import Finding
from typehaus.model.plan import PlanModel
from typehaus.resolve import ResolvedModel, resolve


def load_preferences(house_dir: Path) -> Preferences:
    path = house_dir / "preferences.toml"
    if not path.exists():
        return Preferences()
    data = tomllib.loads(path.read_text())
    env = data.get("envelope", {})
    suppressed = frozenset(data.get("checks", {}).get("suppress", []))
    return Preferences(
        wall_r=env.get("wall_r"), roof_r=env.get("roof_r"),
        window_u=env.get("window_u"), ach50=env.get("ach50"),
        suppressed=suppressed,
    )


def build_context(plan: PlanModel, house_dir: Path | None = None,
                  profile: str = "mn-2024") -> tuple[CheckContext, list[Finding]]:
    model, resolve_findings = resolve(plan)
    prefs = load_preferences(house_dir) if house_dir else Preferences()
    ctx = CheckContext(
        plan=plan, model=model, preferences=prefs,
        profile=get_profile(profile), resolve_findings=resolve_findings,
    )
    return ctx, resolve_findings


def run(plan: PlanModel, house_dir: Path | None = None, profile: str = "mn-2024",
        tier: Tier | None = None) -> CheckReport:
    ctx, _ = build_context(plan, house_dir, profile)
    return run_checks(ctx, tier)


def run_from_model(model: ResolvedModel, resolve_findings: list[Finding],
                   house_dir: Path | None = None, profile: str = "mn-2024",
                   tier: Tier | None = None) -> CheckReport:
    prefs = load_preferences(house_dir) if house_dir else Preferences()
    ctx = CheckContext(plan=model.plan, model=model, preferences=prefs,
                       profile=get_profile(profile), resolve_findings=resolve_findings)
    return run_checks(ctx, tier)
