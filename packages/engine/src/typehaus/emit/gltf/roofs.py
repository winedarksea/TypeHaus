"""Roof shells: the sloped plane triangulated over the footprint, then one offset layer band
per above-structure layer, plus the skin members that trim the edge."""

from __future__ import annotations

import math

from typehaus.emit.gltf.geometry import Vec3, _to_gltf
from typehaus.emit.gltf.members import _add_member, is_roof_framing_member
from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.emit.gltf.palette import _material_finish_color
from typehaus.resolve.roof_layer_setbacks import above_structure_layers
from typehaus.resolve.model import ResolvedModel, ResolvedRoof


_RoofVertex = tuple[float, float, float]  # plan-space (x, y, z_elevation)


def _roof_plane_z(roof: ResolvedRoof, x: float, y: float) -> float:
    """Base roof-plane elevation at a plan point (mirrors roof_geometry.roof_height_at,
    but *unclamped* so a slightly-outset layer edge lands just below the eave plane)."""
    xs = [p[0] for p in roof.footprint]
    ys = [p[1] for p in roof.footprint]
    coordinate = y if roof.ridge_direction == "x" else x
    low, high = (min(ys), max(ys)) if roof.ridge_direction == "x" else (min(xs), max(xs))
    span = high - low
    if span <= 1e-9:
        return roof.eave_z_m
    if roof.form == "shed":
        return roof.eave_z_m + (coordinate - low) / span * (roof.ridge_z_m - roof.eave_z_m)
    midpoint = (low + high) / 2.0
    ratio = 1.0 - abs(coordinate - midpoint) / (span / 2.0)
    return roof.eave_z_m + ratio * (roof.ridge_z_m - roof.eave_z_m)


def _roof_plane_triangles(
    roof: ResolvedRoof, rect: tuple[float, float, float, float] | None = None,
) -> list[list[_RoofVertex]]:
    """The sloped gable/shed planes as plan-space triangles. A port of roofGeometry.ts
    ``roofPlaneTriangles``; robust to footprint winding (min/max over all corners).

    ``rect`` (minx, maxx, miny, maxy) builds the planes over a per-layer inset rectangle
    instead of the footprint; vertex z is always evaluated from the *base* plane (the
    full footprint), so inset edges land at the right height and the ridge line stays at
    the footprint's midline.
    """
    xs = [p[0] for p in roof.footprint]
    ys = [p[1] for p in roof.footprint]
    fminx, fmaxx, fminy, fmaxy = min(xs), max(xs), min(ys), max(ys)
    minx, maxx, miny, maxy = rect if rect is not None else (fminx, fmaxx, fminy, fmaxy)

    def v(x: float, y: float) -> _RoofVertex:
        return (x, y, _roof_plane_z(roof, x, y))

    if roof.form == "shed":
        if roof.ridge_direction == "x":
            flat = [v(minx, miny), v(maxx, miny), v(maxx, maxy),
                    v(minx, miny), v(maxx, maxy), v(minx, maxy)]
        else:
            flat = [v(minx, miny), v(maxx, miny), v(maxx, maxy),
                    v(minx, miny), v(maxx, maxy), v(minx, maxy)]
    elif roof.ridge_direction == "x":
        mid = (fminy + fmaxy) / 2
        ra, rb = v(minx, mid), v(maxx, mid)
        flat = [v(minx, miny), v(maxx, miny), rb,
                v(minx, miny), rb, ra,
                ra, rb, v(maxx, maxy),
                ra, v(maxx, maxy), v(minx, maxy)]
    else:
        mid = (fminx + fmaxx) / 2
        ra, rb = v(mid, miny), v(mid, maxy)
        flat = [v(minx, miny), ra, rb,
                v(minx, miny), rb, v(minx, maxy),
                ra, v(maxx, miny), v(maxx, maxy),
                ra, v(maxx, maxy), rb]
    return [flat[i:i + 3] for i in range(0, len(flat), 3)]


def _roof_vertex_key(v: _RoofVertex) -> str:
    return ",".join(f"{n:.4f}" for n in v)


def _roof_face_normal(tri: list[_RoofVertex]) -> _RoofVertex:
    """Unit normal of a roof plane, always the up-slope side (roofGeometry.ts ``faceNormal``)."""
    a, b, c = tri
    ab = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    ac = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    nx = ab[1] * ac[2] - ab[2] * ac[1]
    ny = ab[2] * ac[0] - ab[0] * ac[2]
    nz = ab[0] * ac[1] - ab[1] * ac[0]
    length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    nx, ny, nz = nx / length, ny / length, nz / length
    return (-nx, -ny, -nz) if nz < 0 else (nx, ny, nz)


def _roof_offsetter(triangles: list[list[_RoofVertex]]):
    """Offset the roof surface perpendicular to its slope with a mitered ridge, so every layer
    keeps its true thickness instead of opening a wedge. Port of roofGeometry.ts
    ``roofOffsetter``: average over distinct *planes* (not triangles) at each shared vertex."""
    normals = [_roof_face_normal(t) for t in triangles]
    planes: dict[str, dict[str, _RoofVertex]] = {}
    for i, tri in enumerate(triangles):
        for v in tri:
            key = _roof_vertex_key(v)
            per = planes.setdefault(key, {})
            per[",".join(f"{c:.5f}" for c in normals[i])] = normals[i]
    miters: dict[str, _RoofVertex] = {}
    for key, per in planes.items():
        faces = list(per.values())
        sx = sum(n[0] for n in faces)
        sy = sum(n[1] for n in faces)
        sz = sum(n[2] for n in faces)
        length = math.sqrt(sx * sx + sy * sy + sz * sz) or 1.0
        dx, dy, dz = sx / length, sy / length, sz / length
        dot = dx * faces[0][0] + dy * faces[0][1] + dz * faces[0][2]
        scale = 1.0 / max(0.2, dot)
        miters[key] = (dx * scale, dy * scale, dz * scale)

    def offset_at(v: _RoofVertex, distance: float) -> _RoofVertex:
        mx, my, mz = miters[_roof_vertex_key(v)]
        return (v[0] + mx * distance, v[1] + my * distance, v[2] + mz * distance)

    return offset_at


def _roof_boundary_edges(triangles: list[list[_RoofVertex]]):
    """Edges used by exactly one triangle — the eave/rake perimeter to close for thickness."""
    counts: dict[str, list] = {}
    for tri in triangles:
        for i in range(3):
            a, b = tri[i], tri[(i + 1) % 3]
            key = "|".join(sorted((_roof_vertex_key(a), _roof_vertex_key(b))))
            if key in counts:
                counts[key][1] += 1
            else:
                counts[key] = [(a, b), 1]
    return [edge for edge, count in counts.values() if count == 1]


def _above_structure_layers(assembly) -> list:
    """The assembly layers outboard of the structure — everything the sky sees (roofGeometry.ts
    ``aboveStructureLayers``). Delegates to resolve/roof_layer_setbacks.py, the single source of the
    ordering ``ResolvedRoof.layer_edge_setbacks`` is keyed to."""
    return above_structure_layers(assembly)


def _layer_inset_rect(
    roof: ResolvedRoof, entry: dict, base_offset: float,
) -> tuple[float, float, float, float]:
    """Per-layer inset rectangle from serialized edge setbacks + eave drift compensation.

    Serialized setbacks are final *plan* positions (golden-detail clip faces). Offsetting
    a layer perpendicular to the slope drifts its eave edge down-slope (outward) by
    ``base_offset x sin(theta)``, so that drift is added to the eave-edge insets here;
    rake edges run parallel to the slope's fall line and have no drift. Identical math
    lives in ui/src/three/roofGeometry.ts ``layerInsetRect`` (GLB/viewer parity gate).
    """
    xs = [p[0] for p in roof.footprint]
    ys = [p[1] for p in roof.footprint]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    west, east = float(entry.get("west", 0.0)), float(entry.get("east", 0.0))
    south, north = float(entry.get("south", 0.0)), float(entry.get("north", 0.0))
    span = (maxy - miny) if roof.ridge_direction == "x" else (maxx - minx)
    run = span / 2.0 if roof.form != "shed" else span
    rise = roof.ridge_z_m - roof.eave_z_m
    if run > 1e-9 and rise > 1e-9 and base_offset != 0.0:
        pitch = rise / run
        drift = base_offset * pitch / math.sqrt(1.0 + pitch * pitch)
        if roof.form == "shed":
            # One plane: the low (eave) edge drifts outward, the high edge inward.
            if roof.ridge_direction == "x":
                south, north = south + drift, north - drift
            else:
                west, east = west + drift, east - drift
        elif roof.ridge_direction == "x":
            south, north = south + drift, north + drift
        else:
            west, east = west + drift, east + drift
    return (minx + west, maxx - east, miny + south, maxy - north)


def _add_roof(mb: _MeshBuilder, roof: ResolvedRoof, model: ResolvedModel) -> None:
    """Render the roof as its authored above-structure assembly stack — each layer offset
    perpendicular to the slope with a mitered ridge and a closed eave/rake perimeter, so it
    reads (and imports into Revit/SketchUp) as a real solid, not a zero-thickness plane.

    When the resolver serialized per-layer edge setbacks (``roof.layer_edge_setbacks``),
    each layer is built over its own inset rectangle so the deck clips at the wall
    sheathing, the foam at the wall furring, and the metal runs proud — the golden eave
    detail's band ordering. Empty setbacks keep the uniform footprint behavior.
    """
    triangles = _roof_plane_triangles(roof)
    offset_at = _roof_offsetter(triangles)
    perimeter = _roof_boundary_edges(triangles)
    assembly = model.plan.library.resolve_assembly(roof.assembly) if roof.assembly else None
    layers = _above_structure_layers(assembly)
    setbacks = {entry["layer"]: entry for entry in (roof.layer_edge_setbacks or ())}

    def gltf(v: _RoofVertex) -> Vec3:
        return _to_gltf(v[0], v[1], v[2])

    base = 0.0
    # No assembly layers above structure → one default standing-seam roofing skin (matches the
    # viewer's buildRoof fallback), so the roof still has real thickness.
    stack = layers if layers else [None]
    for layer in stack:
        if layer is None:
            thickness = 0.05
            color = _material_finish_color("standing-seam", "cladding")
        else:
            thickness = layer.thickness.meters
            color = _material_finish_color(layer.material_ref, layer.function.value)
        entry = setbacks.get(layer.name) if layer is not None else None
        if entry is not None:
            layer_triangles = _roof_plane_triangles(roof, _layer_inset_rect(roof, entry, base))
            layer_offset_at = _roof_offsetter(layer_triangles)
            layer_perimeter = _roof_boundary_edges(layer_triangles)
        else:
            layer_triangles, layer_offset_at, layer_perimeter = triangles, offset_at, perimeter
        top = base + thickness
        tris: list[tuple[Vec3, Vec3, Vec3]] = []
        for tri in layer_triangles:  # top skin (up) + bottom skin (reversed, down)
            tris.append((gltf(layer_offset_at(tri[0], top)), gltf(layer_offset_at(tri[1], top)),
                         gltf(layer_offset_at(tri[2], top))))
            tris.append((gltf(layer_offset_at(tri[0], base)), gltf(layer_offset_at(tri[2], base)),
                         gltf(layer_offset_at(tri[1], base))))
        for a, b in layer_perimeter:  # close the eave/rake so the layer reads as real thickness
            tris.append((gltf(layer_offset_at(a, base)), gltf(layer_offset_at(b, base)),
                         gltf(layer_offset_at(b, top))))
            tris.append((gltf(layer_offset_at(a, base)), gltf(layer_offset_at(b, top)),
                         gltf(layer_offset_at(a, top))))
        mb.add_triangles(tris, color)
        base = top
    for member in roof.members:
        if not is_roof_framing_member(member):
            _add_member(mb, member)
