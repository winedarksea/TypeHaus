"""What digs near a buried utility: trellis posts, tree holes and bioretention basins.

The first check of its kind — ``params/raised_garden.py`` notes none existed. Horizontal
only: a locate mark is good to ±2 ft (Minn. Stat. ch. 216D), and inside that band the
excavation is hand-dug whatever the depth, so depth does not excuse a conflict.
"""

from __future__ import annotations

from shapely.geometry import LineString, Point, Polygon, box

from typehaus.checks._authoring import advisory, not_applicable
from typehaus.checks._authoring import passed as _pass
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.landscape import Plant, RainGarden, Trellis
from typehaus.resolve.landscape import _dressed_m, trellis_post_stations

_CITE = "Minn. Stat. ch. 216D"
#: Locate marks are good to plus or minus two feet.
TOLERANCE_ZONE_M = 24 * 0.0254
#: An assumed 36-in planting hole for a tree or shrub (1.5x a 24-in dwarf root ball).
PLANTING_HOLE_RADIUS_M = 18 * 0.0254


def _diggers(ctx: CheckContext):
    """``(tag, plan geometry)`` for everything that excavates."""
    types = {t.tag: t for t in ctx.model.plan.library.plant_types}
    for element in ctx.model.plan.all_elements():
        if isinstance(element, Trellis):
            half = _dressed_m(element.post) / 2.0
            for k, (x, y) in enumerate(trellis_post_stations(element)):
                yield f"{element.tag}-P{k + 1}", box(x - half, y - half, x + half, y + half)
        elif isinstance(element, Plant):
            ptype = types.get(element.type_ref)
            if ptype is not None and ptype.form in ("tree", "shrub"):
                yield element.tag, Point(element.position.xy_m).buffer(PLANTING_HOLE_RADIUS_M)
        elif isinstance(element, RainGarden):
            yield element.tag, Polygon([p.xy_m for p in element.outline])


@check(Tier.ADVISORY, "site.utility_clearance")
def utility_clearance(ctx: CheckContext) -> list[Finding]:
    cid = "site.utility_clearance"
    lines = [u for u in ctx.model.plan.project.site.utilities if len(u.path) >= 2]
    diggers = list(_diggers(ctx))
    if not diggers:
        return [not_applicable(cid, "nothing on the site digs: no trellis, tree or basin")]
    if not lines:
        return [advisory(cid, "UNKNOWN — the site authors no utility lines to clear",
                         (), Result.UNKNOWN, code=_CITE)]
    out: list[Finding] = []
    for tag, shape in diggers:
        gap, kind = min((LineString([p.xy_m for p in u.path]).distance(shape), u.kind.value)
                        for u in lines)
        if gap < TOLERANCE_ZONE_M:
            out.append(advisory(
                cid, f"{tag} digs {gap / 0.0254:.0f}\" from the {kind} line, inside the "
                     f"24\" locate tolerance zone — move it or hand-dig after a locate",
                (tag,), Result.FAIL, code=_CITE))
    if not out:
        out.append(_pass(cid, f"{len(diggers)} excavations clear every utility line by the "
                              f"24\" tolerance zone", code=_CITE))
    return out
