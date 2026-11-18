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

import re
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
    #: ``"open_web" | "i_joist" | "solid_sawn" | "rim_board"`` — which rule applied. A
    #: consumer needing to qualify its verdict (an I-joist PASS is not a whole answer)
    #: branches on this rather than on the prose.
    kind: str

    @property
    def height_m(self) -> float:
        return self.z1_m - self.z0_m


def member_window(floor: ResolvedFloor, member: FramedMember | None = None, *,
                  chart=None) -> CrossingWindow | None:
    """The crossing window for this floor, or ``None`` when its section publishes none.

    The band is measured inside the floor's own structural depth — ``min z0`` to ``max z1``
    over its members — rather than off the section's nominal depth, because that is the
    extent the members actually resolved to and the two can differ at a dropped or raised
    bearing.

    ``member`` names the section to read; without it the floor's first **joist** is taken.
    That default matters: ``members[0]`` is whichever member the resolver emitted first,
    which is a rim board on most floors, and a rim board is never an open web.

    ``chart`` is the I-joist's ``JoistHoleChart`` where the library holds one; it only
    changes the sentence an I-joist window quotes.
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

    if member.category == "rim":
        # A centred round hole up to 2/3 of the depth holds anything in the middle 2/3.
        margin = depth_m / 6.0
        return CrossingWindow(
            low + margin, high - margin, kind="rim_board",
            basis=(f"inside the middle 2/3 of a {member.profile}, where TJ-8000 (March 2025) "
                   "p.4 allows a round hole up to 2/3 its depth, centred vertically; its 2D "
                   "end distance and 'not under concentrated loads' are not graded here"))

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
            basis=(f"clear of both {flange_in:.3g}\" flanges of a {member.profile}; "
                   + (f"the hole's size and zone are graded on {chart.source}"
                      if chart is not None else
                      "the hole's diameter and its allowable zone along the span still come "
                      "off the fabricator's chart, which this engine does not hold")))

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


def is_member_line(member) -> bool:
    """One of the floor's own member lines: a joist, a rim, or a trimmer or sister in an
    open-web truss section — an opening's edge or a doubled line on a truss floor is a
    truss, and a leg across it passes through the same web window (catlin's
    FO-S-ERV-CHASE, 2026-09-24; FS-M-NE's peninsula truss)."""
    if member.category in ("joist", "rim"):
        return True
    if member.category not in ("trimmer", "sister_joist"):
        return False
    from typehaus.resolve.framing.profiles import cross_section, open_web_opening_m

    section = cross_section(member.profile)
    return section is not None and open_web_opening_m(section) is not None


#: The 2x6 box ``resolve/floor_blocking`` frames AROUND a crossing run (its own check's).
_BOX_PART = re.compile(r"-(rail-top|rail-bottom|cheek-lo|cheek-hi)$")


def is_solid_floor_member(member) -> bool:
    """A placed, non-I-joist member ``mep.run_through_floor_member`` reads, and the router's
    perpendicular bars (strongback, blocking, ledger): not a bearing block or a run's own box."""
    from typehaus.resolve.framing.profiles import cross_section

    key = member.child_key
    if member.z0_m is None or member.p0 == member.p1 or key.startswith("bearing-block") \
            or _BOX_PART.search(key):
        return False
    section = cross_section(member.profile)
    return section is not None and section.shape != "i_joist"


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
        if member.z0_m is None or not is_member_line(member):
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


#: A joist end this close to a floor header's face hangs on it.
_HUNG_GAP_M = inch(0.25).meters
#: Fallback seat where a support cannot be found (a 2x4 plate's 3 1/2").
_FALLBACK_SEAT_M = inch(3.5).meters


def floor_supports(model, floor: ResolvedFloor) -> tuple:
    """Plan outlines a ``floor``'s joists can end on: flush or dropped BEAM solids and the
    STRUCTURE layer of walls standing under the deck. Each is ``(outline, z0, z1)``."""
    joists = [m for m in floor.members if m.category == "joist" and m.z0_m is not None]
    if not joists:
        return ()
    z0, z1 = min(m.z0_m for m in joists), max(m.z1_m for m in joists)
    tol = inch(1).meters
    out = [tuple(s.outline) for s in model.solids
           if s.category == "beam" and s.z1_m >= z0 - tol and s.z0_m <= z1]
    for wall in model.walls:
        for layer in wall.layers:
            top = layer.z1_m if layer.z1_m is not None else wall.z1_m
            if (layer.function == "structure" and layer.polygon and top is not None
                    and z0 - tol <= top <= z1 + tol):
                out.append(tuple(layer.polygon))
    return tuple(out)


def support_faces(floor: ResolvedFloor, member: FramedMember,
                  supports: tuple = ()) -> tuple[float | None, float | None]:
    """The inside faces of ``member``'s two supports, along its span (plan coordinate).

    Every end is an END support (each piece of a line split over a bearing is a simple span),
    so Table A reads all of them. An end at the deck's outer tip sits on a plate: its face is
    the tip less the seat. An end at a floor HEADER's face hangs there (face = end). Any other
    end is cut at its support's AXIS (``resolve/floors.py``), so the face is the far edge of
    the beam or wall structure in ``supports`` (``floor_supports``) under it; where none is
    found, the deck's larger end seat in (conservative). ``None``: a cantilevered tip, which
    Table A does not grade. ``notes/framing_bore_limits.md`` §11.
    """
    k = 0 if floor.direction == "x" else 1
    lo, hi = sorted((member.p0[k], member.p1[k]))
    line = member.p0[1 - k]
    ends = floor.ends
    seats = [v for v in ((ends.seat_lo, ends.seat_hi) if ends else ()) if v is not None]

    def face(end: float, sign: float) -> float | None:
        if ends is not None:
            for tip, seat in ((ends.tip_lo, ends.seat_lo), (ends.tip_hi, ends.seat_hi)):
                if abs(end - tip) < 1e-3:
                    return None if seat is None else end + sign * seat
        for other in floor.members:
            if other.category != "header":
                continue
            span = sorted((other.p0[1 - k], other.p1[1 - k]))
            if (span[0] - 1e-3 <= line <= span[1] + 1e-3
                    and abs(abs(other.p0[k] - end) - _half_width(other)) < _HUNG_GAP_M):
                return end
        outside = end - sign * 1e-4
        for outline in supports:
            reach = _interval_at(outline, k, line, outside)
            if reach is not None:
                return reach[1] if sign > 0 else reach[0]
        return end + sign * (max(seats) if seats else _FALLBACK_SEAT_M)

    return face(lo, 1.0), face(hi, -1.0)


def _half_width(member: FramedMember) -> float:
    from typehaus.resolve.framing.profiles import cross_section

    section = cross_section(member.profile)
    return section.width_m / 2.0 if section is not None else 0.0


def _interval_at(outline, k: int, line: float, at: float) -> tuple[float, float] | None:
    """The run of ``outline`` along axis ``k`` on the line ``line`` that contains ``at``."""
    cuts = []
    n = len(outline)
    for i in range(n):
        a, b = outline[i], outline[(i + 1) % n]
        if (a[1 - k] - line) * (b[1 - k] - line) > 0 or a[1 - k] == b[1 - k]:
            continue
        t = (line - a[1 - k]) / (b[1 - k] - a[1 - k])
        cuts.append(a[k] + t * (b[k] - a[k]))
    cuts.sort()
    for i in range(0, len(cuts) - 1, 2):
        if cuts[i] - 1e-9 <= at <= cuts[i + 1] + 1e-9:
            return cuts[i], cuts[i + 1]
    return None


# --- open-web PANEL layout ----------------------------------------------------------------
#
# ``member_window`` answers "how tall is the slot"; where along a truss there is a slot at all
# is each truss's ``FramedMember.web`` (``resolve/open_web.OpenWebShape``): the maker's
# published openings placed on that member. Ask it with :func:`web_grade`.


def web_grade(floor: ResolvedFloor, member: FramedMember, station_m: float, z_m: float,
              along_m: float, height_m: float, round_: bool):
    """A run centred at plan ``station_m`` and elevation ``z_m`` against the opening it lands
    in on ``member``'s truss: an ``open_web.CrossingGrade``, or ``None`` where the member
    carries no web layout (not an open-web truss, or its deck quotes no published openings)."""
    from typehaus.resolve.open_web import RunSize, grade_crossing, run_of

    if member.web is None:
        return None
    return grade_crossing(member.web, run_of(member, station_m, floor.direction == "x"),
                          z_m - member.z0_m, RunSize(along_m, height_m, round_))
