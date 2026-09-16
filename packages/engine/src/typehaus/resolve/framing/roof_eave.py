"""Solid eave blocking between rafters at a plumb-cut eave (``Roof.eave_blocking``).

One block per rafter bay, on each side that has a plumb cut: it stands on the plate, its outer
face on the cut plane (tight to the sheathing) and its thickness inboard, and it runs between
the two rafters' flange faces. It is laid on edge and only as deep as its profile, so on a deep
I-joist it fills the lower part of the bay and the foam fills over it.
"""

from __future__ import annotations

from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import FramedMember, ResolvedRoof

EAVE_BLOCKING_CONNECTION = "eave:blocking"
_ON_CUT_TOL_M = 1e-4


def eave_blocking(
    roof: ResolvedRoof,
    profile: str | None,
    rafters: tuple[FramedMember, ...],
    cuts: tuple[float | None, float | None],
    plate_top_z_m: float | None,
) -> tuple[FramedMember, ...]:
    """Blocks for every bay between adjacent rafters whose tails land on a plumb cut."""
    if profile is None or plate_top_z_m is None or len(rafters) < 2:
        return ()
    block = cross_section(profile)
    span_ax = 1 if roof.ridge_direction == "x" else 0
    ridge_ax = 1 - span_ax
    members: list[FramedMember] = []
    for side, cut, inboard in (("lo", cuts[0], 1.0), ("hi", cuts[1], -1.0)):
        if cut is None:
            continue
        on_cut = sorted((r for r in rafters if abs(r.p0[span_ax] - cut) < _ON_CUT_TOL_M),
                        key=lambda r: r.p0[ridge_ax])
        centre = cut + inboard * block.width_m / 2.0
        for index, (a, b) in enumerate(zip(on_cut, on_cut[1:], strict=False)):
            start = a.p0[ridge_ax] + cross_section(a.profile).width_m / 2.0
            end = b.p0[ridge_ax] - cross_section(b.profile).width_m / 2.0
            if end - start <= 1e-6:
                continue
            q0 = [0.0, 0.0]
            q1 = [0.0, 0.0]
            q0[span_ax] = q1[span_ax] = centre
            q0[ridge_ax], q1[ridge_ax] = start, end
            members.append(FramedMember(
                roof.uid, f"eave-block-{side}-{index:03d}", "blocking", profile,
                (q0[0], q0[1]), (q1[0], q1[1]), plate_top_z_m, plate_top_z_m + block.depth_m,
                end - start, connection=EAVE_BLOCKING_CONNECTION,
            ))
    return tuple(members)
