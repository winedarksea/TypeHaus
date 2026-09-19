"""How close two run segments actually come, and where — the measure, not the band.

``resolve/mep_envelopes`` gives every segment a PRISM: a buffered plan footprint over
``min(z)..max(z)`` of its two ends. That is the right solid for a router (it must not plan
through anything the run might occupy) and the wrong one for a verdict. A leg that falls
six inches over eight feet reads as a box six inches tall at every station, so a drain
passing four inches under it reads as interpenetrating it. On catlin that band was
**twenty-five** of the 146 reported clashes: the nine main-ceiling radials against
``PR-M-S-BATH1-WC-DRAIN``'s second leg are 0.0"–0.95" clear where they actually cross, and
``PR-B-KITCH-DRAIN``'s sixth leg clears ``DU-B-ERV-RET-TRUNK`` by 4.26".

So the check keeps the prisms as its COARSE FILTER — an STRtree over footprints, which is
what makes the pair loop affordable — and asks this module for the fine answer on whatever
survives. ``routing/obstacles`` keeps the band, and says so: a router has to avoid where a
run *might* be, because it is choosing, and a check is reading.

**The shape of the answer.** Parameterise along the segment that has plan length. At
station ``s`` the near run is at a point with a centreline z, and the far run is at its
nearest point with its own; the two numbers a builder needs are how deep they are inside
each other **in plan** and **in elevation** at that one station, and the verdict is the
smaller of the two — a right-angle crossing that is an inch inside in plan and clears by a
foot in z is not a clash.

**Why an optimiser and not a sample.** Both terms are concave in ``s``: plan distance to a
segment is convex (distance to a convex set, composed with an affine map) and ``|Δz|`` is
convex on each piece where the far run's projection parameter is unclamped. The minimum of
two concave functions is concave, so a ternary search on each of the at-most-three pieces
finds the true maximum rather than a lattice point near it. A verdict that moved when the
sample rate moved would not be a verdict.

**A riser stays banded, and that is not an exception.** A vertical occupies its whole fall
at ONE plan point, so its z at a station really is an interval and the far reading takes
the nearest point of it. Banding a *sloping* leg claims it is somewhere it never is;
banding a riser states where it is.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot

#: A segment whose plan length is under this is a riser: a vertical standing at one point.
#: Well below the 1/16" grid this repo authors on, so it catches only a true repeat of a
#: vertex and never a short real leg.
RISER_PLAN_M = 1e-4

#: Ternary-search iterations per piece. The interval shrinks by ~0.62 each step, so 48 takes
#: a 10 m leg to under a nanometre — the cost is a hundred arithmetic operations on a pair
#: the coarse filter already accepted, and the alternative is a verdict that depends on a
#: sample rate.
_REFINE_STEPS = 48

_EPS = 1e-12


@dataclass(frozen=True)
class Segment:
    """One leg of one run: its plan ends, its centreline z at each, and its half-section.

    ``half_w_m``/``half_d_m`` are the SURFACE half-dimensions — real outside diameter plus
    lagging, the pair ``mep_envelopes.run_sections`` returns — across the run in plan and
    vertically. A 10x8 duct is 5" and 4", not 5" in both directions.
    """

    tag: str
    index: int
    a: tuple[float, float]
    b: tuple[float, float]
    za: float
    zb: float
    half_w_m: float
    half_d_m: float

    @property
    def plan_length_m(self) -> float:
        return hypot(self.b[0] - self.a[0], self.b[1] - self.a[1])

    @property
    def is_riser(self) -> bool:
        return self.plan_length_m <= RISER_PLAN_M


@dataclass(frozen=True)
class Contact:
    """The deepest place two segments are inside each other, and by how much.

    ``score_m`` is the smaller of the two depths and is what a finding leads with: the
    shallower axis is the one that has to move, and it is also the one a reader can check
    against a drawing. Both ``near_z_m`` and ``far_z_m`` are CENTRELINE elevations at
    ``point``, because that is what a plan file authors.
    """

    score_m: float
    plan_depth_m: float
    z_depth_m: float
    point: tuple[float, float]
    near_z_m: float
    far_z_m: float


#: One joint, as ``run_joints`` returns it: a plan point and the z band a fitting there may
#: occupy, or ``(None, None)`` for a joint the model never placed in z.
Joint = tuple[tuple[float, float], float | None, float | None]


def segment_clearance(near: Segment, far: Segment, *, joints: tuple[Joint, ...] = (),
                      joint_reach_m: float = 0.0) -> Contact | None:
    """The deepest contact between these two legs, or ``None`` where they never touch.

    ``joints`` pardons a contact LOBE whose peak is a fitting between the two runs —
    within ``joint_reach_m`` of the joint in plan AND inside its z band. A pair jointed at
    one end and crossing at the other has two lobes and reports the second, which is what
    the single bool this replaced could not do.
    """
    plan_sum = near.half_w_m + far.half_w_m
    z_sum = near.half_d_m + far.half_d_m
    if plan_sum <= 0.0 and z_sum <= 0.0:
        return None

    swapped = near.is_riser and not far.is_riser
    first, second = (far, near) if swapped else (near, far)
    if first.is_riser and second.is_riser:
        contact = _riser_pair(first, second, plan_sum, z_sum, joints, joint_reach_m)
    else:
        contact = _walk(first, second, plan_sum, z_sum, joints, joint_reach_m)
    if contact is None:
        return None
    if swapped:
        contact = Contact(contact.score_m, contact.plan_depth_m, contact.z_depth_m,
                          contact.point, contact.far_z_m, contact.near_z_m)
    return contact


def _walk(near: Segment, far: Segment, plan_sum: float, z_sum: float,
          joints: tuple[Joint, ...], joint_reach_m: float) -> Contact | None:
    """The general case: ``near`` has plan length, so station ``s`` runs along it."""
    ax, ay = near.a
    dx, dy = near.b[0] - ax, near.b[1] - ay
    cx, cy = far.a
    fx, fy = far.b[0] - cx, far.b[1] - cy
    flen2 = fx * fx + fy * fy
    far_riser = far.is_riser
    far_lo, far_hi = min(far.za, far.zb), max(far.za, far.zb)

    def at(s: float) -> Contact:
        px, py = ax + dx * s, ay + dy * s
        zn = near.za + (near.zb - near.za) * s
        if far_riser:
            qx, qy = cx, cy
            # The riser occupies its whole fall at this one point, so the reading is its
            # nearest elevation to the near run's — banding states where it is.
            zf = far_lo if zn < far_lo else (far_hi if zn > far_hi else zn)
        else:
            t = ((px - cx) * fx + (py - cy) * fy) / flen2
            t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
            qx, qy = cx + fx * t, cy + fy * t
            zf = far.za + (far.zb - far.za) * t
        plan_depth = plan_sum - hypot(px - qx, py - qy)
        z_depth = z_sum - abs(zn - zf)
        return Contact(min(plan_depth, z_depth), plan_depth, z_depth, (px, py), zn, zf)

    best: Contact | None = None
    pieces = _pieces(ax, ay, dx, dy, cx, cy, fx, fy, flen2, far_riser)
    for peak in _lobe_peaks(at, pieces):
        if _at_a_joint(near, peak, joints, joint_reach_m):
            continue
        if best is None or peak.score_m > best.score_m:
            best = peak
    return best


def _pieces(ax: float, ay: float, dx: float, dy: float, cx: float, cy: float,
            fx: float, fy: float, flen2: float, far_riser: bool
            ) -> list[tuple[float, float]]:
    """``[0, 1]`` split where the far run's projection parameter clamps — at most three.

    Inside a piece the far run's z is affine in ``s`` and the concavity argument in the
    module docstring holds; across a clamp it kinks, and a ternary search over the kink
    would converge on the kink rather than on the maximum.
    """
    if far_riser:
        return [(0.0, 1.0)]
    slope = (dx * fx + dy * fy) / flen2
    if abs(slope) < _EPS:
        return [(0.0, 1.0)]
    base = ((ax - cx) * fx + (ay - cy) * fy) / flen2
    cuts = sorted(s for s in ((0.0 - base) / slope, (1.0 - base) / slope) if 0.0 < s < 1.0)
    edges = [0.0, *cuts, 1.0]
    return [(edges[i], edges[i + 1]) for i in range(len(edges) - 1)]


def _maximise(at, low: float, high: float) -> Contact:
    """Ternary search for the maximum of a concave score on ``[low, high]``."""
    best = at(low)
    right = at(high)
    if right.score_m > best.score_m:
        best = right
    for _ in range(_REFINE_STEPS):
        if high - low < 1e-12:
            break
        first = low + (high - low) / 3.0
        second = high - (high - low) / 3.0
        left_value, right_value = at(first), at(second)
        if left_value.score_m < right_value.score_m:
            low = first
            if right_value.score_m > best.score_m:
                best = right_value
        else:
            high = second
            if left_value.score_m > best.score_m:
                best = left_value
    return best


def _lobe_peaks(at, pieces: list[tuple[float, float]]) -> list[Contact]:
    """The peak of each CONTIGUOUS stretch of contact — one per lobe, not per piece.

    **A lobe, not a station, is what a joint pardons.** Two runs tee'd together overlap in
    one connected stretch either side of the fitting; carving a fixed reach out of the
    middle of that stretch leaves slivers at its edges, and on catlin the sliver 4 1/2"
    back down ``PR-M-KITCH-VENT`` reported as a clash against the very fitting that put it
    there. A pair jointed at one end and crossing at the other has TWO lobes with a gap of
    no contact between them, and only the second is a finding — which is the sentence the
    check makes: the exemption is local to the joint, not a pardon for the pair.
    """
    peaks = [_maximise(at, low, high) for low, high in pieces]
    out: list[Contact] = []
    lobe: Contact | None = None
    for index, (piece, peak) in enumerate(zip(pieces, peaks, strict=True)):
        if peak.score_m <= 0.0:
            if lobe is not None:
                out.append(lobe)
                lobe = None
            continue
        # Contiguous with the lobe to the left iff the boundary between them is in contact.
        if lobe is not None and index > 0 and at(piece[0]).score_m > 0.0:
            if peak.score_m > lobe.score_m:
                lobe = peak
            continue
        if lobe is not None:
            out.append(lobe)
        lobe = peak
    if lobe is not None:
        out.append(lobe)
    return out


def _at_a_joint(near: Segment, contact: Contact, joints: tuple[Joint, ...],
                joint_reach_m: float) -> bool:
    """Whether this lobe's peak is the fitting these two runs are joined by.

    Both measures have to agree. The plan test alone would exempt a riser crossing ten feet
    below the stack head it eventually lands on — same plan point, different building. A
    joint whose z the model never resolved falls back to the plan test, which is what the
    model actually knows about it.
    """
    for point, low_z, high_z in joints:
        if hypot(contact.point[0] - point[0], contact.point[1] - point[1]) > joint_reach_m:
            continue
        if low_z is None or high_z is None:
            return True
        if low_z - near.half_d_m <= contact.near_z_m <= high_z + near.half_d_m:
            return True
    return False


def _riser_pair(near: Segment, far: Segment, plan_sum: float, z_sum: float,
                joints: tuple[Joint, ...], joint_reach_m: float) -> Contact | None:
    """Two verticals: one plan point each, one z band each, and no station to search."""
    plan_depth = plan_sum - hypot(near.a[0] - far.a[0], near.a[1] - far.a[1])
    near_lo, near_hi = min(near.za, near.zb), max(near.za, near.zb)
    far_lo, far_hi = min(far.za, far.zb), max(far.za, far.zb)
    gap = max(0.0, near_lo - far_hi, far_lo - near_hi)
    z_depth = z_sum - gap
    score = min(plan_depth, z_depth)
    if score <= 0.0:
        return None
    # The overlap's own middle, so the reported elevations are inside both bands.
    middle = (max(near_lo, far_lo) + min(near_hi, far_hi)) / 2.0
    near_z = min(max(middle, near_lo), near_hi)
    far_z = min(max(middle, far_lo), far_hi)
    for point, low_z, high_z in joints:
        if hypot(near.a[0] - point[0], near.a[1] - point[1]) > joint_reach_m:
            continue
        if low_z is None or high_z is None:
            return None
        if low_z - near.half_d_m <= near_z <= high_z + near.half_d_m:
            return None
    return Contact(score, plan_depth, z_depth, near.a, near_z, far_z)
