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
    ImperviousSurface,
    MonthlyNormal,
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

# Minneapolis-St. Paul Intl AP (NOAA NCEI station USW00014922), U.S. Climate Normals
# 1991-2020. temp_f is the published MLY-TAVG-NORMAL; rh is the monthly mean relative
# humidity computed from the same station's published hourly 1991-2020 normals
# (HLY-TEMP-NORMAL / HLY-DEWP-NORMAL, Magnus conversion, averaged per month) because NCEI
# publishes no monthly RH normal for this station. January..December, feeding the monthly
# (ISO 13788-style) condensation gate.
_MSP_1991_2020_NORMALS = (
    MonthlyNormal(temp_f=16.2, rh=73.7),  # January
    MonthlyNormal(temp_f=20.6, rh=70.2),  # February
    MonthlyNormal(temp_f=33.3, rh=64.5),  # March
    MonthlyNormal(temp_f=47.1, rh=55.6),  # April
    MonthlyNormal(temp_f=59.5, rh=57.2),  # May
    MonthlyNormal(temp_f=69.7, rh=62.4),  # June
    MonthlyNormal(temp_f=74.3, rh=64.4),  # July
    MonthlyNormal(temp_f=71.8, rh=67.5),  # August
    MonthlyNormal(temp_f=63.5, rh=67.0),  # September
    MonthlyNormal(temp_f=49.5, rh=65.1),  # October
    MonthlyNormal(temp_f=34.8, rh=69.4),  # November
    MonthlyNormal(temp_f=22.0, rh=75.0),  # December
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
    monthly_normals=_MSP_1991_2020_NORMALS,
    # Deep-ground boundary temperature for below-grade envelope ΔT: the standard proxy is
    # the station's annual mean air temperature — 46.9 F over the twelve MSP 1991-2020
    # monthly TAVG normals above, rounded to 47. Below-grade walls and slabs see this, not
    # the -15 F design air.
    soil_temp_f=47.0,
    # Hennepin County / Minneapolis ground snow load, IRC Table R301.2(1). Flat-roof
    # Pf = 0.7 x 50 = 35 psf at the fully-exposed heated defaults; the roof framing sheet
    # prints that load case from this number.
    ground_snow_load_psf=50.0,
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
    # sunken-garden condition (decision 2): garden floor at -9', retaining-wall top at +0'-6".
    spot_elevations=(
        # south side (house wall at y=0), draining down toward the sunken garden
        SpotElevation(position=pt(ft(12), ft(-2)), elevation=ft(0, -2)),
        SpotElevation(position=pt(ft(26), ft(-3)), elevation=ft(0, -3)),
        SpotElevation(position=pt(ft(18), ft(-9)), elevation=ft(0, -6)),
        # north side (house wall at y=36'). Both stations sit east of the garage's east wall
        # line (x=24') because the garage now stands only 4' north: the old (12,39) / (24,45)
        # pair fell in the breezeway slot and inside the garage footprint respectively, where
        # there is no longer 10' of open ground to fall into.
        SpotElevation(position=pt(ft(30), ft(39)), elevation=ft(0, -2)),
        SpotElevation(position=pt(ft(32), ft(45)), elevation=ft(0, -6)),
        # east side (house wall at x=36')
        SpotElevation(position=pt(ft(39), ft(12)), elevation=ft(0, -2)),
        SpotElevation(position=pt(ft(45), ft(26)), elevation=ft(0, -6)),
        # west side (house wall at x=0)
        SpotElevation(position=pt(ft(-3), ft(14)), elevation=ft(0, -2)),
        SpotElevation(position=pt(ft(-9), ft(28)), elevation=ft(0, -6)),
        # sunken garden floor, and the retaining wall's top at the far south. The last two
        # read +0'-6" rather than the +3'-6" they carried until 2026-07-25: they record the
        # top of W-SG-S, which used to be the base of a 36" planter bed standing on it. The
        # bed is gone — params/raised_garden.py now builds a retaining apron that tops out
        # level with that wall instead of 3' above it — so the plane these two stations sit
        # on is the wall top itself. Both are inside the apron's U (x 4'..32', y -33.33'..
        # -9.5') and stay there.
        SpotElevation(position=pt(ft(8), ft(-20)), elevation=ft(-9)),
        SpotElevation(position=pt(ft(28), ft(-20)), elevation=ft(-9)),
        SpotElevation(position=pt(ft(10), ft(-29)), elevation=ft(0, 6)),
        SpotElevation(position=pt(ft(26), ft(-29)), elevation=ft(0, 6)),
    ),
    # Impervious hardscapes abutting the main house (footprint x[0,36'] y[0,36']). R401.3 needs
    # each to fall >= 2% away from the foundation within 10'; code.R401_3_impervious asserts it.
    # near_elevation is the grade where the slab meets the foundation (just below the main-floor
    # datum); far_elevation is the outer edge, dropped enough to clear 2% over the run.
    impervious_surfaces=(
        # Apron on the north wall (y=36'), east of the breezeway (which spans x 0.5-8.5').
        # Only 4' deep now that the garage stands at y=40.5': it floors the slot between the
        # two structures, falls away from the house, and drains east to the driveway rather
        # than north into the garage stem.
        ImperviousSurface(
            label="front walk",
            outline=(pt(ft(14), ft(36)), pt(ft(22), ft(36)),
                     pt(ft(22), ft(40)), pt(ft(14), ft(40))),
            near_elevation=ft(0, -1),   # -1" at the foundation
            far_elevation=ft(0, -3),    # -3" at the 4' outer edge (4.2% away)
        ),
        # side patio on the east wall (x=36'), draining east toward the side-yard grade
        ImperviousSurface(
            label="patio",
            outline=(pt(ft(36), ft(10)), pt(ft(42), ft(10)),
                     pt(ft(42), ft(22)), pt(ft(36), ft(22))),
            near_elevation=ft(0, -1),   # -1" at the foundation
            far_elevation=ft(0, -4),    # -4" at the 6' outer edge (4.2% away)
        ),
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
