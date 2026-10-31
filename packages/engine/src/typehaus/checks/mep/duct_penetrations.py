"""``mep.duct_penetration_fit`` — does a duct fit the hole that exists for it?

``mep.run_through_opening`` exempts a run from the rough opening that names it in
``penetration_for``, which is right (the hole is FOR it) and left the fit itself ungraded:
catlin's ``AO-S-ERV-EA`` once sat 1" off its own duct, the duct's far edge 1/2" outside the
hole, through a full verification run. This grades the named pairing instead of skipping it,
and grades a ``SleevePenetration.serves_duct`` wall seal the same way.

The section graded is the duct's BARE outside size. A wrapped outdoor-air leg's insulation
stops in the stud bay (catlin's through-wall detail); outboard of it the annulus is canned
foam, so the hole has to hold the bare duct plus a foam annulus, and the wrapped OD is
``framing_envelope``'s business against the studs.
"""

from __future__ import annotations

import math

from typehaus.checks._authoring import advisory, not_applicable, passed
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.quantities import M_PER_IN

_CID = "mep.duct_penetration_fit"

#: The least gap a low-expansion canned foam fills and bonds across (window-and-door grade
#: is applied as a 1/4"-plus bead). Below it the annulus is a caulk joint, not a foam seal.
MIN_FOAM_ANNULUS_M = 0.25 * M_PER_IN


def _inches(metres: float) -> str:
    return f'{metres / M_PER_IN:.2f}"'


def _wall_crossing(duct, axis) -> tuple[float, float] | None:
    """``(distance along the wall axis, z)`` where the duct crosses the wall's centre line.

    The first segment whose plan line changes side of the wall's centre line, interpolated
    to the line; None if the duct never crosses that wall.
    """
    (ax, ay), (bx, by) = axis[0], axis[-1]
    length = math.dist((ax, ay), (bx, by))
    if length <= 0 or len(duct.z_m) != len(duct.path):
        return None
    ux, uy = (bx - ax) / length, (by - ay) / length

    def side(p) -> float:
        return (p[0] - ax) * -uy + (p[1] - ay) * ux

    for (p, za), (q, zb) in zip(zip(duct.path, duct.z_m, strict=False),
                                zip(duct.path[1:], duct.z_m[1:], strict=False), strict=False):
        sp, sq = side(p), side(q)
        if sp * sq > 0 or abs(sp - sq) < 1e-12:
            continue
        t = sp / (sp - sq)
        x, y = p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t
        return (x - ax) * ux + (y - ay) * uy, za + (zb - za) * t
    return None


def _half_sizes(duct) -> tuple[float, float]:
    """Half the bare section, (across the wall's length, vertical)."""
    if duct.diameter_m is not None:
        return duct.diameter_m / 2.0, duct.diameter_m / 2.0
    return duct.width_m / 2.0, duct.depth_m / 2.0


def _opening_findings(ctx: CheckContext, ducts: dict) -> list[Finding]:
    walls = {wall.tag: wall for wall in ctx.model.walls}
    out: list[Finding] = []
    for opening in ctx.model.openings:
        wall = walls.get(opening.host_wall)
        if wall is None or len(wall.axis) < 2:
            continue
        for tag in opening.penetration_for or ():
            duct = ducts.get(tag)
            if duct is None:
                continue  # a pipe or raceway hole; this grades ducts
            crossing = _wall_crossing(duct, wall.axis)
            if crossing is None:
                out.append(advisory(
                    _CID, f"{tag} is named by {opening.tag} but never crosses {wall.tag}",
                    (tag, opening.tag), Result.FAIL,
                    fix="carry the run through the hole, or drop it from penetration_for"))
                continue
            along, z = crossing
            half_w, half_h = _half_sizes(duct)
            low = wall.base_ref_z_m + opening.sill_m
            margin_x = (opening.width_m / 2.0 - abs(along - opening.center_along_m)
                        - half_w - MIN_FOAM_ANNULUS_M)
            margin_z = (opening.height_m / 2.0 - abs(z - (low + opening.height_m / 2.0))
                        - half_h - MIN_FOAM_ANNULUS_M)
            worst = min(margin_x, margin_z)
            what = (f"{tag} ({_inches(2 * half_w)} bare) through {opening.tag} "
                    f"({_inches(opening.width_m)} x {_inches(opening.height_m)}): "
                    f"{_inches(abs(along - opening.center_along_m))} off centre across, "
                    f"{_inches(abs(z - (low + opening.height_m / 2.0)))} vertically")
            if worst < -1e-6:
                out.append(advisory(
                    _CID, what + f" — {_inches(-worst)} short of a "
                                 f"{_inches(MIN_FOAM_ANNULUS_M)} foam annulus all round",
                    (tag, opening.tag), Result.FAIL,
                    fix="centre the hole on the duct, or grow it"))
            else:
                out.append(passed(
                    _CID, what + f"; {_inches(worst)} spare beyond a "
                                 f"{_inches(MIN_FOAM_ANNULUS_M)} foam annulus",
                    (tag, opening.tag)))
    return out


def _seal_findings(ctx: CheckContext, ducts: dict) -> list[Finding]:
    walls = {wall.tag: wall for wall in ctx.model.walls}
    out: list[Finding] = []
    for sleeve in ctx.model.sleeves:
        if not sleeve.serves_duct:
            continue
        duct = ducts.get(sleeve.serves_duct)
        tags = (sleeve.tag, sleeve.serves_duct)
        if duct is None:
            out.append(advisory(_CID, f"{sleeve.tag} serves {sleeve.serves_duct}, which "
                                      "resolves no duct run", tags, Result.FAIL))
            continue
        bare = 2.0 * max(_half_sizes(duct))
        problems: list[str] = []
        if abs(sleeve.pipe_d_m - bare) > 1e-4:
            problems.append(f"it states a {_inches(sleeve.pipe_d_m)} duct and the run is "
                            f"{_inches(bare)}")
        annulus = (sleeve.sleeve_d_m - bare) / 2.0
        wall = walls.get(sleeve.host_slab)
        crossing = _wall_crossing(duct, wall.axis) if wall is not None else None
        offset = 0.0
        if crossing is not None and sleeve.center_z_m is not None:
            (ax, ay), (bx, by) = wall.axis[0], wall.axis[-1]
            length = math.dist((ax, ay), (bx, by)) or 1.0
            along_sleeve = ((sleeve.center[0] - ax) * (bx - ax)
                            + (sleeve.center[1] - ay) * (by - ay)) / length
            offset = math.hypot(crossing[0] - along_sleeve, crossing[1] - sleeve.center_z_m)
        elif crossing is None:
            problems.append(f"{duct.tag} never crosses {sleeve.host_slab}")
        else:
            problems.append("it states no centre elevation to measure the duct against")
        if annulus - offset < MIN_FOAM_ANNULUS_M - 1e-6:
            problems.append(f"{_inches(annulus)} annulus less {_inches(offset)} offset is under "
                            f"the {_inches(MIN_FOAM_ANNULUS_M)} a foam seal needs")
        if sleeve.host_category == "framed_wall" and not (sleeve.seal and sleeve.insulation):
            problems.append("a framed-wall crossing must state its seal and its annulus fill")
        if problems:
            out.append(advisory(_CID, f"{sleeve.tag}: " + "; ".join(problems), tags,
                                Result.FAIL))
        else:
            out.append(passed(_CID, f"{sleeve.tag} seals {duct.tag} ({_inches(bare)} bare) "
                                    f"with a {_inches(annulus)} annulus, "
                                    f"{_inches(offset)} off centre", tags))
    return out


@check(Tier.ADVISORY, _CID)
def duct_penetration_fit(ctx: CheckContext) -> list[Finding]:
    """A duct's own rough opening or wall seal holds its bare section plus a foam annulus."""
    ducts = {duct.tag: duct for duct in ctx.model.ducts}
    out = _opening_findings(ctx, ducts) + _seal_findings(ctx, ducts)
    if not out:
        # Earned: every opening's penetration_for and every sleeve's serves_duct was read.
        return [not_applicable(_CID, "no rough opening or sleeve in this plan exists for a "
                                     "duct, so there is no duct penetration to fit", ())]
    return out
