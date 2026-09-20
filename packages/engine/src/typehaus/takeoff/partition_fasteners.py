"""The SDPW DEFLECTOR screws at every interior partition's top plate.

``resolve/partition_top.py`` stops a partition's framing 3/4" clear of the structure over
it; this bills the screw that spans that gap. Its own module rather than a fifth derivation
in ``takeoff/fasteners.py``, which is 491 lines against AGENTS.md's 500.

**The geometry is not here any more.** Reading the joint — which walls take a gap, what
condition each top is in, what the gap measures, what the screw lands in — moved to
``resolve/partition_fasteners.py`` on 2026-09-19, because ``checks/structural/
partition_fasteners.py`` has to ask the same questions to grade the screw's SPACING against
Simpson's published maximum, and a check may not import ``takeoff/``. What is left here is
the BILL: one row per (condition, part, required length), and the refusals riding on it.

**The count is one screw per crossing, never a pitch along the plate**, because a screw has
to land IN something. That splits three ways, and coding only the last would call for
blocking in bays that already have a joist in them:

============================================  =======================================
condition                                     count
============================================  =======================================
partition PERPENDICULAR to the framing above  one per resolved crossing
partition UNDER a parallel member             a pitch along the shared run, both ends
partition BETWEEN parallel members            one blocked bay per framing module
============================================  =======================================
"""

from __future__ import annotations

from collections import Counter

from typehaus.hardware.catalog import (
    ROLE_PARTITION_DEFLECTION_SCREW,
    hardware_for_role_and_nominal,
)
from typehaus.hardware.config import PartitionDeflectionRules
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.partition_fasteners import (
    PERPENDICULAR,
    UNDER_MEMBER,
    partition_top_joints,
)
from typehaus.takeoff.hardware_row import hardware_row


def partition_deflection_screw_rows(model: ResolvedModel,
                                    rules: PartitionDeflectionRules) -> list:
    """One row per (condition, part, required length) — plus a refusal row where one is due.

    Grouped on ``(scope, part number, required length)`` and carrying a ``by_storey``
    Counter, the shape ``fasteners.truss_wall_block_screw_rows`` already bills screws in.
    """
    joints, refusals = partition_top_joints(model, rules)
    groups: dict = {}
    for joint in joints:
        required_in = joint.gap_in + joint.plate_in + rules.minimum_embedment_in
        item = hardware_for_role_and_nominal(ROLE_PARTITION_DEFLECTION_SCREW,
                                             joint.plate_condition)
        reaching = [n for n in item.available_lengths_in if n + 1e-9 >= required_in]
        if not reaching:
            refusals.append(f"{joint.wall_tag}: no {item.model} length reaches "
                            f"{required_in:.2f} in")
            continue
        length_in = min(reaching)
        group = groups.setdefault(
            (joint.scope, item.part_number_by_length_in[length_in], round(required_in, 3)), {
                "item": item, "length_in": length_in,
                "part_number": item.part_number_by_length_in[length_in],
                "scope": joint.scope, "count": 0, "by_storey": Counter(),
                "required_in": required_in, "gap_in": joint.gap_in,
                "plate_in": joint.plate_in, "condition": joint.plate_condition,
                "spacing_in": joint.spacing_in, "walls": [],
            })
        group["count"] += joint.count
        group["by_storey"][joint.storey] += joint.count
        group["walls"].append(joint.wall_tag)

    # A refusal rides on the BASIS of the rows that were billed, not on a row of its own.
    # A zero-count line with no part number is not a bill of materials: it reaches the
    # per-trade RFQ and the drawing schedule as an order line for nothing. The fact still
    # has to be carried — silently billing nothing is the failure — so every SDPW row says
    # which partition tops got none and why. The standalone row is the degenerate case
    # where NOTHING was billed and there is no basis to ride on.
    note = ("" if not refusals else
            " NOT BILLED at " + "; ".join(sorted(refusals)) + ".")
    rows = [hardware_row(
        group["item"], scope=group["scope"], count=int(group["count"]),
        part_number=group["part_number"], size=f"{group['length_in']:g} in",
        by_storey=dict(sorted(group["by_storey"].items())),
        basis=_basis(group, rules) + note,
    ) for _key, group in sorted(groups.items())]
    if refusals and not rows:
        rows.append(hardware_row(
            None, scope="partition top plate, NOT BILLED", count=0,
            basis=("no SDPW is billed at any partition top, and the reason is recorded "
                   "rather than absorbed:" + note),
        ))
    return rows


def _basis(group: dict, rules: PartitionDeflectionRules) -> str:
    """The rule that produced the count — and, for the blocked bays, what is NOT billed."""
    length = (f"{group['gap_in']:.3g} in gap + {group['plate_in']:.3g} in top plate + "
              f"{rules.minimum_embedment_in:g} in embedment = {group['required_in']:.2f} in "
              "required")
    walls = f"{len(group['walls'])} partition(s)"
    if group["scope"] == PERPENDICULAR:
        rule = (f"{rules.screws_per_crossing} screw per resolved crossing of the framing "
                f"above, across {walls}")
    elif group["scope"] == UNDER_MEMBER:
        rule = (f"{rules.along_member_pitch_in:g} in o.c. along {walls} running under a "
                "parallel member, fencepost at both ends")
    else:
        rule = (f"one blocked bay per {group['spacing_in']:g} in framing module along "
                f"{walls} running BETWEEN parallel members, fencepost at both ends. The "
                "blocking itself is framed by ``resolve/floor_blocking.py`` over a FLOOR "
                "and is billed with the deck's own members; over a ROOF it is not carried")
    return (f"{rule}. {length}, at the {group['condition']} this wall frames — the "
            "condition the part's own published row is for. The SPACING this schedule "
            "implies is graded against Simpson's own maximum-spacing table by "
            "`structural.partition_deflection_spacing`; nothing here grades a demand, "
            "because this engine carries no interior-partition out-of-plane load to grade")
