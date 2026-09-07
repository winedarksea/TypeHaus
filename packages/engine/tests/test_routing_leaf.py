"""``typehaus.routing`` and ``typehaus.engineering`` are leaves, and this is what says so.

The rule for both is the same and it is a design commitment rather than tidiness:

* **``routing`` proposes and never grades.** A search result is not a fact about the
  building, and a ``Finding`` whose verdict moves when a cost weight moves is not a
  finding. So nothing in ``checks/``, ``resolve/``, ``takeoff/`` or ``emit/`` may reach for
  a route, and ``routing`` may not reach back into them.
* **``engineering`` computes and never checks.** Its output is an ``EngineeringRecord`` —
  demand, capacity, ratio, governing limit state, citation — and ``Finding`` has nowhere to
  hold numbers. ``checks/_authoring.engineered()`` is the one bridge.

``engineering``'s half of that has been stated in prose in the root ``CLAUDE.md`` and
enforced by nothing. It is enforced here now, alongside the package written to the same
rule, because a leaf rule that only one of two leaves is tested for is a rule about one
package.

The walk is over the AST rather than over ``sys.modules``: a lazy import inside a function
is still an import, and hiding a dependency behind ``def`` would be exactly the way this
rule gets broken by somebody who means well.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

_SRC = pathlib.Path(__file__).resolve().parents[1] / "src" / "typehaus"

#: What each leaf may reach. Everything under ``typehaus`` outside this set is forbidden;
#: third-party and stdlib imports are not this test's business.
_ALLOWED = {
    "routing": {"model", "resolve", "quantities", "routing"},
    "engineering": {"model", "resolve", "quantities", "wind", "wind_tables",
                    "engineering", "findings"},
}

#: Named and excused, with the reason, rather than silently permitted by a loose rule.
#: ``findings`` is a leaf itself (``resolve`` and ``source`` both import it), so an
#: engineering module reaching it is not reaching into the checks tree.
_EXCUSED: dict[str, set[str]] = {}


def _typehaus_imports(path: pathlib.Path) -> set[str]:
    """Every ``typehaus.<top>`` a module names, from anywhere in the file.

    Function-local imports count. ``routing/obstacles.py`` imports
    ``resolve.mep_queries`` inside a function for start-up cost, not to dodge this test,
    and a rule that could not see it would be worth nothing.
    """
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


@pytest.mark.parametrize("package", sorted(_ALLOWED))
def test_the_package_is_a_leaf(package: str) -> None:
    root = _SRC / package
    assert root.is_dir(), f"{package} is not a package"
    offences: list[str] = []
    for path in sorted(root.rglob("*.py")):
        allowed = _ALLOWED[package] | _EXCUSED.get(str(path.relative_to(_SRC)), set())
        for top in sorted(_typehaus_imports(path) - allowed):
            offences.append(f"{path.relative_to(_SRC)} imports typehaus.{top}")
    assert not offences, (
        f"typehaus.{package} is a leaf and may import only "
        f"{sorted(_ALLOWED[package])}:\n  " + "\n  ".join(offences))


def test_nothing_upstream_reaches_for_the_router() -> None:
    """The other direction, and the more important one.

    A check that consulted a router would be reporting a search result as a fact about the
    building. ``cli/`` is the one place ``checks`` and ``routing`` meet, and it sits above
    both, which is what keeps the leaf rule true rather than merely stated.
    """
    offenders: list[str] = []
    for package in ("checks", "resolve", "takeoff", "emit", "source", "model"):
        for path in sorted((_SRC / package).rglob("*.py")):
            if "routing" in _typehaus_imports(path):
                offenders.append(str(path.relative_to(_SRC)))
    assert not offenders, (
        "only cli/ may import typehaus.routing — a search result is not a Finding:\n  "
        + "\n  ".join(offenders))
