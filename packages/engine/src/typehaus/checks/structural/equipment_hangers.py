"""A hung machine's trapeze, graded on published reads (``resolve/equipment_hangers.py``).

Three statements per hung unit: every rod lands on a member (with a bridge to a second);
the case weight over ``count`` is within the rod's and the top fixing's ``Product.rated_load_lb``
(one lag carries the rod's whole load, conservatively); and each joist's bridge-seat loads, in
every ``JoistFlangeAllowance.window``, are within the maker's bottom-flange allowance (and its
one-side limit, where read: a bridge bears beside the web). An
unread weight, rating or allowance is UNKNOWN, naming it. Prescriptive, never ``engineered()``:
each limit is a line a reviewer finds in the cited document. IMC 304.1 (install per the
manufacturer and the listing) is the code hook.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed, not_applicable, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding

CID = "structural.equipment_hangers"
CODE = "IMC 304.1; manufacturer's published ratings"


@check(Tier.STRUCTURAL, CID)
def equipment_hangers(ctx: CheckContext) -> list[Finding]:
    rods = list(getattr(ctx.model, "equipment_hangers", ()))
    if not rods:
        return [not_applicable(CID, "no Equipment authors hangers")]
    products = {p.tag: p for p in ctx.plan.library.products}
    by_unit: dict[str, list] = {}
    for rod in rods:
        by_unit.setdefault(rod.equipment_tag, []).append(rod)
    out: list[Finding] = []
    for tag, unit in sorted(by_unit.items()):
        out.append(_landing(tag, unit))
        out.extend(_ratings(tag, unit, products))
    out.extend(_flanges(ctx, rods))
    return out


def _landing(tag: str, unit: list) -> Finding:
    loose = [r for r in unit if r.gap]
    if loose:
        return unknown(CID, f"{tag}: {len(loose)} of {len(unit)} rods have no seat — "
                       + "; ".join(f"rod {r.rod}: {r.gap}" for r in loose),
                       (tag,), code=CODE)
    hosts = sorted({s.member for r in unit for s in r.bridge})
    drops = [r.drop_m / 0.0254 for r in unit]
    return passed(CID, f"{tag}: {len(unit)} rods each bridged to two members "
                  f"({', '.join(hosts)}), drops {min(drops):.1f}-{max(drops):.1f}\"",
                  (tag,), code=CODE)


def _ratings(tag: str, unit: list, products: dict) -> list[Finding]:
    load = unit[0].load_lb
    if load is None:
        return [unknown(CID, f"{tag}: its type publishes no weight_lb, so the per-rod load "
                        "is unread", (tag,), code=CODE)]
    out = []
    for role, ref in (("rod", unit[0].rod_product_ref),
                      ("top fixing", unit[0].fixing_product_ref)):
        product = products.get(ref)
        rating = getattr(product, "rated_load_lb", None)
        if rating is None:
            out.append(unknown(CID, f"{tag}: {role} {ref} has no published rated_load_lb",
                               (tag, ref), code=CODE))
            continue
        verdict = passed if load <= rating else failed
        out.append(verdict(CID, f"{tag}: {load:.1f} lb per rod on {role} {ref}, rated "
                           f"{rating:,.0f} lb ({load / rating:.2f})", (tag, ref), code=CODE))
    return out


def _flanges(ctx: CheckContext, rods: list) -> list[Finding]:
    allowances = {a.member: a for a in
                  getattr(ctx.plan.library, "joist_flange_allowances", ()) or ()}
    seats: dict[str, list[tuple[float, float, str, str | None, int]]] = {}
    for rod in rods:
        for seat in rod.bridge:
            load = None if rod.load_lb is None else rod.load_lb * seat.share
            seats.setdefault(seat.member, []).append(
                (seat.along_m, load, rod.equipment_tag, seat.profile, seat.side))
    out = []
    for member, rows in sorted(seats.items()):
        tags = tuple(sorted({r[2] for r in rows}))
        profile = rows[0][3]
        allowance = allowances.get(profile or "")
        if allowance is None:
            out.append(unknown(CID, f"{member}: no published bottom-flange allowance for "
                               f"{profile or 'its profile'}", tags, code=CODE))
            continue
        if any(r[1] is None for r in rows):
            out.append(unknown(CID, f"{member}: a hung unit's weight is unread", tags,
                               code=allowance.source))
            continue
        window = allowance.window.meters
        worst = _worst_window([(r[0], r[1]) for r in rows], window)
        ok = worst <= allowance.max_load_lb
        text = (f"{member} ({profile}): {worst:.1f} lb hung in {window / 0.3048:.0f}' of "
                f"bottom flange, allowed {allowance.max_load_lb:,.0f} lb")
        side_cap = allowance.max_side_load_lb
        if side_cap is not None:
            side = max(_worst_window([(r[0], r[1]) for r in rows if r[4] == s], window)
                       for s in {r[4] for r in rows})
            ok = ok and side <= side_cap
            text += f"; {side:.1f} lb on one side of the web, allowed {side_cap:,.0f} lb"
        out.append((passed if ok else failed)(CID, text, tags, code=allowance.source))
    return out


def _worst_window(points: list[tuple[float, float]], window_m: float) -> float:
    """Largest load sum over any ``window_m`` of the joist."""
    points.sort()
    return max(sum(load for at, load in points if start <= at <= start + window_m)
               for start, _ in points)
