# haus: editable
# Catlin assemblies — footings, pier bases and the entry piers.
# Split out of plan/assemblies.py verbatim.
from typehaus import (
    Assembly,
    Layer,
    LayerFunction,
    inch,
)
from library import (
    CONCRETE_BEARING,
)
from .mixes import BURIED_MIX, EXPOSED_MIX


# The 12" round pours at the NORTH ENTRY, and nothing else since 2026-09-10: PT-BW-W/-E on
# the pier line, PT-BW-GW/-GE on the garage-side line, and PT-BW-RE/-RNE, which are the same
# section, cage, mix and pad but do not stop at the bearing plane — they run unbroken to
# BM-BW-RE's soffit as the canopy's east lateral system. SIX, 1.51 cy. What left: PT-SG-COL
# went to SUNKEN_GARDEN_COLUMN_12, and PR-BW-1..4 went with the breezeway. Every one is a
# round cast pour, and `solid_material_ref` already reads "12 round" as concrete for the
# section hatch — but only for the hatch. The assembly is what puts
# `structure_material="concrete"` on the BOM row so the [concrete] price table's material
# guard admits it, which is the difference between the pier billing at ready-mix and the pier
# billing at whatever rate the bare "column" key happened to hold.
# ** THE MIX HERE USED TO BE PROSE, AND THE PROSE DID NOT ADD UP. ** The source string below
# said "4,000 psi ... ACI 318-19 class F2", and ACI Table 19.3.2.1 asks **4,500 psi** of class
# F2. Nothing could see that while the numbers were sentences; `structural.
# concrete_mix_matches_exposure` sees it the moment they are a `ConcreteSpec`, which is what
# that check is for.
#
# Resolved by pouring the set from `EXPOSED_MIX` — F3/C2 at 5,000 — rather than by minting
# a compliant fourth mix at F2/4,500. Two reasons, and the second is the real one:
#   * volume. It was 0.82 CY when the set was five; it is 1.51 CY now. Either way a separate
#     ticket for a yard and a half is a delivery charge and a batching risk to save nothing;
#   * the pier tops stand 18 1/2" out of the ground at an entry that is salted every winter,
#     and PT-BW-RE/-RNE carry on to 9'-2 3/4" above grade. F3/C2 is the honest reading of
#     where they sit; F2 never was.
# That second reason belonged to PT-SG-COL and the sunken garden when this was written, and
# it survived the 2026-09-10 retype because the north entry has the same exposure. The
# argument did not have to be re-made — but it did have to be re-grounded, and this is it.
#
# **This galvanizes their cages**, because `bar_coating` is a property of the pour: ~149 lb of
# #5 and #3 moves from black to A767 in the takeoff. That is the 2026-09-02 owner call (hot-dip
# house-wide) reaching the last exterior bar in the house that black steel was still specified
# for, and it removes the one place where a black cage could ever have been lapped to
# galvanized steel — a dissimilar-metal couple is a corrosion cell, and the cheapest time to
# not have one is before it is detailed.
PIER_CONCRETE_12 = Assembly(
    tag="PIER_CONCRETE_12",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(12.0),
              function=LayerFunction.STRUCTURE, concrete=EXPOSED_MIX),
    ),
    interfaces=(CONCRETE_BEARING,),
    # ** ALL SIX CARRY WOOD, AND NOT ONE OF THEM TAKES A GROUT ISLAND (2026-09-12). **
    # PT-BW-W/-E/-GW/-GE each take a 2-2x8 seat beam across the circle; PT-BW-RE/-RNE take
    # BM-BW-RE's 3-ply 2x12, and its south END lands on PT-BW-RE, the one beam end on a pour
    # here. Six joints, one detail: a >=15 degree top wash with a drip lip, an SS316-SHIM-35
    # stainless shim pack holding the KDAT soffit 1/2"-1" clear so the joint drains and dries
    # (AITC/WoodWorks), and a cast-in HETA20Z pair beside it as the TIE. **The shim
    # pack IS the bearing and the tie is never it** — two parts, two jobs, as
    # params/breezeway.py already states. PT-BW-W and PT-BW-GW take a 6x6's ABU66SS base on
    # the same circle as their seat beam; that base is a wood COLUMN on concrete and
    # IRC R317.1.4 really does reach it, which is the one place in this set that citation fits.
    #
    # The grout island this carried until 2026-09-12 is DELETED, not moved. An exposed
    # non-shrink island is a 10-20 year element, not air-entrained, sitting at the wettest
    # point on the column; the NO GROUT ISLAND paragraph above said so on 2026-09-02 and the
    # SS316-SHIM-35 catalog record has said so since. Retyping PT-SG-COL on 2026-09-10 was
    # read as closing that follow-up and did not: the island rode this assembly to
    # PT-BW-RE/-RNE. If a levelling bed proves unavoidable it is EPOXY grout confined under
    # the standoff plate, never a cementitious island with exposed shoulders.
    #
    # Titen Turbo edge distance is >=3", the same figure SUNKEN_GARDEN_COLUMN_12 carries on
    # the identical 12" round — not Simpson's bare 1-1/2" floor, which is what this said. A
    # 4 1/2" 3-ply centred on a 12" circle leaves 3 3/4" per side and a 3" seat beam leaves
    # 4 1/2", so >=3" costs nothing anywhere in the set. BM-BW-RE and both its columns share
    # the axis ROOF_COLUMN_EAST_X_FT, so that centring is exact, not nominal.
    # (single literal: the editable dialect forbids concatenated strings)
    source="catlin-house 12\" round north-entry piers and columns — cast in a fibre form on a spread pad, stripped to the form line; EXPOSED_MIX, 5,000 psi at w/cm 0.40 with 6% +/-1.5 air and galvanized bar (A767 after fabrication or A1094 stock, named on the order); the cage is a fabricated 8-inch unit, one of ten identical cross-sections house-wide (ACI 318-19 class F3 + C2; the 4,000 psi F2 this once specified did not meet Table 19.3.2.1's 4,500 psi for its own class); PT-BW-RE and PT-BW-RNE run unbroken to BM-BW-RE's soffit and are FIXED at the base, same section and cage; at every joint where wood bears (PT-BW-W/-E/-GW/-GE under the seat beams, PT-BW-RE/-RNE under the header): >=15 degree top wash with a >=1\" drip lip screeded around it, top CAST TO LINE under the beam footprint and NO grout island — tolerance taken in the SS316-SHIM-35 stainless standoff shim pack that holds the KDAT soffit 1/2\"-1\" clear (modeled at CN-BW-STDF-*, and its catalog record carries the detailing), or, if a bed is unavoidable, epoxy grout confined under the standoff plate; beam held down by a pair of HETA20Z embedded anchors cast into the column top, one each beam face, straps nailed with HDG 16d and isolated from the standoff with EPDM or HDPE",
)

# ** ONE TYPE FOR ALL FIVE COURT STRIPS SINCE 2026-09-10, AND THE MERGE FIXED A DEFECT. **
# This was RETAINING_FOOTING_96 (the three retaining strips) and PORCH_FOOTING_84 (the two
# braced porch strips), and the split was justified on width — 96" against 84" — which an
# Assembly does not carry. An assembly is a STACK: a layer of concrete, a thickness, a mix.
# Both stacks were one 12" layer of EXPOSED_MIX, so the two cards said the same thing about
# two footings whose only difference is plan geometry.
#
# ** AND ONE OF THEM SAID IT WRONG. ** PORCH_FOOTING_84 declared 13", from a day when the
# porch strips took an extra inch to keep their undersides level with the retaining strips'
# after the porch bearing rose. All five are 12" in the resolved model and have been for
# revisions; the card was lying to the detailer, and a schedule was the only place anyone
# would have met that 13". Merging removes the lie and the row.
#
# Dropping the width from the tag is deliberate rather than cosmetic: a name stating a
# dimension the type does not carry is the reason there were two of these. It also takes a
# row off the S-100 FOUNDATION SCHEDULE, which is one row from stepping down to 1/8".
COURT_FOOTING_12 = Assembly(
    tag="COURT_FOOTING_12",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(12.0),
              function=LayerFunction.STRUCTURE, concrete=EXPOSED_MIX),
    ),
    source="every strip footing in the sunken-garden court, 1'-0\" deep: the three retaining strips FT-SG-W2/E2/S at 8'-0\" wide, reinforced #6 @ 10\" transverse top and bottom (notes/sunken_garden_court_free_body.md §7), and the two braced porch strips FT-SG-W1/E1 at 7'-0\" wide and plain. One F3+C2 mix throughout: every footing here stands INSIDE the excavation, 8\" under a garden floor itself 9' below site grade, frost-protected by drained NFS stone rather than by depth, and concrete in the freezing zone is F3 concrete however it got protected",
)

FOOTING_20 = Assembly(
    tag="FOOTING_20",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(8.0),
              function=LayerFunction.STRUCTURE, concrete=BURIED_MIX),
    ),
    source="the ordinary 20\" x 8\" cast strip under the house and garage walls (IRC Table R403.1), poured against the bedding prep",
)

# ** THE GARAGE'S NINE, ON STONE RATHER THAN CONCRETE (owner, 2026-09-15). ** 2024 IRC
# R403.5 permits a consolidated crushed-stone footing under a NONRETAINING cast-in-place
# foundation complying with R404.1.3, and the garage stem is one: `unbalanced_fill=ft(0)` is
# authored on it (params/foundations.py) because SL-G-FLOOR's top is at grade on the inside
# and the fill stands level on both faces. MN adopts the 2024 edition in 2027 and this build
# starts after it.
#
# A SEPARATE assembly and not a retype of FOOTING_20, because FOOTING_20 is under every
# FT-B-* strip in the house and those are staying concrete. Same 20" x 8" section, same
# bearing plane at -7'-0"; what changes is the material, and with it the price table row
# (`footing:FOOTING_STONE_20` in [concrete]) and the trade that places it.
#
# No `concrete=` spec, and that is not an omission: there is no mix. The durability
# questions BURIED_MIX answers — f'c, air entrainment, the F-exposure class — are questions
# about cement paste, and this pour has none. What replaces them is
# `Footing.stone: CrushedStoneSpec`, which states R403.4.1's five requirements one field
# each, and `code.R403_5_crushed_stone_footings`, which grades them.

# The 12" cast bases under this house's round piers: the sunken garden's two belled footings
# (PD-SG-COL, PD-SG-FCOL) and the four breezeway pads (PD-BW-1..4). One assembly for both
# because they are one detail at two plan shapes — a plain, unreinforced 12" pour bearing at
# frost depth, which is what puts them on the BURIED mix's F0 rather than the court's F3. The
# bells carry 42" of true cover and the pads bottom at -6'-0"; neither ever freezes, and F0 is
# earned by that and not assumed (see BURIED_MIX above).
#
# These six named no assembly at all until 2026-09-03. That is not a cosmetic gap: with no
# assembly there is no `structure_material`, so `resolve/concrete.concrete_spec_for` returned
# None, every calc fell back to the presumptive 3,000 psi, `structural.concrete_mix_matches_
# exposure` could not see them, and the takeoff could not confirm they were concrete — about
# 6 CY of real pour sitting outside both the durability report and the priced bill.
PIER_BASE_12 = Assembly(
    tag="PIER_BASE_12",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(12.0),
              function=LayerFunction.STRUCTURE, concrete=BURIED_MIX),
    ),
    source="the 12\" plain bases under the round piers — the sunken garden's two belled footings and the four breezeway pads, all bearing at or below frost depth (IRC R403.1.4); unreinforced by design and graded as plain concrete under ACI 318-19 §14.1.4, see notes/sunken_garden_piers.md §5",
)

# FOOTING_20's section on the EXPOSED mix (F3): these strips sit inside the court's frost zone.
FOOTING_EXPOSED_20 = Assembly(
    tag="FOOTING_EXPOSED_20",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(8.0),
              function=LayerFunction.STRUCTURE, concrete=EXPOSED_MIX),
    ),
    source="the 20\" x 8\" plain strip under the four sunken-garden-face walls (FT-B-S1..S4), on the 7\" washed-stone bedding; frost-protected under IRC R403.3 by the horizontal wings FROST_WING_XPS_1IN/2 under the garden slab, EXPOSED_MIX because the strip is inside the frost zone",
)
