"""Union, cut and split the kept solids into bed-sized, lift-off pieces.

The cuts are grade and the underside of each storey's floor package, so every upper piece
stands on its own ceiling plane and no room is bridged: lift a storey off and the rooms
below show from above. Planes closer than ``min_piece_m`` merge (into the one with the most
floor). ``decompose()`` runs per piece only; on a whole house it is minutes, not seconds.
The lowest piece is fused to a thin plate; nothing registers the storeys but their walls.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from typehaus.print3d.collect import PrintItem
from typehaus.print3d.policy import PrintSettings
from typehaus.solids3d import require_manifold3d
from typehaus.solids3d.convert import union

#: Architect's scales a standard scale rule reads: 1:N and its name.
STANDARD_SCALES: tuple[tuple[int, str], ...] = (
    (96, '1/8" = 1\'-0"'), (100, "1:100"), (128, '3/32" = 1\'-0"'), (150, "1:150"),
    (192, '1/16" = 1\'-0"'), (200, "1:200"))
#: A face is an overhang when it looks more than 45 degrees downward.
OVERHANG_NZ = -math.cos(math.radians(45.0))
#: Plate and piece fuse through this much overlap, in print mm.
FUSE_MM = 0.05
#: A downward face within the first layer of the bed is laid on it, not supported. A
#: merged ceiling a lining's thickness above its storey's cut is one (0.13 mm at 1:128).
FIRST_LAYER_MM = 0.2
#: Each side of a storey cut is trimmed this far off the plane, in model metres (0.1 mm).
CUT_GAP_M = 1e-4


@dataclass(frozen=True)
class Band:
    name: str
    z0: float
    z1: float


@dataclass
class Piece:
    name: str
    solid: object  # in print mm, resting on z = 0
    dims_mm: tuple[float, float, float]
    support_mm2: float
    orientation: str
    islands_mm3: list[float] = field(default_factory=list)
    shells: int = 1


def cut_bands(items: list[PrintItem], grade_m: float, top_m: float,
              settings: PrintSettings) -> list[Band]:
    """Grade and each storey's floor-package underside, merged closer than a piece."""
    planes: dict[str, tuple[float, float]] = {}  # storey -> (underside z, floor area)
    for item in items:
        if item.kind != "floor" or item.storey is None:
            continue
        z0 = item.solid.bounding_box()[2]
        area = item.solid.project().area()
        low, total = planes.get(item.storey, (math.inf, 0.0))
        planes[item.storey] = (min(low, z0), total + area)
    candidates = sorted((z, area, storey) for storey, (z, area) in planes.items())
    clusters: list[list[tuple[float, float, str]]] = []
    for plane in candidates:
        if clusters and plane[0] - clusters[-1][-1][0] < settings.min_piece_m:
            clusters[-1].append(plane)
        else:
            clusters.append([plane])
    cuts = [max(cluster, key=lambda plane: plane[1]) for cluster in clusters]
    bands: list[Band] = []
    low, name = grade_m, None
    for z, _, storey in cuts:
        if z - low < settings.min_piece_m or top_m - z < settings.min_piece_m:
            name = name or storey  # merged into the band below
            continue
        bands.append(Band(name or storey, low, z))
        low, name = z, storey
    bands.append(Band(name or "house", low, top_m))
    return bands


def choose_scale(extents: list[tuple[float, float, float]], settings: PrintSettings) -> int:
    """The largest standard scale at which every band's extent fits the bed (the first band
    carries the plate's margin). ``settings.scale`` is honoured, or refused."""
    fits = [n for n, _ in STANDARD_SCALES if _fits_all(extents, 1000.0 / n, settings)]
    if settings.scale is not None:
        if _fits_all(extents, 1000.0 / settings.scale, settings):
            return settings.scale
        largest = f"1:{fits[0]}" if fits else "none of the standard scales"
        raise ValueError(f"1:{settings.scale} does not fit the bed; the largest that fits is "
                         f"{largest}")
    if not fits:
        raise ValueError("the house does not fit the bed at 1:200; pass --scale or --bed")
    return fits[0]


def scale_name(n: int) -> str:
    return dict(STANDARD_SCALES).get(n, f"1:{n}")


def band_extents(items: list[PrintItem], bands: list[Band]) -> list[tuple[float, float, float]]:
    """Each band's (x, y, z) extent in metres, from the items' boxes clipped to it."""
    boxes = np.array([item.solid.bounding_box() for item in items])
    out = []
    for band in bands:
        inside = boxes[(boxes[:, 5] > band.z0) & (boxes[:, 2] < band.z1)]
        if not len(inside):
            out.append((0.0, 0.0, 0.0))
            continue
        out.append((float(inside[:, 3].max() - inside[:, 0].min()),
                    float(inside[:, 4].max() - inside[:, 1].min()),
                    float(min(inside[:, 5].max(), band.z1) - max(inside[:, 2].min(), band.z0))))
    return out


def build_pieces(solids: list, bands: list[Band], mm_per_m: float,
                 settings: PrintSettings) -> list[Piece]:
    m3d = require_manifold3d()
    body = union(solids).trim_by_plane((0.0, 0.0, 1.0), bands[0].z0)
    slabs = []
    for band in bands[:-1]:
        # Each cut is a floor package's underside, so the plane is coplanar with faces and
        # an exact split can leave a micron sliver of that floor on the piece below (seen:
        # 85 m² of "overhang" on catlin's second storey). Trimming each side a hair off the
        # plane drops any sliver thinner than the gap.
        slabs.append(body.trim_by_plane((0.0, 0.0, -1.0), -(band.z1 - CUT_GAP_M)))
        body = body.trim_by_plane((0.0, 0.0, 1.0), band.z1 + CUT_GAP_M)
    slabs.append(body)
    pieces: list[Piece] = []
    for index, (band, slab) in enumerate(zip(bands, slabs, strict=True)):
        if slab.is_empty():
            continue
        scaled = slab.scale((mm_per_m, mm_per_m, mm_per_m))
        if index == 0:
            scaled = _on_plate(m3d, scaled, settings)
        objects, islands, shells = _components(m3d, scaled, settings)
        for rank, part in enumerate(objects):
            piece = _oriented(part, band.name if rank == 0 else f"{band.name}-{rank + 1}",
                              flip=index != 0, islands=islands if rank == 0 else [])
            piece.shells = shells[rank]
            pieces.append(piece)
    for piece in pieces:
        if not _fits(piece.dims_mm, settings):
            raise ValueError(f"piece {piece.name} ({_mm(piece.dims_mm)}) does not fit the bed")
    return pieces


def support_area_mm2(solid) -> float:
    """Downward-facing area steeper than 45 degrees that is not on the bed."""
    mesh = solid.to_mesh()
    points = np.asarray(mesh.vert_properties, dtype=float)[:, :3]
    tris = np.asarray(mesh.tri_verts, dtype=int)
    if not len(tris):
        return 0.0
    first = points[tris[:, 0]]
    cross = np.cross(points[tris[:, 1]] - first, points[tris[:, 2]] - first)
    area = np.linalg.norm(cross, axis=1) / 2
    with np.errstate(invalid="ignore", divide="ignore"):
        nz = np.where(area > 0, cross[:, 2] / (2 * area), 0.0)
    on_bed = points[tris][:, :, 2].max(axis=1) <= points[:, 2].min() + FIRST_LAYER_MM
    return float(area[(nz < OVERHANG_NZ) & ~on_bed].sum())


def _on_plate(m3d, solid, settings: PrintSettings):
    x0, y0, z0, x1, y1, _ = solid.bounding_box()
    margin = settings.plate_margin_mm
    plate = m3d.Manifold.cube((x1 - x0 + 2 * margin, y1 - y0 + 2 * margin,
                               settings.plate_mm + FUSE_MM))
    return union([solid, plate.translate((x0 - margin, y0 - margin, z0 - settings.plate_mm))])


def _components(m3d, solid, settings: PrintSettings) -> tuple[list, list[float], list[int]]:
    """One object per building: the largest shell and every shell inside its box (a sink
    that stops a hair above its floor still prints, the gap under a layer), each shell
    outside that box its own object. Islands under ``min_island_mm3`` are dropped; an
    internal void's shell is dropped too, which only fills a sealed cavity."""
    shells = sorted((part for part in solid.decompose() if part.volume() > 0),
                    key=lambda part: -part.volume())
    islands = [part.volume() for part in shells if part.volume() < settings.min_island_mm3]
    kept = [part for part in shells if part.volume() >= settings.min_island_mm3]
    if not kept:
        return [], islands, []
    groups: list[list] = [[kept[0]]]
    main = kept[0].bounding_box()
    for part in kept[1:]:
        box = part.bounding_box()
        inside = all(box[i] < main[i + 3] and main[i] < box[i + 3] for i in range(3))
        if inside:
            groups[0].append(part)
        else:
            groups.append([part])
    objects = [m3d.Manifold.compose(group) if len(group) > 1 else group[0] for group in groups]
    return objects, islands, [len(group) for group in groups]


def _oriented(solid, name: str, flip: bool, islands: list[float]) -> Piece:
    """Upright or upside down, whichever needs less support; resting on z = 0."""
    options = [("upright", solid)]
    if flip:
        options.append(("flipped", solid.rotate((180.0, 0.0, 0.0))))
    scored = [(support_area_mm2(_rest(candidate)), label, _rest(candidate))
              for label, candidate in options]
    support, label, rested = min(scored, key=lambda row: (row[0], row[1] != "upright"))
    box = rested.bounding_box()
    return Piece(name, rested, (box[3] - box[0], box[4] - box[1], box[5] - box[2]), support,
                 label, islands)


def _rest(solid):
    x0, y0, z0, x1, y1, _ = solid.bounding_box()
    return solid.translate((-(x0 + x1) / 2, -(y0 + y1) / 2, -z0))


def _fits(dims_mm, settings: PrintSettings) -> bool:
    bx, by, bz = (value - 2 * settings.margin_mm for value in settings.bed_mm)
    x, y, z = dims_mm
    return z <= bz and ((x <= bx and y <= by) or (y <= bx and x <= by))


def _fits_all(extents, mm_per_m: float, settings: PrintSettings) -> bool:
    for index, (x, y, z) in enumerate(extents):
        pad = 2 * settings.plate_margin_mm if index == 0 else 0.0
        plate = settings.plate_mm if index == 0 else 0.0
        if not _fits((x * mm_per_m + pad, y * mm_per_m + pad, z * mm_per_m + plate), settings):
            return False
    return True


def _mm(dims) -> str:
    return " x ".join(f"{value:.1f}" for value in dims) + " mm"
