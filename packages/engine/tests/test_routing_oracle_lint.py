"""Every routing module names a note that exists, or says why it names none.

The sibling of ``test_calc_package.py``'s lint over ``engineering``'s ``ORACLES``. CLAUDE.md
says every calculation is oracled against a hand-worked note; a module added to
``typehaus.routing`` without one should fail a test rather than pass quietly, and a module
that computes nothing should have to say so out loud rather than by omission.
"""

from __future__ import annotations

import pathlib

import pytest
from _helpers import CATLIN

from typehaus.routing.oracle import NOT_A_CALCULATION, ORACLES

_ROUTING = pathlib.Path(__file__).resolve().parents[1] / "src" / "typehaus" / "routing"


def _modules() -> set[str]:
    return {str(path.relative_to(_ROUTING).with_suffix("")).replace("\\", "/")
            for path in _ROUTING.rglob("*.py")}


def test_every_module_is_oracled_or_declared_not_a_calculation() -> None:
    unaccounted = _modules() - set(ORACLES) - NOT_A_CALCULATION
    assert not unaccounted, (
        "add these to routing/oracle.py — either the note that verifies them, or "
        f"NOT_A_CALCULATION with the reason: {sorted(unaccounted)}")


def test_no_stale_entry_names_a_module_that_is_gone() -> None:
    modules = _modules()
    assert not set(ORACLES) - modules, sorted(set(ORACLES) - modules)
    assert not NOT_A_CALCULATION - modules, sorted(NOT_A_CALCULATION - modules)


@pytest.mark.parametrize("module", sorted(ORACLES))
def test_every_named_note_exists_on_disk(module: str) -> None:
    for oracle in ORACLES[module]:
        assert (CATLIN / "notes" / oracle.note).is_file(), oracle.note


@pytest.mark.parametrize("module", sorted(ORACLES))
def test_every_named_test_module_exists(module: str) -> None:
    """A note nobody reproduces is a document, not an oracle."""
    for oracle in ORACLES[module]:
        if not oracle.test:
            continue
        assert (pathlib.Path(__file__).resolve().parents[1] / oracle.test).is_file(), (
            oracle.test)
