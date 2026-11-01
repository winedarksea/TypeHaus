"""A wall header must stand under its own wall's plates, never inside them.

The solver grows a header UP from the rough head by its spec depth and nothing clips it, and
``structural.member_interference`` excuses every header/plate contact as joinery. So a header
deeper than the room between the head and the plates simply runs through the plates, and
nothing said so (geometry review C3-E1/E2). This is the grader.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding

_CHECK_ID = "integrity.header_under_plate"
_TOL_M = 1e-4
_IN = 0.0254


def _along(axis, point) -> float:
    (x0, y0), (x1, y1) = axis
    dx, dy = x1 - x0, y1 - y0
    length = (dx * dx + dy * dy) ** 0.5 or 1.0
    return ((point[0] - x0) * dx + (point[1] - y0) * dy) / length


def _range(axis, member) -> tuple[float, float]:
    a, b = _along(axis, member.p0), _along(axis, member.p1)
    return min(a, b), max(a, b)


@check(Tier.INTEGRITY, _CHECK_ID)
def header_under_plate(ctx: CheckContext) -> list[Finding]:
    out: list[Finding] = []
    for wall in ctx.model.walls:
        plates = [m for m in wall.members if m.category == "plate"]
        for header in (m for m in wall.members if m.category == "header"):
            lo, hi = _range(wall.axis, header)
            hits = [p for p in plates
                    if header.z1_m > p.z0_m + _TOL_M and header.z0_m < p.z1_m - _TOL_M
                    and min(hi, _range(wall.axis, p)[1]) - max(lo, _range(wall.axis, p)[0])
                    > _TOL_M]
            if not hits:
                continue
            into = header.z1_m - min(p.z0_m for p in hits)
            tag = header.opening_tag or header.child_key
            out.append(failed(
                _CHECK_ID,
                f"{wall.tag}'s {header.profile} header over {tag} runs {into / _IN:.2f}\" "
                f"into its own plates ({', '.join(sorted(p.child_key for p in hits))}): "
                f"header z {header.z0_m / _IN:.2f}..{header.z1_m / _IN:.2f}\", lowest plate "
                f"underside {min(p.z0_m for p in hits) / _IN:.2f}\"",
                (wall.tag,) + ((header.opening_tag,) if header.opening_tag else ()),
                fix=("a shallower header (R602.7.4 flat nonbearing where the wall carries "
                     "nothing), a shorter rough opening, or carry the load in the floor band "
                     "(Door.header_in_band)")))
    return out
