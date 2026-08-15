"""uid and tag uniqueness are load-time errors, not checks-tier findings.

`haus build` never runs the checks registry, so `integrity.uid_unique` — until now the only
uniqueness rule in the engine — could not see the build path at all: a hand-minted colliding
uid built green and shipped two elements sharing one derived IFC GlobalId. Tags had no rule
anywhere; ``_consistency_check``'s ``{el.tag: el for el in ...}`` silently kept the last of a
duplicate pair, so half the collision vanished from every downstream view.
"""

from __future__ import annotations

import pytest

from typehaus.source import load_plan

from _helpers import STARTER, copy_house


@pytest.fixture
def sandbox(tmp_path):
    return copy_house(STARTER, tmp_path / "starter")


def _upper(sandbox):
    return sandbox / "plan" / "storeys" / "upper.py"


def _errors(sandbox, check_id: str):
    result = load_plan(sandbox)
    return [f for f in result.findings if f.check_id == check_id]


def test_the_starter_house_is_clean(sandbox) -> None:
    result = load_plan(sandbox)
    assert result.ok, [f.render() for f in result.findings]


def test_a_duplicate_uid_is_a_hard_load_error(sandbox) -> None:
    path = _upper(sandbox)
    path.write_text(path.read_text().replace('uid="N202AAAAAA"', 'uid="N201AAAAAA"'))

    findings = _errors(sandbox, "loader.uid_unique")
    assert len(findings) == 1
    assert findings[0].severity.value == "error"
    # Both colliding tags are named: knowing only one is not enough to fix it.
    assert set(findings[0].element_tags) == {"N-201", "N-202"}
    assert not load_plan(sandbox).ok


def test_a_duplicate_tag_is_a_hard_load_error(sandbox) -> None:
    path = _upper(sandbox)
    path.write_text(path.read_text().replace('tag="N-202"', 'tag="N-201"'))

    findings = _errors(sandbox, "loader.tag_unique")
    assert len(findings) == 1
    assert findings[0].severity.value == "error"
    assert findings[0].element_tags == ("N-201",)


def test_the_checks_tier_rule_still_mirrors_the_loader(catlin_plan) -> None:
    """The load-time gate is the enforcement; `integrity.uid_unique` stays as the mirror so
    a plan reached by any other route is still graded."""
    import typehaus.checks  # noqa: F401  (importing the package registers every check)
    from typehaus.checks.registry import Tier, registered

    ids = {cid for cid, _ in registered(Tier.INTEGRITY)}
    assert "integrity.uid_unique" in ids

    uids = [el.uid for el in catlin_plan.all_elements() if el.uid]
    assert len(uids) == len(set(uids))
