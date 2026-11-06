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
    outermost_with_function,
    wall_cut_bounds_m,
)
from typehaus.emit.draw.plan_labels import feet_inches
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
    unit's own strings. Elsewhere: the floor band at a rim, and the footing (or its note)
    under a foundation wall.
    """
    from typehaus.emit.draw.detail_components.geometry import condition_walls
    from typehaus.emit.draw.detail_components.opening_unit import opening_strings

    walls = condition_walls(model, derived.condition)
    if derived.condition.kind.value == "opening_perimeter":
        return opening_strings(model, derived, walls[0] if walls else None, crop,
                               direction, station, part)
    framed = next((w for w in walls if not w.is_foundation), None)
    concrete = next((w for w in walls if w.is_foundation), None)
    # No CI / stud / XPS strings across a stack: the layer ladder names every one of those
    # layers with its thickness, and a second tag floated off the wall (D2-009, F5-107).
    nodes: list[IRNode] = []
    if derived.condition.kind.value == "storey_stack" and "rim" in derived.key.split(":"):
        lower = min(walls, key=lambda w: w.z0_m) if walls else None
        if lower is not None:
            nodes += band_strings(model, lower, lower.z1_m, crop)
    footing_wall = concrete if concrete is not None else framed
    nodes += footing_strings(model, footing_wall, crop, direction, station,
                             note=derived.condition.kind.value == "wall_foundation")
    return nodes


def wall_stack_strings(model, view, crop, direction: str, station: float) -> list[IRNode]:
    """The derived strings for an AUTHORED cut: each pour's footing in frame (its layers
    are the ladder's)."""
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
        nodes += footing_strings(model, wall, crop, direction, station)
    return nodes
