"""Checks framework — one registry, two invokers (pytest + `haus check`) (→ 12).

Importing this package imports every tier module, registering all checks.
"""

from __future__ import annotations

from typehaus.checks import (  # noqa: F401 - register
    advisory,
    building_science,
    integrity,
    mep,
    structural,
)
from typehaus.checks.code import mn_energy, mn_residential, site  # noqa: F401 - register
from typehaus.checks.permit import PermitChecklist, PermitChecklistItem, evaluate_permit_checklist
from typehaus.checks.registry import (
    CheckContext,
    CheckReport,
    FramingPreferences,
    JurisdictionProfile,
    PlumbingPreferences,
    Preferences,
    ReferenceUnderlay,
    Tier,
    check,
    registered,
    run_checks,
)
from typehaus.checks.run import build_context, load_preferences, run, run_from_model

__all__ = [
    "run", "run_from_model", "build_context", "load_preferences", "run_checks", "registered",
    "check",
    "CheckContext", "CheckReport", "Preferences", "FramingPreferences", "PlumbingPreferences",
    "ReferenceUnderlay", "JurisdictionProfile", "Tier",
    "PermitChecklist", "PermitChecklistItem", "evaluate_permit_checklist",
]
