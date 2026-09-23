"""Sunken garden court drainage — the field's underdrain, the court's area drain and its
overflow leg. All three let go into (or relieve) FB-SG-ARCH's soakaway course.

Split out of ``params/sunken_garden.py``, which publishes the court geometry these runs are
drawn against. Everything here is generated; uids are minted by hand (``haus fmt`` does not
visit ``params/*.py``).
"""

from __future__ import annotations

from typehaus import (
    AreaDrain,
    DrainTile,
    FrenchDrain,
    ft,
    inch,
    PipeRun,
    PipeSystem,
    pt,
    Service,
    SleevePenetration,
)

from params.sunken_garden import (
    ARCH_AXIS_Y_FT,
    ARCH_BED_WIDTH_IN,
    BALCONY_FRONT_Y_FT,
    COURT_TOP,
    COURT_X_FT,
    COURT_Y_S_FT,
    FIELD_BOTTOM,
    FIELD_X_MID_FT,
    FIELD_Y_N_FT,
    FIELD_Y_S_FT,
    SOAKAWAY_TOP,
)

# --- the field's underdrain, and the court's overflow leg --------------------------
#
# ** THE ASSEMBLY SAID "draining to DRW-SG-MAIN" AND NOTHING IMPLEMENTED IT. ** Until
# 2026-09-05 that was prose in a `source=` string with no element behind it — the exact
# failure `checks/mep/drainage.py`'s own docstring was written about. These two runs are
# the claim made real.
#
# `FrenchDrain` and not a `FootingBedding`'s derived tile: a bedding's tile follows the
# excavation under a footing, while this is "a run somebody put where the water goes".
#
# ** ONE LATERAL, AND THAT IS THE CHEAPEST ANSWER THAT IS ALSO THE RIGHT ONE. ** USGA caps
# lateral spacing at 15'-0". The field is 11'-0" square, so a single centre lateral leaves
# 5'-6" of reach each side, well inside the cap. A second lateral would be owed only past 15'-0"
# of E-W width, which this field cannot reach inside a 17'-0" court.
#
# ** NO PERIMETER "SMILE" DRAIN, DELIBERATELY. ** USGA's trench is 6" wide x 8" deep cut
# INTO the subgrade, which here bottoms at -135 7/16" — 5" below W-SG-ARCH's underside. Run
# hard against the walls, as USGA's perimeter detail wants, it would undermine the grade
# beam that is the court's only real strut. Down the centre it is clear of everything. The
# omission is a decision, not an oversight.
#
# ** NO WICKING BARRIER, AND THAT IS EARNED. ** USGA's optional perimeter membrane exists to
# stop a porous rootzone bleeding sideways into a fine-textured native surround. This field
# is bounded on all four sides by concrete — three retaining strips and the grade beam. The
# concrete IS the barrier.
#
# ** `sock=False`, AND IT IS THE ONLY TILE IN THIS HOUSE THAT CARRIES IT. ** USGA is
# explicit that "any piping encased in geotextile sleeves are not recommended", and PNW 675
# agrees: a sock in a sand profile clogs with fines and seals the line. The FT-SG-* and
# FB-* beds keep `sock=True` — a bearing course in clay is a different job, and there the
# sock is what stops the clay entering the pipe. Here the graded sand above IS the filter.
#
# uid minted by hand, deliberately: `haus fmt` does not visit `params/*.py`.
GARDEN_UNDERDRAIN = FrenchDrain(
    uid="SGFD01AAAA", tag="FD-SG-FIELD",
    # South end of the field to FB-SG-ARCH's south face, on the field's own centreline,
    # derived so it cannot drift from the field or the bed it drains into.
    path=(pt(ft(FIELD_X_MID_FT), ft(FIELD_Y_S_FT)),
          pt(ft(FIELD_X_MID_FT), ft(ARCH_AXIS_Y_FT - ARCH_BED_WIDTH_IN / 24.0))),
    # The trench floor AT THE SOUTH END: 8" into the subgrade below the profile's underside,
    # derived from the court plane and the profile depth. NEVER a literal —
    # `SPEC.field_depth_in` moves.
    invert=FIELD_BOTTOM - inch(8),
    # ** IT ARRIVES IN THE STONE, NOT OVER IT (2026-09-22). ** It used to dive 28" in 10' to
    # the old well's top and resolved as 28 stepped trench pieces. It now falls 1" over the
    # same 10' (0.83%, over USGA's 0.5%) and ends in FB-SG-ARCH's bed, whose stone runs from
    # the beam's underside (-130 7/16") down through the soakaway course — the -136 7/16"
    # outlet is inside that band, which is what `drainage.outfall_connection` grades.
    end_invert=FIELD_BOTTOM - inch(9),
    trench_width=inch(6), trench_depth=inch(8),
    tile=DrainTile(diameter=inch(4), sock=False, discharge="FB-SG-ARCH"),
    discharge_ref="FB-SG-ARCH",
)

# ** THE COURT'S AREA DRAIN (2026-09-22). ** A frozen putting-green field takes no snowmelt,
# so the paved rim needs its own way into the stone. A 12" grate in SL-SG-FLOOR just north of
# W-SG-ARCH, under the balcony overhang (the spot that ices last), 2'-0" west of the x=18'
# overflow line and 1" clear of the beam's north face; a solid 4" riser drops through the
# 12" strip of FB-SG-ARCH's bed north of the beam and lets go at SOAKAWAY_TOP, -163 7/16",
# 12" below the frost line. Passive: no heat trace. The court has no modelled fall to it,
# and the basin can ice — both recorded in DESIGN-LOG, not solved.
#
# `catchment` is the open court south of the balcony's front edge — the surface a melt
# reaches that the balcony does not roof; `drainage.soakaway_storage` reads it.
_GRATE_IN = 12.0
_AD_Y_FT = ARCH_AXIS_Y_FT + 0.5 + (1.0 + _GRATE_IN / 2.0) / 12.0   # beam face + 1" + half
COURT_AREA_DRAIN = AreaDrain(
    uid="SGAD01AAAA", tag="AD-SG-COURT",
    position=pt(ft(FIELD_X_MID_FT - 2.0), ft(_AD_Y_FT)),
    grate_size=inch(_GRATE_IN), basin_depth=inch(12),
    outlet_diameter=inch(4), outlet_invert=SOAKAWAY_TOP,
    host_ref="SL-SG-FLOOR", discharge_ref="FB-SG-ARCH",
    product="NDS 1200 12in square catch basin", outlet_material="pvc",
    catchment=(pt(ft(COURT_X_FT[0]), ft(COURT_Y_S_FT)), pt(ft(COURT_X_FT[1]), ft(COURT_Y_S_FT)),
               pt(ft(COURT_X_FT[1]), ft(BALCONY_FRONT_Y_FT)),
               pt(ft(COURT_X_FT[0]), ft(BALCONY_FRONT_Y_FT))),
)

# ** THE OVERFLOW LEG: THE COURT'S SECOND WAY OUT. ** The soakaway course is in glacial
# till, and MPCA's own numbers say that is a detention structure rather than an infiltration
# one (HSG D, 0.06 in/hr design rate). This leg is FB-SG-ARCH's `overflow_ref`: when the
# course and the drained section above it fill to -127 7/16", the water goes to the sump.
#
# ** Its invert is AT the profile underside. ** -127 7/16", 8" above the underdrain's trench
# floor. Storage in a soakaway is only the volume beneath its inlet, so the stone must fill
# and SPILL — never back up into the gravel, which would drown the rootzone from below.
#
# ** THE TRENCH STOPS AT THE GRADE BEAM'S NORTH FACE, AND THAT IS THE POINT. ** The leg from
# the field north to here is a 4" pipe SLEEVED through W-SG-ARCH at mid-depth, not an
# excavation: a stone trench crossing the beam at this invert would undermine the strut the
# free-body note holds the whole court together with. `FrenchDrain` has no way to say
# "sleeve", so the modelled trench is only the part that really is one; the cast opening is
# `SP-SG-ARCH-OVERFLOW` below. North of the court it ties into the house collector, which as of
# today falls to the same sump.
# ** IT NOW REACHES THE HOUSE STONE, AND IT USED TO STOP SIX INCHES SHORT. ** The trench
# ended at `_y_in_n` (-0'-10"), which is the porch deck's north edge and not a drainage
# elevation at all — the run stopped there because that is where the court's own geometry
# stops, and the sentence above ("North of the court it ties into the house collector") was
# the whole of the connection. `FB-B-S2`/`FB-B-S3`'s bedding stone starts 6" further north
# at -0'-4", so what lay between the two was six inches of undisturbed clay, and
# `drainage.outfall_connection` says so.
#
# `_HOUSE_BED_FACE_Y_FT` is that face, measured. Six inches is a trivial amount of digging
# and the defect it fixes is not trivial: this is the court's SECOND way out, and the leg
# that was missing is the one at the far end of it.
_HOUSE_BED_FACE_Y_FT = -4.0 / 12.0
GARDEN_OVERFLOW = FrenchDrain(
    uid="SGFD02AAAA", tag="FD-SG-OVERFLOW",
    path=(pt(ft(FIELD_X_MID_FT), ft(FIELD_Y_N_FT + 1.0)),
          pt(ft(FIELD_X_MID_FT), ft(_HOUSE_BED_FACE_Y_FT))),
    invert=FIELD_BOTTOM,
    trench_width=inch(6), trench_depth=inch(8),
    tile=DrainTile(diameter=inch(4), sock=False, discharge="SM-B-RADON"),
    discharge_ref="SM-B-RADON",
)

# The overflow crosses the grade beam as a pipe, not as a stone trench. Authoring its cast
# sleeve keeps the opening visible to reinforcement coordination and concrete takeoff.
GARDEN_OVERFLOW_SLEEVE = SleevePenetration(
    uid="SGSP01AAAA", tag="SP-SG-ARCH-OVERFLOW", host_ref="W-SG-ARCH",
    position=pt(ft(FIELD_X_MID_FT), ft(ARCH_AXIS_Y_FT)),
    pipe_diameter=inch(4), sleeve_diameter=inch(6),
    purpose=Service.DRAIN,
    axis="horizontal", center_elevation=GARDEN_OVERFLOW.invert + inch(2),
)
GARDEN_OVERFLOW_BEAM_PIPE = PipeRun(
    uid="SGPR01AAAA", tag="PR-SG-ARCH-OVERFLOW", system=PipeSystem.DRAIN,
    path=(pt(ft(FIELD_X_MID_FT), ft(ARCH_AXIS_Y_FT - 1.0)),
          pt(ft(FIELD_X_MID_FT), ft(ARCH_AXIS_Y_FT + 1.0))),
    diameter=inch(4), material="pvc",
    # A half-inch fall over this two-foot crossing supplies the minimum 1/4 in/ft slope;
    # its midpoint remains concentric with the sleeve above.
    elevations=(GARDEN_OVERFLOW.invert - COURT_TOP + inch(0.25),
                GARDEN_OVERFLOW.invert - COURT_TOP - inch(0.25)),
    serves=(),
)

BASEMENT_ELEMENTS = [GARDEN_UNDERDRAIN, COURT_AREA_DRAIN, GARDEN_OVERFLOW,
                     GARDEN_OVERFLOW_SLEEVE, GARDEN_OVERFLOW_BEAM_PIPE]
