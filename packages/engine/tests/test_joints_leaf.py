"""``typehaus.joints`` is a leaf, and this is what says so.

A joint is a *fact about the building*: a connection of some role belongs at some point.
A BOM row and a ``Finding`` are two opinions about that fact, and a marker solid is a third
reading of it. A locator that could see any of them would be tempted to answer differently
for each — which is precisely the drift this package exists to make impossible.

So: ``joints`` imports ``model`` / ``resolve`` / ``quantities`` / ``hardware`` and stops.
Never ``checks``, never ``takeoff``, never ``emit``. And nothing may smuggle the dependency
back the other way by having ``joints`` ask a take-off what it thinks.

The walk is over the AST rather than ``sys.modules``, for the same reason
``test_routing_leaf.py`` gives: a lazy import inside a function is still an import.
"""

from __future__ import annotations

import pathlib

from test_routing_leaf import _typehaus_imports

_SRC = pathlib.Path(__file__).resolve().parents[1] / "src" / "typehaus"

_ALLOWED = {"model", "resolve", "quantities", "hardware", "joints"}


def test_joints_is_a_leaf() -> None:
    root = _SRC / "joints"
    assert root.is_dir(), "typehaus.joints is not a package"
    offences = [
        f"{path.relative_to(_SRC)} imports typehaus.{top}"
        for path in sorted(root.rglob("*.py"))
        for top in sorted(_typehaus_imports(path) - _ALLOWED)
    ]
    assert not offences, (
        f"typehaus.joints is a leaf and may import only {sorted(_ALLOWED)}:\n  "
        + "\n  ".join(offences))


def test_the_locators_left_takeoff() -> None:
    """The point of the move: a joint is locatable from outside a bill of materials.

    ``resolve`` is upstream of ``takeoff`` and cannot import it, so while these functions
    lived there a derived tie could be specified, billed and graded — and never drawn. If
    one comes back, the marker stage silently loses its source of truth and starts agreeing
    with a second derivation instead of the first.
    """
    moved = {
        "takeoff/uplift.py": ["def bearing_connections(", "def bearing_line_tags(",
                              "class BearingSupport", "class BearingConnection"],
        "takeoff/hangers.py": ["def hung_connections(", "class CarryingElement",
                               "class HungConnection"],
        "takeoff/uplift_joints.py": ["def tags_covered_by(", "def authored_joints(",
                                     "def bears_on_concrete(", "def is_squash_block("],
        "takeoff/anchors.py": ["def strap_holdown_locations("],
    }
    offences = []
    for name, symbols in moved.items():
        text = (_SRC / name).read_text()
        offences += [f"{name} defines {symbol!r} again" for symbol in symbols
                     if symbol in text]
    assert not offences, (
        "these belong in typehaus.joints — a second definition is a second answer:\n  "
        + "\n  ".join(offences))
