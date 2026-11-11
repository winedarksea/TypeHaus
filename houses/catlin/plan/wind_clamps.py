"""Authored S-5-N Mini corner uplift layout; quantities are not an engineered schedule.

House roof: four eave corners, three seams each (12 Minis).
Garage/canopy roof: northwest, northeast and southwest, three seams each (9 Minis).
The southeast canopy corner carries ColorGard and omits separate Minis per owner
instruction. Snow-retention clamps do not establish an equivalent uplift schedule.

Both roofs are Image II direct-fastened nail-flange panels. House PBR walls and
garage corrugated walls have no standing seams, so neither receives seam clamps.

The site's V_ult = 115 mph, Exposure B is authored, but ASCE 7 corner-zone widths,
pressures and a panel attachment design remain outstanding. These 21 clamps are a
builder's layout and estimate, not a wind-capacity claim. S-5! publishes no general
prescriptive spacing for these panels. FM DS 1-31's corner-zone guidance motivated
the layout; it does not engineer this nail-flange roof. Panel fasteners must carry
the loads delivered to them, including snow-retention drag at the canopy corner.

Dimensions, seam stations and roof-derived placement live in params modules.
See notes/s5_snow_retention_review.md for public product evidence and open checks.
"""

from params.garage_roof_wind_clamps import GARAGE_ROOF_WIND_CLAMPS as GARAGE_ROOF_WIND_CLAMPS

GARAGE_WALL_WIND_CLAMPS = []
