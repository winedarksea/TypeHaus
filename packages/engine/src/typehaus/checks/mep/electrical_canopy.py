"""``electrical.canopy_covers_box`` — a wall light's canopy covers the box face it mounts on.

NEC 314.25: a completed box has a cover, faceplate or luminaire canopy. The canopy is
``LuminaireType.canopy`` (width, height off the sheet), or a round ``canopy_diameter``,
which must span a rectangular face's diagonal or a round box's diameter. Both are centred
on the box by construction
(``resolve/device_boxes.place_box``). A surface box's sides stay in view whatever the
canopy; that is a finish note, not graded here. Oracle: catlin's PLAY-N sconces, WAC
Roland 4 1/2" square backplate over a 4" square box (notes/basement_surface_wiring.md).
"""

from __future__ import annotations

import math

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, failed, not_applicable, passed, unknown
from typehaus.model.nec import NEC, cite
from typehaus.quantities import M_PER_IN

_CID, _CODE = "electrical.canopy_covers_box", cite(NEC.BOX_COVER)


def _in(value_m: float) -> str:
    return f'{value_m / M_PER_IN:.3g}"'


@check(Tier.ADVISORY, _CID)
def canopy_covers_box(ctx: CheckContext) -> list[Finding]:
    """Each wall light's canopy against the face of its derived box."""
    # A luminaire takes its own box, never a bank row, so the lead's kind is the box's.
    # A ceiling box (#140) is covered by the fixture's own body or canopy: not graded here.
    boxes = [box for box in ctx.model.device_boxes
             if box.device_kind == "light" and getattr(box, "host", "wall") == "wall"]
    if not boxes:
        return [not_applicable(_CID, "no wall light sits on a derived box", code=_CODE)]
    types = {t.tag: t for t in ctx.plan.library.electrical_device_types}
    type_refs = {obj.tag: obj.type_ref for obj in ctx.model.canvas_objects}
    out: list[Finding] = []
    unstated: dict[str, list[str]] = {}
    for box in sorted(boxes, key=lambda b: b.device_tag):
        type_ref = type_refs.get(box.device_tag) or ""
        product = types.get(type_ref)
        canopy = getattr(product, "canopy", None)
        diameter = getattr(product, "canopy_diameter", None)
        is_round = box.shape == "round"
        # A box seated off the fixture's centre (#149): its far edge is what the canopy covers.
        moved = getattr(box, "snap_shifts_m", ()) or (0.0,)
        off = abs(getattr(box, "stud_shift_m", 0.0) - moved[0])
        size = (f"{_in(box.width_m)} round" if is_round
                else f"{_in(box.width_m)} x {_in(box.height_m)}")
        face = f"{size} {box.mounting} box ({box.box_product})"
        tags = (box.device_tag,)
        if canopy is not None:
            width, height = (part.meters for part in canopy)
            short = max(box.width_m + 2 * off - width, box.height_m - height)
            what = f"{_in(width)} x {_in(height)} canopy"
        elif diameter is not None:
            width = height = diameter.meters
            short = ((box.width_m + 2 * off) if is_round
                     else math.hypot(box.width_m + 2 * off, box.height_m)) - width
            what = f"{_in(width)} round canopy"
        else:
            unstated.setdefault(type_ref, []).append(box.device_tag)
            continue
        if short > 1e-6:
            out.append(failed(_CID, f"{box.device_tag}: its {what} leaves {_in(short)} of the "
                                    f"{face} face uncovered", tags, code=_CODE,
                              fix="a box row the canopy covers (BoxRow use='luminaire'), or "
                                  "a fixture with a larger canopy"))
        else:
            out.append(passed(_CID, f"{box.device_tag}: {what} covers the {face}", tags,
                              code=_CODE))
    if unstated:
        devices = tuple(tag for tags in unstated.values() for tag in tags)
        out.append(unknown(_CID, f"{len(devices)} wall light(s) of {len(unstated)} type(s) "
                                 f"state no canopy: {', '.join(sorted(unstated))}", devices,
                           code=_CODE, fix="author LuminaireType.canopy off each sheet"))
    return out
