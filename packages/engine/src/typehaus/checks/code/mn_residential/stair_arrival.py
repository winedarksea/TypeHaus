"""R311.7.6 at the head of a flight: is there a FLOOR there, or the hole it is cut in?

Its own module, not a third rule in ``stairs.py`` — that file is already 667 lines against
``AGENTS.md``'s 500 — and the separation is real: every rule there measures a DIMENSION of
the stairway, and this one asks a question about the deck beside it.

The gap it closes is stated in :func:`stair_arrival_floor`. In short: the two R311.7.5.1
rules between them grade a flight's interior and its two end RISERS, and both read the
arrival deck through the well the flight is cut in — so a flight that stops a going short of
its own opening edge arrives at exactly the right height over open air, and passes.
"""

from __future__ import annotations

import math

from shapely.geometry import Point, Polygon

from typehaus.checks.code.mn_residential._common import _fail, _pass, _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, not_applicable

#: How far past the top nosing, as a fraction of a going, the first footfall off a flight
#: lands. Half a going is inside the arrival tread's own depth, so the probe is never a
#: question about the *next* surface along; and it is far enough off the opening ring that
#: containment is never decided on a boundary coincidence.
_ARRIVAL_PROBE_GOINGS = 0.5


@check(Tier.CODE, "code.R311_7_6_stair_arrival_floor")
def stair_arrival_floor(ctx: CheckContext) -> list[Finding]:
    """R311.7.6: there is a floor, not a hole, where the top nosing puts a foot down.

    ``code.R311_7_5_1_stair_end_risers`` asks how far the last step is; this asks whether
    there is anything to step onto at all. They are not the same question and the first
    cannot answer the second: it compares *elevations*, reading the arrival deck through
    ``deck_owning_opening`` — the deck the well is cut in — whatever the flight's plan
    position inside that well happens to be. A flight that stops a going short of its own
    opening edge arrives at the right height over open air, and passes.

    That is not hypothetical. It is what ``resolve/stairs/u_split.py`` built until
    2026-09-15 on any U-stair with an odd tread split: the upper flight was laid out
    backwards from the *lower* flight's line, so ST-M2S's head stood 10" out into
    ``FO-S-STAIR`` — a 10" x 3'-6 3/8" strip of open floor opening across the whole width of
    the stair. Nothing in the engine saw it. See ``notes/u_stair_split_landing.md``.

    So: step half a going off the top nosing along the walking route's own direction, and
    ask what is there. Inside the stair's own floor opening with nothing standing at the
    arrival elevation is a **FAIL**. Nothing found anywhere is UNKNOWN, not a pass — a floor
    nobody drew is exactly the ambiguity the end-riser rule already refuses to guess at
    (ST-SG-PORCH heads onto 12" of wall top that is deliberately not modelled). A stair that
    perforates no deck has no opening edge to fall short of, and that absence is positive:
    NOT_APPLICABLE.
    """
    from typehaus.resolve.stairs.walkline import stair_walk_stations
    from typehaus.resolve.walking_surface import surfaces_at as _surfaces_at

    cid, code = "code.R311_7_6_stair_arrival_floor", "R311.7.6"
    if not ctx.model.stairs:
        return [_unknown(cid, "no resolved stairs", (), code)]
    out: list[Finding] = []
    for stair in ctx.model.stairs:
        route = stair_walk_stations(stair)
        if len(route) < 2:
            out.append(not_applicable(cid, f"{stair.tag} resolves fewer than two walking "
                                      "stations, so it has no arrival nosing",
                                      (stair.tag,), code))
            continue
        opening_tag = getattr(ctx.plan.by_tag(stair.tag), "floor_opening", None)
        opening = ctx.plan.by_tag(opening_tag) if opening_tag else None
        ring = [point.xy_m for point in getattr(opening, "outline", ())]
        if len(ring) < 3:
            out.append(not_applicable(cid, f"{stair.tag} perforates no floor opening, so "
                                      "its head has no opening edge to fall short of",
                                      (stair.tag,), code))
            continue
        (ax, ay), (bx, by), arrival_z = route[-1]
        (px, py), (qx, qy), _ = route[-2]
        nose = ((ax + bx) / 2.0, (ay + by) / 2.0)
        back = ((px + qx) / 2.0, (py + qy) / 2.0)
        dx, dy = nose[0] - back[0], nose[1] - back[1]
        span = math.hypot(dx, dy)
        if span < 1e-9:
            out.append(_unknown(cid, f"{stair.tag}'s arrival station has no travel "
                                "direction to step off along", (stair.tag,), code))
            continue
        step = _ARRIVAL_PROBE_GOINGS * stair.going_depth_m
        probe = (nose[0] + dx / span * step, nose[1] + dy / span * step)
        band = stair.riser_height_m / 2.0
        surfaces = _surfaces_at(ctx.model, probe)
        standing = [s for s in surfaces
                    if abs((s.surface_m if s.surface_m is not None else s.deck_top_m)
                           - arrival_z) <= band]
        inside = Polygon(ring).contains(Point(*probe))
        if standing:
            out.append(_pass(cid, f"{stair.tag} steps off its top nosing onto "
                             f"{standing[0].deck_tag}", code))
        elif inside:
            short = math.hypot(*_nearest_edge_offset(ring, nose))
            out.append(_fail(cid, f"{stair.tag}'s top nosing stands {short / .0254:.2f}\" "
                             f"inside {opening_tag} with no surface at the arrival "
                             "elevation — the flight ends over the hole it is cut in; "
                             "R311.7.6 requires a floor or landing at the top of a "
                             "stairway", (stair.tag, opening_tag), code))
        else:
            out.append(_unknown(cid, f"{stair.tag} steps off its top nosing outside "
                                f"{opening_tag} onto no modelled surface, so the floor it "
                                "arrives at is undrawn", (stair.tag,), code))
    return out


def _nearest_edge_offset(ring: list[tuple[float, float]],
                         point: tuple[float, float]) -> tuple[float, float]:
    """Vector from ``point`` to the nearest point on ``ring``'s boundary — how far short."""
    best = (float("inf"), (0.0, 0.0))
    px, py = point
    for (x0, y0), (x1, y1) in zip(ring, [*ring[1:], ring[0]], strict=True):
        dx, dy = x1 - x0, y1 - y0
        run2 = dx * dx + dy * dy
        t = 0.0 if run2 < 1e-18 else max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy)
                                                 / run2))
        cx, cy = x0 + dx * t, y0 + dy * t
        gap = math.hypot(px - cx, py - cy)
        if gap < best[0]:
            best = (gap, (cx - px, cy - py))
    return best[1]
