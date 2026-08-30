"""The MN residential rule set, one module per code article.

Importing this package is what *registers* the rules — the registry is populated by import
side effect, and ``tests/test_permit_coverage.py`` compares ``report.ran`` against every
registered id. A new rule module that is not imported here is a silent coverage hole rather
than a failure, which is why the list below is exhaustive rather than lazy.
"""

from __future__ import annotations

from typehaus.checks.code.mn_residential import (  # noqa: F401 - registers checks
    alarms,
    attic,
    attic_ventilation,
    circulation,
    egress,
    energy_storage,
    fall_protection,
    fire_separation,
    foam_plastic,
    foundation_protection,
    glazing,
    illumination,
    radon,
    rules,
    stair_guards,
    stairs,
    ventilation,
)
from typehaus.checks.code.mn_residential.profile import MN_2024, PROFILES, get_profile

__all__ = ["MN_2024", "PROFILES", "get_profile"]
