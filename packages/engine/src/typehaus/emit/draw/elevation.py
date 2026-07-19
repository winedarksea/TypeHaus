"""Orthographic exterior elevations derived from resolved walls, openings, and roofs
(M3, → Permit-ready plan set Phase 5: grade profile, material callouts, vertical dims).
"""

from __future__ import annotations

from typehaus.emit.draw.scene import (
    ArchDimension,
    Leader,
    NamedPoint,
    Polyline,
    Scene,
    SceneBuilder,
    Symbol,
    Text,
)
from typehaus.resolve.model import ResolvedModel, ResolvedWall

_M_TO_IN = 39.37007874015748
_FACING = {"north", "south", "east", "west"}
_CAPTURE_BAND_M = 3.048  # 10'
_EXTEND_M = 0.6096  # 24"


def build_elevation(model: ResolvedModel, facing: str) -> Scene:
    """Project the exterior wall lines of each storey into one cardinal elevation.

    Selecting an extreme parallel wall *per storey* preserves the house, garage, and
    freestanding garden rather than collapsing the whole site to one global outline.
    Interior partitions cannot be extrema when an exterior perimeter is modeled.
    """
    facing = facing.lower()
    if facing not in _FACING:
        raise ValueError(f"unknown elevation facing {facing!r}")
    b = SceneBuilder(name=f"elevation-{facing}", units="in")
    selected = _facade_walls(model, facing)
    for wall in selected:
        _emit_wall(b, model, wall, facing)
    for roof in model.roofs:
        _emit_roof_profile(b, roof, facing)
    edge_u = _emit_grade_profile(b, model, facing, selected)
    _emit_material_callouts(b, model, selected, facing, edge_u)
    _emit_vertical_dim_string(b, model, facing, edge_u)
    b.add(Text(anchor=(0, _label_z(model)), content=f"{facing.upper()} ELEVATION",
               height=5.0, align="left"))
    return b.build()


def _facade_walls(model: ResolvedModel, facing: str) -> list[ResolvedWall]:
    horizontal = facing in {"north", "south"}
    candidate_by_storey: dict[str, list[ResolvedWall]] = {}
    for wall in model.walls:
        (x0, y0), (x1, y1) = wall.axis
        parallel = abs(y1 - y0) < 1e-6 if horizontal else abs(x1 - x0) < 1e-6
        if parallel:
            candidate_by_storey.setdefault(wall.storey, []).append(wall)
    selected: list[ResolvedWall] = []
    use_max = facing in {"north", "east"}
    for walls in candidate_by_storey.values():
        coordinates = [((wall.axis[0][1] + wall.axis[1][1]) / 2 if horizontal
                        else (wall.axis[0][0] + wall.axis[1][0]) / 2) for wall in walls]
        extreme = max(coordinates) if use_max else min(coordinates)
        selected.extend(wall for wall, coordinate in zip(walls, coordinates)
                        if abs(coordinate - extreme) < 1e-6)
    return selected


def _u(point: tuple[float, float], facing: str) -> float:
    return point[0] if facing in {"north", "south"} else point[1]


def _emit_wall(b: SceneBuilder, model: ResolvedModel, wall: ResolvedWall, facing: str) -> None:
    start_u, end_u = _u(wall.axis[0], facing), _u(wall.axis[1], facing)
    bottom = wall.z0_m
    top_start = wall.top_z0_m if wall.top_z0_m is not None else wall.z1_m
    top_end = wall.top_z1_m if wall.top_z1_m is not None else wall.z1_m
    points = tuple((u * _M_TO_IN, z * _M_TO_IN) for u, z in (
        (start_u, bottom), (end_u, bottom), (end_u, top_end), (start_u, top_start),
    ))
    b.add(Polyline(points=points, layer="A-WALL", closed=True, lineweight=0.35,
                   uid=wall.uid, tag=wall.tag))
    for opening in (item for item in model.openings if item.host_wall == wall.tag):
        length = max(1e-9, abs(end_u - start_u))
        direction = 1 if end_u >= start_u else -1
        center = start_u + direction * opening.center_along_m
        half = opening.width_m / 2
        sill, head = wall.z0_m + opening.sill_m, wall.z0_m + opening.sill_m + opening.height_m
        opening_points = tuple((u * _M_TO_IN, z * _M_TO_IN) for u, z in (
            (center - half, sill), (center + half, sill), (center + half, head), (center - half, head),
        ))
        if abs(center - start_u) <= length + 1e-6:
            b.add(Polyline(points=opening_points, layer="A-GLAZ", closed=True,
                           lineweight=0.25, uid=opening.uid, tag=opening.tag))


def _emit_roof_profile(b: SceneBuilder, roof, facing: str) -> None:
    horizontal_projection = facing in {"north", "south"}
    projects_slope = ((roof.ridge_direction == "y" and horizontal_projection)
                      or (roof.ridge_direction == "x" and not horizontal_projection))
    coordinates = [point[0] if horizontal_projection else point[1] for point in roof.footprint]
    lo, hi = min(coordinates), max(coordinates)
    if projects_slope and roof.form == "gable":
        profile = ((lo, roof.eave_z_m), ((lo + hi) / 2, roof.ridge_z_m), (hi, roof.eave_z_m))
    elif roof.form == "shed":
        profile = ((lo, roof.eave_z_m), (hi, roof.ridge_z_m))
    else:
        profile = ((lo, roof.eave_z_m), (hi, roof.eave_z_m))
    b.add(Polyline(points=tuple((u * _M_TO_IN, z * _M_TO_IN) for u, z in profile),
                   layer="A-ROOF", lineweight=0.5, uid=roof.uid, tag=roof.tag))


def _label_z(model: ResolvedModel) -> float:
    tops = [roof.ridge_z_m for roof in model.roofs]
    return ((max(tops) if tops else 0.0) + 0.5) * _M_TO_IN


def _facade_extent(walls: list[ResolvedWall], facing: str) -> tuple[float, float]:
    us = [_u(p, facing) for wall in walls for p in wall.axis]
    return (min(us), max(us)) if us else (0.0, 0.0)


def _facade_depth(walls: list[ResolvedWall], facing: str) -> float:
    """The facade's own perpendicular (depth) coordinate — all extreme walls share it."""
    if not walls:
        return 0.0
    horizontal = facing in {"north", "south"}
    wall = walls[0]
    return ((wall.axis[0][1] + wall.axis[1][1]) / 2 if horizontal
            else (wall.axis[0][0] + wall.axis[1][0]) / 2)


def _emit_grade_profile(b: SceneBuilder, model: ResolvedModel, facing: str,
                        walls: list[ResolvedWall]) -> float:
    """Grade line interpolated from spot elevations within a 10' capture band of the
    facade, extended flat 24" beyond the facade; flat ``Site.grade`` fallback otherwise
    (decision 2). Returns the u-coordinate just past the facade — the material-callout
    and vertical-dimension sheet-edge reference."""
    site = model.plan.project.site
    horizontal = facing in {"north", "south"}
    lo_u, hi_u = _facade_extent(walls, facing)
    facade_depth = _facade_depth(walls, facing)

    captured: list[tuple[float, float]] = []
    for spot in site.spot_elevations:
        x, y = spot.position.xy_m
        depth = y if horizontal else x
        if abs(depth - facade_depth) <= _CAPTURE_BAND_M:
            u = x if horizontal else y
            captured.append((u, spot.elevation.meters))
    captured.sort(key=lambda item: item[0])
    deduped: list[tuple[float, float]] = []
    for u, z in captured:
        if deduped and abs(u - deduped[-1][0]) < 1e-6:
            continue  # nearest-in-band point already kept (sorted by u, first wins)
        deduped.append((u, z))

    if len(deduped) < 2:
        grade_z = site.grade.meters if site.grade is not None else 0.0
        points = [(lo_u - _EXTEND_M, grade_z), (hi_u + _EXTEND_M, grade_z)]
    else:
        def z_at(u: float) -> float:
            if u <= deduped[0][0]:
                return deduped[0][1]
            if u >= deduped[-1][0]:
                return deduped[-1][1]
            for (u0, z0), (u1, z1) in zip(deduped, deduped[1:]):
                if u0 <= u <= u1:
                    t = 0.0 if abs(u1 - u0) < 1e-9 else (u - u0) / (u1 - u0)
                    return z0 + t * (z1 - z0)
            return deduped[-1][1]

        sample_us = sorted({lo_u - _EXTEND_M, hi_u + _EXTEND_M,
                            *(u for u, _ in deduped if lo_u - _EXTEND_M <= u <= hi_u + _EXTEND_M)})
        points = [(u, z_at(u)) for u in sample_us]

    poly = tuple((u * _M_TO_IN, z * _M_TO_IN) for u, z in points)
    b.add(Polyline(points=poly, layer="L-SITE-GRAD", lineweight=0.7))
    _emit_grade_hatch(b, points)
    b.add(Text(anchor=(poly[0][0], poly[0][1] - 3.0), content="GRADE", height=2.5,
               layer="L-SITE-GRAD"))
    return hi_u + _EXTEND_M


def _emit_grade_hatch(b: SceneBuilder, points: list[tuple[float, float]]) -> None:
    """45° tick hatching below the grade line (the standard grade-hatch convention)."""
    if len(points) < 2:
        return
    tick_spacing_m = 0.6096  # 24"
    lo_u = points[0][0]
    hi_u = points[-1][0]
    u = lo_u
    while u <= hi_u:
        z = _interp(points, u)
        b.add(Polyline(points=((u * _M_TO_IN, z * _M_TO_IN),
                               ((u - 0.15) * _M_TO_IN, (z - 0.15) * _M_TO_IN)),
                       layer="L-SITE-GRAD", lineweight=0.25))
        u += tick_spacing_m


def _interp(points: list[tuple[float, float]], u: float) -> float:
    for (u0, z0), (u1, z1) in zip(points, points[1:]):
        if u0 <= u <= u1:
            t = 0.0 if abs(u1 - u0) < 1e-9 else (u - u0) / (u1 - u0)
            return z0 + t * (z1 - z0)
    return points[-1][1]


def _emit_material_callouts(b: SceneBuilder, model: ResolvedModel, walls: list[ResolvedWall],
                            facing: str, edge_u: float) -> None:
    """One Leader per distinct exterior assembly (layers[-1].material_ref), staggered at
    the sheet edge; one roof callout from ``roof.assembly``."""
    callout_u = edge_u + 1.0
    seen: set[str] = set()
    row = 0
    for wall in walls:
        if not wall.layers:
            continue
        material = wall.layers[-1].material_ref.upper()
        if material in seen:
            continue
        seen.add(material)
        anchor_u = _u(wall.axis[0], facing)
        anchor_z = wall.top_z1_m if wall.top_z1_m is not None else wall.z1_m
        to_z = anchor_z - row * 0.9
        row += 1
        b.add(Leader(
            anchor=NamedPoint(xy=(anchor_u * _M_TO_IN, anchor_z * _M_TO_IN), name=wall.tag),
            at=(anchor_u * _M_TO_IN, anchor_z * _M_TO_IN),
            to=(callout_u * _M_TO_IN, to_z * _M_TO_IN),
            text=material, layer="A-ANNO-TEXT",
        ))
    if model.roofs:
        mid_u = sum(_facade_extent(walls, facing)) / 2.0
        ridge_z = max(roof.ridge_z_m for roof in model.roofs)
        to_z = ridge_z - row * 0.9
        assembly = next(roof.assembly for roof in model.roofs).upper()
        b.add(Leader(
            anchor=NamedPoint(xy=(mid_u * _M_TO_IN, ridge_z * _M_TO_IN), name="roof"),
            at=(mid_u * _M_TO_IN, ridge_z * _M_TO_IN), to=(callout_u * _M_TO_IN, to_z * _M_TO_IN),
            text=assembly, layer="A-ANNO-TEXT",
        ))


def _emit_vertical_dim_string(b: SceneBuilder, model: ResolvedModel, facing: str,
                              edge_u: float) -> None:
    """Stacked vertical ArchDimensions between grade, each storey floor/top-of-plate,
    and the ridge, at the right margin — plus level-marker symbols + elevation labels."""
    site = model.plan.project.site
    grade_z = site.grade.meters if site.grade is not None else 0.0
    levels: dict[str, float] = {"GRADE": grade_z}
    for storey in sorted(model.plan.storeys, key=lambda s: s.elevation.meters):
        levels[f"{storey.tag.upper()} FLOOR"] = storey.elevation.meters
        storey_walls = [w for w in model.walls if w.storey == storey.tag]
        if storey_walls:
            levels[f"{storey.tag.upper()} T.O. PLATE"] = max(w.z1_m for w in storey_walls)
    if model.roofs:
        levels["RIDGE"] = max(roof.ridge_z_m for roof in model.roofs)

    dim_u = edge_u + 2.5
    ordered = sorted(levels.items(), key=lambda item: item[1])
    for (label0, z0), (label1, z1) in zip(ordered, ordered[1:]):
        if abs(z1 - z0) < 1e-6:
            continue
        b.add(ArchDimension(
            kind="linear",
            ends=(NamedPoint(xy=(dim_u * _M_TO_IN, z0 * _M_TO_IN), name=label0),
                  NamedPoint(xy=(dim_u * _M_TO_IN, z1 * _M_TO_IN), name=label1)),
            p0=(dim_u * _M_TO_IN, z0 * _M_TO_IN), p1=(dim_u * _M_TO_IN, z1 * _M_TO_IN),
            offset=6.0,
        ))
    for label, z in ordered:
        b.add(Symbol(name="level-marker", insert=(dim_u * _M_TO_IN, z * _M_TO_IN),
                     layer="A-ANNO-SYMB"))
        b.add(Text(anchor=((dim_u + 8.0) * _M_TO_IN, z * _M_TO_IN),
                   content=f"{label} EL. {_feet_inches_signed(z)}", height=2.5,
                   layer="A-ANNO-TEXT"))


def _feet_inches_signed(z_m: float) -> str:
    total_in = round(z_m * _M_TO_IN)
    sign = "-" if total_in < 0 else ""
    total_in = abs(total_in)
    return f"{sign}{total_in // 12}'-{total_in % 12}\""
