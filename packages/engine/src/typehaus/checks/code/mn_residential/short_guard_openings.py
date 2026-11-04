"""A short guard bay may need no picket: measure its actual bounding post faces."""

import math

from typehaus.quantities import inch
from typehaus.resolve.railings.guard_line import guard_post_stations


def short_bay_opening_m(ctx, guard, limit_m):
    stations = guard_post_stations(ctx.plan.library, guard)
    posts = [s for s in ctx.model.solids if s.category == "railing" and "-POST" in s.tag]
    outlines = []
    for station in stations:
        matches = [s.outline for s in posts if math.dist(station, (
            sum(p[0] for p in s.outline)/len(s.outline),
            sum(p[1] for p in s.outline)/len(s.outline))) < inch(1/16).meters]
        if not matches:
            return None
        outlines.append(matches[0])
    gaps = []
    for index, (a, b) in enumerate(zip(stations[:-1], stations[1:], strict=True)):
        run = math.dist(a, b)
        if run <= 1e-9:
            return None
        axis = ((b[0]-a[0])/run, (b[1]-a[1])/run)

        def project(point, origin=a, direction=axis):
            return (point[0]-origin[0])*direction[0]+(point[1]-origin[1])*direction[1]

        gap = min(map(project, outlines[index+1]))-max(map(project, outlines[index]))
        if gap > limit_m + 1e-9:
            return None
        gaps.append(max(0, gap))
    return max(gaps) if gaps else None
