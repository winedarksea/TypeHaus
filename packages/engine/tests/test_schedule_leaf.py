"""``typehaus.schedule`` is a leaf, and this is what says so.

The rule, and it is a design commitment rather than tidiness: **readiness is derived from
facts, and it is not itself a fact about the building.** A visit is blocked because a
``Finding`` says a wall fails, not because this package decided anything about the wall.
So ``schedule/`` may read the model, the takeoff and the findings somebody else produced —
and nothing in ``checks/``, ``resolve/``, ``takeoff/`` or ``emit/`` may reach back for a
readiness state. A verdict that moved when a sub rescheduled would not be a verdict.

Written to the same shape as ``test_routing_leaf.py``, and the walk is over the AST for the
same reason: a lazy import inside a function is still an import.
"""

from __future__ import annotations

import ast
import pathlib

_SRC = pathlib.Path(__file__).resolve().parents[1] / "src" / "typehaus"

#: Everything under ``typehaus`` outside this set is forbidden. ``checks`` is deliberately
#: absent: the package reads ``checks.jurisdiction`` (an inspection is *data* on a profile)
#: and is excused for exactly that below, module by module, so nobody can reach the check
#: registry by widening one line.
_ALLOWED = {"model", "resolve", "quantities", "findings", "takeoff", "emit", "schedule"}

_EXCUSED: dict[str, set[str]] = {
    # ``InspectionSpec`` lives beside ``PermitItemSpec`` because the two are the same kind
    # of thing — a jurisdiction's own declared list — and a second copy of the shape here
    # would be a second definition of what a jurisdiction requires.
    "schedule/model.py": set(),
    "schedule/inspection_state.py": {"checks"},
    "schedule/milestones.py": set(),
    "schedule/readiness.py": set(),
}


def _typehaus_imports(path: pathlib.Path) -> set[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            parts = node.module.split(".")
            if parts[0] == "typehaus" and len(parts) > 1:
                found.add(parts[1])
        elif isinstance(node, ast.Import):
            for alias in node.names:
                parts = alias.name.split(".")
                if parts[0] == "typehaus" and len(parts) > 1:
                    found.add(parts[1])
    return found


def test_schedule_is_a_leaf() -> None:
    offences: list[str] = []
    for path in sorted((_SRC / "schedule").rglob("*.py")):
        allowed = _ALLOWED | _EXCUSED.get(str(path.relative_to(_SRC)), set())
        for top in sorted(_typehaus_imports(path) - allowed):
            offences.append(f"{path.relative_to(_SRC)} imports typehaus.{top}")
    assert not offences, (
        "typehaus.schedule is a leaf and may import only "
        f"{sorted(_ALLOWED)}:\n  " + "\n  ".join(offences))


def test_a_checks_import_names_only_the_jurisdiction_module() -> None:
    """The one excused ``checks`` edge must stay ``checks.jurisdiction``.

    Reaching ``checks.registry`` or ``checks.run`` from here would make a readiness state
    depend on running the checks, which is how "derived" quietly becomes "computed".
    """
    offenders: list[str] = []
    for path in sorted((_SRC / "schedule").rglob("*.py")):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            module = getattr(node, "module", None) if isinstance(node, ast.ImportFrom) else None
            if module and module.startswith("typehaus.checks") \
                    and not module.startswith("typehaus.checks.jurisdiction"):
                offenders.append(f"{path.relative_to(_SRC)} imports {module}")
    assert not offenders, "\n  ".join(offenders)


def test_nothing_upstream_reaches_for_the_schedule() -> None:
    """The other direction, and the more important one."""
    offenders: list[str] = []
    for package in ("checks", "resolve", "takeoff", "emit", "source", "model",
                    "routing", "engineering"):
        for path in sorted((_SRC / package).rglob("*.py")):
            if "schedule" in _typehaus_imports(path):
                offenders.append(str(path.relative_to(_SRC)))
    assert not offenders, (
        "only cli/ and server/ may import typehaus.schedule — a readiness state is not a "
        "fact about the building:\n  " + "\n  ".join(offenders))
