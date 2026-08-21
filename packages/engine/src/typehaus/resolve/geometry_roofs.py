"""Roof shells as IR solids: one closed band per above-structure assembly layer.

Moved out of ``emit/gltf/roofs.py`` (itself a port of ``ui/src/three/roofGeometry.ts``), which
was the third copy of this math — and the one that disagreed with IFC, whose ``ifc/roof.py``
built vertical-sided layer prisms with no eave-drift compensation. The plan blessed *this*
interpretation as canonical; ``ifc/roof.py`` now reads these bands too, so its roof layers
changed shape slightly and the exported assembly matches what the viewer draws.

The rules, stated once:

* each layer is offset **perpendicular to the slope** with a mitered ridge, so it keeps its
  true thickness instead of opening a wedge at the hip;
* serialized ``layer_edge_setbacks`` are final *plan* positions (the golden eave detail's clip
  faces), so the perpendicular offset's down-slope drift is added back on the eave edges —
  rake edges run along the fall line and do not drift;
* the eave/rake perimeter is closed, so a layer imports as a real solid rather than a
  zero-thickness plane.

Output is a :class:`GMesh` per layer: a triangle soup in the plan frame, positions unshared so
every facet keeps its own flat normal (an offset roof band has no curvature to smooth).
"""

from __future__ import annotations

import math

from typehaus.emit.finishes import layer_material_key, layer_visibility_group
from typehaus.resolve.geometry_ir import GMesh, GPart, Vec3
from typehaus.resolve.roof_geometry import roof_plane_z, roof_slope_coordinate
from typehaus.resolve.roof_layer_setbacks import above_structure_layers
from typehaus.resolve.model import ResolvedRoof

# The roof still has to read as a solid when its assembly declares nothing above the
# structure — the viewer's ``buildRoof`` fallback, mirrored here so the GLB agrees with it.
_FALLBACK_THICKNESS_M = 0.05
_FALLBACK_MATERIAL_REF = "standing-seam"
_FALLBACK_FUNCTION = "cladding"


def _plane_z(roof: ResolvedRoof, x: float, y: float) -> float:
    """Base roof-plane elevation at a plan point, *unclamped*, so a slightly-outset layer
    edge lands just below the eave plane rather than kinking flat."""
    return roof_plane_z(roof, roof_slope_coordinate(roof, (x, y)))


def plane_triangles(roof: ResolvedRoof,
                    rect: tuple[float, float, float, float] | None = None,
                    ) -> list[list[Vec3]]:
    """The sloped gable/shed planes as plan-space triangles; robust to footprint winding.

    ``rect`` (minx, maxx, miny, maxy) builds the planes over a per-layer inset rectangle
    instead of the footprint; vertex z is always evaluated from the *base* plane, so inset
    edges land at the right height and the ridge line stays on the footprint's midline.
    """
    xs = [p[0] for p in roof.footprint]
    ys = [p[1] for p in roof.footprint]
    fminx, fmaxx, fminy, fmaxy = min(xs), max(xs), min(ys), max(ys)
    minx, maxx, miny, maxy = rect if rect is not None else (fminx, fmaxx, fminy, fmaxy)

    def v(x: float, y: float) -> Vec3:
        return (x, y, _plane_z(roof, x, y))

    if roof.form == "shed":
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


def _vertex_key(v: Vec3) -> str:
    return ",".join(f"{n:.4f}" for n in v)


def _face_normal(tri: list[Vec3]) -> Vec3:
    """Unit normal of a roof plane, always the up-slope side."""
    a, b, c = tri
    ab = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    ac = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    nx = ab[1] * ac[2] - ab[2] * ac[1]
    ny = ab[2] * ac[0] - ab[0] * ac[2]
    nz = ab[0] * ac[1] - ab[1] * ac[0]
    length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    nx, ny, nz = nx / length, ny / length, nz / length
    return (-nx, -ny, -nz) if nz < 0 else (nx, ny, nz)


def _offsetter(triangles: list[list[Vec3]]):
    """Offset the surface perpendicular to its slope with a mitered ridge: average over the
    distinct *planes* (not triangles) meeting at each shared vertex."""
    normals = [_face_normal(t) for t in triangles]
    planes: dict[str, dict[str, Vec3]] = {}
    for i, tri in enumerate(triangles):
        for v in tri:
            per = planes.setdefault(_vertex_key(v), {})
            per[",".join(f"{c:.5f}" for c in normals[i])] = normals[i]
    miters: dict[str, Vec3] = {}
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

    def offset_at(v: Vec3, distance: float) -> Vec3:
        mx, my, mz = miters[_vertex_key(v)]
        return (v[0] + mx * distance, v[1] + my * distance, v[2] + mz * distance)

    return offset_at


def _boundary_edges(triangles: list[list[Vec3]]):
    """Edges used by exactly one triangle — the eave/rake perimeter to close for thickness."""
    counts: dict[str, list] = {}
    for tri in triangles:
        for i in range(3):
            a, b = tri[i], tri[(i + 1) % 3]
            key = "|".join(sorted((_vertex_key(a), _vertex_key(b))))
            if key in counts:
                counts[key][1] += 1
            else:
                counts[key] = [(a, b), 1]
    return [edge for edge, count in counts.values() if count == 1]


def layer_inset_rect(roof: ResolvedRoof, entry: dict,
                     base_offset: float) -> tuple[float, float, float, float]:
    """Per-layer inset rectangle from serialized edge setbacks + eave-drift compensation.

    Offsetting a layer perpendicular to the slope drifts its eave edge down-slope (outward)
    by ``base_offset x sin(theta)``, so that drift is added to the eave-edge insets; rake
    edges run parallel to the fall line and have none.
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


def _band_mesh(triangles: list[list[Vec3]], offset_at, perimeter, base: float,
               top: float) -> GMesh:
    """One layer as a closed solid: top skin, bottom skin, and the perimeter that joins them."""
    positions: list[Vec3] = []
    faces: list[tuple[int, int, int]] = []

    def face(a: Vec3, b: Vec3, c: Vec3) -> None:
        index = len(positions)
        positions.extend((a, b, c))
        faces.append((index, index + 1, index + 2))

    for tri in triangles:  # top skin (up) + bottom skin (reversed, down)
        face(offset_at(tri[0], top), offset_at(tri[1], top), offset_at(tri[2], top))
        face(offset_at(tri[0], base), offset_at(tri[2], base), offset_at(tri[1], base))
    for a, b in perimeter:  # close the eave/rake so the layer reads as real thickness
        face(offset_at(a, base), offset_at(b, base), offset_at(b, top))
        face(offset_at(a, base), offset_at(b, top), offset_at(a, top))
    return GMesh(positions=tuple(positions), triangles=tuple(faces))


def roof_parts(roof: ResolvedRoof, assembly) -> tuple[GPart, ...]:
    """The roof's above-structure assembly stack, one part per layer, outboard-going.

    ``assembly`` is the resolved :class:`Assembly` for ``roof.assembly`` (``None`` when the
    roof names none), looked up by the caller so this module stays free of the library.
    """
    triangles = plane_triangles(roof)
    offset_at = _offsetter(triangles)
    perimeter = _boundary_edges(triangles)
    layers = above_structure_layers(assembly)
    setbacks = {entry["layer"]: entry for entry in (roof.layer_edge_setbacks or ())}

    parts: list[GPart] = []
    base = 0.0
    for layer in (layers if layers else [None]):
        if layer is None:
            name, thickness = "roofing", _FALLBACK_THICKNESS_M
            material_ref, function = _FALLBACK_MATERIAL_REF, _FALLBACK_FUNCTION
        else:
            name, thickness = layer.name, layer.thickness.meters
            material_ref, function = layer.material_ref, layer.function.value
        entry = setbacks.get(name) if layer is not None else None
        if entry is not None:
            layer_triangles = plane_triangles(roof, layer_inset_rect(roof, entry, base))
            band = _band_mesh(layer_triangles, _offsetter(layer_triangles),
                              _boundary_edges(layer_triangles), base, base + thickness)
        else:
            band = _band_mesh(triangles, offset_at, perimeter, base, base + thickness)
        parts.append(GPart(key=f"layer:{name}", solids=(band,),
                           material_key=layer_material_key(material_ref, function),
                           layer_group=layer_visibility_group(function)))
        base += thickness
    return tuple(parts)
