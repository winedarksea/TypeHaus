"""``typehaus.hardware`` is a leaf, and this is what says so.

What a Simpson part *is* — its role, its allowable, the report the number was read out of —
and the named spacings a derivation applies are facts about products and rules, not about a
building. They lived in ``takeoff/`` until they were promoted, which made them look like
take-off private property while ``checks/structural``, ``emit/draw``, ``joints/`` and
``schedule/handoff`` were already importing them: a layering inversion that compiled.

So the rule: ``hardware`` reads the standard library and ``typehaus.library`` (the catalog
*items*, the same split as ``Material`` / ``library/materials.py``) and stops. It may not
reach for ``model``, ``resolve``, ``checks`` or ``takeoff``.

The walk is over the AST, not ``sys.modules``: ``catalog.structural_hardware_catalog``
imports ``library.hardware`` inside the function to break the catalog/items cycle, and a
rule that could not see a function-local import would be worth nothing.
"""

from __future__ import annotations

import pathlib

import pytest
from test_routing_leaf import _typehaus_imports

_SRC = pathlib.Path(__file__).resolve().parents[1] / "src" / "typehaus"

#: ``library`` for the catalog items; nothing else under ``typehaus``.
_ALLOWED = {"library", "hardware"}


def test_hardware_is_a_leaf() -> None:
    root = _SRC / "hardware"
    assert root.is_dir(), "typehaus.hardware is not a package"
    offences = [
        f"{path.relative_to(_SRC)} imports typehaus.{top}"
        for path in sorted(root.rglob("*.py"))
        for top in sorted(_typehaus_imports(path) - _ALLOWED)
    ]
    assert not offences, (
        f"typehaus.hardware is a leaf and may import only {sorted(_ALLOWED)}:\n  "
        + "\n  ".join(offences))


@pytest.mark.parametrize("module", ["config", "catalog", "plan_geometry"])
def test_the_promoted_modules_are_where_they_say_they_are(module: str) -> None:
    """No compatibility shim was left behind in ``takeoff/``.

    ``AGENTS.md`` §3 blesses the break: a shim would keep the inversion alive at the one
    place a reader would look to find out whether it was fixed.
    """
    assert (_SRC / "hardware" / f"{module}.py").is_file()
    stale = {"config": "hardware_config", "catalog": "hardware_catalog",
             "plan_geometry": "plan_geometry"}[module]
    assert not (_SRC / "takeoff" / f"{stale}.py").exists(), (
        f"takeoff/{stale}.py is back — import typehaus.hardware.{module} instead")
