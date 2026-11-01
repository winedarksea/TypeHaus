"""``mep.fitting_pattern`` — every turn is a part somebody orders, and this says which.

A run's polyline turns at a vertex; what gets installed there is a fitting. Until Phase 5 of
the routing roadmap nothing in the engine could name it: the take-off snapped a measured
angle to one of three numbers and billed a row, and whether a part existed at that angle and
size was never asked. ``elbow-22.5-1in`` stood on catlin's price list for two years as a row
for a fitting **ASME B16.22 does not make**.

The reading is :mod:`typehaus.resolve.mep_fittings` — the same records the pipe take-off,
the duct take-off and the router's proposal read, so a fitting can never be priced as one
part here and drawn as another there.

**This check does not FAIL, and the reason is the point.** "No catalogued pattern turns 79
degrees at 3 inches" is a statement about ``library/fittings.py``, not about the building: a
fabricator makes off-angle turns every day, and whether *this* one is buildable depends on a
laying length no submittal in this repo publishes. So a matched turn PASSes honestly and an
unmatched one is UNKNOWN with the reason and the remedy attached — read a submittal, widen
the catalog, or look at the run. Inventing a FAIL out of a gap in our own catalog would be
the engine grading its own ignorance as the house's defect.

**Laying length.** Where a pattern defines a centreline radius (a gored round duct elbow,
1.5 D by SMACNA), its take-off ``R tan(theta/2)`` has to fit on the straight between it and
the next fitting or the run's end. A shorter leg is UNKNOWN, not FAIL: the stocked stamped
elbow is tighter than the gored pattern and no submittal publishes its radius.

``Tier.STRUCTURAL`` and **no** ``PermitItemSpec``, the same footing as
``mep.run_interference``: no IRC section says which pattern a turn must be, and a CODE tier
would trip the coverage test and the ``code_ref`` requirement dishonestly.
"""

from __future__ import annotations

import math
from collections import defaultdict

from typehaus.checks._authoring import passed as _pass
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding

_CID = "mep.fitting_pattern"

#: How many ungraded turns one finding names before it stops listing and starts counting. A
#: reader needs to know which run and roughly where, not eleven coordinates.
_MAX_LISTED = 4


@check(Tier.STRUCTURAL, _CID)
def fitting_pattern(ctx: CheckContext) -> list[Finding]:
    """One finding per run that holds a turn no catalogued pattern makes.

    Grouped by run rather than by vertex: four ungraded vertices on one drain are one
    conversation with one plumber, and four findings would be four.
    """
    from typehaus.resolve.mep_fittings import fitting_records

    records = fitting_records(ctx.model)
    if not records:
        return [_unknown(_CID, "no pipe or duct run resolves a turn, so there is no fitting "
                               "in this model to name a pattern for")]

    ungraded: dict[str, list] = defaultdict(list)
    for record in records:
        if record.spec is None:
            ungraded[record.run_tag].append(record)

    out: list[Finding] = []
    for run_tag, group in sorted(ungraded.items()):
        # The reasons are already written in report prose by ``mep_fittings._match``; one
        # run usually has one of them, and where it has two both are worth printing.
        reasons: list[str] = []
        for record in group:
            if record.gap is not None and record.gap not in reasons:
                reasons.append(record.gap)
        where = ", ".join(
            (f"vertex {record.index} ({record.angle_deg:.1f}°)" if record.index is not None
             else f"the {record.nominal_in:g}\"x{record.branch_in:g}\" branch")
            for record in group[:_MAX_LISTED])
        more = f" (+{len(group) - _MAX_LISTED} more)" if len(group) > _MAX_LISTED else ""
        out.append(_unknown(
            _CID,
            f"{run_tag} takes {len(group)} fitting(s) no catalogued pattern names — "
            f"{where}{more}. " + " ".join(reasons),
            (run_tag,),
            fix="read a manufacturer submittal into library/fittings.py, or re-draw the "
                "run so its turns land on patterns that are made — `haus route --run "
                f"{run_tag}` proposes a lane and `--evaluate` grades it"))

    out.extend(_laying_length(ctx, records))

    graded = len(records) - sum(len(group) for group in ungraded.values())
    if graded:
        out.append(_pass(
            _CID,
            f"{graded} of {len(records)} fittings name a catalogued pattern with its source "
            "(ASTM D3311 for DWV, ASME B16.22 for copper, SMACNA for round duct, the "
            "maker's minimum radius for a bent PEX tube)", ()))
    return out


def _takeoff_in(record) -> float:
    """Centre-to-tangent of a turn whose pattern defines a radius, inches; 0 otherwise."""
    radius = getattr(record.spec, "bend_radius_in", None)
    if not radius or record.bendable or record.index is None:
        return 0.0
    return radius * math.tan(math.radians(record.angle_deg) / 2.0)


def _laying_length(ctx: CheckContext, records: list) -> list[Finding]:
    """One UNKNOWN per run with a straight shorter than the take-offs at its two ends.

    A straight is measured along the cleaned path between consecutive fittings, or between
    a fitting and the run's end (a collar, port or tee, which take no take-off of their own).
    """
    from typehaus.quantities import M_PER_IN
    from typehaus.resolve.sweep import clean_path

    turns: dict[str, dict[int, object]] = defaultdict(dict)
    for record in records:
        if _takeoff_in(record) > 0.0:
            turns[record.run_tag][record.index] = record
    out: list[Finding] = []
    for run in (*ctx.model.ducts, *ctx.model.pipe_runs):
        at = turns.get(run.tag)
        z = getattr(run, "z_m", None)
        if not at or z is None or len(z) != len(run.path):
            continue
        path = clean_path([(x, y, zz) for (x, y), zz in zip(run.path, z, strict=True)])
        stops = sorted({0, len(path) - 1, *at})
        short: list[str] = []
        for a, b in zip(stops, stops[1:], strict=False):
            length = sum(math.dist(path[i], path[i + 1]) for i in range(a, b)) / M_PER_IN
            need = sum(_takeoff_in(at[i]) for i in (a, b) if i in at)
            if length + 1.0 / 16.0 < need:
                short.append(f"{length:.1f}\" between vertex {a} and {b} against "
                             f"{need:.1f}\"")
        if short:
            more = f" (+{len(short) - _MAX_LISTED} more)" if len(short) > _MAX_LISTED else ""
            out.append(_unknown(
                _CID,
                f"{run.tag}: {len(short)} straight(s) shorter than the elbow take-offs at "
                f"their ends at the catalogued centreline radius — "
                f"{'; '.join(short[:_MAX_LISTED])}{more}. No submittal gives the stocked "
                "stamped elbow's radius, so this is UNKNOWN, not a FAIL",
                (run.tag,),
                fix="lengthen the straight, or read the stocked elbow's radius into "
                    "library/fittings.py"))
    return out
