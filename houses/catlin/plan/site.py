# haus: editable
# ** THE LOT IS REAL NOW: 50'-0" x 133'-0", 6,650 SF. ** The owner has stated the parcel's
# dimensions, so the 100' x 165' rectangle that used to sit here — drawn to be the smallest
# "plausible" lot the structures cleared — is gone. What has NOT arrived is a licensed land
# surveyor's certificate: nobody has located a corner in the field. That middle state is
# ``parcel_basis="plat"``, and ``code.site_parcel_is_surveyed`` grades it UNKNOWN rather
# than PASS (nothing is certified) or FAIL (the dimensions are no longer drawn).
#
# ** WHAT THE "plat" BASIS STILL COVERS, FIELD BY FIELD. ** A reviewer needs to know which
# numbers on C-101 rest on a stated record rather than a measurement:
#
#   * ``parcel`` — a 50' x 133' rectangle at the stated dimensions. No corner located, and
#     the lot's position relative to the house is a siting decision made here, not a shot.
#   * ``setbacks`` — the H1 district minima, not a plat's platted building lines.
#   * ``address``, ``pin``, ``legal_description`` — all absent except a stand-in address;
#     nothing is invented.
#   * ``streets`` — name "TBD", a 60' ROW assumed as the St Paul residential norm.
#   * ``erosion_controls`` — real design decisions (where the fence and the entrance go),
#     drawn against an uncertified ring, so the LINES move when the survey lands even
#     though the intent does not.
#   * ``easements=()`` — an empty tuple is a claim, and it is the one claim here that a
#     title search rather than a survey settles. See its own note below.
#   * every ``SpotElevation`` and both ``*_elevation`` fields on the hardscapes: these are
#     DESIGN elevations relative to the main-floor datum, not shots off a benchmark. There
#     is no ``benchmark`` for the same reason — a benchmark is a physical object a field
#     crew recovers, and authoring one would be the only outright fiction in the file.
#
# ** ZONING: H1, AND RL IS NOT AVAILABLE. ** Saint Paul Ordinance 23-43 (adopted
# 2023-11-26) repealed R1-R4 / RT1 / RT2; the one-family districts are now RL / H1 / H2.
# This file graded against RL on the reasoning that RL is the most restrictive of the
# three, so a house clearing RL clears all of them. That reasoning no longer applies, and
# not as a preference: **RL requires a 60'-0" minimum lot width and 9,000 sf of area, and
# this lot is 50'-0" wide and 6,650 sf.** An RL lot line cannot be drawn around this
# parcel, so RL is not a conservative choice here — it is an impossible one.
#
# H1 and H2 carry the same setbacks (front 10', side 5', rear 10'); the owner chose H1,
# which is the more restrictive of the pair on the two figures that differ (45% max lot
# coverage and 35' height, against H2's 50% and 39').
#
# ** SITING. ** The wall axes span x 0.00'..36.00' and y -31.33'..67.22'. H1's envelope on
# this ring (x -7'..43', y -48.5'..84.5') is x -2'..38' by y -38.5'..74.5', so the house
# clears by 2'-0" on each side line and by about 7'-2" rear / 7'-3" front. The 2'-0" side
# margins are the binding dimension on this lot and nothing may grow outboard into them.
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
    ErosionControl,
    ImperviousSurface,
    MonthlyNormal,
    Site,
    SetbackSpec,
    SpotElevation,
    StreetFrontage,
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
    # ** THE PARCEL'S OWN SOIL, STATED HERE RATHER THAN INHERITED. ** The mn-2020 profile
    # carries GM as a regional Twin Cities presumption for any house with no soils report.
    # (It cited the **Hennepin County** survey by name until 2026-09-10 — the same
    # wrong-county citation as the snow load below, in the shared engine where no house
    # could correct it; it now names the metro glacial till regionally instead.)
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
    # Title-block and site-plan identity. No lot has been purchased, so the address is a
    # stand-in and `pin` / `legal_description` stay unauthored rather than invented — an
    # empty row on the cover is a gap a reviewer can see, a made-up parcel number is not.
    address="LOT TBD - Saint Paul, Ramsey County, MN",
    zoning_district="H1",
    # The one field that makes every dimension on C-101 honest. "plat" says the owner has
    # STATED the lot's dimensions (50' x 133') off a record, and that nobody has certified
    # them: `code.site_parcel_is_surveyed` reports UNKNOWN, not PASS. It becomes "survey"
    # when a licensed land surveyor's certificate arrives and `survey_by` / `survey_date`
    # name the document. It is a non-blocking permit item, so the set still prints.
    #
    # It read "placeholder" — a hard FAIL, WARN severity — until the dimensions arrived.
    # That verdict is still reachable and still red for any house with a drawn ring; see
    # checks/code/site.py::_placeholder.
    parcel_basis="plat",
    # 50'-0" x 133'-0" = 6,650 sf, counter-clockwise from the SW corner. The winding is
    # what the edge labels below depend on: 0 south, 1 east, 2 north, 3 west.
    parcel=(pt(ft(-7), ft(-48.5)), pt(ft(43), ft(-48.5)), pt(ft(43), ft(84.5)),
            pt(ft(-7), ft(84.5))),
    # H1 minima (Ord. 23-43): front 10', side 5', rear 10' — H2's are identical. Edge
    # indices run parcel[e] -> parcel[e+1]: 0 is the south/rear line, 2 the north/front
    # line at the street. These were RL's 30'/10'/10' until the lot width ruled RL out.
    setbacks=(
        SetbackSpec(edge=0, distance=ft(10), label="REAR"),
        SetbackSpec(edge=1, distance=ft(5), label="SIDE"),
        SetbackSpec(edge=2, distance=ft(10), label="FRONT"),
        SetbackSpec(edge=3, distance=ft(5), label="SIDE"),
    ),
    # ** AN EMPTY TUPLE IS AN ASSERTION, AND THIS ONE IS NOT YET EARNED. ** No easement is
    # known on this parcel because no title search has been run on a parcel that has not
    # been chosen. A recorded utility, drainage or access easement is the one thing on a
    # site plan a footprint may not cross, so this stays () with the reason attached rather
    # than being read as "the lot is clear". A title commitment, not the survey, settles it.
    easements=(),
    # The public street this lot fronts, and the right-of-way the 10' front setback is
    # measured from the near line of. 60' is Saint Paul's ordinary residential ROW; the name
    # is TBD with the lot. Edge 2 is the north line, which is where the front setback,
    # the water service and the driveway already agree the street is.
    streets=(StreetFrontage(name="TBD", edge=2, right_of_way_ft=60.0),),
    # Erosion and sediment control, as the site plan shows it (MPCA CSW / St Paul DSI). These
    # are design decisions, not survey products: they move when the parcel does.
    erosion_controls=(
        # Silt fence around the DOWNHILL half of the lot. The soil plane is flat at -2'-10"
        # and every grade station falls away from the house, but the excavation that matters
        # is the sunken garden's — 9'-1" deep, 17'-2" off the rear line — so the sediment
        # this site can lose leaves to the south. The fence runs 2' inside the west, rear and
        # east lines, from y=20' (level with the house's midpoint, above which the ground
        # drains back to the street) around the bottom of the lot and up the east side to
        # match. The lines moved with the 50' x 133' parcel; the 2' offset did not.
        ErosionControl(
            kind="silt_fence",
            path=(pt(ft(-5), ft(20)), pt(ft(-5), ft(-46.5)),
                  pt(ft(41), ft(-46.5)), pt(ft(41), ft(20))),
            description="silt fence, trenched 6 in, 2 ft inside the W/S/E lot lines",
        ),
        # Rock construction entrance where vehicles leave the site, which is the only place
        # they can: the driveway's crossing of the north right-of-way. On the 133'-deep lot
        # the whole drive is only 17'-3 3/8" long, so the mat is the whole of it — from the
        # front lot line at y=84'-6" back to the garage face — at its full 12' width.
        ErosionControl(
            kind="construction_entrance",
            path=(pt(ft(18), ft(84.5)), pt(ft(18), ft(67, 2.625))),
            description="rock construction entrance, 17 ft x 12 ft, 1-2 in clear rock",
        ),
    ),
    # Grade stations. Two rings per house side let code.R401_3_grading measure the fall
    # away from the foundation: a near-wall point (~2-3' out) plus a ~9'-out point that has
    # dropped 6" (5%+ per IRC R401.3, "6 inches within the first 10 feet"). Each side reads
    # slightly below the -2'-10" grade plane right at the wall and keeps falling.
    #
    # ** THE "10'-DEEP GRADE-CAPTURE BAND" CLAIM THAT USED TO SIT HERE WAS A BUG, NOT AN
    # INVARIANT. ** An elevation drew its ground line through every spot within 10' of the
    # facade plane *on either side*, so each facade's own far ring — 9' out and 6" down,
    # perpendicular to the wall, describing the fall away from it and not a station along
    # it — printed as a 4" V in the middle of the drawing, and the sunken-court floor 9'
    # behind the E/W planes ramped those two 3-4' into the ground. The soil plane here is
    # flat. `emit_grade_profile` now captures 4' outboard / 12" inboard (and only
    # `kind="grade"` spots), which is the near ring and nothing else. Do not re-author
    # these stations to suit a drawing: R401.3 is what they are for.
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
        # ** MOVED EAST 4'-0" ON 2026-09-04. ** (30, 39) is 1/4" east of SL-M-HP1PAD's edge
        # and would read -3'-0" of soil hard against a slab topped at -2'-8". (34, 39) is
        # clear of the pad in open ground. Do not push it further out: `code.R401_3_grading`
        # passes here by only 0.6 points.
        SpotElevation(position=pt(ft(34), ft(39)), elevation=ft(-3)),
        SpotElevation(position=pt(ft(32), ft(45)), elevation=ft(-3, -4)),
        # east side (house wall at x=36')
        SpotElevation(position=pt(ft(39), ft(12)), elevation=ft(-3)),
        SpotElevation(position=pt(ft(45), ft(26)), elevation=ft(-3, -4)),
        # west side (house wall at x=0)
        SpotElevation(position=pt(ft(-3), ft(14)), elevation=ft(-3)),
        SpotElevation(position=pt(ft(-9), ft(28)), elevation=ft(-3, -4)),
        # ** THE GARAGE RING, NEW 2026-09-10 — THE GARAGE HAD NEVER BEEN GRADED BY
        # ANYTHING. ** `code.R401_3_grading` built its footprint by polygonizing every
        # foundation wall and keeping only the LARGEST ring; the house is 1,296 sf and the
        # garage 576, so the garage was discarded every time and not one station had ever
        # been authored around it. The check now iterates every enclosure
        # (`checks/code/mn_residential/_common.py::_foundation_enclosures`), so these four
        # are what it reads. The garage's foundation ring is x 6'..30', y 43'-2 5/8"..
        # 67'-2 5/8" (the stem wall AXES, which is what the check polygonizes).
        #
        # ** ONE NEAR STATION PER SIDE, 4'-6" OUT, AND THE 4'-6" IS FORCED. ** The house's
        # own rings sit at 2-3' and 9'. Neither reach is available here, because a station
        # is captured by an elevation's ground line when it lies within 4' outboard (or 12"
        # inboard) of that facade's plane — `emit_grade_profile`'s band — and the garage's
        # planes are only 6' from the house's on the west and east. 4'-6" out of the garage
        # is 1'-6" east of the house's west plane and 1'-6" west of its east plane: clear of
        # both bands, and clear of the house's own 10' grading band as well (each of these
        # is 19'+ from the house footprint). A 9'-out ring would land at x=-3' and x=39',
        # squarely inside the house's west and east capture bands, and would drag those two
        # elevations' ground lines 19' past the end of the house.
        #
        # Each reads -3'-1": 3" of fall over 4'-6" is 5.56%, the same bench slope the house
        # rings encode, against R401.3's 5%. The yard plane they fall to is -3'-4".
        SpotElevation(position=pt(ft(1, 6), ft(55)), elevation=ft(-3, -1)),
        SpotElevation(position=pt(ft(34, 6), ft(55)), elevation=ft(-3, -1)),
        # North of the garage the driveway is the graded surface (`code.R401_3_impervious`
        # reads it at 2.21% now that it has an enclosure within 10' to be measured against),
        # so these two sit WEST of it — the drive is x 12'..24' — in open front yard, and
        # they are the one side with room for both rings: 4'-6" and 9'-0" off y=67'-2 5/8".
        SpotElevation(position=pt(ft(9), ft(71, 8.625)), elevation=ft(-3, -1)),
        SpotElevation(position=pt(ft(9), ft(76, 2.625)), elevation=ft(-3, -4)),
        # ** THE SOUTH YARD RING, NEW 2026-09-10. ** These three are not R401.3 stations —
        # they are 20'+ from the house and the sunken court's own enclosure is excluded from
        # grading (an open excavation is ground the site drains INTO by design, which is the
        # whole point of a sunken garden). They are here for `resolve/site_earth.
        # local_grade_elevation_m`, which now reads grade stations as well as excavation
        # floors, and they are what makes the retaining run's exposure above grade a derived
        # number rather than an assumption: the yard south of the court is a flat plane at
        # -3'-4", so a wall topping out on the porch datum stands 3'-4" out of it.
        #
        # They also set the raised-garden apron's base. `params/raised_garden.py` derives
        # that base as `RETAINING_WALL_TOP_FT - drop_ft`; with the yard authored at -3'-4"
        # the drop has to reach past it, which is why the drop grew to 4'-0".
        #
        # Sited clear of every facade capture band: x=-6' is 2' west of the house's west
        # band, x=41' is 1' east of its east band, and y=-38' is 38' south of the south one.
        # The two side stations are at y=-22' and y=-18', not both at -20': the site plan's
        # drainage arrows pair a station with the nearest LOWER one within its radius, and
        # the court-floor pair sits at y=-20'. A yard station collinear with one of those
        # draws a due-east arrow whose two ends share a y, which is a real drawing artefact
        # and not only a test one — `test_drainage_arrows_point_downhill` indexes spots by
        # y and cannot tell such an arrow's ends apart.
        SpotElevation(position=pt(ft(-6), ft(-22)), elevation=ft(-3, -4)),
        SpotElevation(position=pt(ft(41), ft(-18)), elevation=ft(-3, -4)),
        SpotElevation(position=pt(ft(18), ft(-38)), elevation=ft(-3, -4)),
        # sunken garden floor, and the retaining wall's top at the far south. The last two
        # read 0'-0": they record the top of W-SG-S, which params/raised_garden.py's
        # retaining apron tops out level with. The plane these two stations sit on is the
        # wall top itself.
        #
        # ** THEY HAVE NOW BEEN STALE THREE TIMES, AND THE THIRD IS WHY THEY READ A DATUM
        # RATHER THAN A FIGURE. ** +0'-6" while the retaining run stood 40" over grade,
        # left at +0'-6" when it was capped at +0'-2" on 2026-09-05, and corrected to
        # +0'-2" only on 2026-09-10 — the same day the run came flush with the porch datum
        # and took them to 0'-0". This is data, not prose: `engineering/balcony_wind`
        # reads the site's spot elevations and nothing reconciles these two against
        # `params/sunken_garden.SPEC.retaining_top_ft`. Move them with the wall.
        # ** AND A FOURTH TIME, IN y RATHER THAN IN z (2026-09-10). ** The court shortened
        # 28'-0" -> 26'-0", which walked `W-SG-S`'s axis from -29.3333 to -27.3333 and left
        # both stations 1'-8" south of the wall they record, out in the apron. Moved with
        # it. Both are inside the apron's U (x 4'..32', y -31.33'..-9.5') and stay there.
        #
        # None of these four move with GRADE: they are the tops of structures, not readings
        # of the soil plane. But they must move when those structures do, and the first two
        # just did. That is what `kind="structure"` says, and it is load-bearing in two
        # directions: it keeps all four out of every ground line (the court floor sat 9'
        # behind the east and west facade planes and dragged those profiles down 3-4'), and
        # it does **not** take them out of anything that wants a real elevation —
        # `engineering/balcony_wind.ground_below_ft` still takes the site's lowest spot,
        # court floor included, because the court *is* the surface under the balcony, and
        # `code.R401_3_grading` still reads every station (these four are 20'+ from the
        # footprint, outside its 10' band, so they never join the perimeter ring anyway).
        # The stations therefore do not move; only their label does.
        #
        # ** THE GARDEN FLOOR READS -9'-1 7/16" SINCE 2026-09-05 — THE FLUSH COURT. **
        # `params/sunken_garden.SPEC.court_step_down_in` went back to 0, so the court surface
        # (rim and field alike) is the basement floor plane again and these two stations
        # follow it up 7 1/4". History, because this station has been stale twice already:
        # it read -9'-4" until 2026-09-03 (already 1 7/16" wrong), then -9'-8 11/16" while
        # the flood step existed.
        #
        # ** AND THE CLAIM THAT USED TO SIT HERE — "nothing structural reads spot
        # elevations, they are drafting annotation" — WAS FALSE. **
        # `engineering/balcony_wind.ground_below_ft` takes the LOWEST spot elevation on the
        # site and it is these two that win it, so this pair sets `z` for the balcony
        # columns' wind demand (notes/balcony_moment_columns.md). Raising them shortens `z`
        # by 7 1/4", which lowers K_z and lowers the demand — the safe direction, and the
        # reason the columns need no re-sizing. Do not restore that comment: a station here
        # is a structural input, and the stale-annotation trap it warned about is exactly
        # the one it was itself an instance of.
        SpotElevation(position=pt(ft(8), ft(-20)), elevation=ft(-9, -1.4375),
                      kind="structure"),
        SpotElevation(position=pt(ft(28), ft(-20)), elevation=ft(-9, -1.4375),
                      kind="structure"),
        SpotElevation(position=pt(ft(10), ft(-27, -4)), elevation=ft(0), kind="structure"),
        SpotElevation(position=pt(ft(26), ft(-27, -4)), elevation=ft(0), kind="structure"),
    ),
    # Impervious hardscapes abutting the main house (footprint x[0,36'] y[0,36']). R401.3 needs
    # each to fall >= 2% away from the foundation within 10'; code.R401_3_impervious asserts it.
    # near_elevation is the grade where the slab meets the foundation (just below the *grade*
    # plane, which is 2'-10" under the main-floor datum since 2026-08-21); far_elevation is the
    # outer edge, dropped enough to clear 2% over the run. Both ends of both surfaces dropped
    # with grade; the falls they encode are unchanged, and the falls are what R401.3 measures.
    impervious_surfaces=(
        # Apron on the north wall (y=36'), east of the breezeway (which spans x 6'-9"..
        # 11'-3") and east of SL-M-HP3PAD. Only 4' deep now that the garage stands at
        # y=40.5': it floors the slot between the two structures, falls away from the house,
        # and drains east rather than north into the garage stem. (It drained "east to the
        # driveway" until 2026-09-07; the driveway premise is retired — see
        # notes/garage_orientation_lot.md — and the 4.2% fall is unchanged and still legal,
        # it simply no longer drains *to* anything named.)
        #
        # ** THE WEST EDGE MOVED 14'-0" -> 15'-9" ON 2026-09-09, AND IT WAS FORCED. **
        # EQ-M-HP3-OD went 2'-4" east to get out of the widened breezeway's east glazing,
        # taking SL-M-HP3PAD to x 12'-1"..15'-5" — 1'-5" of pad inside this walk. 15'-9"
        # leaves the pad 4" clear, the same never-touch convention the pad uses against the
        # house cladding, and there is no version of that move that does not reach this
        # walk: even a zero-clearance cabinet puts the pad's east edge at 14'-4 11/16".
        # The walk loses 7 sf (32 -> 25); the fall it is graded on is in y and unchanged.
        ImperviousSurface(
            label="north entry drained paver landing and east approach",
            # ** THE WEST EDGE FOLLOWS THE STAIR, AND IT IS NOT DERIVED. ** This outline is
            # authored on the site while `params/breezeway.py::STAIR_FOOT_X_FT` derives from
            # TREAD_DEPTH_FT, so the two only agree because somebody keeps them agreeing.
            # The 2026-09-10 going change (24" -> 18") moved the stair foot from x=19'-6" to
            # x=17'-6", and the 2026-09-11 landing narrowing (LANDING_EAST_FT 11'-6" ->
            # 9'-7", the service door's east jamb) moved it to x=15'-7"; this edge moved
            # with it both times. Move it again if either moves again.
            outline=(pt(ft(15, 7), ft(36, 10.25)), pt(ft(30), ft(36, 10.25)),
                     pt(ft(30), ft(42, 10.75)), pt(ft(15, 7), ft(42, 10.75))),
            near_elevation=ft(-2, -10),
            far_elevation=ft(-3, -0.5),  # 2% eastward; first 36in is the lower landing
            kind="walk",
        ),
        # side patio on the east wall (x=36'), draining east toward the side-yard grade
        ImperviousSurface(
            label="patio",
            outline=(pt(ft(36), ft(10)), pt(ft(42), ft(10)),
                     pt(ft(42), ft(22)), pt(ft(36), ft(22))),
            near_elevation=ft(-2, -11),  # -1" below grade at the foundation
            far_elevation=ft(-3, -2),  # -4" below grade at the 6' outer edge (4.2% away)
            kind="patio",
        ),
        # The two pads in the pocket east of the porch, both authored in
        # params/sunken_garden.py. They were one 56.9 sf pour for a day; on 2026-09-04 the
        # condenser row crossed to the house side and ST-SG-PORCH took the south half, and a
        # rectangle spanning both would have been 94 sf of concrete to serve 40. Both tops
        # are -2'-8", 2" PROUD of the -2'-10" grade — Gree's "install 2 in above the expected
        # snow line" — and both fall away from the house. The Slabs are modelled flat at
        # their high edge; the fall is a finishing fact and lives here, where
        # code.R401_3_impervious can read it.
        #
        # SL-SG-HPPAD, x 29'-0"..32'-7" by y -3'-4"..-0'-10" — 8.96 sf, shrunk from 19.6
        # on 2026-09-04 when EQ-M-HP1-OD crossed to the north face. It falls 3/4" south
        # over 2'-6", 2.5% against R401.3's 2%, and its far edge lands 1/2" below grade so
        # the sheet leaves onto gravel rather than ponding at a lip.
        ImperviousSurface(
            label="hp pad",
            outline=(pt(ft(29), ft(-3, -4)), pt(ft(32, 7), ft(-3, -4)),
                     pt(ft(32, 7), ft(0, -10)), pt(ft(29), ft(0, -10))),
            near_elevation=ft(-2, -8),
            far_elevation=ft(-2, -8.75),
            kind="pad",
        ),
        # SL-M-HP3PAD, the north-side equipment pad under EQ-M-HP3-OD (params/hp3_pad.py),
        # x -0'-3"..3'-1" by y 37'-2 1/4"..39'-3" — 6.9 sf.
        #
        # ** THIS RECORD FOLLOWED ITS SLAB 12'-4" WEST ON 2026-09-10, TWO REVISIONS LATE. **
        # The pad went to the open north-west yard with EQ-M-HP3-OD (notes/
        # hp3_north_relocation.md); this surface stayed at x 9'-9"..13'-1", in the slot
        # between the house and the garage, describing a piece of ground that has had no
        # pad on it since. Nothing caught it: `code.R401_3_impervious` grades an authored
        # rectangle against the foundation, and a rectangle in the wrong place still grades.
        # Cross-check an ImperviousSurface against its Slab after any equipment move — the
        # two are separate records and only this comment ties them.
        #
        # Its fall straightened with the move, and the reason the old one was diagonal went
        # with it: the pad ran its sheet to the NORTH-EAST only because the garage stem
        # stood directly north of it and there was nowhere else for the water to go. In the
        # open yard off the house's north-west corner there is nothing north of it at all,
        # so it falls 1" straight north over 2'-0 3/4", 4.1% against R401.3's 2%, away from
        # the wall it abuts.
        ImperviousSurface(
            label="hp3 pad",
            outline=(pt(ft(0, -3), ft(37, 2.25)), pt(ft(3, 1), ft(37, 2.25)),
                     pt(ft(3, 1), ft(39, 3)), pt(ft(0, -3), ft(39, 3))),
            near_elevation=ft(-2, -8),
            far_elevation=ft(-2, -9),
            kind="pad",
        ),
        # ** THE PASSAGE FLOOR, NEW 2026-09-10 — AND IT IS A PAVED SURFACE ON PURPOSE. **
        # The house's north foundation and the garage's south foundation face each other
        # across 6'-6 1/2" of ground, fully roofed by the canopy. Neither can fall 6" in 10'
        # away from the other: R401.3's 5% ground rule has no solution in a slot that narrow
        # with a building on both sides. A PAVED surface owes 2%, not 5%, and that is a
        # solution — which is why the answer here is paving rather than a swale concept the
        # model has no word for.
        #
        # The strategy already existed at the east end and simply stopped 13'-6" short: the
        # drained paver landing above runs x 17'-6"..30' on the same y band and carries the
        # passage's water east into the open approach. This piece is the rest of it, from
        # x 4'-0" (2' outboard of the screen line, where the passage daylights into the west
        # yard) east to the stair foot at x 17'-6", where the landing takes over. Same y
        # band, same construction, one continuous surface in the field; two records only
        # because an ImperviousSurface is a rectangle and the landing carries its own note.
        #
        # 81.6 sf. **It does not touch the driveway/parking cap**: Ord. 23-43 bounds
        # `_PAVING_KINDS = ("driveway", "pad")` and this is a walk. Paving stands at 478 sf
        # of the 1,000 sf cap either way — there was room, and this does not spend it.
        #
        # It is COVERED, so it takes no direct rain; the code grants no exemption for that
        # and none is claimed. What the ground under the canopy and the four cast tiers
        # actually needs is to not pond and to drain out, and 2" over the 6'-0" run does
        # both. The fall is graded against the HOUSE, which is the foundation it abuts (its
        # near edge is 10 1/4" off the house and 2'-0" off the garage's stem line at the
        # closest corner); the garage side is the outlet, not a second thing to fall away
        # from. See `_foundation_enclosures` for why that is the rule and not a dodge.
        ImperviousSurface(
            label="house-to-garage passage floor",
            # East edge follows the paver landing's west edge above (the stair foot).
            outline=(pt(ft(4), ft(36, 10.25)), pt(ft(15, 7), ft(36, 10.25)),
                     pt(ft(15, 7), ft(42, 10.75)), pt(ft(4), ft(42, 10.75))),
            near_elevation=ft(-2, -10),
            far_elevation=ft(-3),  # 2.8% away from the house, draining east to the landing
            kind="walk",
        ),
        # SL-M-HP1PAD, the north-face pad under EQ-M-HP1-OD (params/hp1_north_pad.py),
        # x 32'-9 1/4"..36'-5 3/4" by y 36'-10"..39'-4" — 9.27 sf, new 2026-09-04, moved
        # 6'-6" east on 2026-09-07 with its cabinet. Same top, -2'-8", 2" proud of grade.
        # It runs 5 3/4" past the house's NE corner, into open yard, as the cabinet does.
        #
        # ** IT FALLS STRAIGHT NORTH, unlike SL-M-HP3PAD's diagonal. ** That pad runs its
        # fall on the diagonal only because the garage stem stands directly north of it and
        # there is nowhere else for the sheet to go. The garage is x 6'..30'; this pad is at
        # x 32'-9 1/4"..36'-5 3/4", with open front yard in front of it. 3/4" over 30" is
        # 2.5% against R401.3's 2%, away from the house, and that is the whole story.
        ImperviousSurface(
            label="hp1 pad",
            outline=(pt(ft(32, 9.25), ft(36, 10)), pt(ft(36, 5.75), ft(36, 10)),
                     pt(ft(36, 5.75), ft(39, 4)), pt(ft(32, 9.25), ft(39, 4))),
            near_elevation=ft(-2, -8),
            far_elevation=ft(-2, -8.75),
            kind="pad",
        ),
        # SL-SG-STAIRPAD, x 28'-6"..35'-3" by y -9'-0"..-6'-0" — 20.3 sf, the flight and its
        # bottom landing. It is 5'-2" clear of the house so R401.3's within-10-feet rule is
        # the only thing that reaches it at all; it falls 2" EAST over its 6'-9" run, 2.5%,
        # carrying meltwater off the treads away from the porch wall rather than along it.
        ImperviousSurface(
            label="porch stair pad",
            outline=(pt(ft(28, 6), ft(-9)), pt(ft(35, 3), ft(-9)),
                     pt(ft(35, 3), ft(-6)), pt(ft(28, 6), ft(-6))),
            near_elevation=ft(-2, -8),
            far_elevation=ft(-2, -10),
            kind="stair",
        ),
        # ** THE DRIVEWAY, NEW 2026-09-09. ** The garage's overhead door faced a lot with no
        # approach to it: notes/garage_orientation_lot.md records that the drive premise was
        # retired in the rotation, and it was retired one structure too far. Saint Paul DSI
        # will not review a garage a car cannot reach, and the drive is also the only place
        # a vehicle can leave the site, which is what the rock construction entrance above
        # is sited on.
        #
        # Geometry: 12'-0" wide, centred on D-G-OVERHEAD (the door spans x 10'..26' on
        # W-G-N, so its centreline is x=18'), from the garage face at y=67'-2 5/8" north to
        # the front lot line at y=84'-6". 12' is the ORDINANCE width, not the door width:
        # Ord. 23-43 caps a driveway in the front yard at 12'-0" and the 16' door gets its
        # flare in the apron, off this rectangle. It ran to y=105' against the retired
        # 100' x 165' ring and now stops at the real one, 17'-3 3/8" long, ~207 sf.
        #
        # ** THE PAVING CAP INVERTED WITH THE LOT. ** Ord. 23-43 caps driveway and parking
        # paving at the LESSER of 15% of the lot or 1,000 sf. On the retired 16,500 sf
        # placeholder, 15% was 2,475 sf and the flat 1,000 sf governed. On the real 6,650 sf
        # lot, **15% is 997.5 sf and the percentage governs instead** — barely, but it is the
        # binding number now, and it shrinks with any further correction to the lot area.
        # The drive plus the three `kind="pad"` surfaces come to 232 sf against it — 3.5%
        # of the lot, under a quarter of the cap — so the inversion moves no verdict today;
        # it is the arithmetic that has to be re-done first if any paving is added.
        # (`emit/draw/site_metrics.py` computes this cap for the C-101 coverage table; no
        # check grades it, so the table is where a reviewer sees it.)
        #
        # ** IT IS OUTSIDE code.R401_3_impervious's REACH AND THE ELEVATIONS ARE STILL REAL. **
        # That check measures against the PRIMARY foundation footprint (the house, y<=36')
        # and skips any surface whose nearest vertex is past 10'; this one starts 28'-9"
        # north of the house. The near/far pair below is the drive's own fall to the street,
        # 4 1/2" over 17'-3 3/8" (2.17%, the same bench slope it carried at its old length),
        # starting 1" below the -2'-10" garage threshold so the apron sheds away from the
        # slab rather than into it.
        ImperviousSurface(
            label="driveway",
            outline=(pt(ft(12), ft(67, 2.625)), pt(ft(24), ft(67, 2.625)),
                     pt(ft(24), ft(84.5)), pt(ft(12), ft(84.5))),
            near_elevation=ft(-2, -11),
            far_elevation=ft(-3, -3.5),
            kind="driveway",
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
        UtilityLine(kind=UtilityKind.WATER, path=(pt(ft(11), ft(72)), pt(ft(11), ft(62))),
                    entry=pt(ft(11), ft(62)), depth=ft(6)),
        # Runs in from the WEST lot line, which sits at x=-7' on the 50'-wide parcel (it
        # was x=-32' on the retired 100' ring).
        UtilityLine(kind=UtilityKind.POWER, path=(pt(ft(-7), ft(18)), pt(ft(0), ft(18))),
                    entry=pt(ft(0), ft(18)), depth=ft(3)),
    ),
)
