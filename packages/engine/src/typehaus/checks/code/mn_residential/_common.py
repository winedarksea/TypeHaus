"""Shared constructors and geometry helpers for the MN residential rules.

The rules live in topic modules (``egress``, ``stairs``, ``fall_protection``, ``alarms``,
``circulation``, ``fire_separation``, ``ventilation``, ``attic``); what they share lands
here.

Nothing in this module registers a check. The tri-state constructors are the contract that
matters: a rule that cannot evaluate reports UNKNOWN with the reason (#32), never a pass.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed, not_applicable, passed, unknown
from typehaus.checks.registry import CheckContext
from typehaus.findings import Finding
from typehaus.model.enums import Occupancy
from typehaus.resolve.room_openings import room_windows, rooms_by_storey, wall_is_exterior

#: R202's definition of habitable space — "a space in a building for living, sleeping, eating
#: or cooking" — whose very next sentence excludes bathrooms, toilet rooms, closets, halls,
#: storage and utility spaces. Every rule that says "habitable" takes this same subject
#: (R303.1 glazing, R305.1 ceiling height, R304's minimum areas), so it is defined once here
#: rather than re-typed per module, where the copies drift.
HABITABLE_OCCUPANCIES = frozenset({
    Occupancy.BEDROOM, Occupancy.LIVING, Occupancy.DINING, Occupancy.KITCHEN,
    Occupancy.MEDIA, Occupancy.OFFICE,
})

#: Square feet per square metre. Findings are read by people who think in feet.
SF_PER_M2 = 10.7639


# Thin, signature-preserving adapters over ``checks._authoring``: every call site in this
# package's topic modules (egress, stairs, alarms, ...) calls these three positionally as
# ``(cid, msg, code)`` / ``(cid, msg, tags, code)`` — a shape the shared constructors don't
# take directly (they put ``tags`` before ``code``, and ``code`` is optional there). Rather
# than touch the ~150 call sites across this package, these adapters keep the old shape and
# delegate the actual ``Finding(...)`` construction to the shared module.
def _pass(cid: str, msg: str, code: str) -> Finding:
    return passed(cid, msg, code=code)


def _fail(cid: str, msg: str, tags: tuple[str, ...], code: str) -> Finding:
    return failed(cid, msg, tags, code=code)


def _unknown(cid: str, reason: str, tags: tuple[str, ...], code: str) -> Finding:
    return unknown(cid, reason, tags, code=code)


def _na(cid: str, reason: str, tags: tuple[str, ...], code: str) -> Finding:
    return not_applicable(cid, reason, tags, code=code)


def _room_storey(ctx: CheckContext, room_tag: str):
    for storey in ctx.plan.storeys:
        if any(e.tag == room_tag for e in ctx.plan.storey_elements(storey.tag)):
            return storey
    return None


def _room_windows(ctx: CheckContext, room, point_type, polygon_type, *,
                  exterior_only: bool = False) -> list:
    """Re-export of ``resolve.room_openings.room_windows`` — see there for the reasoning.

    Lives in ``resolve`` because ``resolve_rooms`` needs it to total a room's glazing, and
    ``checks`` imports ``resolve``, never the reverse. The signature matches the R310 and
    R303.1 callers; ``point_type`` and ``polygon_type`` were only ever a way of deferring the
    shapely import and are now ignored.
    """
    del point_type, polygon_type
    return room_windows(ctx.model, room, exterior_only=exterior_only)


def _rooms_by_storey(ctx: CheckContext) -> dict[str, list]:
    return rooms_by_storey(ctx.model)


def _wall_is_exterior(ctx: CheckContext, wall, rooms_by_storey_index=None) -> bool:
    return wall_is_exterior(ctx.model, wall, rooms_by_storey_index)


#: Fraction of an enclosure that must be floored by an open excavation before the
#: enclosure is read as a hole rather than a building. The sunken court reads 0.93 and the
#: house and garage read 0.00, so anything in the middle of that range would do; a simple
#: majority is the one that needs no tuning.
_EXCAVATION_MAJORITY = 0.5

#: Plan tolerances for "this wall stands on that foundation line" (metres).
_ON_LINE_TOL_M = 0.0127      # 1/2" off the foundation run's line
_MIN_BEARING_OVERLAP_M = 0.3048  # and sharing at least a foot of it


def _bridging_walls(foundation: list, walls: list) -> list:
    """Walls collinear with, and bearing on, a foundation run — the ones that span its gaps.

    A stem gapped under a vehicle door is still a building: the wall above runs across the
    opening on its header. Such a wall adds nothing where the foundation already is, and
    closes the ring where it is not. Collinearity plus a real overlap keeps a freestanding
    wall that merely touches a foundation line from inventing a ring.
    """
    from shapely.geometry import LineString

    bridges = []
    for wall in walls:
        a, b = wall.axis[0], wall.axis[1]
        line = LineString([a, b])
        for run in foundation:
            p, q = run.coords[0], run.coords[-1]
            dx, dy = q[0] - p[0], q[1] - p[1]
            span = (dx * dx + dy * dy) ** 0.5
            if span < 1e-9:
                continue
            off = [abs((pt[0] - p[0]) * dy - (pt[1] - p[1]) * dx) / span for pt in (a, b)]
            if max(off) <= _ON_LINE_TOL_M and \
                    line.buffer(_ON_LINE_TOL_M).intersection(run).length >= \
                    _MIN_BEARING_OVERLAP_M:
                bridges.append(line)
                break
    return bridges


def _foundation_enclosures(ctx: CheckContext) -> list:
    """Every foundation-wall enclosure a **building** stands in, largest first.

    R401.3 asks that the ground fall away from "the building". A site with one house has
    one such ring; this one has three — the house at 1,296 sf, the detached garage at 576,
    and the sunken court's retaining run at 562 — and until 2026-09-10 the helper here kept
    only the largest and silently discarded the other two. The garage had therefore never
    been graded by anything, and no station had ever been authored around it.

    Two rings are returned here, not three. **An open excavation is not a building**: the
    sunken court is ground the site drains *into* by design, and asking grade to fall away
    from a retaining wall is asking the court to fill. That is earned from positive
    evidence rather than assumed from a tag — ``resolve.site_earth.open_excavation_floors``
    already identifies a below-grade slab with no conditioned room over it, and an
    enclosure a majority floored by one is a hole.

    A foundation run gapped under a door is closed by the wall standing on it
    (``_bridging_walls``): catlin's garage stem is an open U under its overhead door since
    2026-09-23, and read off the stem alone the garage stopped being graded at all.

    Empty when no foundation walls resolve, or when they close no ring at all. The caller
    distinguishes the two, because "no foundation" and "a foundation we could not
    reconstruct" are different UNKNOWNs.
    """
    from shapely.geometry import LineString
    from shapely.ops import polygonize, unary_union

    from typehaus.resolve.site_earth import open_excavation_floors

    segments = [LineString([wall.axis[0], wall.axis[1]])
                for wall in ctx.model.walls if wall.is_foundation]
    if not segments:
        return []
    segments += _bridging_walls(
        segments, [wall for wall in ctx.model.walls if not wall.is_foundation])
    faces = list(polygonize(unary_union(segments)))
    if not faces:
        return []
    merged = unary_union(faces)
    polys = list(merged.geoms) if merged.geom_type == "MultiPolygon" else [merged]
    excavations = [polygon for _tag, polygon, _z in open_excavation_floors(ctx.model)]
    if excavations:
        dug = unary_union(excavations)
        polys = [poly for poly in polys
                 if poly.intersection(dug).area <= _EXCAVATION_MAJORITY * poly.area]
    return sorted(polys, key=lambda poly: poly.area, reverse=True)


def _nearest_enclosure(enclosures: list, point) -> tuple:
    """``(enclosure, distance to its boundary)`` for the ring ``point`` stands against.

    **The foundation a station is graded against is the nearest one.** A point between two
    buildings cannot slope away from both, and the code's own exception for drains and
    swales exists because of it; naming the nearer foundation is what a grading plan does
    and what the far side being the outlet means. On this site the rule only ever moves one
    station — the garage's south-west yard point, 2'-0" from the garage and 9'-0" from the
    house — and both readings pass there.
    """
    best, best_distance = None, None
    for enclosure in enclosures:
        distance = enclosure.exterior.distance(point)
        if best_distance is None or distance < best_distance:
            best, best_distance = enclosure, distance
    return best, best_distance


def _foundation_footprint(ctx: CheckContext):
    """Largest foundation-wall enclosure (the primary building), or None if unavailable."""
    enclosures = _foundation_enclosures(ctx)
    return enclosures[0] if enclosures else None


# A storey counts as below grade once its finished floor sits this far under the site's
# average-grade datum. Two feet, not zero: a slab-on-grade main floor is normally authored a
# few inches below the grade datum, and calling that a basement would put every house's
# ground floor under R310.1's below-grade escape rule.
_BELOW_GRADE_MARGIN_M = 0.6


def _storey_is_below_grade(ctx: CheckContext, storey) -> bool | None:
    """Is this storey's floor below the site's average grade?

    ``None`` — not ``False`` — when the site states no grade datum. The caller must report
    UNKNOWN in that case: "we do not know where grade is" is not "this storey is above it",
    and R310.1 and E3902 both change answer on the distinction.
    """
    grade = ctx.plan.project.site.grade
    if grade is None:
        return None
    return storey.elevation.meters + _BELOW_GRADE_MARGIN_M <= grade.meters


def _min_clear_width(ring, *, ceiling_m: float = 4.0) -> float | None:
    """The narrowest clear width across a room polygon, in metres.

    Binary search on the erosion ``polygon.buffer(-w / 2)``: the largest ``w`` that still
    leaves something behind is the widest corridor the polygon admits everywhere, which for
    a hallway is exactly R311.6's measurement. ``None`` for a degenerate ring.
    """
    from shapely.geometry import Polygon

    if ring is None or len(ring) < 3:
        return None
    polygon = Polygon(ring)
    if not polygon.is_valid or polygon.area <= 1e-9:
        return None
    lo, hi = 0.0, ceiling_m
    if not polygon.buffer(-lo / 2.0).is_empty and polygon.buffer(-hi / 2.0).is_empty:
        for _ in range(40):  # 4 m / 2^40 — far past any dimension the code cares about
            mid = (lo + hi) / 2.0
            if polygon.buffer(-mid / 2.0).is_empty:
                hi = mid
            else:
                lo = mid
    return lo
