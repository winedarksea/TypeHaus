"""``mep.terminal_neck_fit`` — does a terminal's boot, spigot or damper fit its cavity?

The neck box is ``resolve/terminal_necks.neck_boxes`` (one per register whose type states a
``TerminalNeck``). It is graded against the framing members and against every other run —
not its own ``duct_ref``, which it is plumbed to. ADVISORY: a boot clipping a stud is a
buildability fact, not a code section, and its result is still FAIL so a clean house stays
clean.
"""

from __future__ import annotations

from typehaus.checks._authoring import advisory, not_applicable, passed, unknown
from typehaus.checks.mep.framing_envelope import TOLERANCE_M, legs, member_footprint
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.quantities import M_PER_IN

_CID = "mep.terminal_neck_fit"


def _depth(a, b) -> float:
    """The shallower plan extent of ``a ∩ b`` — how far one bites into the other."""
    overlap = a.intersection(b)
    if overlap.is_empty or overlap.area <= 0:
        return 0.0
    x0, y0, x1, y1 = overlap.bounds
    return min(x1 - x0, y1 - y0)


@check(Tier.ADVISORY, _CID)
def terminal_neck_fit(ctx: CheckContext) -> list[Finding]:
    """A register's in-cavity part clears the framing and every run but its own."""
    from shapely.geometry import Polygon

    from typehaus.resolve.terminal_necks import neck_boxes

    boxes = neck_boxes(ctx.model)
    if not boxes:
        # Earned: every register type was read and none states a neck to place.
        return [not_applicable(_CID, "no register type in this plan states a TerminalNeck, "
                                     "so there is no in-cavity part to fit", ())]
    own = {e.tag: e.duct_ref for e in ctx.plan.all_elements()
           if e.element_kind == "Register"}
    owners = {e.uid: e.tag for e in ctx.plan.all_elements() if getattr(e, "uid", None)}
    # Furring and resilient channel are cut at a terminal by trade practice; framing is not.
    members = [(m, fp) for m in ctx.model.all_members() if m.category != "strapping"
               and (fp := member_footprint(m)) is not None]
    runs = legs(ctx.model)
    component_policy = {}
    for obj in ctx.model.canvas_objects:
        catalog = next((t for t in ctx.plan.library.register_types if t.tag == obj.type_ref), None)
        for component in getattr(getattr(catalog, "neck", None), "components", ()):
            component_policy[obj.tag, component.part] = component.receives_duct

    out: list[Finding] = []
    for tag, ring, z0, z1, part in boxes:
        if not ring:
            out.append(unknown(_CID, f"{tag}'s {part} could not be placed (no mount or body "
                                     "band, or a wall terminal whose host side was not "
                                     "found), so it is not graded", (tag,)))
            continue
        box = Polygon(ring)
        clashes: list[str] = []
        for member, (footprint, m0, m1) in members:
            if min(z1, m1) - max(z0, m0) <= TOLERANCE_M:
                continue
            bite = _depth(box, footprint)
            if bite > TOLERANCE_M:
                owner = owners.get(member.parent_uid, member.parent_uid)
                clashes.append(f"{owner} {member.child_key} by "
                               f"{bite / M_PER_IN:.2f}\"")
        for leg in runs:
            if leg.tag == own.get(tag) and component_policy.get((tag, part), True):
                continue
            low = min(leg.za, leg.zb) - leg.half_z_m
            high = max(leg.za, leg.zb) + leg.half_z_m
            if min(z1, high) - max(z0, low) <= TOLERANCE_M:
                continue
            bite = _depth(box, leg.footprint)
            if bite > TOLERANCE_M:
                clashes.append(f"{leg.kind} {leg.tag} by {bite / M_PER_IN:.2f}\"")
        if (tag, part) in component_policy:
            # Multipart assemblies occupy the whole cavity, including the actuator. The
            # older boot boxes keep their existing grading contract.
            for floor in ctx.model.floors:
                if (floor.deck_outline and floor.members
                        and box.intersects(Polygon(floor.deck_outline))):
                    deck_bottom = max(member.z1_m for member in floor.members)
                    if z0 < deck_bottom and z1 > deck_bottom + TOLERANCE_M:
                        clashes.append(f"{floor.tag} underside of deck")
            for obj in ctx.model.canvas_objects:
                if obj.tag == tag or obj.body_z0_m is None or obj.body_z1_m is None:
                    continue
                if min(z1, obj.body_z1_m) - max(z0, obj.body_z0_m) <= TOLERANCE_M:
                    continue
                if len(obj.footprint) >= 3 and _depth(box, Polygon(obj.footprint)) > TOLERANCE_M:
                    clashes.append(f"{obj.kind} {obj.tag}")
        span = f"{(z1 - z0) / M_PER_IN:.2f}\" tall at z {z0 / M_PER_IN:.2f}\""
        if clashes:
            out.append(advisory(
                _CID, f"{tag}'s {part} ({span}) meets " + ", ".join(sorted(set(clashes))[:4])
                      + (", ..." if len(set(clashes)) > 4 else ""),
                (tag,), Result.FAIL,
                fix="move the terminal to a clear bay, or pick a shallower boot or collar"))
        else:
            out.append(passed(_CID, f"{tag}'s {part} ({span}) clears the framing and every "
                                    "other run", (tag,)))
    from typehaus.resolve.terminal_connections import inlet_connection_error

    for obj in ctx.model.canvas_objects:
        if obj.kind != "Register":
            continue
        catalog = next((t for t in ctx.plan.library.register_types if t.tag == obj.type_ref), None)
        if catalog is None or catalog.neck is None or catalog.neck.inlet is None:
            continue
        problem = inlet_connection_error(ctx.model, obj.tag)
        if problem:
            out.append(advisory(_CID, f"{obj.tag}: {problem}", (obj.tag,), Result.FAIL,
                                fix="connect the matching duct mouth to the dimensioned inlet"))
        else:
            out.append(passed(_CID, f"{obj.tag}: feeding duct matches its dimensioned inlet",
                              (obj.tag,)))
    return out
