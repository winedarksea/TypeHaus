"""WP1.6 tests — one fixture per excluded construct → exactly one finding at the line."""

from __future__ import annotations

import pytest

from typehaus.source.dialect import lint_source

HEADER = "# haus: editable\nfrom typehaus import Wall, ft\n"

CASES = {
    "loop": "for x in range(3):\n    pass\n",
    "conditional": "x = ft(1)\nif x:\n    pass\n",
    "comprehension": "xs = [ft(i) for i in range(3)]\n",
    "binary_op": "x = ft(12) + ft(6)\n",
    "fstring": 'x = f"{ft(1)}"\n',
    "lambda": "f = lambda x: x\n",
    "subscript": "x = ft(1)\ny = x[0]\n",
    "def": "def make():\n    return ft(1)\n",
    "plain_import": "import os\n",
    "bad_import": "from numpy import array\n",
}


@pytest.mark.parametrize("name,body", list(CASES.items()))
def test_each_excluded_construct_flags(name: str, body: str) -> None:
    findings = lint_source(f"{name}.py", HEADER + body)
    grammar = [f for f in findings if f.check_id == "dialect.grammar"]
    assert len(grammar) >= 1, f"{name} should be flagged"
    assert all(f.source_loc is not None for f in grammar)


def test_valid_plan_has_no_findings() -> None:
    good = HEADER + (
        'WALLS = [Wall(uid="AAAAAAAAAA", tag="W-1", start_node="N-1", '
        'end_node="N-2", assembly="X", top=ft(9))]\n'
    )
    assert lint_source("good.py", good) == []


def test_missing_uid_is_flagged() -> None:
    from typehaus.source.dialect import missing_uid_findings

    src = HEADER + 'Wall(tag="W-1", start_node="N-1", end_node="N-2", assembly="X")\n'
    findings = missing_uid_findings("m.py", src)
    assert len(findings) == 1
    assert findings[0].check_id == "dialect.missing_uid"
