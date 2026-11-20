"""Bodies above a ceiling plane: a recessed can's housing and a flush ceiling box (#140).

Each must sit in a clear bay of the frame above. ``electrical.ceiling_box_support`` asks a
ceiling fan's box to be listed for a fan (NEC 314.27).
"""

from __future__ import annotations

from typing import Any

from typehaus.checks._authoring import by_result
from typehaus.checks.mep.framing_envelope import (
    TOLERANCE_M,
    band_over,
    legs,
    member_footprint,
    z_overlap,
)
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, failed, not_applicable, passed, unknown
from typehaus.model.nec import NEC, cite
from typehaus.quantities import M_PER_IN

CID = "electrical.ceiling_can_framing"
BOX_CID = "electrical.ceiling_box_framing"
SUPPORT_CID = "electrical.ceiling_box_support"
#: A host this far below the body's base still counts as above it (a soffit's underside).
_HOST_SLACK_M = 0.05
_SHIFT_STEP_M = 0.25 * M_PER_IN
_SHIFT_MAX_M = 24 * M_PER_IN
_DIRECTIONS = (("east", 1.0, 0.0), ("west", -1.0, 0.0), ("north", 0.0, 1.0),
               ("south", 0.0, -1.0))


def _ceiling_cans(ctx: CheckContext) -> list:
    return [element for element in ctx.plan.all_elements()
            if element.element_kind == "ElectricalDevice"
            and element.mount is not None and element.mount.kind.value == "ceiling"
            and element.mount.recessed_into_host_surface]


def _hosts(model) -> list[tuple[str, float, float, object, tuple, list]]:
    """(tag, z band, plan shape, voids, members) for every framed system a body can sit in.

    A floor or soffit is one plane; a roof spans eave to ridge, so a cathedral can sits
    anywhere inside that band.
    """
    from shapely.geometry import Polygon

    out = []
    for floor in model.floors:
        if len(floor.deck_outline) >= 3:
            out.append((floor.tag, floor.deck_z0_m, floor.deck_z0_m, Polygon(floor.deck_outline),
                        tuple(Polygon(v) for v in floor.deck_voids if len(v) >= 3),
                        list(floor.members)))
    for roof in model.roofs:
        if len(roof.footprint) >= 3:
            out.append((roof.tag, roof.eave_z_m, roof.ridge_z_m, Polygon(roof.footprint), (),
                        list(roof.members)))
    for soffit in model.soffits:
        if len(soffit.outline) >= 3:
            out.append((soffit.tag, soffit.z0_m, soffit.z0_m, Polygon(soffit.outline), (),
                        list(soffit.members)))
    return out


class _Frame:
    """The framing and the pipe/duct legs above every ceiling, indexed once."""

    def __init__(self, model: Any) -> None:
        from shapely.strtree import STRtree

        self.hosts = _hosts(model)
        self.framing = []
        for tag, _low, _high, _shape, _voids, members in self.hosts:
            for member in members:
                envelope = member_footprint(member)
                if envelope is not None:
                    self.framing.append((f"{tag}/{member.child_key}", *envelope))
        self.tree = STRtree([shape for _, shape, _, _ in self.framing])
        self.runs = [leg for leg in legs(model) if leg.kind in ("pipe", "duct")]
        self.run_tree = STRtree([leg.footprint for leg in self.runs])

    def host(self, footprint: Any, z0: float) -> tuple | None:
        over = [(max(low, z0), tag, voids) for tag, low, high, shape, voids, _ in self.hosts
                if high >= z0 - _HOST_SLACK_M and shape.covers(footprint.centroid)]
        return min(over, key=lambda item: item[0]) if over else None

    def member_hits(self, footprint: Any, z0: float, z1: float) -> list[str]:
        hits = []
        for i in self.tree.query(footprint):
            name, shape, bottom, top = self.framing[i]
            if (min(top, z1) - max(bottom, z0) > TOLERANCE_M
                    and footprint.intersection(shape).area > 0):
                hits.append(name)
        return hits

    def hits(self, footprint: Any, z0: float, z1: float) -> list[str]:
        out = self.member_hits(footprint, z0, z1)
        for i in self.run_tree.query(footprint):
            leg = self.runs[i]
            band = band_over(leg, footprint)
            if band is not None and z_overlap(leg, band, z0, z1) > TOLERANCE_M:
                out.append(f"{leg.kind} {leg.tag}")
        return sorted(set(out))


@check(Tier.STRUCTURAL, CID)
def ceiling_can_framing(ctx: CheckContext) -> list[Finding]:
    """Keep a recessed can's housing clear of joists, rafters, blocking, ducts and pipes.

    The body is the type's footprint over ``height`` above the ceiling plane, so a clear
    result needs the real housing height on the type. The host is the nearest framed
    floor, roof or soffit over the can; a can under a floor opening has none (UNKNOWN).
    """
    from shapely.geometry import Polygon

    cans = _ceiling_cans(ctx)
    if not cans:
        return [by_result(CID, Result.NOT_APPLICABLE, "no recessed ceiling luminaires", ())]
    model = ctx.model
    objects = {item.tag: item for item in model.canvas_objects}
    frame = _Frame(model)
    findings = []
    for can in cans:
        body = objects.get(can.tag)
        if body is None or body.body_z0_m is None or body.body_z1_m is None:
            findings.append(by_result(CID, Result.UNKNOWN,
                                      f"{can.tag}: housing body is unresolved", (can.tag,)))
            continue
        footprint = Polygon(body.footprint)
        z0, z1 = body.body_z0_m, body.body_z1_m
        host = frame.host(footprint, z0)
        if host is None or any(void.covers(footprint.centroid) for void in host[2]):
            where = f"under an opening in {host[1]}" if host else "with no framed system above"
            findings.append(by_result(CID, Result.UNKNOWN, f"{can.tag}: no host ceiling, {where}",
                                      (can.tag,), fix="move the can under a framed ceiling"))
            continue
        hits = frame.hits(footprint, z0, z1)
        message = (f"{can.tag} housing intersects {', '.join(hits)}" if hits else
                   f"{can.tag}: housing clears the framing and runs in {host[1]}")
        findings.append(by_result(CID, Result.FAIL if hits else Result.PASS, message,
                                  (can.tag,), fix="move the can into a clear bay, or use a "
                                  "shallower housing" if hits else None))
    return findings


def _shift(frame: _Frame, footprint: Any, z0: float, z1: float) -> str | None:
    """The shortest plan move along a house axis that clears the framing and runs, or None."""
    from shapely.affinity import translate

    steps = int(_SHIFT_MAX_M / _SHIFT_STEP_M)
    for step in range(1, steps + 1):
        distance = step * _SHIFT_STEP_M
        for name, dx, dy in _DIRECTIONS:
            moved = translate(footprint, dx * distance, dy * distance)
            if not frame.hits(moved, z0, z1):
                return f'{distance / M_PER_IN:.2f}" {name}'
    return None


@check(Tier.STRUCTURAL, BOX_CID)
def ceiling_box_framing(ctx: CheckContext) -> list[Finding]:
    """Each flush ceiling box's body (footprint x depth above the face) against the framing
    and runs above it. A pancake's body sits inside the board, so it clears the joist it
    screws under. A FAIL names the shortest move that clears the members."""
    from shapely.geometry import Polygon

    boxes = [b for b in ctx.model.device_boxes
             if b.host == "ceiling" and b.mounting != "surface"]
    if not boxes:
        return [not_applicable(BOX_CID, "no flush ceiling box")]
    frame = _Frame(ctx.model)
    out = []
    for box in sorted(boxes, key=lambda b: b.device_tag):
        footprint = Polygon(box.footprint)
        hits = frame.hits(footprint, box.z0_m, box.z1_m)
        tags = (box.device_tag,)
        if not hits:
            out.append(passed(BOX_CID, f"{box.device_tag}'s {box.box_product} box clears the "
                                       "framing and runs above it", tags))
            continue
        move = _shift(frame, footprint, box.z0_m, box.z1_m)
        fix = (f"move {box.device_tag} {move} into the clear bay" if move else
               f"move {box.device_tag} into a clear bay")
        out.append(failed(BOX_CID, f"{box.device_tag}'s {box.box_product} box intersects "
                                   f"{', '.join(hits)}", tags,
                          fix=fix + ", or author box_use='pancake' where centring governs"))
    return out


@check(Tier.STRUCTURAL, SUPPORT_CID)
def ceiling_box_support(ctx: CheckContext) -> list[Finding]:
    """A ceiling-fan luminaire's box is listed for a fan; earned N/A with no ceiling fan."""
    code = cite(NEC.FAN_BOX)
    types = {t.tag: t for t in ctx.plan.library.electrical_device_types}
    fans = {obj.tag for obj in ctx.model.canvas_objects
            if getattr(getattr(types.get(obj.type_ref or ""), "form", None), "value", None)
            == "ceiling_fan_light"}
    if not fans:
        return [not_applicable(SUPPORT_CID, "no ceiling-suspended fan in the house", code=code)]
    standard = next((el for el in ctx.plan.all_elements() if el.element_kind == "BoxStandard"),
                    None)
    boxes = {b.device_tag: b for b in ctx.model.device_boxes if b.host == "ceiling"}
    out = []
    for tag in sorted(fans):
        box = boxes.get(tag)
        if box is None or standard is None:
            out.append(unknown(SUPPORT_CID, f"{tag} has no derived ceiling box", (tag,),
                               code=code))
            continue
        row = next((r for r in standard.rows if r.box_product_ref == box.box_product
                    and r.mounting == box.mounting and r.use == box.box_use), None)
        if row is not None and row.fan_rated:
            out.append(passed(SUPPORT_CID, f"{tag}'s {box.box_product} box is listed for a fan",
                              (tag,), code=code))
        else:
            out.append(failed(SUPPORT_CID, f"{tag} hangs a fan from {box.box_product}, a box "
                                           "not listed for fan support", (tag,), code=code,
                              fix="a fan-rated row (BoxRow fan_rated=True, use='fan')"))
    return out
