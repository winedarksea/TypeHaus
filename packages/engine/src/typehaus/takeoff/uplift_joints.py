"""The BOM rows for post bases, their cast-in anchors, and beam-on-post straps.

The seam from ``takeoff/uplift.py`` is not arbitrary: that module groups hardware derived
along a *run* — a tie at every member seating on a bearing line, a plate every four feet
along a bottom plate — while these three group a part per point where two named members
meet.

**Every predicate behind them lives in ``typehaus.joints.posts``**, with the reason each
guard exists and the order they must stay in. What is here is only the grouping: which rows,
what basis, and how the count is worded for a framer who has to audit it.
"""

from __future__ import annotations

from collections import Counter

from typehaus.hardware.catalog import (
    ROLE_BEAM_HOLD_DOWN,
    ROLE_POST_BASE,
    ROLE_POST_BASE_ANCHOR,
    hardware_for_role,
    hardware_for_role_and_nominal,
)
from typehaus.hardware.config import UpliftTieRules
from typehaus.joints.posts import (
    post_base_anchor_joints,
    post_base_joints,
    post_beam_strap_joints,
)
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.hardware_row import hardware_row


def post_base_rows(model: ResolvedModel, rules: UpliftTieRules) -> list:
    """A standoff base under every wood post that declares what it bears on.

    Three conditions are deliberately out of reach of this rule, and each is a real one
    rather than a rounding decision:

    * a post inside a wall (``within_wall``) is developed by the wall's own plates and studs,
      which the SP tie already bills — a base under it would be a second connection at a
      joint that already has one;
    * a post with no ``supported_by`` has nothing declared to fasten a base to;
    * a concrete column is not a section this catalog stocks a wood base for;
    * a post whose joint is already made another way — an authored ``POST_BASE`` *or* an
      authored ``TENSION_TIE``;
    * a **squash block** — a post under ``blocking_max_height_ft`` — bears and does nothing
      else. Buying it a base would be the same error the tie-plate rule makes on a sill:
      hardware at a joint whose connection is already made another way.

    All four are reported by ``structural.uplift_path_coverage`` rather than being quietly
    absent from the order.
    """
    by_size: dict = {}
    for storey, post in post_base_joints(model, rules):
        entry = by_size.setdefault(post.size, {"by_storey": Counter(), "tags": []})
        entry["by_storey"][storey] += 1
        entry["tags"].append(post.tag)

    rows = []
    for size in sorted(by_size):
        entry = by_size[size]
        item = hardware_for_role_and_nominal(ROLE_POST_BASE, size)
        by_storey = entry["by_storey"]
        rows.append(hardware_row(
            item, scope="post base", count=int(sum(by_storey.values())), size=size,
            by_storey=dict(sorted(by_storey.items())),
            basis=(f"one per {size} post that declares what it bears on: "
                   + ", ".join(sorted(entry["tags"])))))
    return rows


def post_base_anchor_rows(model: ResolvedModel, rules: UpliftTieRules) -> list:
    """The cast-in bolt under every post base — authored or derived — that lands on concrete.

    An ABU is a stirrup with a hole in it; Simpson's published uplift and lateral values are
    taken *through* a 5/8 in anchor the base does not include.

    This rule counts posts rather than bases because it is the JOINT that decides whether a
    bolt is needed. ``StructuralHardware.requires_role`` — the mechanism that already puts an
    S-5! clamp under every CanDuit ring — cannot express it: that field is a flat property of
    the part, and it would bill a cast-in bolt for any base landing on
    FRAMING rather than on a pour. A base on framing is through-bolted or screwed to it, and
    those fixings are inside the framing rate exactly as a joist hanger's nails are.
    (``PT-SG-BR2``/``BF2``'s ABU66SS standing on the porch DECK were the worked example
    until 2026-09-03, when both pillars went to wood-to-wood bearing with a ``TENSION_TIE``
    and stopped taking a base at all. The rule they motivated is unchanged.)

    Both halves of the population are counted here: the ten bases catlin authors as
    ``Connector`` elements *and* the ones ``post_base_rows`` derives. They are one order.
    """
    by_storey: Counter = Counter()
    tags: list = []
    for storey, post in post_base_anchor_joints(model, rules):
        by_storey[storey] += 1
        tags.append(post.tag)
    if not tags:
        return []
    item = hardware_for_role(ROLE_POST_BASE_ANCHOR)
    return [hardware_row(
        item, scope="post base anchor", count=len(tags), tags=tags,
        by_storey=dict(sorted(by_storey.items())),
        basis=("one per post base landing on concrete (a base on framing is fastened to it "
               "and those fixings are in the framing rate): " + ", ".join(sorted(tags))))]

# --- rule 3: post/beam straps --------------------------------------------------------


def post_beam_strap_rows(model: ResolvedModel, rules: UpliftTieRules) -> list:
    """A strap at every beam end that lands on a wood post.

    ``Beam.bearing_refs`` already names the post, so this counts declarations rather than
    searching for coincident geometry. One strap per beam end by default, not the matched
    pair: a pair only fits where the beam *stops* at the post, and a beam that runs past its
    post has one reachable face — the same lesson ``KneeBraceRules`` learned when a pair rule
    billed twelve unbuildable braces. A joint that wants two authors the second by hand.
    """
    by_storey: Counter = Counter()
    joints: list = []
    for storey, beam, post in post_beam_strap_joints(model, rules):
        by_storey[storey] += rules.straps_per_post_beam_joint
        joints.append(f"{beam.tag}->{post.tag}")
    if not joints:
        return []
    item = hardware_for_role(ROLE_BEAM_HOLD_DOWN)
    return [hardware_row(
        item, scope="beam on post", count=int(sum(by_storey.values())),
        by_storey=dict(sorted(by_storey.items())),
        basis=(f"{rules.straps_per_post_beam_joint} per beam end landing on a wood post "
               f"({len(joints)} joints: " + ", ".join(sorted(joints)) + ")"))]

