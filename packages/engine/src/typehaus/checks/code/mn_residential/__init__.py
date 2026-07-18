from __future__ import annotations

from typehaus.checks.code.mn_residential import rules  # noqa: F401 - registers checks
from typehaus.checks.code.mn_residential.profile import MN_2024, PROFILES, get_profile

__all__ = ["MN_2024", "PROFILES", "get_profile"]
