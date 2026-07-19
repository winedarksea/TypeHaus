# haus: editable
# Simple flat site: no spot elevations authored, so the elevation grade line falls back
# to flat Site.grade (decision 2 in the Permit-ready plan set plan).
from typehaus import Site, SetbackSpec, UtilityKind, UtilityLine, degF, deg, ft, pt

SITE = Site(
    lat=44.9778,
    lon=-93.2650,
    elevation=ft(830),
    crs="EPSG:26915",
    true_north=deg(0),
    design_temp_heating=degF(-15),
    design_temp_cooling=degF(90),
    parcel=(pt(ft(-28), ft(-30)), pt(ft(52), ft(-30)), pt(ft(52), ft(70)),
            pt(ft(-28), ft(70))),
    setbacks=(
        SetbackSpec(edge=0, distance=ft(25), label="FRONT"),
        SetbackSpec(edge=1, distance=ft(10), label="SIDE"),
        SetbackSpec(edge=2, distance=ft(20), label="REAR"),
    ),
    utilities=(
        UtilityLine(kind=UtilityKind.SEWER, path=(pt(ft(10), ft(-30)), pt(ft(10), ft(0))),
                    entry=pt(ft(10), ft(0)), depth=ft(5)),
        UtilityLine(kind=UtilityKind.WATER, path=(pt(ft(14), ft(-30)), pt(ft(14), ft(0))),
                    entry=pt(ft(14), ft(0)), depth=ft(6)),
    ),
)
