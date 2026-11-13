"""Solid floor members a run crosses at right angles to the joists: strongback, blocking, ledger.

``mep.run_through_floor_member`` grades a leg ACROSS any non-joist solid member as a bore
(``resolve/mep_bores.joist_bore``: D/3 of the member's own depth) and a riser through one, or
a leg riding inside it, as the member's removal. The lattice saw only joist lines (and rails,
which cover riding along), so a 2" drain crossed a 2x6 strongback (D/3 = 1.83") at 0 cost.

Here each such member is a ``Bar``: a level crossing is a bore (priced as a joist's, refused
when the check would FAIL it), a riser through a non-flat one is refused. A falling run's z is
unknown, so an illegal bar is a banded hard prism (``bar_prisms``) it may pass under or over.
Engineered members (LVL: ``joist_bore`` is UNKNOWN) are left to the check, as before.
``notes/framing_bore_limits.md`` §15 works one strongback by hand.
"""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING, Any

from typehaus.quantities import M_PER_IN

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.routing.obstacles import HardPrism
    from typehaus.routing.space import RoutingSpace

_TOL_M = 1e-6


@dataclass(frozen=True)
class Bar:
    axis: str       # "x" or "y": the way the member runs
    station: float  # its centreline across that axis
    lo: float
    hi: float       # extent along the axis
    half: float     # half its plan width
    z0: float
    z1: float
    profile: str
    tag: str        # ``<floor> <child key>``

    @property
    def flat(self) -> bool:
        """Laid on its face: a riser through it is a drilled hole, not its removal."""
        return self.z1 - self.z0 < 2.0 * self.half


@lru_cache(maxsize=256)
def bore_ok(profile: str, diameter_m: float) -> bool | None:
    """The check's own verdict on a bored hole of this outside diameter (None: engineered)."""
    from typehaus.resolve.mep_bores import joist_bore

    return joist_bore(profile, round(diameter_m / M_PER_IN, 4)).ok


class FloorBars:
    """One floor's bars, sorted by station for each axis so a crossing is a bisect."""

    def __init__(self, bars: list[Bar]) -> None:
        self.bars = bars
        self.by_axis = {axis: sorted((b for b in bars if b.axis == axis),
                                     key=lambda b: b.station) for axis in "xy"}
        self.stations = {axis: [b.station for b in found]
                         for axis, found in self.by_axis.items()}

    def crossed(self, axis: str, station: float, lo: float, hi: float, z: float | None,
                band: tuple[float, float] | None, r: float) -> list[Bar] | None:
        """Bars a level edge along ``axis`` crosses, or None when it runs into one's face.

        An edge ending within a bar's half width + r short of its centreline is the member
        notched (the check's "runs along inside"), refused whole. ``band`` replaces ``z``.
        """
        other = "y" if axis == "x" else "x"
        found = self.by_axis[other]
        out: list[Bar] = []
        top = self.stations[other]
        for i in range(bisect_left(top, lo - r - 0.05), bisect_right(top, hi + r + 0.05)):
            bar = found[i]
            if not bar.lo - _TOL_M <= station <= bar.hi + _TOL_M:
                continue
            low, high = band if band is not None else (z, z)
            if not (high + r > bar.z0 + _TOL_M and low - r < bar.z1 - _TOL_M):
                continue
            if lo + _TOL_M < bar.station < hi - _TOL_M:
                out.append(bar)
            elif (band is None and hi > bar.station - bar.half - r + _TOL_M
                  and lo < bar.station + bar.half + r - _TOL_M):
                return None
        return out

    def riser_on(self, x: float, y: float, low: float, high: float, r: float) -> bool:
        """A vertical through a non-flat bar is its removal; through a flat one, a bore."""
        for bar in self.bars:
            across, along = (y, x) if bar.axis == "x" else (x, y)
            if (abs(across - bar.station) < bar.half + r - _TOL_M
                    and bar.lo - r < along < bar.hi + r
                    and high > bar.z0 + _TOL_M and low < bar.z1 - _TOL_M
                    and (not bar.flat or bore_ok(bar.profile, 2.0 * r) is False)):
                return True
        return False


def floor_bars(floor: Any) -> FloorBars | None:
    """Every level, axis-aligned solid member of ``floor`` that is not a joist line."""
    from typehaus.resolve.geometry_members import member_box
    from typehaus.resolve.mep_crossings import is_member_line, is_solid_floor_member

    out = []
    for member in floor.members:
        if (not is_solid_floor_member(member) or is_member_line(member)
                or member.category == "header"):
            continue
        (ax, ay), (bx, by) = member.p0, member.p1
        box = member_box(member)
        if box is None or (abs(ax - bx) > _TOL_M and abs(ay - by) > _TOL_M):
            continue
        corners = [*box.corners_bottom, *box.corners_top]
        xs, ys, zs = ([c[i] for c in corners] for i in range(3))
        axis = "x" if abs(bx - ax) > abs(by - ay) else "y"
        lo, hi = (min(xs), max(xs)) if axis == "x" else (min(ys), max(ys))
        across = (min(ys), max(ys)) if axis == "x" else (min(xs), max(xs))
        out.append(Bar(axis, sum(across) / 2.0, lo, hi, (across[1] - across[0]) / 2.0,
                       min(zs), max(zs), member.profile, f"{floor.tag} {member.child_key}"))
    return FloorBars(out) if out else None


def bar_prisms(space: RoutingSpace) -> list[HardPrism]:
    """Bars a bore of this run's size would FAIL, as banded prisms (any horizontal edge)."""
    from shapely.geometry import box

    from typehaus.routing.obstacles import HardPrism

    grow = space.radius_m + space.clearance_m
    out = []
    for floor in getattr(space.members, "floors", ()):
        for bar in floor.bars.bars if floor.bars else ():
            if bore_ok(bar.profile, 2.0 * space.radius_m) is not False:
                continue
            w = bar.half + grow
            footprint = (box(bar.lo, bar.station - w, bar.hi, bar.station + w)
                         if bar.axis == "x"
                         else box(bar.station - w, bar.lo, bar.station + w, bar.hi))
            out.append(HardPrism(tag=bar.tag, kind="member", footprint=footprint,
                                 z0_m=bar.z0 - grow, z1_m=bar.z1 + grow,
                                 applies=frozenset({"x", "y"})))
    return out
