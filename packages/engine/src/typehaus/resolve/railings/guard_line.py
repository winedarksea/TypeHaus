"""Where a guard actually stands in plan, and which of its end posts belong to another guard.

``Railing.path`` is the edge a guard protects. A surface guard stands on it; a fascia guard
stands outboard of it, its posts in brackets on the fascia face (ESR-3485 Fig. 10). Posts,
rails, infill and the checks that measure them all read :func:`guard_line`, so the drawn
guard and the graded one are the same line.
"""

from __future__ import annotations

import math

from typehaus.findings import Finding, Result, Severity
from typehaus.model.structure import Post, Railing
from typehaus.quantities import inch
from typehaus.resolve.geometry import Vec, length, sub
from typehaus.resolve.railings.parts import railing_type

#: Mounts whose guard draws its own posts (the others hang on a wall or another guard).
_POSTLESS_MOUNTS = frozenset({"wall", "post"})
#: A shared end must land on the other guard's station to this.
_SHARED_POST_TOL_M = inch(1 / 16).meters


def guard_line_offset_m(library, el: Railing) -> float:
    """How far outboard (right-hand normal) of ``path`` the posts stand: 0 off a fascia."""
    product = railing_type(library, el)
    if (el.mount != "fascia" or product is None or product.fascia_post_offset is None
            or el.fascia_face_offset is None):
        return 0.0
    return el.fascia_face_offset.meters + product.fascia_post_offset.meters


def offset_path(path: list[Vec], distance: float) -> list[Vec]:
    """``path`` moved ``distance`` along each segment's right-hand normal, mitred at corners."""
    if abs(distance) < 1e-12 or len(path) < 2:
        return list(path)
    normals: list[Vec] = []
    for a, b in zip(path[:-1], path[1:], strict=True):
        run = length(sub(b, a))
        dx, dy = ((b[0] - a[0]) / run, (b[1] - a[1]) / run) if run > 1e-12 else (0.0, 0.0)
        normals.append((dy, -dx))
    out = [(path[0][0] + normals[0][0] * distance, path[0][1] + normals[0][1] * distance)]
    for i in range(1, len(path) - 1):
        na, nb = normals[i - 1], normals[i]
        denom = 1.0 + na[0] * nb[0] + na[1] * nb[1]
        k = distance / denom if denom > 1e-9 else distance  # a reversal: no mitre exists
        out.append((path[i][0] + (na[0] + nb[0]) * k, path[i][1] + (na[1] + nb[1]) * k))
    out.append((path[-1][0] + normals[-1][0] * distance,
                path[-1][1] + normals[-1][1] * distance))
    return out


def guard_line(library, el: Railing) -> list[Vec]:
    """The plan line the guard's posts and rails stand on."""
    return offset_path([p.xy_m for p in el.path], guard_line_offset_m(library, el))


def guard_post_stations(library, el: Railing) -> list[Vec]:
    """Every post station of ``el`` (shared ends included), off its :func:`guard_line`."""
    from typehaus.resolve.railings.frame import MIN_POST_SPACING_M, railing_post_stations

    line = guard_line(library, el)
    if len(line) < 2:
        return []
    return railing_post_stations(line, max(el.post_spacing.meters, MIN_POST_SPACING_M))


def shared_post_ends(plan, el: Railing, stations: list[Vec]) -> tuple[set[int], list[Finding]]:
    """Station indices whose post another guard draws, and a WARN for each that does not.

    An end naming ``start_post_ref``/``end_post_ref`` draws no post only when the named guard
    draws one on that very station, or the named column's face is there; otherwise this
    guard keeps its own and says why.
    """
    skipped: set[int] = set()
    findings: list[Finding] = []
    if not stations:
        return skipped, findings
    for index, ref in ((0, el.start_post_ref), (len(stations) - 1, el.end_post_ref)):
        if ref is None:
            continue
        other = plan.by_tag(ref) if plan is not None else None
        station = stations[index]
        if isinstance(other, Post):  # a column is this end's post (→ .column_ends)
            from typehaus.resolve.railings.column_ends import column_face_distance

            if column_face_distance(other, station) <= _SHARED_POST_TOL_M:
                skipped.add(index)
                continue
            findings.append(Finding(
                severity=Severity.WARN, check_id="geometry.railing_shared_post_missing",
                message=(f"railing {el.tag} ends on column {ref}, but ({station[0]:.3f}, "
                         f"{station[1]:.3f}) m is not on its face; its own post is drawn"),
                element_tags=(el.tag, ref), result=Result.FAIL))
            continue
        # Two guards deferring to each other would leave the station bare.
        if (isinstance(other, Railing) and other.mount not in _POSTLESS_MOUNTS
                and el.tag not in (other.start_post_ref, other.end_post_ref)
                and any(math.dist(station, s) <= _SHARED_POST_TOL_M
                        for s in guard_post_stations(plan.library, other))):
            skipped.add(index)
            continue
        findings.append(Finding(
            severity=Severity.WARN, check_id="geometry.railing_shared_post_missing",
            message=(f"railing {el.tag} ends on {ref}'s post, but {ref} draws no post at "
                     f"({station[0]:.3f}, {station[1]:.3f}) m; its own post is drawn"),
            element_tags=(el.tag, ref), result=Result.FAIL))
    return skipped, findings
