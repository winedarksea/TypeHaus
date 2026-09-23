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
    # ** 332 -> 334 ON 2026-09-14, AND IT IS THE CHASES, NOT THE PILLARS. ** The two centre
    # balcony pillars came down onto the cast column tops that day and pass through
    # ``FS-SG-PORCH`` on the way, through a framed 9" opening each (FO-SG-BF2 / FO-SG-BR2).
    # A tie is derived per seated member END, and cutting the joist line at x = 18'-0" makes
    # more ends: ``FO-SG-BR2`` sits over the back beam and splits that line in two, giving
    # BM-SG-BKW two ends where it had one (+2), and ``FO-SG-BF2`` moves the same line's south
    # end from one station to the next on BM-SG-FRW (+1/-1). Net +2, all on one joist line.
    #
    # The PILLARS themselves add nothing here, which is worth saying because it looks as
    # though they should: the four porch beams now stop at the pillar faces and hang there on
    # authored HU212-3 hangers (CN-SG-HGR-C*), and an authored connector stands the
    # derivation down rather than adding to it.
    # 334 -> 369 ON 2026-09-16: a joist that CROSSES its bearing and cantilevers past it is
    # tied there too (``joints/bearing._crossing``). The balcony's edge beams BLW/BLE (+16),
    # the porch back beams BKW/BKE (+15) and the breezeway house seat (+4) had none. Then
    # -8 the same day: BM-SG-BLC went flush, and its joists hang rather than bear.
    # 361 -> 131, also 2026-09-16: floor joists on WALL plates take no tie (owner) — the
    # I-joists and floor trusses on W-B/W-M/W-S (-230). Joists on deck beams still do.
    #
    # 131 -> 82 in 2026-09 (the 17'-0" court): the sunken garden derives NO tie any more
    # (-49). The balcony's joist-to-beam ties are authored stainless (CN-SG-TIE-W/E01..12,
    # naming FS-SG-DECK), which stands the derivation down, and the porch hangs ledger to
    # ledger on LUS210Z with no beam to bear on. What is left: 64 rafter-to-plate ties on
    # RF-HOUSE / RF-GARAGE, 10 along the ridge, and FS-BW-FLOOR's 4 + 4 on its two seats.
    assert joints["hurricane_tie"] == 82
    # 137 -> 136 in 2026-09: the main-storey sill run over the sunken garden (y = -11 3/4")
    # spans axis to axis of the court's side walls, 20'-0" -> 18'-0" with the 17'-0" court.
    # At a 4' pitch, fencepost: floor(20/4)+1 = 6 became floor(18/4)+1 = 5.
    assert joints["mudsill_anchor"] == 136
    # 39 -> 40 on 2026-09-23: ST-G-SERVICE's stringer-1 moved 3/4" in with the outer-stringer
    # inset and its head now lands inside BM-BW-FE's 6" end gap, matching stringer-0 on
    # BM-BW-FC. Both carriers run PARALLEL to the stringers (plans/TODO.md: hung.py axis test).
    assert joints["sloped_joist_hanger"] == 40
    assert joints["ridge_tie_strap"] == 19
    assert joints["embedded_strap_holdown"] == 40
    # The leg that had nothing until 2026-09-14: six attic gable-end walls, 22 ties, plus one
    # LTP4 (was HGA10) under each of the garage's two gable-end trusses (2026-09-16). Worth
    # pinning hard, because the rule that finds them is four predicates and dropping any one
    # of them silently changes the set (the interior partitions run the same way and rise to
    # the same height; the breezeway canopy shares the garage's storey).
    assert joints["gable_end_tie"] == 22
    assert joints["gable_truss_anchor"] == 2
