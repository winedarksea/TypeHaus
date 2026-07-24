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
    # Grade stations. Two rings per house side let code.R401_3_grading measure the fall
    # away from the foundation: a near-wall point (~2-3' out) plus a ~9'-out point that has
    # dropped 6" (5%+ per IRC R401.3, "6 inches within the first 10 feet"). Each side reads
    # slightly below datum right at the wall and keeps falling. Distinct y-stations also feed
    # every elevation's 10'-deep grade-capture band. The four southern garden points hold the
    # sunken-garden condition (decision 2): garden floor at -9', raised planter block at +3'-6".
    spot_elevations=(
        # south side (house wall at y=0), draining down toward the sunken garden
        SpotElevation(position=pt(ft(12), ft(-2)), elevation=ft(0, -2)),
        SpotElevation(position=pt(ft(26), ft(-3)), elevation=ft(0, -3)),
        SpotElevation(position=pt(ft(18), ft(-9)), elevation=ft(0, -6)),
        # north side (house wall at y=36')
        SpotElevation(position=pt(ft(12), ft(39)), elevation=ft(0, -2)),
        SpotElevation(position=pt(ft(24), ft(45)), elevation=ft(0, -6)),
        # east side (house wall at x=36')
        SpotElevation(position=pt(ft(39), ft(12)), elevation=ft(0, -2)),
        SpotElevation(position=pt(ft(45), ft(26)), elevation=ft(0, -6)),
        # west side (house wall at x=0)
        SpotElevation(position=pt(ft(-3), ft(14)), elevation=ft(0, -2)),
        SpotElevation(position=pt(ft(-9), ft(28)), elevation=ft(0, -6)),
        # sunken garden floor and the raised-garden block wall at the far south
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
