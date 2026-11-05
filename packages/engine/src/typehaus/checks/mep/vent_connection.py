"""``mep.vent_connection`` — where a fixture's vent leaves its drain, and how it climbs.

Graded at each vent run's end that meets a drain in 3D (``resolve/mep_trap_arm._project``
within the drain's bore plus ``TEE_TOL_M``); a branch vent tying into another vent is not a
vent connection and is not graded here. Four rules, MN 4714 (UPC):

1. **905.2** — the vent connects above the drain's centreline: its end is not below it, and
   its first leg rises at 45 degrees or steeper. A level first leg is a side inlet.
2. **MN 905.3** — it rises vertically to 6" over the flood rim before any offset flatter
   than 45 degrees. The rim is the type's declared ``flood_rim_height``, else the served
   fixture body's top (``fixture_rim_m``), which no rim exceeds.
3. **905.5 / 1002.4** — the vent opening is not below the trap weir: the tee stands no more
   than one arm diameter under it (a bigger fall before the vent is an S-trap). The model
   has no trap, so the weir is ``trap_weir_m``'s: the drain point, a floor outlet's trap 3"
   under a framed floor, or the foot of its drop on a slab. Water closets are
   exempt: they trap in the bowl, and the closet bend is not an arm.
4. **MN 1002.2** — weir to the vent's inner edge, never under twice the arm's diameter. The
   model has no trap, so this measures the drain point to the tee's centreline, no weir
   offset; an advisory sub-finding, and only where an arm is authored at all — a wall-outlet
   lavatory's stub-out IS its tee, and its arm is inside the trap kit.

ADVISORY until every catlin vent passes. ``houses/catlin/notes/vent_grade_basis.md`` §6
works PR-M-LSINK-VENT by hand.
"""

from __future__ import annotations

import math

from typehaus.checks._authoring import passed as _pass
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, advisory, not_applicable
from typehaus.quantities import M_PER_IN

_CID = "mep.vent_connection"
_OVER_RIM_M = 6 * M_PER_IN
_TOL_M = 1 / 16 * M_PER_IN


def _flat(a, b) -> bool:
    """Flatter than 45 degrees: more plan run than rise."""
    return abs(b[2] - a[2]) < math.dist(a[:2], b[:2]) - 1e-9


@check(Tier.ADVISORY, _CID)
def vent_connection(ctx: CheckContext) -> list[Finding]:
    """Each vent's connection to its drain against UPC 905.2, MN 905.3, 905.5 and 1002.2."""
    from typehaus.model.enums import Service
    from typehaus.resolve.mep_sleeves import _expected_drain_point, expected_port_point
    from typehaus.resolve.mep_trap_arm import (
        TEE_TOL_M,
        _project,
        arm_leaves,
        developed_arm,
        fixture_rim_m,
        run_points,
        trap_weir_m,
        wet_vent_data,
    )

    model = ctx.model
    vents = [(r, pts) for r in model.pipe_runs
             if r.system == "vent" and (pts := run_points(r)) is not None and len(pts) > 1]
    if not vents:
        return [not_applicable(_CID, "the house has no vent run")]
    data = wet_vent_data(model)
    symbol = {fx: row[2] for fx, row in data.fx.items()}
    datum = {}
    for storey in ctx.plan.storeys:
        for element in ctx.plan.storey_elements(storey.tag):
            datum[element.tag] = storey.elevation.meters
    out: list[Finding] = []
    for run, pts in vents:
        for seq in (pts, pts[::-1]):
            tee = _tee(seq[0], data, _project, TEE_TOL_M)
            if tee is None:
                continue
            drain, z_centre = tee
            fixtures = [f for f in run.serves if f in data.fx
                        and any(f in r.serves for r in model.pipe_runs if r.tag == drain)]
            fixtures = fixtures or [f for f in run.serves if f in data.fx]
            tags = (run.tag, drain, *fixtures)
            bad: list[str] = []
            if seq[0][2] < z_centre - _TOL_M or _flat(seq[0], seq[1]):
                bad.append("905.2: it leaves " + (
                    f'{(z_centre - seq[0][2]) / M_PER_IN:.2f}" under the drain\'s centreline'
                    if seq[0][2] < z_centre - _TOL_M else "on a level first leg (a side inlet)"))
            rims = [(r, f) for f in fixtures if (r := fixture_rim_m(model, f)) is not None]
            offset = next((a for a, b in zip(seq, seq[1:], strict=False) if _flat(a, b)), None)
            if rims and offset is not None:
                rim, rim_fx = max(rims)
                if offset[2] < rim + _OVER_RIM_M - _TOL_M:
                    bad.append(f"MN 905.3: it offsets at {offset[2] / M_PER_IN:.1f}\", "
                               f"{(rim + _OVER_RIM_M - offset[2]) / M_PER_IN:.1f}\" under "
                               f"6\" over {rim_fx}'s rim")
            notes = []
            for fx in fixtures:
                if symbol.get(fx, "").startswith("toilet"):
                    continue
                leaf = data.fx[fx][0]
                arm_d = 2.0 * data.radii[leaf]
                port = expected_port_point(model, fx, Service.DRAIN)
                weir = trap_weir_m(model, fx, datum.get(fx, 0.0), port, data.drains[leaf])
                if seq[0][2] < weir - arm_d - _TOL_M:
                    bad.append(f"905.5/1002.4: the tee is {(weir - seq[0][2]) / M_PER_IN:.2f}\" "
                               f"under {fx}'s trap weir, over the arm's "
                               f"{arm_d / M_PER_IN:g}\" (an S-trap)")
                point = _expected_drain_point(model, fx)
                serving = [r for r in model.pipe_runs if r.system == "drain"
                           and fx in r.serves and r.tag in data.drains]
                if point is None or not serving:
                    continue
                start = arm_leaves(serving, point, data.drains, data.radii)[0][1].tag
                arm_m = developed_arm(start, data.drains, data.radii, [seq[0]])[0]
                if arm_m is not None and _TOL_M < arm_m < 2.0 * arm_d - 1e-6:
                    notes.append(f"MN 1002.2: {fx}'s arm develops {arm_m / M_PER_IN:.1f}\" "
                                 f"drain point to tee centreline, under twice its "
                                 f"{arm_d / M_PER_IN:g}\" (a trap that may self-siphon)")
            said = f"vent {run.tag} on {drain}"
            if bad:
                out.append(advisory(_CID, f"{said}: " + "; ".join(bad), tags, Result.ADVISORY))
            else:
                out.append(_pass(_CID, f"{said} leaves above its centreline, rises plumb to "
                                       "6\" over the rim, and stands within an arm diameter "
                                       "of the weir", tags))
            out += [advisory(_CID, f"{said}: {n}", tags, Result.ADVISORY) for n in notes]
            break
    return out


def _tee(end, data, project, tol: float) -> tuple[str, float] | None:
    """``(drain, its centreline z under the end)`` where this vent end meets a drain."""
    best = None
    for tag, dpts in data.drains.items():
        for a, b in zip(dpts, dpts[1:], strict=False):
            d, t = project(end, a, b)
            if d <= data.radii[tag] + tol and (best is None or d < best[0]):
                best = (d, tag, a[2] + t * (b[2] - a[2]))
    return None if best is None else (best[1], best[2])
