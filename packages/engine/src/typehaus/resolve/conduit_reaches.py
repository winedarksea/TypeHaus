"""Where a raceway lies: in a wall, indoors, under a building, in earth, or in the open.

The one reading ``checks/mep/conduit_burial.py`` and ``conduit_damage.py`` share (NEC 300.6,
300.7, 300.8, 300.9). A run is walked every ``STEP_M`` along its authored path, with the
z the run authors at each vertex (a schematic run has none and is skipped by the callers).
Each sample is classed from the model, never from a name:

* ``in_wall``: inside a wall's plan footprint and z range (a cast-in or sleeved crossing);
* ``under_building``: inside a roof's bearing footprint, below a slab on grade;
* ``indoor``: inside that footprint otherwise;
* ``earth``: outside every building and under the surface, which is the top of the highest
  slab over the run, else the local grade (``site_earth.local_grade_elevation_m``);
* ``open``: outside, above the surface.

Cover is NEC Note 1: top of the run to the top of the surface. Grade is a design elevation,
not a survey. Heavy imports are local so a leaf can import this module cheaply.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from shapely.geometry import LineString, Point, Polygon

from typehaus.resolve.model import ResolvedConduitRun, ResolvedModel
from typehaus.resolve.pipe_sections import raceway_outside_diameter_m

STEP_M = 0.0762  # 3 in.
#: A slab this far above grade still covers a run in the ground (a walk cast 1 in. proud).
_SLAB_ABOVE_GRADE_M = 0.3
_WALL_BUFFER_M = 0.16  # half of the thickest exterior wall, to reach its outer face


@dataclass(frozen=True)
class Sample:
    x: float
    y: float
    z: float  # centreline
    top: float  # top of the run
    kind: str  # in_wall | under_building | indoor | earth | open
    surface_z: float | None = None  # earth only
    surface_tag: str | None = None  # the slab over it, or None for grade
    slab_thickness_in: float | None = None
    slab_edge_clear_m: float | None = None  # slab edge to the run's near side, plan
    host: str | None = None  # wall tag, or building tag
    building: str | None = None  # in_wall only: the building the wall stands in, if any
    vertical: bool = False


@dataclass(frozen=True)
class Site:
    """Per-model geometry, built once."""

    walls: tuple[tuple[str, Polygon, float, float], ...]
    buildings: tuple[tuple[str, Polygon], ...]
    slabs: tuple[tuple[Any, Polygon], ...]
    floors: list
    heated: Any
    grade_m: float


def build_site(model: ResolvedModel) -> Site:
    from typehaus.resolve.roof_geometry import roof_bearing_footprint, roof_bearing_walls
    from typehaus.resolve.site_earth import (
        heated_floor_footprint,
        open_excavation_floors,
        site_grade_elevation_m,
    )

    walls = []
    for wall in model.walls:
        if len(wall.axis) >= 2 and wall.thickness_m > 0:
            shape = LineString(wall.axis).buffer(wall.thickness_m / 2, cap_style=2)
            walls.append((wall.tag, shape, wall.z0_m, wall.z1_m))
    buildings = []
    for roof in model.roofs:
        # A canopy stands on beams, not walls: it shelters, it is not a building.
        if not any(b.wall is not None for b in roof_bearing_walls(model, roof)):
            continue
        ring = roof_bearing_footprint(model, roof)
        if ring is not None and len(ring) >= 3:
            buildings.append((roof.tag, Polygon(ring).buffer(_WALL_BUFFER_M)))
    slabs = []
    for solid in model.solids:
        if solid.category == "slab" and len(solid.outline) >= 3:
            shape = Polygon(solid.outline)
            if shape.is_valid and shape.area > 0:
                slabs.append((solid, shape))
    return Site(tuple(walls), tuple(buildings), tuple(slabs), open_excavation_floors(model),
                heated_floor_footprint(model), site_grade_elevation_m(model))


def _z_at(run: ResolvedConduitRun, index: int, t: float) -> float:
    return run.z_m[index] + (run.z_m[index + 1] - run.z_m[index]) * t


def samples(model: ResolvedModel, run: ResolvedConduitRun, site: Site) -> list[Sample]:
    """Every STEP_M along an authored-elevation run; ``[]`` for a schematic one."""
    from typehaus.resolve.site_earth import local_grade_elevation_m

    if run.z_m is None or len(run.z_m) != len(run.path):
        return []
    radius = raceway_outside_diameter_m(run.trade_size_m, run.material) / 2
    out: list[Sample] = []
    for i in range(len(run.path) - 1):
        (x0, y0), (x1, y1) = run.path[i], run.path[i + 1]
        plan_len = math.hypot(x1 - x0, y1 - y0)
        z_len = abs(run.z_m[i + 1] - run.z_m[i])
        length = plan_len if plan_len > 1e-9 else z_len
        if length < 1e-9:
            continue
        count = max(1, math.ceil(length / STEP_M))
        for k in range(count + 1):
            t = k / count
            x, y, z = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, _z_at(run, i, t)
            heading = ((x1 - x0) / plan_len, (y1 - y0) / plan_len) if plan_len > 1e-9 else None
            out.append(_classify(model, site, x, y, z, radius, heading, local_grade_elevation_m))
    return out


def _classify(model, site: Site, x, y, z, radius, heading, local_grade) -> Sample:
    point = Point(x, y)
    vertical = heading is None
    top = z + radius
    for tag, shape, z0, z1 in site.walls:
        if z0 - 1e-6 <= z <= z1 + 1e-6 and shape.contains(point):
            inside = next((b for b, bshape in site.buildings if bshape.contains(point)), None)
            return Sample(x, y, z, top, "in_wall", host=tag, vertical=vertical,
                          building=inside)
    for tag, shape in site.buildings:
        if shape.contains(point):
            over = [s for s, p in site.slabs if s.z1_m <= site.grade_m + _SLAB_ABOVE_GRADE_M
                    and s.z1_m > top and p.contains(point)]
            return Sample(x, y, z, top, "under_building" if over else "indoor", host=tag,
                          vertical=vertical)
    covering = [(s, p) for s, p in site.slabs
                if s.z1_m > top and s.z1_m <= site.grade_m + _SLAB_ABOVE_GRADE_M
                and p.contains(point)]
    if covering:
        slab, shape = max(covering, key=lambda item: item[0].z1_m)
        edge = _lateral_clear(shape, x, y, heading, radius)
        return Sample(x, y, z, top, "earth", slab.z1_m, slab.tag,
                      (slab.z1_m - slab.z0_m) / 0.0254, edge, vertical=vertical)
    ring = [(x - .05, y - .05), (x + .05, y - .05), (x + .05, y + .05), (x - .05, y + .05)]
    grade, _ = local_grade(model, ring, floors=site.floors, sheltered_by=site.heated)
    if top < grade:
        return Sample(x, y, z, top, "earth", grade, None, vertical=vertical)
    return Sample(x, y, z, top, "open", vertical=vertical)


def _lateral_clear(shape: Polygon, x: float, y: float, heading, radius: float) -> float | None:
    """Plan distance from the run's near side to the slab edge, ACROSS the run. Where a run
    enters or leaves under an edge, the slab cannot extend past that end, so only the sides
    count (Table 300.7(A): the slab extends 6 in. beyond the installation)."""
    if heading is None:
        return None
    nx, ny = -heading[1], heading[0]
    reach = 2.0
    best = reach
    for sign in (1, -1):
        probe = LineString([(x, y), (x + sign * nx * reach, y + sign * ny * reach)])
        hit = shape.boundary.intersection(probe)
        if not hit.is_empty:
            best = min(best, Point(x, y).distance(hit))
    return best - radius
