"""STRUCTURAL — every device box holds to its framing as its datasheet says (decision #149).

Reads the mount ``resolve/box_supports.py`` derived off each box's ``BoxRow.support``: a
nail-on box seated against a stud (or a joist's side), a bracket or bar spanning its bay
within the listed range (member centres or clear opening, as the datasheet states), a
one-side bracket reaching its member, a box screwed under a member. A mount that cannot
reach is a FAIL (NEC 314.23: a box is securely supported). A row asking a block behind
the box (``block_profile``) FAILs where none fits. N/A only where no row names a mount.
"""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, failed, not_applicable, passed
from typehaus.model.nec import NEC, cite
from typehaus.quantities import M_PER_IN

CHECK_ID = "electrical.box_support"
_CODE = cite(NEC.BOX_SUPPORT)


def _what(box) -> str:
    names = "+".join(box.device_tags or (box.device_tag,))
    where = f" on {box.wall_tag}" if box.wall_tag else " in the ceiling"
    return f"{names}'s {box.box_product} box{where}"


@check(Tier.STRUCTURAL, CHECK_ID)
def box_support(ctx: CheckContext) -> list[Finding]:
    """Each box's derived mount reaches its framing; a block row's block fits."""
    blocked = {(row.box_product_ref, row.mounting) for el in ctx.plan.all_elements()
               if el.element_kind == "BoxStandard" for row in el.rows if row.block_profile}
    out: list[Finding] = []
    for box in sorted(ctx.model.device_boxes, key=lambda b: b.device_tag):
        tags = tuple(dict.fromkeys((*(box.device_tags or (box.device_tag,)),
                                    *((box.wall_tag,) if box.wall_tag else ()))))
        if (box.box_product, box.mounting) in blocked and box.host == "wall":
            if box.block_key is None:
                out.append(failed(CHECK_ID, f"{_what(box)}: its row asks a block behind the "
                                            "box and none fits (no stud each side, or too "
                                            "shallow a cavity)", tags, code=_CODE,
                                  fix="re-station the box in a full stud bay"))
            else:
                out.append(passed(CHECK_ID, f"{_what(box)} screws to its derived block "
                                            f"{box.block_key}", tags, code=_CODE))
            continue
        if box.support_kind is None:
            continue
        if box.support_fault:
            out.append(failed(CHECK_ID, f"{_what(box)}: {box.support_fault}", tags, code=_CODE,
                              fix="move the device into a bay its mount reaches, or choose "
                                  "a row whose mount does (ElectricalDevice.box_use)"))
            continue
        on = ", ".join(box.support_members)
        if box.support_kind == "stud_side" and box.host == "wall":
            moved = (f", seated {box.stud_shift_m / M_PER_IN:+.2f} in."
                     if abs(box.stud_shift_m) > 1e-4 else "")
            message = f"{_what(box)} nails to {on}{moved}"
        elif box.support_span_m is not None and box.support_kind in ("joist_span", "stud_span"):
            message = (f"{_what(box)} spans {on} at {box.support_span_m / M_PER_IN:.2f} in.")
        else:
            message = f"{_what(box)}: {box.support_kind.replace('_', ' ')} mount on {on}"
        out.append(passed(CHECK_ID, message, tags, code=_CODE))
    if not out:
        return [not_applicable(CHECK_ID, "no box standard row names a mount or a block",
                               code=_CODE)]
    return out
