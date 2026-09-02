# haus: editable
# Parcel/setbacks/utilities are placeholders the user can correct. The four structures
# already span ~102' N-S (sunken garden at y=-29.8' to the garage at y=72'), so a
# 100'-wide x 165'-deep parcel is the minimum "plausible" lot that clears the 30'/25'
# front/rear placeholders without immediately failing code.site_setback; a real survey
# will replace all of this.
#
# **Grade sits 2'-10" below the main floor.** The model's vertical datum is the main floor,
# so "the house comes 2'-10" out of the ground" is authored the way a drawing set states it:
# FFE stays 0'-0" and grade drops to -2'-10". The house, the sunken garden, the porch and
# the balcony do not move; the garage, its stem, and the breezeway's frost pads follow grade
# down (params/foundations.py::SITE_GRADE is the one derived copy of this number, and
# plan/manifest.py asserts the two agree — this file is editable and may hold only literals,
# which is why the number appears twice at all).
#
# The 4" beyond the earlier 2'-6" is the basement-ceiling overhaul: the mixed I-joist /
# EPS-formed deck over the basement is 12 5/8" deep against the old slab's 9", so the house
# rose 4" and the basement floor stayed in the ground to keep its headroom.
#
# Spot elevations capture the walkout + sunken-garden condition (decision 2): grade near
# -2'-10" at the street/north side and around the house, the sunken-garden floor still at
# -9'-4", and the raised-garden apron now standing 3'-4" proud of the soil.
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
    grade=ft(-2, -10),
    design_temp_heating=degF(-15),
    design_temp_cooling=degF(90),
    monthly_normals=_MSP_1991_2020_NORMALS,
    # Deep-ground boundary temperature for below-grade envelope ΔT: the standard proxy is
    # the station's annual mean air temperature — 46.9 F over the twelve MSP 1991-2020
    # monthly TAVG normals above, rounded to 47. Below-grade walls and slabs see this, not
    # the -15 F design air.
    soil_temp_f=47.0,
    # ** THE PARCEL'S OWN SOIL, STATED HERE RATHER THAN INHERITED. ** The mn-2024 profile
    # carries GM as a Twin Cities presumption, citing the **Hennepin County** soil survey —
    # the same wrong-county citation as the snow load below, in the shared engine where no
    # house could correct it.
    #
    # GM (silty gravel to inorganic silt), IRC Table R405.1's 45 psf/ft equivalent-fluid
    # group, is right for this site for the same reason it is right regionally: the whole
    # Ramsey/Hennepin uplands are Des Moines-lobe glacial till, and the **Ramsey County**
    # soil survey reads the same GM/ML as its neighbour's. The number does not move; what
    # moves is that it is now this parcel's statement about itself rather than a borrowed
    # one, and it will not silently follow a change made for some other house.
    #
    # ** IT IS STILL PRESUMPTIVE, NOT A SOILS REPORT. ** No geotechnical investigation has
    # been done here. The sunken garden's retaining walls are the walls this number decides,
    # and they are the walls a real report would be commissioned for
    # (structural.foundation_unbalanced_fill).
    soil_class="GM",
    # Ground snow load, **MN Rules 1303.1700**. The IRC Table R301.2(1) citation once used
    # here named "Hennepin County / Minneapolis" — the right number from the wrong document
    # and the wrong county; the IRC table is the blank the state fills in, not the source,
    # and this parcel is in RAMSEY County, not Hennepin.
    #
    # The number does not move either way: 1303.1700 sets **50 psf** in every Minnesota county
    # EXCEPT twenty-nine named northern ones, and neither Ramsey nor Hennepin is among them.
    # So the citation is now the one that survives a parcel lookup — if this house is ever
    # sited in a different county, the rule to re-read is named here and the exception list
    # is where the answer is.
    #
    # Flat-roof Pf = 0.7 x 50 = 35 psf at the fully-exposed heated defaults; the roof
    # framing sheet prints that load case from this number.
    ground_snow_load_psf=50.0,
    # Design wind. **MN Rules 1309.0301**, the state's amendment to IRC Table R301.2(1),
    # read 2026-08-30 at revisor.mn.gov: "ULTIMATE DESIGN WIND SPEED (mph) — 115",
    # "TOPOGRAPHIC EFFECTS — YES (in accordance with Section R301.2.1.5)", and "Wind exposure
    # category shall be determined on a site-specific basis in accordance with Section
    # R301.2.1.4." The 115 is statewide, so unlike the snow load it survives a county
    # correction without any lookup at all; it derives from IRC Figure R301.2(5)A, which is
    # ASCE 7-16 Figure 26.5-1B (Risk Category II, 700-yr MRI). It is the same V_ult
    # `notes/catlin_truss_engineering.md` §2 hand-carries, now sourced from the adopted rule
    # rather than restated in a note.
    #
    # V_ult is a strength-level 3-s gust **at 33 ft in Exposure C by definition** — the
    # exposure of the site does not change it, only the velocity-pressure coefficient K_z it
    # is later multiplied by. So the two fields below do not contradict each other and no
    # exposure correction belongs on the speed.
    design_wind_speed_mph=115.0,
    # Exposure **B** — R301.2.1.4's site-specific determination, and the site's actual
    # condition: a suburban Ramsey County parcel with buildings and trees in every upwind
    # sector for well past the 1,500' fetch §26.7.3 asks about. This is the **model-wide
    # design basis**.
    #
    # `notes/catlin_truss_engineering.md` §2 sizes the cladding stand-off on Exposure **C**
    # instead, and that is deliberate and stays: it prints its own Exposure B number
    # (q_h 20.1 psf vs C's 28.2) and states it is carrying the ~40 % higher C figure as
    # margin on a screw-withdrawal check where the margin is nearly free. One assembly
    # choosing to be conservative is not a second site record; when a calculation reads
    # `wind_exposure` it gets B, and a note that wants C says so in its own arithmetic.
    wind_exposure="B",
    # A single-family dwelling: ASCE 7-16 Table 1.5-1 / IBC Table 1604.5 Risk Category II,
    # which is the map V_ult above is read from.
    risk_category="II",
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
    # slightly below the -2'-10" grade plane right at the wall and keeps falling. Distinct
    # y-stations also feed every elevation's 10'-deep grade-capture band.
    #
    # The nine house-perimeter stations moved with grade; their
    # *differences* — which is all R401.3 reads — are untouched. The four southern garden
    # stations below deliberately did **not** move: they record structures that did not move
    # either (the sunken-garden floor, and the top of W-SG-S). Both pairs sit 20'+ from the
    # house footprint, outside code.R401_3_grading's 10' band, so they never mix with the
    # perimeter ring.
    spot_elevations=(
        # south side (house wall at y=0), draining down toward the sunken garden
        SpotElevation(position=pt(ft(12), ft(-2)), elevation=ft(-3)),
        SpotElevation(position=pt(ft(26), ft(-3)), elevation=ft(-3, -1)),
        SpotElevation(position=pt(ft(18), ft(-9)), elevation=ft(-3, -4)),
        # north side (house wall at y=36'). Both stations sit east of the garage's east wall
        # line (x=24') because the garage now stands only 4' north: the old (12,39) / (24,45)
        # pair fell in the breezeway slot and inside the garage footprint respectively, where
        # there is no longer 10' of open ground to fall into.
        SpotElevation(position=pt(ft(30), ft(39)), elevation=ft(-3)),
        SpotElevation(position=pt(ft(32), ft(45)), elevation=ft(-3, -4)),
        # east side (house wall at x=36')
        SpotElevation(position=pt(ft(39), ft(12)), elevation=ft(-3)),
        SpotElevation(position=pt(ft(45), ft(26)), elevation=ft(-3, -4)),
        # west side (house wall at x=0)
        SpotElevation(position=pt(ft(-3), ft(14)), elevation=ft(-3)),
        SpotElevation(position=pt(ft(-9), ft(28)), elevation=ft(-3, -4)),
        # sunken garden floor, and the retaining wall's top at the far south. The last two
        # read +0'-6": they record the top of W-SG-S, which params/raised_garden.py's
        # retaining apron now tops out level with (rather than 3' above it, as a since-removed
        # planter bed once stood). The plane these two stations sit on is the wall top itself.
        # Both are inside the apron's U (x 4'..32', y -33.33'..-9.5') and stay there.
        #
        # None of these four move with grade: they are the tops of structures, not readings
        # of the soil plane, and those structures stay put.
        # The garden floor reads -9'-4": SL-SG-FLOOR is filed on the basement storey and goes
        # down with that datum. Nothing structural reads spot elevations — they are drafting
        # annotation — which is exactly why a stale one can survive unnoticed.
        SpotElevation(position=pt(ft(8), ft(-20)), elevation=ft(-9, -4)),
        SpotElevation(position=pt(ft(28), ft(-20)), elevation=ft(-9, -4)),
        SpotElevation(position=pt(ft(10), ft(-29)), elevation=ft(0, 6)),
        SpotElevation(position=pt(ft(26), ft(-29)), elevation=ft(0, 6)),
    ),
    # Impervious hardscapes abutting the main house (footprint x[0,36'] y[0,36']). R401.3 needs
    # each to fall >= 2% away from the foundation within 10'; code.R401_3_impervious asserts it.
    # near_elevation is the grade where the slab meets the foundation (just below the *grade*
    # plane, which is 2'-10" under the main-floor datum since 2026-08-21); far_elevation is the
    # outer edge, dropped enough to clear 2% over the run. Both ends of both surfaces dropped
    # with grade; the falls they encode are unchanged, and the falls are what R401.3 measures.
    impervious_surfaces=(
        # Apron on the north wall (y=36'), east of the breezeway (which spans x 0.5-8.5').
        # Only 4' deep now that the garage stands at y=40.5': it floors the slot between the
        # two structures, falls away from the house, and drains east to the driveway rather
        # than north into the garage stem.
        ImperviousSurface(
            label="front walk",
            outline=(pt(ft(14), ft(36)), pt(ft(22), ft(36)),
                     pt(ft(22), ft(40)), pt(ft(14), ft(40))),
            near_elevation=ft(-2, -11),  # -1" below grade at the foundation
            far_elevation=ft(-3, -1),    # -3" at the 4' outer edge (4.2% away)
        ),
        # side patio on the east wall (x=36'), draining east toward the side-yard grade
        ImperviousSurface(
            label="patio",
            outline=(pt(ft(36), ft(10)), pt(ft(42), ft(10)),
                     pt(ft(42), ft(22)), pt(ft(36), ft(22))),
            near_elevation=ft(-2, -11),  # -1" below grade at the foundation
            far_elevation=ft(-3, -2),  # -4" below grade at the 6' outer edge (4.2% away)
        ),
    ),
    # ``UtilityLine.depth`` is a bury depth *below finished grade* (emit/ifc/site.py reads
    # it as ``grade_z - depth``), so these three follow grade down on their own and want no
    # re-basing.
    utilities=(
        UtilityLine(kind=UtilityKind.SEWER, path=(pt(ft(3), ft(-20)), pt(ft(3), ft(0))),
                    entry=pt(ft(3), ft(0)), depth=ft(5)),
        # Enters at the FRONT, matching the street on the NORTH (SetbackSpec(edge=2,
        # label="FRONT")) and grade "at the street/north side") — a municipal water main
        # does not run behind the house. Terminates at the hydrant, the first thing it
        # reaches.
        UtilityLine(kind=UtilityKind.WATER, path=(pt(ft(5), ft(72)), pt(ft(5), ft(59, 6))),
                    entry=pt(ft(5), ft(59, 6)), depth=ft(6)),
        UtilityLine(kind=UtilityKind.POWER, path=(pt(ft(-32), ft(18)), pt(ft(0), ft(18))),
                    entry=pt(ft(0), ft(18)), depth=ft(3)),
    ),
)
