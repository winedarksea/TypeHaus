"""Detail dimension strings read off the resolved stack (C7-E4).

Every string measures resolved geometry — layer intervals, footing and floor members, the
opening's seat — so an assembly change re-labels the drawing. Strings print at 1/8": a
detail is where the fraction is the point.
"""

from __future__ import annotations

from typehaus.emit.draw.detail_components.below_grade import footing_under
from typehaus.emit.draw.detail_components.geometry import (
    floor_band_at,
    layer_intervals,
    outboard_is_high,
    outermost_with_function,
    wall_cut_bounds_m,
)
from typehaus.emit.draw.plan_labels import feet_inches, inches_fraction
from typehaus.emit.draw.scene import ArchDimension, IRNode, NamedPoint, Text
from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry_slice import CutPlane, ring_intervals


def dim_text(inches: float) -> str:
    """A detail string at 1/16" (I3-104: 84 1/16" headroom printed 7'-0 1/8"):
    ``6 5/8"`` under a foot, ``2'-10 1/16"`` over."""
    text = feet_inches(abs(inches), denominator=16)
    if text.startswith("0'-"):
        text = text[3:]
    return text[2:] if text.startswith("0 ") else text


def dim(p0, p1, offset: float, text: str | None = None,
        along: float = 0.0) -> ArchDimension:
    """A linear string between two measured points; ``text`` defaults to the 1/8" length.

    ``along`` slides the label off a string too short to hold it (the writer leaders it)."""
    length = ((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2) ** 0.5
    return ArchDimension(kind="linear", ends=(NamedPoint(xy=p0), NamedPoint(xy=p1)),
                         p0=p0, p1=p1, offset=offset, text_along=along,
                         text=text if text is not None else dim_text(length))


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
    # behind it — the same reading ``resolve.rainscreen_closures._vented_band`` takes to size the
    # insect strip, and the reason the vent is the slice nearest the cladding.
    if abs(b_lo - hi) <= abs(b_hi - lo):
        return (lo, max(hi, b_lo + packed), total + packed, "ext. insul.")
    return (min(lo, b_hi - packed), hi, total + packed, "ext. insul.")


def _outboard_insulation_run(wall, intervals: dict) -> list:
    """``[(interval, label)]`` for the insulation contiguous outboard of the structure.

    Membranes between the pour and the first board are stepped over; anything else ends the
    run, so an ICF core's inside and outside EPS are never summed across the concrete."""
    names = list(intervals)
    structure = [i for i, n in enumerate(names) if intervals[n][2] == "structure"]
    if not structure:
        return []
    material = {layer.name: layer.material_ref for layer in wall.layers}
    run: list = []
    for name in names[structure[-1] + 1:]:
        if intervals[name][2] == "insulation":
            ref = material.get(name, "").lower()
            run.append((intervals[name], "XPS" if "xps" in ref
                        else "EPS" if "eps" in ref else ref or name))
        elif run:
            break
    return run




def framed_strings(framed, direction: str, station: float, z_here: float,
                   z_hi: float) -> list[IRNode]:
    """CI total and stud depth across a framed wall at ``z_here`` (stud 8" above if room)."""
    nodes: list[IRNode] = []
    intervals = layer_intervals(framed, direction, station)
    ci = _continuous_insulation(framed, intervals)
    if ci is not None and outboard_is_high(framed, direction, station) is not None:
        lo, hi, total, label = ci
        nodes.append(dim((lo, z_here), (hi, z_here), 4.0, f'{inches_fraction(total)} {label}'))
    stud = outermost_with_function(intervals, "structure")
    stud_z = z_here + 8.0 if z_here + 8.0 <= z_hi else z_here - 8.0
    if stud is not None:
        nodes.append(dim((stud[0], stud_z), (stud[1], stud_z), 3.0,
                         f'{inches_fraction(abs(stud[1] - stud[0]))} stud'))
    return nodes


def concrete_strings(concrete, crop, direction: str, station: float) -> list[IRNode]:
    """The outboard XPS run on a pour, at the wall's mid-height AS CROPPED (D2-009)."""
    intervals = layer_intervals(concrete, direction, station)
    xps = _outboard_insulation_run(concrete, intervals)
    if not xps or outboard_is_high(concrete, direction, station) is None:
        return []
    total = sum(abs(iv[1] - iv[0]) for iv, _m in xps)
    (_u0, cz0), (_u1, cz1) = crop
    z_lo = max(concrete.z0_m, min(cz0, cz1))
    z_hi = min(concrete.z1_m, max(cz0, cz1))
    z_here = (z_lo + z_hi) / 2.0 / M_PER_IN
    names = sorted({m for _iv, m in xps})
    plies = f" ({len(xps)} layers)" if len(xps) > 1 else ""
    return [dim((min(iv[0] for iv, _m in xps), z_here), (max(iv[1] for iv, _m in xps), z_here),
                3.0, f'{inches_fraction(total)} {"/".join(names)}{plies}')]


def footing_strings(model, wall, crop, direction: str, station: float,
                    note: bool = False) -> list[IRNode]:
    """Footing width, depth and toes when it is in frame; else a size/bearing note (F5-011).

    A junction crop often stops above the footing; the note under the wall still states
    the footing a reader would otherwise have to find on S-100.
    """
    footing = footing_under(model, wall) if wall is not None else None
    if footing is None:
        return []
    ivs = ring_intervals(footing.outline, CutPlane(axis=direction, station_m=station))
    w_lo, w_hi = wall_cut_bounds_m(wall, direction, station)
    if not ivs or w_lo is None:
        return []
    f_lo = min(min(iv) for iv in ivs) / M_PER_IN
    f_hi = max(max(iv) for iv in ivs) / M_PER_IN
    w_lo, w_hi = w_lo / M_PER_IN, w_hi / M_PER_IN
    core = outermost_with_function(layer_intervals(wall, direction, station), "structure")
    if core is not None:  # toes off the pour, not its insulation
        w_lo, w_hi = min(core[0], core[1]), max(core[0], core[1])
    top, bottom = footing.z1_m / M_PER_IN, footing.z0_m / M_PER_IN
    toes = (w_lo - f_lo, f_hi - w_hi)
    (cu0, cz0), (cu1, cz1) = crop
    lo_z, hi_z = min(cz0, cz1), max(cz0, cz1)
    if lo_z <= footing.z0_m and footing.z1_m <= hi_z:
        # Below the bedding: toe | wall | toe, then the overall; depth off the outer toe.
        chain_z, overall_z = bottom - 8.5, bottom - 13.0
        nodes = [dim((f_lo, overall_z), (f_hi, overall_z), 0.0,
                     f'{dim_text(f_hi - f_lo)} ftg'),
                 dim((f_lo - 6.0, bottom), (f_lo - 6.0, top), 0.0,
                     f'{dim_text(top - bottom)} ftg')]
        stations = [f_lo, *(u for u, toe in ((w_lo, toes[0]),) if toe > 0.5),
                    *(u for u, toe in ((w_hi, toes[1]),) if toe > 0.5), f_hi]
        if len(stations) > 2:
            nodes += [dim((a, chain_z), (b, chain_z), 0.0)
                      for a, b in zip(stations, stations[1:], strict=False)]
        return nodes
    if not note:
        return []
    toe_text = " / ".join(dim_text(t) for t in toes if t > 0.5)
    text = (f'FTG {dim_text(f_hi - f_lo)} x {dim_text(top - bottom)}'
            + (f' · TOES {toe_text}' if toe_text else '')
            + f' · BRG EL. {feet_inches(bottom, denominator=8)}')
    # Under the drawing, beside its caption: the wall stops above the footing in this view.
    return [Text(anchor=(min(cu0, cu1) / M_PER_IN, lo_z / M_PER_IN - 10.0), content=text,
                 height_pt=6.5, layer="A-ANNO-DIMS")]


def band_strings(model, lower, junction_z_m: float, crop) -> list[IRNode]:
    """The floor band at a rim, joists plus subfloor (F3-004), as a note under the drawing.

    A vertical string here lands on the layer ladder or the continuity column, whichever
    side it takes; the note beside the caption overprints neither."""
    band = floor_band_at(model, junction_z_m)
    if band is None or lower is None:
        return []
    z0, z1 = band
    deck = next((f for f in model.floors
                 if f.deck_z0_m is not None and abs(f.deck_z0_m - z1) < 0.01), None)
    top = deck.deck_z1_m if deck is not None else z1
    text = f"FLOOR BAND {dim_text((top - z0) / M_PER_IN)}: {dim_text((z1 - z0) / M_PER_IN)} JOIST"
    if deck is not None:
        text += f" + {dim_text((top - z1) / M_PER_IN)} SUBFLOOR"
    (cu0, cz0), (cu1, cz1) = crop
    return [Text(anchor=(min(cu0, cu1) / M_PER_IN, min(cz0, cz1) / M_PER_IN - 10.0),
                 content=text, height_pt=6.5, layer="A-ANNO-DIMS")]


def dimension_strings(model, derived, crop, direction, station,
                      part: str | None = None) -> list[IRNode]:
    """Every string a derived detail carries, by junction kind.

    An opening detail's crop holds the opening, not a junction: it takes the R.O. and the
    unit's own strings. Elsewhere: CI and stud on the framed wall, XPS on the pour, the
    floor band at a rim, and the footing (or its note) under a foundation wall.
    """
    from typehaus.emit.draw.detail_components.geometry import condition_walls
    from typehaus.emit.draw.detail_components.opening_unit import opening_strings

    walls = condition_walls(model, derived.condition)
    if derived.condition.kind.value == "opening_perimeter":
        return opening_strings(model, derived, walls[0] if walls else None, crop,
                               direction, station, part)
    framed = next((w for w in walls if not w.is_foundation), None)
    concrete = next((w for w in walls if w.is_foundation), None)
    nodes: list[IRNode] = []
    if framed is not None:
        junction_z = framed.z0_m / M_PER_IN
        top = (framed.top_z1_m if framed.top_z1_m is not None else framed.z1_m) / M_PER_IN
        # At a wall→roof junction the band just under the plate is roofed over: drop the
        # pair low enough that both strings sit in clear wall.
        drop = 16.0 if derived.condition.kind.value == "wall_roof" else 6.0
        z_here = junction_z + 6.0 if concrete is not None else top - drop
        # Keep both strings on the wall as CROPPED (D2-009), not the whole storey's wall.
        vis_lo = max(junction_z, min(crop[0][1], crop[1][1]) / M_PER_IN) + 2.0
        vis_hi = min(top, max(crop[0][1], crop[1][1]) / M_PER_IN) - 2.0
        if vis_hi > vis_lo:
            z_here = min(max(z_here, vis_lo), vis_hi)
        nodes += framed_strings(framed, direction, station, z_here, vis_hi)
    if concrete is not None:
        nodes += concrete_strings(concrete, crop, direction, station)
    if derived.condition.kind.value == "storey_stack" and "rim" in derived.key.split(":"):
        lower = min(walls, key=lambda w: w.z0_m) if walls else None
        if lower is not None:
            nodes += band_strings(model, lower, lower.z1_m, crop)
    footing_wall = concrete if concrete is not None else framed
    nodes += footing_strings(model, footing_wall, crop, direction, station,
                             note=derived.condition.kind.value == "wall_foundation")
    return nodes


def wall_stack_strings(model, view, crop, direction: str, station: float) -> list[IRNode]:
    """The derived strings for an AUTHORED cut: each pour's XPS and its footing in frame.

    Framed CI/stud strings are left to the layer ladder here: an authored section is drawn
    at whatever scale its crop admits, and a 7 pt string across a 14" wall at 3/16" prints
    over its neighbours.
    """
    from typehaus.emit.draw.detail_components.geometry import wall_in_frame

    (_u0, cz0), (_u1, cz1) = crop
    lo_z, hi_z = min(cz0, cz1), max(cz0, cz1)
    nodes: list[IRNode] = []
    for wall in model.walls:
        top = wall.top_z1_m if wall.top_z1_m is not None else wall.z1_m
        if not wall.is_foundation or top < lo_z or wall.z0_m > hi_z:
            continue
        if not wall_in_frame(wall, direction, station, crop):
            continue
        nodes += concrete_strings(wall, crop, direction, station)
        nodes += footing_strings(model, wall, crop, direction, station)
    return nodes
