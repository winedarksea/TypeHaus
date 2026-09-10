"""Stage the `haus new` starter template into the build, from either source layout.

`haus new` scaffolds from a template. In a checkout `cli/scaffold._find_template` walks up to
`houses/<template>`; a pip-installed engine has no checkout to walk, so the template has to
ship inside the wheel or `haus new` cannot scaffold anything — which is exactly what 0.1.0a0
did, and why it was unusable.

A plain `force-include` of `../../houses/starter` cannot do this job, because it is resolved
against the project directory and PyPI gets an sdist as well as a wheel. In the monorepo the
template is two levels up; in an extracted sdist it sits beside `pyproject.toml`. A static
path is right in one layout and a hard build failure in the other, so a wheel built from the
published sdist would not match the wheel built from the repo. This hook looks in both.

Only `starter`: the catlin reference house is a checkout-only template.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

# Everything a scaffolded house needs. `plan/` is a directory; the rest are single files.
_TEMPLATE_PARTS = ("plan", "brief.md", "preferences.toml", "CLAUDE.md")


def _template_root(project_root: Path) -> Path:
    """The starter house, in the monorepo layout or in an extracted sdist."""
    for candidate in (project_root / ".." / ".." / "houses" / "starter",
                      project_root / "houses" / "starter"):
        if (candidate / "plan" / "manifest.py").is_file():
            return candidate.resolve()
    raise FileNotFoundError(
        "no houses/starter template found beside packages/engine or at the project root; "
        "`haus new` would ship unable to scaffold a house"
    )


class StarterTemplateHook(BuildHookInterface):  # type: ignore[type-arg]
    PLUGIN_NAME = "starter-template"

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        root = _template_root(Path(self.root))
        forced = build_data.setdefault("force_include", {})
        for part in _TEMPLATE_PARTS:
            source = root / part
            if source.exists():
                forced[str(source)] = f"typehaus/templates/starter/{part}"
