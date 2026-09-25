"""Beam hold-downs, panel fasteners, equipment anchors, shims, pocket-frame kits.

Split out of the former ``library/hardware.py``; see the package docstring.
"""

from __future__ import annotations

from typehaus.hardware.catalog import (
    ROLE_BEAM_HOLD_DOWN,
    ROLE_BEARING_STANDOFF,
    ROLE_DECK_EQUIPMENT_ANCHOR,
    ROLE_EQUIPMENT_PAD_ANCHOR,
    ROLE_EXPOSED_FASTENER_PANEL_SCREW,
    ROLE_GLAZING_PANEL_FASTENER,
    ROLE_KNEE_BRACE,
    ROLE_LEDGER_ANCHOR,
    ROLE_MODELED_CONNECTOR,
    ROLE_POCKET_DOOR_FRAME_KIT,
    ROLE_PV_SEAM_CLAMP,
    ROLE_THROUGH_PANEL_PIPE_STRAP,
    AllowableLoads,
    StructuralHardware,
)
from typehaus.library.hardware._common import _SIMPSON

SS316_HEX_BOLT_38 = StructuralHardware(
    tag="generic-ss316-hex-bolt-38",
    name="3/8 in Type 316 stainless through-bolt with nut and washer",
    role=ROLE_MODELED_CONNECTOR,
    manufacturer="generic",
    model="SS316-BOLT-38",
    source=("Generic 3/8-16 Type 316 stainless hex bolt, nut and washer; length to suit the "
            "joint. Bolt Depot's Type 316 catalog lists the bolt, 3/8-16 nut and washer "
            "separately: boltdepot.com/Hex_bolts_Stainless_steel_316_3_8-16"),
)

KBS_BEAM_HOLD_DOWN = StructuralHardware(
    tag="simpson-kbs1z-strap",
    name="KBS1Z knee-brace / beam strap (ZMAX)",
    role=ROLE_BEAM_HOLD_DOWN,
    manufacturer=_SIMPSON,
    model="KBS1Z",
    source="Simpson Strong-Tie KBS1Z strap (strongtie.com/kbs) — ZMAX galvanized strap "
           "tying a beam to the post it bears on; published for knee braces and for "
           "beam-to-post uplift, which is the joint it is used for here",
    # IAPMO UES ER-280 Table 7 (rev. 04/28/2026), cross-read against Simpson's C-C-2019
    # catalog page, which prints the same rows split by species where the report prints only
    # the DF/SP figures. **The SPF/HF column is recorded**, because that is what this house
    # frames in and it is 14 % below the DF/SP number the report leads with.
    #
    # The KBS1Z is the reason this record matters beyond its current use. It is the only
    # knee-brace connector in the Simpson line with a code-report allowable at all (§3.1.7,
    # Table 7, Figure 7), and its F1 values are published BY BRACE ANGLE with an explicit
    # interpolation rule (footnote 3) — which is exactly the capacity the balcony's braces
    # need and exactly what the APVKB45-6 above does not have.
    #
    # Which row: **connection type 1, two connectors per joint** — equal-width members, one
    # KBS1Z each side of the brace, 12 - 8d each. That is the configuration a 2x brace into a
    # 6x6 post is not (type 2, single connector, 630/510 DF-SP), so the type is recorded in
    # `fasteners` rather than left to be assumed. The uplift/lateral rows below type 2 are
    # the BEAM-to-post use (types 3 and 4) and are a different joint again; the 1,160/1,725
    # pair is what `takeoff/uplift.py` derives this part for today.
    allowable=AllowableLoads(
        uplift_lb=1000.0,        # connection type 3, 4 connectors per joint, SPF/HF
        lateral_f2_lb=1480.0,    # "Lateral", connection type 3, 4 connectors, SPF/HF
        load_duration_factor=1.6,
        species="SPF/HF — the column recorded; DF/SP is 1,160 uplift / 1,725 lateral "
                "for the same rows",
        fasteners="12 - 8d (0.131 x 2-1/2 in) per connector, connection type 3 "
                  "(continuous beam-to-post, four connectors per joint). SD9x1-1/2 screws "
                  "substitute with no load reduction (ER-280 Table 7 footnote 1)",
        citation=("IAPMO UES ER-280 rev. 04/28/2026 §3.1.7 and Table 7, read 2026-08-30, "
                  "cross-read against Simpson C-C-2019 for the SPF/HF split. This record is "
                  "the BEAM-to-post rows; the knee-brace F1 rows are on "
                  "KBS1Z_KNEE_BRACE. Footnote 2: already increased for wind/earthquake at "
                  "C_D 1.60, no further increase allowed"),
    ),
)

# The same part, serving the knee-brace role, and carrying a DIFFERENT row of the same table.
# Two records rather than one because ``hardware_for_role`` holds exactly one item per role
# and because the load that matters is not the same number: ER-280 Table 7 tabulates the
# KBS1Z by CONNECTION TYPE, and a beam-to-post cap (types 3 and 4) and a knee brace (types 1
# and 2) read different rows. Collapsing them would have handed the balcony's braces the
# 1,010 lbf of the two-connector equal-width row when what they get is 540.
#
# **Connection type 2, and that is the one judgement in this record.** Type 1 is "for
# equal-width members, install (2) KBS1Z on each end of brace"; type 2 is "for 2x knee brace,
# install single KBS1Z on each end". These braces are 2x6 diagonals into 6x6 posts — not
# equal width — so type 2 governs, at 540 lbf SPF/HF against type 1's 1,010. Taking the
# larger number would have been an 87 % overstatement of capacity on the only lateral
# elements this structure has.
KBS1Z_KNEE_BRACE = StructuralHardware(
    tag="simpson-kbs1z-knee-brace",
    name="KBS1Z knee-brace stabilizer (ZMAX), one per brace end",
    role=ROLE_KNEE_BRACE,
    manufacturer=_SIMPSON,
    model="KBS1Z",
    source="Simpson Strong-Tie KBS1Z knee-brace stabilizer (strongtie.com/kbs) — the only "
           "knee-brace connector in this catalog with a code-report allowable load, and the "
           "one Simpson publish by brace angle. Factory-formed at 45 degrees with a "
           "one-time field bend for other angles",
    allowable=AllowableLoads(
        lateral_f1_lb=540.0,     # connection type 2, single connector, 45 deg, SPF/HF
        load_duration_factor=1.6,
        species="SPF/HF — the column recorded; DF/SP is 630 lbf for the same row",
        fasteners="12 - 8d x 1-1/2 in per connector, one connector at each end of the "
                  "brace (connection type 2, a 2x knee brace into a wider member). "
                  "SD9x1-1/2 screws substitute with no load reduction",
        citation=("IAPMO UES ER-280 rev. 04/28/2026 Table 7, connection type 2, read "
                  "2026-08-30; SPF/HF split from Simpson C-C-2019. F1 by brace angle: "
                  "540 lbf at 45 deg, 440 lbf at 30 or 60 deg (SPF/HF, in-service moisture "
                  "<= 19 %; the > 19 % columns are 385 and 330). Footnote 3 permits "
                  "interpolation between the two angles. Footnote 2: values already include "
                  "C_D = 1.60 for wind, no further increase allowed"),
    ),
)

# The screw an exposed-fastener wall panel is hung on. Driven through the panel flat (not
# the rib) into the support behind, it is the ONLY penetration in the water plane, so the
# gasket — not the steel — sets the service life of the wall.
#
# 316, not 304: this is a lakeside/road-salt exposure, and a stainless screw head that
# streaks or pits is both the leak path and the thing you look at from the driveway.
#
# Length arithmetic, so the choice is auditable: 1-1/2" through a ~0.02" 26 ga panel into
# the flat 1.5" KDAT outer girt leaves ~1.4" of embedment — the full thickness of the
# nailer, with the tip breaking through into the blind 0.5" vent gap behind it rather than
# stopping in the sheathing. Longer is not better here: a screw that reaches the WRB adds a
# second penetration in a plane that is meant to stay unbroken.
EXPOSED_FASTENER_PANEL_SCREW = StructuralHardware(
    tag="simpson-t09150hwam-panel-screw",
    name="#9 x 1-1/2\" 316 stainless metal-panel screw, EPDM washer",
    role=ROLE_EXPOSED_FASTENER_PANEL_SCREW,
    manufacturer=_SIMPSON,
    model="T09150HWAM",
    part_number_by_length_in={1.5: "T09150HWAM"},
    source="Simpson Strong-Tie T09150HWAM (strongtie.com) — #9 x 1-1/2\" Type 316 stainless "
           "metal-panel screw, hex washer head with a bonded EPDM sealing washer, for "
           "through-fastening metal panel to a wood support",
)

# The strap that carries a round pipe on an exposed-fastener panel. The CanDuit ring above
# cannot serve here: it mounts on a seam clamp by its M8 shaft (``requires_role``), and a
# PBR wall has no seam to clamp. This one reaches the building the other way — two panel
# screws straight through the panel flat into the girt — so it declares no ``requires_role``
# and brings its own fixings instead of a bracket.
#
# The standoff block is what makes it legal on a ribbed panel: without it the strap would
# bear on the rib crowns and either crush them or hold the pipe off the wall unevenly.
THROUGH_PANEL_PIPE_STRAP = StructuralHardware(
    tag="through-panel-standoff-pipe-strap",
    name="316 stainless two-hole pipe strap on standoff block",
    role=ROLE_THROUGH_PANEL_PIPE_STRAP,
    manufacturer="generic",
    model="SS316-STANDOFF-STRAP",
    source="generic Type 316 stainless two-hole pipe strap on a moulded standoff block, "
           "sized on pipe OUTER diameter the way the CanDuit ring is; fixed with two "
           "T09150HWAM gasketed panel screws per point. No single manufacturer system is "
           "specified, so this record is deliberately generic",
)

# Multiwall polycarbonate is fastened through oversize holes so the sheet can move: the
# washer seals, the screw does not clamp. Stainless because the fastener sits in the wet
# zone of an exterior roof for the life of the sheet.
POLY_PANEL_FASTENER = StructuralHardware(
    tag="stainless-gasketed-panel-screw",
    name="#12 stainless gasketed panel screw with EPDM-bonded washer",
    role=ROLE_GLAZING_PANEL_FASTENER,
    manufacturer="generic",
    model="SS-GASKET-12",
    source="generic 304 stainless #12 hex-head panel screw with a bonded EPDM sealing "
           "washer, the standard multiwall-polycarbonate fixing; no single manufacturer "
           "system is specified, so this record is deliberately generic",
)

# The balcony heat-pump stands' hold-down. THIS IS THE ONE FASTENER IN THIS
# FILE THAT IS MEANT TO PIERCE A WATERPROOF PLANE, and every part of the spec is about that:
#
# * **3/8" x 4", so it reaches.** Wahoo's own AridDek guardrail detail is a 3/8" lag through
#   the deck board into timber blocking below, which is the precedent this borrows — the
#   plank is 1 1/2", leaving ~2 1/2" of thread in the 2x8 blocking, well past the ~100-150 lb
#   of wind uplift a condenser at +10' develops.
# * **316 stainless, not 304 and not galvanised.** It passes through copper-treated KDAT
#   blocking and lands under an aluminium stand on an aluminium plank. Plain or galvanised
#   steel in MCA-treated wood is the corrosion case AWC DCA6 warns about outright.
# * **Bonded EPDM washer, and butyl under the base plate.** The washer seals the shank at the
#   plank; the butyl seals the plate to the plank. Neither alone is the detail — a sealed
#   surface with an unsealed hole is how this joint fails.
#
# It is NOT a ``post_base``: a post base is selected by the post section, and this is selected
# by the seal and the alloy. Sharing the role would also have made
# ``hardware_for_role(ROLE_POST_BASE)`` ambiguous.
DECK_EQUIPMENT_ANCHOR = StructuralHardware(
    tag="stainless-through-deck-equipment-anchor",
    name="3/8 in x 4 in 316 stainless hex lag, 1 in EPDM-bonded washer, through-deck",
    role=ROLE_DECK_EQUIPMENT_ANCHOR,
    manufacturer="generic",
    model="SS316-LAG-38x4-EPDM",
    source="generic 316 stainless 3/8 in x 4 in hex lag screw with a bonded EPDM sealing "
           "washer; the fastener in Wahoo's own AridDek guardrail-post detail is a 3/8 in "
           "lag through the deck board into added timber blocking, and this is that "
           "connection made stainless for a copper-treated host — no single manufacturer "
           "system is specified, so this record is deliberately generic. INSTALLATION is "
           "most of what this part is: a 1/4 in pilot through the plank and the full depth "
           "of the blocking, the pilot wetted with sealant before the lag is driven, butyl "
           "under the base plate, and the washer seated but not crushed — a flattened EPDM "
           "washer has stopped sealing. 1 1/2 in of plank leaves ~2 1/2 in of thread in the "
           "2x8 blocking",
)

# The shim pack under a wood beam soffit where it lands on a pour. Modelled as a part since
# 2026-09-03; before that it existed only as prose inside SUNKEN_GARDEN_COLUMN_12.source and
# PIER_CONCRETE_12.source — a real purchased item at a real joint, with nothing in the BOM,
# nothing in 3D and nothing a reviewer could click.
#
# * **It holds a GAP, and the gap is the point.** A beam sitting flat on a wash ponds against
#   its own end grain; the gap drains and lets both faces dry. 1/2"-1" is AITC/WoodWorks'
#   range for exposed timber on concrete and the range the column tops are cast to, so the
#   pack is shimmed to suit rather than being one thickness. FPInnovations' durability
#   hierarchy is the reason it is a gap and not a membrane: drain and dry the joint before
#   trying to seal it, and a barrier that can hold water is worse than the air it replaced.
# * **NO CODE SECTION REQUIRES THIS PART, and the record should not pretend one does.** This
#   said "IRC R317.1.4 wants a wood member on concrete held clear of it" until 2026-09-12 and
#   that is not what R317.1.4 says: it governs wood COLUMNS, and its 1"/6"/8" projections are
#   exceptions that RELIEVE the treatment requirement rather than impose a clearance.
#   R317.1 item (2) needs a foundation wall and less than 8" to grade; R317.1.2 is embedment,
#   not bearing. A treated beam on a concrete column top satisfies R317 with no barrier and
#   no standoff. This is a durability choice on top of the code. (The R317.1.4 citation on
#   ABU66SS above is a different joint and is correct — that one IS a wood column on
#   concrete.) FPInnovations bounds the wood-on-concrete wicking concern to ~150 mm above
#   soil, and published equilibrium capillary rise in concrete is 100-480 mm — bounded by
#   evaporation, not by suction, which is why a taller column does not pull further. Nothing
#   this part sits on is within reach of that: catlin's north-entry pier tops stand 18 1/2"
#   above grade, its two full-height canopy columns 9'-2 3/4", and the garden's porch columns
#   rise 10'-0 15/16" out of the court floor. What the gap IS aimed at is rain standing on the
#   pour, and end-grain uptake where a beam END lands there rather than crossing it.
# * **NO GROUT ISLAND under it.** An exposed non-shrink cementitious island is a 10-20 year
#   element carrying a 100-year member, and it re-wets the soffit it was meant to lift. Where
#   a levelling bed is unavoidable it is EPOXY grout confined under the plate — that sentence
#   used to live in an assembly ``source`` and belongs on the part.
# * **316 stainless, or HDG with an isolator.** These sit under copper-treated KDAT and under
#   treated glulam, both of which eat plain steel. Where the pack meets a zinc-coated tie
#   (HETA20Z strap, HGAM10 gusset) an EPDM or HDPE isolator goes between them.
#
# Deliberately NOT a post base and not a bearing plate: it is selected by the gap and the
# alloy, not by a post section, and ``hardware_for_role`` holds one part per role.
BEARING_STANDOFF_SHIM = StructuralHardware(
    tag="stainless-beam-bearing-standoff-shim",
    name="3-1/2 in square 316 stainless beam standoff shim pack, 1/2 in to 1 in",
    role=ROLE_BEARING_STANDOFF,
    manufacturer="generic",
    model="SS316-SHIM-35",
    source="generic 316 stainless plate shims, 3-1/2 in square, stacked to the 1/2 in-1 in "
           "gap a cast column top is finished to — no manufacturer system is specified, so "
           "this record is deliberately generic, as SS316-LAG-38x4-EPDM and SS316-WEDGE-38x3 "
           "are. INSTALLATION is most of what it is: set on the cast wash under the beam "
           "footprint with NO grout island (epoxy grout confined under the plate if a "
           "levelling bed proves unavoidable, never a cementitious one), an EPDM or HDPE "
           "isolator where the pack meets a zinc-coated tie (HETA20Z strap), and the stack "
           "shimmed so the soffit stands clear of the pour rather than bedded on it. "
           "**Where the beam is "
           "TILTED, the leaves are LAPPED TO THE DRAINAGE SLOPE** — full leaves at the low "
           "edge, progressively short ones toward the high edge — rather than a custom "
           "tapered shim being fabricated: a tapered stainless shim is a laser-cut/CNC "
           "specialist item, and a pack is already a stack of leaves. At catlin\'s balcony "
           "that taper is 1/8\" over the 6\" bearing (0.0227 in/in), over an EPDM isolator "
           "that conforms the rest under load. SJI requires no sloped seat below 3/8 in per "
           "foot and bridge practice taper-shims sloped girders to the nearest 1/16 in, so "
           "this slope is inside the range a conforming pad handles — "
           "houses/catlin/notes/balcony_differential_movement.md §3",
)

# The ground-pad twin of the part above, and a much simpler joint: an equipment stand
# standing on a 4" concrete pad at grade, wedge-anchored into it.
#
# * **3/8" x 3", so it fits the pour.** A 3/8" wedge anchor wants ~1 1/2"-2" of embedment;
#   3" of length leaves that in a 4" slab with the stand's base plate and a nut on top, and
#   does not reach the capillary break under it.
# * **316 stainless, not 304 and not galvanised.** The stand is aluminium, the pad is at
#   grade in a de-iced climate, and the anchor sits in the splash zone the whole winter.
#   316 in aluminium is the same non-couple 316 in an aluminium plank was.
# * **No sealing washer, and that is the difference.** ``DECK_EQUIPMENT_ANCHOR`` is chosen
#   for its seal because it pierces a roof. Nothing is below this one but stone, so it is
#   selected for embedment and alloy alone.
EQUIPMENT_PAD_ANCHOR = StructuralHardware(
    tag="stainless-equipment-pad-wedge-anchor",
    name="3/8 in x 3 in 316 stainless wedge anchor, into a concrete equipment pad",
    role=ROLE_EQUIPMENT_PAD_ANCHOR,
    manufacturer="generic",
    model="SS316-WEDGE-38x3",
    source="generic 316 stainless 3/8 in x 3 in wedge (expansion) anchor for a mechanical "
           "stand's base plate into a 4 in slab-on-grade; no single manufacturer system is "
           "specified, so this record is deliberately generic. INSTALLATION: drill 3/8 in "
           "to depth in cured concrete, blow the hole clean, drive the anchor to the mark "
           "and torque the nut to the manufacturer's value — an under-torqued wedge has not "
           "set and an over-torqued one has spun its cone",
)

# A deck ledger into a cast wall: the porch ledgers on catlin's court walls (2026-09-22).
# Spacing is graded off the Simpson letter authored on the ledger (``Beam.published_span``).
THDSS_LEDGER_ANCHOR = StructuralHardware(
    tag="simpson-thd50600h6ss-ledger-anchor",
    name="Titen HD 1/2 in x 6 in Type 316 stainless screw anchor, deck ledger to concrete",
    role=ROLE_LEDGER_ANCHOR,
    manufacturer=_SIMPSON,
    model="THD50600H6SS",
    source="Simpson Strong-Tie stainless Titen HD (THDSS), Type 316, 1/2 in x 6 in — a 1:1 "
           "replacement for a 1/2 in ledger bolt per engineering letter L-A-THDSSLDGR23. "
           "INSTALLATION: 1/2 in bit, hole 1/2 in deeper than the embedment, blow clean, "
           "drive once (never reinstall); rows 2 in in from the ledger's edges and 3-5 in "
           "apart, staggered; 4-8 in from the ledger's ends; wall at least 6-1/4 in thick",
)

# PV module mounting on the standing seam: the S-5! PVKIT clamp+bracket assembly grips a
# panel rib without penetration and takes the module frame directly (no rails). Distinct
# model string so ``Connector(size="S-5-PVKIT")`` bills this kit, not the plain clamp.
S5_PV_KIT = StructuralHardware(
    tag="s5-pvkit-clamp",
    name="S-5! PVKIT standing-seam PV mounting kit",
    role=ROLE_PV_SEAM_CLAMP,
    manufacturer="S-5!",
    model="S-5-PVKIT",
    source="S-5! PVKIT 2.0 (s-5.com/pvkit) — non-penetrating standing-seam clamp with "
           "integrated module clamp; one kit per module corner support point",
)

# --- door hardware ------------------------------------------------------------------
# The first non-structural family in this catalog, and it earns its place: a pocket door's
# frame kit is the whole reason a pocket is a *product* decision and not a framing one. The
# kit brings the split studs, the head track, the hangers and the leaf guides, and it is
# what caps the leaf width — which is why the two records below are two products, not two
# rows of one ladder. A takeoff that orders the commodity kit for a 4'-0" solid-core leaf
# gets a frame the door will pull off the wall.
#
# Selected by door width through ``fits_nominal`` (inches, as authored on the DoorType).
POCKET_FRAME_KIT_1500PF = StructuralHardware(
    tag="johnson-1500pf-pocket-frame-kit",
    name="Pocket door frame kit, 2x4 wall (commodity, to 36\"/125 lb)",
    role=ROLE_POCKET_DOOR_FRAME_KIT,
    manufacturer="Johnson Hardware",
    # Named for its trade, not its brand: ``cost_codes`` routes ``pocket-frame-*`` to
    # CSI 08 71 00 Door Hardware rather than to the hardware section's rough-carpentry
    # default, and this string is the BOM key that rule matches.
    model="POCKET-FRAME-1500PF",
    fits_nominal=("24", "28", "30", "32", "36"),
    part_number_by_length_in={24: "152068PF", 28: "152468PF", 30: "152668PF",
                              32: "152868PF", 36: "153068PF"},
    source="Johnson Hardware 1500PF series pocket door frame kit "
           "(johnsonhardware.com/1500-series-pocket-door-frame-kits) — all-steel split "
           "studs, 6063T6 extruded aluminium track, 125 lb max per door, 3-1/2\" minimum "
           "wall structure. Door, jambs, drywall and locks not included.",
)

# Past the commodity ladder the frame, the track and the hangers all change. No published
# SKU ladder is recorded here on purpose: the width families are published, the part
# numbers are configured per order, and inventing one would be an estimate wearing a part
# number's clothes.
POCKET_FRAME_KIT_HEAVY = StructuralHardware(
    tag="cavity-sliders-cs-for-wood-pocket-frame",
    name="Pocket door frame, 2x4 wall (heavy duty, to 4'-0\")",
    role=ROLE_POCKET_DOOR_FRAME_KIT,
    manufacturer="Cavity Sliders",
    model="POCKET-FRAME-CS-WOOD",
    fits_nominal=("48",),
    source="Cavity Sliders CS For Wood cavity slider pocket frame, 2x4 stud "
           "(cavitysliders.com/cavislider/cavity-slider-pocket-door-frame/2x4-stud/) — "
           "published to 4'0\" x 8'0\", above the 36\"/125 lb ceiling of the commodity "
           "series.",
)
