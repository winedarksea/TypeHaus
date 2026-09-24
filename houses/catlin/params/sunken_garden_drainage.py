"""Sunken garden court drainage — the field's underdrain, the court's area drain and its
overflow leg. The first two let go into FB-SG-ARCH's soakaway course; the leg relieves the
court's body of stone from FB-SG-W1 to the house tile and SM-B-RADON.

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
    pt,
)

from params.sunken_garden import (
    ARCH_AXIS_Y_FT,
    ARCH_BED_WIDTH_IN,
    BALCONY_FRONT_Y_FT,
    COURT_X_FT,
    COURT_Y_S_FT,
    FIELD_BOTTOM,
    FIELD_X_MID_FT,
    FIELD_Y_S_FT,
    SOAKAWAY_TOP,
    WALL_N_END_Y_FT,
    WALL_W_AXIS_X_FT,
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
# W-SG-ARCH, under the balcony overhang (the spot that ices last), at x=20' (2'-0" east of
# FD-SG-FIELD, 13'-0" from FD-SG-OVERFLOW) and 1" clear of the beam's north face; its basin
# voids the slab. A solid 4" riser drops through the 12" strip of FB-SG-ARCH's bed north of
# the beam and lets go at SOAKAWAY_TOP, -163 7/16", 12" below the frost line. Passive: no heat trace. The court has no modelled fall to it,
# and the basin can ice — both recorded in DESIGN-LOG, not solved.
#
# `catchment` is the open court south of the balcony's front edge — the surface a melt
# reaches that the balcony does not roof; `drainage.soakaway_storage` reads it.
_GRATE_IN = 12.0
_AD_Y_FT = ARCH_AXIS_Y_FT + 0.5 + (1.0 + _GRATE_IN / 2.0) / 12.0   # beam face + 1" + half
COURT_AREA_DRAIN = AreaDrain(
    uid="SGAD01AAAA", tag="AD-SG-COURT",
    position=pt(ft(FIELD_X_MID_FT + 2.0), ft(_AD_Y_FT)),
    grate_size=inch(_GRATE_IN), basin_depth=inch(12),
    outlet_diameter=inch(4), outlet_invert=SOAKAWAY_TOP,
    host_ref="SL-SG-FLOOR", discharge_ref="FB-SG-ARCH",
    product="NDS 1200 12in square catch basin", outlet_material="pvc",
    catchment=(pt(ft(COURT_X_FT[0]), ft(COURT_Y_S_FT)), pt(ft(COURT_X_FT[1]), ft(COURT_Y_S_FT)),
               pt(ft(COURT_X_FT[1]), ft(BALCONY_FRONT_Y_FT)),
               pt(ft(COURT_X_FT[0]), ft(BALCONY_FRONT_Y_FT))),
)

# ** THE OVERFLOW LEG: THE COURT'S SECOND WAY OUT, AND THE SUMP'S. ** The soakaway course is
# in glacial till, and MPCA's own numbers say that is a detention structure rather than an
# infiltration one (HSG D, 0.06 in/hr design rate). This leg lets the court and SM-B-RADON
# share overflow either way when one of them is behind: it is FB-SG-W1's `overflow_ref`, and
# the pit's bridge arrives by it.
#
# ** ON THE WEST HEEL, NOT DOWN THE COURT (2026-09-23). ** It ran down the centreline from the
# field, sleeved through W-SG-ARCH (SP-/PR-SG-ARCH-OVERFLOW, retired, uids spent). Since the
# court beds run no pipe, W1's stone IS the court's body and reaches to the closure break, so
# the leg is a short level trench from inside that stone, 2'-0" west of the wall axis on the
# footing's heel, across the joint into FB-B-S1's bedding. Almost no digging beyond the bed.
#
# ** -127 7/16" (the field profile's underside) is the COURT's lip; the PIT relieves at
# -123 7/16". ** The court's stone fills and spills here, never backing up into the field's
# gravel. The house end is higher: FB-B-S1's stone bottoms at -124 7/16" and SM-B-RADON takes
# its tile at -123 7/16", so the house footing tile surcharges 3-4" over this invert before
# the pit relieves. A true one-invert tie would be a dedicated pipe from the pit
# (plans/TODO.md). The trench's stone also joins the sub-slab radon stone to the
# court's, which opens at AD-SG-COURT's grate — logged there too.
_HOUSE_BED_FACE_Y_FT = -4.0 / 12.0   # FB-B-S1/S2's south face, measured
_OVERFLOW_X_FT = WALL_W_AXIS_X_FT - 2.0
GARDEN_OVERFLOW = FrenchDrain(
    uid="SGFD02AAAA", tag="FD-SG-OVERFLOW",
    path=(pt(ft(_OVERFLOW_X_FT), ft(WALL_N_END_Y_FT - 1.0)),
          pt(ft(_OVERFLOW_X_FT), ft(_HOUSE_BED_FACE_Y_FT))),
    invert=FIELD_BOTTOM,
    trench_width=inch(6), trench_depth=inch(8),
    tile=DrainTile(diameter=inch(4), sock=False, discharge="SM-B-RADON"),
    discharge_ref="SM-B-RADON",
)

BASEMENT_ELEMENTS = [GARDEN_UNDERDRAIN, COURT_AREA_DRAIN, GARDEN_OVERFLOW]
