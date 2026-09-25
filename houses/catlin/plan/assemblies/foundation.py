# haus: editable
# Catlin assemblies — basement walls, slabs and the garage ICF stem (ConcreteSpec assemblies).
# Split out of plan/assemblies.py verbatim.
from typehaus import (
    Assembly,
    ControlLayer,
    FramingSpec,
    Layer,
    LayerBound,
    LayerDatum,
    LayerExtent,
    LayerFunction,
    MasonrySpec,
    inch,
)
from library import (
    CONCRETE_BEARING,
    FOUNDATION_WALL_XPS4_OUTBOARD,
)
from .mixes import BURIED_MIX, DECK_CAP_MIX, INTERIOR_SLAB_MIX


# --- concrete family -----------------------------------------------------------
#
# **The pour is not this house's to own.** It comes from library
# `FOUNDATION_WALL_8_XPS4_CORE` / `_12_XPS4_CORE` — the pour, waterproofing and two
# staggered 2" XPS courses (R-21.8 either way; the concrete's R-0.08/in is noise) — and each
# wall below splats one of those cores and appends the one skin that covers the foam. What stays house-local is exactly that skin, because it is a colour and
# exposure decision: neither `foundation-coating-acrylic` nor `stucco` resolves in
# ALL_MATERIALS, and the coating's colour is a stock-grey palette call that has no
# business going upstream.
#
# **The perimeter is two thicknesses and one rule, not one default.** 8" is earned only
# where a *cast concrete deck* lands on the wall top beside the sill plate and needs its own
# bearing seat inboard of it. A wood floor buys no extra width: the I-joists and their rim
# bear on the same 2x6 mudsill the framed wall above stands on, and an 8" wall carries that
# sill with 2" to spare — the conventional Minnesota wall. The only cast deck left is
# SL-M-DECK (x 18'-36', y 13'-36', spanning east-west), which bears on the EAST wall and
# the centre line and nowhere else. So W-B-E1/E2 stay 12" and the west, north and south
# perimeter goes to 8".
#
# IRC Table R404.1.2(8) permits it and says what it costs: at GM soil's 45 psf/ft, on the
# 10' wall row (9'-4" actual, footnote f forbids interpolating) retaining the 7' row (6'-6"
# actual, grade at -2'-10"), 12" reads NR and 8" reads #6 @ 48" o.c. vertical. That steel is
# authored on each wall in storeys/basement.py — without it
# `structural.foundation_unbalanced_fill` FAILs, which is the intended behaviour.
#
# 8" and not 10", which also reads NR: 8" is the standard residential form module, and the
# market rate quoted for a poured foundation "is for a typical 8" wall" (see prices.toml).
# Thickness above that adds concrete without adding forming, so 10" would keep an
# odd-thickness forming premium and hand back half the yardage saving to avoid ~245 LF of
# #6 bar. Thinning also seats the wall properly: at 12" the pour overhung the inside edge of
# its own 20" strip footing by 2", and at 8" it sits entirely on it with a 2" inboard toe.
#
# **Within each thickness, two assemblies, because the north/east/west walls and the south
# wall are two genuinely different conditions.** Both are the same core; they differ only in
# what covers the foam, and they differ because what exposes it is different.
#
# On N/E/W the foam is buried except for the 2'-10" band the grade lifts raised out of the
# ground, so it gets a coating *over that band only* — below grade the backfill protects
# the XPS and above grade the coating does, and nothing is bought for the 6'-6" in
# between. That band is not a number in this file: the extent is authored off the GRADE
# datum, so a grade lift grows it (and its coated area) without anything here being edited.
#
# On the south the sunken garden exposes the foam from -9'-4" to 0'-0", which is not a band
# off grade at all — grade is above the garden floor by nine feet there. **The court walls
# buy no skin at all**, because the sunken garden's foam is not exposed — it is inside
# W-B-BRICK's ventilated cavity, with no UV and no impact on it. What is genuinely exposed
# on the south is 6" of nobody's business either side of the excavation, so W-B-S1 and
# W-B-S4 took the ordinary BASEMENT_8 coated band and the court segments took
# nothing. See the parge retirement note below.
#
# So the two are no longer the same tail. The banded walls carry 4.175" outboard of the
# concrete face over their band and 4.05" below it; the court walls carry 4.05" throughout.
# N-B-BRICK-W/-E's stand-off is inch(-4.05) — the court walls' finished face, bare XPS —
# and the veneer's clear cavity is 1-1/2" (IRC R703.8.4 asks 1" minimum). It was inch(-4.55)
# until 2026-09-04, struck against the parge; the parge's deletion left the node stranded
# half an inch off the foam with nothing describing the gap. See BASEMENT_BRICK_VENEER's
# `air-gap` layer. Those nodes stand over the COURT segments, not the banded walls, so the
# band's own thickness has never been theirs to follow. 4.06" is 0.06" waterproofing + 2x 2"
# XPS, and is independent of the pour's thickness.

# The exposed-foundation band runs from 6" *below* grade — so no foam edge shows at the
# soil line, and so the coating is what the shovel hits rather than bare XPS — up to the top
# of the wall, where its head tucks under the rainscreen's Z-flashing with the bug screen
# above it. It is the ONLY skin over foundation XPS anywhere in this house, on all four
# sides. The wall top is the bearing seat at -1'-1 7/16", not 0'-0": the framed wall above
# reaches back down to meet it (``resolve/platform.extend_walls_to_foundation``), so the
# two skins abut there rather than leaving the mudsill and rim bare. It replaced a
# full-height parge the N/E/W walls used to claim over nine feet of buried foam, added for
# the *south* wall's exposure and applied to all four sides because a layer had no way to
# say "only here".
#
# ** IT IS A TROWEL-APPLIED ACRYLIC COATING SINCE 2026-09-04, NOT A RIGID BOARD. ** The
# 1/2" aluminium-faced panel is kept as the named alternate (see `foundation-coating-acrylic`
# and `foundation-protection-panel` below); what the swap buys is a verdict. The board's
# installed permeance is a butted joint nobody publishes a test for, so
# `building_science.condensation` reported UNKNOWN on BOTH basement assemblies for as long
# as it was authored. A mesh-reinforced lamina is seamless, a published band describes it,
# and the wall gets graded.
#
# **`function` stays CLADDING and MUST.** `checks/building_science/condensation.py` screens
# on `any(layer.function == "cladding")` — retagging to FINISH would drop both foundation
# walls out of the Glaser scope entirely, which makes the UNKNOWN vanish by losing the check
# rather than by answering it. CLADDING also holds `_is_exterior_assembly`, the rainscreen
# terminator, and `code.MN_1309_0406_waterproofing`'s accepted-function list.
#
# **The outboard sum moves 4.55" -> 4.185"** over the band (0.06 waterproofing + 2 + 2 XPS +
# 0.125 coating) and is unchanged at 4.05" below it. `W-B-BRICK` does NOT follow: its
# `N-B-BRICK-W/-E` nodes stand over the *south court* walls, which carry no band at all, so
# the band's thickness was never theirs and the 1-1/2" cavity (IRC R703.8.4 asks 1"
# minimum) is untouched. The face moves INBOARD, so nothing wall-mounted can be buried.
_PROTECTION_PANEL = Layer(name="foundation-coating",
                          material_ref="foundation-coating-acrylic-black",
                          thickness=inch(0.125), function=LayerFunction.CLADDING,
                          extent=LayerExtent(
                              bottom=LayerBound(datum=LayerDatum.GRADE, offset=inch(-6))))

# The full-height stucco parge over the south foundation was RETIRED 2026-09-04 and its one
# remaining consumer, BASEMENT_8_GARDEN, is deleted with it (2026-09-12, #70: a tag nothing
# references is deleted). The short version: 273.7 SF billed, ~29 SF of it ever visible, the
# rest inside W-B-BRICK's ventilated cavity or behind 6'-4" of backfill — a scope that never
# cleared a plasterer's mobilisation. The 29 SF is now the same GRADE band the N/E/W walls
# carry. The layer, the assembly and the full argument are in git; `Material(tag="stucco")`
# stays in library/materials/ because engine tests use the tag.

# The east wall (W-B-E1/E2), the only perimeter run SL-M-DECK bears on.
# ** THE POUR IS AUTHORED HERE NOW, NOT SPLATTED FROM THE LIBRARY CORE. **
# A ``ConcreteSpec`` is a purchase — one ticket from one plant — so it belongs to the house
# and the library must not carry one in a shared core. Stating it means authoring this
# house's own concrete layer and splatting only what is outboard of it
# (``FOUNDATION_WALL_XPS4_OUTBOARD``, published for exactly this). Slicing the core at the
# point of use is not available: this file is the constrained editable dialect and
# subscripting is forbidden in it. The thicknesses are the library's, unchanged.
BASEMENT_12 = Assembly(
    tag="BASEMENT_12",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(12.0),
              function=LayerFunction.STRUCTURE, concrete=BURIED_MIX),
        *FOUNDATION_WALL_XPS4_OUTBOARD,
        _PROTECTION_PANEL,
    ),
    interfaces=(CONCRETE_BEARING,),
    source="library FOUNDATION_WALL_12_XPS4 + the house's above-grade acrylic coating band (catlin basement east, where SL-M-DECK bears)",
)

# The west and north walls (W-B-W1/W2, W-B-N1/N2/N3) — wood floor only, so 8" reinforced.
BASEMENT_8 = Assembly(
    tag="BASEMENT_8",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(8.0),
              function=LayerFunction.STRUCTURE, concrete=BURIED_MIX),
        *FOUNDATION_WALL_XPS4_OUTBOARD,
        _PROTECTION_PANEL,
    ),
    interfaces=(CONCRETE_BEARING,),
    source="library FOUNDATION_WALL_8_XPS4 + the house's above-grade acrylic coating band (catlin basement west/north, wood floor only)",
)

# Basement slab-on-grade: 2" XPS below the slab (R-10 @ 25 psi compressive — rated for
# slab loading, not the lighter foundation-wall grade) breaks direct slab-to-clay contact.
#
# **2", an owner target call, not a code one.** The R-10 slab target is the owner's; a 3"
# board would read R-16.1 whole-assembly against it, six points of over-spec on the
# lowest-value surface in the envelope (a conditioned basement floor loses to 50 F soil, not
# to -15 F air). 2" lands the assembly at about R-11 and still clears MN Zone 6's R-10
# prescriptive slab row, which is what `code.energy_prescriptive` grades.
#
# **25 psi, and the grade is now stated per use rather than assumed house-wide.** 40 psi
# (Foamular 400 / Styrofoam Highload 40) is the frost-wing and footing-bearing grade and
# stays on those assemblies, where a strip footing imposes 10-14 psi on the board. A
# residential basement floor imposes far less, and 25 psi (Foamular 250, the standard
# under-slab board) carries it with the same margin. NOTE: `library/materials/` has ONE
# `xps` tag with no compressive field, and prices.toml keys XPS on THICKNESS only — so the
# psi grade lives in this `source=` line and is NOT priced. A 25 psi board is genuinely
# cheaper than a 40 psi one; the estimate does not yet see that.
#
# Order below the slab is the order it is built in, bottom last: concrete, then foam, then
# the retarder, then the base course. The retarder goes *under* the foam rather than between
# foam and slab — a sheet directly under a slab traps bleed water with nowhere to go and is
# the classic cause of curling; below the foam it still separates the slab from ground
# moisture and the slab can dry downward into the foam joints. (IRC R506.2.3 permits either;
# ACI 302.2R is where the preference comes from.)
SLAB_FLOOR = Assembly(
    tag="SLAB_FLOOR",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE, concrete=INTERIOR_SLAB_MIX),
        Layer(name="xps-below", material_ref="xps", thickness=inch(2.0),
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
        Layer(name="vapour-retarder", material_ref="polyethylene", thickness=inch(0.01),
              function=LayerFunction.MEMBRANE, control={ControlLayer.VAPOR}),
        Layer(name="capillary-break", material_ref="capillary-break-stone", thickness=inch(4.0),
              function=LayerFunction.SHEATHING),
    ),
    source="catlin-house basement slab: 2\" below-slab XPS, R-10 @ >=25 psi compressive (ASTM C578 Type IV), over a 10-mil ASTM E1745 Class A vapour retarder on a 4\" open-graded capillary break (IRC R506.2.2/R506.2.3); 3\" @ 40 psi until 2026-08-31",
)

# Main-floor structural deck: an EPS stay-in-place form with a cast concrete cap, over the
# (conditioned) basement — so it is an interior floor, not an envelope slab. The "INT" tag
# token is the codebase's signal for that (see FOUNDATION_WALL_12_INT, INT_2X6_PLUMBING) — it
# tells the prescriptive-energy table to skip this deck instead of holding it to the R-10
# slab minimum. Keep the token underscore-delimited: ``mn_energy._is_interior_assembly``
# keys on it and would otherwise grade a deck between two conditioned storeys against MN
# Zone 6's R-21.
#
# **This replaced a 1,233 SF x 9" cast suspended slab.** That slab was the single most
# expensive line in the model — 34.26 cy of concrete on shored plywood formwork whose
# commercial mobilisation floor alone was $25-40k — and it forced eight interior 12"
# concrete cross walls with strip footings under them, because it was designed to span
# between them. Concrete now goes only where it is wanted, under the dining radiant zone
# (x 18'-36', y 13'-36', 414 SF); the other 819 SF is wood I-joists on the same 18' span,
# and the two systems are interchangeable bay by bay because their depths match.
#
# The depth is the whole point. 4 3/8" cap + 10" form = 14 3/8", which is exactly the
# 11 7/8" joist beside it (truss west of x=18', I-joist east — same depth either way) plus
# its 3/4" plywood subfloor, its 1 1/2" mudsill and the 1/16" compressed gasket under that:
# same bearing seat, same finished-floor plane, same 18' span to the x=18' bearing line.
# (The old "4 5/8" cap + 8" form = 12 5/8"" reading here predates the 2026-08-23 deepening
# and was stale until 2026-09-12.) Both numbers are owned by ``params/main_deck.py``
# (EPS_CAP / EPS_FORM_DEPTH); ``integrity.slab_thickness`` fails the build if these two
# layers drift from them.
#
# ** BUILDDECK IS THE BASIS OF DESIGN. ** The row actually read is BuildDeck's 10" deck /
# 4" cap at 2-#5 beam bars: 20'-0" span at 62 psf live load, f'c 4,000 psi, fy 60 ksi,
# +15 psf additional dead load, deflection < L/480. The span here is 18'-0" at a cap
# 3/8" deeper than the row, and the row is quoted onto ``SL-M-DECK.published_span`` where
# ``structural.slab_published_span`` grades it and refuses it if the section drifts.
# LiteDeck (LiteForm) and Insul-Deck stay named alternates — the depth-matching argument
# above is product-neutral, which is the point — but neither publishes a span table for
# this section in its free literature, and BuildDeck's shoring design is PE-sealed where
# LiteDeck's is the installer's.
#
# Layers read top-down like SLAB_FLOOR. The gypsum is not optional trim: IRC R316.4
# requires a thermal barrier over foam plastic on the room side, and this is it.
DECK_EPS_INT = Assembly(
    tag="DECK_EPS_INT",
    layers=(
        Layer(name="concrete-cap", material_ref="concrete", thickness=inch(4.375),
              function=LayerFunction.STRUCTURE, concrete=DECK_CAP_MIX),
        Layer(name="eps-form", material_ref="eps-deck-form", thickness=inch(10.0),
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
        # The form's own integral steel rib, which is what the ceiling screws to — the same
        # "the vapour path is the air between the sections" reading `steel-stud` carries.
        Layer(name="furring-rib", material_ref="steel-stud", thickness=inch(0.5),
              function=LayerFunction.FURRING,
              framing=FramingSpec(member="1x4", direction="horizontal")),
        Layer(name="gwb", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
    ),
    interfaces=(CONCRETE_BEARING,),
    source="catlin-house main-floor deck — LiteDeck 10\" EPS stay-in-place beam (8\" base panel + 2\" top hat) with a 4 3/8\" cast cover (14 3/8\" total, so the soffit lands on the same flat bearing seat as the wood bays' mudsill), steel furring rib and a 5/8\" gypsum R316.4 thermal barrier under it; replaced CATLIN_DECK_9_INT 2026-08-21, deepened 2026-08-23",
)

# --- garage (freestanding: ICF stem + 2x6 wood wall) ---------------------------
# The form's two published dimensions, as constants rather than literals inside the layer
# stack: params/foundations.py aligns the stem off the EPS thickness (the exterior foam
# face has to land on the same node line the wood wall's zip-R face uses) and insets the
# slab off the whole 11" section. Repeating either number there would let the two drift.
#
# Reconciled against library GARAGE_ICF (CONTRIBUTING "do NOT duplicate" —
# the two used to restate the same "ICF-6" masonry spec independently). The 6" concrete
# core matches library's exactly, so GARAGE_ICF_CORE is authored as the same literal
# rather than as a coincidence. GARAGE_ICF_EPS stays 2.5" and NOT library's 2.625"
# generic default: this garage's ICF-6 form genuinely has a thinner EPS facing, a real
# product difference rather than authoring drift. The editable-plan dialect forbids
# subscripting or comprehensions, so there is no way to splice *only* library's concrete
# Layer out of its `layers` tuple here without also pulling its 2.625" EPS along with
# it — doing that would silently thicken this stem by 1/4" and break every section
# golden keyed on "2.5\"" (see fixtures/section_goldens/catlin/*GARAGE_ICF_6*). The
# concrete Layer below is restated with library's own numbers instead, which is as
# close to "pointing at" the library assembly as one Assembly's `layers` letting
# another's masonry spec drift is possible to get in this dialect.
GARAGE_ICF_EPS = inch(2.5)
GARAGE_ICF_CORE = inch(6.0)

# The stem's inside face carries the same 5/8" board the wood wall above it already lines
# with, banded from grade up — `code.R316_4` asked for it. The
# ICF's interior EPS stood bare inside the garage from the slab (poured at grade) to the
# stem top 1'-10" above it, ~176 SF of exposed foam plastic facing an occupied space with
# no thermal barrier over it. R316.4 wants 1/2" gypsum, 23/32" wood structural panel or an
# NFPA 275 barrier, and the garage is boarded already (GARAGE_WALL_2X6's `default_lining`),
# so continuing that board down the stem is the detail rather than a new one.
#
# BANDED, not full height: below grade the stem is backfilled and there is no interior to
# separate anything from — a full-height layer would bill board into the soil. The `GRADE`
# datum is the same mechanism the basement's foundation-protection panel uses, and it
# tracks `Site.grade` rather than restating it, so the band follows the next lift down.
#
# Held 1/2" off the slab in the field, as any board over a garage slab is; the model has no
# way to say so and the gap is inside the layer's own thickness either way.
GARAGE_ICF_6 = Assembly(
    tag="GARAGE_ICF_6",
    layers=(
        Layer(name="gwb-stem", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH,
              extent=LayerExtent(bottom=LayerBound(datum=LayerDatum.GRADE))),
        Layer(name="eps-int", material_ref="icf-eps", thickness=GARAGE_ICF_EPS,
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
        Layer(name="concrete", material_ref="concrete", thickness=GARAGE_ICF_CORE,
              function=LayerFunction.STRUCTURE, concrete=BURIED_MIX,
              masonry=MasonrySpec(unit_size="ICF-6", core_fill=True)),
        Layer(name="eps-ext", material_ref="icf-eps", thickness=GARAGE_ICF_EPS,
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
        # THE EXTERIOR HALF OF A REQUIREMENT THAT WAS ONLY EVER HALF-BUILT.
        # notes/garage_wall_detail_side.md asks for protective covering on BOTH faces of
        # the exposed ICF EPS above grade — "elastomeric coating, PVC trim, or rigid
        # aluminum sheeting" outside, a 15-minute thermal barrier inside. `gwb-stem` above
        # is the inside half; outboard of `eps-ext` there was nothing at all, so ~176 SF of
        # bead foam stood bare to UV, string trimmers and plow-thrown ice. This is the
        # outside half, and it is a gap being closed rather than a finish being added.
        #
        # BANDED FROM 2" BELOW GRADE, no top — so it runs to the stem top and the buried
        # inch or two seals the termination instead of leaving a lip for water to sit on.
        # `GRADE` is a datum, not a literal, so the band follows `Site.grade` on the next
        # lift exactly as `gwb-stem` and the basement's `_PROTECTION_PANEL` do.
        #
        # SINCE 2026-09-03 IT IS THE GARAGE'S WHOLE BASE SKIN. It used to run BEHIND a
        # 4'-0" aluminium wainscot on the two east piers flanking the overhead door — the
        # wainscot was a wear layer over this band, never a substitute for it, which is why
        # deleting the wainscot took nothing away from the piers. They keep exactly the
        # protection the other three walls always had, and the east elevation now reads as
        # one uniform base course. This band is not a leftover of that change; it is the
        # thing the change kept.
        #
        # ITS TOP IS A REAL JUNCTION AND IT IS FLASHED. The band's top and the corrugated
        # panel's base both land on the stem top, and a rainscreen's cavity water arrives at
        # exactly that line. `STEM_TOP_Z_FLASHING` in plan/storeys/garage.py is the Z that
        # catches it — aluminium over aluminium, broken only at the two stem gaps where
        # there is no stem to band.
        #
        # The band pushes the stem's exterior face 0.30" east (gap + sheet), which nicks the "stem and wood
        # wall are coplanar on the outside" promise this garage is built on. It is inside
        # `resolve/stacking.py::_axis_match`'s 1/2" tolerance by two orders of magnitude,
        # and it is physically true — the band really does stand proud by its own build.
        # Do not recess the EPS to hold the face still.
        # ON A VENTED STANDOFF, NOT GLUED TO THE FOAM, and `building_science.condensation`
        # is what settled that. A painted aluminium sheet is 0 perms: laid directly on
        # `eps-ext` it is a Class I retarder on the COLD side of the stem, and the Glaser
        # walk immediately found a January dew point at the concrete — a crossing against a
        # monthly MEAN, i.e. a plane that runs wet for weeks. A 1/4" drainage/vent gap
        # behind the sheet restores the drying path and is the better build anyway: it
        # drains what gets behind the band, and it keeps aluminium off damp foam and out of
        # contact with the concrete below. It is the same standoff the east wainscot uses,
        # at a quarter of the depth. CONFIRMED BY EXPERIMENT, not assumed: deleting this
        # layer puts the FAIL straight back.
        #
        # IT COSTS A DERIVED FASTENER ROW, and that row is honest. An AIRGAP outboard of
        # continuous exterior insulation is exactly the signature
        # `takeoff/fasteners.exterior_insulation_fastening` reads as screwed-furring-through-
        # foam, so the band bills ~its own grid of `SDWS22500DB`. The GEOMETRY is right — the
        # sheet really is held 2.75" off the concrete by foam and needs a long anchor — but
        # the PART is a proxy: that rule was written for furring into wood studs, and into an
        # ICF you fasten to the webs or with a stainless masonry anchor into the core. The
        # engine has no masonry-anchor concept. Quantity and length are usable; the part
        # number is not a purchase instruction. See test_hardware_takeoff.py, which used to
        # assert this house bills no such row at all.
        Layer(name="coil-gap", material_ref="air-barrier", thickness=inch(0.25),
              function=LayerFunction.AIRGAP,
              extent=LayerExtent(bottom=LayerBound(datum=LayerDatum.GRADE,
                                                   offset=inch(-2.0)))),
        Layer(name="coil-ext", material_ref="aluminum-flat-pvdf", thickness=inch(0.05),
              function=LayerFunction.CLADDING,
              extent=LayerExtent(bottom=LayerBound(datum=LayerDatum.GRADE,
                                                   offset=inch(-2.0)))),
    ),
    source="library GARAGE_ICF's 6\" concrete core (ICF-6, matching masonry spec) + this house's 2.5\" EPS facing (thinner than library's 2.625\" generic default) and gwb-stem interior banding above grade (code.R316_4); exterior face protected above grade by a PVDF-painted aluminium band from 2\" below grade to the stem top, fixed with 316 stainless gasketed screws into the ICF webs, closing the other half of the note's both-faces requirement",
)
