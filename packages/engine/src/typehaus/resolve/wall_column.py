"""The drain column: washed stone against a bedded wall's soil face (``DrainColumn``).

Plan footprint: the dug outline (``earthwork_outline``) buffered out by the column width with
a mitre join, less the outline — a band that fills outside corners by itself and never
reaches a face the outline swallows (the house's court-facing walls). Each bed claims the
band square to its wall's exterior face, in uid order so an inside corner is never counted
twice; the outside-corner squares left over then go, again in uid order, to a bed whose wall
they touch. Other beds' footprints are cut out: a column never stands in another bed.

Section: beside the bed the column drops to the excavation floor (``stone_z0_m``), which puts
the exterior tile run fully in stone; over the footing's own ledge it starts on the footing
top. The top is ``cap_below_grade`` under the wall's strip grade, or ``height`` over ``z1``.
"""

from __future__ import annotations

import math
from typing import Any

from shapely.geometry import JOIN_STYLE, LineString, Point, Polygon

from typehaus.findings import Finding, Severity
from typehaus.resolve.earthwork_outline import dug_outline, host_wall, polygon_of, wall_body
from typehaus.resolve.model import ResolvedFootingBedding, ResolvedModel, ResolvedSolid
from typehaus.resolve.model_earthwork import ResolvedWallColumn
from typehaus.resolve.overlay import difference, intersection, union_all
from typehaus.resolve.site_earth import grade_strip, strip_grade_elevation_m

CATEGORY = "drain_column"
_MITRE = JOIN_STYLE.mitre
_PROBE_M = 0.05
_EPS_M = 1e-3
_MIN_AREA_M2 = 1e-4


def _exterior_face(wall, body, outline) -> tuple[LineString, tuple[float, float]] | None:
    """The wall body's face on the soil side of ``outline``, and the outward unit normal."""
    (x0, y0), (x1, y1) = wall.axis
    run = math.hypot(x1 - x0, y1 - y0)
    if run <= 1e-9:
        return None
    ux, uy = (x1 - x0) / run, (y1 - y0) / run
    nx, ny = -uy, ux
    pts = list(body.exterior.coords) if isinstance(body, Polygon) else [
        c for g in body.geoms for c in g.exterior.coords]
    along = [(px - x0) * ux + (py - y0) * uy for px, py in pts]
    across = [(px - x0) * nx + (py - y0) * ny for px, py in pts]
    s0, s1, mid = min(along), max(along), (min(along) + max(along)) / 2
    for t, sign in ((max(across), 1.0), (min(across), -1.0)):
        offset = t + sign * _PROBE_M
        if not outline.contains(Point(x0 + ux * mid + nx * offset, y0 + uy * mid + ny * offset)):
            face = LineString([(x0 + ux * s0 + nx * t, y0 + uy * s0 + ny * t),
                               (x0 + ux * s1 + nx * t, y0 + uy * s1 + ny * t)])
            return face, (nx * sign, ny * sign)
    return None


def soil_face(model: ResolvedModel, bed: ResolvedFootingBedding, outline: Any
              ) -> tuple[Any, Any, LineString, tuple[float, float]] | None:
    """``(wall, body, face line, outward normal)`` of the bed's wall on the soil side."""
    wall = host_wall(model, bed)
    body = wall_body(wall) if wall is not None else None
    face = _exterior_face(wall, body, outline) if body is not None else None
    return (wall, body, *face) if face is not None else None


def parts(geometry: Any) -> list[Polygon]:
    if geometry is None or geometry.is_empty:
        return []
    if isinstance(geometry, Polygon):
        return [geometry] if geometry.area > _MIN_AREA_M2 else []
    return [g for g in getattr(geometry, "geoms", ()) if isinstance(g, Polygon)
            and g.area > _MIN_AREA_M2]


def footing_top(model: ResolvedModel, bed: ResolvedFootingBedding) -> float:
    host = next((s for s in model.solids if s.tag == bed.host
                 and s.category in ("footing", "pad")), None)
    return host.z1_m if host is not None else bed.z1_m


def resolve_wall_columns(model: ResolvedModel) -> list[Finding]:
    authored = {el.tag: el.wall_column for el in model.plan.all_elements()
                if getattr(el, "wall_column", None) is not None}
    beds = sorted((b for b in model.footing_beddings if b.tag in authored), key=lambda b: b.uid)
    if not beds:
        return []
    outline = dug_outline(model)
    findings: list[Finding] = []
    if outline is None:
        return [Finding(severity=Severity.WARN, check_id="integrity.drain_column",
                        message="drain columns authored but no dug outline found",
                        element_tags=tuple(b.tag for b in beds))]
    faces: dict[str, tuple] = {}
    for bed in beds:
        face = soil_face(model, bed, outline)
        if face is None:
            findings.append(Finding(severity=Severity.WARN, check_id="integrity.drain_column",
                                    message=f"{bed.tag}'s drain column has no soil face",
                                    element_tags=(bed.tag,)))
            continue
        faces[bed.tag] = face
    claimed: dict[str, Any] = {}
    taken: list[Any] = []
    for bed in beds:  # pass 1: the band square to each face
        if bed.tag not in faces:
            continue
        _wall, _body, line, outward = faces[bed.tag]
        width = authored[bed.tag].width.meters
        band = difference(outline.buffer(width, join_style=_MITRE), outline)
        strip = grade_strip(line, outward, width + _PROBE_M)
        piece = intersection(strip, band)
        if taken:
            piece = difference(piece, union_all(taken))
        claimed[bed.tag] = piece
        taken.append(piece)
    for bed in beds:  # pass 2: outside-corner squares the faces left over
        if bed.tag not in faces:
            continue
        width = authored[bed.tag].width.meters
        band = difference(outline.buffer(width, join_style=_MITRE), outline)
        corner = difference(intersection(band, faces[bed.tag][1].buffer(
            width + _PROBE_M, join_style=_MITRE)), union_all(taken))
        if corner.is_empty:
            continue
        claimed[bed.tag] = union_all([claimed[bed.tag], corner])
        taken.append(corner)
    for bed in beds:
        if bed.tag in claimed:
            findings.extend(_emit(model, bed, authored[bed.tag], claimed[bed.tag], outline,
                                  faces[bed.tag], claimed))
    return findings


def _emit(model, bed, spec, plan, outline, face, claimed) -> list[Finding]:
    # Beside the beds the column drops to this bed's stone floor; over a bed (its own
    # footing's ledge, a neighbour's heel) it starts on that bed's footing top instead. A bed
    # founded higher than this one stands on the backfill, so the column stops short of it.
    beds = [(b, p) for b in model.footing_beddings if (p := polygon_of(b.outline)) is not None]
    above = [p for b, p in beds if b.stone_z0_m > bed.z1_m]
    beds = [(b, p) for b, p in beds if b.stone_z0_m <= bed.z1_m]
    if above:
        plan = difference(plan, union_all(above))
    main = difference(plan, union_all([p for _b, p in beds])) if beds else plan
    pieces = [(bed.stone_z0_m, p) for p in parts(main)]
    for other, footprint in beds:
        pieces += [(footing_top(model, other), p) for p in parts(intersection(plan, footprint))]
    _wall, _body, line, outward = face
    grade, _ = strip_grade_elevation_m(model, grade_strip(line, outward))
    top = (bed.z1_m + spec.height.meters if spec.height is not None
           else grade - spec.cap_below_grade.meters)
    solids = []
    for z0, part in pieces:
        if top - z0 <= 1e-6:
            continue
        index = len(solids)
        solids.append(ResolvedSolid(
            uid=f"{bed.uid}-DC-{index:02d}", tag=f"{bed.tag}-DC-{index + 1}", storey=bed.storey,
            category=CATEGORY, outline=list(part.exterior.coords)[:-1], z0_m=z0, z1_m=top,
            voids=tuple(list(r.coords)[:-1] for r in part.interiors), material=spec.material_ref))
    if not solids:
        return [Finding(severity=Severity.WARN, check_id="integrity.drain_column",
                        message=f"{bed.tag}'s drain column resolves to nothing",
                        element_tags=(bed.tag,))]
    model.solids.extend(solids)
    volume = sum(Polygon(s.outline, s.voids).area * (s.z1_m - s.z0_m) for s in solids)
    whole = union_all([Polygon(s.outline, s.voids) for s in solids])
    # Fabric: the faces that meet soil (not the outline or another column) + the top.
    neighbours = [g for tag, g in claimed.items() if tag != bed.tag and not g.is_empty]
    keep_off = union_all([outline, *neighbours]).buffer(_EPS_M)
    boundary = whole.boundary.difference(keep_off)
    floor = min(s.z0_m for s in solids)
    soil_height = top - floor
    fabric = (boundary.length * soil_height + whole.area) if spec.geotextile else 0.0
    origin, outward = face[2].coords[0], face[3]

    def reach(points) -> float:
        return max((x - origin[0]) * outward[0] + (y - origin[1]) * outward[1] for x, y in points)

    own = polygon_of(bed.outline)
    beyond = (reach([p for s in solids for p in s.outline])
              - (reach(own.exterior.coords) if own is not None else 0.0))
    model.wall_columns.append(ResolvedWallColumn(
        bed_tag=bed.tag, wall_tag=face[0].tag, aggregate=spec.aggregate,
        width_m=spec.width.meters, z0_m=floor, top_m=top, grade_m=grade, volume_m3=volume,
        geotextile_m2=fabric, plan_area_m2=whole.area, beyond_footing_m=beyond,
        footing_top_m=footing_top(model, bed)))
    return []

