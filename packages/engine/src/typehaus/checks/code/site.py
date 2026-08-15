"""Site setback check (→ Permit-ready plan set Phase 4).

Shapely is already a dependency (checks/advisory, checks/building_science). Distance is
measured from every wall-axis endpoint to the finite parcel-edge segment the setback
applies to — a reasonable approximation near corners without a full offset-polygon solve.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.quantities import M_PER_IN

# Setbacks are a *local zoning* requirement, not an IRC one — there is no section number to
# cite, and citing one would be a fabrication. "local zoning" is the honest citation, and
# saying so is what lets the coverage test insist every CODE finding carries one.
_SETBACK_REF = "local zoning"


def _pass(cid: str, msg: str, tags: tuple[str, ...] = ()) -> Finding:
    return passed(cid, msg, tags, code=_SETBACK_REF)


def _fail(cid: str, msg: str, tags: tuple[str, ...]) -> Finding:
    return failed(cid, msg, tags, code=_SETBACK_REF)


def _unknown(cid: str, reason: str, tags: tuple[str, ...] = ()) -> Finding:
    return unknown(cid, reason, tags, code=_SETBACK_REF)


@check(Tier.CODE, "code.site_setback")
def site_setback(ctx: CheckContext) -> list[Finding]:
    from shapely.geometry import LineString, Point

    site = ctx.plan.project.site
    parcel = [p.xy_m for p in site.parcel]
    if len(parcel) < 3 or not site.setbacks:
        return [_unknown("code.site_setback", "site setbacks not modeled")]

    out: list[Finding] = []
    n = len(parcel)
    for spec in site.setbacks:
        a, b = parcel[spec.edge % n], parcel[(spec.edge + 1) % n]
        edge = LineString([a, b])
        label = spec.label or f"edge {spec.edge}"
        violations: list[tuple[str, float]] = []
        for wall in ctx.model.walls:
            for point in (wall.axis[0], wall.axis[1]):
                dist = Point(point).distance(edge)
                if dist + 1e-6 < spec.distance.meters:
                    shortfall_in = (spec.distance.meters - dist) / M_PER_IN
                    violations.append((wall.tag, shortfall_in))
        if violations:
            tag, shortfall_in = max(violations, key=lambda item: item[1])
            out.append(_fail(
                "code.site_setback",
                f"wall {tag} is {shortfall_in:.1f}\" short of the {label} setback "
                f"({spec.distance.inches / 12:.0f}')", (tag,),
            ))
        else:
            out.append(_pass(
                "code.site_setback", f"{label} setback ({spec.distance.inches / 12:.0f}') "
                "satisfied by every wall",
            ))
    return out
