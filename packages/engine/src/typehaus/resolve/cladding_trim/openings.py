"""Dimensioned window-first custom metal trim sections.

Section coordinates are inches. They describe the installed section before the
sheet is swept along an opening side; the dimensions follow the actual reveal.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class WindowTrimSection:
    points_in: tuple[tuple[float, float], ...]
    receiver_depth_in: float
    frame_lap_in: float = 0.0


def window_jamb_section(reveal_in: float, jamb_inset_in: float, *,
                        panel_lap_in: float = 1.0,
                        frame_lap_in: float = 1.0) -> WindowTrimSection:
    """Jamb section in (along-wall, outward-depth) coordinates.

    The panel-side leg bears on the rib plane. The return crosses the panel edge;
    the inboard leg crosses the RO-to-frame gap and laps the frame on its mount plane.
    Mirror the along-wall axis for the opposite jamb.
    """
    values = (reveal_in, jamb_inset_in, panel_lap_in, frame_lap_in)
    if any(not isfinite(v) or v <= 0 for v in values):
        raise ValueError("jamb dimensions must be finite and positive")
    return WindowTrimSection(
        ((-panel_lap_in, reveal_in), (0.0, reveal_in), (0.0, 0.0),
         (jamb_inset_in + frame_lap_in, 0.0)),
        receiver_depth_in=reveal_in, frame_lap_in=frame_lap_in,
    )


def window_sill_section(reveal_in: float, sill_rise_in: float, *,
                        upstand_clearance_in: float = 0.125,
                        drip_in: float = 0.5,
                        hem_in: float = 0.25,
                        slope_in_per_ft: float = 0.25) -> WindowTrimSection:
    """Sill section in (outward-depth, height) at the rough sill.

    The pan turn-down laps the back upstand; the cap drains across the panel
    end and past its rib. Its upstand remains below the unit's sill.
    """
    values = (reveal_in, sill_rise_in, upstand_clearance_in, drip_in, hem_in,
              slope_in_per_ft)
    if any(not isfinite(v) or v <= 0 for v in values):
        raise ValueError("sill dimensions must be finite and positive")
    if sill_rise_in <= upstand_clearance_in:
        raise ValueError("sill rise must clear the upstand")
    fall = reveal_in * slope_in_per_ft / 12.0
    return WindowTrimSection(
        ((0.0, sill_rise_in - upstand_clearance_in), (0.0, 0.0),
         (reveal_in, -fall), (reveal_in, -fall - drip_in),
         (reveal_in - hem_in, -fall - drip_in)),
        receiver_depth_in=reveal_in,
    )


def is_profiled_metal_wall(model, wall) -> bool:
    """Identify the wall skins for which the window-first kit is specified."""
    finishes = {material.tag: material.finish for material in model.plan.library.materials}
    return any(layer.function == "cladding" and finishes.get(layer.material_ref) in {
        "ribbed-panel", "board-and-batten", "corrugated",
    } for layer in wall.layers)


def window_trim_solids(model, wall, opening, frame, material):
    """Sweep the stock head and custom jamb/sill around a seated metal-wall window."""
    from dataclasses import replace

    from typehaus.library.trim.metal_sales import (
        OPENING_HEAD,
        WINDOW_JAMB_CUSTOM,
        WINDOW_SILL_CUSTOM,
    )
    from typehaus.resolve.cladding_trim.members import split_stock_run
    from typehaus.resolve.cladding_trim.section import folded_section_mesh
    from typehaus.resolve.flashing_solids import flashing_solid
    from typehaus.resolve.metal_skin_profiles import INCH_M, SHEET_24_GA_M

    seat = opening.window_seat
    lo = opening.center_along_m - opening.width_m / 2
    hi = lo + opening.width_m
    sill = wall.base_ref_z_m + opening.sill_m
    head = sill + opening.height_m - seat.head_drop_m
    reveal = frame.clad - frame.mount
    jamb = window_jamb_section(reveal / INCH_M, seat.jamb_inset_m / INCH_M)
    sill_section = window_sill_section(reveal / INCH_M, seat.sill_rise_m / INCH_M)
    # The head's one-inch inner upstand is a folded return against the 2.5-inch leg;
    # the visible single-thickness centerline is sufficient for the formed sheet sweep.
    head_section = ((0.0, 2.5), (0.0, 0.0), (1.5, 0.0), (1.853553, -0.353553))
    solids = []
    axis_up = (0.0, 0.0, 1.0)
    outward = (*frame.outward, 0.0)
    along = (*frame.along, 0.0)

    def add(key, profile_key, profile, section, origin, axis_a, axis_b, direction, length):
        for index, (start, end, stock) in enumerate(split_stock_run(
                length, tuple(v * INCH_M for v in profile.stock_lengths_in),
                profile.min_lap_in * INCH_M)):
            point = tuple(origin[i] + direction[i] * start for i in range(3))
            mesh = folded_section_mesh(tuple((a * INCH_M, b * INCH_M) for a, b in section),
                                       point, axis_a, axis_b,
                                       tuple(v * (end - start) for v in direction), SHEET_24_GA_M)
            solid = flashing_solid(uid=f"{opening.uid}-trim-{key}-{index}",
                tag=f"{opening.tag}-TRIM-{key.upper()}-{index + 1}", storey=wall.storey,
                category="cladding_trim", mesh=mesh, material=material, host_ref=opening.tag)
            solids.append(replace(solid, product=profile_key, trim_length_m=end - start,
                                  trim_stock_length_in=stock / INCH_M))

    for key, station, sign in (("jamb-left", lo, 1.0), ("jamb-right", hi, -1.0)):
        add(key, "WINDOW_JAMB_CUSTOM", WINDOW_JAMB_CUSTOM, jamb.points_in,
            frame.point(station, frame.mount, sill),
            tuple(v * sign for v in along), outward, axis_up, head - sill)
    add("sill", "WINDOW_SILL_CUSTOM", WINDOW_SILL_CUSTOM, sill_section.points_in,
        frame.point(lo, frame.mount, sill), outward, axis_up, along, opening.width_m)
    add("head", "OPENING_HEAD", OPENING_HEAD, head_section,
        frame.point(lo - INCH_M, frame.mount, head), outward, axis_up, along,
        opening.width_m + 2 * INCH_M)
    return solids
