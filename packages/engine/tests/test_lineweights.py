"""The lineweight hierarchy (→ 30 §Graphics).

A drawing is read by line weight before it is read by anything else, and that only works if
the weights form a hierarchy rather than a set. Before ``emit/draw/lineweights.py`` there
were thirteen distinct literals across about twenty modules, with 0.3 and 0.35 both in
heavy use and no rule saying which meant what. Two weights that print alike are not a
hierarchy; they are noise with a standard deviation.
"""

from __future__ import annotations

import ast
import pathlib

from typehaus.emit.draw import lineweights as lw

_DRAW = pathlib.Path(lw.__file__).parent


def test_every_named_weight_is_a_real_pen():
    """ISO 128-2's preferred series. A weight off the ladder is a pen no plotter has."""
    named = {name: value for name, value in vars(lw).items()
             if name.isupper() and isinstance(value, float) and name != "MIN_THICK_THIN_RATIO"}
    off = {n: v for n, v in named.items() if v not in lw.LADDER}
    assert not off, f"not on the ISO ladder: {off}"


def test_the_hierarchy_is_ordered_and_wide_enough():
    """ISO 128-2 wants at least 2:1 thick to thin. This ladder gives 3.8:1."""
    assert lw.CUT_HEAVY > lw.CUT > lw.PROFILE > lw.LIGHT > lw.REFERENCE > lw.FAINT
    assert lw.CUT_HEAVY / lw.FAINT >= lw.MIN_THICK_THIN_RATIO
    # The pairing that carries a section: cut against what is seen beyond it.
    assert lw.CUT / lw.PROFILE >= 1.4


def test_no_drawing_module_writes_a_bare_lineweight():
    """The regression this module exists to prevent — a fourteenth literal.

    ``0.0`` is exempt and is not a weight: it means *no stroke*, which is a statement about
    a band that is filled and not outlined.
    """
    offenders: list[str] = []
    for path in sorted(_DRAW.rglob("*.py")):
        if path.name == "lineweights.py":
            continue
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.keyword) or node.arg != "lineweight":
                continue
            value = node.value
            if isinstance(value, ast.Constant) and value.value not in (0.0, None):
                offenders.append(f"{path.name}:{value.lineno} lineweight={value.value}")
    assert not offenders, (
        "use a name from emit/draw/lineweights.py, and add a name before adding a number:\n"
        + "\n".join(offenders))


def test_snap_quantises_rather_than_rejects():
    """A caller holding an authored literal gets the nearest pen, not an exception.

    A drawing with a slightly wrong pen is a drawing; a drawing with an exception in it is
    not, and a house may author a ``Polyline.lineweight`` this module never saw.
    """
    assert lw.snap(0.30) in (0.25, 0.35)
    assert lw.snap(0.02) == 0.13
    assert lw.snap(9.0) == 1.00
    for rung in lw.LADDER:
        assert lw.snap(rung) == rung
