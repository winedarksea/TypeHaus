# haus: editable
# Catlin assemblies — the exterior wall family, the rafter plate and the garage wood wall.
# Split out of plan/assemblies.py verbatim.
from typehaus import (
    Assembly,
    CavityFill,
    ControlLayer,
    FramingSpec,
    Layer,
    LayerFunction,
    inch,
)
from library import (
    STUD_BEARING,
    GWB_LINING,
)


# --- exterior wall family -----------------------------------------------------
# One 2x6 exterior wall type for main, second and attic. Storey nuance that is a
# purchasing note rather than a different assembly: the MAIN storey's studs are LSL
# (straightness under the 9' first-floor glazing/cabinet runs); second + attic are
# standard dimensional 2x6 SPF. Same 5.5" depth either way, so one assembly tells
# the truth about the geometry and the source string records the material split.
#
# A SWINBURNE TRUSS WALL, not a rigid-CI wall: cladding stands off on an INTERMITTENT
# WOODEN TRUSS — a 2x4 block flat on the sheathing, a 1/2" plywood tab on the block's
# side, a KDAT 2x4 outrigger on edge lap-screwed to the tab — with closed-cell spray foam
# filling the whole 4" around it. Three consequences:
#   1. NO WRB: ccSPF is air + water + vapour + thermal in one bonded, seamless
#      application, so the foam face IS the water plane. `plan/transitions.py` names it
#      `AIR_WATER_THERMAL`, watched by `advisory.control_continuity`. Bucks go in FIRST,
#      foam sprayed around them.
#   2. Only the TAB crosses the insulation zone, every 40" up every 16" bay — R-38.6
#      against R-36.8. The outrigger's back 2-1/2" is inside the foam and the engine
#      parallel-paths it (conservative 1D reading of a 2D detail).
#   3. Cladding plane sits OUT 1/2" (11.5" total). Walls align on `face("sheathing-ext")`,
#      so nothing interior moves, but `params/roof_trim.py`, `params/breezeway.py` and
#      `plan/wind_clamps.py` measure off the cladding face and move with it.
# See notes/outie_window_truss_detail.md.
#
# LAYOUT_ORIGIN: both framing specs below set ``layout_origin="line"``, which counts the
# 16" module from this wall's *layout line* — the derived chain of collinear, stacked
# walls (``resolve/layout_lines.py``) — instead of from each wall's own start node. Both,
# deliberately: the outriggers are clipped to the studs, so a stud spec on the line and a
# batten spec on the wall would take the rainscreen off its backing.
#
# Deliberately one type for main, second and attic — the south facade alone is eight
# walls on one line (W-M-S1/S2, W-S-S1/S2, W-A-S1..S4), split at tees purely as an
# authoring convenience. ``PLANT_EXT_2X6_HUMID`` sets `layout_origin="line"` too: W-S-S1
# and W-S-W4 are members of the south and west lines, and one wall left on wall-start
# origin puts a jog in a line that is otherwise continuous. See CLAUDE.md, Facade rules.
EXT_2X6 = Assembly(
    tag="EXT_2X6",
    layers=(
        # Four-stud outside corners: the thermal objection APA/BASC raise against a solid
        # corner post does not apply here — the primary insulation is the continuous
        # exterior closed-cell foam OUTBOARD of this layer, so the post itself does not
        # need an insulable void. See houses/catlin/CLAUDE.md's corner section.
        # `double_top_plate=True` is the FramingSpec DEFAULT, stated anyway because it is
        # load-bearing: the roof is 24" o.c. and the second storey's studs stay at 16", so
        # half the rafters land 8" off a stud — an off-stud rafter at 24" delivers ~900 lb
        # into the plate rather than ~600. IRC R602.3.2's 5"-of-a-stud bearing rule does not
        # bite here (its trigger is framing over 16" o.c. *and* bearing studs at 24" o.c.;
        # these are at 16"), and with a double top plate no alignment is required at all —
        # this is the ordinary trusses-at-24-over-studs-at-16 condition, which catlin's own
        # garage already builds. The plate that matters is THIS one, under
        # RAFTER_PLATE's flat 2x6: a 2x6 laid flat has little bending capacity of its
        # own and does not distribute an off-stud reaction; the doubled plate below it does.
        Layer(name="stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x6", sill_gasket=inch(0.0625),
                                  layout_origin="line", corner_style="4-stud",
                                  double_top_plate=True),
              # FIBREGLASS, not mineral wool (owner). See the batt note under
              # EXT_2X6_SWINBURNE below for the whole argument; the short form is
              # that the library `fiberglass` tag's 3.7/in IS the high-density R-21 batt
              # value for a 5-1/2" bay (see the `fiberglass-r19` material comment), so this
              # is the correct 2x6 SKU and not a downgrade to a lofted R-19.
              cavity=CavityFill(material_ref="fiberglass")),
        Layer(name="sheathing", material_ref="struct-1-plywood", thickness=inch(0.5),
              function=LayerFunction.SHEATHING,
              sheet_length=inch(120.0)),  # 4x10: wall + rim above, one sheet
        # BAND A, 0 - 4" off the sheathing. ONE application of continuous ccSPF, crossed
        # only by the BLOCK: three loose 3-1/2" x 3-1/2" x 1-1/2" KDAT offcuts stacked flat
        # on the sheathing over every other stud at every 24" course, 4-1/2" tall so the
        # last 1/2" stands proud of the foam. There is no WRB above it because there is
        # nothing left for one to do — ccSPF is air, water, vapour and thermal in one
        # bonded, seamless application.
        #
        # Sprayed AFTER tilt-up, through the 20-1/2" clear between courses and behind them:
        # the girt stands 1/2" off the foam face, so the applicator reaches the whole plane
        # from outside and no course shadows a pocket. Fillet the foam against the block
        # sides rather than butting it square (BSI-048) — planed lumber shrinks and a square
        # cold joint at a block is where the crack would be — and shave the lift to a gauge
        # 1/2" behind the block's outer face.
        #
        # THE INNER GIRT TIER: a plain SPF girt buried in the foam (bands B/C) sits directly
        # ON the sheathing, giving its screw no thermal break, and costs 10.9% wood in the
        # first 1-1/2" of the foam to hold up nothing but the tier above it — omitted. The
        # foam does not need backing (ESR-4073 §4.4.2 permits 7-1/4" on a vertical surface)
        # and its racking contribution is its bond to the sheathing face, unchanged.
        #
        # THE PRODUCT IS HUNTSMAN HEATLOK HFO HIGH LIFT, ICC-ES ESR-4073. §4.2 permits
        # 6-1/2" PER PASS and the TDS ladder is 6.5" at or below 70 F, 4" at 70-80 F, 3.25"
        # above 80 F — so ONE 4" application holds below 80 F, and substrate temperature on
        # the spray day is the condition, not the 1-1/2"/pass legacy SPFA figure. Heatlok HFO
        # *Pro* is a different product (ESL-1372, 2"/pass) and would make this two lifts.
        #
        # WRB IS NOT IN ESR-4073'S SCOPE. The report does not evaluate water-resistive
        # barrier, and the only ccSPF report found granting one (Icynene ProSeal Eco
        # ESR-3493 §4.6) expired in 2021. This wall has no other water plane, so it is an
        # OPEN alternate-approval item under Minn. R. 1300.0110 on Huntsman's own ASTM E331 /
        # E2178 data for the product bought. See notes/catlin_truss_engineering.md §9.
        #
        # No framing factor is authored here, deliberately, and it is why the card reads
        # high. The blocks are 1.6% of this band's area and they are modelled by
        # `resolve/framing/truss_girts.py`, not by the assembly: a plain INSULATION layer
        # carries no framing factor, and giving this layer one would mean naming KDAT as its
        # material and the foam as its *fill* — which would take the air/water/vapour plane
        # off the layer that actually is it (`plan/transitions.py`, AIR_WATER_THERMAL). So
        # the card says R-26 for this band and notes/catlin_truss_engineering.md §7 states
        # the honest ~R-23.5 with the blocks and the screws in it.
        Layer(name="spray-foam", material_ref="closed-cell-spray-foam", thickness=inch(4.0),
              function=LayerFunction.INSULATION,
              control={ControlLayer.AIR, ControlLayer.WATER,
                       ControlLayer.VAPOR, ControlLayer.THERMAL}),
        # BAND A', 4.0 - 4.5". The block's proud 1/2": the vent gap, and it is CONTINUOUS
        # behind every course now that nothing else stands in it. That continuity is a
        # function of stack depth (6") against foam depth (4") and of nothing else — a girt
        # buried in the foam would interrupt it at every course, which is why the 4-1/2"
        # variant with the girt in the foam was rejected.
        Layer(name="vent-gap", material_ref="air-barrier", thickness=inch(0.5),
              function=LayerFunction.AIRGAP),
        # BAND B, 4.5 - 6.0". THE GIRT: KDAT 2x4 laid flat, horizontal, 24" o.c., standing
        # in free air on the blocks. The cladding nailer, the window mount plane, and the
        # only wood outboard of the sheathing — the block inherits its material, so the two
        # bill on one KDAT row. It is a 3-1/2"-deep horizontal ledge behind the cladding
        # that will wet-cycle for the life of the wall, which is why KDAT and not the vent
        # alone carries it. No fill: the gap behind it is the drainage plane and it vents.
        #
        # `standoff="block"` is the whole selector for `resolve/framing/truss_girts.py`;
        # `layout_origin="line"` puts its blocks on the same unified stud module the
        # facade's studs and windows already sit on. 24" courses against the 16" stud module
        # make the crossing tributary 32" x 24" = 5.33 ft2.
        #
        # ONE 8" FASTENMASTER TIMBERLOK (TLOK08) PER CROSSING, through girt (1-1/2") +
        # block (4-1/2") + sheathing (1/2"), 1-1/2" into the stud. One fastener pass, no
        # nails, and it is the entire load path: the block bears the cladding's gravity in
        # direct compression on the sheathing, so the screw is a pure withdrawal element.
        # Mark the stud line across the girt face as it is laid so the screw is not blind.
        #
        # THE CLAMPED STACK IS 6.0", not 6.5": girt 1-1/2" + block 4-1/2". The sheathing is
        # nailed to the stud, so it sits on the stud's side of the joint and is not one of
        # the members being drawn together. TimberLOK threads 2" (ESR-1078 Table 1A), so 6"
        # of plain shank spans that 6.0" exactly and the thread starts where the stud does;
        # 1-1/2" of it lands in the stud, past ESR-1078's 1.25" minimum embedded thread.
        #
        # THE SDWS22800DB THIS WALL CARRIED UNTIL 2026-09-12 CANNOT DO THAT. Every SDWS22
        # threads 3" whatever its length (IAPMO UES ER-192 Table 7), so at 8" it stands 1"
        # of thread inside the 6.0" stack and jacks the girt off the block instead of
        # pulling it down. Graded as `girt_screw/W-A-N1`; see
        # notes/catlin_truss_engineering.md §3.
        #
        # `course_offset=inch(0)` is the swept phase for the 24" module, not a default left
        # in place: the whole 1/8" sweep from -16" to +8" was run against the openings, and
        # zero is the winner — 13 opening edges land exactly on a course line and 30 sit in
        # the 7" shadow of one. At zero no bay exceeds 24.00" anywhere.
        #
        # The phase IS the authoring rule for a new opening, and it flipped with the sign:
        # a course BOTTOM now lands on the framing-base module, so put the HEAD on a 24"
        # multiple above the sole plate, or the SILL 3-1/2" above one. It was the mirror of
        # that at -3.5". See houses/catlin/CLAUDE.md, Facade rules.
        Layer(name="outer-girt", material_ref="kdat", thickness=inch(1.5),
              function=LayerFunction.FURRING,
              framing=FramingSpec(member="2x4", direction="horizontal", laid="flat",
                                  spacing=inch(24), layout_origin="line",
                                  course_datum="framing-base", course_offset=inch(0),
                                  standoff="block",
                                  standoff_fastener="FastenMaster TimberLOK 8\" TLOK08, ESR-1078",
                                  standoff_fastener_part="TLOK08",
                                  standoff_fastener_diameter_in=0.189,
                                  standoff_fastener_length_in=8.0,
                                  standoff_fastener_thread_in=2.0,
                                  standoff_fastener_withdrawal_lb_per_in=170.0,
                                  standoff_fastener_pull_through_lb=200.0,
                                  standoff_fastener_source="ICC-ES ESR-1078 (reissued 2026-01), Tables 1A (2 in thread), 2 (withdrawal, SPF G 0.42) and 3 (head pull-through, 1-1/2 in side member at SG 0.55); coating for ACQ-D <= 0.40 pcf per 4.1.7 / Table 6")),
        Layer(name="cladding", material_ref="pbr-panel-24", thickness=inch(1.25),
              function=LayerFunction.CLADDING),
    ),
    interfaces=(STUD_BEARING,),
    default_lining=GWB_LINING,
    source="catlin-house ifcplot/catlin_house.py wall siding stack; main-storey studs are LSL, second/attic standard dimensional 2x6",
)

# --- the attic rafter plate -----------------------------------------------------
#
# The attic eave is a 2x6 laid FLAT on the attic subfloor
# over the second-storey wall line, and the rafters birdsmouth onto it. One layer, no
# lining, no sheathing, no cladding: a plate on a deck has no faces to finish, and the
# empty `skin_layers()` is exactly what `resolve/roof_edge.py` and `resolve/envelope.py`
# read to know this bearing element laps the cladding of the wall it `stacks_on` rather
# than carrying a weather skin of its own.
#
# 5.5" of structure is not a coincidence: `deck_rise_m` cuts the birdsmouth as
# structure_depth x pitch, so this depth has to match EXT_2X6's stud layer or the
# seat lands off the wall below. That coupling is why the assembly belongs to the house
# and not to `library/`.
#
# `wall_frame="plate"` is what stops the framing solver treating 1 1/2" of wall as a stud
# wall and framing a top plate inside the bottom plate with negative-length studs between.
#
# **`double_top_plate=False` here is NOT the double plate the 24" o.c. roof needs** — that
# one belongs to the stud wall underneath (EXT_2X6, where it is now stated rather
# than defaulted, with the reasoning). This element is a single flat 2x6 bearing plate lying
# on the attic subfloor; doubling *it* would raise the deck plane, the ridge and every PV
# clamp by 1 1/2" and answer a question nobody asked. The load path is rafter -> this plate
# -> 3/4" subfloor -> the second storey's DOUBLE top plate -> studs at 16" o.c.
RAFTER_PLATE = Assembly(
    tag="RAFTER_PLATE",
    layers=(
        Layer(name="plate", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE,
              # corner_style is inert here — a plate frames no studs to pack a corner
              # with — but it is stated to match EXT_2X6 so the junction solver
              # sees one rule at N-A-NE/NW/SE/SW rather than two that disagree.
              framing=FramingSpec(member="2x6", wall_frame="plate", corner_style="4-stud",
                                  double_top_plate=False, layout_origin="line")),
    ),
    source="2026-08-29 attic redesign: rafter bearing plate laid flat on the attic deck",
)

# --- the Swinburne truss wall, kept one swap away --------------------------------
#
# What EXT_2X6 was before the girt band, verbatim: a 3-piece chiral pack — a 2x4
# flat block on the sheathing, a 1/2" plywood tab, a KDAT 2x4 outrigger stood on edge and
# lap-screwed to the tab, vertical, 16" o.c. — inside 4" of ccSPF. It works. It is fussy to
# build (tab lap-screws that were never even billed, a pack the engine has to slide and
# sometimes drop), and its vertical outriggers give a vertical standing-seam clip no
# horizontal nailer at all, which is why the girts replaced it.
#
# **Referenced by nothing, and that is the point** — like `glazed-green-brick`, it is here so
# the revert is a swap and not an archaeology exercise. To go back: give EXT_2X6 and
# PLANT_EXT_2X6_HUMID this layer tuple, restore `_WALL_OUTBOARD_IN` in params/roof_trim.py
# and `HOUSE_CLADDING_Y_FT` in params/north_entry_frame.py to their 5.5"-proud values, and uncomment
# the corresponding rows in prices.toml. `resolve/framing/truss_frame.py` and its branch of
# the pass never went anywhere: they are selected by `laid="edge"` + vertical, which is
# exactly what this tuple says.
# --- THE STUD-BAY BATT IS FIBREGLASS, NOT MINERAL WOOL -------------------------
#
# An owner cost review swept `mineral-wool` -> `fiberglass` across the house. Mineral wool
# runs 2x fibreglass or more installed ($1.50-2.30 + $0.60-1.15 against $0.45-0.90 +
# $0.45-0.85 per SF), and the two reasons usually given for paying it do not hold in a
# cavity:
#
# 1. **Acoustics.** A cavity batt's job in a stud wall is to damp the cavity resonance, and
#    glass wool and stone wool do that within a point or two of each other at the same
#    thickness. Published STC tables separate assemblies by MASS and DECOUPLING (layer
#    count, resilient channel, staggered or double studs), not by which wool is in the bay.
# 2. **Vapour.** Both materials read 116 perm-in in `library/materials/`. Identical. The
#    swap has no Glaser consequence anywhere in this house.
#
# **Where mineral wool IS kept, and why** — every one of these is a damp, hot or wet case
# the owner accepted, not an oversight the next sweep should finish:
#   * `TUBDECK_INT_2X4` — the tub deck box. The long-standing documented exception.
#   * `SAUNA_2X4`, `SAUNA_LINER_INT_2X6_BRG`, `SAUNA_LINER_ON_GARDEN_FRAMED` — non-
#     combustible and dimensionally stable beside a 10.5 kW heater through repeated
#     180 F / loyly humidity cycling.
#   * `PLANT_EXT_2X6_HUMID`, `PLANT_INT_2X6_BRG_HUMID`, `PLANT_INT_2X4_HUMID` — 75 F / 70 %
#     RH against -15 F. The 0.05-perm liner is the control layer and the bay is dry BY
#     DESIGN; the hydrophobic, non-slumping batt is the insurance if that liner is ever
#     breached. ~446 SF, under $1k, and the owner bought it deliberately.
#   * `_GARDEN_FRAMED_STUD` — SHARED by GARDEN_FRAMED_2X6 and
#     SAUNA_LINER_ON_GARDEN_FRAMED. The sauna half must stay mineral wool per the line
#     above, and forking one Layer constant into two so the walkout half could save
#     $80-112 would put two halves of ONE framed run on two sources of truth. It is also a
#     below-grade court face, which is a damp case in its own right. Kept whole.
#
# **What the swap costs thermally: about 1 point of whole-wall R, and the target was
# already missed.** The library `fiberglass` tag is 3.7/in, which the `fiberglass-r19`
# material comment records as a HIGH-DENSITY value — the R-21-in-5-1/2" batt, i.e. the
# correct SKU for a 2x6 bay, not the lofted R-19 that only reaches its label at 6-1/4".
# So the bay goes R-23.1 -> R-20.4 and the whole wall, at 23 % framing, R-14.97 -> R-14.03.
# The CARD reads R-40.4. **The honest number is R-37.3**, and `preferences.toml`'s
# `wall_r = 40` was already unmet at 38.2 for reasons that have nothing to do with the
# batt — see notes/catlin_truss_engineering.md section 7, which is the number to quote.
# Do not read the card's R-40.4 as "still on target".
EXT_2X6_SWINBURNE = Assembly(
    tag="EXT_2X6_SWINBURNE",
    layers=(
        Layer(name="stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x6", sill_gasket=inch(0.0625),
                                  layout_origin="line", corner_style="4-stud"),
              # Kept in step with EXT_2X6 above, which is the whole point of this
              # assembly: a revert that silently reintroduced mineral wool would undo the
              # fiberglass batt sweep the day anyone took it.
              cavity=CavityFill(material_ref="fiberglass")),
        Layer(name="sheathing", material_ref="struct-1-plywood", thickness=inch(0.5),
              function=LayerFunction.SHEATHING),
        # The band behind the outrigger: continuous, crossed by nothing but the blocks and
        # the tabs. There is no WRB above it because there is nothing left for one to do —
        # ccSPF is air, water, vapour and thermal in one bonded, seamless application.
        Layer(name="spray-foam", material_ref="closed-cell-spray-foam", thickness=inch(1.5),
              function=LayerFunction.INSULATION,
              control={ControlLayer.AIR, ControlLayer.WATER,
                       ControlLayer.VAPOR, ControlLayer.THERMAL}),
        # The outrigger band. 3.5" deep (2x4 on edge), of which the inner 2.5" is foam and
        # the outer 1" is the drained rainscreen gap to the clip line. Wood and foam here
        # are a PARALLEL path, which is the whole reason the foam is authored as two bands
        # rather than one 4" layer: a single layer would credit 4" of foam over 100% of the
        # area and hide the outrigger entirely. Split, `analysis._layer_rsi` parallel-paths
        # this band exactly as it already does a stud bay, and the take-off bills the outer
        # band as `insulation (cavity)`. ff 0.094 is 1.5" of outrigger per 16" bay.
        # ``corner_cap="plywood-box"`` closes the Larsen/Swinburne corner box (FHB Jan
        # 2024) outboard of the sheathing, at every owned L corner — the ~5"x5" full-height
        # void the mitred outrigger band otherwise leaves standing open at the corner.
        Layer(name="outrigger", material_ref="kdat", thickness=inch(3.5),
              function=LayerFunction.FURRING,
              framing=FramingSpec(member="2x4", direction="vertical", laid="edge",
                                  layout_origin="line", corner_cap="plywood-box"),
              cavity=CavityFill(material_ref="closed-cell-spray-foam",
                                thickness=inch(2.5), framing_factor=0.094,
                                control={ControlLayer.AIR, ControlLayer.WATER,
                                         ControlLayer.VAPOR, ControlLayer.THERMAL})),
        Layer(name="cladding", material_ref="standing-seam-snaplock", thickness=inch(0.5),
              function=LayerFunction.CLADDING),
    ),
    interfaces=(STUD_BEARING,),
    default_lining=GWB_LINING,
    source="the 2026-08-23 EXT_2X6 outrigger stack, retired 2026-08-26 in favour of the catlin truss; kept unreferenced so the revert is a swap",
)

GARAGE_WALL_2X6 = Assembly(
    tag="GARAGE_WALL_2X6",
    layers=(
        # Zip-R replaced with CDX + 2" ccSPF; nail strip replaced with corrugated.
        #
        # 24" o.c., not the solver's 16" default. W-G-E is NONBEARING (the ridge runs E-W
        # and the trusses bear on W-G-S/W-G-N), the 16'-0" overhead door is carried by its
        # own 2-ply 14" LVL on jamb packs the solver sizes from the opening, and field studs
        # beside a nonbearing opening carry nothing extra — so there is no 16" zone at the
        # door. There could not cheaply be one anyway: `FramingSpec.spacing` lives on the
        # ASSEMBLY and a Wall names one assembly, so a closer-spaced zone means a second
        # assembly tag, a second prices.toml row and a second condition_gates key to say
        # "same wall, closer studs". The trusses above went to 24" with it (GARAGE_ROOF).
        #
        # THE BAYS ARE INSULATED. They were deliberately empty with 1.5" Zip-R's continuous
        # R-6.6 doing the whole thermal job — and the assembly card lied about it, because
        # with no CavityFill `analysis._layer_rsi` bills the 5.5"
        # STRUCTURE layer as SOLID SPF over the full area and read R-14.3 for a wall whose
        # honest whole-wall was R-7-8. 2" of ccSPF in the bay is a real air seal and roughly
        # doubles the true whole-wall R for about a third of what the cladding and spacing
        # changes save. The crew is already mobilised for the house's exterior bands.
        #
        # ff 0.20 is the honest 24" o.c. figure including plates, corners and jamb packs;
        # the field default of 0.23 is the 16" number and would under-credit the foam here.
        # RM-GARAGE is `conditioned=False`, so none of this is a code minimum — it is
        # exempt from code.energy_prescriptive, building_science.condensation and the MN
        # prescriptive table alike. Every envelope number in this assembly is an owner
        # choice. Walls only: the garage ceiling is insulated separately (GARAGE_ROOF).
        Layer(name="stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x6", sill_gasket=inch(0.0625),
                                  spacing=inch(24)),
              cavity=CavityFill(material_ref="closed-cell-spray-foam", thickness=inch(2.0),
                                framing_factor=0.20,
                                control={ControlLayer.AIR, ControlLayer.WATER,
                                         ControlLayer.VAPOR, ControlLayer.THERMAL})),
        # Ordinary 5/8" CDX, NOT the house's shear-rated `struct-1-plywood` (see that
        # material's comment). It carries NO `control` set on purpose: the ccSPF behind it
        # is the air, water and vapour plane, exactly the division EXT_2X6 draws, and
        # a bare sheathing panel that claimed those layers would be a WRB nobody is buying.
        #
        # NO WRB, and that is a decision rather than an omission (owner). IRC
        # R703.2's exception releases an unconditioned detached accessory building from the
        # water-resistive barrier, and this is one. The corrugated skin over an open crown
        # cavity is the drainage plane, closed top and bottom by strips (prices.toml) — a
        # vented closure at the base and a solid one at the head, which is what makes the
        # profile self-draining rather than a trough.
        Layer(name="cdx", material_ref="cdx-plywood", thickness=inch(0.625),
              function=LayerFunction.SHEATHING,
              sheet_length=inch(108.0)),  # 4x9 on the 100" wall
        # NO RAINSCREEN FURRING, and that is a decision rather than an omission
        # (owner). Corrugated is face-fastened
        # through its crowns straight into the studs, and the corrugation itself IS the
        # drainage and vent cavity — 7/8" of continuous open flute behind every sheet, which
        # is more free area than the 3/8" 1x4 vertical furring this once carried ever gave
        # it. It is a GARAGE-only move: EXT_2X6 keeps its girts, because there the
        # cladding has to be held off 4" of exterior foam and has no sheathing face to bear
        # on.
        #
        # 7/8" CORRUGATED, not the 26 ga. concealed nail strip that stood here before. Same
        # 26 ga., same coil white, same `skin_family` so the wall and the garage roof still
        # read as one continuous skin at the flush edge — but exposed fasteners instead of
        # concealed ones, at $6.00-11.00/SF less the seam hardware.
        # `plans/pbr-cladding-savings-report.md` excluded the garage from the house's move
        # to PBR solely because PBR over Zip-R needed a girt layer whose cost cancelled the
        # saving. Removing the Zip-R removed that objection. It is corrugated rather than
        # the house's PBR because this is a secondary building and the profile is allowed
        # to differ; the white does not.
        Layer(name="cladding", material_ref="corrugated-panel-24", thickness=inch(0.875),
              function=LayerFunction.CLADDING),
    ),
    default_lining=GWB_LINING,
    source="catlin-house ifcplot/assemblies.py GARAGE_WALL; rainscreen furring dropped 2026-08-20; rebuilt 2026-08-31 — 24\" o.c. studs, 2\" ccSPF in the bays, 5/8\" CDX for the 1.5\" Zip-R, and 7/8\" corrugated exposed-fastener panel for the 26 ga. nail strip. No WRB (IRC R703.2 exception, unconditioned detached accessory building)",
)
