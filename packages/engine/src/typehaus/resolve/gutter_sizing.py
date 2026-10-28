"""Metal Sales rectangular gutter and leader sizing (PGI-16 to PGI-18).

Pure arithmetic in US units. ``W`` is the bottom width the chart returns; ``M`` is the
waterway depth over that width. Oracled by ``houses/catlin/notes/box_gutter_sizing.md``.
"""

from __future__ import annotations

#: PGI-16 chart constant, W in feet.
_PGI16_CONSTANT = 0.0106
#: PGI-18: DS = 1200 * A / (R * I), A in sq in, R in ft, I in in/hr.
_PGI18_CONSTANT = 1200.0


def pgi_required_width_in(
    intensity_in_hr: float,
    area_sf: float,
    length_ft: float,
    depth_over_width: float,
) -> float:
    """Bottom width (in) a level gutter needs: W = 0.0106 M^(-4/7) L^(3/28) (IA)^(5/14)."""
    if min(intensity_in_hr, area_sf, length_ft, depth_over_width) <= 0.0:
        raise ValueError("intensity, area, length and depth ratio must be positive")
    width_ft = (
        _PGI16_CONSTANT
        * depth_over_width ** (-4.0 / 7.0)
        * length_ft ** (3.0 / 28.0)
        * (intensity_in_hr * area_sf) ** (5.0 / 14.0)
    )
    return 12.0 * width_ft


def leader_served_area_sf(leader_area_sq_in: float, intensity_in_hr: float) -> float:
    """Roof area one leader drains at the given intensity: 1200 A / I (PGI-18 with DS = L)."""
    if leader_area_sq_in <= 0.0 or intensity_in_hr <= 0.0:
        raise ValueError("leader area and intensity must be positive")
    return _PGI18_CONSTANT * leader_area_sq_in / intensity_in_hr
