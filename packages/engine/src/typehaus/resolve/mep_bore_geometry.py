"""Where a run's leg meets a wall's framing members: the shapely half of the bore rules.

:mod:`typehaus.resolve.mep_bores` holds the scalar limits (R502.8.1, R602.6, R602.6.1);
this module measures what a run would cut — which members, at what station and z, and how
much of the diameter each gives up — so the check and the router read one geometry.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from typehaus.quantities import M_PER_IN

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import FramedMember, ResolvedWall


#: The member categories a run's leg can be measured against. A ``header`` is here and was
#: not until 2026-09-19: the list was the reason a run over a door met nothing at all, and
#: silence is the one verdict a member carrying an opening's whole tributary load may not
#: get. It is graded by ``mep_bores.header_bore``, which is NOT R602.6 — see that function.
_CUTTABLE_CATEGORIES = ("stud", "king", "jack", "cripple", "plate", "sill", "header")


@dataclass(frozen=True)
class MemberCut:
    """One place a run's leg meets one wall member, and what it would have to cut.

    ``diameter_in`` is the hole the run's outside needs; ``through_in`` is how much of it
    the member gives up here — a 4" duct 0.25" above a header's top takes a 1.75" NOTCH, not
    a 4" bore. Equal wherever the run passes wholly inside the z band, the ordinary case.

    ``station`` is where the run MEETS the member, never the member's own centroid: a
    header's centroid is its midspan, and a hole's cost to a bending member is a question
    about where along the span it sits.
    """

    member_key: str
    category: str  # "stud" | "plate" | "king" | "jack" | "cripple" | "sill" | "header"
    profile: str
    station: tuple[float, float]
    z_m: float
    diameter_in: float
    through_in: float
    #: The authored opening this member was framed around, where it has one — a header
    #: naming its door, so a consumer can reach that opening's own hole chart.
    opening_tag: str | None = None
    #: Distance along a HORIZONTAL member from the crossing to its nearer END, metres. A
    #: hole chart is indexed on distance from the BEARING, which is this less the bearing
    #: inset; the inset belongs to whoever knows the opening's width, not to this reading.
    from_end_m: float = 0.0
    #: The member's own length, metres — the other half of that arithmetic.
    member_length_m: float = 0.0
    #: Clear wood between the hole's edge and the NEARER of the member's two z faces. The
    #: depth half of a chart's hole zone is stated against exactly this.
    edge_clear_in: float = 0.0
    #: The member's z band, metres: a VERTICAL member's own length (``member_length_m`` is
    #: plan length, 0 for a stud). What tells a 5 3/4" cripple from a stud.
    member_height_m: float = 0.0
    #: A HORIZONTAL member whose both long faces the run's envelope meets: it crosses the
    #: plate's whole width, so full thickness there severs it (``top_plate_cut``).
    spans_width: bool = False


def leg_crossings(wall: ResolvedWall, a: tuple[float, float], b: tuple[float, float],
                  za: float, zb: float, radius_m: float) -> list[MemberCut]:
    """Every stud and plate of ``wall`` this one leg of a run would have to cut.

    **The actual stud positions, never "the wall is empty".** A staggered wall is the case
    this exists for: its studs alternate between two rows, so a run down the middle of a
    2x6 plate misses half of them and bores the other half, and a rule applied to "the
    wall" cannot express that. ``ResolvedWall.members`` already carries each stud's own
    plan point and its ``orient``, so the question is answered against the framing that
    resolved rather than against a spacing.

    A member is crossed when the run's inflated plan line meets the member's own plan
    rectangle AND the run's elevation there is inside the member's z band. Both, for the
    same reason ``mep_crossings.leg_crossings`` needs both: a run passing over a wall's
    plate is not boring it. **The station is the meeting, not the member** — the run's axis
    where it lies inside it. A stud's centroid IS that point, so nothing moved there; a
    header's is its midspan, which was a wrong z and a station no hole chart can be read at.
    """
    from shapely.geometry import LineString, Point

    from typehaus.resolve.framing.profiles import cross_section

    axis = Point(a) if a == b else LineString([a, b])
    swept = axis.buffer(radius_m)
    out: list[MemberCut] = []
    for member in wall.members:
        if member.category not in _CUTTABLE_CATEGORIES:
            continue
        section = cross_section(member.profile)
        shape = member_plan_shape(member, section)
        if shape is None:
            continue
        overlap = swept.intersection(shape)
        if overlap.is_empty:
            continue
        # The axis, falling back to the envelope where only the envelope grazes: an
        # envelope clipped by the member's END drags its own centroid inward.
        axis_in = axis.intersection(shape)
        centre = (overlap if axis_in.is_empty else axis_in).centroid
        top = member.z1_m if member.z1_m is not None else wall.z1_m
        if a == b:
            # A riser occupies its whole z range at one plan point; its midpoint is not
            # where it meets anything (DU-ERV-RISER-EXH's fell 0.9" above W-M-MECH-S).
            low, high = min(za, zb), max(za, zb)
            if high + radius_m < member.z0_m or low - radius_m > top:
                continue
            z = min(max((member.z0_m + top) / 2.0, low), high)
        else:
            z = _z_at(a, b, za, zb, (centre.x, centre.y))
            if not (member.z0_m - radius_m <= z <= top + radius_m):
                continue
        length_m = ((member.p1[0] - member.p0[0]) ** 2
                    + (member.p1[1] - member.p0[1]) ** 2) ** 0.5
        from_end_m = min(
            ((centre.x - member.p0[0]) ** 2 + (centre.y - member.p0[1]) ** 2) ** 0.5,
            ((centre.x - member.p1[0]) ** 2 + (centre.y - member.p1[1]) ** 2) ** 0.5)
        out.append(MemberCut(member_key=member.child_key, category=member.category,
                             profile=member.profile, station=(centre.x, centre.y),
                             z_m=z, diameter_in=2.0 * radius_m / M_PER_IN,
                             through_in=_through_in(a, b, za, zb, z, radius_m,
                                                    member.z0_m, top),
                             opening_tag=member.opening_tag,
                             from_end_m=from_end_m, member_length_m=length_m,
                             edge_clear_in=max(0.0, min(z - radius_m - member.z0_m,
                                                        top - z - radius_m)) / M_PER_IN,
                             member_height_m=top - member.z0_m,
                             spans_width=_spans_width(swept, member, section)))
    return out


def _spans_width(swept: Any, member: FramedMember, section: Any) -> bool:
    """Whether ``swept`` meets both long faces of a horizontal member's plan rectangle."""
    from shapely.geometry import LineString

    if member.p0 == member.p1:
        return False
    (x0, y0), (x1, y1) = member.p0, member.p1
    length = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    half = max(section.width_m, section.depth_m) / 2.0
    nx, ny = -(y1 - y0) / length * half, (x1 - x0) / length * half
    return all(swept.intersects(LineString([(x0 + s * nx, y0 + s * ny),
                                            (x1 + s * nx, y1 + s * ny)]))
               for s in (1.0, -1.0))


def _through_in(a: tuple[float, float], b: tuple[float, float], za: float, zb: float,
                z: float, radius_m: float, z0_m: float, top_m: float) -> float:
    """How deep into the member's z band the run's own envelope reaches (→ ``MemberCut``).

    A RISER — a leg whose rise beats its plan travel — crosses the member the long way and
    takes its whole diameter out of it. A level leg takes only the part of its OD band
    inside the member, which clipped at the top is a notch off the top face.
    """
    diameter_in = 2.0 * radius_m / M_PER_IN
    plan_m = ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
    if abs(zb - za) > plan_m:
        return diameter_in
    inside = min(z + radius_m, top_m) - max(z - radius_m, z0_m)
    if inside >= 2.0 * radius_m - 1e-9:  # contained: snap, or ulps read as a notch
        return diameter_in
    return max(0.0, inside) / M_PER_IN


def member_plan_shape(member: FramedMember, section: Any) -> Any:
    """A framing member's own plan rectangle, from its axis and its section.

    A stud is a vertical: ``p0 == p1``, and its ``orient`` is the wall direction, so the
    rectangle is its 1 1/2" thickness ALONG the wall by its 5 1/2" depth ACROSS it. A plate
    is horizontal and its axis is the wall run, so the rectangle is its length by its width.
    """
    from shapely.geometry import LineString, Polygon

    if section is None:
        return None
    if member.p0 == member.p1:
        orient = member.orient or (1.0, 0.0)
        norm = (orient[0] ** 2 + orient[1] ** 2) ** 0.5 or 1.0
        ux, uy = orient[0] / norm, orient[1] / norm
        nx, ny = -uy, ux
        # `width_m` is the member's 1 1/2" face and `depth_m` its 5 1/2" — the convention
        # `cross_section` documents — so along the wall is the width and across is the depth.
        half_along, half_across = section.width_m / 2.0, section.depth_m / 2.0
        cx, cy = member.p0
        corners = [(cx + ux * sa * half_along + nx * sc * half_across,
                    cy + uy * sa * half_along + ny * sc * half_across)
                   for sa, sc in ((1, 1), (1, -1), (-1, -1), (-1, 1))]
        return Polygon(corners)
    return LineString([member.p0, member.p1]).buffer(
        max(section.width_m, section.depth_m) / 2.0, cap_style=2)


def _z_at(a: tuple[float, float], b: tuple[float, float], za: float, zb: float,
          point: tuple[float, float]) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    span = dx * dx + dy * dy
    if span <= 0:
        return (za + zb) / 2.0
    t = max(0.0, min(1.0, ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / span))
    return za + t * (zb - za)
