"""Where a service may pass THROUGH a floor's members, and where it meets one.

Three readings of "the window a run gets" existed in this tree and no two agreed:
``routing/corridors.crossing_window`` fell back to a hardcoded chord when it could not
answer; ``mep_queries.duct_bay_occupancy`` asked ``open_web_opening_m`` directly and
treated ``None`` as "conflict" or "unknown" by branch; and no check asked at all. This
module is the one place the question is answered, and both of those now read it.

**The window is not one rule, it is three, and which applies is a fact about the section:**

* an **open-web floor truss** hands a service its web space —
  ``profiles.open_web_opening_m`` owns the 8 7/8" derivation and the note's §3 checks it by
  hand — inset symmetrically inside the floor's own structural depth;
* an **I-joist** wants a bored hole in the web, so the window is the depth less both
  flanges. **Nothing may touch a flange, on any manufacturer's chart, ever**, which is why
  a check can honestly FAIL a surface that reaches one while saying plainly that the hole's
  *diameter* and its *allowable zone along the span* still come off that chart and this
  engine does not hold it;
* **solid-sawn** lumber takes IRC R502.8.1: a bored hole stays 2" clear of top and bottom.

A member whose section answers none of those gets no window at all, and the caller reports
that rather than guessing — the failure mode this module replaces is a fallback that
"answered right for the wrong reason on the one floor it was checked against".
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from typehaus.quantities import M_PER_IN, inch

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import FramedMember, ResolvedFloor

#: IRC R502.8.1: a bored hole in a solid-sawn joist keeps 2" clear of the top and bottom
#: edges. The only one of the three readings that is a code number rather than a product's.
SOLID_SAWN_EDGE_CLEARANCE_M = inch(2).meters


@dataclass(frozen=True)
class CrossingWindow:
    """The z band a run's OUTSIDE may occupy while passing through this floor's members.

    ``basis`` is the sentence a finding quotes. It is carried rather than re-derived because
    "1.194" of crown" means nothing to a builder without "inside the truss's 8 7/8"
    chord-to-chord web" beside it, and because the three readings are not equally strong —
    one is a code section, one a product geometry, one a manufacturer's chart this engine
    does not hold.
    """

    z0_m: float
    z1_m: float
    basis: str
    #: ``"open_web" | "i_joist" | "solid_sawn"`` — which of the three rules applied. A
    #: consumer needing to qualify its verdict (an I-joist PASS is not a whole answer)
    #: branches on this rather than on the prose.
    kind: str

    @property
    def height_m(self) -> float:
        return self.z1_m - self.z0_m


def member_window(floor: ResolvedFloor,
                  member: FramedMember | None = None) -> CrossingWindow | None:
    """The crossing window for this floor, or ``None`` when its section publishes none.

    The band is measured inside the floor's own structural depth — ``min z0`` to ``max z1``
    over its members — rather than off the section's nominal depth, because that is the
    extent the members actually resolved to and the two can differ at a dropped or raised
    bearing.

    ``member`` names the section to read; without it the floor's first **joist** is taken.
    That default matters: ``members[0]`` is whichever member the resolver emitted first,
    which is a rim board on most floors, and a rim board is never an open web.
    """
    from typehaus.resolve.framing.profiles import cross_section, open_web_opening_m

    placed = [m for m in floor.members if m.z0_m is not None]
    if not placed:
        return None
    low = min(m.z0_m for m in placed)
    high = max((getattr(m, "z1_m", None) or floor.deck_z0_m) for m in placed)
    depth_m = high - low
    if depth_m <= 0:
        return None

    if member is None:
        member = next((m for m in placed if m.category == "joist"), placed[0])
    section = cross_section(member.profile)

    opening_m = open_web_opening_m(section)
    if opening_m is not None and opening_m > 0:
        margin = (depth_m - opening_m) / 2.0
        return CrossingWindow(
            low + margin, high - margin, kind="open_web",
            basis=(f"inside the {opening_m / M_PER_IN:.3g}\" chord-to-chord web of a "
                   f"{member.profile}, which needs no hole cut in anything"))

    if section.shape == "i_joist" and section.flange_thickness_m:
        flange_in = section.flange_thickness_m / M_PER_IN
        return CrossingWindow(
            low + section.flange_thickness_m, high - section.flange_thickness_m,
            kind="i_joist",
            basis=(f"clear of both {flange_in:.3g}\" flanges of a {member.profile}; the "
                   "hole's diameter and its allowable zone along the span still come off "
                   "the fabricator's chart, which this engine does not hold"))

    if section.shape == "rect":
        clear = SOLID_SAWN_EDGE_CLEARANCE_M
        if depth_m <= 2 * clear:
            return None  # nothing left to bore; a 2x4 flat has no window at all
        return CrossingWindow(
            low + clear, high - clear, kind="solid_sawn",
            basis=(f"2\" clear of the top and bottom edges of a {member.profile}, "
                   "per IRC R502.8.1"))

    return None


@dataclass(frozen=True)
class MemberCrossing:
    """One place a run's centreline meets one member's line, interpolated.

    **Per-crossing, not per-leg.** Banding a whole leg against the window is the tempting
    shortcut and it is wrong in both directions: it reads a leg's high end against the
    chords even where that end sits in a clear bay with no truss in it — worth three false
    FAILs on catlin, including the 0.694" that is the whole of BLD-05's "half an inch of
    clearance" — and a station-only test in the other direction produced 17 phantom pairs
    grading one floor's runs against another's.
    """

    member_key: str
    #: Plan coordinate along the member's own direction of travel, where the run met it.
    station_m: float
    #: The run's centreline there.
    z_m: float
    #: Where along the LEG the meeting happened, 0 at ``a`` and 1 at ``b``. Carried because
    #: a gravity search needs the developed length at the crossing, and the developed length
    #: is a fraction of the leg — recovering it from ``station_m`` is impossible on a leg
    #: that runs square to the member lines, where every crossing shares one station.
    t: float = 0.0


def leg_crossings(floor: ResolvedFloor,
                  a: tuple[float, float], b: tuple[float, float],
                  za: float, zb: float) -> list[MemberCrossing]:
    """Every member of ``floor`` this one leg crosses, with the run's z at each.

    A crossing is earned three ways over, and dropping any one of them invents findings:

    * the leg must actually change the coordinate the member lines vary in — a leg running
      **along** a bay crosses nothing, whatever it passes over;
    * the meeting point must lie within that member's own **plan extent**, because a joist
      is a piece of wood between two bearings, not an infinite line (this is what localises
      a finding to the right floor);
    * the run's centreline there must lie within the member's own **z band**, or the run is
      passing under or over the floor rather than through it — which is
      ``mep.run_in_finished_volume``'s question, not this one.
    """
    along_x = floor.direction == "x"  # members span in x, so their lines are at constant y
    perp_a, perp_b = (a[1], b[1]) if along_x else (a[0], b[0])
    if abs(perp_a - perp_b) < 1e-9:
        return []
    along_a, along_b = (a[0], b[0]) if along_x else (a[1], b[1])

    out: list[MemberCrossing] = []
    for member in floor.members:
        if member.z0_m is None or member.category not in ("joist", "rim"):
            continue
        p0 = member.p0[1] if along_x else member.p0[0]
        p1 = member.p1[1] if along_x else member.p1[0]
        if abs(p1 - p0) > 1e-6:
            continue  # a member running the other way is not one of this floor's lines
        if not (min(perp_a, perp_b) < p0 < max(perp_a, perp_b)):
            continue
        t = (p0 - perp_a) / (perp_b - perp_a)
        station = along_a + t * (along_b - along_a)
        lo = min(member.p0[0], member.p1[0]) if along_x else min(member.p0[1], member.p1[1])
        hi = max(member.p0[0], member.p1[0]) if along_x else max(member.p0[1], member.p1[1])
        if not (lo - 1e-6 <= station <= hi + 1e-6):
            continue
        z = za + (zb - za) * t
        top = getattr(member, "z1_m", None) or floor.deck_z0_m
        if not (member.z0_m <= z <= top):
            continue
        out.append(MemberCrossing(member.child_key, station, z, t))
    return out


# --- open-web PANEL layout (2026-09-19) -----------------------------------------------
#
# ``member_window`` above answers "how tall is the slot"; this answers "and where along the
# member is there a slot at all". The two are a pair, and the engine has been asking only
# the first: an open-web truss reads as a CONTINUOUS 8 7/8" chase, so thirteen 4" ducts
# crossing every truss inside a 41" band all pass. Real trusses have webs at panel points.
#
# Unauthored is silence, not a pass: a fabricator's panel layout is a shop drawing, and
# ``mep.open_web_panel`` reports UNKNOWN naming the floor rather than inventing a pitch.


@dataclass(frozen=True)
class WebPanels:
    """One open-web deck's panel layout, in the member's own direction of travel.

    ``pitch_m`` is centre to centre of the panel points, ``opening_m`` the CLEAR run
    between two webs measured at the chord, and ``offset_m`` the station of the first
    panel point. The web band either side of a panel point is therefore
    ``pitch - opening`` wide, which is the solid the run has to miss.
    """

    pitch_m: float
    opening_m: float
    offset_m: float

    @property
    def web_width_m(self) -> float:
        return max(0.0, self.pitch_m - self.opening_m)

    def index_at(self, station_m: float) -> int:
        """Which opening this station falls in — openings numbered from the offset."""
        import math

        return int(math.floor((station_m - self.offset_m) / self.pitch_m))

    def opening_at(self, station_m: float) -> tuple[float, float]:
        """The clear run ``(low, high)`` of the opening containing ``station_m``.

        Every station is *in* an opening in this sense; whether it is CLEAR of the webs is
        :meth:`clear_at`. Returning the span unconditionally is what lets a check say "this
        opening holds three runs" about the one the crossing landed in.
        """
        index = self.index_at(station_m)
        low = self.offset_m + index * self.pitch_m + self.web_width_m / 2.0
        return low, low + self.opening_m

    def clear_at(self, station_m: float, radius_m: float = 0.0) -> bool:
        """Whether a run of this radius at this station misses both webs."""
        low, high = self.opening_at(station_m)
        return low + radius_m <= station_m <= high - radius_m

    def web_bands(self, low_m: float, high_m: float) -> list[tuple[float, float]]:
        """The solid web runs between ``low_m`` and ``high_m``, as ``(start, end)``.

        The complement of the openings. ``routing/obstacles`` turns each into a ``fixed``
        hard prism so a router threads the openings by construction rather than by being
        told off afterwards.
        """
        width = self.web_width_m
        if width <= 0.0 or self.pitch_m <= 0.0:
            return []
        out: list[tuple[float, float]] = []
        index = self.index_at(low_m)
        while True:
            centre = self.offset_m + index * self.pitch_m
            start, end = centre - width / 2.0, centre + width / 2.0
            if start > high_m:
                break
            if end >= low_m:
                out.append((max(start, low_m), min(end, high_m)))
            index += 1
        return out


def web_panels(floor: ResolvedFloor) -> WebPanels | None:
    """This deck's authored panel layout, or ``None`` where it states none."""
    stated = getattr(floor, "web_panels", None)
    if not stated:
        return None
    pitch, opening, offset = stated
    if pitch <= 0.0 or opening <= 0.0 or opening > pitch:
        return None
    return WebPanels(pitch_m=pitch, opening_m=opening, offset_m=offset)
