"""``integrity.door_floor_finish`` — the floor a derived RO was sized from is the one built.

Openings resolve before floors and rooms, so ``resolve/door_floor_finish`` reads the
build-up from the plan. This grades that read against the resolved walking surface at the
same probe points: a disagreement means the RO head was framed for a floor that is not
there, silently (a 3/4" short head on every joisted storey was the first one).
"""
from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, failed, not_applicable, passed
from typehaus.resolve.door_sizing import CASED_DOOR_DEFAULTS
from typehaus.resolve.geometry import wall_frame
from typehaus.resolve.walking_surface import surfaces_at

_CID = "integrity.door_floor_finish"
_IN = 0.0254
_TOLERANCE_M = _IN / 16
# Same level window as the plan read: a deck at the door, not a platform or a pad.
_BELOW_M, _ABOVE_M = 0.01, 0.10


def _resolved_build_up(ctx: CheckContext, wall, opening, base: float) -> float | None:
    """Base to the higher resolved finished floor either side; None where neither side has
    a resolved deck with a stated covering (nothing to compare)."""
    origin, tangent, normal, _ = wall_frame(wall)
    reach = wall.thickness_m / 2 + CASED_DOOR_DEFAULTS.room_probe_m
    floors = []
    for side in (-1, 1):
        point = tuple(origin[i] + tangent[i] * opening.center_along_m
                      + normal[i] * side * reach for i in (0, 1))
        tops = [s.surface_m for s in surfaces_at(ctx.model, point)
                if s.surface_m is not None
                and base - _BELOW_M <= s.deck_top_m <= base + _ABOVE_M]
        if tops:
            floors.append(max(tops))
    return max(floors) - base if floors else None


@check(Tier.INTEGRITY, _CID)
def door_floor_finish(ctx: CheckContext) -> list[Finding]:
    """A derived RO's floor build-up matches the resolved finished floor at the door."""
    derived = [o for o in ctx.model.openings
               if o.sizing is not None and not o.sizing.held
               and o.sill_m <= CASED_DOOR_DEFAULTS.raised_sill_m
               and o.sizing.required_basis.startswith(("derived", "pocket"))]
    if not derived:
        return [not_applicable(_CID, "no door derives its RO from the floor it stands on")]
    out: list[Finding] = []
    for opening in derived:
        sizing = opening.sizing
        wall = ctx.model.wall(opening.host_wall)
        if wall is None:
            continue
        base = wall.base_ref_z_m + opening.sill_m
        resolved = _resolved_build_up(ctx, wall, opening, base)
        if resolved is None:
            continue
        planned = sizing.floor_finish_m
        text = (f'{opening.tag}: RO sized for {planned / _IN:.3f}" of floor over its base, '
                f'the resolved finished floor is {resolved / _IN:.3f}"')
        if abs(planned - resolved) > _TOLERANCE_M:
            out.append(failed(_CID, text, (opening.tag,),
                              fix="resolve/door_floor_finish misread the deck or covering "
                                  "here; the RO head and clear height are off by the gap"))
        else:
            out.append(passed(_CID, text, (opening.tag,)))
    return out
