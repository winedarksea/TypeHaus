# haus: editable
# Parcel/setbacks/utilities are placeholders the user can correct. The four structures
# already span ~102' N-S (sunken garden at y=-29.8' to the garage at y=72'), so a
# 100'-wide x 165'-deep parcel is the minimum "plausible" lot that clears the 30'/25'
# front/rear placeholders without immediately failing code.site_setback; a real survey
# will replace all of this. Spot elevations capture the walkout + sunken-garden
# condition (decision 2): grade ~0 at the street/north side and near the house,
# retaining-wall top just above grade, the garden floor at -9', and the ~3'
# raised-garden block wall at the far south.
from typehaus import (
    Site,
    SetbackSpec,
    SpotElevation,
    UtilityKind,
    UtilityLine,
    deg,
    degF,
    ft,
    pt,
)

SITE = Site(
    lat=44.9778,
    lon=-93.2650,
    elevation=ft(830),
    crs="EPSG:26915",
    true_north=deg(0),
    grade=ft(0),
    design_temp_heating=degF(-15),
    design_temp_cooling=degF(90),
    parcel=(pt(ft(-32), ft(-60)), pt(ft(68), ft(-60)), pt(ft(68), ft(105)),
            pt(ft(-32), ft(105))),
    setbacks=(
        SetbackSpec(edge=0, distance=ft(25), label="REAR"),
        SetbackSpec(edge=1, distance=ft(10), label="SIDE"),
        SetbackSpec(edge=2, distance=ft(30), label="FRONT"),
        SetbackSpec(edge=3, distance=ft(10), label="SIDE"),
    ),
    # Spread across both x (facade width) and y (north-south depth) so every elevation's
    # 10'-deep capture band picks up distinct, non-degenerate stations: south/north see
    # only the near-wall transition (subtle), east/west see the full sunken-garden drop.
    spot_elevations=(
        SpotElevation(position=pt(ft(4), ft(5)), elevation=ft(0)),
        SpotElevation(position=pt(ft(32), ft(5)), elevation=ft(0)),
        SpotElevation(position=pt(ft(6), ft(-4)), elevation=ft(0, 6)),
        SpotElevation(position=pt(ft(30), ft(-4)), elevation=ft(0, 6)),
        SpotElevation(position=pt(ft(8), ft(-20)), elevation=ft(-9)),
        SpotElevation(position=pt(ft(28), ft(-20)), elevation=ft(-9)),
        SpotElevation(position=pt(ft(10), ft(-29)), elevation=ft(3, 6)),
        SpotElevation(position=pt(ft(26), ft(-29)), elevation=ft(3, 6)),
    ),
    utilities=(
        UtilityLine(kind=UtilityKind.SEWER, path=(pt(ft(3), ft(-20)), pt(ft(3), ft(0))),
                    entry=pt(ft(3), ft(0)), depth=ft(5)),
        UtilityLine(kind=UtilityKind.WATER, path=(pt(ft(5), ft(-20)), pt(ft(5), ft(0))),
                    entry=pt(ft(5), ft(0)), depth=ft(6)),
        UtilityLine(kind=UtilityKind.POWER, path=(pt(ft(-32), ft(18)), pt(ft(0), ft(18))),
                    entry=pt(ft(0), ft(18)), depth=ft(3)),
    ),
)
