"""Wall ledgers replace backed ladder portions; crossing walls cut real lumber."""

from __future__ import annotations

import math
from dataclasses import replace

from shapely.geometry import LineString, Point, Polygon

from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.framing.tables import member_actual
from typehaus.resolve.overlay import difference, union_all
from typehaus.resolve.soffits import (
    CONTACT_TOLERANCE_M,
    SOFFIT_LINING_THICKNESS,
    wall_footprint,
)


def _pieces(shape):
    if shape.geom_type == "LineString":
        if shape.length > CONTACT_TOLERANCE_M:
            yield shape
    else:
        for part in getattr(shape, "geoms", ()):
            yield from _pieces(part)


def coordinate_soffit_support(model, soffit, members):
    """Keep bottom nailers tight to supporting walls, screwed through finish to studs.

    The exposed box keeps its ladders. A backed portion needs only its bottom ledger;
    carrying a second vertical frame alongside wall studs would obstruct the same cavity
    without supporting any additional board.
    """
    lining = SOFFIT_LINING_THICKNESS.meters
    walls = [(wall, wall_footprint(wall)) for wall in model.walls
             if wall.storey == soffit.storey]
    xmin = min(x for x, _ in soffit.outline)
    xmax = max(x for x, _ in soffit.outline)
    ymin = min(y for _, y in soffit.outline)
    ymax = max(y for _, y in soffit.outline)
    long_x = xmax - xmin >= ymax - ymin
    along = 0 if long_x else 1
    across = 1 - along
    contacts = []
    for contact in soffit.wall_contacts:
        start = soffit.outline[contact.edge_index]
        end = soffit.outline[(contact.edge_index + 1) % len(soffit.outline)]
        if abs(end[across] - start[across]) > CONTACT_TOLERANCE_M:
            continue
        edge_length = math.dist(start, end)
        stations = [start[along] + station * (end[along] - start[along]) / edge_length
                    for station in (contact.start_m, contact.end_m)]
        contacts.append((start[across], min(stations), max(stations), contact.wall_ref))

    rail_profile = getattr(soffit.framing, "plate_member", None) or soffit.framing.member
    rail_depth = member_actual(rail_profile)[1] * 0.0254
    coordinated = []
    for member in members:
        is_rail = member.child_key.startswith("soffit-plate-")
        is_stud = member.child_key.startswith("soffit-stud-")
        if is_rail or is_stud:
            face = min((ymin, ymax) if long_x else (xmin, xmax),
                       key=lambda value: abs(value - member.p0[across]))
            backed = [contact for contact in contacts if abs(contact[0] - face)
                      < CONTACT_TOLERANCE_M]
            if is_stud:
                if any(low <= member.p0[along] <= high for _, low, high, _ in backed):
                    continue
            elif backed:
                lo, hi = sorted((member.p0[along], member.p1[along]))
                cuts = sorted({lo, hi} | {max(lo, min(hi, value))
                                         for _, low, high, _ in backed for value in (low, high)})
                for index, (start, end) in enumerate(zip(cuts, cuts[1:], strict=False)):
                    if end - start <= CONTACT_TOLERANCE_M:
                        continue
                    wall_ref = next((tag for _, low, high, tag in backed
                                     if low <= (start + end) / 2 <= high), None)
                    if wall_ref and "-top-" in member.child_key:
                        continue
                    p0, p1 = list(member.p0), list(member.p1)
                    p0[along], p1[along] = start, end
                    if wall_ref:
                        direction = 1 if member.p0[across] > face else -1
                        p0[across] -= direction * lining
                        p1[across] -= direction * lining
                    coordinated.append(replace(
                        member, p0=tuple(p0), p1=tuple(p1), length_m=end - start,
                        child_key=f"{member.child_key}-{index:03d}",
                        connection=(f"soffit-ledger:screw-to-studs:{wall_ref}"
                                    if wall_ref else member.connection)))
                continue
        # Rungs butt to the moved ledger rather than stopping at its old inner face.
        if member.child_key.startswith(("soffit-rung-", "soffit-end-")):
            p0, p1 = list(member.p0), list(member.p1)
            for point in (p0, p1):
                for face, low, high, _tag in contacts:
                    if (low <= point[along] <= high
                            and abs(abs(point[across] - face) - lining - rail_depth)
                            < CONTACT_TOLERANCE_M):
                        point[across] += lining if point[across] < face else -lining
            member = replace(member, p0=tuple(p0), p1=tuple(p1),
                             length_m=math.dist(p0, p1))
        coordinated.append(member)

    # Crossing walls interrupt the lumber; trim it at their actual finished faces.
    result = []
    for member in coordinated:
        obstacles = [shape for wall, shape in walls
                     if wall.z0_m < member.z1_m and wall.z1_m > member.z0_m]
        if not obstacles:
            result.append(member)
            continue
        footprint = Polygon(member_footprint(member)[0])
        blocked = union_all(obstacles)
        if footprint.intersection(blocked).area < CONTACT_TOLERANCE_M ** 2:
            result.append(member)
            continue
        if math.dist(member.p0, member.p1) <= CONTACT_TOLERANCE_M:
            continue
        line = LineString((member.p0, member.p1))
        # Project the actual footprint overlap onto the stock's axis. A centreline-only
        # clip misses walls touching just the side of a member; projecting cuts the whole
        # stock clear without inventing an ungraded notch in its cross-section.
        overlap = footprint.intersection(blocked)
        polygons = ([overlap] if overlap.geom_type == "Polygon"
                    else [part for part in getattr(overlap, "geoms", ())
                          if part.geom_type == "Polygon"])
        intervals = []
        for polygon in polygons:
            stations = [line.project(Point(point)) for point in polygon.exterior.coords]
            low, high = min(stations), max(stations)
            if high - low > CONTACT_TOLERANCE_M:
                intervals.append(LineString((line.interpolate(low), line.interpolate(high))))
        remaining = difference(line, union_all(intervals))
        for index, piece in enumerate(_pieces(remaining)):
            p0, p1 = tuple(piece.coords[0]), tuple(piece.coords[-1])
            if line.project(Point(p1)) < line.project(Point(p0)):
                p0, p1 = p1, p0
            result.append(replace(member, p0=p0, p1=p1, length_m=piece.length,
                                  child_key=f"{member.child_key}-cut-{index:03d}"))
    return result
