"""Nobody loads the reference house by name again.

A full ``load_plan`` + ``resolve`` + ``run_checks`` on catlin is ~20 s and does not get
cheaper on a repeat. Before the fixtures landed, ~74 call sites across the suite each paid
their own, for bytes that had not changed since the last one — ``test_catlin_contract_m3.py``
alone ran the registry twelve times, once per test function.

``AGENTS.md`` §3 already said "take the highest-scoped fixture you can". Nothing enforced it,
which is how it drifted, so this module is the enforcement: pure AST, no engine import, tens
of milliseconds, deliberately NOT ``slow``.

The rule is about FORM, not about intent, and that is what makes the legitimate exceptions
fall out for free: it flags ``load_plan(CATLIN)`` where the argument is literally that name.
A ``copy_house`` sandbox passes a local (``load_plan(dst)``) and is never flagged; so is
every mutated variant. What is left over is a short list of files that really do need their
own load, and each one says why.
"""

from __future__ import annotations

import ast
import pathlib
from functools import cache

import pytest

_TESTS = pathlib.Path(__file__).resolve().parent

#: The names ``_helpers`` exports for the reference house.
_CATLIN_NAMES = {"CATLIN", "CATLIN_DIR"}

#: The expensive compositions, and the fixture that already holds each one.
_INSTEAD = {
    "load_plan": "catlin_plan",
    "resolve": "catlin_model_ro",
    "build_context": "catlin_ctx",
    "run": "catlin_check_report()",
    "build_sheet_index": "catlin_sheet_index()",
}

#: file -> (how many catlin loads it may pay for, why it may).
#:
#: **This table can only go down.** Every number in it went down when the fixtures landed,
#: and an entry that no longer corresponds to a real load is a lie about the suite — which
#: ``test_the_budget_table_is_not_stale`` below is what catches.
_BUDGET: dict[str, tuple[int, str]] = {
    "conftest.py": (
        1, "the fixture itself — this is the one load the whole suite shares"),
    "test_editable_guard.py": (
        3, "needs the LoadResult's FINDINGS (loader.uneditable_movable_element), which "
           "catlin_plan discards"),
    "test_electrical_circuits.py": (
        3, "each is the baseline a mutated device variant is built from, in a module whose "
           "whole subject is what happens when a port or a cabinet is dropped"),
    "test_ifc_structural_enrichment.py": (
        2, "emits an IFC at a NON-default LOD with engineering enrichment; the shared "
           "catlin_ifc_path is the framed default and is a different file"),
    "test_model_json.py": (
        1, "reads `result.provenance` off the LoadResult, which catlin_plan discards"),
    "test_member_interference.py": (
        1, "empties `ctx.model.junctions`; a shared model must never be mutated"),
    "test_concrete_interference.py": (
        1, "builds a plan variant with a pad's `cast_with` dropped"),
    "test_work_packages.py": (
        1, "a module-level helper reads only `.storeys`; a fixture cannot reach it"),
    "test_catlin_bath2_tub_deck.py": (
        1, "a @cache'd module helper — one load for the module, not one per test"),
    "test_catlin_bath2_vanity_heat_and_joists.py": (
        1, "a @cache'd module helper — one load for the module, not one per test"),
    "test_catlin_bathroom_vanities.py": (
        1, "a @cache'd module helper — one load for the module, not one per test"),
    "test_masonry_finish.py": (
        0, "its one `run(plan)` carries NO house_dir — an empty Preferences, so a different "
           "suppression set and jurisdiction — but it takes the plan from the fixture"),
}


@cache
def _tree(path: pathlib.Path) -> ast.AST:
    """Parsed once. Both rules below walk every module in the suite."""
    return ast.parse(path.read_text(), filename=str(path))


def _modules() -> list[pathlib.Path]:
    return sorted(p for p in _TESTS.glob("*.py") if p.name != pathlib.Path(__file__).name)


def _catlin_loads(tree: ast.AST) -> list[ast.Call]:
    """Every ``load_plan(CATLIN)`` / ``load_plan(CATLIN_DIR)`` call in a module.

    Form-based on purpose: the argument must be one of the two names ``_helpers`` exports.
    A sandbox's ``load_plan(dst)`` names a local and is not this.
    """
    return [node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name) and node.func.id == "load_plan"
            and node.args
            and isinstance(node.args[0], ast.Name) and node.args[0].id in _CATLIN_NAMES]


def _is_catlin_load(node: ast.expr) -> bool:
    """``load_plan(CATLIN)``, or ``.plan`` / ``.findings`` read off one."""
    if isinstance(node, ast.Attribute):
        node = node.value
    return (isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name) and node.func.id == "load_plan"
            and bool(node.args)
            and isinstance(node.args[0], ast.Name) and node.args[0].id in _CATLIN_NAMES)


@pytest.mark.parametrize("path", _modules(), ids=lambda p: p.name)
def test_no_module_loads_the_reference_house_beyond_its_budget(path: pathlib.Path) -> None:
    budget, _why = _BUDGET.get(path.name, (0, ""))
    found = _catlin_loads(_tree(path))
    assert len(found) <= budget, (
        f"{path.name} loads the real catlin {len(found)} times (budget {budget}). A load + "
        f"resolve + run on this house is ~20 s and does not get cheaper on a repeat — take "
        f"`catlin_plan` / `catlin_model_ro` / `catlin_ctx` / `catlin_check_report` / "
        f"`catlin_sheet_index` from conftest (→ AGENTS.md §3). If this module genuinely "
        f"needs its own, raise its entry in _BUDGET and say why in the same line.\n  "
        + "\n  ".join(f"line {node.lineno}" for node in found))


@pytest.mark.parametrize("path", _modules(), ids=lambda p: p.name)
def test_the_expensive_composition_is_never_built_on_a_fresh_load(path: pathlib.Path) -> None:
    """``run(load_plan(CATLIN).plan, ...)`` and friends — the shape that cost the most.

    Separate from the budget above because it names the fixture to take instead: a bare
    load is 4.7 s, but a ``run`` or a ``build_sheet_index`` on top of one is the full ~20 s.

    A module that already holds a budget is skipped: it has been looked at, one line above
    says what it spends and why, and the point of this rule is to meet the NEXT one with a
    message that names the fixture rather than to restate a decision already recorded.
    """
    if path.name in _BUDGET:
        pytest.skip(f"{path.name} holds a budget: {_BUDGET[path.name][1]}")
    offences: list[str] = []
    for node in ast.walk(_tree(path)):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
            continue
        name = node.func.id
        if name in _INSTEAD and name != "load_plan" and node.args \
                and _is_catlin_load(node.args[0]):
            offences.append(
                f"line {node.lineno}: {name}(load_plan(CATLIN)…) "
                f"— take `{_INSTEAD[name]}` instead")
    assert not offences, (
        f"{path.name} rebuilds the reference house to compose something on top of it; that "
        f"is the ~20 s shape, not the 4.7 s one:\n  " + "\n  ".join(offences))


def test_the_budget_table_is_not_stale() -> None:
    """Every excused file must still exist and still spend what it is excused for.

    A budget nobody is using any more is a claim about the suite that stopped being true,
    and the next person reads it as a reason not to bother.
    """
    stale: list[str] = []
    for name, (budget, why) in sorted(_BUDGET.items()):
        path = _TESTS / name
        if not path.is_file():
            stale.append(f"{name}: no such module — drop the entry")
            continue
        found = len(_catlin_loads(_tree(path)))
        if found < budget:
            stale.append(f"{name}: budget {budget}, actual {found} — lower it to {found}")
        assert why, f"{name}: every entry states its reason"
    assert not stale, "\n  ".join(stale)
