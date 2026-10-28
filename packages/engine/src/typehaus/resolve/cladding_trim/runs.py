"""Straight formed-metal trim runs laid against a wall's cladding layer."""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.library.trim.metal_sales import TrimProfile
from typehaus.quantities import M_PER_IN
from typehaus.resolve.cladding_trim.members import split_stock_run
from typehaus.resolve.cladding_trim.section import folded_section_mesh
from typehaus.resolve.geometry_walls import cuts_layer
from typehaus.resolve.metal_skin_profiles import SHEET_24_GA_M
from typehaus.resolve.model import ResolvedSolid


@dataclass(frozen=True)
class CladdingFace:
    """A cladding layer's frame: axis ``d``, outward normal ``n``, back plane, extents."""

    wall: object
    layer: object
    d: tuple[float, float]
    n: tuple[float, float]
    back: float
    lo: float
    hi: float
    z0: float
    z1: float

    def xy(self, station: float, depth: float = 0.0) -> tuple[float, float]:
        """World point at an along station, ``depth`` outboard of the back plane."""
        off = self.back + depth
        return (station * self.d[0] + off * self.n[0], station * self.d[1] + off * self.n[1])

    def openings(self, model):
        """Openings cutting this face's layer as (opening, lo, hi) along-stations."""
        origin = self.wall.axis[0][0] * self.d[0] + self.wall.axis[0][1] * self.d[1]
        for opening in model.openings:
            if (opening.host_wall == self.wall.tag
                    and cuts_layer(self.wall, self.layer.name, opening)):
                mid = origin + opening.center_along_m
                yield opening, mid - opening.width_m / 2, mid + opening.width_m / 2


def cladding_face(wall, layer) -> CladdingFace | None:
    (ax, ay), (bx, by) = wall.axis[0], wall.axis[-1]
    length = math.hypot(bx - ax, by - ay)
    if length < 1e-6:
        return None
    d = ((bx - ax) / length, (by - ay) / length)
    n = (-d[1], d[0])
    mid = [sum(p[i] for p in layer.polygon) / len(layer.polygon) for i in (0, 1)]
    inner = [sum(p[i] for p in wall.layers[0].polygon) / len(wall.layers[0].polygon)
             for i in (0, 1)]
    if sum((mid[i] - inner[i]) * n[i] for i in (0, 1)) < 0:
        n = (-n[0], -n[1])
    along = [x * d[0] + y * d[1] for x, y in layer.polygon]
    z0, z1 = layer.band(wall)
    return CladdingFace(wall, layer, d, n, min(x * n[0] + y * n[1] for x, y in layer.polygon),
                        min(along), max(along), z0, z1)


def metal_faces(model, finishes: set[str]):
    """Every cladding layer whose material finish is in ``finishes``."""
    finish = {m.tag: m.finish for m in model.plan.library.materials}
    for wall in model.walls:
        for layer in wall.layers:
            clad = layer.function == "cladding" and finish.get(layer.material_ref) in finishes
            if clad and (face := cladding_face(wall, layer)) is not None:
                yield face


def kit_faces(model, condition):
    """(face, profile key) for every outermost wall layer whose material kit has ``condition``."""
    materials = {m.tag: m for m in model.plan.library.materials}
    for wall in model.walls:
        for layer in wall.layers:
            material = materials.get(layer.material_ref)
            key = material.trim_kit.get(condition) if material else None
            outermost = layer.function == "cladding" or layer is wall.layers[-1]
            if key and outermost and (face := cladding_face(wall, layer)) is not None:
                yield face, key


def covered_below(face: CladdingFace, faces) -> bool:
    """Whether another face continues this one's panel run downward (no free bottom edge)."""
    for other in faces:
        if other is face or abs(other.z1 - face.z0) > M_PER_IN:
            continue
        if abs(face.d[0] * other.d[0] + face.d[1] * other.d[1]) < 1 - 1e-6:
            continue
        offset = abs(sum((p - q) * c for p, q, c in zip(other.xy(0), face.xy(0), face.n,
                                                        strict=True)))
        ends = [sum(p * c for p, c in zip(other.xy(s), face.d, strict=True))
                for s in (other.lo, other.hi)]
        overlap = min(max(ends), face.hi) - max(min(ends), face.lo)
        if offset < M_PER_IN and overlap > M_PER_IN:
            return True
    return False


def subtract_spans(lo: float, hi: float, cuts) -> list[tuple[float, float]]:
    """``[lo, hi]`` less the (a, b) cuts, dropping slivers under half an inch."""
    spans, cursor = [], lo
    for a, b in sorted(cuts):
        if a > cursor:
            spans.append((cursor, min(a, hi)))
        cursor = max(cursor, b)
    if cursor < hi:
        spans.append((cursor, hi))
    return [(a, b) for a, b in spans if b - a > 0.5 * M_PER_IN]


def _emit(model, face, profile, key, tag_base, host_ref, index, mesh, length, stock):
    xs, ys, zs = zip(*mesh.positions, strict=True)
    model.solids.append(ResolvedSolid(
        uid=f"{face.wall.uid}-{tag_base.lower()}-{index}", tag=f"{tag_base}-{index + 1}",
        storey=face.wall.storey, category="cladding_trim",
        outline=((min(xs), min(ys)), (max(xs), min(ys)), (max(xs), max(ys)), (min(xs), max(ys))),
        z0_m=min(zs), z1_m=max(zs), material=face.layer.material_ref, product=key,
        body_mesh=mesh, host_ref=host_ref or face.wall.tag, trim_length_m=length,
        trim_stock_length_in=round(stock / M_PER_IN, 6)))


def _pieces(profile, length):
    return split_stock_run(length, tuple(v * M_PER_IN for v in profile.stock_lengths_in),
                           profile.min_lap_in * M_PER_IN)


def _section_m(profile, section_in=None):
    return tuple((x * M_PER_IN, y * M_PER_IN) for x, y in (section_in or profile.section_in))


def add_horizontal_run(model, face: CladdingFace, profile: TrimProfile, key: str, tag_base: str,
                       lo: float, hi: float, z: float, *, depth: float = 0.0,
                       host_ref: str | None = None, section_in=None) -> int:
    """Sweep ``profile`` along stations ``lo..hi`` at height ``z``; return pieces added.

    The section is (outboard, up) from the cladding back plane + ``depth``.
    """
    section, n = _section_m(profile, section_in), (*face.n, 0.0)
    pieces = _pieces(profile, hi - lo)
    for index, (start, end, stock) in enumerate(pieces):
        x, y = face.xy(lo + start, depth)
        mesh = folded_section_mesh(
            section, (x, y, z), n, (0.0, 0.0, 1.0),
            (face.d[0] * (end - start), face.d[1] * (end - start), 0.0), SHEET_24_GA_M)
        _emit(model, face, profile, key, tag_base, host_ref, index, mesh, end - start, stock)
    return len(pieces)


def add_vertical_run(model, face: CladdingFace, profile: TrimProfile, key: str, tag_base: str,
                     station: float, z0: float, z1: float, inward: float, *, depth: float = 0.0,
                     host_ref: str | None = None) -> int:
    """Sweep ``profile`` up from ``z0`` to ``z1`` at an along ``station``.

    The section is (outboard, along); ``inward`` (+1 or -1) is the along direction the
    back leg runs, away from the panel edge or opening the trim finishes.
    """
    section, n = _section_m(profile), (*face.n, 0.0)
    pieces = _pieces(profile, z1 - z0)
    along = (face.d[0] * inward, face.d[1] * inward, 0.0)
    for index, (start, end, stock) in enumerate(pieces):
        x, y = face.xy(station, depth)
        mesh = folded_section_mesh(section, (x, y, z0 + start), n, along,
                                   (0.0, 0.0, end - start), SHEET_24_GA_M)
        _emit(model, face, profile, key, tag_base, host_ref, index, mesh, end - start, stock)
    return len(pieces)
