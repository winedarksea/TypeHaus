"""What the geometry IR deliberately does not carry — the fills, drawn by hand.

``geometry_build`` gives a cavity no solid: a batt shares its host structure layer's
polygon, so a second solid there would z-fight the studs in 3D. That omission is right for
the model and wrong for a *section*, because a batt between studs is exactly what the
drawing is cut to show — a roof that reads as 11-7/8" of solid timber is not a drawing of
this roof. So the fills are drawn here, from the resolved layer, unoutlined, and clipped to
the bay they actually occupy.

The opening split lives here for the same reason. ``geometry_walls.layer_solids`` jamb-splits
every layer that *has* a solid; a cavity has none, so the split around a window has to happen
on this side or the batt draws straight across the glass.

The real fix for the wall case is to emit the cavity as a solid inset to the framing bay,
which does not z-fight. That is its own geometry change with its own risk, and until it lands
this module is the honest statement of what the section knows that the IR does not.
"""

from __future__ import annotations

from typehaus.emit.draw.palette import aia_layer, detail_hatch
from typehaus.emit.draw.scene import Hatch
from typehaus.emit.draw.section_clip import clip_polygon, clip_rect, quad_nodes, rect_nodes
from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry_slice import CutPlane, ring_intervals
from typehaus.resolve.roof_geometry import roof_plane_z, roof_ridge_coordinate
from typehaus.resolve.roof_layer_setbacks import assembly_layer_spans, structure_datum_m


def emit_wall_cavity(b, model, wall, plane: CutPlane, crop, is_detail, min_draw,
                     wall_top, joints=None) -> None:
    """The batt between the studs, which the IR deliberately does not carry.

    ``geometry_build._wall_geometry`` skips cavity layers because a second solid on the
    structure layer's own polygon would z-fight it in 3D. For a section that omission is
    wrong — a batt between studs is exactly what the drawing is cut to show — so the fill is
    drawn here from the resolved layer, **unoutlined**, the way the roof's ``_CavityBand``
    is. The real fix is to emit the cavity as a solid *inset to the framing bay*, which does
    not z-fight; that is its own geometry change with its own risk.
    """
    openings = [op for op in model.openings if op.host_wall == wall.tag]
    for layer in wall.layers:
        if not layer.is_cavity or not layer.polygon:
            continue
        term = joints.termination(wall.uid, layer.name) if joints is not None else None
        band_z0, band_z1 = layer.band(wall)
        pattern = detail_hatch(layer.material_ref, layer.function)
        aia = aia_layer(layer.function)
        tag = f"{wall.tag}/{layer.name}"
        for (u0, u1) in ring_intervals(layer.polygon, plane):
            top_left = term.z(u0) if term is not None else min(wall_top, band_z1)
            top_right = term.z(u1) if term is not None else min(wall_top, band_z1)
            rect = clip_rect(u0, u1, band_z0, max(top_left, top_right), crop)
            if rect is None:
                continue
            ru0, ru1, rz0, rz1 = rect
            if is_detail and 0 < (ru1 - ru0) < min_draw:
                grow = (min_draw - (ru1 - ru0)) / 2.0
                ru0, ru1 = ru0 - grow, ru1 + grow
            if abs(top_left - top_right) > 1e-6:
                b.extend(quad_nodes(ru0, ru1, rz0, min(top_left, rz1), min(top_right, rz1),
                                    aia, pattern, wall.uid, tag,
                                    material=layer.material_ref, outline=False))
                continue
            # The IR jamb-splits every depth layer; a cavity has no IR solid, so the split
            # around an opening has to happen here or the batt draws across the window.
            for (z0, z1, void) in opening_splits(wall, openings, plane.axis,
                                                  plane.station_m, rz0, rz1):
                if void:
                    continue
                b.extend(rect_nodes(ru0, ru1, z0, z1, aia, pattern, wall.uid, tag,
                                    outline=False, material=layer.material_ref))

def opening_splits(wall, openings, direction, station, z0, z1):
    """Split a wall's z-band where the cut passes through an opening."""
    (sx, sy), (ex, ey) = wall.axis
    length = ((ex - sx) ** 2 + (ey - sy) ** 2) ** 0.5
    if length < 1e-9:
        return [(z0, z1, False)]
    # Station of the cut along the wall axis (only meaningful when the cut crosses it).
    a0, a1 = (sy, ey) if direction == "x" else (sx, ex)
    if (a0 - station) * (a1 - station) > 0:
        return [(z0, z1, False)]
    denominator = (a1 - a0) or 1e-12
    t = (station - a0) / denominator
    s = t * length
    bands: list[tuple[float, float, bool]] = []
    cut_openings = [
        op for op in openings
        if op.center_along_m - op.width_m / 2 <= s <= op.center_along_m + op.width_m / 2
    ]
    if not cut_openings:
        return [(z0, z1, False)]
    op = cut_openings[0]
    sill_z = wall.z0_m + op.sill_m
    head_z = sill_z + op.height_m
    if sill_z > z0:
        bands.append((z0, min(sill_z, z1), False))
    v0, v1 = max(sill_z, z0), min(head_z, z1)
    if v1 > v0:
        bands.append((v0, v1, True))
    if head_z < z1:
        bands.append((max(head_z, z0), z1, False))
    return bands or [(z0, z1, False)]

def _rafter_plan_span(roof, direction: str) -> tuple[float, float] | None:
    """The rafters' in-section (u) extent — where the framed structure actually ends.

    A zero-overhang roof's structure layer stops at the rafters' plumb-cut tails (the
    bearing wall's stud face), well inboard of a footprint edge that laps the wall
    cladding. ``None`` when the roof has no rafter members (truss roofs keep the
    uniform footprint band).
    """
    axis = 0 if direction == "x" else 1
    coords = [point[axis] for member in roof.members if member.category == "rafter"
              for point in (member.p0, member.p1)]
    if not coords:
        return None
    return min(coords), max(coords)

def roof_cavity_bands(asm):
    """``(layer, d0, d1)`` for each cavity fill, in the same datum frame.

    The batt between the rafters is not a layer of its own — it shares the bay's depth — so
    ``geometry_build`` does not give it a solid (it would z-fight the structure) and the IR
    cannot answer for it. It is the difference between a roof that reads as 11-7/8" of solid
    timber and one that reads as a batt between rafters, which is what the section is cut to
    show, so it is drawn here from the assembly. Held to the ceiling side: the remaining bay
    depth stays open.
    """
    datum = structure_datum_m(asm)
    bands = []
    for (layer, c0, c1) in assembly_layer_spans(asm):
        cavity = getattr(layer, "cavity", None)
        if cavity is None:
            continue
        fill = cavity.thickness.meters if cavity.thickness is not None else c1 - c0
        bands.append((_CavityBand(layer, cavity), datum - (c0 + fill), datum - c0))
    return bands


class _CavityBand:
    """A cavity fill dressed as a ``Layer`` so one band loop draws both.

    It borrows the host structure layer's function on purpose: the fill is clipped by the
    rafter plan span, exactly as its bay is, and carries no edge setback of its own.
    """

    __slots__ = ("name", "material_ref", "function", "_cavity")

    def __init__(self, host, cavity) -> None:
        self.name = f"{host.name} fill"
        self.material_ref = cavity.material_ref
        self.function = host.function
        self._cavity = cavity

def emit_roof_cavity(b, roof, asm, plane: CutPlane, crop) -> None:
    """The bay fill, as a sloped band under the structure datum, clipped to the rafters."""
    bands = roof_cavity_bands(asm)
    if not bands:
        return
    intervals = ring_intervals(tuple(roof.footprint), plane)
    if not intervals:
        return
    ridge_u = roof_ridge_coordinate(roof)
    slope_along_cut = (
        (roof.ridge_direction == "y" and plane.axis == "x")
        or (roof.ridge_direction == "x" and plane.axis == "y")
    )
    structure_span = _rafter_plan_span(roof, plane.axis)

    def top_line(a: float, b_: float) -> list[tuple[float, float]]:
        if slope_along_cut:
            fold = [ridge_u] if ridge_u is not None and a < ridge_u < b_ else []
            return [(u, roof_plane_z(roof, u)) for u in ([a] + fold + [b_])]
        z = roof_plane_z(roof, plane.station_m)
        return [(a, z), (b_, z)]

    for (u0, u1) in intervals:
        for (layer, d0, d1) in bands:
            a, b_ = u0, u1
            if structure_span is not None:
                a, b_ = max(a, structure_span[0]), min(b_, structure_span[1])
            if b_ - a < 1e-9:
                continue
            top = top_line(a, b_)
            polygon = ([(u, z - d0) for (u, z) in top]
                       + [(u, z - d1) for (u, z) in reversed(top)])
            clipped = clip_polygon(polygon, crop)
            if len(clipped) < 3:
                continue
            pts = tuple((u / M_PER_IN, z / M_PER_IN) for (u, z) in clipped)
            b.add(Hatch(boundary=pts,
                        pattern=detail_hatch(layer.material_ref, layer.function.value)
                        or "batt",
                        layer="A-WALL-PATT", uid=roof.uid, material=layer.material_ref))
