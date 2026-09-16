"""The plan stair symbol: cut, break line, occlusion, travel line, one line per riser.

Split out of ``floorplan.py``, which was 542 lines against ``AGENTS.md``'s 500, and grown
into the symbol ``plans/20-m2-engine.md`` §137-140 actually specified — "tread lines +
break/direction line + ``UP N R`` label". The break half was never built.

What a plan stair symbol IS
---------------------------
A floorplan is a horizontal cut 4'-0" above the floor, looked at from above. That single
sentence settles four things the old symbol got wrong:

* **A departing flight is cut.** Its treads run up through the cut plane and out of the
  view; everything above the cut is not in this drawing. Drawing all sixteen risers of a
  flight that leaves the storey prints eight feet of stair that is not there.
* **Where it is cut, it is broken.** The break line is the drawing's statement that the
  object continues past the edge of the view.
* **An arriving flight is under the departing one.** Both flights of catlin's U-stair
  occupy one well; from above, the flight coming up hides the one going down where they
  overlap. Drawing both, in full, in the same well is what produced every reported symptom
  at once — two lane widths 1.3" apart, "an extra riser on the right", and two landings.
* **The heaviest line on the symbol is the walk.** It was a bounding-box centreline of the
  floor opening, which on a U-stair lands exactly on the well partition *between* the two
  lanes, and on a winder runs one straight segment across the fan.

Nothing here is a new layer. The hierarchy is lineweight — 0.50 travel, 0.35 ring and
break, 0.25 treads, landings and edges — which both writers already honour.
"""

from __future__ import annotations

import math

from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

from typehaus.emit.draw._shared import to_in as _in
from typehaus.emit.draw.lineweights import LIGHT, PROFILE
from typehaus.emit.draw.scene import Polyline, SceneBuilder
from typehaus.emit.draw.stair_travel import emit_travel, travel_path
from typehaus.quantities import inch
from typehaus.resolve.framing.profiles import cross_section, plan_cross_section_m
from typehaus.resolve.geometry import rect_between
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.stairs.walkline import stair_walk_stations

Pt = tuple[float, float]
Segment = tuple[Pt, Pt]
Box = tuple[float, float, float, float]

#: The plan cut plane, above the storey's floor datum. ``floorplan.py``'s docstring has said
#: "cut 4' above a storey floor" since it was written and nothing encoded it; this is that
#: sentence, as a number. The datum is the storey elevation (top of joists) — the ~1"
#: finished-floor build-up is noise against a 7 1/2" riser, and reading it per room would
#: make the cut a function of the flooring schedule.
PLAN_CUT_HEIGHT_M = inch(48).meters

#: The categories of stair member that are walking surfaces. The framing *under* a landing
#: is ``landing_framing`` and belongs on a framing plan — see ``_landing_platform``.
_WALKING = frozenset({"tread", "winder", "landing"})

#: Break-line geometry, both as fractions of the stair's own dimensions so the symbol scales
#: with the flight and no printed constant appears here. The skew is of the flight's width
#: (0.25 → about 63° to the direction of travel, the conventional lean); the pitch is of a
#: going, which is what sets the two diagonals apart.
_BREAK_DIAGONAL_SKEW = 0.25
_BREAK_LINE_PITCH_GOINGS = 0.4

#: Collinear-and-contained tolerance for the segment ledger, metres. Resolver coordinates
#: are exact sums of authored dimensions, so the only thing being absorbed here is float
#: summation noise.
_LEDGER_TOL_M = 1e-6



# --------------------------------------------------------------- the segment ledger
class _SegmentLedger:
    """One line per riser face; each face drawn by exactly one owner.

    The owner is the tread it lifts you onto — *unless* a drawn landing edge or the floor
    opening's own ring already covers that face, in which case that edge is the line. On the
    second-floor plan the upper flight's springing riser lies on the landing rectangle's
    south edge and its arrival nosing lies on the well ring; drawing them again is the
    doubled line a reader sees as an extra riser.

    Not key equality: a landing rectangle spans lane → partition centre while the riser
    spans the lane, so the two segments are collinear-but-unequal and only containment
    catches it.
    """

    def __init__(self, segments: list[Segment] = ()) -> None:
        self._claimed: list[Segment] = list(segments)

    def claim(self, a: Pt, b: Pt) -> bool:
        """True (and registers) when no already-claimed segment covers ``a``-``b``."""
        if any(_covers(p, q, a, b) for p, q in self._claimed):
            return False
        self._claimed.append((a, b))
        return True

    def claim_ring(self, points: list[Pt], closed: bool = True) -> None:
        """Register every edge of a polyline without testing — the ring is an owner."""
        ends = [*points[1:], points[0]] if closed else list(points[1:])
        self._claimed.extend(zip(points, ends, strict=False))


def _covers(p: Pt, q: Pt, a: Pt, b: Pt) -> bool:
    """Is segment ``a``-``b`` collinear with ``p``-``q`` and contained inside it?"""
    dx, dy = q[0] - p[0], q[1] - p[1]
    run = math.hypot(dx, dy)
    if run < _LEDGER_TOL_M:
        return False
    ux, uy = dx / run, dy / run
    ts = []
    for point in (a, b):
        ox, oy = point[0] - p[0], point[1] - p[1]
        if abs(ox * uy - oy * ux) > _LEDGER_TOL_M:   # off the line
            return False
        ts.append(ox * ux + oy * uy)
    return min(ts) >= -_LEDGER_TOL_M and max(ts) <= run + _LEDGER_TOL_M


# --------------------------------------------------------------- member → plan geometry
def member_footprint(member) -> list[Pt]:
    """A member's plan rectangle: its axis swept by the section face it shows in plan.

    The same construction every emitter builds a member's footprint from, so a landing
    drawn here covers exactly the plan area the 3D deck occupies — which means reading the
    flat-vs-on-edge rule from ``plan_cross_section_m`` rather than assuming either.
    """
    half = plan_cross_section_m(cross_section(member.profile),
                               member.z1_m - member.z0_m) / 2.0
    return rect_between(member.p0, member.p1, -half, half)


def _flight_key(member) -> str:
    """Which flight a walking surface belongs to — the key :func:`flight_stations` uses."""
    if member.category == "winder":
        return "winder"
    if member.category == "tread":
        return member.child_key.rsplit("-", 1)[0]
    return member.child_key


def _mark(member) -> Segment:
    """The line a walking surface draws: its riser FACE, never its board centreline.

    The centreline sits half a going past the riser, which drew a ``(going - nosing)/2``
    sliver at one end of every flight and ``(going + nosing)/2`` at the other — uniform
    steps that read as non-uniform.
    """
    if member.riser_line is not None:
        return member.riser_line
    return (member.p0, member.p1)


def _occlusion_point(member) -> Pt:
    """The point the member's drawn line marks — what occlusion is decided on.

    On *the point*, not on footprint-area fraction. An area rule needs a magic threshold and
    gets ST-B2M's ``tread-lower-005`` wrong: its board pokes 2.7" of 11" past ST-M2S's break,
    so any fraction below 25% leaves one orphan riser line behind the break. The point rule
    hides or shows a flight whole and states cleanly.
    """
    if member.category == "landing":
        return tuple(Polygon(member_footprint(member)).centroid.coords[0])
    if member.plan_outline:
        return tuple(Polygon(member.plan_outline).centroid.coords[0])
    (ax, ay), (bx, by) = _mark(member)
    return ((ax + bx) / 2.0, (ay + by) / 2.0)


def _interpolate(lo, hi, z: float) -> tuple[Segment, Pt]:
    """The ``(a, b)`` segment and its midpoint where the walk route crosses elevation ``z``."""
    (a0, b0, z0), (a1, b1, z1) = lo, hi
    t = 0.0 if abs(z1 - z0) < 1e-12 else (z - z0) / (z1 - z0)
    t = max(0.0, min(1.0, t))
    a = (a0[0] + (a1[0] - a0[0]) * t, a0[1] + (a1[1] - a0[1]) * t)
    b = (b0[0] + (b1[0] - b0[0]) * t, b0[1] + (b1[1] - b0[1]) * t)
    return (a, b), ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)


def _break_segment(route, cut_z: float) -> Segment | None:
    """Where the WALK LINE crosses the cut elevation, as a segment across the flight.

    The one derivation that works for a tread, a landing edge and a winder fan alike, and it
    provably agrees with the per-member cut test: a station's ``z`` *is* its member's
    ``z1_m``. It cannot be pinned to a riser line — ST-B2M's break on the basement plan
    lands on a **landing**.
    """
    for lo, hi in zip(route, route[1:], strict=False):
        if lo[2] <= cut_z < hi[2]:
            return _interpolate(lo, hi, cut_z)[0]
    return None


# --------------------------------------------------------------- the public entry point
def emit_stairs(b: SceneBuilder, model: ResolvedModel, storey: str,
                opening_segments: list[Segment] = ()) -> list[Box]:
    """Draw every stair on both connected plans. Returns its label boxes, in metres.

    ``opening_segments`` are the floor-opening rings ``plan_voids`` has already drawn on
    this sheet (every opening is drawn once, on the plan of the deck it perforates). They
    seed the ledger, which is how a flight's arrival nosing comes for free: the well's own
    edge *is* that riser face.
    """
    storey_record = model.plan.storey(storey)
    if storey_record is None:
        return []
    cut_z = storey_record.elevation.meters + PLAN_CUT_HEIGHT_M
    candidates = [stair for stair in model.stairs
                  if len(stair.outline) >= 3 and storey in {stair.storey, stair.to_storey}]
    # The departing flight is drawn first because it is the one NEARER the reader: it is
    # what occludes, and what the arriving flight is hidden under.
    candidates.sort(key=lambda stair: (stair.storey != storey, stair.uid))
    ledger = _SegmentLedger(list(opening_segments))
    bands: list[Polygon] = []
    boxes: list[Box] = []
    travels: list[list[Pt]] = []
    for stair in candidates:
        band, box = _emit_one(b, model, stair, storey, cut_z, ledger, bands, travels)
        if band is not None:
            bands.append(band)
        boxes.extend(box)
    return boxes


def _emit_one(b: SceneBuilder, model: ResolvedModel, stair, storey: str, cut_z: float,
              ledger: _SegmentLedger, bands: list[Polygon],
              travels: list[list[Pt]]) -> tuple[Polygon | None, list[Box]]:
    """One stair: its visible surfaces, its break, its travel line and its label."""
    route = stair_walk_stations(stair)
    surfaces = [member for member in stair.members
                if member.category in _WALKING and member.p0 != member.p1]
    if not surfaces or len(route) < 2:
        return None, []
    occluder = unary_union(bands) if bands else None
    cut_any = any(member.z1_m > cut_z for member in surfaces)
    visible = [member for member in surfaces
               if member.z1_m <= cut_z
               and not (occluder is not None
                        and occluder.covers(Point(*_occlusion_point(member))))]
    if not visible:
        return None, []

    flights: dict[str, list] = {}
    for member in visible:
        flights.setdefault(_flight_key(member), []).append(member)
    for members in flights.values():
        members.sort(key=lambda member: member.z1_m)
    break_seg = _break_segment(route, cut_z) if cut_any else None

    # Emit order IS the ledger's rule: rings (already claimed), then landings, then the
    # flight side edges, then the riser lines. Each tier is an owner for the one under it.
    _emit_well_ring(b, model, stair, ledger)
    _emit_landings(b, stair, flights, ledger)
    _emit_flight_edges(b, stair, flights, break_seg, ledger)
    _emit_risers(b, stair, flights, ledger)
    if break_seg is not None:
        _emit_break(b, stair, break_seg)
    cut_at = cut_z if cut_any else None
    path = travel_path(route, cut_at, occluder)
    boxes: list[Box] = []
    if path:
        boxes = emit_travel(b, stair, storey, path, route, travels)
        travels.append(path)
    band = _band(stair, flights, break_seg) if cut_any else None
    return band, boxes


# --------------------------------------------------------------- the pieces
def _emit_well_ring(b: SceneBuilder, model: ResolvedModel, stair,
                    ledger: _SegmentLedger) -> None:
    """A stair that perforates NO deck closes its own treads with its footprint ring.

    Every ``FloorOpening`` is drawn once by ``plan_voids``, on the plan of the deck it
    perforates, and that ring is what bounds a stair in a well. A within-storey step-down —
    ST-SG-PORCH, ST-BW-ENTRY, ST-G-SERVICE — cuts no deck and has no such ring, so its
    ``outline`` (built by ``dispatch._flight_footprint``) is drawn here instead. Without it
    those treads are a ladder of unconnected rungs.
    """
    if getattr(model.plan.by_tag(stair.tag), "floor_opening", None):
        return
    ring = [tuple(point) for point in stair.outline]
    b.add(Polyline(points=tuple(_in(point) for point in ring), closed=True,
                   layer="A-STAIR", lineweight=PROFILE, uid=stair.uid,
                   tag=f"{stair.tag}-well"))
    ledger.claim_ring(ring)


def _emit_landings(b: SceneBuilder, stair, flights: dict[str, list],
                   ledger: _SegmentLedger) -> None:
    """A landing's symbol is its OUTLINE, not its axis.

    The deck member is a board with a real width, and one centreline down the middle of a
    platform is the "weird split on the landing".
    """
    for key in sorted(flights):
        for member in flights[key]:
            if member.category != "landing":
                continue
            ring = member_footprint(member)
            b.add(Polyline(points=tuple(_in(point) for point in ring), closed=True,
                           layer="A-STAIR", lineweight=LIGHT, uid=stair.uid,
                           tag=member.child_key))
            ledger.claim_ring(ring)


def _flight_stations_drawn(stair, members: list) -> list[Segment]:
    """The drawn members' marks, plus the one station past the last of them.

    That trailing station is the edge the drawn run ends at — the next riser face, or (when
    the whole flight is drawn) the arrival nosing one going beyond the top one. It is what
    the side edges and the band run out to.
    """
    marks = [_mark(member) for member in members]
    if len(marks) >= 2:
        (a0, b0), (a1, b1) = marks[-2], marks[-1]
        marks.append(((2 * a1[0] - a0[0], 2 * a1[1] - a0[1]),
                      (2 * b1[0] - b0[0], 2 * b1[1] - b0[1])))
    return marks


def _emit_flight_edges(b: SceneBuilder, stair, flights: dict[str, list],
                       break_seg: Segment | None, ledger: _SegmentLedger) -> None:
    """The two sides of a tread flight, through the ``a`` and ``b`` ends of its drawn marks.

    The opening ring does not close a departing flight's sides: ST-M2S's treads run
    x 170.25"-212.625" while ``FO-M-STAIR`` ends at x 210". Only tread flights need this — a
    winder's wedges are already closed rings, and a landing is a rectangle. Deriving the
    edges from the DRAWN marks is also what keeps an occluded flight from leaving stray
    side lines behind a break.
    """
    for key in sorted(flights):
        members = flights[key]
        if members[0].category != "tread" or len(members) < 1:
            continue
        marks = _flight_stations_drawn(stair, members)
        end = break_seg if break_seg is not None and _between(marks, break_seg) \
            else marks[-1]
        run = [*marks[:-1], end]
        for index in (0, 1):
            points = [segment[index] for segment in run]
            if len(points) < 2:
                continue
            b.add(Polyline(points=tuple(_in(point) for point in points), layer="A-STAIR",
                           lineweight=LIGHT, uid=stair.uid,
                           tag=f"{members[0].child_key.rsplit('-', 1)[0]}-edge-{index}"))
            ledger.claim_ring(points, closed=False)


def _between(marks: list[Segment], segment: Segment) -> bool:
    """Does ``segment`` fall inside the span the drawn marks cover, along the run?"""
    if len(marks) < 2:
        return False
    (a0, _), (a1, _) = marks[0], marks[-1]
    dx, dy = a1[0] - a0[0], a1[1] - a0[1]
    run = math.hypot(dx, dy)
    if run < 1e-9:
        return False
    t = ((segment[0][0] - a0[0]) * dx + (segment[0][1] - a0[1]) * dy) / (run * run)
    return -1e-9 <= t <= 1.0 + 1e-9


def _emit_risers(b: SceneBuilder, stair, flights: dict[str, list],
                 ledger: _SegmentLedger) -> None:
    """One line per riser face, suppressed where a landing or a ring already drew it."""
    for key in sorted(flights):
        for member in flights[key]:
            if member.category == "landing":
                continue
            if member.plan_outline is not None:
                b.add(Polyline(points=tuple(_in(p) for p in member.plan_outline),
                               closed=True, layer="A-STAIR", lineweight=LIGHT,
                               uid=stair.uid, tag=member.child_key))
                ledger.claim_ring(list(member.plan_outline))
                continue
            a, c = _mark(member)
            if not ledger.claim(a, c):
                continue
            b.add(Polyline(points=(_in(a), _in(c)), layer="A-STAIR", lineweight=LIGHT,
                           uid=stair.uid, tag=member.child_key))


def _emit_break(b: SceneBuilder, stair, segment: Segment) -> None:
    """Two skewed diagonals across the flight where the cut plane crosses the walk.

    The drawing's statement that the object continues past the edge of the view. Both the
    lean and the pitch scale off the stair itself — the skew off the flight's width, the
    pitch off a going — so a wider flight gets a wider break and no printed constant
    appears. Emitted only when the cut actually excluded something.
    """
    (ax, ay), (bx, by) = segment
    nx, ny = bx - ax, by - ay
    width = math.hypot(nx, ny)
    if width < 1e-9:
        return
    # Travel is perpendicular to the riser face; either normal will do, since the pair of
    # diagonals is symmetric about the segment.
    ux, uy = -ny / width, nx / width
    pitch = _BREAK_LINE_PITCH_GOINGS * stair.going_depth_m
    skew = _BREAK_DIAGONAL_SKEW * width
    for index in (0, 1):
        along = index * pitch
        start = (ax + ux * (along - skew), ay + uy * (along - skew))
        end = (bx + ux * (along + skew), by + uy * (along + skew))
        b.add(Polyline(points=(_in(start), _in(end)), layer="A-STAIR",
                       lineweight=PROFILE, linetype="CONTINUOUS", uid=stair.uid,
                       tag=f"{stair.tag}-break-{index}"))


def _band(stair, flights: dict[str, list], break_seg: Segment | None) -> Polygon | None:
    """The plan area the DRAWN part of this stair occupies, for the flight under it.

    A quad from the first drawn mark to the break — never the union of the tread boards,
    whose top one oversails the break by its nosing.
    """
    pieces: list[Polygon] = []
    for members in flights.values():
        if members[0].category == "winder":
            pieces.extend(Polygon(member.plan_outline) for member in members
                          if member.plan_outline)
            continue
        if members[0].category == "landing":
            pieces.extend(Polygon(member_footprint(member)) for member in members)
            continue
        marks = _flight_stations_drawn(stair, members)
        end = break_seg if break_seg is not None and _between(marks, break_seg) \
            else marks[-1]
        pieces.append(Polygon([marks[0][0], marks[0][1], end[1], end[0]]))
    pieces = [piece for piece in pieces if piece.is_valid and not piece.is_empty]
    return unary_union(pieces) if pieces else None
