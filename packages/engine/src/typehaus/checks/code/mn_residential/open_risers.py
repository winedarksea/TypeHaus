"""R311.7.5.1 open risers: a 4" sphere through a riser more than 30" above the floor below.

Every step of a flight is a gap between two walking faces. It is closed when a resolved
``riser`` member (``Stair.riser_thickness``) stands in it, or when the carriage itself is the
riser (a box tier's rim, a cast tier). Otherwise its clear height is the step less the board
above it, and the sphere passes where that is 4" or more. The floor below is the flight's
springing floor, which is conservative for any step over a higher floor. An opening counts
as above 30" when its top is. Oracle: ``houses/catlin/notes/stair_riser_basis.md``.
"""

from __future__ import annotations

from typehaus.checks.code.mn_residential._common import _fail, _na, _pass, _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.quantities import inch
from typehaus.resolve.model import ResolvedStair

CHECK_ID = "code.R311_7_5_1_open_risers"
_CODE = "R311.7.5.1"
_SPHERE_M = inch(4).meters
_HEIGHT_M = inch(30).meters
_TOL_M = 0.002
_WALKING = frozenset({"tread", "winder", "landing"})


def steps(stair: ResolvedStair) -> list[tuple[float, float, float, bool]]:
    """``(lower face, upper underside, opening top above the floor below, closed)`` for
    every step, springing floor to arrival."""
    boards = [m for m in stair.members if m.category in _WALKING]
    if not boards:
        return []
    thick = {round(m.z1_m, 4): m.z1_m - m.z0_m for m in boards}
    faces = sorted(thick)
    base = (stair.base_elevation_m if stair.base_elevation_m is not None
            else faces[0] - stair.riser_height_m)
    arrival = (stair.arrival_elevation_m if stair.arrival_elevation_m is not None
               else faces[-1] + stair.riser_height_m)
    board = min(thick.values())
    levels = [base, *faces, arrival]
    under = [*(thick[f] for f in faces), board]
    risers = [m.z0_m for m in stair.members if m.category == "riser"]
    out = []
    for lower, upper, depth in zip(levels, levels[1:], under, strict=False):
        if upper - lower < _TOL_M:
            continue
        top = upper - depth
        closed = any(abs(z - lower) < _TOL_M for z in risers)
        out.append((lower, top, top - base, closed))
    return out


@check(Tier.CODE, CHECK_ID)
def open_risers(ctx: CheckContext) -> list[Finding]:
    if not ctx.model.stairs:
        return [_unknown(CHECK_ID, "no resolved stairs", (), _CODE)]
    out: list[Finding] = []
    for stair in ctx.model.stairs:
        tags = (stair.tag,)
        carriage = getattr(ctx.plan.by_tag(stair.tag), "carriage", "stringer")
        if carriage in ("box", "cast"):
            out.append(_pass(CHECK_ID, f"{stair.tag}: each {carriage} tier closes its own "
                             "riser", _CODE))
            continue
        flight = steps(stair)
        if not flight:
            out.append(_na(CHECK_ID, f"{stair.tag} resolves no walking surface, so it has "
                           "no riser", tags, _CODE))
            continue
        open_ = [(lo, top, above) for lo, top, above, closed in flight if not closed]
        if not open_:
            out.append(_pass(CHECK_ID, f"{stair.tag}: all {len(flight)} risers closed",
                             _CODE))
            continue
        bad = [(top - lo, above) for lo, top, above in open_
               if top - lo >= _SPHERE_M - 1e-6 and above > _HEIGHT_M + 1e-6]
        widest = max(top - lo for lo, top, _ in open_) / 0.0254
        if bad:
            gap, above = max(bad, key=lambda item: item[1])
            out.append(_fail(
                CHECK_ID, f"{stair.tag}: {len(bad)} open riser(s) pass a 4\" sphere more than "
                f"30\" above the floor below (a {gap / 0.0254:.2f}\" opening topping out "
                f"{above / 0.0254:.1f}\" up); close them: Stair.riser_thickness", tags, _CODE))
        else:
            out.append(_pass(CHECK_ID, f"{stair.tag}: {len(open_)} open riser(s), widest "
                             f"{widest:.2f}\", none both 4\" or more and over 30\" up",
                             _CODE))
    return out


__all__ = ["CHECK_ID", "open_risers", "steps"]
