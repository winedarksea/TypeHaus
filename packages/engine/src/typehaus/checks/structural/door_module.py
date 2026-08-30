"""``structural.door_framing_module`` — doors against their host wall's stud grid.

``window_module.py`` has skipped every door since it was written (``if opening.is_door: continue``),
and the reason it must go on skipping them is the whole argument for a second file rather than
one shared loop:

**``_ro_caps`` must not apply to a door.** That ladder caps a rough opening's WIDTH — one clear
bay, two bays less the broken stud, that again less a jack each side — because a window that
wide breaks more than one stud line and wants a wider header than the prescriptive table gives.
A door is chosen by what has to pass through it. Run catlin's doors through the ladder and it
reports ``D-M-PANTRY`` (60" bypass), ``D-B-PLAY``, ``D-B-PATIO`` and ``D-G-OVERHEAD`` (192",
with a named engineered header) as exceeding a 30" limit: four FAILs the house must not act on,
because narrowing a garage door to fit a stud module is not a thing anyone does.

So this grades **position only**, and it grades it on one criterion: does the opening interrupt
more stud lines than an opening its width has to. ``opening_stud_module`` gives both numbers,
and when they are equal the door is already in the best bay configuration there is — being off
the "ideal" centre by an inch costs nothing then, and reporting it would be noise. That is
narrower than the window check's test (which also fires on ``offset_from_ideal``), deliberately:
a window's position is a facade decision with a right answer, and a door's is a circulation
decision with a budget.

The tier is STRUCTURAL and the severity WARN — advisory, matching the window check. **Not
CODE**: no IRC section requires an opening to land on a stud module, so there is no citation to
hang a ``PermitItemSpec`` on and nothing for ``tests/test_permit_coverage.py`` to demand.

Tri-state, and the third state is what makes it usable:

* a legal station exists   -> **FAIL**, naming the nearest one in inches along the wall.
* none does                -> **UNKNOWN**, saying so and naming the three remedies.

The second case is not a technicality. Six catlin openings are in it — ``D-M-ENTRY`` (36" in a
48" wall), ``D-M-PANTRY``, ``D-S-BATH1``, ``D-S-BED3``, ``D-S-NCLOSET``, ``D-S-STUDY2`` — and
for every one of them the answer "shift the RO" is wrong. The wall is too short to hold that
leaf on the module with a jamb pack at each end, and the fix is the start node, the layout
origin, or a narrower leaf. A check that said FAIL there would be sending somebody to look for
a position that does not exist.
"""

from __future__ import annotations

from typehaus.checks._authoring import structural_advisory as _advisory
from typehaus.checks._authoring import unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.checks.structural._stud_grid import (
    feasible_stations,
    module_origin,
    nearest_station,
    segment_residue_in,
    structure_framing,
    wall_module,
)
from typehaus.findings import Finding, Result

_IN_M = 0.0254
_CID = "structural.door_framing_module"


@check(Tier.STRUCTURAL, _CID)
def door_framing_module(ctx: CheckContext) -> list[Finding]:
    """Keep doors on their host wall's framing module, or say why one cannot be."""
    from typehaus.resolve.framing.stud_module import opening_stud_module
    from typehaus.resolve.framing.tables import member_actual
    from typehaus.resolve.geometry import length, sub

    rules = ctx.preferences.framing
    out: list[Finding] = []
    for opening in ctx.model.openings:
        # ``type_ref is None`` catches a bare RoughOpening — a cased opening with no leaf,
        # which frames exactly like a door and which the window check also skips.
        if not (opening.is_door or opening.type_ref is None):
            continue
        wall = ctx.model.wall(opening.host_wall)
        if wall is None:
            continue
        framing = structure_framing(ctx.plan.library.resolve_assembly(wall.assembly))
        if framing is None:
            continue  # concrete / masonry openings consume no stud bays
        module_in = wall_module(framing, rules.module_in)
        spacing = module_in * _IN_M
        stud_m = member_actual(framing.member)[0] * _IN_M
        phase, origin = module_origin(ctx, wall, framing, spacing)
        module = opening_stud_module(opening.center_along_m, opening.width_m, spacing,
                                     stud_m, phase)
        # The one criterion — see the module note. Equal counts means the opening is already
        # in the cheapest bay configuration its width allows, whatever its offset reads.
        if module.interrupted <= module.minimum_interrupted:
            continue
        axis_len = length(sub(wall.axis[1], wall.axis[0]))
        stations = feasible_stations(opening.width_m, axis_len, spacing, stud_m, phase)
        station = nearest_station(stations, opening.center_along_m)
        centre_in = opening.center_along_m / _IN_M
        cost = module.interrupted - module.minimum_interrupted
        if origin == "segment":
            residue = segment_residue_in(wall, module_in)
            where = (f"{wall.tag} lays out from a {residue:.1f}\" residue mod "
                     f"{module_in:.0f}\", so its legal centres are {residue:.1f}\" + "
                     f"n×{module_in:.0f}\"")
        else:
            where = (f"{wall.tag} lays out from layout line {origin} and reaches the module "
                     f"{phase / _IN_M:.1f}\" along itself")
        if station is None:
            out.append(unknown(
                _CID,
                f"door {opening.tag} is off {wall.tag}'s stud module and cuts {cost} stud(s) "
                f"more than it needs to, and NO position on this wall fixes it: at "
                f"{opening.width_m / _IN_M:.0f}\" wide in a {axis_len / _IN_M:.0f}\" wall "
                f"there is no station that both lands on the module and leaves a jamb pack "
                f"clear of each end. {where}",
                (opening.tag, wall.tag),
                fix=("this one is not a move. Either re-phase the grid — swap the wall's "
                     "start/end nodes, or give its assembly `layout_origin=\"line\"` so it "
                     "takes its layout line's phase instead of its own start node — or move "
                     "the start NODE, or fit a narrower leaf. Moving the opening cannot help"),
            ))
            continue
        delta = (station - opening.center_along_m) / _IN_M
        out.append(_advisory(
            _CID,
            f"door {opening.tag} is {abs(delta):.1f}\" off {wall.tag}'s stud module and cuts "
            f"{module.interrupted} stud(s) where {module.minimum_interrupted} would do; "
            f"{where}",
            (opening.tag, wall.tag), Result.FAIL,
            fix_hint=(f"move its centre {delta:+.1f}\" to {station / _IN_M:.0f}\" along the "
                      f"wall — that is a legal station, and the nearest one. Remember the "
                      f"`from_node` offset is to the opening's near EDGE, so it becomes "
                      f"{(station - opening.width_m / 2) / _IN_M:.2f}\" (centre {centre_in:.1f}"
                      f"\" -> {station / _IN_M:.1f}\")"),
        ))
    return out
