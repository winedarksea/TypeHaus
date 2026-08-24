"""Detail chrome: the material legend band and the derived dimension strings.

Both read the resolved layer thicknesses rather than authored numbers, so a change to an
assembly re-labels the drawing instead of silently leaving a stale dimension on the sheet.
Both emit ordinary IR nodes (``Hatch``/``Polyline``/``Text``/``ArchDimension``).
"""

from __future__ import annotations

from typehaus.emit.draw.detail_components.below_grade import footing_under
from typehaus.emit.draw.detail_components.config import (
    LAYER,
    LEGEND_ROW_PITCH_IN,
    LEGEND_SWATCH_IN,
    TEXT_HEIGHT_IN,
)
from typehaus.emit.draw.detail_components.geometry import (
    layer_intervals,
    outboard_is_high,
    outermost_with_function,
    rect_points,
)
from typehaus.emit.draw.scene import ArchDimension, Hatch, IRNode, NamedPoint, Polyline, Text
from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry_slice import CutPlane, ring_intervals


def _participating_layers(model, derived):
    """``(material_ref, thickness_in, function)`` for every cut layer in this detail."""
    from typehaus.emit.draw.detail_components.geometry import condition_walls

    out: list[tuple[str, float, str]] = []
    for wall in condition_walls(model, derived.condition):
        for layer in wall.layers:
            if layer.is_cavity:
                continue
            out.append((layer.material_ref, layer.thickness_m / M_PER_IN, layer.function))
    tags = derived.condition.element_tags
    for roof in model.roofs:
        # By **assembly** as well as by element tag. A wall/roof condition is keyed on the
        # two assemblies it joins (``CATLIN_EXT_2X6|CATLIN_ROOF``), never on the roof
        # element's own tag (``RF-HOUSE``), so this loop matched nothing on the one detail
        # that is mostly roof: the eave legended its wall and left every roof layer out,
        # including the underlayment and the vent mat the notes spend a paragraph each on.
        if roof.tag not in tags and roof.assembly not in tags:
            continue
        asm = model.plan.library.resolve_assembly(roof.assembly)
        if asm is None:
            continue
        for layer in asm.layers:
            out.append((layer.material_ref, layer.thickness.meters / M_PER_IN,
                        layer.function))
    return out


def drawn_materials(scene) -> set[str]:
    """Every material that actually reaches the page, off the ``Hatch`` nodes themselves.

    ``_participating_layers`` reads the *assemblies* in the condition, which is not the same
    question: a layer whose band falls outside the crop, or which the cut misses entirely,
    is in the assembly and not in the drawing. Legending it invites a reader to look for
    something that is not there, and it is why the band ran a third longer than it needed to.
    """
    from typehaus.emit.draw.scene import Hatch

    return {node.material for node in getattr(scene, "nodes", ())
            if isinstance(node, Hatch) and node.material}


def material_legend(model, derived, u_left: float, z_top: float,
                    band=None, drawn: set[str] | None = None) -> list[IRNode]:
    """One swatch + label per distinct material in the cut, with its resolved thickness.

    With a ``band`` — ``(x, y, w, h)`` paper inches out of ``Frame.bands`` — the legend is
    laid out **in paper space**, in a strip whose size is a property of the card. It runs in
    columns across the strip rather than down a single tall list, because a legend that grew
    downward was the thing measuring itself against the drawing.
    """
    if band is not None:
        return _paper_legend(model, derived, band, drawn)
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


#: Paper-space legend metrics, inches.
_SWATCH_IN = 0.14
_ROW_PITCH_IN = 0.17
#: Three columns across a 6.45" strip. The widest label the catalog produces is
#: ``roof-underlayment-synthetic  0.06"`` — 33 monospace characters, 1.85" at _LEGEND_PT,
#: which clears this with the swatch and its gap.
_COL_W_IN = 2.15
_LEGEND_PT = 6.5


def _paper_legend(model, derived, band, drawn=None) -> list[IRNode]:
    from typehaus.emit.draw.palette import detail_hatch

    seen: dict[str, float] = {}
    for material, thickness, _function in _participating_layers(model, derived):
        if material and material not in seen and (drawn is None or material in drawn):
            seen[material] = thickness
    if not seen:
        return []
    x, y, w, h = band
    rows = max(1, int(h / _ROW_PITCH_IN) - 1)
    nodes: list[IRNode] = [
        Text(anchor=(x, y + h - _ROW_PITCH_IN * 0.4), content="MATERIALS",
             height_pt=_LEGEND_PT, layer="A-ANNO-TEXT", space="paper")
    ]
    for index, (material, thickness) in enumerate(seen.items()):
        column, row = divmod(index, rows)
        cx = x + column * _COL_W_IN
        if cx + _COL_W_IN > x + w + 1e-9:
            # The strip is full — a legend may not push the drawing off its own card. Say so
            # rather than stopping mid-list: a legend that quietly ends is read as complete,
            # and a reader then goes looking for a material the drawing never named.
            nodes.append(Text(
                anchor=(x + w, y + h - _ROW_PITCH_IN * 0.4), align="right",
                content=f"+{len(seen) - index} more (see notes)",
                height_pt=_LEGEND_PT, layer="A-ANNO-TEXT", space="paper"))
            break
        cy = y + h - _ROW_PITCH_IN * (row + 1.6)
        boundary = rect_points(cx, cy, cx + _SWATCH_IN, cy + _SWATCH_IN)
        nodes.append(Hatch(boundary=boundary, pattern=detail_hatch(material) or "metal",
                           layer=LAYER, material=material, space="paper"))
        nodes.append(Polyline(points=boundary, layer=LAYER, closed=True, lineweight=0.2,
                              space="paper"))
        nodes.append(Text(anchor=(cx + _SWATCH_IN + 0.06, cy + _SWATCH_IN / 2),
                          content=f'{material}  {thickness:.3g}"',
                          height_pt=_LEGEND_PT, layer="A-ANNO-TEXT", space="paper"))
    return nodes


def _continuous_insulation(wall, intervals: dict):
    """``(u_lo, u_hi, total_in, label)`` of the exterior insulation outboard of the frame.

    ``layer_intervals`` drops cavity fills, and it is right to — a stud bay's batt shares
    the structure layer's band, and counting it would print the cavity into a string that
    says CI. But a fill hosted by a **furring** layer is not a stud bay: it is foam packed
    into a rainscreen band, wholly outboard of the sheathing, and dropping it is how a truss
    wall carrying 4" of exterior foam came to dimension "1.5" CI" — the 2-1/2" in the
    outrigger bays, five eighths of the wall's exterior insulation, simply not counted.

    So the band is measured to the outermost insulated face, fill included. What it is
    CALLED changes with it: 2-1/2" of foam interrupted by outriggers at 16" o.c. is not
    continuous insulation, whatever it is worth thermally (``analysis`` parallel-paths it at
    a 9.4% framing factor), so a filled band prints "ext. insul." and only an unbroken board
    stack keeps the letters CI.
    """
    insulation = [iv for iv in intervals.values() if iv[2] == "insulation"]
    if not insulation:
        return None
    lo = min(iv[0] for iv in insulation)
    hi = max(iv[1] for iv in insulation)
    total = sum(abs(iv[1] - iv[0]) for iv in insulation)

    band = outermost_with_function(intervals, "furring")
    bands = {layer.name for layer in wall.layers
             if not getattr(layer, "is_cavity", False) and layer.function == "furring"}
    fill = next((layer for layer in wall.layers
                 if getattr(layer, "is_cavity", False) and layer.cavity_host in bands), None)
    if band is None or fill is None or fill.thickness_m <= 0.0:
        return (lo, hi, total, "CI")

    packed = fill.thickness_m / M_PER_IN
    b_lo, b_hi = min(band[0], band[1]), max(band[0], band[1])
    # The fill packs against the band's INBOARD face, hard up against the continuous boards
    # behind it — the same reading ``resolve.accessories._vented_band`` takes to size the
    # insect strip, and the reason the vent is the slice nearest the cladding.
    if abs(b_lo - hi) <= abs(b_hi - lo):
        return (lo, max(hi, b_lo + packed), total + packed, "ext. insul.")
    return (min(lo, b_hi - packed), hi, total + packed, "ext. insul.")


def dimension_strings(model, derived, crop, direction, station) -> list[IRNode]:
    """``ArchDimension`` strings derived from the resolved layer thicknesses.

    Total continuous insulation and stud depth on the framed wall; XPS layer count ×
    thickness on the foundation side; footing width and depth when the footing is in frame.
    """
    from typehaus.emit.draw.detail_components.geometry import (
        condition_opening,
        condition_walls,
        wall_cut_bounds_m,
    )

    nodes: list[IRNode] = []
    walls = condition_walls(model, derived.condition)
    framed = next((w for w in walls if not w.is_foundation), None)
    concrete = next((w for w in walls if w.is_foundation), None)

    def _dim(p0, p1, offset, text):
        nodes.append(ArchDimension(
            kind="linear", ends=(NamedPoint(xy=p0), NamedPoint(xy=p1)),
            p0=p0, p1=p1, offset=offset, text=text))

    # An opening detail's crop holds the opening, not a junction — the storey-band CI /
    # stud / footing strings would all land outside it. The one dimension the detail is
    # for is the rough opening height, hung just clear of the wall's cut band.
    if derived.condition.kind.value == "opening_perimeter":
        opening = condition_opening(model, derived.condition)
        host = walls[0] if walls else None
        if opening is None or host is None:
            return []
        sill_z = (host.z0_m + opening.sill_m) / M_PER_IN
        head_z = sill_z + opening.height_m / M_PER_IN
        _lo, hi = wall_cut_bounds_m(host, direction, station)
        if hi is None:
            return []
        u = hi / M_PER_IN + 3.0
        _dim((u, sill_z), (u, head_z), 3.0,
             f'{opening.height_m / M_PER_IN:.4g}" R.O.')
        return nodes

    if framed is not None:
        intervals = layer_intervals(framed, direction, station)
        junction_z = framed.z0_m / M_PER_IN
        top = (framed.top_z1_m if framed.top_z1_m is not None else framed.z1_m) / M_PER_IN
        # At a wall→roof junction the band just under the plate is roofed over — the
        # sloped assembly stack crosses the wall there, and a dimension string 6" below
        # the plate prints its text straight into the rafter hatch. Drop the pair low
        # enough that both strings sit in clear wall.
        drop = 16.0 if derived.condition.kind.value == "wall_roof" else 6.0
        z_here = junction_z + 6.0 if concrete is not None else top - drop
        ci = _continuous_insulation(framed, intervals)
        if ci is not None and outboard_is_high(framed, direction, station) is not None:
            lo, hi, total, label = ci
            _dim((lo, z_here), (hi, z_here), 4.0, f'{total:.3g}" {label}')
        stud = outermost_with_function(intervals, "structure")
        if stud is not None:
            _dim((stud[0], z_here + 8.0), (stud[1], z_here + 8.0), 3.0,
                 f'{abs(stud[1] - stud[0]):.3g}" stud')

    if concrete is not None:
        intervals = layer_intervals(concrete, direction, station)
        xps = [iv for iv in intervals.values() if iv[2] == "insulation"]
        if xps and outboard_is_high(concrete, direction, station) is not None:
            total = sum(abs(iv[1] - iv[0]) for iv in xps)
            z_here = (concrete.z0_m + concrete.z1_m) / 2.0 / M_PER_IN
            _dim((min(iv[0] for iv in xps), z_here), (max(iv[1] for iv in xps), z_here),
                 3.0, f'{total:.3g}" XPS ({len(xps)} layers)')

    # Footing width + depth, from the resolved strip footing — drawn only when the footing is
    # actually in the crop, so a wall-top junction (footing out of frame) gets neither.
    (_cu0, cz0), (_cu1, cz1) = crop
    lo_z, hi_z = min(cz0, cz1), max(cz0, cz1)
    footing_wall = concrete if concrete is not None else framed
    footing = footing_under(model, footing_wall) if footing_wall is not None else None
    if footing is not None and lo_z <= footing.z0_m and footing.z1_m <= hi_z:
        intervals_f = ring_intervals(
            footing.outline, CutPlane(axis=direction, station_m=station))
        if intervals_f:
            f_lo = min(min(iv) for iv in intervals_f) / M_PER_IN
            f_hi = max(max(iv) for iv in intervals_f) / M_PER_IN
            top, bottom = footing.z1_m / M_PER_IN, footing.z0_m / M_PER_IN
            _dim((f_lo, bottom - 3.0), (f_hi, bottom - 3.0), 3.0,
                 f'{f_hi - f_lo:.3g}" ftg width')
            _dim((f_lo - 3.0, bottom), (f_lo - 3.0, top), 3.0,
                 f'{top - bottom:.3g}" ftg depth')
    return nodes
