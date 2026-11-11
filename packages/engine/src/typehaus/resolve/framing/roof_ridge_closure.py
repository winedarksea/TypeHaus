"""A joist roof seated on a beveled ridge plate: the plate's section and the closure blocks.

TJ-4000 R14/R14W: the joists run to the centreline and bear on a double-beveled plate over a
continuous wall. One centreline block per bay closes the peak, notched over the plate and
beveled on top to carry both deck edges. Two eave-style rows would leave those edges
unsupported, and full-depth rows would trap a void the foam cannot reach.
"""

from __future__ import annotations

from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import FramedMember, ResolvedRoof

RIDGE_PLATE_CONNECTION = "ridge:beveled-plate"
RIDGE_CLOSURE_CONNECTION = "ridge:closure"
#: TJ-4000 p.30's blocking list. Bought 14" deep and cut to the joist's plumb depth.
_CLOSURE_PROFILE = "1.5x14 LSL"


def plate_ring(width_m: float, depth_m: float, pitch: float) -> tuple[tuple[float, float], ...]:
    """The double-beveled section: flat underside, both top faces falling at the roof pitch."""
    half = width_m / 2.0
    edge = depth_m - half * pitch
    return ((-half, 0.0), (half, 0.0), (half, edge), (0.0, depth_m), (-half, edge))


def ridge_closures(
    roof: ResolvedRoof, rafters: tuple[FramedMember, ...], plate: FramedMember,
    plumb_m: float, pitch: float,
) -> tuple[FramedMember, ...]:
    """One closure per bay between adjacent rafter stations along the ridge."""
    ridge_ax = 0 if roof.ridge_direction == "x" else 1
    line = plate.p0[1 - ridge_ax]
    stations = sorted({round(r.p1[ridge_ax], 6): r for r in rafters}.items())
    block = cross_section(_CLOSURE_PROFILE)
    half = block.width_m / 2.0
    notch = half * pitch
    # z0 is the underside at the block's faces, where the plate has fallen away.
    z0 = plate.z1_m - notch
    ring = ((-half, 0.0), (0.0, notch), (half, 0.0), (half, plumb_m),
            (0.0, plumb_m + notch), (-half, plumb_m))
    members: list[FramedMember] = []
    for index, ((a, rafter_a), (b, rafter_b)) in enumerate(
            zip(stations, stations[1:], strict=False)):
        start = a + cross_section(rafter_a.profile).width_m / 2.0
        end = b - cross_section(rafter_b.profile).width_m / 2.0
        if end - start <= 1e-6:
            continue
        q0, q1 = [0.0, 0.0], [0.0, 0.0]
        q0[1 - ridge_ax] = q1[1 - ridge_ax] = line
        q0[ridge_ax], q1[ridge_ax] = start, end
        members.append(FramedMember(
            roof.uid, f"ridge-closure-{index:03d}", "blocking", _CLOSURE_PROFILE,
            (q0[0], q0[1]), (q1[0], q1[1]), z0, z0 + plumb_m + notch, end - start,
            connection=RIDGE_CLOSURE_CONNECTION, section_ring=ring,
        ))
    return tuple(members)
