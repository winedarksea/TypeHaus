"""North entry STRUCTURE — the piers, columns, headers and beams the landing stands on.

Split out of `params/breezeway.py` on 2026-09-10 (AGENTS.md's 500-line rule; the
`plan/storeys/attic_studio.py` precedent). The cut is at the seam that already existed:
**everything here is below and including the beams** — what carries load to the ground —
and `breezeway.py` authors what sits on top of it, the deck, the tiers, the guards and the
screen. Both are ordinary `params/` modules, not `# haus: editable`, which is correct:
piers and headers are structure, not a thing the UI drags.

The bearing map is `notes/north_entry_structure.md`; the arithmetic is
`notes/north_entry_piers.md`, which oracles `engineering/roof_beam.py` and the pier calcs.

**The landing touches nothing on the house, and the canopy bears on nothing of the
garage — but since 2026-09-29 it BRACES off it.** Grep this file for `W-B-` or `W-G-` and
expect nothing but comments. The landing's house-side bearing is two cast piers on the pier
line at y=37'-6"; the canopy stands on four supports of its own for gravity, and its
lateral load crosses the tied joint into `RF-GARAGE` and the garage's walls
(`RF-BW-CANOPY.diaphragm.delivers_to`, notes/canopy_garage_diaphragm.md). What stands
under the east header is `EAST_POST_SYSTEM` below.

**Two pier depths, on purpose.** The house-side pads bear at -9'-11 7/16", the house footing
underside, because the basement excavation is already open to it -- and they must be cast
WHILE it is open or they undermine the house footing ten inches away. The garage-side pads
bear at -7'-4", their tops level with the garage strip footings' tops, and are cast with the
garage foundation. There is no excavation out there to make depth cheap.

**KDAT longevity, house-wide (owner, 2026-09-10).** Every treated member here and in
`breezeway.py` carries the same four-part detail, stated once rather than per element:
304 stainless fasteners (316 Cap-Tor xd for Trex boards; structural connectors per schedule);
butyl joist tape over every beam and rim top (`top_protection`);
AWPA M4 field treatment of every cut end, notch and drilled hole with 2% copper naphthenate
(IRC R317.1.1 makes this "shall", not advice); and a pigmented penetrating oil finish
applied on installation. `AN-BW-KDAT` carries it onto the drawings.
"""

from typehaus import (
    Annotation, BarSpec, Beam, Connector, ConnectorKind, DeckLayer, FloorSystem, Footing,
    JoistSpec, Node, Pad, Post, Railing, RailingKind, ReinforcementSpec, SlatScreen, Stair,
    ft, inch, pt,
)
from typehaus.library import TREX_ENHANCE_BASICS_DECK_LAYER
from typehaus.resolve.connector_geometry.bases_caps import (
    COLUMN_BASE_DIMENSIONS,
    STEEL_GAUGE_THICKNESS_IN,
)
from params.cladding import HOUSE_NS_OUTBOARD_IN
from params.column_heads import CBSTQ66Z_HEAD, HETA20Z_PAIR_HEAD, STANDOFF_PACK_IN
from params.east_posts import east_supports, full_height_columns, moment_piers, pier_assembly
from plan.storeys.garage import (
    GARAGE_X_EAST, GARAGE_X_WEST, GARAGE_Y_SOUTH, SERVICE_DOOR_OFFSET, SERVICE_DOOR_WIDTH,
)

# What stands under BM-BW-RE: "steel" | "kdat" | "cast" (params/east_posts.py,
# notes/canopy_garage_diaphragm.md). All three are graded by
# tests/test_catlin_east_post_variants.py.
EAST_POST_SYSTEM = "kdat"

HOUSE_CLADDING_Y_FT = 36 + HOUSE_NS_OUTBOARD_IN / 12
GARAGE_CLADDING_Y_FT = GARAGE_Y_SOUTH.feet - 0.875 / 12
# D-G-SERVICE's rough opening (garage SW corner, plan/storeys/garage.py::SERVICE_DOOR_OFFSET) sets
# the east edge of the landing: the deck ends on its east jamb and the east edge beam sits just
# inside it. The west edge is the canopy column line.
SERVICE_RO_WEST_FT = GARAGE_X_WEST.feet + SERVICE_DOOR_OFFSET.feet
SERVICE_RO_EAST_FT = SERVICE_RO_WEST_FT + SERVICE_DOOR_WIDTH.feet
# The column lines are the garage's truss bearing lines (decision #108): each header centres on
# the 2x6 garage plate it extends, so one truss, heel at the outside face and bottom chord across
# the full 5 1/2", bears the same on both roofs.
GARAGE_PLATE_INSET_FT = (0.625 + 5.5 / 2) / 12
# The column line, 6'-3 3/8"; also the screen panel's reference.
LANDING_WEST_FT = GARAGE_X_WEST.feet + GARAGE_PLATE_INSET_FT
# East edge: the RO's east jamb covers both the D-M-ENTRY and D-G-SERVICE patches.
LANDING_EAST_FT = SERVICE_RO_EAST_FT
# The west corrugated plane, published so nothing re-derives it: W-BW-SCREEN's
# `alignment=face("stud-ext", offset=inch(-1.75))` (params/breezeway.py) puts its 2x4s flush with
# the 6x6s' west faces, 1" west of the column line, so both west planes are the garage's own.
# W-BW-SCREEN-SKIRT reads this: a drifted skirt is a step in steel, graded by nothing.
SCREEN_AXIS_X_FT = LANDING_WEST_FT - (5.5 - 3.5) / 24
SCREEN_CLADDING_WEST_X_FT = SCREEN_AXIS_X_FT - (1.75 + 0.625 + 0.875) / 12
assert abs(SCREEN_CLADDING_WEST_X_FT - (GARAGE_X_WEST.feet - 0.875 / 12)) < 1e-9
DECK_FINISH_FT = 0.0
DECK_JOIST_TOP_FT = DECK_FINISH_FT - TREX_ENHANCE_BASICS_DECK_LAYER.thickness.feet
JOIST_DEPTH_IN = 7.25

# Pier line y=37'-6" leaves room to form a pier off the house concrete face (W-B-N2/N3, y=36'-4")
# and cladding face (36'-7 1/4"). These piers bottom on the house footing's plane about 10" away:
# cast them in the open basement excavation, never after backfill (AN-BW-STRUCTURE).
PIER_LINE_Y_FT = 37.5
# Half of a 6x6 canopy column. BM-BW-SCSILL's ends are set off the column centres by this (the 6x6
# is wider than the 3" seat beam on the same centreline).
COLUMN_HALF_FT = 2.75 / 12
# Seat beams start SEAT_END_GAP_IN past the west column's face: with `axis="y"` the CBSTQ strap
# leaves sit on the column's E/W faces, so the beam stops 1/8" off the SDS heads (strap 0.1345 +
# head 0.190, ESR-2236 max, + 1/8" fit-up = 0.4495"). The LUS26-2Z hangs on an 11/32" filler
# notched round the strap, end gap 0.1055" vs Simpson's 1/8" (C-C-2026 p. 22 note m); a longer
# beam cannot get there (canopy_west_band.md, 2026-11-06 amendment (b)). Rotating the base would
# put F1 along the screen (canopy_west_band.md §4c).
SDS_HEAD_IN = 0.190
SEAT_END_GAP_IN = STEEL_GAUGE_THICKNESS_IN[COLUMN_BASE_DIMENSIONS.strap_gauge] + SDS_HEAD_IN + 0.125
SEAT_START_X_FT = LANDING_WEST_FT + COLUMN_HALF_FT + SEAT_END_GAP_IN / 12
PIER_BOTTOM_FT = -(9 + 9.4375 / 12)   # nominal; pads resolve 2" lower, at the footing underside
# 10" pad, not 12": a 12" pad would top at -8'-9 7/16" and swallow the garage hydrant line
# (-8'-10"); at 10" it passes 1 7/16" clear above.
FOOTING_DEPTH_FT = 10 / 12
FOOTING_TOP_FT = PIER_BOTTOM_FT + FOOTING_DEPTH_FT
# Every landing bearing is cast concrete (pier tops about 18" above grade, Site.grade -2'-10"), so
# no treated member lies below the deck framing. The seats are dropped, not flush: floor beams sit
# ON them, since flush framing reads as `structural.member_interference` FAILs without a hanger.
SEAT_TOP_FT = DECK_JOIST_TOP_FT - JOIST_DEPTH_IN / 12      # -8.19"
BEARING_TOP_FT = SEAT_TOP_FT - JOIST_DEPTH_IN / 12         # -15.44", the seat-beam SOFFIT
# Piers are cast one pack (STANDOFF_PACK_IN) below the soffits so the SS316 pack is a solid; the
# CBSTQ bases under PT-BW-CW/-CNW drop with them.
PIER_TOP_FT = BEARING_TOP_FT - STANDOFF_PACK_IN / 12       # -16.19"

# Headers top out at the GARAGE PLATE, +7'-4" (W-G-E/W-G-W z1), so RF-BW-CANOPY is one plane with
# RF-GARAGE. The soffit (+6'-4 1/8") is where SB-BW-BAND's top plate stops.
HEADER_TOP_FT = 7 + 4 / 12
HEADER_DEPTH_IN = 11.875
HEADER_SIZE = "5.5x11.875"
HEADER_SOFFIT_FT = HEADER_TOP_FT - HEADER_DEPTH_IN / 12
ROOF_COLUMN_EAST_X_FT = GARAGE_X_EAST.feet - GARAGE_PLATE_INSET_FT  # 29'-8 5/8"

# W-BW-SCREEN's top: it covers the guard zone outright and is SB-BW-BAND's sill. No cross rails.
SCREEN_PANEL_TOP_FT = 4.0


# One tier of beams: the joists run N-S straight on the two seat beams. The seats, not N-S beams
# on the piers, are the tier that fits: x=6'-3 3/8" is occupied at both y stations by a canopy
# column on the same pier, so a beam there would interpenetrate it.
#
# BM-BW-FE is the deck's east edge beam, seat to seat in the joist plane; nothing crosses the stem
# or W-G-S. Its tip is what line 1 of the deck tie lands on (params/landing_tie.py), wood to wood
# into W-G-S's east jamb pack. It is 3-ply because the tie's HL43HDG is published only into wood
# >= 5 1/8" thick (C-C-2024 p. 303 fn 5): the bolt passes through FE (4 1/2") and the rim (1 1/2").
#
# The joist field's edges are joist centrelines: west clear of the 6x6 columns (east face 6'-6
# 1/8"), east clear of BM-BW-FE (west face 9'-2 1/2").
BEAM_WIDTH_IN = 3.0
EDGE_BEAM_WIDTH_IN = 4.5
JOIST_MEMBER_WIDTH_IN = 1.5
FIELD_WEST_X_FT = LANDING_WEST_FT + 3 / 12 + JOIST_MEMBER_WIDTH_IN / 24
FIELD_EAST_X_FT = LANDING_EAST_FT - EDGE_BEAM_WIDTH_IN / 12 - JOIST_MEMBER_WIDTH_IN / 24
# FE's east face is ON the RO's east jamb line; the deck's east edge is the same jamb.
EDGE_BEAM_X_FT = SERVICE_RO_EAST_FT - EDGE_BEAM_WIDTH_IN / 24
HOUSE_SEAT_Y_FT = PIER_LINE_Y_FT
# The garage seat stands 8" south of the cladding face, clear of the stem (W-G-S's bottom plate
# and corner post; the concrete core is north of this line). The joists cantilever north to the
# framing edge, inside R507.5.1's quarter of the back span.
GARAGE_SEAT_Y_FT = GARAGE_CLADDING_Y_FT - 8 / 12

# The joist field runs south to y=36'-8 1/2", cantilevering 9 1/2" past the seat. A deck sheet
# running 12 1/4" to the cladding over air is past `structural.subfloor_oversail`'s 8" bound
# (`preferences.toml [framing] bearing_plan_tolerance_in`, also used by takeoff/uplift.py): the
# uplift pass then finds neither a tie nor a hanger and FAILs every member under the deck, far from
# its cause. The southernmost joist IS the rim.
FRAME_Y0_FT = 36 + 8.5 / 12
FRAME_Y1_FT = GARAGE_CLADDING_Y_FT - 0.75 / 12
# Boards stay 1/2" off the house cladding so the rainscreen gap drains. Abutting is not bearing,
# but it has to be DRAWN or a carpenter will close it.
DECK_SHEET_SOUTH_Y_FT = HOUSE_CLADDING_Y_FT + 0.5 / 12
DECK_SHEET_NORTH_Y_FT = GARAGE_CLADDING_Y_FT - 0.5 / 12
# A-508's cut, 55 1/2" north of the deck sheet: mid-panel of the MDO screen, so the MDO layer is
# in the cut.
DETAIL_CUT_Y_FT = DECK_SHEET_SOUTH_Y_FT + 55.5 / 12


def rectangle(x0, y0, x1, y1):
    return (pt(ft(x0), ft(y0)), pt(ft(x1), ft(y0)),
            pt(ft(x1), ft(y1)), pt(ft(x0), ft(y1)))


NODES = []
BEAMS = []


def beam(number, tag, x0, y0, x1, y1, bearings, top=DECK_JOIST_TOP_FT, size="2-2x8",
         assembly="BEAM_KDAT", roof_bearing_insets=None):
    for end, x, y in (("S", x0, y0), ("N", x1, y1)):
        NODES.append(Node(uid=f"BWNB{number:02d}{end}AAA", tag=f"N-{tag}-{end}",
                          position=pt(ft(x), ft(y))))
    result = Beam(uid=f"BWB{number:03d}AAAA", tag=tag,
                  start_node=f"N-{tag}-S", end_node=f"N-{tag}-N", size=size,
                  top_elevation=ft(top), bearing_refs=bearings, assembly=assembly,
                  roof_bearing_insets=roof_bearing_insets,
                  top_protection="butyl-tape-beam")
    BEAMS.append(result)
    return result


# Seat beams on cast piers (`structural.deck_beam_span` reads two Posts each). `bearing_refs` stays
# on the PIERS, the end of the load path that `pier_basis`'s tributary is built on; naming the
# columns drops PT-BW-W/-GW's dowel-lap limit state from the register. The west ends hang off the
# column (CN-BW-HGR-*, LUS26-2Z): authored to the column line, inside the 6x6, and only an authored
# hanger pair is cleared by `_butt_joint`. They start SEAT_END_GAP_IN past the column face, off the
# base strap (`structural.post_base_interference`); R507.5.2 needs 3" of bearing on the pier.
beam(1, "BM-BW-HOUSE-SEAT", SEAT_START_X_FT, HOUSE_SEAT_Y_FT,
     LANDING_EAST_FT, HOUSE_SEAT_Y_FT, ("PT-BW-W", "PT-BW-E"), SEAT_TOP_FT)
beam(2, "BM-BW-GARAGE-SEAT", SEAT_START_X_FT, GARAGE_SEAT_Y_FT,
     LANDING_EAST_FT, GARAGE_SEAT_Y_FT, ("PT-BW-GW", "PT-BW-GE"), SEAT_TOP_FT)
# The east edge beam, seat to seat with the joist field. Uid number stays 5: 3 (BM-BW-FW), 4
# (BM-BW-FC) and 11 are retired. Its tip runs 3/4" past the joist ends to the garage's cladding
# face, so the deck tie's bolt stands 2" (4D) off the end grain (params/landing_tie.py).
beam(5, "BM-BW-FE", EDGE_BEAM_X_FT, FRAME_Y0_FT, EDGE_BEAM_X_FT, GARAGE_CLADDING_Y_FT,
     ("BM-BW-HOUSE-SEAT", "BM-BW-GARAGE-SEAT"), size="3-2x8")

# The canopy is freestanding on four 6x6 posts of its own for gravity (PT-BW-CW/-CNW west,
# PT-BW-RE/-RNE east); nothing bears on a garage wall terminus. x=6'-3 3/8" and x=29'-8 5/8" are
# the garage's truss bearing lines, so the roofs are one plane with sheathing continuous across the
# tied joint (the canopy's lateral system, AN-BW-ROOF), which carries no gravity.
#
# Headers end flush on the outer faces of their end posts (65 1/4", no tails) on ACE6Z caps. The
# deck reaches the garage on its own north overhang (plan/storeys/garage.py); the header does not.
#
# 5-1/2" x 11-7/8" glulam, flush with the 6x6 faces: the joints chose it, not bending. An AC6/ACE6
# cap is published for a 5-1/2" beam on a 6x6 (ESR-2604 Table 3, the only post cap with a lateral
# row along the beam), and the flush face takes the band brace's KBS1Z (params/entry_band_brace.py).
# `roof_beam` grades it as 24F-V4 DF, wet (notes/canopy_west_band.md §7). The roof-bearing run
# starts 3/4" in (`TRUSS_DATUM_INSET_FT`), so truss 1 bears its full 1 1/2" on the beam end.
HEADER_SOUTH_Y_FT = PIER_LINE_Y_FT - COLUMN_HALF_FT
HEADER_NORTH_Y_FT = GARAGE_SEAT_Y_FT + COLUMN_HALF_FT
TRUSS_DATUM_INSET_FT = 0.75 / 12
TRUSS_DATUM_Y_FT = HEADER_SOUTH_Y_FT + TRUSS_DATUM_INSET_FT
beam(6, "BM-BW-RW", LANDING_WEST_FT, HEADER_SOUTH_Y_FT,
     LANDING_WEST_FT, HEADER_NORTH_Y_FT, ("PT-BW-CW", "PT-BW-CNW"), HEADER_TOP_FT,
     HEADER_SIZE, "BEAM_GLULAM_TREATED",
     roof_bearing_insets=(ft(TRUSS_DATUM_INSET_FT), ft(0)))
# What the east header lands on is EAST_POST_SYSTEM (params/east_posts.py); its tag and uid
# never change.
beam(7, "BM-BW-RE", ROOF_COLUMN_EAST_X_FT, HEADER_SOUTH_Y_FT,
     ROOF_COLUMN_EAST_X_FT, HEADER_NORTH_Y_FT, ("PT-BW-RE", "PT-BW-RNE"), HEADER_TOP_FT,
     HEADER_SIZE, "BEAM_GLULAM_TREATED",
     roof_bearing_insets=(ft(TRUSS_DATUM_INSET_FT), ft(0)))

# BM-BW-SCSILL carries W-BW-SCREEN (no joist under it) between the two columns: 39.2 plf, 57.3
# with the band (notes/north_entry_piers.md §2). It sits in the joist plane, not the seat plane,
# which would cross the seats' west ends at one elevation (`structural.member_interference`), and
# doubles as the deck's west rim since the joist field starts 3 3/4" east of this line.
#
# It hangs off both columns (LUS28Z, CN-BW-HGR-SCS-* in params/breezeway.py): the 6x6 (5 1/2")
# fully shadows the 3" seat beam on the same centreline, so authored to the column centres it
# buried 2 3/4" in each 6x6, and shortened to the faces it stops 1 1/4" clear of its own bearing
# (`test_analytical_graph`). Both columns carry `within_wall`, so the panel's plates are cut at the
# same faces.
#
# `bearing_refs` follows the hanger to the columns, the opposite of the seat beams: this sill's
# load is taken by the column, which stands on its own pier through `supported_by`.
beam(10, "BM-BW-SCSILL", SCREEN_AXIS_X_FT, PIER_LINE_Y_FT + COLUMN_HALF_FT,
     SCREEN_AXIS_X_FT, GARAGE_SEAT_Y_FT - COLUMN_HALF_FT,
     ("PT-BW-CW", "PT-BW-CNW"), DECK_JOIST_TOP_FT, "2x8")

# --- piers, pedestals and columns -------------------------------------------------------
#
# Shaft slenderness exceeds ACI 318-19 §6.2.5's non-sway floor of 22 and is computed, not
# neglected; it is a false alarm. The pad area is what governs (notes/north_entry_piers.md).
#
# These are `Pad`, not `Footing`: `structural.deck_footing_size` (R507.3.1) reads a post's roof
# share as deck currency, `(DECK_DEAD_LOAD_PSF + design snow) / DECK_TOTAL_LOAD_PSF` (1.674 here;
# `engineering/pier_basis.design_roof_snow_psf`), via `checks/structural/deck.py::
# _roof_borne_posts`. PT-BW-RE/-RNE carry only a roof header, so no deck's post list held them.
# The pour is a SQUARE of side `width` either way (`_pad_outline`); `bottom_elevation` sets depth.
#
# A cage is authored twice and the two must agree: `vertical_reinforcement` is drawing text,
# `reinforcement` is what `reinforcement_takeoff` bills (the string alone bills no steel).
# ENTRY_PIER_CAGE is the court columns' 8" cage, a fabricated part. Coating belongs to the pour
# (EXPOSED_MIX `bar_coating`), so none is stated per bar.
ENTRY_PIER_CAGE = ReinforcementSpec(
    bars=(
        BarSpec(role="vertical", bar=5, count=4),
        BarSpec(role="ties", bar=3, spacing=inch(10.0)),
    ),
    # 2" cover, not 3": the pad dowels lap one bar inside the verticals, and at 3" cover they stand
    # 2.39" apart, under ACI 318-19 Table 25.4.3.2's 6 db, so psi_r goes 1.0 -> 1.6 and ldh
    # 7.11 -> 11.38" against the 9" a 12" pad holds (balcony_moment_columns.md §14,
    # north_entry_piers.md §6).
    cover=inch(2.0),
    lap_class="B",
    source='8" cage, (4) #5 + #3 rings @ 10", one of ten house-wide; notes/north_entry_piers.md §6 — the ACI 318-19 §10.6.1.1 1% floor, four bars per §10.7.3.1(b)',
)

#: The piers that are a lateral system (fixed-base moment columns, `deck_post`'s bending
#: records) take the cage plus a #5 dowel at each vertical into their pad (decision #75 D6).
ENTRY_MOMENT_CAGE = ReinforcementSpec(
    bars=(
        BarSpec(role="vertical", bar=5, count=4),
        BarSpec(role="ties", bar=3, spacing=inch(10.0)),
        BarSpec(role="dowels", bar=5, note="one per vertical, hooked into the pad"),
    ),
    cover=inch(2.0),
    lap_class="B",
    source="ENTRY_PIER_CAGE plus its base dowels; notes/north_entry_piers.md §6",
)

#: (6) #5 in the 14" round: (4) #5 is 0.806% of the gross, under ACI 318-19 §10.6.1.1's 1%; six
#: give 1.21%. Each dowel laps BESIDE its vertical on the bar circle, so the hooks keep
#: 4.31" >= 6 db (inside, 3.69" would take psi_r to 1.6). notes/north_entry_piers.md §13b.
ENTRY_PIER_CAGE_14 = ReinforcementSpec(
    bars=(
        BarSpec(role="vertical", bar=5, count=6),
        BarSpec(role="ties", bar=3, spacing=inch(10.0)),
    ),
    cover=inch(2.0),
    lap_class="B",
    source='10" cage, (6) #5 + #3 rings @ 10", the 14" rounds; notes/north_entry_piers.md §13b — ACI 318-19 §10.6.1.1 1% on the gross area',
)
ENTRY_MOMENT_CAGE_14 = ReinforcementSpec(
    bars=(
        BarSpec(role="vertical", bar=5, count=6),
        BarSpec(role="ties", bar=3, spacing=inch(10.0)),
        BarSpec(role="dowels", bar=5,
                note="one per vertical, lapped beside it on the bar circle, hooked into the pad"),
    ),
    cover=inch(2.0),
    lap_class="B",
    source="ENTRY_PIER_CAGE_14 plus its base dowels; notes/north_entry_piers.md §13b",
)

#: Pier size -> (plain cage, moment cage, drawing text). Both spellings, always.
PIER_CAGES = {
    "12 round": (ENTRY_PIER_CAGE, ENTRY_MOMENT_CAGE, '(4) #5 vertical, #3 ties @ 10" o.c.'),
    "14 round": (ENTRY_PIER_CAGE_14, ENTRY_MOMENT_CAGE_14, '(6) #5 vertical, #3 ties @ 10" o.c.'),
}
#: Moment piers (fixed-base columns: `pier_basis._base_moments`, `structural.lateral_racking`) take
#: the moment cage and a 12" pad: the four landing piers plus the east posts' set. Tops are
#: unchanged and only bottoms drop, so `column_base`'s embedment (grade to PAD TOP) holds.
_MOMENT_PIERS = frozenset({"PT-BW-W", "PT-BW-E", "PT-BW-GW", "PT-BW-GE"}
                          | moment_piers(EAST_POST_SYSTEM))
#: 12" under every moment pier: the #5 dowel foot rests at 3" bottom cover, so embedment is
#: thickness - 3" (9" at 12" vs ldh 7.11", ACI 318-19 §25.4.3.1). Tops stay put: pier heights, the
#: hydrant's 1 7/16" over the house-side tops, the garage strip's aligned top.
MOMENT_PAD_DEPTH_FT = 1.0

#: The east supports are a switch (`EAST_POST_SYSTEM`). Default pinned KDAT piers have pads on the
#: plane each side already has: PD-BW-RE on the house-side `FOOTING_TOP_FT` beside FT-B-N1..-N4,
#: PD-BW-RNE on the garage strip's own plane. The deep -10'-2" plane survives only in
#: `_EAST_VARIANTS["cast"]` (params/east_posts.py), with two sequencing notes: house side, the pad
#: bears below FT-B-N1..-N4 close beside them (dig and cast it BEFORE the strip bears); garage
#: side, PD-BW-RNE laps under FT-GF-S1/-S3 and sits well below (pad first, stone compacted
#: round it).

#: No column here claims IBC §1806.3.4: `column_base` basis 4 counts the doweled, monolithic pad as
#: part of the pole (embedment to the pad bottom), and all pass Eq. 18-1 on Table 1806.2's S1
#: (notes/entry_column_base_fixity.md 6e).

PIERS = []
def _pad_outline(x_ft, y_ft, side_in, along_in=None):
    """A square (or rectangle) pad footprint centred on the pier, in plan.

    ** THE SHAPE IS THE SAME SHAPE THE FOOTING ALREADY DREW. ** ``resolve/envelope.py``
    resolves a post-hosted ``Footing`` as a SQUARE of side ``width`` — the round the tag
    suggests was never what got built or billed — so authoring the square here changes no
    concrete volume at all. What changes is the credited BEARING AREA: ``deck_footing_size``
    stops reading the inscribed circle and reads the square, 3.14 -> 4.00 ft² on a 24".

    ``along_in`` (the y dimension) defaults to ``side_in`` and exists for the one thing a
    ``Pad`` can do that a ``Footing`` cannot: be a rectangle. ``structural.concrete_interference``
    scopes every Pad but only a wall-less Footing, so a lap that was invisible while these
    were Footings becomes a FAIL the moment they are Pads — and pulling a pad clear of a
    strip footing in one direction is what a rectangle is for.
    """
    half_x, half_y = inch(side_in) / 2.0, inch(along_in or side_in) / 2.0
    return (pt(ft(x_ft) - half_x, ft(y_ft) - half_y),
            pt(ft(x_ft) + half_x, ft(y_ft) - half_y),
            pt(ft(x_ft) + half_x, ft(y_ft) + half_y),
            pt(ft(x_ft) - half_x, ft(y_ft) + half_y))


#: What ties each head to its beam (`params/column_heads.py`). The west pair carry a 6x6
#: canopy column on a cast-in CBSTQ66Z-SDS2 and hang the seat beam off it; the rest take the
#: HETA20Z pair.
_HEAD_CONNECTORS = {"PT-BW-W": CBSTQ66Z_HEAD, "PT-BW-GW": CBSTQ66Z_HEAD,
                    "PT-BW-E": HETA20Z_PAIR_HEAD, "PT-BW-GE": HETA20Z_PAIR_HEAD}

#: 14" under a cast-in CBSTQ: ESR-3050 Table 2 fn. 4 wants 3" of side cover to the embedded straps
#: (a 12" round gives 2 3/4"), and the seat beam gets 4 1/4" of bearing instead of 3 1/4"
#: (notes/canopy_west_band.md §5). Its cage is (6) #5 (`ENTRY_PIER_CAGE_14`).
_PIER_SIZE = {"PT-BW-W": "14 round", "PT-BW-GW": "14 round"}


def _cage(tag):
    return PIER_CAGES[_PIER_SIZE.get(tag, "12 round")]

FOOTINGS = []
#: House-side pads are 30" x 18" (E-W x N-S). `FT-B-N1`..`-N4`, the basement's north strip footing
#: on this plane, reach y=36'-8 1/8", and a 24" square reached 2 1/8" into them
#: (`concrete_interference` scopes every `Pad`); 18" clears by 1 1/16" and 30" keeps the area
#: (3.75 ft² against PT-BW-W's 2.48 required). One size for all three: three pad sizes are three
#: rows in S-100's FOUNDATION SCHEDULE (`test_schedule_columns.py`), and one size is one form.
_PAD_WIDE_IN = 30.0
_PAD_DEPTH_IN = 18.0

for _uid, _tag, _x, _height in (
    ("BWPT01AAAA", "PT-BW-W", LANDING_WEST_FT, PIER_TOP_FT - FOOTING_TOP_FT),
    ("BWPT02AAAA", "PT-BW-E", LANDING_EAST_FT, PIER_TOP_FT - FOOTING_TOP_FT),
):
    PIERS.append(Post(
        uid=_uid, tag=_tag, position=pt(ft(_x), ft(PIER_LINE_Y_FT)),
        head_connector=_HEAD_CONNECTORS[_tag],
        # `"12 round"`. Never a nominal form like "12x12": that matches `_RE_NOMINAL` in
        # resolve/framing/profiles.py, misses LUMBER_ACTUAL and silently resolves to 1.5x5.5.
        size=_PIER_SIZE.get(_tag, "12 round"), height=ft(_height),
        assembly=pier_assembly(_PIER_SIZE.get(_tag, "12 round")),
        # (4) #5 clears ACI 318-19 §10.6.1.1's 1% floor on A_g=113.10 in2 and is §10.7.3.1(b)'s
        # four-bar minimum; #3 ties at the §25.7.2.2 maximum, 10". The floor is load-independent.
        # Galvanized house-wide (EXPOSED_MIX, A767). The 14" rounds take (6) #5 (`PIER_CAGES`).
        vertical_reinforcement=_cage(_tag)[2],
        reinforcement=_cage(_tag)[1 if _tag in _MOMENT_PIERS else 0],
        supported_by=f"PD-BW-{_tag.split('-')[-1]}"))
    FOOTINGS.append(Pad(
        uid=f"BWF{_uid[4:8]}AA", tag=f"PD-BW-{_tag.split('-')[-1]}",
        outline=_pad_outline(_x, PIER_LINE_Y_FT, _PAD_WIDE_IN, _PAD_DEPTH_IN),
        thickness=ft(MOMENT_PAD_DEPTH_FT if _tag in _MOMENT_PIERS else FOOTING_DEPTH_FT),
        assembly="PIER_BASE_12",
        # PT-BW-W/-E keep FOOTING_TOP_FT: the hydrant clearance at PIER_BOTTOM_FT is written
        # against that plane. Only the moment pads' bottoms move.
        bottom_elevation=ft(FOOTING_TOP_FT - MOMENT_PAD_DEPTH_FT if _tag in _MOMENT_PIERS
                            else PIER_BOTTOM_FT)))

# Garage side: two piers of their own, at the same elevation and span as the house side, so
# `structural.deck_beam_span` grades both seat beams alike. Pad width is per pier: PT-BW-GE carries
# landing load only (18"); PT-BW-GW and PT-BW-RNE also carry a canopy column and take 2'-0".
#
# These stop at the garage strip footing's plane (-7'-0"), cast with the garage foundation in the
# same excavation and visit; the house-side piers reach deeper only because the basement
# excavation is already open. The 2'-0" pads reach under `FT-GF-S1`/`-S3` in plan on that same
# plane and meet them edge to edge. The strips are consolidated crushed stone (R403.5), so these
# pads are the only concrete in the hole. `PR-G-HYDRANT-CW` (invert -8'-10") passes beneath;
# `mep.footing_clearance` grades it.
#: The garage piers declare no pour (`Pad.cast_with`): the `FT-GF-*` strips are consolidated crushed
#: stone (R403.5, params/foundations.py) and nothing is cast monolithically with stone. The stone
#: is placed round the pad in R403.4.1's 8" lifts, so there is no cold joint or interface steel.
#: `concrete_interference` drops non-concrete footings by material, and
#: `engineering/spread_base.pours_for` and `column_base` refuse a named pour that is not concrete
#: (notes/entry_column_base_fixity.md 6f).
GARAGE_FOOTING_THICKNESS_FT = 8 / 12   # the garage strip's own 8", so the two tops align
GARAGE_PIER_BOTTOM_FT = -7.0
GARAGE_FOOTING_TOP_FT = GARAGE_PIER_BOTTOM_FT + GARAGE_FOOTING_THICKNESS_FT
PEDESTALS = []
for _uid, _tag, _x, _pad_in, _top in (
    ("BWPT05AAAA", "PT-BW-GW", LANDING_WEST_FT, 24.0, PIER_TOP_FT),
    ("BWPT06AAAA", "PT-BW-GE", LANDING_EAST_FT, 18.0, PIER_TOP_FT),
):
    PEDESTALS.append(Post(
        uid=_uid, tag=_tag, position=pt(ft(_x), ft(GARAGE_SEAT_Y_FT)),
        size=_PIER_SIZE.get(_tag, "12 round"),
        head_connector=_HEAD_CONNECTORS[_tag],
        height=ft(_top - GARAGE_FOOTING_TOP_FT),
        assembly=pier_assembly(_PIER_SIZE.get(_tag, "12 round")),
        vertical_reinforcement=_cage(_tag)[2],
        reinforcement=_cage(_tag)[1 if _tag in _MOMENT_PIERS else 0],
        supported_by=f"PD-BW-{_tag.split('-')[-1]}"))
    # These lap the garage strip footing `FT-GF-S1`/`-S3` and cannot be pulled clear: the pier line
    # is south of that footing's face and the column overhangs any pad that stops at it. The strip
    # is stone, so the lap needs no declaration (see above).
    FOOTINGS.append(Pad(
        uid=f"BWFG{_uid[4:6]}AAAA"[:10], tag=f"PD-BW-{_tag.split('-')[-1]}",
        outline=_pad_outline(_x, GARAGE_SEAT_Y_FT, _pad_in),
        thickness=ft(MOMENT_PAD_DEPTH_FT if _tag in _MOMENT_PIERS
                     else GARAGE_FOOTING_THICKNESS_FT),
        assembly="PIER_BASE_12",
        # Moment pads keep the strip's top; their bottom is 4" below its plane (-7'-4").
        bottom_elevation=ft(GARAGE_FOOTING_TOP_FT - MOMENT_PAD_DEPTH_FT
                            if _tag in _MOMENT_PIERS else GARAGE_PIER_BOTTOM_FT)))

# The two west roof columns: 6x6 KDAT on cast-in CBSTQ66Z-SDS2 bases, with ACE6Z end caps at the
# header (k*lu/d under 17; NDS §3.7.1.4's limit is 50). `engineering/wood_roof_post` grades them,
# `lateral_system` their chord role. Uplift does not govern (notes/north_entry_piers.md §4).
COLUMN_HEIGHT_FT = HEADER_SOFFIT_FT - PIER_TOP_FT
FULL_HEIGHT_COLUMNS = full_height_columns(EAST_POST_SYSTEM)

# East line from one factory (params/east_posts.py); the pads keep their tags and uids in every
# variant, on the house-side and garage planes their neighbours use.
_EAST_POSTS, _EAST_PIERS, _EAST_PADS = east_supports(
    EAST_POST_SYSTEM, x_ft=ROOF_COLUMN_EAST_X_FT,
    stations={"RE": ("BWPT03AAAA", PIER_LINE_Y_FT), "RNE": ("BWPT04AAAA", GARAGE_SEAT_Y_FT)},
    header_soffit_ft=HEADER_SOFFIT_FT, pack_ft=STANDOFF_PACK_IN / 12,
    cages=PIER_CAGES,
    house_pad=("BWF03AAAA",
               lambda y: _pad_outline(ROOF_COLUMN_EAST_X_FT, y, _PAD_WIDE_IN, _PAD_DEPTH_IN),
               FOOTING_TOP_FT, MOMENT_PAD_DEPTH_FT),
    garage_pad=("BWFG04AAAA", lambda y: _pad_outline(ROOF_COLUMN_EAST_X_FT, y, 24.0),
                GARAGE_FOOTING_TOP_FT, MOMENT_PAD_DEPTH_FT))
FOOTINGS.extend(_EAST_PADS)
ROOF_COLUMNS = [
    # Both stand ON the screen panel's line, so its plates and studs are cut round them and the 2x4
    # infill butts the column faces (`Post.within_wall`). Geometry only: each still stands on its
    # own cast-in CBSTQ66Z-SDS2 base over a cast pier.
    Post(uid=_uid, tag=_tag, position=pt(ft(_x), ft(_y)),
         size="6x6", height=ft(COLUMN_HEIGHT_FT), assembly="POST_KDAT", supported_by=_pier,
         within_wall="W-BW-SCREEN")
    for _uid, _tag, _x, _y, _pier in (
        ("BWPT07AAAA", "PT-BW-CW", LANDING_WEST_FT, PIER_LINE_Y_FT, "PT-BW-W"),
        ("BWPT11AAAA", "PT-BW-CNW", LANDING_WEST_FT, GARAGE_SEAT_Y_FT, "PT-BW-GW"),
    )
]

FRAME_ELEMENTS = [*NODES, *BEAMS, *PIERS, *FOOTINGS, *PEDESTALS, *ROOF_COLUMNS,
                  *_EAST_PIERS, *_EAST_POSTS]
