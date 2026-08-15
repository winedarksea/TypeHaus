"""`ft(f, i)` is ``f*12 + i``, and the sign rides on each argument independently.

Two different traps, needing two different guards:

- ``ft(-7, 10)`` reads as "minus seven-foot-ten" and is actually ``-84 + 10 = -74``″ — 20″
  wrong, in the wrong direction. The function can see this one, so it raises.
- ``ft(-0, 8)`` reads as "minus eight inches" and is ``+8``″, because ``-0 == 0`` before the
  call is even made. **Only the source text still knows**, so the dialect linter is the only
  thing that can catch it.
"""

from __future__ import annotations

import pytest

from typehaus.quantities.length import ft
from typehaus.source.dialect import lint_source

_HEADER = "# haus: editable\nfrom typehaus import Node, ft, pt\n\n"


def _lint(expr: str) -> list[str]:
    src = f'{_HEADER}NODES = (Node(uid="AAAAAAAAAA", tag="N-1", position=pt({expr}, ft(0))),)\n'
    return [f.check_id for f in lint_source("plan/x.py", src)]


def test_negative_feet_with_positive_inches_raises() -> None:
    with pytest.raises(ValueError, match="mixed signs"):
        ft(-7, 10)


def test_the_message_names_both_the_actual_and_the_intended_value() -> None:
    with pytest.raises(ValueError) as exc:
        ft(-7, 10)
    assert "-74" in str(exc.value) and "-94" in str(exc.value)
    assert "ft(-7, -10)" in str(exc.value)


def test_a_fully_negative_pair_is_the_supported_spelling() -> None:
    assert ft(-7, -10).meters == pytest.approx(ft(7, 10).meters * -1)


@pytest.mark.parametrize("expr", ["ft(0, 8)", "ft(-7, -10)", "ft(7, 10)", "ft(-7, 0)",
                                  "ft(8)", "ft(-8)"])
def test_legitimate_spellings_do_not_lint(expr: str) -> None:
    assert "dialect.mixed_sign_ft" not in _lint(expr)


@pytest.mark.parametrize("expr", ["ft(-0, 8)", "ft(-7, 10)", "ft(-0, 0.5)"])
def test_mixed_sign_spellings_lint(expr: str) -> None:
    assert "dialect.mixed_sign_ft" in _lint(expr)


def test_negative_zero_is_invisible_at_runtime_which_is_why_the_lint_exists() -> None:
    """The premise of the lint, pinned: if this ever stops being true, drop it."""
    assert ft(-0, 8).meters == ft(0, 8).meters > 0


def test_the_lint_names_the_fix() -> None:
    src = f'{_HEADER}NODES = (Node(uid="AAAAAAAAAA", tag="N-1", position=pt(ft(-0, 8), ft(0))),)\n'
    finding = next(f for f in lint_source("plan/x.py", src)
                   if f.check_id == "dialect.mixed_sign_ft")
    assert finding.fix_hint is not None and "ft(-0, -8)" in finding.fix_hint
