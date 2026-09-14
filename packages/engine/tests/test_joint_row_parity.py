"""The test the ``typehaus.joints`` refactor exists to make possible.

Before the locators were promoted out of ``takeoff/``, the count in the order and the count
on the drawing came from two derivations that merely happened to agree. Now there is one:
the row builders group the joints, so a joint that moves moves the row, and a joint that
disappears takes its row with it.

**Every derived joint is billed, and every derived part is located.** Two populations are
deliberately outside that equality, and each is named here with its reason rather than
excluded by a loose filter:

* a row whose scope is ``"modeled connector"`` is an *authored* ``Connector`` — the plan
  made the joint by hand, ``resolve/accessories.py`` already draws it, and
  ``typehaus.joints`` stands down at exactly those joints so it is never bought twice;
* the resolver-emitted hanger members are real framed members with real geometry, billed
  from what the resolver already built rather than located again.
"""

from __future__ import annotations

from collections import Counter

import pytest

from typehaus.hardware.config import DEFAULT_HARDWARE_TAKEOFF_CONFIG as CONFIG
from typehaus.joints import derived_joints
from typehaus.joints.derive import COVERED_ROLES
from typehaus.takeoff.hardware import hardware_takeoff

#: An authored ``Connector``'s row. See the module docstring.
_AUTHORED_SCOPE = "modeled connector"
#: Hangers the resolver emitted as members in their own right.
_RESOLVER_EMITTED = "resolver-emitted"


def _derived_row_counts(model) -> Counter:
    counts: Counter = Counter()
    for row in hardware_takeoff(model, CONFIG):
        role = row.get("role")
        if not role or row["scope"] == _AUTHORED_SCOPE:
            continue
        if str(row.get("basis", "")).startswith(_RESOLVER_EMITTED):
            continue
        counts[role] += row["count"]
    return counts


@pytest.mark.parametrize("role", sorted(COVERED_ROLES))
def test_every_derived_joint_is_billed_exactly_once(catlin_model_ro, role: str) -> None:
    joints = Counter(joint.role for joint in derived_joints(catlin_model_ro, CONFIG))
    assert joints[role] == _derived_row_counts(catlin_model_ro)[role], (
        f"{role}: {joints[role]} located joints but "
        f"{_derived_row_counts(catlin_model_ro)[role]} on the order — the locator and the "
        f"row builder have stopped agreeing, which is the drift typehaus.joints prevents")


def test_the_covered_roles_are_the_ones_actually_located(catlin_model_ro) -> None:
    """``COVERED_ROLES`` is a claim, and an unbacked one would make the test above vacuous.

    A role in the set with no joints in this house would pass ``0 == 0`` forever while the
    derivation quietly broke.
    """
    joints = Counter(joint.role for joint in derived_joints(catlin_model_ro, CONFIG))
    assert set(joints) <= COVERED_ROLES, (
        f"derived_joints returned roles COVERED_ROLES does not claim: "
        f"{sorted(set(joints) - COVERED_ROLES)}")
    assert set(joints) == COVERED_ROLES, (
        f"COVERED_ROLES claims roles this house locates none of, so the parity test above "
        f"is vacuous for them: {sorted(COVERED_ROLES - set(joints))}")


def test_the_joint_counts_are_the_ones_the_house_is_known_to_have(catlin_model_ro) -> None:
    """A regression pin on the five families drawn in 3D.

    Not a golden of the whole derivation — a number here moving is not automatically wrong,
    a house changes — but these five were counted by hand when the markers were specified,
    and a silent move in one of them is what this would catch.
    """
    joints = Counter(joint.role for joint in derived_joints(catlin_model_ro, CONFIG))
    assert joints["hurricane_tie"] == 332
    assert joints["mudsill_anchor"] == 137
    assert joints["sloped_joist_hanger"] == 39
    assert joints["ridge_tie_strap"] == 19
    assert joints["embedded_strap_holdown"] == 40
    # The leg that had nothing until 2026-09-14: eight gable-end walls, 36 ties. Worth
    # pinning hard, because the rule that finds them is four predicates and dropping any one
    # of them silently changes the set (the interior partitions run the same way and rise to
    # the same height; the breezeway canopy shares the garage's storey).
    assert joints["gable_end_tie"] == 36
