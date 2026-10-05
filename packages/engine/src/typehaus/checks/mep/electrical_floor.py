"""Floor receptacles: listed enclosures and clearance from floor framing."""

from __future__ import annotations

from typehaus.checks._authoring import by_result
from typehaus.checks.mep.framing_envelope import member_footprint
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result


def _floor_receptacles(ctx: CheckContext) -> list:
    from typehaus.checks.mep.electrical import _counts_as_a_125v_receptacle

    return [element for element in ctx.plan.all_elements()
            if element.element_kind == "ElectricalDevice"
            and _counts_as_a_125v_receptacle(ctx, element)
            and element.mount is not None and element.mount.kind.value == "floor"]


@check(Tier.CODE, "code.E3905_7_floor_boxes")
def listed_floor_boxes(ctx: CheckContext) -> list[Finding]:
    """A receptacle's listing does not substitute for a box listed for floor use."""
    cid, code = "code.E3905_7_floor_boxes", "E3905.7 / NEC 314.27(B)"
    devices = _floor_receptacles(ctx)
    if not devices:
        return [by_result(cid, Result.NOT_APPLICABLE, "no floor receptacles", (), code)]
    types = {item.tag: item for item in ctx.plan.library.electrical_device_types}
    findings = []
    for device in devices:
        product = types.get(device.type_ref)
        listing = (product.floor_box_listing or "").strip() if product else ""
        if listing:
            findings.append(by_result(cid, Result.PASS,
                                      f"{device.tag}: {listing}", (device.tag,), code))
        else:
            findings.append(by_result(
                cid, Result.UNKNOWN,
                f"{device.tag} has no declared listing for a floor-box assembly",
                (device.tag,), code, "specify a box listed for floor receptacles"))
    return findings


@check(Tier.STRUCTURAL, "electrical.floor_box_framing")
def floor_box_framing(ctx: CheckContext) -> list[Finding]:
    """Keep a recessed box's full catalog envelope clear of joists, rims and blocking.

    Using the outer envelope (including the flange) is conservative: a clear result
    guarantees the smaller cutout clears framing too, without guessing a body shape.
    This checks the box, not unmodeled branch wiring or hidden site conditions.
    """
    from shapely.geometry import Polygon

    cid = "electrical.floor_box_framing"
    devices = [device for device in _floor_receptacles(ctx)
               if device.mount.recessed_into_host_surface]
    if not devices:
        return [by_result(cid, Result.NOT_APPLICABLE, "no recessed floor receptacles", ())]
    objects = {item.tag: item for item in ctx.model.canvas_objects}
    findings = []
    for device in devices:
        body = objects.get(device.tag)
        if body is None or body.body_z0_m is None or body.body_z1_m is None:
            findings.append(by_result(cid, Result.UNKNOWN,
                                      f"{device.tag}: box body is unresolved", (device.tag,)))
            continue
        footprint = Polygon(body.footprint)
        floors = [floor for floor in ctx.model.floors
                  if floor.storey == body.storey
                  and Polygon(floor.deck_outline).covers(footprint.centroid)]
        if not floors:
            findings.append(by_result(
                cid, Result.UNKNOWN, f"{device.tag}: no modeled framed floor under the box",
                (device.tag,)))
            continue
        hits = []
        for floor in floors:
            for member in floor.members:
                envelope = member_footprint(member)
                if envelope is None:
                    continue
                member_polygon, bottom, top = envelope
                if (min(top, body.body_z1_m) > max(bottom, body.body_z0_m)
                        and footprint.intersection(member_polygon).area > 0):
                    hits.append(f"{floor.tag}/{member.child_key}")
        result = Result.FAIL if hits else Result.PASS
        message = (f"{device.tag} intersects floor framing: {', '.join(hits)}" if hits else
                   f"{device.tag}: recessed box envelope clears modeled floor framing")
        findings.append(by_result(cid, result, message, (device.tag,),
                                  fix="move the box into a clear bay; do not cut framing"
                                  if hits else None))
    return findings
