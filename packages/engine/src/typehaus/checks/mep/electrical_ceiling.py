"""Recessed ceiling cans: the housing body must sit in a clear bay of the frame above."""

from __future__ import annotations

from typehaus.checks._authoring import by_result
from typehaus.checks.mep.framing_envelope import (
    TOLERANCE_M,
    band_over,
    legs,
    member_footprint,
    z_overlap,
)
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result

CID = "electrical.ceiling_can_framing"
#: A host this far below the body's base still counts as above it (a soffit's underside).
_HOST_SLACK_M = 0.05


def _ceiling_cans(ctx: CheckContext) -> list:
    return [element for element in ctx.plan.all_elements()
            if element.element_kind == "ElectricalDevice"
            and element.mount is not None and element.mount.kind.value == "ceiling"
            and element.mount.recessed_into_host_surface]


def _hosts(model) -> list[tuple[str, float, float, object, tuple, list]]:
    """(tag, z band, plan shape, voids, members) for every framed system a can can sit in.

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


@check(Tier.STRUCTURAL, CID)
def ceiling_can_framing(ctx: CheckContext) -> list[Finding]:
    """Keep a recessed can's housing clear of joists, rafters, blocking, ducts and pipes.

    The body is the type's footprint over ``height`` above the ceiling plane, so a clear
    result needs the real housing height on the type. The host is the nearest framed
    floor, roof or soffit over the can; a can under a floor opening has none (UNKNOWN).
    """
    from shapely.geometry import Polygon
    from shapely.strtree import STRtree

    cans = _ceiling_cans(ctx)
    if not cans:
        return [by_result(CID, Result.NOT_APPLICABLE, "no recessed ceiling luminaires", ())]
    model = ctx.model
    objects = {item.tag: item for item in model.canvas_objects}
    hosts = _hosts(model)
    framing = []
    for tag, _low, _high, _shape, _voids, members in hosts:
        for member in members:
            envelope = member_footprint(member)
            if envelope is not None:
                framing.append((f"{tag}/{member.child_key}", *envelope))
    tree = STRtree([shape for _, shape, _, _ in framing])
    runs = [leg for leg in legs(model) if leg.kind in ("pipe", "duct")]
    run_tree = STRtree([leg.footprint for leg in runs])
    findings = []
    for can in cans:
        body = objects.get(can.tag)
        if body is None or body.body_z0_m is None or body.body_z1_m is None:
            findings.append(by_result(CID, Result.UNKNOWN,
                                      f"{can.tag}: housing body is unresolved", (can.tag,)))
            continue
        footprint = Polygon(body.footprint)
        z0, z1 = body.body_z0_m, body.body_z1_m
        over = [(max(low, z0), tag, voids) for tag, low, high, shape, voids, _ in hosts
                if high >= z0 - _HOST_SLACK_M and shape.covers(footprint.centroid)]
        host = min(over, key=lambda item: item[0]) if over else None
        if host is None or any(void.covers(footprint.centroid) for void in host[2]):
            where = f"under an opening in {host[1]}" if host else "with no framed system above"
            findings.append(by_result(CID, Result.UNKNOWN, f"{can.tag}: no host ceiling, {where}",
                                      (can.tag,), fix="move the can under a framed ceiling"))
            continue
        hits = []
        for i in tree.query(footprint):
            name, shape, bottom, top = framing[i]
            if (min(top, z1) - max(bottom, z0) > TOLERANCE_M
                    and footprint.intersection(shape).area > 0):
                hits.append(name)
        for i in run_tree.query(footprint):
            leg = runs[i]
            band = band_over(leg, footprint)
            if band is not None and z_overlap(leg, band, z0, z1) > TOLERANCE_M:
                hits.append(f"{leg.kind} {leg.tag}")
        hits = sorted(set(hits))
        message = (f"{can.tag} housing intersects {', '.join(hits)}" if hits else
                   f"{can.tag}: housing clears the framing and runs in {host[1]}")
        findings.append(by_result(CID, Result.FAIL if hits else Result.PASS, message,
                                  (can.tag,), fix="move the can into a clear bay, or use a "
                                  "shallower housing" if hits else None))
    return findings
