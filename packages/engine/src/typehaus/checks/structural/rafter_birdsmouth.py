"""``structural.ijoist_birdsmouth`` — an I-joist rafter's eave seat is TJ-4000's low-end cut.

TJ-4000 (Jul 2025) p.31 R5 and APA D710A 10h permit a birdsmouth at the LOW end only, the
flange bearing fully on the plate, the cut not past the plate's inside face, beveled web
stiffeners both sides; p.32 sets 1 3/4" of bearing. Graded per roof, worst rafter named,
off the resolved solids (``_rafter_seat.ijoist_seat``). Sawn rafters are R802.7.1's, in
``member_interference``.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed, not_applicable, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.checks.structural._rafter_seat import IJOIST_SEAT_CODE_REF, ijoist_seat
from typehaus.findings import Finding
from typehaus.resolve.framing.profiles import cross_section

_CID = "structural.ijoist_birdsmouth"
_IN = 0.0254


@check(Tier.STRUCTURAL, _CID)
def ijoist_birdsmouth(ctx: CheckContext) -> list[Finding]:
    out: list[Finding] = []
    for roof in ctx.model.roofs:
        rafters = [m for m in roof.members if m.category == "rafter"
                   and cross_section(m.profile).shape == "i_joist"]
        if not rafters:
            continue
        keys = {m.child_key for m in roof.members if m.category == "bearing_stiffener"}
        unseated = [m.child_key for m in rafters if m.seat is None]
        if unseated:
            out.append(unknown(_CID, f"{roof.tag}: {len(unseated)} I-joist rafter(s) resolve "
                                     f"no eave seat (first {unseated[0]})", (roof.tag,),
                               code=IJOIST_SEAT_CODE_REF))
        graded = [(m, s) for m in rafters if m.seat is not None and (s := ijoist_seat(
            m, f"{m.child_key}-eave-stiffener" in keys)) is not None]
        if not graded:
            continue
        bad = [(m, s) for m, s in graded if s.problems]
        if bad:
            member, seat = bad[0]
            out.append(failed(_CID, f"{roof.tag}: {len(bad)} of {len(graded)} birdsmouths "
                                    f"fail; {member.child_key} has "
                                    f"{'; '.join(seat.problems)}", (roof.tag, member.child_key),
                              code=IJOIST_SEAT_CODE_REF,
                              fix="re-seat at the low end on a 1 3/4\"-to-flange-depth seat, "
                                  "or bear on a beveled plate (TJ-4000 p.32)"))
            continue
        worst = max(graded, key=lambda item: item[1].notch_m)[1]
        out.append(passed(_CID, f"{roof.tag}: {len(graded)} low-end birdsmouths, worst cut "
                                f"{worst.notch_m / _IN:.2f}\" of a {worst.flange_plumb_m / _IN:.2f}\""
                                f" flange, seat {worst.seat_m / _IN:.2f}\" on a "
                                f"{(worst.bearing_run_m or 0.0) / _IN:.2f}\" plate, stiffened",
                          (roof.tag,), code=IJOIST_SEAT_CODE_REF))
    if not out:
        return [not_applicable(_CID, "no roof in this model is framed with I-joist rafters",
                               (), code=IJOIST_SEAT_CODE_REF)]
    return out
