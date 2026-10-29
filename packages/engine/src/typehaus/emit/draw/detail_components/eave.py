"""The zero-overhang eave: what the cut cannot say on its own — vent screen, gutter support,
and the leaders naming the pieces and the three water paths.

The metal itself (the Image II eave, the pan ends, the strip-in, the gutter, the wall panel
heads) is real geometry the section already cuts; this overlay draws no metal of its own. The vent
screen draws only over a roof whose assembly carries an air gap above the deck.
"""

from __future__ import annotations

from typehaus.emit.draw.detail_components.config import SHEET_METAL
from typehaus.emit.draw.detail_components.eave_anchors import eave_cut
from typehaus.emit.draw.detail_components.eave_framing import eave_gutter_support
from typehaus.emit.draw.detail_components.eave_labels import (
    above_structure_bands,
    eave_labels,
    member_anchor,
    roof_labels,
    solid_anchor,
)
from typehaus.emit.draw.detail_components.eave_water import (
    eave_piece_labels,
    provisional_hanger,
)
from typehaus.emit.draw.detail_components.geometry import (
    face_of,
    layer_intervals,
    outboard_is_high,
    outermost_with_function,
    rect_region,
)
from typehaus.emit.draw.lineweights import PROFILE
from typehaus.emit.draw.scene import IRNode
from typehaus.emit.draw.typography import TEXT_PT
from typehaus.quantities import M_PER_IN
from typehaus.resolve.roof_geometry import roof_height_at, roof_slope_factor


def eave_frame(model, wall, direction, station):
    """``(roof, clad_out, junction_z, out_sign, slope)`` at a wall→roof eave, or ``None``."""
    is_outboard_high = outboard_is_high(wall, direction, station)
    if is_outboard_high is None:
        return None
    intervals = layer_intervals(wall, direction, station)
    weather_face = (outermost_with_function(intervals, "cladding")
                    or outermost_with_function(intervals, "furring"))
    if weather_face is None:
        return None
    clad_out = face_of(weather_face, is_outboard_high, outer=True)
    roof = _roof_over(model, direction, station, clad_out)
    junction_z = _junction_z_in(roof, wall, direction, station, clad_out)
    slope = roof_slope_factor(roof) if roof is not None else 1.0
    return roof, clad_out, junction_z, 1.0 if is_outboard_high else -1.0, slope


def zero_overhang_eave(model, wall, crop, direction, station,
                       scale=None) -> list[IRNode]:
    """Screened eave vent, gutter support and the water-chain leaders at a flush eave."""
    frame = eave_frame(model, wall, direction, station) if crop is not None else None
    if frame is None:
        return []
    roof, clad_out, junction_z, out_sign, slope = frame
    (_cu0, cz0), (_cu1, _cz1) = crop
    nodes: list[IRNode] = []
    nodes += eave_vent_intake(model, roof, clad_out, junction_z, out_sign, cz0 / M_PER_IN,
                              slope)
    support, support_labels = eave_gutter_support(model, clad_out, out_sign, direction,
                                                  station, crop)
    nodes += support
    at = (roof, direction, station, clad_out, junction_z)
    pieces = eave_cut(model, *at, out_sign)
    compact = scale is not None and scale < _ENLARGED_SCALE
    entries = roof_labels(model, roof, clad_out, junction_z, out_sign, slope,
                          roofing=pieces is None)  # the pan-hem leader names the pan
    if pieces is not None:
        entries += eave_piece_labels(pieces, compact=compact)
    else:
        entries.append((member_anchor(*at, "gutter")
                        or solid_anchor(model, direction, station, clad_out, junction_z,
                                        "gutter"), "gutter"))
    entries += provisional_hanger(support_labels, compact)
    entries = [(target, text) for target, text in entries
               if target is not None and _in_crop(target, crop)]
    # Top to bottom by what they point at, so the leaders fan out instead of crossing.
    entries.sort(key=lambda entry: -entry[0][1])
    # One and a half lines a row: the Image II eave carries a dozen leaders at 3/4" scale.
    nodes += eave_labels(entries, clad_out, junction_z, out_sign, scale, step_pt=1.5 * TEXT_PT)
    return nodes


def _in_crop(point, crop) -> bool:
    """Whether a leader target (inches) lies inside the crop (metres): off-sheet, it is dropped."""
    (cu0, cz0), (cu1, cz1) = crop
    u, z = point[0] * M_PER_IN, point[1] * M_PER_IN
    return min(cu0, cu1) <= u <= max(cu0, cu1) and min(cz0, cz1) <= z <= max(cz0, cz1)


def _cut_point(direction: str, station: float, u_in: float) -> tuple[float, float]:
    """A plan point from the section's own frame: ``u`` across the cut, ``station`` along it."""
    u_m = u_in * M_PER_IN
    return (u_m, station) if direction == "x" else (station, u_m)


def _roof_over(model, direction: str, station: float, clad_out_in: float):
    """The roof whose footprint covers the eave point, or ``None``.

    Containment is given an inch of slop deliberately: on a zero-overhang roof the wall's
    cladding face *is* the footprint edge, so an exact test lands on the boundary and its
    answer is a rounding coin-flip. Where roofs overlap the highest wins, which is the one
    the eave is under.
    """
    point = _cut_point(direction, station, clad_out_in)
    tolerance = 1.0 * M_PER_IN
    covering = []
    for roof in model.roofs:
        xs = [p[0] for p in roof.footprint]
        ys = [p[1] for p in roof.footprint]
        if (min(xs) - tolerance <= point[0] <= max(xs) + tolerance
                and min(ys) - tolerance <= point[1] <= max(ys) + tolerance):
            covering.append(roof)
    return max(covering, key=lambda r: roof_height_at(r, point)) if covering else None


def _junction_z_in(roof, wall, direction: str, station: float, clad_out_in: float) -> float:
    """The elevation the eave assembly hangs from, in inches — the **roof plane**, not the plate.

    A wall stops at its top plate; the roof deck at the eave sits the rafter's own rise above
    that (on catlin, the I-joist's 10" of depth less its seat drop). Registering the gutter,
    drip and vent slot on ``wall.top_z1_m`` therefore drew the whole assembly most of a foot
    below the eave it belongs to — floating mid-wall, with the authored gutter it is supposed
    to work with a storey of roof stack above it. Only a wall with no roof over it, which has
    no eave to detail anyway, falls back to its plate.
    """
    if roof is not None:
        return roof_height_at(roof, _cut_point(direction, station, clad_out_in)) / M_PER_IN
    return (wall.top_z1_m if wall.top_z1_m is not None else wall.z1_m) / M_PER_IN


def eave_vent_intake(model, roof, clad_out: float, junction_z: float, out_sign: float,
                     crop_bottom_z: float, slope: float = 1.0) -> list[IRNode]:
    """The screened intake at the eave end of an air gap above the deck.

    A roof with no such gap (catlin's unvented flash-and-batt roof) gets no screen.
    """
    cfg = SHEET_METAL
    gaps = [(lo, hi) for (layer, lo, hi) in above_structure_bands(model, roof)
            if layer.function.value == "airgap"]
    if not gaps:
        return []
    lo, hi = gaps[-1]
    # Perpendicular offsets, vertical elevations: ``slope`` is what converts between them
    # (roof_geometry.roof_slope_factor). Without it the screen lands a third of an inch low
    # on catlin's 4:12 — off the mat and onto the underlayment under it.
    band_z = junction_z + lo * slope
    if band_z <= crop_bottom_z:  # slot below the crop — drawing it would float off the sheet
        return []
    inboard = clad_out - out_sign * 2.0
    height = max((hi - lo) * slope, cfg.screen_band_in)
    return rect_region(min(clad_out, inboard), band_z, max(clad_out, inboard),
                       band_z + height, "insect-screen", None, "rigid", lineweight=PROFILE)


#: From this scale up (paper inches per foot) the hook and the face line read as separate
#: pieces and get a leader each.
_ENLARGED_SCALE = 1.5
#: How far under the roof plane at its face a wall's top may stop and still be the eave wall
#: (inches): the rafter's rise over the plate is ~10".
_WALL_UNDER_EAVE_IN = 24.0


def eave_overlay_for_slice(model, view, scale=None) -> list[IRNode]:
    """The flush-eave overlay for an authored DETAIL ``Slice`` whose crop holds an eave.

    Self-gated: the first exterior wall the cut crosses whose top stands under the roof and
    whose eave (cladding face at the roof plane) lies inside the crop — a basement wall below
    the same face line has a "roof over" it too. Any other authored detail gets nothing.
    """
    if view.crop is None or view.cut_origin is None:
        return []
    direction = view.cut_direction or "x"
    station = view.cut_origin.xy_m[1] if direction == "x" else view.cut_origin.xy_m[0]
    crop = (view.crop[0].xy_m, view.crop[1].xy_m)
    (cu0, cz0), (cu1, cz1) = crop
    for wall in model.walls:
        frame = eave_frame(model, wall, direction, station)
        if frame is None or frame[0] is None:
            continue
        _roof, clad_out, junction_z, *_ = frame
        top_in = max(t for t in (wall.top_z0_m, wall.top_z1_m, wall.z1_m)
                     if t is not None) / M_PER_IN
        if (junction_z - _WALL_UNDER_EAVE_IN <= top_in <= junction_z
                and min(cu0, cu1) <= clad_out * M_PER_IN <= max(cu0, cu1)
                and min(cz0, cz1) <= junction_z * M_PER_IN <= max(cz0, cz1)):
            return zero_overhang_eave(model, wall, crop, direction, station, scale)
    return []
