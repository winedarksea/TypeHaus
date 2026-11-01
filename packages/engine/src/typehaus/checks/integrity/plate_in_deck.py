"""A bottom plate stands ON its deck, never inside it (decision #110).

Nothing else notices. ``structural.member_interference`` compares members with members, and a
subfloor sheet or a slab is not a member, so a main-floor plate resolved at the joist top sat
3/4" deep in the plywood and 15/16" deep in ``SL-M-DECK``'s cap with every check green. Read
off the RESOLVED plates and decks — the subfloor sheets less their voids, the slab solids
less theirs — so it grades what was framed and poured, not ``plate_seat``'s own arithmetic.
"""

from __future__ import annotations

from shapely.geometry import Polygon

from typehaus.checks._authoring import failed
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, not_applicable, passed
from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.overlay import union_all
from typehaus.resolve.solid_categories import in_slab_family

_CHECK_ID = "integrity.plate_in_deck"
_TOL_M = 1e-4
_MIN_AREA_M2 = 1e-4
#: A deck authored to the axis of the line it dies into covers half the plate and stops at
#: it (catlin's ``W-BW-SCREEN`` at the breezeway deck's edge); past this the plate bears in it.
_MIN_COVER = 0.6
_IN = 0.0254


def _sheet(ring, voids) -> Polygon | None:
    if len(ring) < 3:
        return None
    shape = Polygon(ring)
    shape = shape if shape.is_valid else shape.buffer(0)
    for void in voids:
        if len(void) >= 3:
            shape = shape.difference(Polygon(void).buffer(0))
    return shape


def _decks(ctx: CheckContext) -> list[tuple[str, Polygon, float, float]]:
    """``(tag, plan shape, bottom, top)`` for every subfloor sheet and slab solid."""
    out = []
    for floor in ctx.model.floors:
        shape = _sheet(floor.deck_outline, floor.deck_voids)
        if shape is not None and floor.deck_z1_m > floor.deck_z0_m and floor.deck_plane is None:
            out.append((floor.tag, shape, floor.deck_z0_m, floor.deck_z1_m))
    for solid in ctx.model.solids:
        if not in_slab_family(solid.category) or solid.sweep is not None:
            continue
        shape = _sheet(solid.outline, solid.voids)
        if shape is not None:
            out.append((solid.tag, shape, solid.z0_m, solid.z1_m))
    return out


@check(Tier.INTEGRITY, _CHECK_ID)
def plate_in_deck(ctx: CheckContext) -> list[Finding]:
    decks = _decks(ctx)
    out: list[Finding] = []
    graded = 0
    for wall in ctx.model.walls:
        for member in wall.members:
            if not member.child_key.startswith("plate-bottom"):
                continue
            graded += 1
            ring, z_lo, z_hi = member_footprint(member)
            plate = Polygon(ring)
            hits = [(tag, top, part) for tag, shape, bottom, top in decks
                    if z_lo < top - _TOL_M and z_hi > bottom + _TOL_M
                    and (part := plate.intersection(shape)).area > _MIN_AREA_M2]
            if not hits or union_all([part for _, _, part in hits]).area \
                    < _MIN_COVER * plate.area:
                continue
            tag, top, _ = max(hits, key=lambda hit: hit[1])
            out.append(failed(
                _CHECK_ID,
                f"{wall.tag}'s {member.child_key} bottom is {(top - z_lo) / _IN:.3f}\" "
                f"below the top of {tag} ({top / _IN:+.4f}\"): the plate sits inside the "
                f"deck it should stand on",
                (wall.tag, *sorted({hit[0] for hit in hits})),
                fix=("stand the wall on the deck: a platform wall's frame base is its "
                     "subfloor top (resolve/plate_seat.py)")))
    if not graded:
        return [not_applicable(_CHECK_ID, "no framed wall has a bottom plate")]
    if not out:
        out.append(passed(_CHECK_ID, f"{graded} bottom plate(s) stand on, not in, every deck "
                                     f"and slab under them"))
    return out
