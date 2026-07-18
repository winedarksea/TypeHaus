"""Checks framework — one registry, two invokers (pytest + `haus check`) (→ 12).

Importing this package imports every tier module, registering all checks.
"""

from __future__ import annotations

from typehaus.checks import advisory, building_science, integrity, structural  # noqa: F401 - register
from typehaus.checks.code import mn_residential  # noqa: F401 - register
from typehaus.checks.registry import (
    CheckContext,
    CheckReport,
    JurisdictionProfile,
    Preferences,
    Tier,
    check,
    registered,
    run_checks,
)
from typehaus.checks.run import build_context, load_preferences, run, run_from_model

__all__ = [
    "run", "run_from_model", "build_context", "load_preferences", "run_checks", "registered", "check",
    "CheckContext", "CheckReport", "Preferences", "JurisdictionProfile", "Tier",
]
