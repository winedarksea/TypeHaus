"""One flat bearing seat under a mixed concrete/wood deck (→ 12 §checks/structural).

A deck that is cast concrete over part of its plan and joists over the rest has two stacks
that have to agree twice: at the top, where the two finished floors meet, and at the bottom,
where both land on the same pour. The top is guarded by an explicit ``Slab.top_elevation``
and by ``integrity.slab_thickness`` holding the build-up to a layer boundary. This check
guards the bottom, which nothing else does.

The physical rule is one sentence. *The deck's soffit and the underside of the wood bay's
mudsill are the same plane, and every concrete wall in the storey below tops out on it.*
Nothing steps, nothing is packed out, the forms are set once. This check is that sentence:

* the deck soffit within :data:`_SEAT_TOL_IN` of the pour it lands on;
* the joist soffit above that seat by a mudsill's thickness and no more, so the joists are
  demonstrably on a plate rather than inside the pour or floating over it;
* the two finished planes within :data:`_FINISH_TOL_IN`.

The finish tolerance is the loose one, deliberately. ``FloorSystem``/``Room``
``floor_finish`` is a bare material tag with no thickness (``model/floors.py``), so the
model cannot see the plank on the plywood; what it can see is the subfloor top against the
cap top, and the gap between those two is *meant* to be roughly the finish thickness. A
quarter inch is what that buys — enough to catch a cover or a subfloor that changed, too
loose to catch a plank swapped for a thicker one. Giving finishes a real thickness is the
change that tightens it.

Scope is derived, not tagged: a ``Slab`` and a ``FloorSystem`` on the same storey whose
outlines are **edge-adjacent** — they share a boundary and do not overlap. That is what a
mixed deck is. A slab lying ON a joist field (the breezeway's plank) overlaps and is not
this; a slab on another storey is not this either.
"""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity, not_applicable
from typehaus.model.floors import FloorSystem, Slab
from typehaus.model.project import Storey
from typehaus.model.structure import FoundationWall
from typehaus.quantities import M_PER_IN
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import ResolvedSolid

# One flat seat means one plane. A sixteenth is the tolerance a form crew works to and the
# tolerance the arithmetic upstream is authored in.
_SEAT_TOL_IN = 0.0625
# The finished planes, loose by the thickness of a floor finish the model cannot hold.
_FINISH_TOL_IN = 0.25
# A joist soffit sits this far above the seat: a mudsill plus its gasket. Below the lower
# bound the joists are in the pour; above the upper one they are on something this check
# cannot see, which is exactly as bad.
_PLATE_MIN_IN = 0.5
_PLATE_MAX_IN = 2.5
# Two outlines are adjacent if they share this much boundary. A foot — long enough that a
# corner touch is not a shared edge.
_SHARED_EDGE_M = 0.3048


def _fail(msg: str, tags: tuple[str, ...], hint: str | None = None) -> Finding:
    return Finding(severity=Severity.ERROR, check_id="structural.mixed_deck_bearing_seat",
                   message=msg, element_tags=tags, result=Result.FAIL, fix_hint=hint)


def _adjacent(a: list[tuple[float, float]], b: list[tuple[float, float]]) -> bool:
    from shapely.geometry import Polygon

    pa, pb = Polygon(a), Polygon(b)
    if not (pa.is_valid and pb.is_valid):
        return False
    if pa.intersection(pb).area > 1e-6:
        return False  # one lies on the other — not a mixed deck, a slab on a floor
    return bool(pa.buffer(1e-3).intersection(pb).area / 1e-3 >= _SHARED_EDGE_M)


@check(Tier.STRUCTURAL, "structural.mixed_deck_bearing_seat")
def mixed_deck_bearing_seat(ctx: CheckContext) -> list[Finding]:
    out: list[Finding] = []
    solids = {s.tag: s for s in ctx.model.solids if s.category == "slab" and s.tag}
    for storey in ctx.plan.storeys:
        elements = list(ctx.plan.storey_elements(storey.tag))
        slabs = [e for e in elements if isinstance(e, Slab) and e.tag in solids]
        floors = [e for e in elements if isinstance(e, FloorSystem) and e.outline]
        if not slabs or not floors:
            continue
        for slab in slabs:
            ring = [p.xy_m for p in slab.outline]
            for floor in floors:
                other = [p.xy_m for p in floor.outline]
                if len(ring) < 3 or len(other) < 3 or not _adjacent(ring, other):
                    continue
                out.extend(_grade(ctx, storey, slab, solids[slab.tag], floor))
    return out


def _grade(ctx: CheckContext, storey: Storey, slab: Slab, solid: ResolvedSolid,
           floor: FloorSystem) -> list[Finding]:
    tags = (slab.tag, floor.tag)
    seats = _seats(ctx, floor)
    if not seats:
        return [Finding(
            severity=Severity.WARN, check_id="structural.mixed_deck_bearing_seat",
            message=(f"UNKNOWN — {floor.tag} names no FoundationWall in its joist "
                     f"bearing_refs, so there is no pour to compare {slab.tag}'s soffit to"),
            element_tags=tags, result=Result.UNKNOWN)]
    out: list[Finding] = []
    lo, hi = min(seats.values()), max(seats.values())
    if (hi - lo) / M_PER_IN > _SEAT_TOL_IN:
        stepped = ", ".join(f"{tag} {z / M_PER_IN:+.4g}\"" for tag, z in sorted(seats.items()))
        out.append(_fail(
            f"the walls {floor.tag} bears on do not top out on one plane — {stepped}",
            (*tags, *sorted(seats)),
            "one flat bearing seat: give every wall in the storey below the same top"))
    seat = lo
    soffit = solid.z0_m
    if abs(soffit - seat) / M_PER_IN > _SEAT_TOL_IN:
        out.append(_fail(
            f"deck {slab.tag}'s soffit is {soffit / M_PER_IN:+.4g}\" but the bearing seat "
            f"beside it is {seat / M_PER_IN:+.4g}\" — {abs(soffit - seat) / M_PER_IN:.4g}\" "
            f"of step in a plane that is poured flat",
            tags,
            "retune the deck's form + cover so its soffit reaches the seat, or move the seat"))
    joist_soffit = storey.elevation.meters - cross_section(floor.joists.member).depth_m
    plate_in = (joist_soffit - seat) / M_PER_IN
    if not (_PLATE_MIN_IN <= plate_in <= _PLATE_MAX_IN):
        out.append(_fail(
            f"{floor.tag}'s joists soffit {plate_in:+.4g}\" off the bearing seat — a mudsill "
            f"and its gasket are {_PLATE_MIN_IN:g}\"-{_PLATE_MAX_IN:g}\", so the joists are "
            + ("inside the pour" if plate_in < _PLATE_MIN_IN else "not on it"),
            tags,
            "the joists bear on the framed wall's own mudsill, laid on the pour"))
    subfloor = floor.subfloor.thickness.meters if floor.subfloor is not None else 0.0
    wood_top = storey.elevation.meters + subfloor
    if abs(solid.z1_m - wood_top) / M_PER_IN > _FINISH_TOL_IN:
        out.append(_fail(
            f"deck {slab.tag} tops at {solid.z1_m / M_PER_IN:+.4g}\" against {floor.tag}'s "
            f"subfloor at {wood_top / M_PER_IN:+.4g}\" — "
            f"{abs(solid.z1_m - wood_top) / M_PER_IN:.4g}\" is more than a floor finish",
            tags,
            "the cast cover is what tunes this plane; the seat below it is not free to move"))
    if not out:
        out.append(Finding(
            severity=Severity.WARN, check_id="structural.mixed_deck_bearing_seat",
            message=(f"{slab.tag} and {floor.tag} share one bearing seat at "
                     f"{seat / M_PER_IN:+.4g}\" — deck soffit {soffit / M_PER_IN:+.4g}\", "
                     f"joists on {plate_in:.4g}\" of plate above it, finished planes "
                     f"{solid.z1_m / M_PER_IN:+.4g}\" and {wood_top / M_PER_IN:+.4g}\""),
            element_tags=tags, result=Result.PASS))
    return out


def _seats(ctx: CheckContext, floor: FloorSystem) -> dict[str, float]:
    """Top of every concrete wall the floor's joists declare bearing on."""
    seats: dict[str, float] = {}
    for ref in floor.joists.bearing_refs:
        if not isinstance(ctx.plan.by_tag(ref), FoundationWall):
            continue
        wall = ctx.model.wall(ref)
        if wall is not None:
            seats[ref] = wall.z1_m
    return seats


# --- the bearing grid ---------------------------------------------------------
#
# ``resolve/floors.py`` cuts a joist at its bearing ref's **node axis** — the line the wall
# is authored on, never the line its structure actually occupies. For a plain centred wall
# those are the same. For a wall carrying ``alignment=face(...)`` they are not, and the
# offset is usually a hand-written half of the thickness: catlin's W-B-CS is
# ``face("concrete-ext", offset=inch(-6))`` on a 12" pour, which re-centres the concrete on
# the x=18' bearing grid exactly — and would slide it 2" off that grid the day anyone thinned
# the wall to 8" without touching the number.
#
# The failure is silent and it is not a small one: the joists still resolve, still span, and
# still land where the model draws them, on a line the concrete is no longer under. So the
# rule is not "the node axis is the band's axis" — a perimeter wall on ``face("concrete-ext")``
# legitimately keeps its whole pour inboard of the node line — but "the joists that stop at
# this line have something to sit on", which is a bearing length, on the side they come from.
_MIN_BEARING_IN = 1.5


@check(Tier.INTEGRITY, "integrity.floor_bearing_grid")
def floor_bearing_grid(ctx: CheckContext) -> list[Finding]:
    from typehaus.resolve.framing.solver import _structure_polygon

    out: list[Finding] = []
    for storey in ctx.plan.storeys:
        for floor in ctx.plan.storey_elements(storey.tag):
            if not isinstance(floor, FloorSystem) or not floor.joists.bearing_refs:
                continue
            along_x = floor.joists.direction == "x"
            axis_i = 0 if along_x else 1
            lines: list[tuple[float, str, tuple[float, float]]] = []
            for ref in floor.joists.bearing_refs:
                wall = ctx.model.wall(ref)
                if wall is None:
                    continue  # a Beam ref, or an unresolved tag — integrity.floor_bearing's
                (p0, p1) = wall.axis
                coord = (p0[axis_i] + p1[axis_i]) / 2.0
                band = _structure_polygon(wall)
                if band is None or len(band) < 3:
                    continue
                span = [p[axis_i] for p in band]
                lines.append((coord, ref, (min(span), max(span))))
            if len(lines) < 2:
                continue
            coords = sorted({round(c, 6) for c, _, _ in lines})
            tol = _MIN_BEARING_IN * M_PER_IN
            graded = 0
            for coord, ref, (lo, hi) in lines:
                index = coords.index(round(coord, 6))
                below = index > 0
                above = index < len(coords) - 1
                short = []
                if below and lo > coord - tol + 1e-9:
                    short.append(f"{(coord - lo) / M_PER_IN:.4g}\" on the near side")
                if above and hi < coord + tol - 1e-9:
                    short.append(f"{(hi - coord) / M_PER_IN:.4g}\" on the far side")
                graded += 1
                if not short:
                    continue
                out.append(Finding(
                    severity=Severity.ERROR, check_id="integrity.floor_bearing_grid",
                    message=(f"{floor.tag}'s joists are cut at {ref}'s node axis "
                             f"({coord / 0.3048:.4g}') but its structure runs "
                             f"{lo / 0.3048:.4g}'..{hi / 0.3048:.4g}' — "
                             + " and ".join(short)
                             + f", against {_MIN_BEARING_IN:g}\" of bearing"),
                    element_tags=(floor.tag, ref), result=Result.FAIL,
                    fix_hint=("a bearing ref's alignment offset is what moves its structure "
                              "off its own node line; the span boundary does not follow")))
            if graded and not any(f.element_tags[0] == floor.tag for f in out):
                out.append(Finding(
                    severity=Severity.WARN, check_id="integrity.floor_bearing_grid",
                    message=(f"{floor.tag} cuts its joists on {graded} bearing line(s), each "
                             f"with at least {_MIN_BEARING_IN:g}\" of its wall's structure "
                             f"under the cut"),
                    element_tags=(floor.tag,), result=Result.PASS))
    return out


# --- end bearing, by what the member actually is ------------------------------
#
# ``floor_bearing_grid`` above asks whether there is *structure* under the line the joists
# are cut at. This asks how much of it each end actually sits on, against what the member
# needs. IRC R502.6 wants 1 1/2" on wood for a sawn joist; the other two numbers are the
# fabricator's, not the code's — an I-joist bears on its web and its maker asks 1 3/4", an
# open-web truss lands on its bottom chord over a block and BCSI/SBCA ask 3". Grading all
# three at 1 1/2" passed catlin's x=18' line, where a centreline split gave a truss and an
# I-joist 2 3/4" each. It is now split 3 1/2" / 2" (``params/second_deck.py``).
_MIN_SEAT_IN = {"floor_truss": 3.0, "i_joist": 1.75}
_MIN_SEAT_DEFAULT_IN = 1.5
_SEAT_TOL_M = 1e-4


@check(Tier.INTEGRITY, "integrity.floor_end_bearing")
def floor_end_bearing(ctx: CheckContext) -> list[Finding]:
    """Each deck's two end seats, against the bearing its own member needs."""
    out: list[Finding] = []
    graded = 0
    for floor in ctx.model.floors:
        system = ctx.plan.by_tag(floor.tag)
        ends = floor.ends
        if ends is None or not isinstance(system, FloorSystem):
            continue
        member = system.joists.member
        shape = cross_section(member).shape
        needed = _MIN_SEAT_IN.get(shape, _MIN_SEAT_DEFAULT_IN)
        for label, seat in (("low", ends.seat_lo), ("high", ends.seat_hi)):
            if seat is None:
                continue  # a cantilevered tip seats on nothing, and says so by having no seat
            graded += 1
            got_in = seat / M_PER_IN
            if seat >= needed * M_PER_IN - _SEAT_TOL_M:
                continue
            out.append(Finding(
                severity=Severity.ERROR, check_id="integrity.floor_end_bearing",
                message=(f"{floor.tag}'s {member} takes {got_in:.4g}\" of bearing at its "
                         f"{label} end, against the {needed:g}\" it needs"),
                element_tags=(floor.tag,), result=Result.FAIL,
                fix_hint=("author JoistSpec.end_bearing to take the share this deck needs "
                          "off a shared plate, or widen the bearing wall")))
    if not graded:
        return [not_applicable(
            "integrity.floor_end_bearing",
            "no deck in this building frames joists onto a resolvable bearing — every "
            "FloorSystem either has no bearing refs or cantilevers both ends", ())]
    if not out:
        out.append(Finding(
            severity=Severity.WARN, check_id="integrity.floor_end_bearing",
            message=(f"{graded} deck end(s) seated, each on at least the bearing its own "
                     f"member needs (sawn {_MIN_SEAT_DEFAULT_IN:g}\", I-joist "
                     f"{_MIN_SEAT_IN['i_joist']:g}\", floor truss "
                     f"{_MIN_SEAT_IN['floor_truss']:g}\")"),
            element_tags=(), result=Result.PASS))
    return out
