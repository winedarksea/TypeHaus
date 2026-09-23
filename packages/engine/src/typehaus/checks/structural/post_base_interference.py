"""Framing in the space a post base occupies (→ 12 §checks/structural).

A standoff post base (an ABU) puts steel and 1" of air between a post's end grain and the
pour: ``resolve/envelope._post_connector_insets`` already starts the wood that far up, off
the catalog's ``bearing_standoff_in``. Nothing graded that space. A connector draws only a
marker box, and ``structural.member_interference`` clears a beam hung off the post by the
hanger the author named — so a beam end sitting on the same pier top, inside the post's
footprint, shared its volume with the base at 0 FAIL (catlin's ``PT-BW-W``/``-GW``: a seat
beam end and ``PT-BW-CW``/``-CNW``'s ``ABU66SS`` on one 12" circle).

**The envelope is the carried post's own footprint over the standoff height**: from the
post's resolved bottom down by the catalog standoff, to the bearing surface. That is a
lower bound on the part — the stirrup's side plates rise up the post faces, and no catalog
record here measures them — so a clash this reports is certain, and one it passes is only
clear of the standoff.

A base whose part has no measured standoff has no envelope and is not graded; it is named
in the summary rather than passed.
"""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.checks.structural._interference_geom import _TOL_AREA, framing_candidates
from typehaus.checks.structural.interference import _ENVELOPE_SKIN_KINDS
from typehaus.findings import Finding, Result, Severity, not_applicable
from typehaus.quantities import inch

_CHECK_ID = "structural.post_base_interference"


def _bases(model) -> list[tuple[str, str, float]]:
    """``(connector tag, carried post tag, standoff m)`` for every authored post base."""
    from typehaus.model.enums import ConnectorKind
    from typehaus.model.structure import Connector
    from typehaus.resolve.envelope import _post_connector_insets

    insets = _post_connector_insets(model)
    out = []
    for el in model.plan.all_elements():
        if isinstance(el, Connector) and el.kind is ConnectorKind.POST_BASE:
            carried = [t for t in el.connects if insets.get(t, (0.0, 0.0))[0] > 0.0]
            out.append((el.tag, carried[0] if carried else "",
                        insets[carried[0]][0] if carried else 0.0))
    return out


@check(Tier.STRUCTURAL, _CHECK_ID)
def post_base_interference(ctx: CheckContext) -> list[Finding]:
    """No framing member shares the standoff space of an authored post base."""
    from shapely.geometry import Polygon

    if getattr(ctx.model, "plan", None) is None:
        return []
    bases = _bases(ctx.model)
    if not bases:
        return [not_applicable(_CHECK_ID, "no post base is authored in this plan, so no "
                               "standoff space exists to share")]
    tol_z = inch(ctx.preferences.framing.interference_tolerance_in).meters
    posts = {s.tag: s for s in ctx.model.solids if s.category == "column"}
    connects = {tag: set(el.connects) for el in ctx.model.plan.all_elements()
                if (tag := getattr(el, "tag", None)) and hasattr(el, "connects")}
    cands = [c for c in framing_candidates(ctx.model) if c.kind not in _ENVELOPE_SKIN_KINDS]
    out: list[Finding] = []
    clear: list[str] = []
    unmeasured: list[str] = []
    for tag, post_tag, standoff in bases:
        post = posts.get(post_tag)
        if post is None or standoff <= 0.0:
            unmeasured.append(tag)
            continue
        poly = Polygon(post.outline)
        z0, z1 = post.z0_m - standoff, post.z0_m
        named = connects.get(tag, set()) | {post_tag}
        hit = False
        for c in cands:
            if c.label in named or c.parent in named:
                continue
            inter = poly.intersection(c.poly)
            if inter.area <= _TOL_AREA:
                continue
            rp = inter.representative_point()
            lo, hi = c.zband_at((rp.x, rp.y))
            overlap = min(hi, z1) - max(lo, z0)
            if overlap <= tol_z:
                continue
            hit = True
            out.append(Finding(
                severity=Severity.WARN, check_id=_CHECK_ID, result=Result.FAIL,
                message=(f"[advisory, not engineering] {c.label} occupies the standoff of "
                         f"{tag} ({post_tag}'s post base): "
                         f"{inter.area / inch(1).meters ** 2:.1f} sq in of the post's "
                         f"footprint, {overlap / inch(1).meters:.2f}\" of its "
                         f"{standoff / inch(1).meters:.2f}\" standoff"),
                element_tags=(c.label, tag, post_tag),
                fix_hint=("stop the member at the post face and carry it on its own bearing, "
                          "or give the post and the member separate supports"),
            ))
        if not hit:
            clear.append(tag)
    if clear:
        out.append(Finding(
            severity=Severity.WARN, check_id=_CHECK_ID, result=Result.PASS,
            message=(f"[advisory, not engineering] {len(clear)} post base standoff(s) are "
                     f"clear of every framing member (the stirrup plates above are not "
                     f"measured and not graded)"),
            element_tags=tuple(sorted(clear))))
    if unmeasured:
        out.append(Finding(
            severity=Severity.WARN, check_id=_CHECK_ID, result=Result.UNKNOWN,
            message=(f"{len(unmeasured)} post base(s) carry no post with a measured "
                     f"standoff, so there is no envelope to grade"),
            element_tags=tuple(sorted(unmeasured)),
            fix_hint="record bearing_standoff_in on the part's catalog record"))
    return out
