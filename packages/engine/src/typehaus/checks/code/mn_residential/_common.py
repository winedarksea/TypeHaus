"""Shared constructors and geometry helpers for the MN residential rules.

``rules.py`` grew to nine hundred lines covering seven unrelated articles, and every helper
in it was reachable only by importing the module that also registered thirteen checks. The
rules now live in topic modules (``egress``, ``stairs``, ``fall_protection``, ``alarms``,
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
from typehaus.quantities import inch
from typehaus.resolve.geometry import opening_center

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
    """Find windows on the room's bounding wall, not any window in the building.

    ``exterior_only`` decides whether an *interior* window counts, and the two callers of
    this helper genuinely want different answers — which is why it is a flag rather than a
    behaviour change.

    **R310 passes it True, and that is a safety fix, not a refinement.** The band below
    selects on proximity to the room boundary and nothing else, so before this flag existed
    an interior transom or a borrowed-light sash of adequate size was credited to a sleeping
    room as its *emergency escape opening*. R310.1's subject is an opening "opening directly
    into a public way, yard or court"; a window into the next room reaches none of those, and
    a false pass there is the one class of false pass this engine cannot afford. The exterior
    test is ``_wall_is_exterior`` — derived from what has modeled space on each side, never a
    tag prefix (see its own docstring).

    **R303.1 leaves it False, deliberately.** Borrowed light through an interior opening is
    not what R303.1's 8% is measured on either, but that rule already adjudicates its own
    Exception 1 and reports the shortfall in the finding text, so the conservative default
    there is to keep counting what the room can see and let the exception do the arguing. The
    day this house authors real borrowed-light glazing, that choice is worth revisiting on
    its own evidence — it is recorded here rather than left to be rediscovered.
    """
    if room is None or not room.clear_face:
        return []
    face = polygon_type(room.clear_face)
    # Wall axes normally lie just beyond the clear-face polygon.  The generous 12" band
    # reaches the wall's exterior centerline without accidentally claiming a window in a
    # neighboring room separated by an interior partition.
    boundary_band = face.boundary.buffer(inch(12).meters)
    # Built once per call, not once per opening: `_wall_is_exterior` rebuilds every room
    # polygon in the house when it is handed no index, and this loop asks it 80 times.
    rooms_by_storey = _rooms_by_storey(ctx) if exterior_only else None
    windows = []
    for opening in ctx.model.openings:
        if opening.is_door or opening.type_ref is None:
            continue
        wall = ctx.model.wall(opening.host_wall)
        if wall is None or wall.storey != room.storey:
            continue
        if exterior_only and not _wall_is_exterior(ctx, wall, rooms_by_storey):
            continue
        point = opening_center(wall, opening)
        if point is None:
            continue
        center = point_type(*point)
        if boundary_band.covers(center):
            windows.append(opening)
    return windows


def _foundation_footprint(ctx: CheckContext):
    """Largest foundation-wall enclosure (the primary building), or None if unavailable."""
    from shapely.geometry import LineString
    from shapely.ops import polygonize, unary_union

    segments = [LineString([wall.axis[0], wall.axis[1]])
                for wall in ctx.model.walls if wall.is_foundation]
    if not segments:
        return None
    faces = list(polygonize(unary_union(segments)))
    if not faces:
        return None
    merged = unary_union(faces)
    polys = list(merged.geoms) if merged.geom_type == "MultiPolygon" else [merged]
    return max(polys, key=lambda poly: poly.area)


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


# How far past a wall's own face to probe for a room on that side. Generous enough to clear
# lining and junction resolution, tight enough not to reach across a closet.
_WALL_SIDE_PROBE_M = 0.15


def _rooms_by_storey(ctx: CheckContext) -> dict[str, list]:
    from shapely.geometry import Polygon

    out: dict[str, list] = {}
    for room in ctx.model.rooms:
        if len(room.clear_face) >= 3:
            out.setdefault(room.storey, []).append((room, Polygon(room.clear_face)))
    return out


def _wall_is_exterior(ctx: CheckContext, wall, rooms_by_storey=None) -> bool:
    """Does this wall have modeled space on one side only?

    Derived, never named: there is no ``Assembly.exterior`` flag, and a tag-prefix list is
    the exact mistake the energy check had to unwind — one house's naming convention
    compiled into the engine. A wall with a room on both sides is a partition; a wall with a
    room on one side is the envelope. Foundation walls count as exterior outright: what is
    on the other side of them is earth.
    """
    from shapely.geometry import Point

    if wall.is_foundation:
        return True
    rooms = (rooms_by_storey if rooms_by_storey is not None
             else _rooms_by_storey(ctx)).get(wall.storey, ())
    if not rooms:
        return False
    (sx, sy), (ex, ey) = wall.axis
    run = ((ex - sx) ** 2 + (ey - sy) ** 2) ** 0.5
    if run <= 1e-9:
        return False
    nx, ny = -(ey - sy) / run, (ex - sx) / run  # unit normal
    reach = wall.thickness_m / 2.0 + _WALL_SIDE_PROBE_M
    sides = [False, False]
    for t in (0.25, 0.5, 0.75):
        mx, my = sx + (ex - sx) * t, sy + (ey - sy) * t
        for index, sign in enumerate((1.0, -1.0)):
            probe = Point(mx + nx * reach * sign, my + ny * reach * sign)
            if any(poly.covers(probe) for _room, poly in rooms):
                sides[index] = True
    return sides[0] != sides[1]


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
