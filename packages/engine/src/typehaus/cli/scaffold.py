"""``haus new`` scaffolder (→ 20 §brief.md, WP2.12).

Copies a shipped house as the starting point rather than writing one out of inline string
constants: ``houses/starter`` by default (a small, immediately-buildable two-storey house)
or ``houses/catlin`` with ``--template catlin``. The inline "minimal" template that used to
live here was a third copy of the starter plan and drifted from it — a scaffolded house that
no test ever built.
"""

from __future__ import annotations

import re
import shutil
import uuid
from pathlib import Path


class ScaffoldError(RuntimeError):
    """No copy of the requested template house is reachable from here."""


TEMPLATES = ("starter", "catlin")


def scaffold_house(directory: Path, name: str, template: str = "starter") -> list[Path]:
    """Scaffold a new house by copying ``houses/<template>`` (#22)."""
    directory = directory.resolve()
    if template not in TEMPLATES:
        raise ValueError(f"unknown template {template!r} ({' | '.join(TEMPLATES)})")
    source = _find_template(directory, template)
    if source is None:
        raise ScaffoldError(
            f"no houses/{template} found near {directory} or {Path.cwd()} — "
            "run `haus new` inside a checkout that ships the template houses"
        )
    return _copy_template(source, directory, name)


def _find_template(start: Path, template: str) -> Path | None:
    """Walk up from the new house dir (then cwd) to find ``houses/<template>``.

    Same walk-up discovery as ``loader._find_library_root``: it must not assume the engine
    is running out of the monorepo.
    """
    for base in (start, Path.cwd()):
        for parent in (base, *base.parents):
            candidate = parent / "houses" / template
            if (candidate / "plan" / "manifest.py").is_file():
                return candidate
    # Installed from a wheel there is no checkout to walk up: the default template ships
    # inside the package (see pyproject's force-include).
    packaged = Path(__file__).resolve().parent.parent / "templates" / template
    if (packaged / "plan" / "manifest.py").is_file():
        return packaged
    return None


def _copy_template(source: Path, directory: Path, name: str) -> list[Path]:
    """Copy the template's plan source verbatim, minting a fresh project uuid + name.

    Element uids are kept: GlobalIds derive from (project_uuid, uid), so a fresh
    project uuid is what makes the copy a distinct project (→ 10 §IDs).
    """
    directory.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for rel in ("plan", "params", "notes"):
        src = source / rel
        if src.is_dir():
            shutil.copytree(src, directory / rel, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns("__pycache__"))
            written.extend(sorted(p for p in (directory / rel).rglob("*") if p.is_file()))
    for rel in ("brief.md", "preferences.toml", "CLAUDE.md"):
        src = source / rel
        if src.is_file():
            dest = directory / rel
            shutil.copyfile(src, dest)
            written.append(dest)
    manifest = directory / "plan" / "manifest.py"
    text = manifest.read_text()
    text = re.sub(r'PROJECT_UUID = uuid\.UUID\("[0-9a-fA-F-]+"\)',
                  f'PROJECT_UUID = uuid.UUID("{uuid.uuid4()}")', text)
    if name and name != "My House":
        # The Project's own name, not the Building's: match the first `name=` kwarg only.
        text = re.sub(r'name="[^"]*"', f'name="{name}"', text, count=1)
    manifest.write_text(text)
    return written
