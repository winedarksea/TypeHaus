"""The platform stud stack, printed for the framer (decision #110; A-301 and S-101).

A wall stands on the subfloor and a bearing wall's double top plate meets the joist soffit
over it, so the precut is whatever closes ``seat + sole + stud + top plates`` — a number the
crew cuts, not the 9'-0" nominal. Read off the resolved members, never restated.
"""

from __future__ import annotations

from collections import Counter

from typehaus.emit.draw.plan_labels import inches_fraction
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel, ResolvedWall
from typehaus.resolve.partition import bearing_ref_tags, takes_a_deflection_gap
from typehaus.resolve.partition_top import deck_underside_over


def _stack(wall: ResolvedWall) -> tuple[float, float, float, float] | None:
    """``(sole, stud, top plates, plate top)`` in inches for a flat-topped seated wall."""
    if wall.plate_seat_z_m is None or wall.top_z0_m is not None or wall.plate_top_z_m is None:
        return None
    studs = Counter(round((m.z1_m - m.z0_m) / M_PER_IN, 4) for m in wall.members
                    if m.child_key.startswith("stud-"))
    soles = [m for m in wall.members if m.child_key.startswith("plate-bottom")]
    if not studs or not soles:
        return None
    sole = (soles[0].z1_m - soles[0].z0_m) / M_PER_IN
    stud = studs.most_common(1)[0][0]
    top = wall.plate_top_z_m / M_PER_IN
    return sole, stud, top - wall.frame_base_z_m / M_PER_IN - sole - stud, top


def stud_stack_notes(model: ResolvedModel, storey_tags: tuple[str, ...] | None = None,
                     ) -> tuple[str, ...]:
    """One line per platform storey whose walls stand on a deck: the bearing and partition
    precuts and the stack that closes them."""
    bearing_refs = bearing_ref_tags(model.plan)
    lines: list[str] = []
    for storey in sorted(model.plan.storeys, key=lambda s: s.elevation.meters):
        if storey_tags is not None and storey.tag not in storey_tags:
            continue
        walls = [w for w in model.walls if w.storey == storey.tag and w.plate_seat_z_m is not None]
        if not walls:
            continue
        datum = storey.elevation.meters / M_PER_IN
        seat = Counter(round(w.frame_base_z_m / M_PER_IN - datum, 4) for w in walls)
        seat_in = seat.most_common(1)[0][0]
        parts = [f"{storey.tag.upper()} WALLS STAND ON THE SUBFLOOR, BOTTOM PLATE "
                 f"+{inches_fraction(seat_in)} OVER THE TOP OF JOISTS"]
        bearing = Counter(s for w in walls
                          if not takes_a_deflection_gap(model, w, bearing_refs)
                          and (s := _stack(w)) is not None)
        if bearing:
            sole, stud, plates, top = bearing.most_common(1)[0][0]
            parts.append(f"BEARING STUDS {inches_fraction(stud)}: {inches_fraction(seat_in)}"
                         f" + {inches_fraction(sole)} SOLE + {inches_fraction(stud)} + "
                         f"{inches_fraction(plates)} DOUBLE TOP = {inches_fraction(top - datum)}"
                         f" TO THE JOIST SOFFIT")
        gapped = [w for w in walls if takes_a_deflection_gap(model, w, bearing_refs)]
        partition = Counter(s for w in gapped if (s := _stack(w)) is not None)
        if partition:
            _sole, stud, _plates, top = partition.most_common(1)[0][0]
            soffits = [z for w in gapped if (z := deck_underside_over(model, w)) is not None]
            gap = f", {inches_fraction(min(soffits) / M_PER_IN - top)} UNDER THE STRUCTURE " \
                  f"(SDPW DEFLECTOR)" if soffits else ""
            parts.append(f"PARTITION STUDS {inches_fraction(stud)}{gap}")
        lines.append("; ".join(parts) + ".")
    return tuple(lines)
