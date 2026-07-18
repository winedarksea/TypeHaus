# haus: editable
from typehaus import Site, degF, deg, ft

SITE = Site(
    lat=44.9778,
    lon=-93.2650,
    elevation=ft(830),
    crs="EPSG:26915",
    true_north=deg(0),
    design_temp_heating=degF(-15),
    design_temp_cooling=degF(90),
)
