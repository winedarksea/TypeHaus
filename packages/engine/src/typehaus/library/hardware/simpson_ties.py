"""Mudsill anchors, strap hold-downs, floor ties, stud-plate ties, coil strap.

Split out of the former ``library/hardware.py``; see the package docstring.
"""

from __future__ import annotations

from typehaus.hardware.catalog import (
    ROLE_COIL_STRAP,
    ROLE_EMBEDDED_STRAP_HOLDOWN,
    ROLE_FLOOR_TIE_HOLDOWN,
    ROLE_MUDSILL_ANCHOR,
    ROLE_STUD_PLATE_TIE,
    AllowableLoads,
    StructuralHardware,
)
from typehaus.library.hardware._common import _SIMPSON

MASA_MUDSILL_ANCHOR = StructuralHardware(
    tag="simpson-masa-mudsill-anchor",
    name="MASA mudsill anchor",
    role=ROLE_MUDSILL_ANCHOR,
    manufacturer=_SIMPSON,
    model="MASA",
    source="Simpson Strong-Tie MASA mudsill anchor (strongtie.com/masa) — cast into the "
           "top of a concrete or ICF wall to anchor the sill plate",
    # ESR-2555 Table 1, STANDARD INSTALLATION / 2x4, 2x6 / uncracked concrete / Wind and
    # SDC A&B. Two choices in reading this table are worth stating:
    #   * **Uncracked** is recorded (920 vs 750 lbf uplift cracked). A sill plate at the top
    #     of a wall is in the compression zone and away from flexural cracking; if a reviewer
    #     disagrees the cracked column is one line away in the same table.
    #   * **Wind and SDC A&B**, not SDC C-F: Minnesota is SDC A/B.
    # The species caveat below is the real one. §3.2.3 requires SG >= 0.50 lumber, and this
    # house's sill plates are SPF (SG 0.42). The tabulated values therefore do NOT apply
    # as-is here, which is exactly why `species` records what the report says rather than
    # what the house builds.
    allowable=AllowableLoads(
        uplift_lb=920.0,
        lateral_f1_lb=1475.0,
        lateral_f2_lb=1095.0,
        load_duration_factor=1.6,
        species="DF/SP or better — §3.2.3 requires assigned SG >= 0.50; catlin's SPF "
                "sill plates are SG 0.42 and these values do not apply to them unreduced",
        fasteners="3 - 10d x 1.5 in each side leg + 6 - 10d x 1.5 in top, "
                  "strap cast into the wet concrete",
        citation=("ICC-ES ESR-2555 (MASA/MASAP foundation anchor straps) Table 1, standard "
                  "installation, 2x4/2x6 sill, uncracked concrete, Wind and SDC A&B; §3.2.3 "
                  "for the SG >= 0.50 requirement. Read 2026-08-30"),
    ),
)

STHD_STRAP_HOLDOWN = StructuralHardware(
    tag="simpson-sthd-embedded-strap-holdown",
    name="STHD embedded strap-tie holdown",
    role=ROLE_EMBEDDED_STRAP_HOLDOWN,
    manufacturer=_SIMPSON,
    model="STHD",
    source="Simpson Strong-Tie STHD embedded strap-tie holdown (strongtie.com/sthd) — "
           "cast into concrete and nailed to the framing at the end of a braced sill run",
    # NO ALLOWABLE ON THE FAMILY RECORD, DELIBERATELY. The family spans STHD8/10/14 and the
    # report tabulates each separately (STHD10 endwall cracked 2,480 lbf against STHD14's
    # 4,410), so one number here would be right for one member of the family and wrong for
    # the rest. The size a house actually specifies carries the row — see STHD14RJ below.
)

#: ICC-ES ESR-2920, "Cast-in-Place Strap-Style Hold-Downs and Purlin Anchors", reissued
#: February 2026, Table 1 — read 2026-09-22 from the ICC-ES PDF. **NOT ESR-2611**, which
#: evaluates the SSTB/SB/SABR anchor bolts and carries no STHD row at all.
STHD14RJ_STRAP_HOLDOWN = StructuralHardware(
    tag="simpson-sthd14rj-embedded-strap-holdown",
    name="STHD14RJ embedded strap-tie holdown (rim-joist length)",
    role=ROLE_EMBEDDED_STRAP_HOLDOWN,
    manufacturer=_SIMPSON,
    model="STHD14RJ",
    source="Simpson Strong-Tie STHD14RJ — the 39-5/8\" strap of the STHD14 (26-1/8\"), cast "
           "14\" into the concrete and nailed up PAST the floor band into the studs above. "
           "The RJ length is the whole reason this part is here: catlin's main-floor braced "
           "wall panels stand on a floor deck over the basement wall, and the standard strap "
           "does not reach them",
    # Table 1 publishes ONE set of wood-side values per model, shared by STHD14 and
    # STHD14RJ (the rows are paired "STHD14/STHD14RJ"); only the strap length differs.
    # The 8" stem-wall rows are the ones read: catlin's basement wall is 8" nominal.
    # ENDWALL is recorded — the lowest of the three installation columns — because the
    # geometry at a braced-wall-line end is what this part is authored for and a corner
    # value would flatter a strap that turns out to sit at an end. Wind / SDC A&B, and
    # uncracked and cracked read the SAME for this model, so the crack question does not
    # arise here (it does for the STHD10: 4,075 -> 3,350 at a corner).
    allowable=AllowableLoads(
        uplift_lb=4410.0,
        # ESR-2920 §4.1.1 says the tabulated loads are ASD and already include the NDS
        # load-duration factor, and never states which. §5.8 limits the part to tension
        # from WIND OR EARTHQUAKE only, and 1.6 is the factor those two carry — so the
        # number is the report's own scope read back, not a choice, and it is recorded
        # rather than left None so nothing downstream re-applies a duration increase.
        load_duration_factor=1.6,
        species="sawn lumber SG >= 0.42 by Table 1 footnote 8 (the nail counts are set at "
                "0.42), which is the SPF this house frames — but §3.2.3 of the same report "
                "says SG >= 0.50. The report contradicts itself and the conflict is recorded "
                "rather than resolved; at 4,410 lbf against an 800 lbf requirement the "
                "margin swallows any species derate either reading would impose",
        fasteners="30 - 16d sinker nails into a double 2x or larger vertical member "
                  "(footnote 2: 10d common may be substituted with no reduction); strap cast "
                  "14 in into the pour with one No. 4 bar 3-5 in below the top of the "
                  "foundation (§4.2, and it may be the foundation's own rebar); 17 in maximum "
                  "unnailed clear span across the rim, plate and sill",
        citation=("ICC-ES ESR-2920 (cast-in-place strap-style hold-downs), Table 1, "
                  "\"installed on wood vertical members - 2,500 psi concrete\", 8 in minimum "
                  "stem wall, STHD14/STHD14RJ row, Wind and SDC A&B: midwall 5,285, corner "
                  "5,285, endwall 4,410 lbf, uncracked and cracked alike, 30 nails, "
                  "l_e = 14 in. Read 2026-09-22. §2.0 qualifies the IRC use: for wall "
                  "bracing the tabulated capacity must equal or exceed what R602.10 asks "
                  "for, which is 800 lbf. C_D is included per §4.1.1; the report states no "
                  "number for it"),
    ),
)

#: The same report's 6-inch stem-wall rows, for a strap cast into an ICF-6 core rather than
#: into an 8-inch poured wall. Separate record because the allowable belongs to the WALL the
#: strap is cast in, not only to the part: 4,935 / 4,935 / 3,065 lbf (midwall / corner /
#: endwall) at 6 in against 5,285 / 5,285 / 4,410 at 8 in.
STHD14_STRAP_HOLDOWN = StructuralHardware(
    tag="simpson-sthd14-embedded-strap-holdown",
    name="STHD14 embedded strap-tie holdown",
    role=ROLE_EMBEDDED_STRAP_HOLDOWN,
    manufacturer=_SIMPSON,
    model="STHD14",
    source="Simpson Strong-Tie STHD14 — the 26-1/8\" strap, cast 14\" into the pour and "
           "nailed straight up into the studs where the wall bears on the concrete with no "
           "floor band between (catlin's garage, on its ICF stem)",
    allowable=AllowableLoads(
        uplift_lb=3065.0,
        # ESR-2920 §4.1.1 says the tabulated loads are ASD and already include the NDS
        # load-duration factor, and never states which. §5.8 limits the part to tension
        # from WIND OR EARTHQUAKE only, and 1.6 is the factor those two carry — so the
        # number is the report's own scope read back, not a choice, and it is recorded
        # rather than left None so nothing downstream re-applies a duration increase.
        load_duration_factor=1.6,
        species="sawn lumber SG >= 0.42 by Table 1 footnote 8; see the STHD14RJ record for "
                "the report's own contradiction with its §3.2.3",
        fasteners="30 - 16d sinker nails into a double 2x or larger vertical member; 14 in "
                  "embedment in a 6 in minimum stem wall with one No. 4 bar 3-5 in below "
                  "the top of the pour (§4.2)",
        citation=("ICC-ES ESR-2920 Table 1, 6 in minimum stem wall, STHD14/STHD14RJ row, "
                  "Wind and SDC A&B, ENDWALL column (the lowest of the three): 3,065 lbf, "
                  "uncracked and cracked alike; midwall and corner both read 4,935. Read "
                  "2026-09-22"),
    ),
)

#: ICC-ES ESR-2330, "Screw Hold-Down Connectors", reissued May 2026, Table 4 — read
#: 2026-09-22. The report spells the model "DTT2"; §3.2.1 says the -Z (G185) suffix is
#: covered by the same values.
DTT2Z_FLOOR_TIE = StructuralHardware(
    tag="simpson-dtt2z-tension-tie",
    name="DTT2Z screw hold-down / tension tie",
    role=ROLE_FLOOR_TIE_HOLDOWN,
    manufacturer=_SIMPSON,
    model="DTT2Z",
    source="Simpson Strong-Tie DTT2Z tension tie (strongtie.com/dtt) — one each side of a "
           "floor, joined by a 1/2 in threaded rod through the band, to carry a braced wall "
           "panel's end tension from an upper storey into the post below it (R602.10.7)",
    # The 1.5 in row is recorded, not the 3.0 in one: it is the lower number and it applies
    # to any member from a single 2x up, so a pack cannot be credited with a thickness the
    # model does not state. ESR-2330 §2.0 lists R602.10.7 among the report's prescriptive
    # IRC uses, which is precisely the clause this part is authored under.
    allowable=AllowableLoads(
        uplift_lb=1825.0,
        load_duration_factor=1.6,
        species="sawn or engineered lumber, SG >= 0.50 (§3.2.2) — DF-L or SP. ESR-2330 "
                "publishes NO SPF column, and this house frames SPF (SG 0.42): the two "
                "corner posts this part lands on are specified DF-L for that reason",
        fasteners="8 - SDS 1/4 x 1-1/2 in screws into a member at least 1-1/2 in thick and "
                  "3-1/2 in wide (footnote 6), plus the supplied F844 plate washer under the "
                  "nut (footnote 1). The 1/2 in ASTM A307/A36/F1554 rod and its anchorage are "
                  "OUTSIDE the report: §4.1.3 hands embedment, edge and end distance to a "
                  "registered design professional",
        citation=("ICC-ES ESR-2330 (Simpson Strong-Tie screw hold-down connectors), Table 4, "
                  "DTT2 series, 1.5 in wood member row: 1,825 lbf at both C_D 1.0 and 1.6 "
                  "(the 3.0 in row reads 2,000 / 2,145). Read 2026-09-22. Footnote 3: the "
                  "duration factors are already in the tabulated values and no further "
                  "increase is allowed. §4.1: the values are for continuously dry interior "
                  "service; treated or fire-retardant lumber is outside the report's scope"),
    ),
)

SP4_STUD_PLATE_TIE = StructuralHardware(
    tag="simpson-sp4-stud-plate-tie",
    name="SP4 stud plate tie (2x4)",
    role=ROLE_STUD_PLATE_TIE,
    manufacturer=_SIMPSON,
    model="SP4",
    fits_nominal=("2x4",),
    source="Simpson Strong-Tie SP stud plate tie family (strongtie.com/sp) — SP4 is the "
           "published size for a 2x4 stud-to-plate connection",
)

SP6_STUD_PLATE_TIE = StructuralHardware(
    tag="simpson-sp6-stud-plate-tie",
    name="SP6 stud plate tie (2x6)",
    role=ROLE_STUD_PLATE_TIE,
    manufacturer=_SIMPSON,
    model="SP6",
    fits_nominal=("2x6",),
    source="Simpson Strong-Tie SP stud plate tie family (strongtie.com/sp) — SP6 is the "
           "published size for a 2x6 stud-to-plate connection",
)

CS16_COIL_STRAP = StructuralHardware(
    tag="simpson-cs16-coiled-strap",
    name="CS16 coiled strap, 16 ga",
    role=ROLE_COIL_STRAP,
    manufacturer=_SIMPSON,
    model="CS16",
    unit="coil",
    source="Simpson Strong-Tie CS16 coiled strap (strongtie.com/cs) — 16 ga coiled "
           "strapping cut to length for wall-to-wall continuity across a floor band",
    # **A ladder, not a number, and the model does not carry the rung.** ESR-2105 Table 4
    # publishes the CS16 at 1,890 lbf with 20 - 10d x 2-1/2 in common nails, or 1,725 lbf
    # with 22 - 8d common, against a steel strength of 1,705 lbf — and footnote 1 requires
    # half the total in each member. The allowable is therefore a function of how many nails
    # are actually driven, and `takeoff/anchors.py::coil_strap_rows` bills coils by LENGTH.
    # Nothing in this model says how many nails go in a given strap.
    #
    # Recording 1,890 anyway would be the single most tempting error available in this file:
    # it is a real published number, from the right report, for the right part, and it would
    # be wrong for any strap nailed with fewer than 20 nails — which is to say, wrong for
    # every strap in this house, because none of them has a nail count at all. So the load
    # stays None and the citation carries the ladder for whoever adds nail counts later.
    allowable=AllowableLoads(
        fasteners="by nail count — 20 - 10d x 2-1/2 in common or 22 - 8d common, half in "
                  "each connected member (ESR-2105 Table 4 footnote 1); the model carries "
                  "no nail count for a coil strap",
        citation=("ICC-ES ESR-2105 (CS/CMST coil straps) Table 4, read 2026-08-30: CS16 "
                  "1,890 lbf at 20-10d x 2-1/2 common, 1,725 lbf at 22-8d common, steel "
                  "strength 1,705 lbf, all at SG >= 0.50 (footnote 2). No single value is "
                  "recorded because the allowable is selected by a nail count this model "
                  "does not track, and the species basis is SG 0.50 against this house's SPF"),
    ),
)

#: ICC-ES ESR-1622, the ABU family's evaluation report.
