"""Handrail hardware: R311.7.8.2 end terminations and R301.5 support spacing.

* **Ends.** "Handrail ends shall be returned or shall terminate in newel posts or safety
  terminals." A plain end cap is none of those. A ``wall_return`` must have been drawn
  (``{tag}-RETURN{n}``); a ``newel`` must have a post at that end; a post-mounted rail
  earns newel from its own POST solids. Unstated on a wall rail is UNKNOWN.
* **Spacing.** R301.5's 200 lb concentrated load is carried bracket to bracket, so the
  span between supports may not exceed what the product states (``RailingType
  .bracket_spacing_max``). Supports are the BRACKET solids with a wall behind them and the
  drawn returns; a stub bracket with no wall carries nothing.
"""

from __future__ import annotations

import math

from typehaus.checks.code.mn_residential._common import _fail, _na, _pass, _unknown
from typehaus.checks.code.mn_residential.handrail_clearance import (
    serving_handrails,
    top_rail_path,
)
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.structure import Railing
from typehaus.quantities import inch
from typehaus.resolve.railings.parts import railing_type

#: How close a post must stand to a rail end to be the newel it terminates in.
_NEWEL_REACH_M = inch(6).meters
_WALL_MOUNTS = frozenset({"wall"})
#: A bracket no longer than its own 1" section is a stub with no wall behind it.
_STUB_EXTENT_M = inch(1.0).meters + 0.001


def _end_points(rail: Railing) -> tuple[tuple[float, float], tuple[float, float]]:
    return rail.path[0].xy_m, rail.path[-1].xy_m


def _post_near(ctx: CheckContext, point: tuple[float, float]) -> str | None:
    for solid in ctx.model.solids:
        if "-POST" not in solid.tag or not solid.outline:
            continue
        cx = sum(x for x, _ in solid.outline) / len(solid.outline)
        cy = sum(y for _, y in solid.outline) / len(solid.outline)
        if math.hypot(cx - point[0], cy - point[1]) <= _NEWEL_REACH_M:
            return solid.tag
    return None


def _end_verdict(ctx: CheckContext, rail: Railing, index: int, point,
                 stated: str | None) -> tuple[str, str]:
    """``(result, words)`` for one end, result in pass / fail / unknown."""
    label = "start" if index == 1 else "end"
    if rail.mount not in _WALL_MOUNTS and stated in (None, "newel"):
        post = _post_near(ctx, point)
        return (("pass", f"{label} terminates in post {post}") if post else
                ("unknown", f"{label} names no termination and no post stands there"))
    if stated is None:
        return "unknown", f"{label} termination not stated"
    if stated == "open":
        return "fail", f"{label} is open (an end cap is not a return)"
    if stated == "wall_return":
        drawn = any(s.tag == f"{rail.tag}-RETURN{index}" for s in ctx.model.solids)
        return (("pass", f"{label} returns to the wall") if drawn else
                ("fail", f"{label} is authored wall_return but no return reached a wall"))
    if stated == "newel":
        post = _post_near(ctx, point)
        return (("pass", f"{label} terminates in newel {post}") if post else
                ("unknown", f"{label} names a newel but no post stands within 6\""))
    return "pass", f"{label} ends in a safety terminal (as authored)"


@check(Tier.CODE, "code.R311_7_8_2_handrail_ends")
def handrail_ends(ctx: CheckContext) -> list[Finding]:
    """R311.7.8.2 — handrail ends return, or terminate in newel posts or safety terminals."""
    cid, code = "code.R311_7_8_2_handrail_ends", "R311.7.8.2"
    if not ctx.model.stairs:
        return [_unknown(cid, "no resolved stairs", (), code)]
    rails = serving_handrails(ctx)
    if not rails:
        return [_unknown(cid, "no Railing declares a handrail role", (), code)]
    out: list[Finding] = []
    for rail in rails:
        start, end = _end_points(rail)
        ends = (_end_verdict(ctx, rail, 1, start, rail.start_termination),
                _end_verdict(ctx, rail, 2, end, rail.end_termination))
        words = f"handrail {rail.tag}: " + "; ".join(w for _, w in ends)
        results = {r for r, _ in ends}
        if "fail" in results:
            out.append(_fail(cid, words, (rail.tag,), code))
        elif "unknown" in results:
            out.append(_unknown(cid, words, (rail.tag,), code))
        else:
            out.append(_pass(cid, words, code))
    return out


def _station_along(path, point: tuple[float, float]) -> float:
    """Developed (3D) distance along ``path`` to the plan foot of ``point``."""
    best, best_d, walked = 0.0, math.inf, 0.0
    for a, b in zip(path[:-1], path[1:], strict=False):
        dx, dy = b[0] - a[0], b[1] - a[1]
        run2 = dx * dx + dy * dy
        seg3 = math.dist(a, b)
        t = 0.0 if run2 < 1e-18 else max(0.0, min(1.0, (
            (point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / run2))
        d = math.hypot(point[0] - (a[0] + dx * t), point[1] - (a[1] + dy * t))
        if d < best_d:
            best, best_d = walked + seg3 * t, d
        walked += seg3
    return best


def support_stations(ctx: CheckContext, rail: Railing, path) -> tuple[list[float], int]:
    """Developed stations of every real support, and how many brackets had no wall."""
    stations: list[float] = []
    stubs = 0
    for solid in ctx.model.solids:
        if not solid.tag.startswith(f"{rail.tag}-") or not solid.outline:
            continue
        suffix = solid.tag[len(rail.tag) + 1:]
        if suffix.startswith("RETURN") and solid.sweep is not None:
            start = solid.sweep.path[0]
            stations.append(_station_along(path, (start[0], start[1])))
        elif suffix.startswith("BRACKET"):
            # An arm reaches a wall; a stub is the bare 1" cleat dropped where none was
            # found (resolve/railings/frame.emit_brackets), and carries nothing.
            xs = [x for x, _ in solid.outline]
            ys = [y for _, y in solid.outline]
            if max(max(xs) - min(xs), max(ys) - min(ys)) <= _STUB_EXTENT_M:
                stubs += 1
                continue
            stations.append(_station_along(path, (sum(xs) / len(xs), sum(ys) / len(ys))))
    return sorted(stations), stubs


@check(Tier.CODE, "code.R301_5_handrail_support_spacing")
def handrail_support_spacing(ctx: CheckContext) -> list[Finding]:
    """R301.5 — a wall handrail's supports sit no farther apart than its product allows."""
    cid, code = "code.R301_5_handrail_support_spacing", "R301.5"
    if not ctx.model.stairs:
        return [_unknown(cid, "no resolved stairs", (), code)]
    rails = serving_handrails(ctx)
    if not rails:
        return [_unknown(cid, "no Railing declares a handrail role", (), code)]
    out: list[Finding] = []
    for rail in rails:
        if rail.mount not in _WALL_MOUNTS:
            out.append(_na(cid, f"handrail {rail.tag} is carried by posts, not brackets",
                           (rail.tag,), code))
            continue
        product = railing_type(ctx.plan.library, rail)
        limit = product.bracket_spacing_max if product is not None else None
        if limit is None:
            out.append(_unknown(cid, f"handrail {rail.tag} names no product bracket "
                                "spacing (RailingType.bracket_spacing_max)", (rail.tag,),
                                code))
            continue
        path = top_rail_path(ctx, rail)
        stations, stubs = support_stations(ctx, rail, path)
        if len(stations) < 2:
            out.append(_fail(cid, f"handrail {rail.tag} has {len(stations)} support(s) "
                             "with a wall behind them", (rail.tag,), code))
            continue
        widest = max(b - a for a, b in zip(stations[:-1], stations[1:], strict=True))
        stub_note = f"; {stubs} bracket(s) with no wall behind them ignored" if stubs else ""
        msg = (f"handrail {rail.tag}: {len(stations)} supports, widest span "
               f"{widest / 0.0254:.1f}\" against the product's {limit.inches:.1f}\""
               f"{stub_note}")
        out.append(_pass(cid, msg, code) if widest <= limit.meters + 1e-6
                   else _fail(cid, msg, (rail.tag,), code))
    return out
