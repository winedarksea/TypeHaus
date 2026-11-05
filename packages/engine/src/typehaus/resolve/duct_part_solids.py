"""Draw every derived duct part and hanger as a product solid (decision #114).

``resolve/duct_parts.py`` leaves ``ResolvedDuctPart`` / ``ResolvedDuctSupport`` records;
this turns each into one ``derived`` ``ResolvedSolid`` with a closed ``body_mesh``: a loft
between two sections for a collar, reducer, transition, boot or flex, a U strap or paired
rods for a hanger. Billing stays on the records. An integral part (the terminal's or
machine's own collar) draws nothing. Dimensions the row never read fall back to the
envelope of the sections it joins, never to detail the standard does not state.

Sections parse from the record text (``4in`` round, ``18x8`` width x depth, inches).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from typehaus.quantities import M_PER_IN
from typehaus.resolve.connector_geometry.mesh import combine_meshes, plate_mesh, transform_mesh
from typehaus.resolve.geometry_ir import GMesh, Vec3, signed_volume
from typehaus.resolve.model import ResolvedModel, ResolvedSolid
from typehaus.resolve.model_ducts import ResolvedDuctPart, ResolvedDuctSupport
from typehaus.resolve.sweep import leg_frame

_FACETS = 16
COLLAR_LENGTH_M = 2.0 * M_PER_IN
MIN_DROP_M = 0.5 * M_PER_IN
STRAP_WIDTH_M, STRAP_THICKNESS_M = 1.0 * M_PER_IN, M_PER_IN / 32.0
ROD_DIAMETER_M = 0.375 * M_PER_IN
#: The collar damper's quadrant handle: along the collar, around it, and out from it.
HANDLE_M = (1.5 * M_PER_IN, 2.0 * M_PER_IN, 0.25 * M_PER_IN)
HANDLE_STANDOFF_M = 0.125 * M_PER_IN  # the shaft, undrawn
_CATEGORY = {"takeoff": "duct_fitting", "tee": "duct_fitting", "reducer": "duct_fitting",
             "transition": "duct_fitting", "boot": "duct_fitting",
             "collar_damper": "duct_damper", "flex": "duct_connector",
             "connector": "duct_connector"}


@dataclass(frozen=True)
class Section:
    """A duct section in metres: ``width`` across the run, ``depth`` through it."""

    is_round: bool
    width: float
    depth: float

    @property
    def larger(self) -> float:
        return max(self.width, self.depth)


def parse_section(text: str | None) -> Section | None:
    """``4in`` -> round, ``18x8`` -> rectangular; anything else (``none``, None) -> None."""
    if not text:
        return None
    try:
        if text.endswith("in"):
            d = float(text[:-2]) * M_PER_IN
            return Section(True, d, d) if d > 0 else None
        w, _, h = text.partition("x")
        w, h = float(w) * M_PER_IN, float(h) * M_PER_IN
        return Section(False, w, h) if w > 0 and h > 0 else None
    except ValueError:
        return None


def _add(a: Vec3, b: Vec3, k: float = 1.0) -> Vec3:
    return (a[0] + b[0] * k, a[1] + b[1] * k, a[2] + b[2] * k)


def _unit(v: Vec3) -> Vec3 | None:
    n = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)
    return None if n < 1e-9 else (v[0] / n, v[1] / n, v[2] / n)


def _ring(section: Section, centre: Vec3, right: Vec3, up: Vec3, count: int) -> list[Vec3]:
    """The section's outline at ``centre``: ``count`` 4 (rectangle) or ``_FACETS`` points."""
    hw, hd = section.width / 2.0, section.depth / 2.0
    if section.is_round:
        pts = [(hw * math.cos(2 * math.pi * i / count), hd * math.sin(2 * math.pi * i / count))
               for i in range(count)]
    elif count == 4:
        pts = [(-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd)]
    else:  # a rectangle lofted to a round: sampled on the same angles, never collinear in uv
        pts = []
        for i in range(count):
            c, s = math.cos(2 * math.pi * i / count), math.sin(2 * math.pi * i / count)
            t = min(hw / abs(c) if abs(c) > 1e-9 else math.inf,
                    hd / abs(s) if abs(s) > 1e-9 else math.inf)
            pts.append((t * c, t * s))
    return [_add(_add(centre, right, u), up, v) for u, v in pts]


def prism(a: list[Vec3], b: list[Vec3]) -> GMesh:
    """A closed solid between two convex rings of equal length, capped from their centres."""
    n = len(a)
    ca = tuple(sum(p[i] for p in a) / n for i in range(3))
    cb = tuple(sum(p[i] for p in b) / n for i in range(3))
    positions = (*a, *b, ca, cb)
    tris: list[tuple[int, int, int]] = []
    for i in range(n):
        j = (i + 1) % n
        tris += [(i, j, n + j), (i, n + j, n + i), (2 * n, j, i), (2 * n + 1, n + i, n + j)]
    if signed_volume(positions, tris) < 0:
        tris = [(x, z, y) for x, y, z in tris]
    return GMesh(positions=positions, triangles=tuple(tris))


def loft(origin: Vec3, axis: Vec3, start: Section, end: Section, length: float) -> GMesh:
    """``start`` at ``origin`` to ``end`` ``length`` along ``axis``."""
    right, up = leg_frame(axis)
    count = 4 if not start.is_round and not end.is_round else _FACETS
    far = _add(origin, axis, length)
    return prism(_ring(start, origin, right, up, count), _ring(end, far, right, up, count))


def _box(centre: Vec3, axes: tuple[Vec3, Vec3, Vec3], dims: tuple[float, float, float]) -> GMesh:
    def corner(sx: float, sy: float, sz: float) -> Vec3:
        p = centre
        for sign, axis, dim in zip((sx, sy, sz), axes, dims, strict=True):
            p = _add(p, axis, sign * dim / 2.0)
        return p

    return prism([corner(-1, -1, -1), corner(1, -1, -1), corner(1, 1, -1), corner(-1, 1, -1)],
                 [corner(-1, -1, 1), corner(1, -1, 1), corner(1, 1, 1), corner(-1, 1, 1)])


def _run_at(model: ResolvedModel, tag: str, point: Vec3) -> tuple[Any, Vec3 | None]:
    """The run and its unit direction at the leg nearest ``point`` (plan, then z)."""
    duct = next((d for d in model.ducts if d.tag == tag), None)
    if duct is None or len(duct.path) < 2 or len(duct.z_m) != len(duct.path):
        return duct, None
    pts = [(x, y, z) for (x, y), z in zip(duct.path, duct.z_m, strict=True)]
    best = None
    for a, b in zip(pts, pts[1:], strict=False):
        ab = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        n2 = sum(c * c for c in ab)
        if n2 < 1e-12:
            continue
        t = max(0.0, min(1.0, sum((point[i] - a[i]) * ab[i] for i in range(3)) / n2))
        gap = math.dist(point, _add(a, ab, t))
        if best is None or gap < best[0]:
            best = (gap, ab)
    return duct, _unit(best[1]) if best else None


def _surface_offset(model: ResolvedModel, part: ResolvedDuctPart, axis: Vec3) -> float:
    """From the main's centreline out to its surface along ``axis`` (a take-off's start)."""
    duct, direction = _run_at(model, part.run_tag, part.point)
    section = parse_section(part.size)
    if section is None or direction is None:
        return 0.0
    if section.is_round:
        return section.width / 2.0
    right, up = leg_frame(direction)
    ar = abs(sum(axis[i] * right[i] for i in range(3)))
    au = abs(sum(axis[i] * up[i] for i in range(3)))
    reach = (section.width / 2.0 / ar if ar > 1e-9 else math.inf,
             section.depth / 2.0 / au if au > 1e-9 else math.inf)
    return min(reach) if min(reach) < math.inf else 0.0


def _into_run(part: ResolvedDuctPart, model: ResolvedModel) -> bool:
    """Whether the record's ``axis`` runs into its own ``run_tag`` (not its ``other``)."""
    from typehaus.resolve.duct_branches import duct_ends

    duct = next((d for d in model.ducts if d.tag == part.run_tag), None)
    return duct is not None and any(
        math.dist(end, part.point) < 1e-3 and sum(a * b for a, b in zip(axis, part.axis,
                                                                         strict=True)) > 0.99
        for _, end, axis in duct_ends(duct))


def _transition_length(part: ResolvedDuctPart) -> float:
    sizes = [s for s in (parse_section(part.size), parse_section(part.branch)) if s]
    return part.length_m or max((s.larger for s in sizes), default=0.0)


def _part_mesh(model: ResolvedModel, part: ResolvedDuctPart,
               siblings: list[ResolvedDuctPart]) -> GMesh | None:
    axis = _unit(part.axis)
    size, branch = parse_section(part.size), parse_section(part.branch)
    if axis is None or size is None:
        return None
    if part.kind in ("takeoff", "tee"):
        stub = branch or size
        start = _add(part.point, axis, _surface_offset(model, part, axis))
        return loft(start, axis, stub, stub, part.length_m or COLLAR_LENGTH_M)
    if part.kind in ("reducer", "transition"):
        small = branch or size
        length = _transition_length(part)
        # A reducer's record is on the bigger run and its axis may point down either side;
        # a transition runs from the machine's port into the run.
        flipped = _into_run(part, model) if part.kind == "reducer" else True
        ends = (small, size) if flipped else (size, small)
        return loft(part.point, axis, *ends, length)
    if part.kind == "collar_damper":
        collar = loft(part.point, axis, size, size, COLLAR_LENGTH_M)
        right, up = leg_frame(axis)
        mid = _add(part.point, axis, COLLAR_LENGTH_M / 2.0)
        out = size.width / 2.0 + HANDLE_STANDOFF_M + HANDLE_M[2] / 2.0
        along, around, thick = HANDLE_M
        return combine_meshes(collar, _box(_add(mid, right, out), (axis, up, right),
                                           (along, around, thick)))
    if part.kind == "boot":
        return _boot_mesh(model, part, size, branch)
    # flex / connector: a sleeve of the run's section, clear of a transition at the same port
    behind = sum(_transition_length(s) for s in siblings
                 if s.kind == "transition" and s.run_tag == part.run_tag
                 and s.port == part.port and s.point == part.point)
    return loft(_add(part.point, axis, behind), axis, size, size,
                part.length_m or size.larger)


def _boot_mesh(model: ResolvedModel, part: ResolvedDuctPart, size: Section,
               neck: Section | None) -> GMesh | None:
    if part.width_m and part.height_m:
        neck = Section(False, part.width_m, part.height_m)
    neck = neck or size
    target = next((o for o in model.canvas_objects if o.tag == part.other), None)
    direction, reach = (0.0, 0.0, 1.0), None
    if target is not None:
        z = target.body_z0_m if target.body_z0_m is not None else part.point[2]
        to = (target.position[0] - part.point[0], target.position[1] - part.point[1],
              z - part.point[2])
        direction = _unit(to) or direction
        reach = math.sqrt(sum(c * c for c in to))
    length = part.length_m or max(size.larger, neck.larger)
    if part.length_m is None and reach:
        length = min(length, reach)
    return loft(part.point, direction, size, neck, length)


def _support_mesh(model: ResolvedModel, hanger: ResolvedDuctSupport) -> GMesh | None:
    duct, direction = _run_at(model, hanger.run_tag, hanger.point)
    if duct is None:
        return None
    flat = _unit((direction[0], direction[1], 0.0)) if direction else None
    run = flat or (1.0, 0.0, 0.0)
    across = (run[1], -run[0], 0.0)
    half_w, half_d = duct.width_m / 2.0, duct.depth_m / 2.0
    drop = max(hanger.drop_m, MIN_DROP_M)
    px, py, pz = hanger.point
    top = half_d + drop
    if hanger.hanger == "rod_trapeze":
        diameter = hanger.width_m or ROD_DIAMETER_M
        rod = Section(True, diameter, diameter)
        reach = half_w + diameter / 2.0
        return combine_meshes(*(
            loft((px + across[0] * s * reach, py + across[1] * s * reach, pz - half_d),
                 (0.0, 0.0, 1.0), rod, rod, half_d + top) for s in (-1.0, 1.0)))
    width = hanger.width_m or STRAP_WIDTH_M
    t = hanger.thickness_m or STRAP_THICKNESS_M
    u = ((-half_w - t, top), (-half_w - t, -half_d - t), (half_w + t, -half_d - t),
         (half_w + t, top), (half_w, top), (half_w, -half_d), (-half_w, -half_d),
         (-half_w, top))
    plate = plate_mesh(tuple((a / M_PER_IN, 0.0, z / M_PER_IN) for a, z in u),
                       (0.0, width / M_PER_IN, 0.0))
    shifted = transform_mesh(plate, origin_m=_add(hanger.point, run, -width / 2.0),
                             x_axis=across, y_axis=run, z_axis=(0.0, 0.0, 1.0))
    return shifted


def _solid(uid: str, tag: str, storey: str, category: str, mesh: GMesh,
           product: str | None, host: str) -> ResolvedSolid:
    from shapely.geometry import MultiPoint

    xs, ys, zs = zip(*mesh.positions, strict=True)
    hull = MultiPoint([(x, y) for x, y, _ in mesh.positions]).convex_hull
    ring = ([(min(xs), min(ys)), (max(xs), min(ys)), (max(xs), max(ys)), (min(xs), max(ys))]
            if hull.geom_type != "Polygon" else [tuple(p) for p in hull.exterior.coords][:-1])
    return ResolvedSolid(uid=uid, tag=tag, storey=storey, category=category, outline=ring,
                         z0_m=min(zs), z1_m=max(zs), product=product, host_ref=host,
                         body_mesh=mesh, derived=True)  # billed off its record, not measured


def part_solids(model: ResolvedModel) -> None:
    """Append one solid per non-integral part and per hanger."""
    uids = {d.tag: d.uid for d in model.ducts}
    seen: dict[tuple[str, str], int] = {}
    for part in model.duct_parts:
        if part.integral:
            continue
        mesh = _part_mesh(model, part, model.duct_parts)
        if mesh is None:
            continue
        n = seen[(part.run_tag, part.kind)] = seen.get((part.run_tag, part.kind), 0) + 1
        model.solids.append(_solid(
            f"{uids.get(part.run_tag, part.run_tag)}-{part.kind}-{n}",
            f"{part.run_tag}-{part.kind.upper()}-{n}", part.storey, _CATEGORY[part.kind],
            mesh, part.product_ref, part.run_tag))
    for n, hanger in enumerate(model.duct_supports, start=1):
        mesh = _support_mesh(model, hanger)
        if mesh is None:
            continue
        model.solids.append(_solid(
            f"{uids.get(hanger.run_tag, hanger.run_tag)}-hanger-{n}",
            f"{hanger.run_tag}-HANGER-{n}", hanger.storey, "duct_support", mesh,
            hanger.product_ref, hanger.run_tag))
