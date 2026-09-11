"""Does every floor covering state how far it stands proud of the deck?

Everything authored "above the floor" — a receptacle at 15", a grab bar at 34", a mantel —
is measured from the plane a foot lands on, and that plane is the subfloor plus the covering
on it. ``resolve/room_floor.py::room_finished_floor_elevation`` is what builds it, and it can
only add a covering whose depth ``Material.finish_thickness_in`` states.

A resolver returns a number and has nowhere to put UNKNOWN, so an unstated covering falls
back to the structural top — the answer it gave before finishes carried a depth at all, no
worse but no longer honest about itself. This is where that is said out loud (decision #32:
a missing number propagates as UNKNOWN, it never becomes a silent zero).

ADVISORY, not code: no section requires a material catalog to publish a thickness. What it
governs is whether the AFF numbers in a room can be trusted, which is a modelling fact.
"""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, not_applicable, passed, unknown


@check(Tier.ADVISORY, "advisory.floor_finish_depth")
def floor_finish_depth(ctx: CheckContext) -> list[Finding]:
    """Every floored room's covering states a depth, or says outright it has none."""
    materials = {material.tag: material for material in ctx.plan.library.materials}
    floored = [room for room in ctx.model.rooms if room.floor_finish]
    if not floored:
        # Earned, not assumed: no room in this plan names a floor covering at all, so there
        # is no depth for anything to be missing.
        return [not_applicable("advisory.floor_finish_depth",
                               "no room names a floor covering")]
    out: list[Finding] = []
    for room in sorted(floored, key=lambda item: item.tag):
        material = materials.get(room.floor_finish)
        if material is None:
            out.append(unknown("advisory.floor_finish_depth",
                               f"{room.tag}'s floor finish '{room.floor_finish}' is in no "
                               "material catalog, so nothing states how far it stands above "
                               "the deck and every height authored in this room is measured "
                               "from the subfloor instead of the floor",
                               (room.tag,)))
        elif material.finish_thickness_in is not None:
            out.append(passed("advisory.floor_finish_depth",
                              f"{room.tag} walks on {room.floor_finish} "
                              f"{material.finish_thickness_in:g}\" above its deck",
                              (room.tag,)))
        elif material.coating:
            out.append(passed("advisory.floor_finish_depth",
                              f"{room.tag} walks on the deck itself — {room.floor_finish} "
                              "is a coating and stands no height above it",
                              (room.tag,)))
        else:
            out.append(unknown("advisory.floor_finish_depth",
                               f"{room.tag}'s {room.floor_finish} states no "
                               "finish_thickness_in and is not a coating, so every height "
                               "authored in this room resolves from the subfloor and is "
                               "short by whatever the covering is",
                               (room.tag,)))
    return out
