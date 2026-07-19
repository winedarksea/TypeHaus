"""Orthographic exterior elevations derived from resolved walls, openings, and roofs (M3)."""

from __future__ import annotations

from typehaus.emit.draw.scene import Polyline, Scene, SceneBuilder, Text
from typehaus.resolve.model import ResolvedModel, ResolvedWall

_M_TO_IN = 39.37007874015748
_FACING = {"north", "south", "east", "west"}


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
