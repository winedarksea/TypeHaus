"""The jurisdiction's inspection list has to be internally consistent, or it is fiction.

Four properties, each of which has a failure mode that is silent without a test: a check id
nobody registered folds to "no evaluable model input" and blocks forever; a trade nobody
recognises gates nothing; a cycle in ``after`` deadlocks the whole board; and an
applicability key with no probe raises at request time, on a phone, in a basement.
"""

from __future__ import annotations

import pytest

import typehaus.checks  # noqa: F401  - registers every check
from typehaus.checks.code.mn_residential.inspections import MN_INSPECTIONS
from typehaus.checks.code.mn_residential.profile import MN_2020
from typehaus.checks.registry import registered
from typehaus.emit.trades import TRADES
from typehaus.schedule.applicability import PROBES
from typehaus.schedule.milestones import MILESTONE_IDS
from typehaus.schedule.model import AUTHORITIES


def test_every_check_id_is_registered() -> None:
    known = {check_id for check_id, _fn in registered()}
    unknown = sorted({cid for spec in MN_INSPECTIONS for cid in spec.check_ids} - known)
    assert not unknown, f"inspections name unregistered check(s): {unknown}"


def test_every_gated_trade_exists() -> None:
    unknown = sorted({trade for spec in MN_INSPECTIONS for trade in spec.gates} - TRADES)
    assert not unknown, f"inspections gate unknown trade(s): {unknown}"


def test_after_is_acyclic_and_names_real_inspections() -> None:
    by_id = {spec.id: spec for spec in MN_INSPECTIONS}
    for spec in MN_INSPECTIONS:
        missing = sorted(set(spec.after) - set(by_id))
        assert not missing, f"{spec.id} comes after unknown inspection(s): {missing}"
    # The list is in build order, so a predecessor must already have been listed. That is
    # strictly stronger than acyclicity and it is what makes one forward pass correct in
    # ``readiness.inspection_readiness``.
    seen: set[str] = set()
    for spec in MN_INSPECTIONS:
        late = sorted(set(spec.after) - seen)
        assert not late, f"{spec.id} comes after {late}, which the list has not reached yet"
        seen.add(spec.id)


def test_ids_are_unique() -> None:
    ids = [spec.id for spec in MN_INSPECTIONS]
    assert len(ids) == len(set(ids)), "duplicate inspection id"


def test_authorities_and_milestones_are_known() -> None:
    for spec in MN_INSPECTIONS:
        assert spec.authority in AUTHORITIES, f"{spec.id}: authority {spec.authority!r}"
        assert spec.milestone in MILESTONE_IDS, f"{spec.id}: milestone {spec.milestone!r}"


def test_applicability_keys_have_probes() -> None:
    unknown = sorted({spec.applies_when for spec in MN_INSPECTIONS
                      if spec.applies_when} - set(PROBES))
    assert not unknown, f"no applicability probe for: {unknown}"


def test_the_profile_carries_the_list() -> None:
    assert MN_2020.inspections == MN_INSPECTIONS
    assert MN_2020.inspection("footing") is not None
    assert MN_2020.inspection("no_such_inspection") is None


@pytest.mark.parametrize("spec", MN_INSPECTIONS, ids=lambda s: s.id)
def test_every_inspection_says_something_actionable(spec: object) -> None:
    """An inspection with neither a check nor an on-site item is a row nobody can close."""
    assert spec.check_ids or spec.on_site, f"{spec.id} has nothing to satisfy"
