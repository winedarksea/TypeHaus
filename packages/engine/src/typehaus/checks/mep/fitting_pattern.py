"""``mep.fitting_pattern`` — every turn is a part somebody orders, and this says which.

A run's polyline turns at a vertex; what gets installed there is a fitting. Until Phase 5 of
the routing roadmap nothing in the engine could name it: the take-off snapped a measured
angle to one of three numbers and billed a row, and whether a part existed at that angle and
size was never asked. ``elbow-22.5-1in`` stood on catlin's price list for two years as a row
for a fitting **ASME B16.22 does not make**.

The reading is :mod:`typehaus.resolve.mep_fittings` — the same records the pipe take-off,
the duct take-off and the router's proposal read, so a fitting can never be priced as one
part here and drawn as another there.

**A pattern gap does not FAIL, and the reason is the point.** "No catalogued pattern turns 79
degrees at 3 inches" is a statement about ``library/fittings.py``, not about the building: a
fabricator makes off-angle turns every day, and whether *this* one is buildable depends on a
laying length no submittal in this repo publishes. So a matched turn PASSes honestly and an
unmatched one is UNKNOWN with the reason and the remedy attached — read a submittal, widen
the catalog, or look at the run. Inventing a FAIL out of a gap in our own catalog would be
the engine grading its own ignorance as the house's defect.

**Laying length.** Where a pattern defines a centreline radius (a gored round duct elbow,
1.5 D by SMACNA, or the house's bought duct elbow, decision #114), its take-off
``R tan(theta/2)`` has to fit on the straight between it and the next fitting or the run's
end. Shorter is UNKNOWN; shorter than two elbows at R = D/2, the tightest throat made, FAIL.

``Tier.STRUCTURAL`` and **no** ``PermitItemSpec``, the same footing as
``mep.run_interference``: no IRC section says which pattern a turn must be, and a CODE tier
would trip the coverage test and the ``code_ref`` requirement dishonestly.
"""

from __future__ import annotations

import math
from collections import defaultdict

from typehaus.checks._authoring import failed
from typehaus.checks._authoring import passed as _pass
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.quantities import M_PER_IN
from typehaus.resolve.duct_standard import elbow_for_turn
from typehaus.resolve.mep_fittings import FAMILY_DUCT, RECTANGULAR_DUCT_GAP

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


def _takeoff_in(record, elbows: dict) -> float:
    """Centre-to-tangent of a turn, inches: the house's bought duct elbow where the
    ``DuctStandard`` reads its centre-to-face (#114, M4-107), else the pattern's radius; 0
    where neither defines one. ``R tan(theta/2)`` with R the 90-degree centre-to-face."""
    if record.bendable or record.index is None:
        return 0.0
    row = None
    if record.family == FAMILY_DUCT and elbows and record.gap != RECTANGULAR_DUCT_GAP:
        hit = elbow_for_turn(elbows["standard"], record.nominal_in * M_PER_IN,
                             record.angle_deg)
        row = hit[0] if hit is not None else None
    radius = (row.center_to_face.meters / M_PER_IN if row is not None and row.center_to_face
              else getattr(record.spec, "bend_radius_in", None))
    return radius * math.tan(math.radians(record.angle_deg) / 2.0) if radius else 0.0


def _floor_in(record) -> float:
    """The take-off at R = D/2, the tightest throat any round duct elbow has (M4-101)."""
    if record.family != FAMILY_DUCT or record.index is None or record.spec is None:
        return 0.0
    return record.nominal_in / 2.0 * math.tan(math.radians(record.angle_deg) / 2.0)


def _laying_length(ctx: CheckContext, records: list) -> list[Finding]:
    """Per run, a straight shorter than the take-offs at its two ends.

    Measured along the cleaned path between consecutive fittings, or a fitting and the
    run's end (a collar, port or tee, which take no take-off of their own). Shorter than the
    R = D/2 floor is a FAIL — no elbow is made that tight. Shorter than the bought elbow
    (or, unread, the 1.5 D pattern) is UNKNOWN: the installer cuts it to fit or it does not.
    """
    from typehaus.resolve.duct_standard import duct_standard
    from typehaus.resolve.sweep import clean_path

    standard, _ = duct_standard(getattr(ctx, "plan", None))
    elbows = {"standard": standard} if standard is not None else {}
    turns: dict[str, dict[int, object]] = defaultdict(dict)
    for record in records:
        if _takeoff_in(record, elbows) > 0.0:
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
        impossible: list[str] = []
        for a, b in zip(stops, stops[1:], strict=False):
            length = sum(math.dist(path[i], path[i + 1]) for i in range(a, b)) / M_PER_IN
            need = sum(_takeoff_in(at[i], elbows) for i in (a, b) if i in at)
            floor = sum(_floor_in(at[i]) for i in (a, b) if i in at)
            text = f"{length:.1f}\" between vertex {a} and {b}"
            if length + 1.0 / 16.0 < floor:
                impossible.append(f"{text} against {floor:.1f}\" at R = D/2")
            elif length + 1.0 / 16.0 < need:
                short.append(f"{text} against {need:.1f}\"")
        if impossible:
            out.append(failed(
                _CID, f"{run.tag}: {_listed(impossible)} — shorter than two elbows at the "
                      "tightest radius any is made, so the run cannot be built as drawn",
                (run.tag,), fix="lengthen the straight or drop a turn"))
        if short:
            source = ("the house's bought elbow" if run.tag in _with_row(run, elbows)
                      else "the catalogued 1.5 D radius")
            out.append(_unknown(
                _CID, f"{run.tag}: {len(short)} straight(s) shorter than the elbow take-offs "
                      f"at their ends at {source} — {_listed(short)}",
                (run.tag,),
                fix="lengthen the straight, or read the elbow's centre-to-face into the "
                    "house's DuctStandard"))
    return out


def _with_row(run, elbows: dict) -> set[str]:
    size = getattr(run, "diameter_m", None)
    rows = elbows["standard"].elbows if elbows else ()
    return {run.tag} if size and any(abs(r.diameter.meters - size) < 1e-4
                                     for r in rows) else set()


def _listed(items: list[str]) -> str:
    more = f" (+{len(items) - _MAX_LISTED} more)" if len(items) > _MAX_LISTED else ""
    return "; ".join(items[:_MAX_LISTED]) + more
