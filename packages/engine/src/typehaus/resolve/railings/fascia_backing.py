"""What a fascia bracket's fasteners bite: the band behind the face, and the backing behind it."""

import math

from typehaus.quantities import M_PER_IN
from typehaus.resolve.framing.profiles import cross_section

_BACKING = ("rim", "joist", "blocking", "sister_joist")
_CONTIGUOUS_M = M_PER_IN / 16  # a ply further off than this is not backing
_TIP_PAST_M = 0.5 * M_PER_IN   # a screw tip may run this far past its last ply
_END_DISTANCES = 4             # NDS Table 12.5.1A: 4D end distance, load across the grain


def band_behind(deck, face, tag):
    """(distance from the face origin to its axis, member) of the band parallel to ``face``.

    A joist extending away from the face cannot be the band: only a member parallel to it
    gives a back face a bolt can reach or a ply a screw can start in.
    """
    candidates = []
    for member in deck.members:
        if member.category not in ("rim", "joist"):
            continue
        dx, dy = member.p1[0]-member.p0[0], member.p1[1]-member.p0[1]
        length = math.hypot(dx, dy)
        if length and abs(dx*face.outward[0]+dy*face.outward[1])/length < 1e-8:
            distance = abs(sum((member.p0[i]-face.origin[i])*face.outward[i] for i in range(2)))
            candidates.append((distance, member))
    if not candidates:
        raise ValueError(f"{tag}: no rim behind fascia mounting face")
    return min(candidates, key=lambda item: item[0])


def _crossing(member, point, inward, z):
    """(entry, exit) along the ray ``point + t*inward`` through ``member``, or None."""
    z_lo = min(member.z0_m, member.z0_end_m if member.z0_end_m is not None else member.z0_m)
    z_hi = max(member.z1_m, member.z1_end_m if member.z1_end_m is not None else member.z1_m)
    if not z_lo <= z <= z_hi:
        return None
    run = math.dist(member.p0, member.p1)
    if not run:
        return None
    axis = ((member.p1[0]-member.p0[0])/run, (member.p1[1]-member.p0[1])/run)
    across = (-axis[1], axis[0])
    half = cross_section(member.profile).width_m / 2
    rel = (point[0]-member.p0[0], point[1]-member.p0[1])
    lo, hi = -math.inf, math.inf
    for direction, low, high in ((axis, 0.0, run), (across, -half, half)):
        start = rel[0]*direction[0] + rel[1]*direction[1]
        rate = inward[0]*direction[0] + inward[1]*direction[1]
        if abs(rate) < 1e-12:
            if not low - 1e-9 <= start <= high + 1e-9:
                return None
            continue
        a, b = (low-start)/rate, (high-start)/rate
        lo, hi = max(lo, min(a, b)), min(hi, max(a, b))
    return (lo, hi) if hi > max(lo, 0.0) + 1e-9 else None


def check_screw(deck, band, face, point, z, spec, tag, corner=False):
    """Raise unless a screw from ``point`` (the bracket's outer face) bites the band, holds
    4D to its end, and tips out in, or just past, the last ply contiguous with it.

    A corner bracket's leaves wrap the framed corner, so their holes sit within 4D of it
    by the maker's own detail: they bite whatever member they enter first, with no end rule.
    """
    inward = (-face.outward[0], -face.outward[1])
    crossings = sorted(span for span in (_crossing(m, point, inward, z) for m in deck.members
                                         if m.category in _BACKING) if span is not None)
    if corner:
        reach = crossings[0] if crossings else None
    else:
        run = math.dist(band.p0, band.p1)
        along = sum((point[i]-band.p0[i])*(band.p1[i]-band.p0[i]) for i in range(2)) / run
        if min(along, run-along) < _END_DISTANCES * spec.bolt_diameter.meters:
            raise ValueError(f"{tag}: fascia screw end distance")
        reach = _crossing(band, point, inward, z)
    if reach is None:
        raise ValueError(f"{tag}: fascia screw misses its backing")
    reach = reach[1]
    for entry, exit_ in crossings:
        if entry <= reach + _CONTIGUOUS_M:
            reach = max(reach, exit_)
    if spec.bolt_length.meters > reach + _TIP_PAST_M:
        raise ValueError(f"{tag}: fascia screw misses its backing")
