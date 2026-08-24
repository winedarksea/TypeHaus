"""Where one wall stacks on another: the rim band, and the ledge left by a width change.

Two junction kinds, two recipe ids:

* ``rim-band-air-seal`` (``storey_stack:rim:*``) — the floor band interrupts the sheathing,
  so the air-control layer has to be carried across it. Reference: the basement→framed
  notes' "prioritize air sealing at sill plate (sealant + spray foam)" applied at every
  floor line, not just the first.
* ``stack-width-shelf`` (``stack_width_change:*``) — a wall stepping in over a wider wall
  leaves a horizontal ledge in the weather. Reference: the basement detail's flashed step
  from the 12" foundation with 4" of CI up to the framed wall on the sheathing plane.
  Its inboard sibling, :func:`interior_curb_cap`, shares the same overlay: a masonry stem
  wider than the framed wall it carries leaves a ledge on the *interior* instead — the
  garage ICF stem under its 2x6 wall is the reference case — and that ledge gets capped
  rather than flashed against weather.

Both derive entirely from the resolved faces of the two walls and the floor structure
between them, and both draw nothing when their subject is not genuinely in frame.
"""

from __future__ import annotations

from typehaus.emit.draw.detail_components.config import (
    INTERIOR_CURB_CAP,
    RIM_BAND,
    STACK_WIDTH_SHELF,
)
from typehaus.emit.draw.detail_components.geometry import (
    face_of,
    flashing_nodes,
    floor_band_at,
    is_weather_exposed,
    layer_intervals,
    outboard_is_high,
    outermost_with_function,
    path_from_steps,
    rect_region,
    wall_cut_bounds_m,
)
from typehaus.emit.draw.scene import IRNode
from typehaus.quantities import M_PER_IN


def _lower_and_upper(walls):
    """The stacked pair as ``(lower, upper)``, or ``(None, None)`` if this is not a stack."""
    if len(walls) < 2:
        return None, None
    ordered = sorted(walls, key=lambda w: w.z0_m)
    lower, upper = ordered[0], ordered[-1]
    if upper.z0_m <= lower.z0_m:
        return None, None
    return lower, upper


def rim_band_air_seal(model, walls, crop, direction, station) -> list[IRNode]:
    """Air-barrier strip, plate-line sealant beads and rim cavity foam at a floor band.

    The rim is where a wood-framed air barrier most often fails: the sheathing stops at the
    top plate and restarts at the sole plate above, with the floor structure in between.
    Drawn as the three things that actually close it — a membrane strip lapping the sheathing
    across the band outboard, a bead of sealant at each plate line inboard, and spray foam in
    the rim cavity.
    """
    lower, upper = _lower_and_upper(walls)
    if lower is None or crop is None:
        return []
    # The rim air seal is about the *enclosure* boundary. An interior partition crossing a
    # floor line has conditioned space on both sides and nothing to seal against, so foaming
    # its band would be a drawing that invents work.
    if not is_weather_exposed(upper):
        return []
    is_outboard_high = outboard_is_high(upper, direction, station)
    if is_outboard_high is None:
        return []
    band = floor_band_at(model, upper.z0_m)
    if band is None:
        return []
    band_z0, band_z1 = band[0] / M_PER_IN, band[1] / M_PER_IN
    if band_z1 - band_z0 < RIM_BAND.min_band_depth_in:
        return []
    (_cu0, cz0), (_cu1, cz1) = crop
    if band_z1 < min(cz0, cz1) / M_PER_IN or band_z0 > max(cz0, cz1) / M_PER_IN:
        return []  # band out of frame; a floating rim strip is worse than none

    cfg = RIM_BAND
    out_sign = 1.0 if is_outboard_high else -1.0
    intervals = layer_intervals(upper, direction, station)
    sheath = outermost_with_function(intervals, "sheathing")
    stud = outermost_with_function(intervals, "structure")
    nodes: list[IRNode] = []

    if sheath is not None:
        # Membrane strip on the sheathing face, lapping above and below the band so the air
        # barrier is continuous across the interruption rather than merely adjacent to it.
        sheath_out = face_of(sheath, is_outboard_high, outer=True)
        nodes += rect_region(sheath_out, band_z0 - cfg.air_barrier_lap_in,
                             sheath_out + out_sign * cfg.air_barrier_thickness_in,
                             band_z1 + cfg.air_barrier_lap_in,
                             "rim-air-barrier", "air-barrier", "membrane", lineweight=0.3)

    if stud is not None:
        stud_in = face_of(stud, is_outboard_high, outer=False)
        stud_out = face_of(stud, is_outboard_high, outer=True)
        in_sign = -out_sign
        # Spray foam filling the rim cavity, applied to the inboard face of the rim board.
        nodes += rect_region(stud_out, band_z0, stud_out + in_sign * cfg.cavity_foam_in,
                             band_z1, "rim-cavity-foam", "spray-foam", "foam",
                             lineweight=0.3)
        # A bead at each plate line — the top plate of the wall below and the sole plate of
        # the wall above are two separate joints and both leak if only one is sealed.
        for bead_z in (band_z0, band_z1):
            nodes += rect_region(stud_in, bead_z, stud_out,
                                 bead_z + cfg.sealant_bead_in,
                                 "rim-sealant-bead", "sealant", "foam", lineweight=0.3)
    return nodes


def stack_width_shelf(model, walls, crop, direction, station) -> list[IRNode]:
    """Sloped shelf flashing over the ledge a stepped-in wall leaves exposed.

    Derived by comparing the two walls' outboard faces at the cut: if the wall below projects
    past the wall above by more than a construction tolerance, that projection is a weather
    ledge and gets a flashing with an up-turned back leg (behind the upper wall's water
    layer), a fall outward, and a drip at the outboard edge. A wall stepping in on the
    *interior* leaves no weather ledge and correctly draws nothing.
    """
    lower, upper = _lower_and_upper(walls)
    if lower is None or crop is None:
        return []
    # An interior partition's step-in leaves no weather ledge: there is nothing to flash, and
    # drawing a shelf there would describe drainage the building does not have.
    if not is_weather_exposed(upper):
        return []
    is_outboard_high = outboard_is_high(upper, direction, station)
    if is_outboard_high is None:
        return []
    lower_lo, lower_hi = wall_cut_bounds_m(lower, direction, station)
    upper_lo, upper_hi = wall_cut_bounds_m(upper, direction, station)
    if lower_lo is None or upper_lo is None:
        return []
    if is_outboard_high:
        lower_face, upper_face = lower_hi, upper_hi
        ledge_in = (lower_face - upper_face) / M_PER_IN
    else:
        lower_face, upper_face = lower_lo, upper_lo
        ledge_in = (upper_face - lower_face) / M_PER_IN
    cfg = STACK_WIDTH_SHELF
    if ledge_in < cfg.min_ledge_in:
        return []

    out_sign = 1.0 if is_outboard_high else -1.0
    shelf_z = upper.z0_m / M_PER_IN
    back_u = upper_face / M_PER_IN
    # Back leg up behind the upper wall, fall outward across the ledge, drip off the edge.
    path = path_from_steps((back_u, shelf_z + cfg.back_leg_rise_in), [
        (0.0, -cfg.back_leg_rise_in),
        (out_sign * ledge_in, -cfg.slope_fall_in),
        (out_sign * cfg.drip_projection_in, 0.0),
        (0.0, -cfg.drip_drop_in),
    ])
    return flashing_nodes(path, tag="stack-shelf-flashing")


def interior_curb_cap(model, walls, crop, direction, station) -> list[IRNode]:
    """Sloped cap flashing over the interior curb a masonry stem leaves under a framed wall.

    The inboard sibling of :func:`stack_width_shelf`: compares the two walls' *inboard*
    faces instead of their outboard ones. A masonry wall (a foundation or ICF stem) wider
    than the framed wall it carries steps in on the interior, leaving a ledge behind the
    framed wall's drywall — nothing there sheds weather, but water running down that
    drywall's face (splash, a hosed-down wall, condensation on the cold masonry below)
    still needs somewhere to go besides the ledge and the board joint underneath it.

    Scoped to masonry-to-framed junctions: the lower wall must be a foundation wall, so
    two framed walls of different widths stacking (an interior partition change, say) has
    no masonry curb and correctly draws nothing.
    """
    lower, upper = _lower_and_upper(walls)
    if lower is None or crop is None:
        return []
    if not lower.is_foundation:
        return []
    is_outboard_high = outboard_is_high(upper, direction, station)
    if is_outboard_high is None:
        return []
    lower_lo, lower_hi = wall_cut_bounds_m(lower, direction, station)
    upper_lo, upper_hi = wall_cut_bounds_m(upper, direction, station)
    if lower_lo is None or upper_lo is None:
        return []
    if is_outboard_high:
        # Outboard is the high side, so inboard — the room side — is the low side.
        lower_face, upper_face = lower_lo, upper_lo
        ledge_in = (upper_face - lower_face) / M_PER_IN
    else:
        lower_face, upper_face = lower_hi, upper_hi
        ledge_in = (lower_face - upper_face) / M_PER_IN
    cfg = INTERIOR_CURB_CAP
    if ledge_in < cfg.min_ledge_in:
        return []

    in_sign = -1.0 if is_outboard_high else 1.0
    curb_z = upper.z0_m / M_PER_IN
    back_u = upper_face / M_PER_IN
    # Back leg up behind the upper wall's interior drywall, fall back into the room across
    # the curb, drip off the inboard edge.
    path = path_from_steps((back_u, curb_z + cfg.back_leg_rise_in), [
        (0.0, -cfg.back_leg_rise_in),
        (in_sign * ledge_in, -cfg.slope_fall_in),
        (in_sign * cfg.drip_projection_in, 0.0),
        (0.0, -cfg.drip_drop_in),
    ])
    return flashing_nodes(path, tag="interior-curb-cap-flashing")
