# haus: editable
# Catlin assemblies — the plant room's humid walls and the tub deck.
# Split out of plan/assemblies.py verbatim.
from typehaus import (
    Assembly,
    CavityFill,
    ControlLayer,
    FramingSpec,
    Layer,
    LayerFunction,
    Substitution,
    inch,
    layers,
)
from library import (
    STUD_BEARING,
    PAINT_FINISH_B,
)


# --- plant room (RM-S-PLANT) ------------------------------------------------------
# A room held at ~75 F / 70% RH year-round against a -15 F design temperature is a
# natatorium-class vapour drive in a residential shell, and the failure mode is invisible:
# rot inside the stud bays, found years later. The whole design is one idea — no
# moisture-sensitive material ever sees moist room air — and it is authored the way the
# sauna's hot side is authored, as its own wall TYPE rather than a `Room.wall_lining`
# override. That is deliberate three times over: the liner changes the wall's thickness (a
# lining override may not), an asymmetric wall needs `interior_room` to say which face it
# lands on, and only a type is a thing `building_science.humid_room_liner` can see.
#
# The panel is NOT the vapour barrier — no PVC or FRP maker publishes a perm rating, so the
# control layer is a separate, continuous, sealed membrane behind it, chosen because it has
# a published ASTM E96 number. The furring between them is a drainage and drying gap: any
# water that gets behind the panel runs down it to the floor tray instead of standing on
# the membrane. See notes/plant_room.md for the full argument and the numbers.
_HUMID_LINER = (
    Layer(name="pvc-panel", material_ref="pvc-panel", thickness=inch(0.5),
          function=LayerFunction.FINISH),
    # 1x4 laid flat and running horizontally, like the sauna's: T&G PVC runs vertically, so
    # its concealed screw flange lands on strapping across the studs rather than with them.
    # The gap it makes is the point of it — anything that gets behind the panel drains down
    # it to the floor tray instead of standing on the membrane.
    Layer(name="liner-furring", material_ref="spf", thickness=inch(0.75),
          function=LayerFunction.FURRING,
          framing=FramingSpec(member="1x4", direction="horizontal")),
    Layer(name="humid-membrane", material_ref="humid-room-membrane", thickness=inch(0.04),
          function=LayerFunction.MEMBRANE,
          control={ControlLayer.VAPOR, ControlLayer.AIR}),
)

# The two exterior walls, W-S-S1 and W-S-W4. Everything outboard of the liner is
# EXT_2X6 verbatim, restated rather than composed because the editable dialect has
# no way to splice one assembly's layers into another. Keep the two in step by hand.
#
# EXT_2X6 needs no re-engineering for this room and deliberately gets none: the
# truss wall's 4" of 2 lb ccSPF at 1.6 perm-in runs
# about 0.4 perm — the SAME Class II the polyiso+EPS stack it replaced read, slow but real
# outward drying. The warning the CI stack carried (never foil-faced polyiso, which at 0.03
# perm would sandwich the stud bay between two vapour barriers with wet-prone wood at 25 F
# in between) is moot now that there is no board in the stack at all; it is left here as the
# reason the foam's permeance is a spec line and not an incidental.
# ** LEFT FLAT, DELIBERATELY, WHERE ITS THREE SIBLINGS BECAME VARIANTS (2026-09-12, #70). **
# The obvious conversion is `variant_of="EXT_2X6"` with the humid liner as
# `default_lining` — it would delete the whole verbatim copy of EXT_2X6's outboard tail
# below. It was built and measured, and it moves the building: `resolve/rooms.py`
# polygonises from wall AXES and insets by LINING, so shifting 3.29" of liner out of
# `layers` and into `default_lining` moves this wall's axis and every second-storey room
# polygon with it — conditioned area 5,001 -> 4,973 sf, RM-S-PLANT 159 -> 156 sf, and the
# ventilation and heating loads that are derived from them. Not one check failed, which is
# the point: it is a silent 28 sf, and no room actually changed size on site.
#
# Keeping it flat costs the duplication. That is the honest trade until a variant can state
# an EMPTY `default_lining` distinct from an absent one — today an empty one means "track
# the base", and the base's painted gypsum is exactly what must NOT land in this room.
# ** GYPSUM BEHIND THE MEMBRANE (owner, 2026-09-24). ** This is the one liner wall with
# ccSPF in it, and R316.4 wants a thermal barrier between that foam and the room: neither the
# PVC nor the membrane is one. The house's own 5/8" `gwb` goes on the studs, on the DRY side
# of the membrane, so no moisture-sensitive material sees room air. Durock has no NFPA 275
# listing and no E96 number; 23/32" plywood also qualifies but would not match the house's
# 1/2" sheathing everywhere else.
PLANT_EXT_2X6_HUMID = Assembly(
    tag="PLANT_EXT_2X6_HUMID",
    layers=(
        *_HUMID_LINER,
        Layer(name="gwb-plant", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x6", sill_gasket=inch(0.0625),
                                  layout_origin="line", corner_style="4-stud"),
              cavity=CavityFill(material_ref="mineral-wool")),
        Layer(name="sheathing", material_ref="struct-1-plywood", thickness=inch(0.5),
              function=LayerFunction.SHEATHING,
              sheet_length=inch(120.0)),  # 4x10: see EXT_2X6
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
    source="notes/plant_room.md — EXT_2X6 outboard of a sealed PVC/membrane liner; the sheathing datum does not move (decision #43), the liner grows inward",
)

# W-S-C1, the x=18' bearing line. Liner on the plant-room face, ordinary painted gypsum on
# the study side — the same asymmetry SAUNA_2X4 has, and the same reason `interior_room` is
# not optional on the wall that uses it.
#
# "INT" is a whole `_`-delimited token on purpose: `mn_energy.py` splits the tag on `_` to
# decide whether a wall is interior, and PLANT_INT2X6 or PLANTINT_2X6 would be graded
# against R-21 as though this partition faced the weather.
# `layout_origin="line"` for the same reason `PLANT_EXT_2X6_HUMID` has it on the facades:
# W-S-C1 is a member of the x=18'-0" centreline, and one wall left on its own start node
# puts a jog in a line that is otherwise continuous. Same line, humid liner.
# A VARIANT of INT_2X6_BRG (#70): the liner replaces the base's room-side leaf and the bay
# gains mineral wool; the study face is the base's own painted gypsum (`gwb-b`+`paint-b`,
# the same 5/8"+0.01" the hand-written `gwb-cold`+`paint-b` was).
PLANT_INT_2X6_BRG_HUMID = Assembly(
    tag="PLANT_INT_2X6_BRG_HUMID",
    variant_of="INT_2X6_BRG",
    substitute=(
        Substitution(
            span=layers("paint-a", "stud"),
            replacement=(
                *_HUMID_LINER,
                Layer(name="stud", material_ref="spf", thickness=inch(5.5),
                      function=LayerFunction.STRUCTURE,
                      framing=FramingSpec(member="2x6", layout_origin="line"),
                      cavity=CavityFill(material_ref="mineral-wool")),
            ),
        ),
    ),
    source="notes/plant_room.md — plant room / RM-S-STUDY2 bearing line; humid liner one face, painted gypsum the other",
)

# W-S-PS1 and W-S-PS2, the two north partitions onto RM-S-STUDY2. Same idea one stud size
# down. The cavity is insulated even though both sides are conditioned: it is a 75 F room
# against a 70 F one, and the batt is there for the temperature difference and the noise of
# a fan running continuously, not for an energy code.
PLANT_INT_2X4_HUMID = Assembly(
    tag="PLANT_INT_2X4_HUMID",
    layers=(
        *_HUMID_LINER,
        Layer(name="stud", material_ref="spf", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x4"),
              cavity=CavityFill(material_ref="mineral-wool")),
        Layer(name="gwb-cold", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        PAINT_FINISH_B,
    ),
    interfaces=(STUD_BEARING,),
    source="notes/plant_room.md — plant room north partitions; humid liner one face, painted gypsum the other",
)

# --- RM-M-BATH2 drop-in tub deck --------------------------------------------------------
# The knee-wall box and its plywood cap under FX-M-BATH2-TUB, the Kohler K-5713-W1
# Underscore drop-in with the Bask heated surface (plan/products.py).
#
# ** THE MINERAL WOOL IN THIS CAVITY IS NOT INTERCHANGEABLE WITH FIBERGLASS. ** It is the
# one cavity in the house whose insulation choice is a MOISTURE decision rather than a
# thermal one: it sits under the rim of a 72-gallon bath, permanently inside a sealed box
# that can only be reached through a 14x14 panel, in the wettest room in the house. Mineral
# wool is hydrophobic, non-capillary and dimensionally stable when it does get wet;
# fiberglass in this box would slump into the bottom of the bay and stay damp. If the
# reinsulation pass ever sweeps `mineral-wool` -> `fiberglass` across the house, THIS
# ASSEMBLY IS AN EXPLICIT EXCEPTION and must be skipped. `library/materials/` carries
# both materials; the swap is a material_ref edit, so nothing but this note stops it.
#
# The batt is not there for an energy code — both faces are inside the thermal envelope and
# `mn_energy` never grades it (the tag carries the `INT` token, whole `_`-delimited, so the
# R-21 exterior grade does not apply). It is there for two things the code has no opinion
# about: the acoustics of 72 gallons falling into an acrylic shell over a 18'-0" I-joist
# span, and holding the heat of a Bask-warmed surface in the tub rather than in the box.
#
# Symmetric on purpose — 1/2" exterior-grade plywood BOTH faces, not ply inside and gypsum
# out. Two reasons. (1) The box is a freestanding component in the storey wall graph: its
# two knee walls close no loop, so `resolve/orientation.py` cannot recover a winding and
# falls back to `outward_sign = +1`. A symmetric stack makes that fallback unobservable —
# an asymmetric one would build inside-out on a sign flip and nothing would say so.
# (2) Exterior-grade ply is the right board on the room face too: it is the substrate the
# deck's tile and the tub's silicone joint land on, 4" from a shower.
#
# Tile is NOT a layer here. The deck top and the knee-wall faces are tiled with the room's
# floor tile, which is a finish-schedule fact about RM-M-BATH2 (`Room.floor_finish`), and
# the 1/2" of tile + thinset is the difference between the cap's 21 1/2" top and the tub
# rim's 22" — see the elevation arithmetic on SL-M-TUBDK in plan/storeys/main.py.
TUBDECK_INT_2X4 = Assembly(
    tag="TUBDECK_INT_2X4",
    layers=(
        Layer(name="ply-room", material_ref="struct-1-plywood", thickness=inch(0.5),
              function=LayerFunction.SHEATHING),
        Layer(name="stud", material_ref="spf", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x4", spacing=inch(16)),
              cavity=CavityFill(material_ref="mineral-wool")),
        Layer(name="ply-bay", material_ref="struct-1-plywood", thickness=inch(0.5),
              function=LayerFunction.SHEATHING),
    ),
    interfaces=(STUD_BEARING,),
    source="Kohler Installation and Care Guide 1196030-2 (Bath with Heated Surface): 2x4 or 2x6 stud framing, maximum 1/8 in. gap between the bath rim and the framing/deck. Mineral wool cavity is a moisture decision, not an energy one - see the note above; do not substitute fiberglass",
)

# The cap: flat 2x4 blocking at 16" o.c. with 3/4" exterior-grade plywood over it. TWO
# layers rather than PORCH_DECK_COMPOSITE's one, and both of them earn their place.
#
# The blocking is real construction, not bookkeeping - 3/4" plywood does not span the bay's
# 36" on its own with someone sitting on the ledge, so the sheet lands on flat 2x4s bearing
# on the knee walls' top plates and on ledgers against W-M-BA2E and W-M-HS1/HS2.
#
# It is also what gets the plywood BILLED. `takeoff/framing.py` sends a slab's STRUCTURE
# layer to the structural-solids row as a cubic-yard volume (the long-standing complaint on
# `params/sunken_garden.py`'s SL-SG decks: a laid deck priced like a pour), while every
# non-STRUCTURE layer bills by the square foot in `takeoff/envelope.py`. Putting the
# blocking on STRUCTURE and the sheet on SHEATHING lands each where it belongs: lumber in
# the volume row, plywood as area. A `Slab` must have a STRUCTURE layer -
# `integrity.assembly_layers` is an ERROR without one - so a plywood-only cap is not an
# option anyway.
#
# The tub does not bear on any of this. Kohler is explicit that the rim carries no load and
# the bath sits on a 1"-2" mortar bed on the subfloor, so the cap carries only itself, its
# tile, and whoever sits on the deck.
TUBDECK_INT_PLY_CAP = Assembly(
    tag="TUBDECK_INT_PLY_CAP",
    layers=(
        Layer(name="deck-block", material_ref="spf", thickness=inch(1.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x4", spacing=inch(16))),
        Layer(name="deck-ply", material_ref="struct-1-plywood", thickness=inch(0.75),
              function=LayerFunction.SHEATHING),
    ),
    source="Kohler Installation and Care Guide 1196030-2 - drop-in deck surround; flat 2x4 blocking at 16 in. o.c. under 3/4 in. exterior-grade plywood, tiled, rim on max 1/8 in. spacers",
)
