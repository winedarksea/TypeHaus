"""Loader-discovered storey modules: ``plan/storeys/<tag>.py`` declaring ``STOREY = Storey(...)``.

The UI's "Add floor" writes one of these instead of editing ``manifest.py`` (plain Python, not
editable). The loader appends each discovered storey after the manifest's own and fills it with
every module-level list of elements, so writeback, undo and the watcher need no special case.
"""

from __future__ import annotations

import ast
import importlib
import re
from pathlib import Path

from typehaus.findings import Finding, Severity, SourceLoc
from typehaus.model.base import Element
from typehaus.model.plan import PlanModel
from typehaus.model.project import Storey
from typehaus.source.dialect import is_editable

TAG_RE = re.compile(r"^[a-z][a-z0-9_]*$")

# Lists the template declares; writeback routes adds into them by name.
ELEMENT_LISTS = ("NODES", "WALLS", "OPENINGS", "ROOMS", "STAIRS", "FLOOR_OPENINGS")


def _declares_storey(source: str) -> bool:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    for node in tree.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name) and node.targets[0].id == "STOREY"
                and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name)
                and node.value.func.id == "Storey"):
            return True
    return False


def discover(house_dir: Path) -> list[Path]:
    """Editable ``plan/storeys/*.py`` files with a module-level ``STOREY = Storey(...)``."""
    root = house_dir / "plan" / "storeys"
    if not root.is_dir():
        return []
    found = []
    for path in sorted(root.glob("*.py")):
        try:
            source = path.read_text()
        except OSError:
            continue
        if is_editable(source) and _declares_storey(source):
            found.append(path)
    return found


def append_storey_modules(house_dir: Path, plan: PlanModel,
                          findings: list[Finding]) -> PlanModel:
    """Import each discovered module and append its storey + elements to ``plan``.

    Must run inside the manifest import window (lock, ``sys.path``, authorship capture)."""
    for path in discover(house_dir):
        rel = path.relative_to(house_dir).as_posix()
        module = importlib.import_module(f"plan.storeys.{path.stem}")
        storey = getattr(module, "STOREY", None)
        if not isinstance(storey, Storey):
            continue
        if plan.storey(storey.tag) is not None:
            findings.append(Finding(
                severity=Severity.ERROR, check_id="loader.storey_duplicate",
                message=f"storey {storey.tag!r} in {rel} is already declared; a discovered "
                        "storey module must not also be wired in manifest.py",
                source_loc=SourceLoc(file=rel, line=1),
            ))
            continue
        elements: list[Element] = []
        for name, value in vars(module).items():
            if (not name.startswith("_") and isinstance(value, (list, tuple))
                    and all(isinstance(v, Element) and not isinstance(v, Storey)
                            for v in value)):
                elements.extend(value)
        plan = (plan.model_copy(update={"storeys": (*plan.storeys, storey)})
                .with_elements(storey.tag, elements))
    return plan


def render_storey_module(tag: str, elevation: str, ceiling_height: str, uid: str) -> str:
    """Source for a new storey module. ``elevation``/``ceiling_height`` are dialect source
    (``ft(9)``); ``uid`` must be engine-minted."""
    if not TAG_RE.match(tag):
        raise ValueError(f"storey tag {tag!r} must match {TAG_RE.pattern}")
    lists = "\n".join(f"{name} = []" for name in (*ELEMENT_LISTS, f"{tag.upper()}_PLACEABLES"))
    return (
        "# haus: editable\n"
        f"# Storey {tag!r}: discovered by the loader; do not also wire it in manifest.py.\n"
        "from typehaus import Storey, ft, m\n\n"
        f'STOREY = Storey(uid="{uid}", tag="{tag}", elevation={elevation}, '
        f"default_ceiling_height={ceiling_height})\n\n"
        f"{lists}\n"
    )
