"""R311.7.8.2 wall clearance and R311.7.1 projection, measured off the drawn top rail.

Both read the same samples: the ``{tag}-RAIL1`` sweep every :data:`_SAMPLE_M`, each against
the nearest *parallel* wall finish face (``resolve/railings/wall_contact``) — the reading
the bracket arms are drawn from, so the gap graded is the gap drawn.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.checks.code.mn_residential._common import _fail, _na, _pass, _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.structure import Railing
from typehaus.quantities import inch
from typehaus.resolve.railings.parts import rail_half_section_m
from typehaus.resolve.railings.wall_contact import nearest_wall_face
from typehaus.resolve.sweep import clean_path

#: R311.7.8.2: handrails adjacent to a wall have at least 1-1/2" between wall and rail.
MIN_WALL_CLEARANCE = inch(1.5)
#: R311.7.1: a handrail projects no more than 4-1/2" into the required stair width.
MAX_PROJECTION = inch(4.5)
_SAMPLE_M = 0.1

Vec3 = tuple[float, float, float]


@dataclass(frozen=True)
class RailSample:
    """One station on a drawn top rail: where, which way, and the wall face beside it."""

    point: Vec3
    direction: tuple[float, float]
    wall_tag: str | None
    to_face_m: float | None  # centreline to finish face, plan


def serving_handrails(ctx: CheckContext) -> list[Railing]:
    """Every railing that is (or doubles as) a stair handrail."""
    return [e for e in ctx.plan.all_elements() if isinstance(e, Railing)
            and e.role in ("handrail", "guard_and_handrail") and e.serves_stair]


def top_rail_path(ctx: CheckContext, rail: Railing) -> tuple[Vec3, ...]:
    """The drawn top rail's 3D centreline, or () when none was resolved."""
    solid = next((s for s in ctx.model.solids if s.tag == f"{rail.tag}-RAIL1"), None)
    if solid is None or solid.sweep is None:
        return ()
    return tuple(clean_path(solid.sweep.path))


def rail_samples(ctx: CheckContext, rail: Railing) -> list[RailSample]:
    """Stations every :data:`_SAMPLE_M` along the drawn top rail, each with its wall face."""
    path = top_rail_path(ctx, rail)
    out: list[RailSample] = []
    for a, b in zip(path[:-1], path[1:], strict=False):
        d = (b[0] - a[0], b[1] - a[1])
        run = math.hypot(*d)
        if run < 1e-9:
            continue
        steps = max(int(math.ceil(run / _SAMPLE_M)), 1)
        for k in range(steps + 1):
            t = k / steps
            p = (a[0] + d[0] * t, a[1] + d[1] * t, a[2] + (b[2] - a[2]) * t)
            contact = nearest_wall_face(ctx.model, (p[0], p[1]), p[2], along=(d,))
            out.append(RailSample(p, d, contact.wall_tag if contact else None,
                                  contact.distance_m if contact else None))
    return out


def _grade(ctx: CheckContext, cid: str, code: str, *, clearance: bool) -> list[Finding]:
    if not ctx.model.stairs:
        return [_unknown(cid, "no resolved stairs", (), code)]
    rails = serving_handrails(ctx)
    if not rails:
        return [_unknown(cid, "no Railing declares a handrail role", (), code)]
    out: list[Finding] = []
    for rail in rails:
        tags = (rail.tag, rail.serves_stair)
        samples = rail_samples(ctx, rail)
        if not samples:
            out.append(_unknown(cid, f"handrail {rail.tag}: no drawn top rail to measure",
                                (rail.tag,), code))
            continue
        beside = [s for s in samples if s.to_face_m is not None]
        if not beside:
            out.append(_na(cid, f"handrail {rail.tag}: no wall runs alongside it within "
                           "9\" — free-standing", (rail.tag,), code))
            continue
        half = rail_half_section_m(ctx.plan.library, rail)
        walls = ", ".join(sorted({s.wall_tag for s in beside if s.wall_tag}))
        if clearance:
            worst = min(s.to_face_m for s in beside) - half
            ok = worst >= MIN_WALL_CLEARANCE.meters - 1e-6
            msg = (f"handrail {rail.tag} stands {worst / 0.0254:.2f}\" clear of {walls} "
                   "at its closest; R311.7.8.2 requires 1-1/2\"")
        else:
            worst = max(s.to_face_m for s in beside) + half
            ok = worst <= MAX_PROJECTION.meters + 1e-6
            msg = (f"handrail {rail.tag} projects {worst / 0.0254:.2f}\" from {walls} at "
                   "most; R311.7.1 allows 4-1/2\"")
        out.append(_pass(cid, msg, code) if ok else _fail(cid, msg, tags, code))
    return out


@check(Tier.CODE, "code.R311_7_8_2_handrail_wall_clearance")
def handrail_wall_clearance(ctx: CheckContext) -> list[Finding]:
    """R311.7.8.2 — a handrail beside a wall leaves at least 1-1/2" to grip around."""
    return _grade(ctx, "code.R311_7_8_2_handrail_wall_clearance", "R311.7.8.2",
                  clearance=True)


@check(Tier.CODE, "code.R311_7_1_handrail_projection")
def handrail_projection(ctx: CheckContext) -> list[Finding]:
    """R311.7.1 — a handrail projects no more than 4-1/2" from the wall it is mounted on."""
    return _grade(ctx, "code.R311_7_1_handrail_projection", "R311.7.1", clearance=False)
