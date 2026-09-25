# haus: editable
# Catlin assemblies — posts, beams and the equipment stand that are not concrete.
# Split out of plan/assemblies.py verbatim.
from typehaus import (
    Assembly,
    Layer,
    LayerFunction,
    inch,
)


# Finish-only assembly for the balcony 6x6 pillars so they render (glTF) and read (IFC) as
# white-painted rather than the default bare-wood post colour. Single 5.5" layer = the 6x6.
# No balcony pillar is wood any more (the last two retired 2026-09-22); today this carries only
# the four interior stairwell posts. The notes below are kept for the record.
#
# **The pillar TOP is the detail this assembly exists to carry.** These six
# pillars are the most expensive-per-LF elements in the whole frame — 51.4 LF of them costs
# more than both cast columns and all four porch beams combined — and they are the only
# elements in the structure carrying a recurring repaint cost against a 100-year brief. So
# the durability attention belongs here, not on the columns.
#
# Two field details the model has no field for:
#
# 1. END GRAIN AT THE PILLAR TOP. A 6x6 tops out 5.5" square; the 3-2x12 beam landing on it
#    is 4.5" wide. That leaves 1/2" of exposed UPWARD end grain on the east and west faces
#    of all six pillar tops, directly under a beam whose faces shed onto it. Six joints,
#    upward end grain, in the weather, on the priciest wood in the structure —
#    notes/beam_water_protection.md covers beam tops exhaustively and never mentions these.
#    Chamfer or bevel the exposed rim, or form a small drip under the beam seat, and seal
#    the cut before the pillar is stood. Highest durability-per-dollar item in the porch.
# 2. PLANK CUT-OUT AT THE TWO CENTRE PILLARS — MOOT since 2026-09-22 (both pillars retired).
#    PT-SG-BR2 and PT-SG-BF2 bore on FS-SG-PORCH.
#    Cut a ~9" square through the composite plank at each so the POST ITSELF lands on the
#    3-ply joist pack: Trex's own spec says composite decking "cannot be used as structural
#    material". 9", not the 4" this note said until 2026-09-03 — the post is 5-1/2" square,
#    so 4" never cleared it, and the cut-out has to pass the L50Z angles' legs on the pack
#    faces as well. Size it to the post plus the connector legs plus a working gap. Not a
#    strength question (~50 psi on the plank) — it is CREEP at a 140-160 degF summer surface
#    temperature settling those two pillars relative to the four on concrete and taking the
#    balcony's watertight aluminium plank out of plane, and REPLACEABILITY, because the
#    plank is a wear layer and you cannot pull a board from under a loaded 6x6 without
#    shoring. See params/sunken_garden.py, which records why ``supported_by`` stays the
#    floor system.
POST_WHITE_PAINT = Assembly(
    tag="POST_WHITE_PAINT",
    layers=(
        Layer(name="post-paint-white", material_ref="post-paint-white", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE),
    ),
    # (single literal: the editable dialect forbids concatenated strings)
    source="catlin-house interior white-painted 6x6 posts — P-M-STRWELL-S and P-M-STRWELL-SS, the two stairwell posts standing on SL-B-FLOOR. THE BALCONY PILLARS LEFT THIS ASSEMBLY on 2026-09-03 for POST_WHITE_PAINT_DF: they need Douglas Fir-Larch at specific gravity 0.50 to satisfy ESR-2604 §3.2.2 at their caps and bases, and these two interior posts carry no rated connector and no reason to change stock. Same 5.5\" body and the same white; standard SPF under the paint",
)

# The two heat-pump ground stands. Mill-finish extruded aluminium, and the alloy is a
# corrosion choice rather than a preference: an 18" stand on a pad at grade stands in the
# splash and the plough line all winter, and aluminium with a 316 stainless anchor through
# it is the pair that does not couple. Galvanised steel legs on a de-iced pad are the ones
# that go first.
#
# 2" square section, authored as "2.0x2.0" and NOT "2x2": a bare nominal string is matched by
# `_RE_NOMINAL` in resolve/framing/profiles.py and would silently resolve to a 1.5x1.5 stick
# of lumber (→ memory: post size nominal is silently wrong).
EQUIP_STAND_ALUM = Assembly(
    tag="EQUIP_STAND_ALUM",
    layers=(
        Layer(name="equip-stand-alum", material_ref="aluminum-extrusion", thickness=inch(2.0),
              function=LayerFunction.STRUCTURE),
    ),
    source="catlin-house heat-pump ground stands — 2\" mill-finish extruded aluminium legs and cross-rails under EQ-M-HP1-OD/EQ-M-HP2-OD/EQ-M-HP3-OD, 18\" clear above its pad, wedge-anchored to it with SS316-WEDGE-38x3. THREE FRAMES ON THREE SEPARATE PADS as of 2026-09-04 — SL-SG-HPPAD carries HP2 alone, SL-M-HP1PAD carries HP1 on the north face and SL-M-HP3PAD carries HP3 in the slot. Two of the three are the unit's own published foot-hole pattern, because on a pad the legs CAN sit under the feet: HP1 is 29 3/4 in (width) x 15 9/16 in (depth) for the FXU24HP230V1R32AO and HP2 is 25 in x 15 19/32 in for the MUL30HP230V1R32AO. HP3's is a pair of 17 1/2 in rails instead, because no mounting-hole drawing for the SAP09 chassis could be sourced. That is the whole simplification the move to grade bought — on the balcony the legs answered to the deck's joist bays and beam lines and the frame had to span between two grids (see plans/01-decisions.md #64); here the only host is a flat slab, so leg = foot and the rails carry no cantilever. 18 in puts the coil bottom about 20 in above grade, well past Gree's \"install 2 in above the expected snow line\" and past the drifted depth a stand at grade in this climate has to clear. The depth-direction spacing still has NO adjustment: the cast foot's obround slot runs the WIDTH way, about 1/4 in of travel there and none across the depth",
)


# The two CENTRE pillars, split off POST_WHITE_PAINT on 2026-09-03 for one reason: species.
# POST_WHITE_PAINT stays on the two interior stairwell posts (P-M-STRWELL-S/SS), which carry
# no rated connector and have no reason to change stock. Same 5.5" body, same white, same
# section — only the lumber under the paint differs. See post-df-paint-white above.
# UNREFERENCED since 2026-09-22: kept as the named revert of the centre-pillar trial.
POST_WHITE_PAINT_DF = Assembly(
    tag="POST_WHITE_PAINT_DF",
    layers=(
        Layer(name="post-df-paint-white", material_ref="post-df-paint-white",
              thickness=inch(5.5), function=LayerFunction.STRUCTURE),
    ),
    # (single literal: the editable dialect forbids concatenated strings)
    source="catlin-house balcony CENTRE 6x6 pillars PT-SG-BR2/BF2 — Douglas Fir-Larch, specific gravity 0.50, white-painted finish. THE SPECIES IS A CONNECTOR REQUIREMENT, not a preference: ICC-ES ESR-2604 §3.2.2, ESR-2105 §3.5.2 and ESR-3096 §3.2.2 all carry the SAME clause — sawn or engineered lumber, SG >= 0.50, 19% maximum moisture content — and at SPF 0.42 neither the CCQ46SDS2.5 cap over these posts nor the MSTA12Z strap and L50Z angles that tie their bases down had any published value. The clause is family-wide, so the species call survives every part change at this joint; only the citation widens. The moisture half is still not met by an open deck frame and rides on the seal, while the WET SERVICE half is resolvable and applied: both ESR-2105 §4.1 and ESR-3096 §4.1 send it to the NDS wet service factor, so C_M 0.70 is already inside the 658 lbf and 375 lbf recorded in library/hardware/. Chamfer or bevel the 1/2\" of upward end grain left proud on the east and west faces of each pillar top by the narrower beam over it, and seal the cut before standing. Cut a ~9\" square through the composite porch plank so the POST ITSELF bears on the 3-ply joist pack below, not on decking (Trex: composite decking is not structural material) — 9\" because the post is 5-1/2\" square and the cut must also clear the L50Z angle legs lying on the pack beside it. The post stands directly on the joists with no plate between, so the joint is wood on wood. PT-SG-BF2 also serves as the RL-SG-PORCH south-leg guard post at x 18'-0\", so its top 42\" is a guard post and its rails frame into the 6x6 rather than into a 2x2 beside it",
)

# Guards were split off POST_WHITE_PAINT (they shared it with the balcony's
# 6x6 pillars/knee braces, which must stay white) — same 5.5" body, only the colour differs.
# Metal, not painted PT: `_solid_color` reads the STRUCTURE layer's material, so
# metal-dark-exterior here is what darkens the railings in both renderers.
# The suite bedroom's four elm tudor posts (plans/TODO.md §Hardwood): same pattern as
# POST_WHITE_PAINT — the STRUCTURE material colours the solid and names the species for the
# wood_surfaces takeoff. 6.125" body = the custom timber, sheathing to drywall face, a
# deviation within W-S-W3's stud line, deliberately not a change to EXT_2X6.
ELM_TIMBER = Assembly(
    tag="ELM_TIMBER",
    layers=(
        Layer(name="elm-timber", material_ref="elm-timber", thickness=inch(6.125),
              function=LayerFunction.STRUCTURE),
    ),
    source="plans/TODO.md — suite tudor posts, elm 6-1/8\" square",
)

# --- structural members that are NOT concrete -----------------------------------
# `structural_solids` keys on solid CATEGORY, and "beam"/"column" are categories, not
# materials. Until these four assemblies existed every Beam in the house and four of the
# nine bare columns resolved with `structure_material=None`, which meant three separate
# things went wrong at once: the section hatcher fell back to `solid_material_ref`'s
# "any non-round beam is spf" rule, the GLB palette painted an LVL flitch and a treated
# 2x6 rafter the same colour, and the estimate billed 1.06 cy of engineered lumber
# through a $/cy row sitting in the CONCRETE table because that was the only table
# `structural_solids` reached. Authoring the assembly is what makes `structure_material`
# well-defined per group — see cli/prices.MATERIAL_ONLY, which can now say "this section
# bills wood" instead of only "this section bills concrete".
#
# The LAYER THICKNESS here is one ply, not the built-up width, and that is deliberate: the
# real section is `Beam.size`, which the resolver reads directly. The assembly exists to
# name the MATERIAL, and a ply is the unit LVL is made in.
#
# Two members, both 3-1.75x11.875: BM-M-HALL and BM-S-HALL. NOTHING ON THIS ASSEMBLY IS
# EXTERIOR any more. It used to carry the sunken garden's seven beams too, and to claim in
# its `source` that the back/front pairs were "treated LVL" — which is not a product.
# Treated Parallam Plus PSL is the real article, it comes only in 9 1/4"/11 7/8"/14"/16"
# depths, and Weyerhaeuser forbids resawing it in depth, so the 11 1/4" the porch is derived
# from was never buyable treated. All seven are 3-ply KDAT sawn stock on BEAM_KDAT now
# (see params/sunken_garden.py).

# Every treated sawn member in the house's outdoor frame: the breezeway (four 2-2x8 floor
# and roof beams, three 2x6 rafters), the balcony's two E-W brace rails, and the sunken
# garden's seven beams, which had been on BEAM_LVL claiming a treatment LVL is not sold in.
#
# All of it stands in weather over open ground with no enclosure above it, so every stick is
# treated — and KDAT rather than plain PT, because a wet-treated deck frame shrinks and cups
# through its first season and backs its own fasteners out doing it.

# The four members of the garden's frame that read as trim rather than as structure: the
# porch's front beam pair BM-SG-FRW/FRE and the balcony's west and east beams BM-SG-BLW/BLE.
# Same KDAT stock and the same sections as BEAM_KDAT — nothing about the framing changes —
# but these four are the sticks you see from the garden, in the same plane as the six white
# 6x6 pillars and their knee braces, so they are painted the same white. What stays on
# BEAM_KDAT is what is hidden: the back beam pair sits against the house behind the porch
# deck, BM-SG-BLC is the balcony's centre beam, inside the deck with a joist bay either
# side, and both E-W brace rails are bolted to the pillars' inboard faces rather than
# standing in the garden's own plane.
#
# A SEPARATE ASSEMBLY, not a `POST_WHITE_PAINT` reuse: that one's single 5.5" layer is the
# 6x6 body, and `[timber]` prices it per cubic yard off a 6x6's lineal-foot rate. A beam's
# real section is `Beam.size`, so the layer here is one 1 1/2" ply exactly as BEAM_KDAT's is,
# and the price row below it in `houses/catlin/prices.toml` is the KDAT beam rate plus paint.
# UNREFERENCED since 2026-09-22: kept as the named revert of the centre-pillar trial.
BEAM_WHITE_PAINT = Assembly(
    tag="BEAM_WHITE_PAINT",
    layers=(
        Layer(name="beam-paint-white", material_ref="post-paint-white", thickness=inch(1.5),
              function=LayerFunction.STRUCTURE),
    ),
    source="catlin-house sunken-garden exposed frame — KDAT 2x plies, white-painted to match the pillars: BM-SG-FRW/FRE and BM-SG-BLW/BLE (3-2x12)",
)
