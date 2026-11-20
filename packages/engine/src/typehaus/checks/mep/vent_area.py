"""``mep.vent_aggregate_area`` — UPC 904.1, adopted unamended by MN 4714.0050.

The vents open to atmosphere must total at least the cross-sectional area of the largest
REQUIRED building sewer (Table 703.2 sized on the building drain's DFU, not the pipe as
drawn). Nominal diameters, π/4·d², each VENT system taken at its terminal size. A radon
leg is a separate system and never counts. Oracle: ``houses/catlin/notes/vent_aggregate_area.md``.
"""

from __future__ import annotations

import math

from typehaus.checks._authoring import failed as _fail
from typehaus.checks._authoring import not_applicable as _na
from typehaus.checks._authoring import passed as _pass
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding

_CID = "mep.vent_aggregate_area"
_REF = "UPC 904.1 (MN 4714.0050)"
_CODE = "MN Plumbing Code (ch. 4714) 904.1"


def building_drains(ctx: CheckContext) -> list[str]:
    """Drain runs threading a horizontal drain exit sleeve — the run that leaves the
    building, matched exactly as ``mep.sewer_exit_invert`` matches it."""
    from typehaus.checks.mep.plumbing_concrete import _under_footing_crossing
    from typehaus.resolve.mep import concrete_crossings

    crossings = {c["sleeve"]: c["run"] for c in concrete_crossings(ctx.model)
                 if c["sleeve"] is not None and c["system"] == "drain"}
    out = []
    for sleeve in ctx.model.sleeves:
        if sleeve.axis != "horizontal" or sleeve.purpose != "drain":
            continue
        run = crossings.get(sleeve.tag)
        if run is None:
            under = _under_footing_crossing(ctx, sleeve)
            run = under["run"] if under is not None else None
        if run is not None and run not in out:
            out.append(run)
    return out


def terminal_vents(ctx: CheckContext) -> list[tuple[str, float]]:
    """``(tag, nominal terminal diameter in)`` per VENT system open to atmosphere."""
    from typehaus.model.enums import PipeSystem
    from typehaus.model.mep import VentRun
    from typehaus.resolve.vent_termination import riser_polylines

    return [(e.tag, e.diameter_of(PipeSystem.VENT).inches)
            for e in ctx.plan.all_elements()
            if isinstance(e, VentRun) and PipeSystem.VENT in e.systems
            and riser_polylines(ctx.model, e)]


@check(Tier.CODE, _CID)
def vent_aggregate_area(ctx: CheckContext) -> list[Finding]:
    from typehaus.resolve.mep import accumulated_serves
    from typehaus.takeoff.plumbing_calc import (
        branch_load,
        fixture_units,
        required_drain_diameter_in,
    )

    drains = [r for r in ctx.model.pipe_runs if r.system == "drain"]
    units = {row.tag: row for row in fixture_units(ctx.plan)}
    if not drains and not any(row.dfu for row in units.values()):
        return [_na(_CID, f"no drain run and no fixture with a drainage load: there is "
                          f"no building drain for {_REF} to vent", (), _CODE)]
    exits = building_drains(ctx)
    if not exits:
        return [_unknown(_CID, "no drain run threads a drain exit sleeve, so the building "
                               f"drain and its required sewer size ({_REF}) are unknown",
                         (), _CODE)]
    rolled = accumulated_serves(ctx.model.pipe_runs)
    need_in, need_dfu, governing = 0.0, 0.0, exits[0]
    for tag in exits:
        serves = rolled.get(tag, ())
        load, unresolved = branch_load(serves, units, "drain")
        if load is None:
            return [_unknown(_CID, f"building drain {tag} serves {', '.join(unresolved)}, "
                                   "which carry no DFU row; its required sewer size "
                                   f"({_REF}) cannot be found", (tag,), _CODE)]
        symbols = [units[t].symbol for t in serves if t in units]
        required = required_drain_diameter_in(load, symbols)
        if required is None:
            return [_unknown(_CID, f"building drain {tag} carries {load:g} DFU, beyond "
                                   f"Table 703.2; the {_REF} sewer size needs engineering",
                             (tag,), _CODE)]
        if required > need_in:
            need_in, governing, need_dfu = required, tag, load
    vents = terminal_vents(ctx)
    need = math.pi / 4 * need_in ** 2
    have = sum(math.pi / 4 * d ** 2 for _tag, d in vents)
    tags = (governing, *(t for t, _d in vents))
    listed = ", ".join(f"{t} {d:g}\"" for t, d in vents) or "no vent open to atmosphere"
    msg = (f"vents open to atmosphere ({listed}) total {have:.2f} in² against the "
           f"{need_in:g}\" required building sewer's {need:.2f} in² ({governing}, "
           f"{need_dfu:g} DFU; {_REF})")
    if have + 1e-6 >= need:
        return [_pass(_CID, msg, tags, _CODE)]
    return [_fail(_CID, msg, tags, _CODE)]

