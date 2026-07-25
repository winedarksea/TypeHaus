"""Where the roof meets the walls it lands on, and where it stops in mid-air (→ B2).

Two closures the roof plane and the wall prisms leave open between them:

* **wall → roof closure.** A wall prism stops at its top plate. Over a raised-heel truss the
  deck plane sits a heel above that plate, and at a gable end the plane climbs to the ridge,
  so the sheathing/rainscreen/cladding band between the wall top and the roof underside is
  simply missing — daylight at the heel and an exposed truss at the gable. Every exterior
  wall under a roof gets that band carried up to the roof underside here. A wall that already
  rakes to the roof (``ToRoof``) has no gap and produces nothing.
* **eave / rake trim.** The fascia boards and soffit panel declared by ``Roof.eave_trim``,
  derived along all four roof edges. Deriving rather than authoring keeps the trim on the
  roof plane through a raised-heel lift instead of drifting below it.

Both are emitted as ``FramedMember`` records on the roof: unlike ``ResolvedSolid`` (a plan
prism), a member carries different elevations at each end, which is what a raked gable
closure and a sloped rake fascia need.
"""

from __future__ import annotations

import math
from dataclasses import replace

from typehaus.model.enums import LayerFunction
from typehaus.model.spatial import Roof
from typehaus.model.trim import EaveTrim
from typehaus.quantities import inch
from typehaus.resolve.framing.profiles import panel_profile
from typehaus.resolve.model import FramedMember, ResolvedModel, ResolvedRoof, ResolvedWall
from typehaus.resolve.roof_geometry import roof_height_at, roof_structure_depth_m

# Under this the wall already meets the roof — a sliver band is a rounding artifact, not
# construction. Also the tolerance for "this wall sits under this roof".
_CLOSURE_TOLERANCE_M = inch(0.25).meters
_FOOTPRINT_TOLERANCE_M = inch(1.0).meters
_METERS_PER_INCH = inch(1).meters


def resolve_roof_edges(model: ResolvedModel) -> None:
    """Attach the wall→roof closure band and the derived eave/rake trim to every roof."""
    resolved: list[ResolvedRoof] = []
    for roof in model.roofs:
        walls = _walls_under_roof(model, roof)
        extra = _closure_members(model, roof, walls) + _eave_trim_members(model, roof, walls)
        resolved.append(replace(roof, members=roof.members + extra) if extra else roof)
    model.roofs = resolved


# --- shared geometry ---------------------------------------------------------------------

def _bbox(ring) -> tuple[float, float, float, float]:
    xs = [point[0] for point in ring]
    ys = [point[1] for point in ring]
    return min(xs), min(ys), max(xs), max(ys)


def _walls_under_roof(model: ResolvedModel, roof: ResolvedRoof) -> tuple[ResolvedWall, ...]:
    """The roof's storey's *exterior* walls whose plan axis lies inside its footprint.

    Exterior means "has a sheathing layer": an interior partition has no weather skin to
    carry up, and framing a closure band over one would invent construction.
    """
    minx, miny, maxx, maxy = _bbox(roof.footprint)
    tol = _FOOTPRINT_TOLERANCE_M
    walls: list[ResolvedWall] = []
    for wall in model.walls:
        if wall.storey != roof.storey or not _skin_layers(wall):
            continue
        if all(minx - tol <= x <= maxx + tol and miny - tol <= y <= maxy + tol
               for x, y in wall.axis):
            walls.append(wall)
    return tuple(walls)


def _skin_layers(wall: ResolvedWall):
    """The weather skin: the first SHEATHING layer and everything outboard of it."""
    layers = wall.depth_layers()
    start = next((index for index, layer in enumerate(layers)
                  if layer.function == LayerFunction.SHEATHING.value), None)
    return () if start is None else layers[start:]


def _wall_top_at(wall: ResolvedWall, fraction: float) -> float:
    """The wall's top elevation at a fraction along its axis (a rake interpolates)."""
    start = wall.z1_m if wall.top_z0_m is None else wall.top_z0_m
    end = wall.z1_m if wall.top_z1_m is None else wall.top_z1_m
    return start + (end - start) * fraction


def _layer_offset_m(wall: ResolvedWall, layer) -> float:
    """Signed perpendicular offset of a layer's centerline from the wall axis."""
    (ax, ay), (bx, by) = wall.axis
    run = math.hypot(bx - ax, by - ay) or 1.0
    normal = (-(by - ay) / run, (bx - ax) / run)
    ring = layer.polygon
    cx = sum(point[0] for point in ring) / len(ring)
    cy = sum(point[1] for point in ring) / len(ring)
    return (cx - ax) * normal[0] + (cy - ay) * normal[1]


def _offset_point(wall: ResolvedWall, fraction: float, offset: float) -> tuple[float, float]:
    (ax, ay), (bx, by) = wall.axis
    dx, dy = bx - ax, by - ay
    run = math.hypot(dx, dy) or 1.0
    normal = (-dy / run, dx / run)
    return (ax + dx * fraction + normal[0] * offset, ay + dy * fraction + normal[1] * offset)


def _ridge_crossing_fraction(roof: ResolvedRoof, wall: ResolvedWall) -> float | None:
    """Where along the wall the ridge passes over it, if it does.

    A gable wall runs from eave to eave over the ridge, so a single straight rake between its
    endpoints would cut the peak off. Splitting the closure there follows the real two-plane
    roof instead.
    """
    if roof.form != "gable":
        return None
    minx, miny, maxx, maxy = _bbox(roof.footprint)
    axis = 1 if roof.ridge_direction == "x" else 0
    low, high = (miny, maxy) if axis == 1 else (minx, maxx)
    mid = (low + high) / 2.0
    start, end = wall.axis[0][axis], wall.axis[1][axis]
    if abs(end - start) < _CLOSURE_TOLERANCE_M:
        return None
    fraction = (mid - start) / (end - start)
    return fraction if 1e-6 < fraction < 1.0 - 1e-6 else None


# --- wall → roof closure -----------------------------------------------------------------

def _closure_members(
    model: ResolvedModel, roof: ResolvedRoof, walls: tuple[ResolvedWall, ...]
) -> tuple[FramedMember, ...]:
    """Carry each exterior wall's weather skin from its top up to the roof underside."""
    structure_depth = roof_structure_depth_m(model, roof)
    members: list[FramedMember] = []
    for wall in walls:
        crossing = _ridge_crossing_fraction(roof, wall)
        spans = ((0.0, 1.0),) if crossing is None else ((0.0, crossing), (crossing, 1.0))
        for index, (t0, t1) in enumerate(spans):
            members.extend(_closure_segment(roof, wall, t0, t1, index, structure_depth))
    return tuple(members)


def _closure_segment(
    roof: ResolvedRoof, wall: ResolvedWall, t0: float, t1: float,
    segment: int, structure_depth: float,
) -> tuple[FramedMember, ...]:
    tops = (_wall_top_at(wall, t0), _wall_top_at(wall, t1))
    undersides = tuple(
        roof_height_at(roof, _offset_point(wall, fraction, 0.0)) - structure_depth
        for fraction in (t0, t1)
    )
    if max(undersides[0] - tops[0], undersides[1] - tops[1]) < _CLOSURE_TOLERANCE_M:
        return ()  # the wall already reaches the roof here (a ToRoof rake, or a flush eave)
    members: list[FramedMember] = []
    for layer in _skin_layers(wall):
        offset = _layer_offset_m(wall, layer)
        p0 = _offset_point(wall, t0, offset)
        p1 = _offset_point(wall, t1, offset)
        thickness_in = layer.thickness_m / _METERS_PER_INCH
        members.append(FramedMember(
            parent_uid=wall.uid,
            child_key=f"{wall.tag}-closure-{segment}-{layer.name}",
            category=layer.function, profile=panel_profile(thickness_in, thickness_in),
            p0=p0, p1=p1,
            z0_m=tops[0], z1_m=max(tops[0], undersides[0]),
            length_m=math.hypot(p1[0] - p0[0], p1[1] - p0[1]),
            z0_end_m=tops[1], z1_end_m=max(tops[1], undersides[1]),
            connection="roof:wall-top-closure",
        ))
    return tuple(members)


# --- eave / rake trim --------------------------------------------------------------------

def _eave_trim_members(
    model: ResolvedModel, roof: ResolvedRoof, walls: tuple[ResolvedWall, ...]
) -> tuple[FramedMember, ...]:
    element = model.plan.by_tag(roof.tag)
    trim = element.eave_trim if isinstance(element, Roof) else None
    if trim is None or not trim.fascia:
        return ()
    members: list[FramedMember] = []
    for key, run in _roof_edge_runs(roof):
        members.extend(_edge_trim(roof, trim, key, run, walls))
    return tuple(members)


# An edge run: ((p0, z_at_p0), (p1, z_at_p1), outward unit normal in plan).
_EdgeRun = tuple[tuple[tuple[float, float], float], tuple[tuple[float, float], float],
                 tuple[float, float]]


def _roof_edge_runs(roof: ResolvedRoof) -> tuple[tuple[str, _EdgeRun], ...]:
    """The four roof edges as runs at the plane's elevation.

    The two eaves are level; each rake climbs eave→ridge→eave, so it is split at the ridge
    into two straight runs (the same reason the gable closure splits).
    """
    minx, miny, maxx, maxy = _bbox(roof.footprint)
    along_lo, along_hi = (minx, maxx) if roof.ridge_direction == "x" else (miny, maxy)
    span_lo, span_hi = (miny, maxy) if roof.ridge_direction == "x" else (minx, maxx)
    span_mid = (span_lo + span_hi) / 2.0

    def point(along: float, span: float) -> tuple[float, float]:
        return (along, span) if roof.ridge_direction == "x" else (span, along)

    def height(span: float) -> float:
        return roof_height_at(roof, point(along_lo, span))

    runs: list[tuple[str, _EdgeRun]] = []
    for name, span, sign in (("eave-lo", span_lo, -1.0), ("eave-hi", span_hi, 1.0)):
        normal = point(0.0, sign)
        runs.append((name, (((point(along_lo, span)), height(span)),
                            ((point(along_hi, span)), height(span)), normal)))
    for name, along, sign in (("rake-lo", along_lo, -1.0), ("rake-hi", along_hi, 1.0)):
        normal = point(sign, 0.0)
        for half, (a, b) in enumerate(((span_lo, span_mid), (span_mid, span_hi))):
            runs.append((f"{name}-{half}", ((point(along, a), height(a)),
                                            (point(along, b), height(b)), normal)))
    return tuple(runs)


def _edge_trim(
    roof: ResolvedRoof, trim: EaveTrim, key: str, run: _EdgeRun,
    walls: tuple[ResolvedWall, ...],
) -> tuple[FramedMember, ...]:
    (p0, z0), (p1, z1), normal = run
    members: list[FramedMember] = []
    # Boards stack outward from the roof edge: the first (a wood nailer) hangs directly under
    # the deck edge, each later board laps over the one before it.
    inner = -trim.fascia[0].thickness.meters
    for index, board in enumerate(trim.fascia):
        outer = inner + board.thickness.meters
        center = (inner + outer) / 2.0
        depth = board.depth.meters
        a = (p0[0] + normal[0] * center, p0[1] + normal[1] * center)
        b = (p1[0] + normal[0] * center, p1[1] + normal[1] * center)
        members.append(FramedMember(
            parent_uid=roof.uid, child_key=f"{key}-fascia-{index}", category="fascia",
            profile=panel_profile(board.thickness.meters / _METERS_PER_INCH,
                                  depth / _METERS_PER_INCH),
            p0=a, p1=b, z0_m=z0 - depth, z1_m=z0,
            length_m=math.hypot(b[0] - a[0], b[1] - a[1]),
            z0_end_m=z1 - depth, z1_end_m=z1,
            connection=f"eave-trim:{board.material}",
        ))
        inner = outer
    soffit = _soffit_member(roof, trim, key, run, walls)
    return tuple(members) + (() if soffit is None else (soffit,))


def _soffit_member(
    roof: ResolvedRoof, trim: EaveTrim, key: str, run: _EdgeRun,
    walls: tuple[ResolvedWall, ...],
) -> FramedMember | None:
    """The panel closing the overhang underside, fascia back to the wall face."""
    if trim.soffit_thickness is None:
        return None
    (p0, z0), (p1, z1), normal = run
    inset = _wall_face_inset(normal, p0, walls)
    outer = -trim.fascia[0].thickness.meters  # inner face of the innermost fascia board
    width = outer - inset
    if width <= _CLOSURE_TOLERANCE_M:
        return None  # a flush (zero-overhang) edge has no underside to close
    center = (inset + outer) / 2.0
    drop = trim.fascia[0].depth.meters
    thickness = trim.soffit_thickness.meters
    a = (p0[0] + normal[0] * center, p0[1] + normal[1] * center)
    b = (p1[0] + normal[0] * center, p1[1] + normal[1] * center)
    return FramedMember(
        parent_uid=roof.uid, child_key=f"{key}-soffit", category="soffit",
        profile=panel_profile(width / _METERS_PER_INCH, thickness / _METERS_PER_INCH),
        p0=a, p1=b, z0_m=z0 - drop, z1_m=z0 - drop + thickness,
        length_m=math.hypot(b[0] - a[0], b[1] - a[1]),
        z0_end_m=z1 - drop, z1_end_m=z1 - drop + thickness,
        connection=("eave-trim:vented-soffit" if trim.soffit_vented
                    else f"eave-trim:{trim.soffit_material}"),
    )


def _wall_face_inset(
    normal: tuple[float, float], edge_point: tuple[float, float],
    walls: tuple[ResolvedWall, ...],
) -> float:
    """How far inboard of the roof edge the wall's outermost face is, along ``normal``.

    Measured from the resolved cladding polygons, so a rainscreen or a thicker cladding
    moves the soffit's inner edge with it instead of being assumed away.
    """
    projections = [
        (point[0] - edge_point[0]) * normal[0] + (point[1] - edge_point[1]) * normal[1]
        for wall in walls for layer in _skin_layers(wall) for point in layer.polygon
    ]
    return max(projections) if projections else 0.0
