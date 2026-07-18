"""Brand-name and build-identity constants, centralized for cheap rename (→ 01 §Naming).

A rename touches only this file, the ``pyproject.toml`` ``name``, the ``src/typehaus``
directory, and the UI ``branding.ts`` — see ``docs/RENAME.md``.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

PROJECT_NAME = "Type:Haus"
PROJECT_SLUG = "typehaus"
PROJECT_URL = "https://type-haus.com"
CLI_NAME = "haus"

# IFC header application name and pset prefix. The prefix is kept short and
# brand-agnostic so the emitted IFC does not churn on a rename (→ 01 §Naming).
IFC_APP_NAME = "Type:Haus"
PSET_PREFIX = "Pset_TH"
PSET_SOURCE = f"{PSET_PREFIX}_Source"


def engine_version() -> str:
    """Installed engine version, or a dev sentinel when running from a source tree."""
    try:
        return version(PROJECT_SLUG)
    except PackageNotFoundError:
        return "0.0.0+dev"
