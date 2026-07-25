"""Detail chrome: the material legend band and the derived dimension strings.

Both read the resolved layer thicknesses rather than authored numbers, so a change to an
assembly re-labels the drawing instead of silently leaving a stale dimension on the sheet.
Both emit ordinary IR nodes (``Hatch``/``Polyline``/``Text``/``ArchDimension``).
"""

from __future__ import annotations

from typehaus.emit.draw.detail_components.config import (
    LAYER,
    LEGEND_ROW_PITCH_IN,
    LEGEND_SWATCH_IN,
    M_TO_IN,
    TEXT_HEIGHT_IN,
)
from typehaus.emit.draw.detail_components.below_grade import footing_under
from typehaus.emit.draw.detail_components.geometry import (
    layer_intervals,
    outboard_is_high,
    outermost_with_function,
    rect_points,
)
from typehaus.emit.draw.scene import ArchDimension, Hatch, IRNode, NamedPoint, Polyline, Text


def _participating_layers(model, derived):
    """``(material_ref, thickness_in, function)`` for every cut layer in this detail."""
    out: list[tuple[str, float, str]] = []
    for tag in derived.condition.element_tags:
        wall = model.wall(tag)
        if wall is None:
            continue
        for layer in wall.layers:
            if layer.is_cavity:
                continue
            out.append((layer.material_ref, layer.thickness_m * M_TO_IN, layer.function))
    for roof in model.roofs:
        if roof.tag not in derived.condition.element_tags:
            continue
        asm = model.plan.library.resolve_assembly(roof.assembly)
        if asm is None:
            continue
        for layer in asm.layers:
            out.append((layer.material_ref, layer.thickness.meters * M_TO_IN,
                        layer.function))
    return out


def material_legend(model, derived, u_left: float, z_top: float) -> list[IRNode]:
    """One swatch + label per distinct material in the cut, with its resolved thickness."""
    seen: dict[str, float] = {}
    order: list[str] = []
    for material, thickness, _function in _participating_layers(model, derived):
        if material and material not in seen:
            seen[material] = thickness
            order.append(material)
    if not order:
        return []
    from typehaus.emit.draw.palette import detail_hatch

    nodes: list[IRNode] = [
        Text(anchor=(u_left, z_top + 3.0), content="MATERIALS", height=TEXT_HEIGHT_IN,
             layer="A-ANNO-TEXT")
    ]
    for index, material in enumerate(order):
        y1 = z_top - index * LEGEND_ROW_PITCH_IN
        y0 = y1 - LEGEND_SWATCH_IN
        # ``metal`` maps to a no-overlay fill in both writers (and the UI), so the swatch
        # reads as its material fill when the material has no hatch family of its own.
        pattern = detail_hatch(material) or "metal"
        boundary = rect_points(u_left, y0, u_left + LEGEND_SWATCH_IN, y1)
        nodes.append(Hatch(boundary=boundary, pattern=pattern, layer=LAYER,
                           material=material))
        nodes.append(Polyline(points=boundary, layer=LAYER, closed=True, lineweight=0.2))
        nodes.append(Text(anchor=(u_left + LEGEND_SWATCH_IN + 1.5, (y0 + y1) / 2),
                          content=f'{material}  {seen[material]:.3g}"',
                          height=TEXT_HEIGHT_IN, layer="A-ANNO-TEXT"))
    return nodes


def _continuous_insulation(intervals: dict):
    """``(u_lo, u_hi, total_in)`` of the continuous exterior-insulation band, if any."""
    insulation = [iv for iv in intervals.values() if iv[2] == "insulation"]
    if not insulation:
        return None
    return (min(iv[0] for iv in insulation), max(iv[1] for iv in insulation),
            sum(abs(iv[1] - iv[0]) for iv in insulation))


def dimension_strings(model, derived, crop, direction, station) -> list[IRNode]:
    """``ArchDimension`` strings derived from the resolved layer thicknesses.

    Total continuous insulation and stud depth on the framed wall; XPS layer count ×
    thickness on the foundation side; footing width and depth when the footing is in frame.
    """
    from typehaus.emit.draw.section import _ring_cut_intervals

    nodes: list[IRNode] = []
    walls = [w for w in (model.wall(t) for t in derived.condition.element_tags)
             if w is not None]
    framed = next((w for w in walls if not w.is_foundation), None)
    concrete = next((w for w in walls if w.is_foundation), None)

    def _dim(p0, p1, offset, text):
        nodes.append(ArchDimension(
            kind="linear", ends=(NamedPoint(xy=p0), NamedPoint(xy=p1)),
            p0=p0, p1=p1, offset=offset, text=text))

    if framed is not None:
        intervals = layer_intervals(framed, direction, station)
        junction_z = framed.z0_m * M_TO_IN
        top = (framed.top_z1_m if framed.top_z1_m is not None else framed.z1_m) * M_TO_IN
        z_here = junction_z + 6.0 if concrete is not None else top - 6.0
        ci = _continuous_insulation(intervals)
        if ci is not None and outboard_is_high(framed, direction, station) is not None:
            lo, hi, total = ci
            _dim((lo, z_here), (hi, z_here), 4.0, f'{total:.3g}" CI')
        stud = outermost_with_function(intervals, "structure")
        if stud is not None:
            _dim((stud[0], z_here + 8.0), (stud[1], z_here + 8.0), 3.0,
                 f'{abs(stud[1] - stud[0]):.3g}" stud')

    if concrete is not None:
        intervals = layer_intervals(concrete, direction, station)
        xps = [iv for iv in intervals.values() if iv[2] == "insulation"]
        if xps and outboard_is_high(concrete, direction, station) is not None:
            total = sum(abs(iv[1] - iv[0]) for iv in xps)
            z_here = (concrete.z0_m + concrete.z1_m) / 2.0 * M_TO_IN
            _dim((min(iv[0] for iv in xps), z_here), (max(iv[1] for iv in xps), z_here),
                 3.0, f'{total:.3g}" XPS ({len(xps)} layers)')

    # Footing width + depth, from the resolved strip footing — drawn only when the footing is
    # actually in the crop, so a wall-top junction (footing out of frame) gets neither.
    (_cu0, cz0), (_cu1, cz1) = crop
    lo_z, hi_z = min(cz0, cz1), max(cz0, cz1)
    footing_wall = concrete if concrete is not None else framed
    footing = footing_under(model, footing_wall) if footing_wall is not None else None
    if footing is not None and lo_z <= footing.z0_m and footing.z1_m <= hi_z:
        intervals_f = _ring_cut_intervals(footing.outline, direction, station)
        if intervals_f:
            f_lo = min(min(iv) for iv in intervals_f) * M_TO_IN
            f_hi = max(max(iv) for iv in intervals_f) * M_TO_IN
            top, bottom = footing.z1_m * M_TO_IN, footing.z0_m * M_TO_IN
            _dim((f_lo, bottom - 3.0), (f_hi, bottom - 3.0), 3.0,
                 f'{f_hi - f_lo:.3g}" ftg width')
            _dim((f_lo - 3.0, bottom), (f_lo - 3.0, top), 3.0,
                 f'{top - bottom:.3g}" ftg depth')
    return nodes
