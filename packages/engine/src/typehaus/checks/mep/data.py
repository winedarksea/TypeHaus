"""Structured-cabling checks — does every low-voltage endpoint have a raceway to it?

Deliberately a graph walk with no distance tolerance. Branch wiring is undrawn by doctrine
(model/mep.py ConduitRun: "only main trunks are modeled"), so a proximity test between a
device and the nearest raceway end would be measuring a cable nobody authored, and whatever
radius it used would be invented. What *is* authored is the ``from_ref``/``to_ref`` graph,
and that is exactly the thing that goes wrong: an access point gets placed and its raceway
does not.
"""

from __future__ import annotations

from typehaus.checks._authoring import advisory, passed as _pass, unknown as _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.enums import DeviceKind, Service


# WARN severity (not the usual ERROR) + FAIL result, deliberately: the permit integrity
# gate only blocks on ERROR severity, and this finding is advisory, not a hard blocker.
def _fail(cid: str, msg: str, tags: tuple[str, ...]) -> Finding:
    return advisory(cid, msg, tags, Result.FAIL)


@check(Tier.ADVISORY, "electrical.data_reachability")
def data_reachability(ctx: CheckContext) -> list[Finding]:
    """Every data device is served by a data raceway, and every data raceway reaches the head end.

    The head end is whichever ``DATA_OUTLET`` no data raceway names as its ``to_ref`` — the
    patch enclosure, derived rather than named by tag so the check does not hard-code one
    house's vocabulary. Exactly one is expected: two means a second, disconnected star, and
    none means the runs form a cycle with no source.
    """
    cid = "electrical.data_reachability"
    devices = [element for storey in ctx.plan.storeys
               for element in ctx.plan.storey_elements(storey.tag)
               if element.element_kind == "ElectricalDevice"
               and element.kind is DeviceKind.DATA_OUTLET]
    runs = [element for storey in ctx.plan.storeys
            for element in ctx.plan.storey_elements(storey.tag)
            if element.element_kind == "ConduitRun" and element.service is Service.DATA]
    if not devices and not runs:
        return [_unknown(cid, "no structured cabling modeled")]
    if not runs:
        return [_fail(cid, f"{len(devices)} data device(s) but no data raceway carries "
                           "them — every drop is undrawn",
                      tuple(sorted(d.tag for d in devices)))]

    served = {run.to_ref for run in runs if run.to_ref}
    heads = [device for device in devices if device.tag not in served]
    out: list[Finding] = []

    for device in sorted(devices, key=lambda d: d.tag):
        if device.tag in served:
            out.append(_pass(cid, f"data device {device.tag} is served by a data raceway",
                             (device.tag,)))
        elif len(heads) == 1 and device is heads[0]:
            out.append(_pass(cid, f"data device {device.tag} is the head end — the raceways "
                                  "originate here", (device.tag,)))
        else:
            out.append(_fail(cid, f"data device {device.tag} is not the to_ref of any data "
                                  "raceway — it has no pathway back to the head end",
                             (device.tag,)))

    if len(heads) > 1:
        out.append(_fail(cid, "more than one head end — these data devices are served by no "
                              f"raceway: {', '.join(sorted(d.tag for d in heads))}",
                         tuple(sorted(d.tag for d in heads))))

    # Walk the from_ref chain: a raceway whose source is neither the head end nor another
    # data raceway's destination is an island, however well-formed it looks on its own.
    reachable = {heads[0].tag} if len(heads) == 1 else set()
    remaining = list(runs)
    progressed = True
    while progressed and remaining:
        progressed = False
        for run in list(remaining):
            if run.from_ref in reachable:
                if run.to_ref:
                    reachable.add(run.to_ref)
                remaining.remove(run)
                progressed = True
    for run in sorted(remaining, key=lambda r: r.tag):
        out.append(_fail(cid, f"data raceway {run.tag} starts at {run.from_ref or '(nothing)'}, "
                              "which is not reachable from the head end", (run.tag,)))
    for run in sorted((r for r in runs if r not in remaining), key=lambda r: r.tag):
        out.append(_pass(cid, f"data raceway {run.tag} chains back to the head end",
                         (run.tag,)))
    return out
