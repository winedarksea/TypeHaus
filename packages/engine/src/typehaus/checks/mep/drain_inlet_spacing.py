"""``mep.drain_inlet_spacing`` — two branches landing on one stack, and what is not known.

``houses/catlin/plan/mep_drainage.py`` carries an authored claim: that the attic branch and
the suite WC branch are "two inlets on one barrel, not a double fitting at one point". They
land 2½" apart on the same vertical. Nothing in the engine tested that claim —
``mep.drain_tie_in`` grades that a branch lands *on* the pipe and ``mep.fitting_pattern``
grades that a turn names an orderable part, and neither measures the spacing between two
inlets.

**This check can only ever be UNKNOWN, and that is correct.** Whether two wyes fit 2½" apart
is a question about their laying length, and every ``center_to_face_in`` in
``library/fittings.py`` is ``None`` with a ``data_note`` saying no manufacturer submittal has
been read. The engine can say that it cannot say, and name the pair and the spacing so that
somebody opening a submittal knows exactly which number to look up. Inventing a dimension to
turn this into a FAIL would be worse than the silence it replaces.

``Tier.STRUCTURAL`` and **no ``PermitItemSpec``**, the same footing as
``mep.run_interference`` and ``mep.fitting_pattern``: no IRC section states a laying length,
and a CODE tier would trip the coverage test and the ``code_ref`` requirement dishonestly.
"""

from __future__ import annotations

from typehaus.checks._authoring import passed as _pass
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.quantities import M_PER_IN

_CID = "mep.drain_inlet_spacing"

#: Two inlets further apart than this many BARREL DIAMETERS raise no question: three
#: diameters clears a full-sweep fitting body on the larger pipe, which is the same
#: convention ``run_interference.JOINT_REACH_FACTOR`` states and for the same reason — the
#: catalog records no laying length, so the reach around a fitting is a stated convention
#: rather than a dimension read off a submittal.
INLET_SCREEN_DIAMETERS = 3.0

#: A plan offset under this is "on the same vertical". A sixteenth of an inch is the grid
#: every coordinate in this repo is authored on.
SAME_BARREL_M = 0.0015875


@check(Tier.STRUCTURAL, _CID)
def drain_inlet_spacing(ctx: CheckContext) -> list[Finding]:
    """Branches landing on one vertical drain barrel, sorted by elevation.

    A barrel is a vertical segment of a drain run — a repeated plan point at two
    elevations. An inlet is another drain run's END on that plan point, within the barrel's
    own z span. Two inlets closer than :data:`INLET_SCREEN_DIAMETERS` barrel diameters are
    named with their spacing and with the datum that would settle them.
    """
    barrels = _barrels(ctx)
    if not barrels:
        return [_pass(_CID, "no drain run resolves a vertical barrel, so no two branches "
                            "can land on one", ())]

    out: list[Finding] = []
    for tag, point, z0_m, z1_m, diameter_m in barrels:
        inlets = sorted(_inlets_on(ctx, tag, point, z0_m, z1_m))
        screen = INLET_SCREEN_DIAMETERS * diameter_m
        for (low_z, low_tag), (high_z, high_tag) in zip(inlets[:-1], inlets[1:], strict=False):
            gap = high_z - low_z
            if gap > screen:
                continue
            out.append(_unknown(
                _CID,
                f"{low_tag} and {high_tag} both land on {tag}'s vertical barrel "
                f"{gap / M_PER_IN:.2f}\" apart, and whether two fittings fit that close on a "
                f"{diameter_m / M_PER_IN:.0f}\" barrel is NOT KNOWN: every center_to_face_in "
                "in library/fittings.py is None, with a data_note saying no manufacturer "
                "submittal has been read. The screen is "
                f"{INLET_SCREEN_DIAMETERS:.0f} barrel diameters "
                f"({screen / M_PER_IN:.2f}\"), a stated convention and not a dimension",
                (tag, low_tag, high_tag),
                fix="read the laying length off the two fittings' submittals and author it "
                    "as center_to_face_in in library/fittings.py — or move one branch so "
                    "the question does not arise"))

    if not out:
        out.append(_pass(_CID, f"{len(barrels)} vertical drain barrel(s) carry no two "
                               "branch inlets within a fitting's reach of each other", ()))
    return out


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
