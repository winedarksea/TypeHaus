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
