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

``Tier.STRUCTURAL`` and **no** ``PermitItemSpec``, the same footing as
``mep.run_interference``: no IRC section says which pattern a turn must be, and a CODE tier
would trip the coverage test and the ``code_ref`` requirement dishonestly.
"""

from __future__ import annotations

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

    graded = len(records) - sum(len(group) for group in ungraded.values())
    if graded:
        out.append(_pass(
            _CID,
            f"{graded} of {len(records)} fittings name a catalogued pattern with its source "
            "(ASTM D3311 for DWV, ASME B16.22 for copper, SMACNA for round duct)", ()))
    return out
