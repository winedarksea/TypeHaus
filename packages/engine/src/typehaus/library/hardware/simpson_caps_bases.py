"""The canopy's rated post heads and bases: AC/ACE caps, the A35 angle, the CBSQ base.

Split from ``simpson_post_bases.py`` (470 lines). Every number was read from the ICC-ES PDF
itself on 2026-09-30; the CBSQ's lateral row is the one exception, and it says so.

**Wet service.** ESR-2604 §3.2.2 and ESR-3050 §4.1 both tie the tabulated values to wood at
or below 19% moisture content, reduced by NDS ``C_M`` otherwise. Catlin's KDAT posts stand on
drained standoffs under cover and are graded DRY with that condition printed on the record,
exactly as ``CCQ46SDS_POST_CAP`` already is (houses/catlin/notes/canopy_west_band.md §5).
"""

from __future__ import annotations

from typehaus.hardware.catalog import (
    EXPOSURE_TREATED,
    ROLE_MODELED_CONNECTOR,
    ROLE_POST_BASE,
    ROLE_POST_CAP,
    AllowableLoads,
    StructuralHardware,
)
from typehaus.library.hardware._common import _SIMPSON

_ESR_2604 = ("ICC-ES ESR-2604 (Simpson Strong-Tie column caps and post caps), Table 3, "
             "read 2026-09-30")
_ZMAX = ("the Z suffix is the ZMAX (G185) coating of the same part; the report tabulates "
         "the steel and the nailing, and the coating changes neither")

#: AC6 MAX, the two-piece cap on a CONTINUOUS beam. Footnote 6: lateral is parallel to the
#: beam only; §3.1.3: used in pairs where the beam is continuous over the post.
AC6Z_POST_CAP = StructuralHardware(
    tag="simpson-ac6z-post-cap",
    name="AC6Z adjustable post cap (6x beam on 6x6), MAX nailing",
    role=ROLE_POST_CAP,
    manufacturer=_SIMPSON,
    model="AC6Z",
    exposure=EXPOSURE_TREATED,
    fits_nominal=("6x6",),
    source="Simpson Strong-Tie AC adjustable post cap (strongtie.com/ac) — two pieces, one "
           "each side of a 5-1/2 in beam continuous over a 6x6 post, W 5-1/2 in, L 8-1/2 in",
    allowable=AllowableLoads(
        uplift_lb=2815.0,
        lateral_f1_lb=2075.0,
        load_duration_factor=1.6,
        species="DF-L/SP (160% design-load multiplier row); wood MC <= 19% (§3.2.2)",
        fasteners="MAX: 14-16d into the beam and 14-16d into the post per assembly, round "
                  "AND triangular holes filled (footnote 2), equal on each piece (fn. 4)",
        citation=(_ESR_2604 + ": AC6 MAX uplift 2,815 lbf, lateral 2,075 lbf at C_D 1.6. "
                  "Footnote 3: not for a spliced beam. Footnote 4: in pairs. Footnote 6: "
                  "lateral is PARALLEL to the beam's length — F1 here means along the beam, "
                  "and there is no across-beam value. " + _ZMAX),
    ),
)

#: ACE6 MAX, the END-of-beam twin (§3.1.3: "ACE post caps are used to connect the end of a
#: beam to a post"). Catlin's south header ends sit on their posts, so the AC's "continuous
#: over the post" condition is met by this part and not by an AC.
ACE6Z_POST_CAP = StructuralHardware(
    tag="simpson-ace6z-end-post-cap",
    name="ACE6Z adjustable end post cap (6x beam end on 6x6), MAX nailing",
    role=ROLE_POST_CAP,
    manufacturer=_SIMPSON,
    model="ACE6Z",
    exposure=EXPOSURE_TREATED,
    fits_nominal=("6x6",),
    source="Simpson Strong-Tie ACE end post cap (strongtie.com/ac) — two pieces at the END "
           "of a 5-1/2 in beam landing on a 6x6 post, L 6-1/2 in",
    allowable=AllowableLoads(
        uplift_lb=1950.0,
        lateral_f1_lb=1760.0,
        load_duration_factor=1.6,
        species="DF-L/SP; wood MC <= 19% (§3.2.2)",
        fasteners="MAX: 10-16d into the beam and 10-16d into the post, round and triangular "
                  "holes filled, equal on each piece",
        citation=(_ESR_2604 + ": ACE6 MAX uplift 1,950 lbf, lateral 1,760 lbf at C_D 1.6, "
                  "lateral parallel to the beam (footnote 6). " + _ZMAX),
    ),
)

#: A35, ESR-3096 Table 5 — the across-beam path the AC's footnote 6 leaves out. The F1 and
#: F2 rows do not combine (fn. 3); F2 needs an angle on each side (fn. 6).
A35Z_FRAMING_ANGLE = StructuralHardware(
    tag="simpson-a35z-framing-angle",
    name="A35Z framing angle",
    role=ROLE_MODELED_CONNECTOR,
    manufacturer=_SIMPSON,
    model="A35Z",
    exposure=EXPOSURE_TREATED,
    source="Simpson Strong-Tie A35 framing angle (strongtie.com/a) — 18 ga, post face to "
           "beam soffit, and a plate end to a post side face",
    allowable=AllowableLoads(
        lateral_f1_lb=695.0,
        lateral_f2_lb=845.0,
        load_duration_factor=1.6,
        species="DF/SP",
        fasteners="6-SD9112 each leg (the 6+6 rows of Table 5)",
        citation=("ICC-ES ESR-3096 (Simpson Strong-Tie framing connectors), Table 5, read "
                  "2026-09-30: A35 with 6-SD9112 + 6-SD9112, F1 695 / F2 845 lbf, the same "
                  "at C_D 1.0-1.6 (fn. 2); directions do not combine (fn. 3). " + _ZMAX),
    ),
)

#: CBSQ66-SDS2, cast in. The uplift is measured THROUGH the concrete (cracked and uncracked
#: columns, 2,500 psi), so no separate anchor is bought and no ACI Ch. 17 row stands in for it.
CBSQ66_COLUMN_BASE = StructuralHardware(
    tag="simpson-cbsq66-sds2-column-base",
    name="CBSQ66-SDS2 cast-in column base (6x6)",
    role=ROLE_POST_BASE,
    manufacturer=_SIMPSON,
    model="CBSQ66-SDS2",
    exposure=EXPOSURE_TREATED,
    fits_nominal=("6x6",),
    source="Simpson Strong-Tie CBSQ column base (strongtie.com/cbsq) — 12 ga base, 10 ga x 3 "
           "in straps, W1/W2 5-1/2 in, D 6-7/8 in embedment, 1 in standoff, cast into the pour",
    bearing_standoff_in=1.0 + 0.1046,
    anchorage_in_rating=True,
    allowable=AllowableLoads(
        uplift_lb=3060.0,
        lateral_f1_lb=485.0,
        lateral_f2_lb=1270.0,
        download_lb=14420.0,
        load_duration_factor=1.6,
        species=None,
        fasteners="14 - SDS 1/4 in x 2 in into the post; the straps cast into >= 2,500 psi "
                  "concrete with >= 3 in side cover (fn. 4)",
        citation=("ICC-ES ESR-3050 (Simpson Strong-Tie embedded column bases), Table 1, "
                  "Wind and SDC A & B, read 2026-09-30: CBSQ66-SDS2 uplift 4,375 lbf "
                  "uncracked / 3,060 cracked (the CRACKED value is recorded), download "
                  "14,420 lbf at C_D 1.0; minimum side cover 3 in (fn. 4); fn. 5, the base "
                  "does not prevent rotation. The report publishes NO lateral: F1 485 / F2 "
                  "1,270 lbf are Simpson C-C-2024's CBSQ table, the manufacturer's own "
                  "catalog, and the directions do not combine with uplift except by a "
                  "linear unity sum"),
    ),
)

#: ESR-2105 Table 4, the coil-strap row a cut strap is graded on: ``(steel lbf, row lbf,
#: row nails total, nail)``. Footnote 1: half the nails in each member, so one end's share
#: of the row is ``row / (nails / 2)`` per nail — the pro-rated read ``lateral_band`` makes
#: for an end that holds fewer nails than the row.
COIL_STRAP_ROWS = {
    "CS16": (1705.0, 1890.0, 20, "10d x 2-1/2 in common"),
    "CS14": (2490.0, 2590.0, 26, "10d x 2-1/2 in common"),
}
COIL_STRAP_CITATION = ("ICC-ES ESR-2105 (Simpson Strong-Tie straps), Table 4, read "
                       "2026-09-30: CS16 1,890 lbf with 20-10d x 2-1/2 in common, steel "
                       "strength 1,705 lbf; CS14 2,590 / 2,490; C_D 1.6, SG >= 0.50, half "
                       "the nails in each member (fn. 1)")
