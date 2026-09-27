"""``mep.drain_inlet_spacing`` — two branches landing on one stack, graded on fittings.

Two drain runs ending on one vertical barrel a few inches apart are two fittings stacked,
and whether they fit is a question about where each pattern's branch centreline sits
between its socket stops. ``library/fittings.py`` carries those stations for the full-size
(N x N x N) sanitary tee, wye, combo and street tee/wye, read off Charlotte Pipe
SUB-PAC-PVC-DWV. For a close pair the check takes the tightest catalogued stack —
the lower fitting's branch-to-top, the upper's branch-to-bottom, and a nipple of two socket
depths unless the upper is a street pattern whose spigot seats in the lower's hub — and
grades the authored spacing against it: PASS at or above it, FAIL below.

Which patterns may serve an inlet follows how it arrives: a branch within 22.5 degrees of
level takes a sanitary pattern (tee, combo, street tee), one near 45 degrees a wye. A
reducing pair, an uncatalogued size or any other approach stays UNKNOWN, named with the
spacing so somebody opening a submittal knows which number to look up.

``Tier.STRUCTURAL`` and **no ``PermitItemSpec``**, the same footing as
``mep.run_interference`` and ``mep.fitting_pattern``: no code section states a laying length,
and a CODE tier would trip the coverage test and the ``code_ref`` requirement dishonestly.
"""

from __future__ import annotations

import math

from typehaus.checks._authoring import failed as _fail
from typehaus.checks._authoring import passed as _pass
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.hardware.fittings import (
    KIND_COMBO,
    KIND_STREET_TEE,
    KIND_STREET_WYE,
    KIND_TEE,
    KIND_WYE,
    SERVICE_DRAIN,
    FittingSpec,
    fitting_catalog,
)
from typehaus.quantities import M_PER_IN

_CID = "mep.drain_inlet_spacing"

#: Two inlets further apart than this many BARREL DIAMETERS raise no question unless the
#: catalog says the tightest stack needs more: three diameters clears a full-sweep fitting
#: body on the larger pipe, the convention ``run_interference.JOINT_REACH_FACTOR`` states.
INLET_SCREEN_DIAMETERS = 3.0

#: A plan offset under this is "on the same vertical". A sixteenth of an inch is the grid
#: every coordinate in this repo is authored on.
SAME_BARREL_M = 0.0015875

#: The same sixteenth, as the slack a spacing may fall short of a published stack.
_SLACK_IN = 1.0 / 16.0

#: The patterns an inlet may be, by how it arrives (degrees off level, inclusive bands).
_SANITARY = (KIND_TEE, KIND_COMBO, KIND_STREET_TEE)
_WYES = (KIND_WYE, KIND_STREET_WYE)
_LABEL = {KIND_TEE: "sanitary tee 400", KIND_WYE: "wye 600", KIND_COMBO: "combo 501",
          KIND_STREET_TEE: "street sanitary tee 403", KIND_STREET_WYE: "street wye 602"}


@check(Tier.STRUCTURAL, _CID)
def drain_inlet_spacing(ctx: CheckContext) -> list[Finding]:
    """Branches landing on one vertical drain barrel, sorted by elevation.

    A barrel is a vertical segment of a drain run — a repeated plan point at two
    elevations. An inlet is another drain run's END on that plan point, within the barrel's
    own z span. Each consecutive pair is graded against the tightest catalogued stack.
    """
    barrels = _barrels(ctx)
    if not barrels:
        return [_pass(_CID, "no drain run resolves a vertical barrel, so no two branches "
                            "can land on one", ())]

    runs = {r.tag: r for r in ctx.model.pipe_runs}
    out: list[Finding] = []
    for tag, point, z0_m, z1_m, diameter_m in barrels:
        inlets = sorted(_inlets_on(ctx, tag, point, z0_m, z1_m))
        screen_in = INLET_SCREEN_DIAMETERS * diameter_m / M_PER_IN
        for (low_z, low_tag), (high_z, high_tag) in zip(inlets[:-1], inlets[1:], strict=False):
            gap_in = (high_z - low_z) / M_PER_IN
            tags = (tag, low_tag, high_tag)
            stack = _tightest_stack(runs[tag], runs[low_tag], runs[high_tag], point)
            if stack is None:
                if gap_in <= screen_in:
                    out.append(_unknown(
                        _CID,
                        f"{low_tag} and {high_tag} both land on {tag}'s vertical barrel "
                        f"{gap_in:.2f}\" apart, and no catalogued stack covers the pair "
                        f"(sizes {_nominal(runs[low_tag]):g}/{_nominal(runs[high_tag]):g} on "
                        f"{_nominal(runs[tag]):g}\", or an approach that is neither level "
                        f"nor 45 degrees) — the screen is {INLET_SCREEN_DIAMETERS:.0f} "
                        f"barrel diameters ({screen_in:.2f}\"), a stated convention",
                        tags,
                        fix="read the stack stations off the two fittings' submittal into "
                            "library/fittings.py — or move one branch so the question does "
                            "not arise"))
                continue
            pitch, lower, upper = stack
            pages = ", ".join(dict.fromkeys(_page(f.source) for f in (lower, upper)))
            pair = (f"{_LABEL[lower.kind]} + {_LABEL[upper.kind]}, "
                    f"Charlotte SUB-PAC-PVC-DWV {pages}")
            if gap_in + _SLACK_IN < pitch:
                out.append(_fail(
                    _CID,
                    f"{low_tag} and {high_tag} land on {tag}'s vertical barrel "
                    f"{gap_in:.2f}\" apart; no catalogued fitting pair stacks two "
                    f"{_nominal(runs[tag]):g}\" branches closer than {pitch:.2f}\" "
                    f"({pair})", tags,
                    fix=f"move one branch to at least {pitch:.2f}\" from the other"))
            elif gap_in <= screen_in:
                out.append(_pass(_CID, f"{low_tag} and {high_tag} land on {tag} "
                                       f"{gap_in:.2f}\" apart; the tightest stack is "
                                       f"{pitch:.2f}\" c/l ({pair})", ()))

    if not out:
        out.append(_pass(_CID, f"{len(barrels)} vertical drain barrel(s) carry no two "
                               "branch inlets within a fitting's reach of each other", ()))
    return out


def _page(source: str) -> str:
    """The ``p. NN`` a catalog row's source cites."""
    return next((part.split(":")[0].strip() for part in source.split(", ")
                 if part.startswith("p. ")), source)


def _nominal(run) -> float:
    """A run's nominal size in inches, to the sixteenth the catalog is keyed on."""
    return round(run.diameter_m / M_PER_IN * 16) / 16


def _tightest_stack(barrel, low, high, point
                    ) -> tuple[float, FittingSpec, FittingSpec] | None:
    """``(pitch in, lower, upper)`` for the closest catalogued stack, or None."""
    size = _nominal(barrel)
    if _nominal(low) != size or _nominal(high) != size:
        return None
    lowers, uppers = _candidates(low, point, size), _candidates(high, point, size)
    best = None
    for lower in lowers:
        for upper in uppers:
            nipple = 0.0 if upper.spigot_bottom else 2 * upper.socket_depth_in
            pitch = lower.branch_to_top_in + upper.branch_to_bottom_in + nipple
            if best is None or pitch < best[0]:
                best = (pitch, lower, upper)
    return best


def _candidates(run, point, size: float) -> list[FittingSpec]:
    """The catalogued full-size patterns this inlet may be, by how it arrives."""
    slope = _approach_deg(run, point)
    if slope is None:
        return []
    kinds = _SANITARY if slope <= 22.5 else _WYES if slope <= 67.5 else ()
    return [f for f in fitting_catalog()
            if f.service == SERVICE_DRAIN and f.kind in kinds and f.nominal_in == size
            and f.branch_in == size and f.branch_to_top_in is not None
            and f.branch_to_bottom_in is not None
            and (f.spigot_bottom or f.socket_depth_in is not None)]


def _approach_deg(run, point) -> float | None:
    """Degrees off level of the segment by which ``run`` arrives at ``point``."""
    for end, prev in ((0, 1), (-1, -2)):
        x, y = run.path[end]
        if abs(x - point[0]) > SAME_BARREL_M or abs(y - point[1]) > SAME_BARREL_M:
            continue
        px, py = run.path[prev]
        rise = abs(run.z_m[prev] - run.z_m[end])
        return math.degrees(math.atan2(rise, math.hypot(px - x, py - y)))
    return None


def _barrels(ctx: CheckContext
             ) -> list[tuple[str, tuple[float, float], float, float, float]]:
    """Every vertical drain segment, as ``(tag, plan point, z low, z high, diameter)``."""
    out = []
    for run in ctx.model.pipe_runs:
        if run.system != "drain" or not run.z_m or len(run.z_m) != len(run.path):
            continue
        for index in range(len(run.path) - 1):
            a, b = run.path[index], run.path[index + 1]
            za, zb = run.z_m[index], run.z_m[index + 1]
            if abs(a[0] - b[0]) > SAME_BARREL_M or abs(a[1] - b[1]) > SAME_BARREL_M:
                continue
            if abs(za - zb) <= SAME_BARREL_M:
                continue
            out.append((run.tag, tuple(a), min(za, zb), max(za, zb), run.diameter_m))
    return out


def _inlets_on(ctx: CheckContext, barrel_tag: str, point: tuple[float, float],
               z0_m: float, z1_m: float) -> list[tuple[float, str]]:
    """``(elevation, tag)`` for every other drain run ENDING on this barrel.

    Only an END counts, which is the rule every joint reading in this repo states: a run
    crossing a stack mid-span is a clash and ``mep.run_interference`` reports it as one.
    """
    out = []
    for run in ctx.model.pipe_runs:
        if run.tag == barrel_tag or run.system != "drain" or not run.z_m:
            continue
        if len(run.z_m) != len(run.path) or len(run.path) < 1:
            continue
        for index in (0, -1):
            x, y = run.path[index]
            if abs(x - point[0]) > SAME_BARREL_M or abs(y - point[1]) > SAME_BARREL_M:
                continue
            z = run.z_m[index]
            if z0_m - SAME_BARREL_M <= z <= z1_m + SAME_BARREL_M:
                out.append((z, run.tag))
                break
    return out
