# haus: editable
# Catlin house assemblies — ported from catlin-house ifcplot (WP3.1).
# Layer order is interior → exterior. The exterior wall family is one 2x6 stack on every
# framed storey (sheathing / 4" closed-cell spray foam around a 2x4 truss / standing seam),
# so the sheathing plane and every control layer are continuous with no stud-depth jog.
from typehaus import (
    Assembly,
    AssemblyInterface,
    CavityFill,
    ConstructionRule,
    ControlLayer,
    FramingSpec,
    Layer,
    LayerBound,
    LayerDatum,
    LayerExtent,
    LayerFunction,
    MasonrySpec,
    Material,
    inch,
)
from typehaus.model import PartitionLayout
from library import (
    FOUNDATION_WALL_8_XPS4_CORE,
    FOUNDATION_WALL_12_INT,
    FOUNDATION_WALL_12_XPS4_CORE,
    INT_2X4_PARTITION,
    INT_2X4_STAGGERED_DOUBLE_GWB,
    INT_2X6_PLUMBING,
    INT_2X6_STAGGERED_PLUMBING,
    STARTER_MATERIALS,
)

# Named face roles the junction solver binds mixed-assembly corners/tees to (#44). The
# ``bearing`` role names the load-bearing layer whose face carries structural continuity
# through a return, so two walls are "continuous" when they publish the same bearing
# material (concrete↔concrete, SPF↔SPF) regardless of the finish/insulation around it —
# never by layer name or index. Variants inherit these from their base assembly.
_CONCRETE_BEARING = AssemblyInterface(role="bearing", layer_name="concrete", outboard=False)
_STUD_BEARING = AssemblyInterface(role="bearing", layer_name="stud", outboard=False)

# Painted gypsum lining. Paint comes FIRST (interior->exterior order) because it is the
# room-side face and so the assembly's warm-side vapour retarder in the Glaser walk (IRC
# R702.7/.7.1: latex over gypsum is Class III, 1.0-10 perm). Bare gypsum reads ~30 perm —
# no retarder — which is not the wall that gets built.
# Colour lives on the `latex-paint` material, not on the Layer (no colour slot): a
# different wall colour is a different Material. `latex-paint-accent` + `ACCENT_GWB_LINING`
# below are that mechanism's accent-wall instance, swapped in per room/wall via
# `Room.wall_lining`/`wall_lining_exceptions` (see RM-S-BED1 in storeys/second.py).
_PAINT_FINISH = Layer(name="paint", material_ref="latex-paint", thickness=inch(0.01),
                      function=LayerFunction.FINISH,
                      control={ControlLayer.VAPOR})

# The accent film. Same name ("paint"), same thickness, same Class III vapour job — only the
# material (and so the colour) differs, which is what keeps an accent wall's Glaser walk and
# lining inset identical to its neighbours'.
_PAINT_FINISH_ACCENT = Layer(name="paint", material_ref="latex-paint-accent",
                             thickness=inch(0.01), function=LayerFunction.FINISH,
                             control={ControlLayer.VAPOR})

# The same film named per face, for partitions that carry their gypsum in `layers` and so
# have two room faces rather than one lining. `-a`/`-b` match the `gwb-a`/`gwb-b` each sits on.
_PAINT_FINISH_A = Layer(name="paint-a", material_ref="latex-paint", thickness=inch(0.01),
                        function=LayerFunction.FINISH,
                        control={ControlLayer.VAPOR})
_PAINT_FINISH_B = Layer(name="paint-b", material_ref="latex-paint", thickness=inch(0.01),
                        function=LayerFunction.FINISH,
                        control={ControlLayer.VAPOR})

_GWB_LINING = (
    _PAINT_FINISH,
    Layer(name="gwb-int", material_ref="gwb", thickness=inch(0.625),
          function=LayerFunction.FINISH),
)

# The accent-wall lining: `_GWB_LINING` with the accent film in place of the off-white one.
# Same gypsum sheet, same total thickness, so swapping it via `Room.wall_lining` /
# `wall_lining_exceptions` moves no face and changes no clear-floor inset — only the colour.
ACCENT_GWB_LINING = (
    _PAINT_FINISH_ACCENT,
    Layer(name="gwb-int", material_ref="gwb", thickness=inch(0.625),
          function=LayerFunction.FINISH),
)

# --- exterior wall family -----------------------------------------------------
# One 2x6 exterior wall type for main, second and attic. Storey nuance that is a
# purchasing note rather than a different assembly: the MAIN storey's studs are LSL
# (straightness under the 9' first-floor glazing/cabinet runs); second + attic are
# standard dimensional 2x6 SPF. Same 5.5" depth either way, so one assembly tells
# the truth about the geometry and the source string records the material split.
#
# **A SWINBURNE TRUSS WALL, not a rigid-CI wall** (2026-08-23). Until this date the
# cladding stood off on 1/2" furring held through 4" of polyiso + EPS by 537 eight-inch
# structural screws, over a sheet WRB. It now stands off on an INTERMITTENT WOODEN TRUSS —
# a 2x4 block flat on the sheathing, a 1/2" plywood tab on the block's side, a KDAT 2x4
# outrigger on edge lap-screwed to the tab — with closed-cell spray foam filling the whole
# 4" around it. Three consequences, each load-bearing somewhere else:
#
#   1. THE WRB IS GONE, and its absence is the spec, not an omission. ccSPF is air +
#      water + vapour + thermal in one bonded, seamless application, so the foam face IS
#      the water plane. `plan/transitions.py` names it as such (`AIR_WATER_THERMAL`), and
#      that is what `advisory.control_continuity` watches. The build order follows from it:
#      the bucks go in FIRST and the foam is sprayed around them, never the other way.
#   2. Only the TAB crosses the insulation zone, and only every 40" up every 16" bay.
#      That is what buys the (small) bridging improvement — R-38.6 against R-36.8 — and
#      it is small on purpose: the outrigger's back 2-1/2" is inside the foam and the
#      engine parallel-paths it, which is the conservative 1D reading of a 2D detail.
#   3. The cladding plane moves OUT 1/2" (11.5" total, was 11.02"). Walls align on
#      `face("sheathing-ext")`, so no room changes size and nothing interior moves — but
#      `params/roof_trim.py`, `params/breezeway.py` and `plan/wind_clamps.py` all measure
#      off the cladding face and move with it.
#
# The honest case for the change is LABOUR: no 8" screws, no two-layer board install, no
# separate WRB, one sprayer instead of three operations. See notes/outie_window_truss_detail.md.
# LAYOUT_ORIGIN (2026-08-25). Both framing specs below set ``layout_origin="line"``, which
# counts the 16" module from this wall's *layout line* — the derived chain of collinear,
# stacked walls (``resolve/layout_lines.py``) — instead of from each wall's own start node.
# Both, deliberately: the outriggers are clipped to the studs, so a stud spec on the line
# and a batten spec on the wall would take the rainscreen off its backing.
#
# This is the assembly it was built for: deliberately one type for main, second and attic,
# and the south facade alone is eight walls on one line (W-M-S1/S2, W-S-S1/S2, W-A-S1..S4),
# split at tees purely as an authoring convenience, and every split used to restart the
# module. The attic was the visible symptom — W-A-S2 starts at x=10'-0" and W-A-S3 at
# x=18'-0", both 8" off 16", so two of the four gable segments framed on a grid the storeys
# below never used. ``PLANT_EXT_2X6_HUMID`` sets it too and has to: W-S-S1 and W-S-W4 are
# members of the south and west lines, and one wall left on wall-start origin puts a jog in
# a line that is otherwise continuous.
#
# What it cost: 20 windows moved 3"–8" onto the unified grid, and that is the part to
# understand before moving any of them back. The old per-segment phase was *why* several
# facade compositions were crooked, so hanging them all on one datum let four documented
# defects go at once — the west face's lost fifth column (WIN-S-BATH-W back under
# WIN-M-MUD), the east knee band's 4" north-end miss, the north gable's asymmetry about the
# ridge, and the attic juliet pair's 3" off-module exception. The south face gained mirror
# symmetry about the ridge on both storeys, and the east second-storey row went from a
# 9'-0"/10'-0"/9'-0" beat to an even 9'-4". See CLAUDE.md, Facade rules.
CATLIN_EXT_2X6 = Assembly(
    tag="CATLIN_EXT_2X6",
    layers=(
        # Four-stud outside corners (2026-08-25): the thermal objection APA/BASC raise
        # against a solid corner post does not apply here — the primary insulation is the
        # continuous exterior closed-cell foam OUTBOARD of this layer, so the post itself
        # does not need an insulable void. See houses/catlin/CLAUDE.md's corner section.
        Layer(name="stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x6", sill_gasket=inch(0.0625),
                                  layout_origin="line", corner_style="4-stud"),
              cavity=CavityFill(material_ref="mineral-wool")),
        Layer(name="sheathing", material_ref="struct-1-plywood", thickness=inch(0.5),
              function=LayerFunction.SHEATHING),
        # BAND A, 0 - 1.5" off the sheathing. Continuous ccSPF, crossed only by the
        # block-1s the pass frames on the stud module. There is no WRB above it because
        # there is nothing left for one to do — ccSPF is air, water, vapour and thermal in
        # one bonded, seamless application. Sprayed FIRST, flush to the block-1 faces and
        # before the inner girts go on: a flat girt lying 1.5" off the sheathing shadows the
        # pocket behind it and the foam would void there otherwise.
        Layer(name="spray-foam", material_ref="closed-cell-spray-foam", thickness=inch(1.5),
              function=LayerFunction.INSULATION,
              control={ControlLayer.AIR, ControlLayer.WATER,
                       ControlLayer.VAPOR, ControlLayer.THERMAL}),
        # BAND B, 1.5 - 3.0". The INNER GIRT: plain SPF 2x4 laid flat, horizontal, 24" o.c.,
        # buried in the second foam lift and never wet. One 5" SDWS per block-1 through
        # girt + block + sheathing into the stud. `standoff="block"` is the whole selector
        # for `resolve/framing/truss_girts.py`; `layout_origin="line"` puts its blocks on
        # the same unified stud module the facade's studs and windows already sit on.
        #
        # Wood and foam here are a PARALLEL path, which is the whole reason the 4" of foam
        # is authored as three bands rather than one layer: a single 4" layer would credit
        # foam over 100% of the area and hide both girt tiers entirely. Split,
        # `analysis._layer_rsi` parallel-paths each band exactly as it already does a stud
        # bay, and the take-off bills the fills as `insulation (cavity)`.
        # ff 0.146 is 3.5" of flat girt per 24" course. The band A/C BLOCKS (3.2% each) are
        # modelled by the pass and are deliberately NOT authored as a fill — a plain
        # INSULATION layer carries no framing factor — so the card reads a little high and
        # notes/catlin_truss_engineering.md states the honest number.
        Layer(name="inner-girt", material_ref="spf", thickness=inch(1.5),
              function=LayerFunction.FURRING,
              framing=FramingSpec(member="2x4", direction="horizontal", laid="flat",
                                  spacing=inch(24), layout_origin="line",
                                  standoff="block"),
              cavity=CavityFill(material_ref="closed-cell-spray-foam",
                                thickness=inch(1.5), framing_factor=0.146,
                                control={ControlLayer.AIR, ControlLayer.WATER,
                                         ControlLayer.VAPOR, ControlLayer.THERMAL})),
        # BAND C, 3.0 - 4.5", authored as its two halves. The last 1" of the 4" foam total,
        # then the 1/2" vented gap the block-2s stand in. The applicator shaves this lift to
        # a gauge — inner girt face + 1" — because 1/2" is inside ccSPF surface tolerance;
        # the alternative margins are a 2" block-2 (1" gap) or 3-3/4" of foam. See the
        # engineering note's Risks.
        Layer(name="foam-vent", material_ref="closed-cell-spray-foam", thickness=inch(1.0),
              function=LayerFunction.INSULATION,
              control={ControlLayer.AIR, ControlLayer.WATER,
                       ControlLayer.VAPOR, ControlLayer.THERMAL}),
        Layer(name="vent-gap", material_ref="air-barrier", thickness=inch(0.5),
              function=LayerFunction.AIRGAP),
        # BAND D, 4.5 - 6.0". The OUTER GIRT: the cladding nailer, the window mount plane,
        # and the one treated layer in the wall — block-2 inherits its material, which is
        # what puts the two block tiers on two BOM rows. Same 24" courses at the SAME
        # elevations as the inner girt; one 5" SDWS per block-2 into the inner girt. It is
        # a 3-1/2"-deep horizontal ledge behind the cladding that will wet-cycle for the
        # life of the wall, which is why KDAT and not the vent alone carries it. No fill:
        # the gap behind it is the drainage plane and it vents.
        Layer(name="outer-girt", material_ref="kdat", thickness=inch(1.5),
              function=LayerFunction.FURRING,
              framing=FramingSpec(member="2x4", direction="horizontal", laid="flat",
                                  spacing=inch(24), layout_origin="line",
                                  standoff="block")),
        Layer(name="cladding", material_ref="pbr-panel-26", thickness=inch(1.25),
              function=LayerFunction.CLADDING),
    ),
    interfaces=(_STUD_BEARING,),
    default_lining=_GWB_LINING,
    source="catlin-house ifcplot/catlin_house.py wall siding stack; main-storey studs are LSL, second/attic standard dimensional 2x6",
)

# --- the Swinburne truss wall, kept one swap away (2026-08-26) ----------------
#
# What CATLIN_EXT_2X6 was from 2026-08-23 to 2026-08-26, verbatim: a 3-piece chiral pack —
# a 2x4 flat block on the sheathing, a 1/2" plywood tab, a KDAT 2x4 outrigger stood on edge
# and lap-screwed to the tab, vertical, 16" o.c. — inside 4" of ccSPF. It works. It is
# fussy to build (tab lap-screws that were never even billed, a pack the engine has to slide
# and sometimes drop), and its vertical outriggers give a vertical standing-seam clip no
# horizontal nailer at all, which is why the girts replaced it.
#
# **Referenced by nothing, and that is the point** — like `glazed-green-brick`, it is here so
# the revert is a swap and not an archaeology exercise. To go back: give CATLIN_EXT_2X6 and
# PLANT_EXT_2X6_HUMID this layer tuple, restore `_WALL_OUTBOARD_IN` in params/roof_trim.py
# and `_HOUSE_CLADDING_Y` in params/breezeway.py to their 5.5"-proud values, and uncomment
# the 2026-08-23 rows in prices.toml. `resolve/framing/truss_frame.py` and its branch of the
# pass never went anywhere: they are selected by `laid="edge"` + vertical, which is exactly
# what this tuple says.
CATLIN_EXT_2X6_SWINBURNE = Assembly(
    tag="CATLIN_EXT_2X6_SWINBURNE",
    layers=(
        Layer(name="stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x6", sill_gasket=inch(0.0625),
                                  layout_origin="line", corner_style="4-stud"),
              cavity=CavityFill(material_ref="mineral-wool")),
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
    interfaces=(_STUD_BEARING,),
    default_lining=_GWB_LINING,
    source="the 2026-08-23 CATLIN_EXT_2X6 outrigger stack, retired 2026-08-26 in favour of the catlin truss; kept unreferenced so the revert is a swap",
)

# --- hot roof (unvented; no batten framing grows — → 30 §WP3.11) --------------
#
# **A screwed-down nailbase, not a vented batten roof** (2026-08-20). Until this date the
# metal landed on a 3/4" batten air gap over the foam. It now lands on a second structural
# deck screwed straight through the foam into the rafters, and there is no vent channel at
# all. Three consequences worth stating, because each is load-bearing somewhere else:
#
#   1. ONE sheathing layer became TWO, on opposite sides of the insulation. The lower
#      (1/2" ZIP, taped) is the air/vapour/water control plane and replaces the old
#      plywood-plus-WRB pair — one taped panel doing what two layers did. The upper
#      (5/8" OSB) is a fastening substrate: it exists so the standing seam's concealed
#      floating clips have something to bite that is not foam.
#   2. The polyiso is authored as TWO 3" layers rather than one 6". That is not bookkeeping
#      — it is the spec. The seams of the two courses are staggered and each course taped,
#      so no joint runs unbroken from deck to deck and there is no straight air or thermal
#      path through 6" of foam. One 6" layer cannot say that.
#   3. The screws through the whole sandwich are 0.625 + 6.0 + 0.54 = 7.165" of penetration
#      plus 1.5" of embedment = 8.665", which is why they are the 10" SDWH and not the 8"
#      SDWS. `takeoff/fasteners.py` derives that from this stack; do not hand-size it.
#
# Two layers here exist only because the monthly condensation gate said so, and both are
# cheap answers to expensive problems — see their materials below for the full argument:
#
#   * `deck-vb`, the self-adhered vapour barrier over the taped ZIP. ZIP is an air and water
#     barrier but only Class III for vapour, and the nailbase deck above is three times
#     tighter than it. The control layers all still live outboard of the structure, which is
#     the point: THE INTERIOR IS PAINT AND NOTHING ELSE, no ceiling poly, no smart membrane.
#   * `vent-mat`, the 1/4" ventilated underlayment mat under the metal. Not a furring strip
#     and not framing — the clips screw through it into the top deck. It is the only outward
#     drying path this roof has, and a roof under 0-perm metal with no drying path cannot
#     pass the gate at any foam thickness.
#
# The metal itself is unchanged: 24 ga mechanically field-seamed, hidden floating clips.
CATLIN_ROOF = Assembly(
    tag="CATLIN_ROOF",
    layers=(
        Layer(name="rafter", material_ref="spf", thickness=inch(11.875),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="11.875 I-joist", spacing=inch(16)),
              # ~R-55 whole-assembly, carried mostly by the 6" continuous exterior polyiso,
              # not the cavity batt. This is honestly R-55 and not the R-60 the target names:
              # the library rates polyiso at 5.6/in (a de-rated cold-climate value, not the
              # 6.0 on the label) and an R-19 batt is thinner and weaker than the 5.5"
              # mineral wool it replaced. Accepted on 2026-08-20 rather than papered over by
              # bumping the batt or re-rating the foam — the number that governs here is the
              # CI-to-total RATIO, and that went UP, which is what keeps the deck above dew
              # point. The 6.25" batt tight to the ceiling side leaves ~5.6" unfilled against
              # the ZIP deliberately: that unfilled depth is the condensation margin.
              cavity=CavityFill(material_ref="fiberglass-r19", thickness=inch(6.25),
                                framing_factor=0.07)),
        Layer(name="zip", material_ref="zip-sheathing", thickness=inch(0.5),
              function=LayerFunction.SHEATHING,
              control={ControlLayer.AIR, ControlLayer.WATER}),
        Layer(name="deck-vb", material_ref="roof-deck-vapor-barrier", thickness=inch(0.04),
              function=LayerFunction.MEMBRANE,
              control={ControlLayer.AIR, ControlLayer.VAPOR}),
        Layer(name="polyiso-1", material_ref="polyiso", thickness=inch(3.0),
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
        Layer(name="polyiso-2", material_ref="polyiso", thickness=inch(3.0),
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
        Layer(name="top-deck", material_ref="osb", thickness=inch(0.625),
              function=LayerFunction.SHEATHING),
        Layer(name="underlayment", material_ref="roof-underlayment-synthetic", thickness=inch(0.06),
              function=LayerFunction.MEMBRANE, control={ControlLayer.WATER}),
        Layer(name="vent-mat", material_ref="roof-vent-mat", thickness=inch(0.25),
              function=LayerFunction.AIRGAP),
        Layer(name="roofing", material_ref="standing-seam", thickness=inch(0.5),
              function=LayerFunction.CLADDING),
    ),
    default_lining=(
        _PAINT_FINISH,
        Layer(name="gwb-ceil", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
    ),
    source="catlin-house ifcplot/assemblies.py HOUSE_ROOF (hot roof, 4:12); vented batten cavity replaced by a screwed-down 5/8\" OSB top deck over two staggered 3\" polyiso courses 2026-08-20",
)

# --- concrete family -----------------------------------------------------------
#
# **The pour is not this house's to own.** It comes from library
# `FOUNDATION_WALL_8_XPS4_CORE` / `_12_XPS4_CORE` — the pour, damp-proofing and two
# staggered 2" XPS courses (R-21.8 either way; the concrete's R-0.08/in is noise) — and each
# wall below splats one of those cores and appends the one skin that covers the foam. What stays house-local is exactly that skin, because it is a colour and
# exposure decision: neither `foundation-protection-panel` nor `stucco` resolves in
# STARTER_MATERIALS, and the panel's #1c1f24 is the house's one exterior dark, which is a
# palette call that has no business going upstream.
#
# **The perimeter is two thicknesses and one rule, not one default.** 8" is earned only
# where a *cast concrete deck* lands on the wall top beside the sill plate and needs its own
# bearing seat inboard of it. A wood floor buys no extra width: the I-joists and their rim
# bear on the same 2x6 mudsill the framed wall above stands on, and an 8" wall carries that
# sill with 2" to spare — the conventional Minnesota wall. Since the 2026-08-21
# basement-ceiling overhaul the only cast deck left is SL-M-DECK (x 18'-36', y 13'-36',
# spanning east-west), which bears on the EAST wall and the centre line and nowhere else.
# So W-B-E1/E2 stay 12" and the west, north and south perimeter goes to 8".
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
# On N/E/W the foam is buried except for the 2'-10" band the 2026-08-18 lift and the
# 2026-08-21 deck overhaul raised out of the ground, so it gets a protection panel *over that
# band only* — below grade the backfill protects the XPS and above grade the panel does, and
# nothing is bought for the 6'-6" in between. That band is not a number in this file: the
# extent is authored off the GRADE datum, so the two lifts grew it (and its ~50 SF of panel)
# without anything here being edited.
#
# On the south the sunken garden exposes the foam from -9'-4" to 0'-0", which is not a band
# off grade at all — grade is above the garden floor by nine feet there — so that wall keeps
# the full-height parge coat, and keeps CATLIN_BASEMENT_8_GARDEN to say so.
#
# Both carry the same 4.55" outboard of the concrete face, which is what N-B-BRICK-W/-E's
# inch(-4.55) stand-off is measured from. That number now decomposes as 4.05" of library
# core outboard of the pour (0.05" damp-proof + 2x 2" XPS) plus 0.5" of house skin — the
# panel is deliberately the same 1/2" as the parge it replaces, so the stand-off never moves,
# and it is independent of the pour's thickness.

# The exposed-foundation band (2026-08-18, deeper since 2026-08-21). Runs from 6" *below*
# grade — so no foam edge shows at the soil line, and so the panel is what the shovel hits
# rather than the XPS — up to the top of the wall, where its head tucks under the
# rainscreen's Z-flashing with the bug screen above it. The wall top has been the bearing
# seat at -1'-1 7/16", not 0'-0", since the 2026-08-23 seat rework: the framed wall above
# now reaches back down to meet it (``resolve/platform.extend_walls_to_foundation``), so
# the two skins abut there rather than leaving the mudsill and rim bare. It replaces the
# full-height parge
# the N/E/W walls used to claim over nine feet of buried foam: the parge was added
# 2026-08-01 for the *south* wall's exposure and applied to all four sides because a layer
# had no way to say "only here".
_PROTECTION_PANEL = Layer(name="protection-panel",
                          material_ref="foundation-protection-panel",
                          thickness=inch(0.5), function=LayerFunction.CLADDING,
                          extent=LayerExtent(
                              bottom=LayerBound(datum=LayerDatum.GRADE, offset=inch(-6))))

# Parge coat over mesh (2026-08-01): exposed XPS degrades under UV/impact, and on the south
# the exposure runs the full wall from the sunken garden floor to the main-storey siding —
# bare pink foam was reading as the wall's finish. Reuses the porch railing's Portland-cement
# stucco; rides outboard of everything so the concrete face (the footings/damp-proofing/
# drain-tile datum) is untouched. Full height and staying that way: this face has no grade
# line on it to band against.
_GARDEN_PARGE = Layer(name="parge", material_ref="stucco", thickness=inch(0.5),
                      function=LayerFunction.FINISH)

# The east wall (W-B-E1/E2), the only perimeter run SL-M-DECK bears on.
CATLIN_BASEMENT_12 = Assembly(
    tag="CATLIN_BASEMENT_12",
    layers=(
        *FOUNDATION_WALL_12_XPS4_CORE,
        _PROTECTION_PANEL,
    ),
    interfaces=(_CONCRETE_BEARING,),
    source="library FOUNDATION_WALL_12_XPS4 + the house's above-grade protection panel (catlin basement east, where SL-M-DECK bears)",
)

# The west and north walls (W-B-W1/W2, W-B-N1/N2/N3) — wood floor only, so 8" reinforced.
CATLIN_BASEMENT_8 = Assembly(
    tag="CATLIN_BASEMENT_8",
    layers=(
        *FOUNDATION_WALL_8_XPS4_CORE,
        _PROTECTION_PANEL,
    ),
    interfaces=(_CONCRETE_BEARING,),
    source="library FOUNDATION_WALL_8_XPS4 + the house's above-grade protection panel (catlin basement west/north, wood floor only)",
)

# The south wall, which the sunken garden opens to the air over its whole 9'.
CATLIN_BASEMENT_8_GARDEN = Assembly(
    tag="CATLIN_BASEMENT_8_GARDEN",
    layers=(
        *FOUNDATION_WALL_8_XPS4_CORE,
        _GARDEN_PARGE,
    ),
    interfaces=(_CONCRETE_BEARING,),
    source="library FOUNDATION_WALL_8_XPS4 + the house's full-height parge over the sunken garden (catlin basement south)",
)

# Basement slab-on-grade: 3" XPS below the slab (R-15 @ 40 psi compressive — rated for
# slab loading, not the lighter foundation-wall grade) breaks direct slab-to-clay contact.
#
# The **poly and the stone under it were not modeled at all** until 2026-08-22, and their
# absence had exactly one voice anywhere in the toolchain: `sheet.foundation.vapour_retarder`
# fired UNKNOWN on the permit sheet — "no under-slab vapour retarder in the slab assembly" —
# where nobody reading `haus check` would ever meet it. So the UNDER-SLAB column of S-100
# read "3\" XPS" and stopped, and the takeoff ordered neither sheet nor stone.
#
# Order below the slab is the order it is built in, bottom last: concrete, then foam, then
# the retarder, then the base course. The retarder goes *under* the foam rather than between
# foam and slab — a sheet directly under a slab traps bleed water with nowhere to go and is
# the classic cause of curling; below the foam it still separates the slab from ground
# moisture and the slab can dry downward into the foam joints. (IRC R506.2.3 permits either;
# ACI 302.2R is where the preference comes from.)
CATLIN_SLAB_FLOOR = Assembly(
    tag="CATLIN_SLAB_FLOOR",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE),
        Layer(name="xps-below", material_ref="xps", thickness=inch(3.0),
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
        Layer(name="vapour-retarder", material_ref="polyethylene", thickness=inch(0.01),
              function=LayerFunction.MEMBRANE, control={ControlLayer.VAPOR}),
        Layer(name="capillary-break", material_ref="capillary-break-stone", thickness=inch(4.0),
              function=LayerFunction.SHEATHING),
    ),
    source="catlin-house basement slab: 3\" below-slab XPS, R-15 @ 40 psi compressive, over a 10-mil ASTM E1745 Class A vapour retarder on a 4\" open-graded capillary break (IRC R506.2.2/R506.2.3)",
)

# Main-floor structural deck: an EPS stay-in-place form with a cast concrete cap, over the
# (conditioned) basement — so it is an interior floor, not an envelope slab. The "INT" tag
# token is the codebase's signal for that (see FOUNDATION_WALL_12_INT, INT_2X6_PLUMBING) — it
# tells the prescriptive-energy table to skip this deck instead of holding it to the R-10
# slab minimum. Keep the token underscore-delimited: ``mn_energy._is_interior_assembly``
# keys on it and would otherwise grade a deck between two conditioned storeys against MN
# Zone 6's R-21.
#
# **This replaced a 1,233 SF x 9" cast suspended slab on 2026-08-21.** That slab was the
# single most expensive line in the model — 34.26 cy of concrete on shored plywood formwork
# whose commercial mobilisation floor alone was $25-40k — and it forced eight interior 12"
# concrete cross walls with strip footings under them, because it was designed to span
# between them. Concrete now goes only where it is wanted, under the dining radiant zone
# (x 18'-36', y 13'-36', 414 SF); the other 819 SF is wood I-joists on the same 18' span,
# and the two systems are interchangeable bay by bay because their depths match.
#
# The depth is the whole point. 4 5/8" cap + 8" form = 12 5/8", which is exactly the
# second floor's 11 7/8" joist (truss west of x=18', I-joist east — same depth either
# way) plus its 3/4" plywood subfloor: same soffit plane, same
# finished-floor plane, same 18' span to the x=18' bearing line. Both numbers are owned by
# ``params/main_deck.py`` (EPS_CAP / EPS_FORM_DEPTH), and the 10" form + 3" cap alternative
# — same depth class, ~21% less concrete, R-31 — is a one-line swap there.
#
# BuildDeck's published table takes an 8" form to a 20' clear span at a 4" cap with 4,000
# psi concrete and 60 ksi rebar under 15 psf dead + 40 psf live; the span here is 18'-0".
#
# Layers read top-down like CATLIN_SLAB_FLOOR. The gypsum is not optional trim: IRC R316.4
# requires a thermal barrier over foam plastic on the room side, and this is it.
CATLIN_DECK_EPS_INT = Assembly(
    tag="CATLIN_DECK_EPS_INT",
    layers=(
        Layer(name="concrete-cap", material_ref="concrete", thickness=inch(4.375),
              function=LayerFunction.STRUCTURE),
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
    interfaces=(_CONCRETE_BEARING,),
    source="catlin-house main-floor deck — LiteDeck 10\" EPS stay-in-place beam (8\" base panel + 2\" top hat) with a 4 3/8\" cast cover (14 3/8\" total, so the soffit lands on the same flat bearing seat as the wood bays' mudsill), steel furring rib and a 5/8\" gypsum R316.4 thermal barrier under it; replaced CATLIN_DECK_9_INT 2026-08-21, deepened 2026-08-23",
)

# Freestanding sunken-garden / porch / balcony structure — exposed concrete.
SUNKEN_GARDEN_WALL = Assembly(
    tag="SUNKEN_GARDEN_WALL",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(12.0),
              function=LayerFunction.STRUCTURE),
    ),
    interfaces=(_CONCRETE_BEARING,),
    source="catlin-house sunken_garden_retaining_wall_detail.py",
)

# PT-SG-FCOL, the 16" square cast column carrying the porch's front beams (it replaced a
# 16" arched cross-wall and a 42" masonry parapet).
#
# The assembly is required, not cosmetic. Without one, ``emit/draw/section.py::
# _solid_material`` sees a "column" whose size does not end in "round" and falls back to
# "spf" — a 16" pour would hatch as lumber in every section. One concrete STRUCTURE layer
# resolves it correctly in all three renderers (section hatch, glTF palette, the viewer's
# solidColor).
SUNKEN_GARDEN_COLUMN_16 = Assembly(
    tag="SUNKEN_GARDEN_COLUMN_16",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(16.0),
              function=LayerFunction.STRUCTURE),
    ),
    interfaces=(_CONCRETE_BEARING,),
    # (single literal: the editable dialect forbids concatenated strings)
    source="catlin-house porch front column — 16\" square cast concrete, 3/4\" chamfered arrises, >=15 degree top wash with a >=1\" drip lip (BIA Tech Note 36A), beam bearing on a level non-shrink-grout island (Five Star TB-411: 45 degree shoulders, shoulder width <= grout depth, <= 3\"); 4,000-4,500 psi, w/cm <= 0.45, 6.0-6.5% air at 3/4\" aggregate (Minn. R. 1309.0402 + ACI 318-19 class F2); broom or float finish, never steel-trowelled (NRMCA CIP 2); silane/siloxane repellent",
)

# Glazed-brick veneer over the exposed basement wall (sunken garden excavated against it).
# There is no CMU backer wythe here, because the existing CATLIN_BASEMENT_8_GARDEN concrete
# (damp-proofing + 4" XPS + parge already outboard) IS the backer — this wall stands 1" off
# it on masonry ties. A fictional backer would double-count concrete already modeled by
# W-B-S2/W-B-S3. No `interfaces`: non-bearing.
#
# **The Ishtar scheme (2026-08-20).** The wythe was one flat field of glazed-green-brick
# until the green — liked on its own — was judged not to sit with a house of white standing
# seam, #1c1f24 trim and arched concrete garden walls. It now reads as the Ishtar Gate of
# Babylon: a lapis field with golden-yellow register bands over an unglazed brown plinth.
# `glazed-green-brick` is still in the catalog, unreferenced, so reverting is one word.
#
# All five brick regions are ONE row of the stack — `slot="wythe"` — so they share a single
# 3 5/8" depth position between them instead of taking one each. Without the slot this
# assembly would resolve to a 18 1/8" wythe and shove the whole wall into the garden.
# Every region carries the same thickness and its own band off WALL_BASE (one datum
# throughout, so `integrity.assembly_layers` can actually compare them), and the bands do
# not overlap.
#
# Band heights are on the 2 2/3" modular course, measured off the wall's own base
# (-8'-5", not -9'-0" — see the note on W-B-BRICK in plan/storeys/basement.py). The wall is
# 8'-5" tall, so `brick-field-hi` takes the partial top course. The upper register sits ON
# D-B-PATIO's head line at 88", which is the Ishtar reading — the band runs across the top of
# the opening rather than floating above it. The brick reveal AO-B-BRICK-DOOR crowns 10" under
# that band (2026-08-21): it was first cut to 88" so the band sprang straight off the crown,
# and with no course between them the arch read as sawn off. The lower register caps the
# plinth and crosses the door's foot.
#
# The plinth grew from 9 courses to 12 on 2026-08-21 and the lower register rode up 8" with
# it, out of the lapis field's 22 courses (now 19). The upper register and the door head do
# not move. The whole shift is three courses exactly, so AO-B-BRICK-WIN went up 8" too
# (sill 29" -> 37", head 49" -> 57") and keeps the same 1/3" foot in the register and the
# same clear run of lapis above it; the sauna window it reveals moved with it.
#
# STRUCTURE, not CLADDING, on every region: this wythe has nothing behind it in this
# assembly (the backer is a *different wall*), so it has to be the structure layer or
# integrity.assembly_layers finds none. Same precedent as RETAINING_BLOCK_12.
#
# Every band is measured LINE_BASE, not WALL_BASE, and that is the whole point of the
# datum: a 2 2/3" modular course is a property of the *building*, not of whichever wall
# happens to carry it, so stacking a second wall on this line has to continue the coursing
# rather than restart it at the storey datum. W-B-BRICK is a single-wall line today, so
# ``base_z_m == z0_m`` and every region resolves to exactly the elevation it did as
# WALL_BASE — the conversion is a no-op on this house and a promise about the next one.
_VENEER_WYTHE = inch(3.625)
BASEMENT_BRICK_VENEER = Assembly(
    tag="BASEMENT_BRICK_VENEER",
    layers=(
        Layer(name="air-gap", material_ref="air-barrier", thickness=inch(1.0),
              function=LayerFunction.AIRGAP),
        # 12 courses of ordinary unglazed brown brick — the cheapest face on the wall, and
        # the one the wall stands out of the ground on. Was 9 courses / 24" until
        # 2026-08-21, when the plinth took three courses off the lapis field above it:
        # brown is the cheap brick, so the cheap band is the one that grows.
        Layer(name="brick-plinth", material_ref="brown-brick", thickness=_VENEER_WYTHE,
              function=LayerFunction.STRUCTURE, slot="wythe",
              extent=LayerExtent(
                  bottom=LayerBound(datum=LayerDatum.LINE_BASE, offset=inch(0.0)),
                  top=LayerBound(datum=LayerDatum.LINE_BASE, offset=inch(32.0)))),
        # 2 courses of gold capping the plinth — the same two courses, carried up 8" with it.
        Layer(name="brick-band-lo", material_ref="glazed-gold-brick", thickness=_VENEER_WYTHE,
              function=LayerFunction.STRUCTURE, slot="wythe",
              extent=LayerExtent(
                  bottom=LayerBound(datum=LayerDatum.LINE_BASE, offset=inch(32.0)),
                  top=LayerBound(datum=LayerDatum.LINE_BASE, offset=inch(37.333)))),
        # The field: 19 courses of lapis, plinth cap to door head. It gives up the three
        # courses the plinth gained; the door head at 88" does not move.
        Layer(name="brick-field-lo", material_ref="glazed-lapis-brick",
              thickness=_VENEER_WYTHE,
              function=LayerFunction.STRUCTURE, slot="wythe",
              extent=LayerExtent(
                  bottom=LayerBound(datum=LayerDatum.LINE_BASE, offset=inch(37.333)),
                  top=LayerBound(datum=LayerDatum.LINE_BASE, offset=inch(88.0)))),
        # 2 courses of gold on the door head line, springing off the arch crown.
        Layer(name="brick-band-hi", material_ref="glazed-gold-brick", thickness=_VENEER_WYTHE,
              function=LayerFunction.STRUCTURE, slot="wythe",
              extent=LayerExtent(
                  bottom=LayerBound(datum=LayerDatum.LINE_BASE, offset=inch(88.0)),
                  top=LayerBound(datum=LayerDatum.LINE_BASE, offset=inch(93.333)))),
        # The lapis cap above the upper register. Open top on purpose: `top=None` is the
        # wall's own top, which is the only way to say "run it out" without writing this
        # wall's 8'-9" into an assembly type that any wall may use.
        Layer(name="brick-field-hi", material_ref="glazed-lapis-brick",
              thickness=_VENEER_WYTHE,
              function=LayerFunction.STRUCTURE, slot="wythe",
              extent=LayerExtent(
                  bottom=LayerBound(datum=LayerDatum.LINE_BASE, offset=inch(93.333)))),
    ),
    source="basement south veneer over the sunken garden — the Ishtar scheme (2026-08-20): lapis glazed field with golden-yellow register bands over an unglazed brown plinth, one 3 5/8\" wythe banded by Layer.slot, 1\" airgap, corrugated masonry ties back to the existing CATLIN_BASEMENT_8_GARDEN wall (no CMU backer: the basement concrete is the backer). Was one flat field of glazed-green-brick, which is still in the catalog for a one-word revert",
)

# Raised-garden outer face: dry-stacked segmental retaining-wall block, one unit deep. No
# core fill and no rebar — an SRW wall of this height is held by unit weight, batter and
# the granular backfill behind it, which is exactly why it is the *outer* face here while
# the sunken-garden retaining wall (cast concrete) takes the inner one.
RETAINING_BLOCK_12 = Assembly(
    tag="RETAINING_BLOCK_12",
    layers=(
        Layer(name="srw-block", material_ref="retaining-block", thickness=inch(12.0),
              function=LayerFunction.STRUCTURE,
              masonry=MasonrySpec(unit_size="12x6x18 SRW block", coursing=inch(6.0),
                                  core_fill=False)),
    ),
    source="raised garden (brief.md follow-up) — outer face, dry-stacked SRW units",
)

# Deck walking surfaces (single-layer). The joists/beams under them are separate framing
# members; these are just the finished plank surface so the slab reads with the right
# material in plans/IFC.
PORCH_DECK_COMPOSITE = Assembly(
    tag="PORCH_DECK_COMPOSITE",
    layers=(
        # The plank is the spanning walking surface (STRUCTURE); the 2x8 joists beneath it
        # are separate framing members.
        Layer(name="composite-deck", material_ref="composite-deck", thickness=inch(1.0),
              function=LayerFunction.STRUCTURE),
    ),
    source="catlin-house porch floor — composite decking on PT 2x8 joists",
)

# --- breezeway enclosure -------------------------------------------------------
# Two glazing assemblies, deliberately without insulation, membrane or deck layers: the
# breezeway is an unheated shelter between two heated buildings, so its envelope only sheds
# water/cuts wind and must not fall inside an energy check. Single-layer sheet assemblies
# because the sheet *is* the whole construction — the 2x6 rafters are real Beams
# (params/breezeway.py, on their own drainage-wedge elevations) rather than a framing layer
# here, so a rafter layer would frame nothing and would mislabel the polycarbonate "spf" in
# every consumer that reads an assembly's structure layer (GLB colour, viewer, cut detail).
BREEZEWAY_ROOF_GLAZING = Assembly(
    tag="BREEZEWAY_ROOF_GLAZING",
    layers=(
        Layer(name="glazing", material_ref="polycarbonate-multiwall", thickness=inch(0.63),
              function=LayerFunction.STRUCTURE),
    ),
    source="breezeway roof — two 4'x4' pieces of one 16mm 5-wall sheet on drainage wedges over 2x6 rafters",
)

# The east and west walls: one 4'x8' sheet each, standing in a U-channel at the deck and an
# F-channel at the beam, with no framing of its own — the 6x6 posts either end are the frame.
# The sheet is STRUCTURE here, not CLADDING: it is the whole wall and it spans the 4'-0"
# between those posts unaided, exactly as PORCH_DECK_COMPOSITE's single plank layer is the
# spanning walking surface. On the roof, where 2x6 rafters do the spanning, it is cladding.
BREEZEWAY_GLAZED_WALL = Assembly(
    tag="BREEZEWAY_GLAZED_WALL",
    layers=(
        Layer(name="glazing", material_ref="polycarbonate-multiwall", thickness=inch(0.63),
              function=LayerFunction.STRUCTURE),
    ),
    source="breezeway side walls — one 4'x8' 16mm multiwall sheet per side, bird-safety film",
)

BALCONY_DECK_ALUMINUM = Assembly(
    tag="BALCONY_DECK_ALUMINUM",
    layers=(
        Layer(name="aluminum-deck", material_ref="aluminum-deck", thickness=inch(1.5),
              function=LayerFunction.STRUCTURE),
    ),
    source="catlin-house balcony — Wahoo AridDeck-style aluminum plank on 2x8 joists",
)

# Finish-only assembly for the balcony 6x6 pillars so they render (glTF) and read (IFC) as
# white-painted rather than the default bare-wood post colour. Single 5.5" layer = the 6x6.
POST_WHITE_PAINT = Assembly(
    tag="POST_WHITE_PAINT",
    layers=(
        Layer(name="post-paint-white", material_ref="post-paint-white", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE),
    ),
    source="catlin-house balcony 6x6 pillars — white-painted finish",
)

# Guards were split off POST_WHITE_PAINT on 2026-08-01 (they shared it with the balcony's
# 6x6 pillars/knee braces, which must stay white) — same 5.5" body, only the colour differs.
# Metal, not painted PT: `_solid_color` reads the STRUCTURE layer's material, so
# metal-dark-exterior here is what darkens the railings in both renderers.
# The suite bedroom's four elm tudor posts (plans/TODO.md §Hardwood): same pattern as
# POST_WHITE_PAINT — the STRUCTURE material colours the solid and names the species for the
# wood_surfaces takeoff. 6.125" body = the custom timber, sheathing to drywall face, a
# deviation within W-S-W3's stud line, deliberately not a change to CATLIN_EXT_2X6.
ELM_TIMBER = Assembly(
    tag="ELM_TIMBER",
    layers=(
        Layer(name="elm-timber", material_ref="elm-timber", thickness=inch(6.125),
              function=LayerFunction.STRUCTURE),
    ),
    source="plans/TODO.md — suite tudor posts, elm 6-1/8\" square",
)

# --- structural members that are NOT concrete (2026-08-22) --------------------
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
# from was never buyable treated. All seven went to 3-ply KDAT sawn stock on 2026-08-23 and
# are on BEAM_KDAT now (see params/sunken_garden.py).
BEAM_LVL = Assembly(
    tag="BEAM_LVL",
    layers=(
        Layer(name="lvl", material_ref="lvl", thickness=inch(1.75),
              function=LayerFunction.STRUCTURE),
    ),
    source="catlin-house LVL beams — 1-3/4\" plies, built up 3 wide per Beam.size; interior only (the two dropped hall girders), so untreated LVL is the right product",
)

# Every treated sawn member in the house's outdoor frame. The breezeway (four 2-2x8 floor
# and roof beams, three 2x6 rafters) is where it started; the balcony's four E-W girts
# joined it, and on 2026-08-23 so did the sunken garden's seven beams, which had been on
# BEAM_LVL claiming a treatment LVL is not sold in.
#
# All of it stands in weather over open ground with no enclosure above it, so every stick is
# treated — and KDAT rather than plain PT, because a wet-treated deck frame shrinks and cups
# through its first season and backs its own fasteners out doing it.
BEAM_KDAT = Assembly(
    tag="BEAM_KDAT",
    layers=(
        Layer(name="kdat", material_ref="kdat", thickness=inch(1.5),
              function=LayerFunction.STRUCTURE),
    ),
    source="catlin-house KDAT 2x framing — ply count per Beam.size: the breezeway frame (2-2x8 beams, single 2x6 rafters), the balcony's four E-W girts (2x10), and since 2026-08-23 the sunken garden's seven beams (3-2x12 porch, 3-2x10 balcony)",
)

# The breezeway's four 6x6 posts. NOT POST_WHITE_PAINT: that assembly is white-painted and
# is shared with the balcony pillars and the stairwell posts, which stay white (CLAUDE.md,
# "One exterior dark"), so pointing these at it would either recolour six pillars or claim a
# paint finish nobody is applying. These are bare KDAT 6x6 with a clear water repellent —
# the breezeway reads as structure, not as trim. 5.5" is the true 6x6 section, matching
# POST_WHITE_PAINT's body.
POST_KDAT = Assembly(
    tag="POST_KDAT",
    layers=(
        Layer(name="kdat-post", material_ref="kdat", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE),
    ),
    source="catlin-house breezeway 6x6 posts — ground-contact-rated KDAT, left unpainted with a clear water repellent",
)

# The 12" sonotube piers: PR-BW-1..4 under the breezeway posts and PT-SG-COL at the garden
# back-beam midspan. Every one of the five is a round cast pier, and `solid_material_ref`
# already reads "12 round" as concrete for the section hatch — but only for the hatch. The
# assembly is what puts `structure_material="concrete"` on the BOM row so the [concrete]
# price table's material guard admits it, which is the difference between the pier billing
# at ready-mix and the pier billing at whatever rate the bare "column" key happened to hold.
PIER_CONCRETE_12 = Assembly(
    tag="PIER_CONCRETE_12",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(12.0),
              function=LayerFunction.STRUCTURE),
    ),
    interfaces=(_CONCRETE_BEARING,),
    source="catlin-house 12\" round sonotube piers — cast in a fibre form on a spread pad, stripped to the form line; 4,000 psi, 6.0-6.5% air (Minn. R. 1309.0402, ACI 318-19 class F2)",
)

RAILING_DARK_METAL = Assembly(
    tag="RAILING_DARK_METAL",
    layers=(
        Layer(name="rail-metal", material_ref="metal-dark-exterior", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE),
    ),
    source="catlin-house guards — near-black painted metal, the house's one exterior dark",
)

# --- garage (freestanding: ICF stem + 2x6 wood wall) ---------------------------
# The form's two published dimensions, as constants rather than literals inside the layer
# stack: params/foundations.py aligns the stem off the EPS thickness (the exterior foam
# face has to land on the same node line the wood wall's zip-R face uses) and insets the
# slab off the whole 11" section. Repeating either number there would let the two drift.
#
# Reconciled against library GARAGE_ICF on 2026-08-22 (CONTRIBUTING "do NOT duplicate" —
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
# with, banded from grade up — 2026-08-22, and it is `code.R316_4` that asked for it. The
# ICF's interior EPS stood bare inside the garage from the slab (poured at grade) to the
# stem top 1'-10" above it, ~176 SF of exposed foam plastic facing an occupied space with
# no thermal barrier over it. R316.4 wants 1/2" gypsum, 5/8" wood structural panel or an
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
              function=LayerFunction.STRUCTURE,
              masonry=MasonrySpec(unit_size="ICF-6", core_fill=True,
                                  rebar_spacing=inch(16))),
        Layer(name="eps-ext", material_ref="icf-eps", thickness=GARAGE_ICF_EPS,
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
    ),
    source="library GARAGE_ICF's 6\" concrete core (ICF-6, matching masonry spec) + this house's 2.5\" EPS facing (thinner than library's 2.625\" generic default) and gwb-stem interior banding above grade (code.R316_4)",
)

# --- garage east/south/north brick wainscot (2026-08-26; Roman Maximus 2026-08-26) -------
#
# The two 4'-0" strips of east wall flanking the overhead door, plus a 4'-0" return around
# each of the SE and NE corners, carry a short off-white-brick wainscot: the most-abused surface
# on the building (apron splash, snow piled off the drive, trimmers, car doors) gets the one
# face that does not care. Full 3 5/8" brick, not thin brick, which means real bearing —
# hence the ledge below and the veneer wall in plan/storeys/garage.py rather than a
# WallPaneling band (a band carries neither a wythe thickness nor an air gap, and the
# wood-surfaces rollup only bills materials with a `species`, so a brick band would produce
# no BOM line at all).
#
# Glen-Gery "Columbia Roman Maximus" (glengery.com/brick-catalog/columbia-roman-maximus),
# swapped in 2026-08-26 for the black colourway of the same unit: 3 5/8" x 1 5/8" x 23 5/8",
# ASTM C216 Grade SW Type FBA. The bed depth (3 5/8") is the same as a modular unit, so the
# wythe thickness, air gap, ledge width and every tie/flashing dimension below are
# UNCHANGED from the original buff-modular spec — only the coursing (unit height 1 5/8" +
# 3/8" joint = 2" per course, not 2 2/3") and the unit length/color change. Columbia and
# Black are the same body/size/ASTM grade, an off-white vs. black glaze only, so nothing
# below this comment (ledge rise, ledge depth, or the coursing table) moves for the swap —
# only the Material's `color`/`source` and the renderer's `finish` recipe. `finish=
# "roman-maximus-brick"` on the Material tells the renderer's masonry recipe about the unit
# geometry (an elongated unit); the colourway itself lives in the style's `base` colour
# (ui/src/three/materials.ts) and the palette's `_FINISH_BASE` entry (emit/gltf/palette.py).
#
# Coursing, Roman 2", working up from grade (-2'-10"):
#     ledge/shelf top   2" above grade       (-2'-8")
#     20 courses field  40"                  (+0'-8")
#     rowlock cap       4" (unit bed depth, unaffected by the coursing change)
#     metal cap flash   2"                   (+1'-2" == 4'-0" above grade, on the nose)
# The shelf sits one course module ABOVE finish grade rather than at it — the cheapest
# durability move available in a 40+ freeze-thaw-cycle climate, lifting the base course
# clear of the worst splash and snow-contact zone. The wall height (ledge top to brick top,
# 44") and the cap top (4'-0" above grade, on the nose) are both unchanged from the original
# modular scheme — only the internal course count and the cap flashing's face height moved,
# to keep both anchors exact with a 2" module instead of a 2 2/3" one.
GARAGE_BRICK_LEDGE_RISE = inch(2.0)  # one Roman course; shelf top above grade
# 1" air space (IRC R703.8 minimum) + a 3 5/8" wythe: how far east of the node line the
# bearing shelf has to project. Below the shelf the concrete section widens from 11" to
# ~15 5/8" — all of it below grade and backfilled, so none of it is visible.
GARAGE_BRICK_LEDGE = inch(4.625)

# GARAGE_ICF_6 with a brick ledge appended as one extra OUTERMOST layer. Brick-ledge ICF
# forms are catalog items for 6" and 8" cores (Amvic, Nudura, Alliance), and the ICF Brick
# Ledge Extension is rated for "any height, angle and side of an ICF wall"; ours lands near
# grade, well below the top of the stack — the easy case. A 4' welded-wire reinforcer
# dropped into the ledge is the standard way to develop it.
#
# OUTERMOST is not a style choice, it is the only thing that works. A banded layer with no
# `slot` still occupies its full depth over the whole wall (see model/assembly.py's note on
# `extent`): a general stepped section — thicker core below, thinner above — is not
# expressible, because a stack whose total thickness varies with elevation is not something
# `Wall.alignment` can answer. As the LAST layer nothing outboard of it is displaced, and
# params/foundations.py's `face("concrete-ext", offset=GARAGE_ICF_EPS)` measures from the
# INTERIOR, so `_ALIGN` is unchanged and the ledge grows east exactly as wanted.
#
# NOT a `slot`: every member of a slot must carry the same thickness
# (integrity.assembly_layers), so a slot cannot express a 4 5/8" step against an 11" wall
# and would only add a finding.
#
# The band top is the GRADE datum, not a literal elevation — the same mechanism the
# `gwb-stem` layer already uses, so the ledge tracks `Site.grade` and follows the next grade
# lift instead of silently detaching from it. Everything above the ledge is GARAGE_ICF_6
# restated verbatim; above the shelf this is the same wall.
GARAGE_ICF_6_BRICKLEDGE = Assembly(
    tag="GARAGE_ICF_6_BRICKLEDGE",
    layers=(
        Layer(name="gwb-stem", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH,
              extent=LayerExtent(bottom=LayerBound(datum=LayerDatum.GRADE))),
        Layer(name="eps-int", material_ref="icf-eps", thickness=GARAGE_ICF_EPS,
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
        Layer(name="concrete", material_ref="concrete", thickness=GARAGE_ICF_CORE,
              function=LayerFunction.STRUCTURE,
              masonry=MasonrySpec(unit_size="ICF-6", core_fill=True,
                                  rebar_spacing=inch(16))),
        Layer(name="eps-ext", material_ref="icf-eps", thickness=GARAGE_ICF_EPS,
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
        Layer(name="brick-ledge", material_ref="concrete", thickness=GARAGE_BRICK_LEDGE,
              function=LayerFunction.STRUCTURE,
              extent=LayerExtent(bottom=LayerBound(datum=LayerDatum.WALL_BASE),
                                 top=LayerBound(datum=LayerDatum.GRADE,
                                                offset=GARAGE_BRICK_LEDGE_RISE))),
    ),
    source="GARAGE_ICF_6 + a mid-stack ICF brick-ledge form (Amvic/Nudura/Alliance brick-ledge block, or the ICF Brick Ledge Extension rated for any height) carrying the east wainscot's 3 5/8\" wythe on a shelf one modular course above grade; 4' welded-wire reinforcer in the ledge; ledge and the widened section below it are backfilled and not visible",
)

# The wainscot itself: a short veneer wall standing in front of the existing stem/wood wall,
# exactly W-B-BRICK's precedent (plan/storeys/basement.py). ONE flat field, no `slot`-banded
# courses — BASEMENT_BRICK_VENEER's banding exists to serve the Ishtar scheme; this wall is
# one brick, and the rowlock cap is a separate element, not a band.
#
# STRUCTURE, not CLADDING, on the wythe — the same reason BASEMENT_BRICK_VENEER gives, and
# RETAINING_BLOCK_12's precedent: this wythe has nothing behind it IN THIS ASSEMBLY (the
# backer is a different wall), so it has to be the structure layer or
# integrity.assembly_layers finds none.
#
# The detailing that keeps this alive is in the veneer wall's own notes and the house
# CLAUDE.md: through-wall flashing + weeps at the base course on the ledge, a second
# through-wall flashing under the cap, and ties that DIFFER BY BACKING — the storey datum is
# -1'-0", so ~19 3/8" of brick backs onto the ICF stem and ~24 5/8" onto the wood wall above
# it. Corrugated ties are only valid where the brick back is within 1" of framing, and
# across the zip-R it is not: screw-on adjustable two-piece ties above the datum
# (IRC R703.8.4).
GARAGE_BRICK_WAINSCOT = Assembly(
    tag="GARAGE_BRICK_WAINSCOT",
    layers=(
        Layer(name="air-gap", material_ref="air-barrier", thickness=inch(1.0),
              function=LayerFunction.AIRGAP),
        Layer(name="brick", material_ref="off-white-brick", thickness=inch(3.625),
              function=LayerFunction.STRUCTURE),
    ),
    source="garage east wainscot flanking the overhead door, wrapped 4' around each of the SE/NE corners onto the south and north walls — full-wythe Glen-Gery Columbia Roman Maximus face brick (3 5/8\" bed, ASTM C216 Grade SW Type FBA) on a 1\" drained cavity (IRC R703.8), borne on GARAGE_ICF_6_BRICKLEDGE's shelf; through-wall flashing + weeps at 33\" o.c. max at the base course and again under the cap; two-piece adjustable ties into studs above the storey datum, ICF ties below",
)

# --- frost-protected shallow foundation, sunken-garden side -----------------------------
#
# The condition, measured 2026-08-22: the sunken garden's floor is at -9'-4", the south house
# strips FT-B-S1/S2/S3 bottom out at -10'-0", and the glazed-brick plinth FT-B-BRICK bottoms
# at -9'-2" — 8" of cover, and 2" of *negative* cover, against MN Rules 1303.1600's 42" for
# Ramsey County (Zone II). Frost depth is measured from the LOWEST ADJACENT grade (IRC
# R403.1.4.1), and beside those footings that is the garden floor, not the -2'-10" site
# grade plane. Nothing said so because `structural.frost_depth` compared every footing to one
# global scalar and therefore passed all 35, negative cover included; it derives a local grade
# per footing since the same date, and names these four.
#
# The answer is R403.3 — a frost-protected shallow foundation — under **Figure R403.3(3)**
# specifically: a heated building adjoining a slab-on-ground that is *not* maintained at
# 64 deg F, which is exactly a heated basement beside an open sunken court. Deepening the
# strips is the alternative and it is not available: FT-B-BRICK's whole derivation leans on
# FT-B-S2/S3's 10" south toe being there to bear on (params/foundations.py), so re-centring
# the strips and re-footing the brick wall are one change, and not this one.
#
# Design air-freezing index **AFI 2500** (Minneapolis-St Paul; MN Rules 1303.1600 and the
# IRC's own Figure R403.3(2) put the Twin Cities near 2,500 F-days). Table R403.3(1) at
# AFI 2500 asks for:
#
#     vertical            R-6.7
#     horizontal, walls   R-1.7        dimension B = 24"
#     horizontal, corners R-4.9        dimension C = 40"
#
# The **vertical leg is already built**: the south basement walls compose off
# FOUNDATION_WALL_8_XPS4_CORE, 4" of XPS = R-20 against the table's R-6.7, and
# CATLIN_BASEMENT_8_GARDEN carries that face full height precisely because the garden exposes
# it from -9'-0" to 0'-0". Only the horizontal band is new.
#
# Both wings are specified far over the table rather than at it. R-5 and R-10 against R-1.7
# and R-4.9 is not generosity: 1" is the thinnest XPS anyone stocks, the labour and the
# excavation are identical at either thickness, and a band sitting exactly on a table minimum
# has nothing left if the design AFI is revised upward. 40 psi, the same slab-bearing grade
# as CATLIN_SLAB_FLOOR's, because the garden slab is cast on top of it.
SG_FROST_WING_XPS1 = Assembly(
    tag="SG_FROST_WING_XPS1",
    role="band",
    layers=(
        Layer(name="xps-wing", material_ref="xps", thickness=inch(1.0),
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
    ),
    source="IRC R403.3 Figure R403.3(3) horizontal wing along the wall, Table R403.3(1) at AFI 2500: R-1.7 required over dimension B = 24\"; 1\" XPS at 40 psi is R-5",
)

SG_FROST_WING_XPS2 = Assembly(
    tag="SG_FROST_WING_XPS2",
    role="band",
    layers=(
        Layer(name="xps-wing", material_ref="xps", thickness=inch(2.0),
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
    ),
    source="IRC R403.3 Figure R403.3(3) horizontal wing at a corner, Table R403.3(1) at AFI 2500: R-4.9 required over dimension C = 40\"; 2\" XPS at 40 psi is R-10",
)

# The footings the wings protect, bearing on load-rated insulation rather than on soil.
#
# IRC R403.3 sends a frost-protected shallow foundation to **ASCE 32**, and ASCE 32 is where
# insulation *beneath* a footing comes from — it is the Scandinavian FPSF detail, not an
# improvisation. The arithmetic is the part worth writing down: a 20" strip under a
# residential basement wall delivers on the order of 1,500-2,000 psf to the bearing plane,
# i.e. **10-14 psi**, against 40 psi XPS. The foam is loaded to roughly a third of its rated
# compressive strength at 10% deformation, and creep at that ratio is what the rating exists
# to bound. Same board, same grade, as the 3" under CATLIN_SLAB_FLOOR.
#
# The wall bears on concrete, not on foam: the insulation is the bottom layer and the top of
# the strip is the pour. The vertical faces of the form are insulated too in the built
# detail — that is what makes it an insulated *form* — and this stack cannot say so, because
# a ``Footing``'s layers run depth-wise through a horizontal element and there is no sideways
# axis in them. The wings (SG_FROST_WING_XPS1/2) are the horizontal leg and the basement
# wall's own 4" XPS is the vertical one, so the two legs Table R403.3(1) actually grades are
# both modelled; the form's side foam is detail, not a graded quantity.
FOOTING_FPSF_20 = Assembly(
    tag="FOOTING_FPSF_20",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(8.0),
              function=LayerFunction.STRUCTURE),
        Layer(name="xps-bearing", material_ref="xps", thickness=inch(2.0),
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
    ),
    source="frost-protected shallow footing at the sunken-garden face: 8\" cast strip bearing on 2\" XPS at 40 psi (IRC R403.3 -> ASCE 32; ~10-14 psi imposed against a 40 psi board), with the horizontal wings SG_FROST_WING_XPS1/2 under the garden slab beside it",
)

GARAGE_WALL_2X6 = Assembly(
    tag="GARAGE_WALL_2X6",
    layers=(
        # NO CAVITY INSULATION, and that is a decision rather than an omission (owner,
        # 2026-08-20). The garage is detached and unheated; the 1.5" Zip-R's continuous
        # R-6.6 is all the thermal layer the walls get, and the empty 2x6 bays are left
        # open. Walls only: the garage ceiling is insulated separately and is untouched
        # by this.
        Layer(name="stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x6", sill_gasket=inch(0.0625))),
        Layer(name="zip-r", material_ref="zip-r", thickness=inch(1.5),
              function=LayerFunction.SHEATHING,
              control={ControlLayer.AIR, ControlLayer.WATER, ControlLayer.THERMAL}),
        # NO RAINSCREEN FURRING, and that is a decision rather than an omission
        # (owner, 2026-08-20). Nail strip is face-fastened through an integral flange, and
        # Zip-R's integrated WRB is a taped, drainable face rated for direct cladding
        # attachment — so the panel goes straight onto the sheathing and the 3/8" 1x4
        # vertical furring that used to sit here is gone. This is the cost-options
        # "Garage: rainscreen-drop downgrade" entry, taken. It is a GARAGE-only move:
        # CATLIN_EXT_2X6 keeps its furring, because there the cladding has to be held off
        # 4" of exterior foam and has no sheathing face to bear on.
        Layer(name="cladding", material_ref="standing-seam-nailstrip-26", thickness=inch(0.5),
              function=LayerFunction.CLADDING),
    ),
    default_lining=_GWB_LINING,
    source="catlin-house ifcplot/assemblies.py GARAGE_WALL; rainscreen furring dropped and cavity batts dropped 2026-08-20 (Zip-R is the whole wall thermal layer)",
)

# Garage slab-on-grade. It now carries the same 3" of below-slab XPS as CATLIN_SLAB_FLOOR —
# the owner wants the garage floor insulated even though the structure is detached and
# unheated, so the choice is authored here rather than inferred from "is it conditioned".
# Still a separate assembly from the basement slab: this one keeps the 1" perimeter thermal
# break at the slab edge, and the two are ordered and poured as different scopes.
GARAGE_SLAB_ON_GRADE = Assembly(
    tag="GARAGE_SLAB_ON_GRADE",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE),
        Layer(name="xps-below", material_ref="xps", thickness=inch(3.0),
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
        # Same stack, same reasoning, as CATLIN_SLAB_FLOOR above. R506.2.3 exempts a garage
        # from the vapour retarder; the foam does not care and the stone under it is
        # required either way, and a garage floor with 3" of XPS under it is being asked to
        # stay dry for the same reason a basement floor is.
        Layer(name="vapour-retarder", material_ref="polyethylene", thickness=inch(0.01),
              function=LayerFunction.MEMBRANE, control={ControlLayer.VAPOR}),
        Layer(name="capillary-break", material_ref="capillary-break-stone", thickness=inch(4.0),
              function=LayerFunction.SHEATHING),
    ),
    source="catlin-house detached garage floor — 3\" below-slab XPS over a 10-mil ASTM E1745 Class A vapour retarder on a 4\" open-graded capillary break (IRC R506.2.2)",
)

# REMOVED 2026-08-22: GARAGE_STEP_CONCRETE, 6" plain concrete on compacted base. It was the
# assembly of SL-G-STEP-1..4, the four treads of the garage service step-down, and those are
# a real `Stair` now (ST-G-SERVICE in plan/storeys/garage.py) in pressure-treated KDAT rather
# than concrete. SL-G-STEP-0 survives as the 3'-0" landing at the threshold, pours with the
# slab, and names no assembly of its own.

GARAGE_ROOF = Assembly(
    tag="GARAGE_ROOF",
    layers=(
        # Raised-heel trusses (2x4 chords + webs) with a 9.25" energy heel so full
        # insulation depth carries over the top plate; the truss carries the ridge, so no
        # ridge beam is required. `haus` frames the chords/webs/heel as first-class members.
        #
        # The fill is loose-fill fiberglass blown onto the ceiling plane, 14.5" settled —
        # R-38 nominal (owner, 2026-08-20). The 9.25" energy heel is the FLOOR of that
        # depth, not the ceiling: the heel is what guarantees full depth survives over the
        # top plate instead of pinching to nothing at the eave, and the blow runs deeper
        # than the heel across the field, tapering into it at the last bay. That is why
        # 14.5" is thicker than this layer's own 11.875" — the fill lies on the bottom
        # chord in a vented attic void that is far deeper than 14.5" anywhere but the very
        # eave, so it is not bounded by the structural depth the way a stud-bay batt is.
        # Nothing moves geometrically: a CavityFill adds no thickness to the stack
        # (→ CavityFill), it is a parallel thermal path with the chords, not a series one.
        # The attic above it is the vent void the PVC soffit feeds (ROOFS in
        # storeys/garage.py). framing_factor is the 2x4 bottom chord at the solver's 16"
        # o.c. (1.5/16); the blow buries the chords, so this is the conservative reading
        # of the bridge.
        Layer(name="truss", material_ref="spf", thickness=inch(11.875),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x4", roof_frame="truss",
                                  heel_height=inch(9.25),
                                  chord_member="2x4", web_member="2x4"),
              cavity=CavityFill(material_ref="blown-fiberglass", thickness=inch(14.5),
                                framing_factor=0.09)),
        Layer(name="deck", material_ref="struct-1-plywood", thickness=inch(0.75),
              function=LayerFunction.SHEATHING),
        Layer(name="membrane", material_ref="air-barrier", thickness=inch(0.02),
              function=LayerFunction.MEMBRANE,
              control={ControlLayer.AIR, ControlLayer.WATER}),
        Layer(name="roofing", material_ref="standing-seam-nailstrip", thickness=inch(0.5),
              function=LayerFunction.CLADDING),
    ),
    # Gypsum ceiling on the bottom chord — the air barrier the loose fill sits on. 5/8"
    # and not 1/2" for two reasons: nothing in the code forces a thickness here (RM-GARAGE
    # shares no wall with a dwelling room, so R302.5/R302.6 do not reach a detached garage
    # — code.R302_5_garage_separation says exactly that), and 5/8" is the sag-resistant
    # board for a ceiling. It is also what GARAGE_WALL_2X6's lining already uses, so the
    # garage is one board thickness throughout.
    #
    # NO PAINT LAYER, and that is a decision rather than an omission (owner, 2026-08-20):
    # the ceiling is taped and primed, not finished. GARAGE_WALL_2X6 keeps its paint, so
    # the garage is board-and-paint on the walls and board-and-primer overhead. A
    # `latex-paint` layer here would bill a finish coat nobody is applying; the primer
    # coat itself is not a modelled layer, so it rides in whatever the `gwb` row's
    # hang-tape-finish labour is taken to cover — the one thing this stack under-bills.
    default_lining=(
        Layer(name="gwb-ceil", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
    ),
    source="catlin-house detached garage roof (vented 4:12 truss attic); gypsum ceiling + 9.25\" blown fiberglass added 2026-08-20",
)

# --- interior ------------------------------------------------------------------
# These partitions carry gypsum in `layers` (not a lining), so paint is authored face by
# face as `paint-a`/`paint-b`. Both faces separate conditioned rooms, so there's no vapour
# drive to control — the paint is here purely for the finish takeoff. Deliberately unpainted
# elsewhere: SAUNA_* (T&G/foil-polyiso is already the vapour/air control, no paint in a
# löyly room), CATLIN_MUDROOM_INT_2X6_EXPOSED (exposed wood faces, already hardwax-oil
# finished), the masonry/concrete/deck/glazing assemblies (no gypsum face), POST_WHITE_PAINT
# (its own exterior-paint material), and INT_2X4_PARTITION (a tested STC assembly — see
# library/assemblies.py for why it doesn't get layers added).
# LAYOUT_ORIGIN, INTERIOR (2026-08-25). The five bearing assemblies below join the four
# facades on ``layout_origin="line"``. The facades were done first because they are what you
# look at; the centreline is the one that actually matters structurally. `W-M-C1..C5B`,
# `W-S-C1..C4B` and `W-A-C1..C2` are the x=18'-0" line that carries the ridge beam
# continuously to the footings, and until now each of those twelve walls restarted the 16"
# module at its own start node — three storeys, three phases, on the house's primary load
# path. Stacking them is an APA Advanced Framing technique, **not** an IRC mandate: R602.3.3
# is the *bearing-stud* rule (a joist, truss or rafter landing within 5" of a stud, and only
# where both runs are 24" o.c., with three exceptions), and R602.3.2's single-top-plate
# exception turns on rafters/joists centred over studs within 1" — neither says studs stack
# over studs. See ``model/assembly.py``'s note on ``layout_origin``. Worth doing anyway, and
# worth doing here first: a continuous load path is the whole argument for the centreline.
#
# STRUCTURE spec only, unlike the exterior pair: an interior wall has no vertical FURRING
# band to phase-lock to the studs. Both liner bands here are `direction="horizontal"`, and
# `furring._layout_horizontal` takes no phase, so there is nothing else to keep in step.
#
# Not opted in, deliberately: `INT_2X4_PARTITION` and the other non-bearing partitions
# (~46 walls — bearing lines first), and the staggered assemblies, which have a live
# rounding trap in `solver.py`'s face-parity rule that a non-zero phase would wake. See
# plans/TODO.md.
CATLIN_INT_2X6_BRG = Assembly(
    tag="CATLIN_INT_2X6_BRG",
    layers=(
        _PAINT_FINISH_A,
        Layer(name="gwb-a", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x6", layout_origin="line")),
        Layer(name="gwb-b", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        _PAINT_FINISH_B,
    ),
    interfaces=(_STUD_BEARING,),
    source="catlin-house centerline bearing wall (2x6)",
)


# --- the study's bookcase wall ----------------------------------------------------
# W-A-SN only (2026-08-27). The owner wanted a bookcase wall at the stair head with
# D-A-STUDY hidden inside it as a Murphy-style bookcase door. The obvious move — push the
# wall north to make room — is the one thing that cannot happen: W-A-SN's SOUTH FACE IS THE
# ONLY THING COVERING FO-A-STAIR's NORTH EDGE, and moving it north FAILs code.R312_1_guard
# with ~14'-3" of unguarded well. So the wall is THICKENED, NOT MOVED: the south face stays
# pinned on the well edge at 8'-9 5/8" and the extra depth grows north.
#
# 12 3/4" total is not a round number chosen for looks. With the wall centred on its axis,
# 105.625 + 12.75/2 = 112.000" puts the axis at y = 9'-4" exactly, which is also a 16"
# station — so FS-ATTIC (joists at y = 16k) has a joist directly under the sole plate where
# the old 4 3/4" partition had none, and the source-survey error at N-A-C2/N-A-E1 drops from
# 2.74" to 1.26". Do not "simplify" the stack-up without re-deriving that number.
#
# Clear shelf depth is 9 7/8" (the 6 3/8" pocket plus the 3 1/2" case face). The five bay
# stations and their tops are on W-A-SN in plan/storeys/attic.py; the casework itself is a
# prices.toml [allowances] lump, since a 1'-0"-deep catalog bookcase would stand 2 1/8"
# proud of this pocket — out over the well, the exact lie this wall exists to avoid.
#
# Four engine traps, each verified and each avoided on purpose:
#   * ONE STRUCTURE LAYER. `framing/solver.py::structure_layer` frames the FIRST one; a
#     second draws a solid and bills nothing. The case is the cavity, not a second frame.
#   * `laid` STAYS AT ITS DEFAULT "flat". A vertical FURRING band with `laid="edge"` is the
#     selector for the Swinburne truss wall (`truss_wall.py::_outrigger_layer_name`) and
#     would reframe this partition with blocks, tabs, KDAT outriggers and plywood bucks.
#   * `direction="vertical"` IS STATED. `framing/furring.py` reports an unstated direction
#     rather than guessing one.
#   * `PartitionLayout.DOUBLE` is declared but UNIMPLEMENTED (`solver.py` branches on
#     STAGGERED only). It is the shape this wall superficially resembles. Do not use it.
#
# `blocking_heights` is one row at 4'-0" and stops there: `framing/backing.py` does not clip
# blocking to a raked top, and this wall's top runs 11'-0" at x=18' down to 5'-0" at x=36'.
# That row is also the through-bolt line for the bookcase door's hinge-side jamb.
#
# No CavityFill (the cavity is the shelf), no `default_lining` and no paint layer (the study
# face is millwork — the CATLIN_MUDROOM_INT_2X6_EXPOSED precedent above), and no `stc=`:
# STC in this house is a transcribed lab test, never a computed number.
# The "INT" token is load-bearing as everywhere else (`_is_interior_assembly` in
# mn_energy.py splits the tag on "_") — without it an uninsulated bay grades against R-21.
CATLIN_INT_2X4_BOOKCASE_12 = Assembly(
    tag="CATLIN_INT_2X4_BOOKCASE_12",
    layers=(
        Layer(name="stud-case", material_ref="spf", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x4", spacing=inch(16),
                                  blocking_heights=(inch(48),))),
        Layer(name="case-pocket", material_ref="air-barrier", thickness=inch(6.375),
              function=LayerFunction.AIRGAP),
        Layer(name="case-back", material_ref="cabinet-plywood", thickness=inch(0.75),
              function=LayerFunction.FINISH),
        Layer(name="nailer-n", material_ref="spf", thickness=inch(1.5),
              function=LayerFunction.FURRING,
              framing=FramingSpec(member="2x4", spacing=inch(16),
                                  direction="vertical")),
        Layer(name="gwb-n", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
    ),
    # NOT `_STUD_BEARING`: that one names the layer "stud", and this assembly's structure
    # layer is "stud-case". The role must resolve to a real layer — `topology._bearing_layer`
    # would otherwise fall through to "the first STRUCTURE layer" and get the right answer by
    # accident, which is exactly the layer-index coupling the role mechanism exists to avoid.
    interfaces=(AssemblyInterface(role="bearing", layer_name="stud-case", outboard=False),),
    source="plans/TODO.md — study bookcase wall at the stair head: a 12 3/4\" built-in whose SOUTH face is pinned on FO-A-STAIR's north edge (the wall is thickened, never moved) and whose axis therefore lands on y=9'-4\", a 16\" station with an FS-ATTIC joist directly under it. 9 7/8\" clear shelf depth; five bays from x=22'-8\" stepping down the rake; the casework itself is a prices.toml [allowances] lump, so the BOM sees only the case-back sheet and the nailers. D-A-STUDY is hidden in this wall as DT-INT-BOOKCASE30 — its hinge-side jamb wants a full-depth 3-ply post through-bolted to the sole plate and the 4'-0\" blocking row (a 250 lb leaf on a 10\" moment arm is torsion, not bending), for which there is no schema field",
)

# INT_2X6_PLUMBING and INT_2X6_STAGGERED_PLUMBING (generic wet-wall partitions, no
# house-specific geometry or owner data) were promoted to library/assemblies.py on
# 2026-08-22 (CONTRIBUTING §Promotion flow) and are imported above. The staggered
# variant's non-bearing rationale — same 5.5" pipe cavity as the bearing wall above, but
# decoupled staggered studs so a stack never needs a stud bored on the way through —
# lives with it there now.

# --- energy storage closet -------------------------------------------------------
# The ESS closet's partitions (notes/backup_power.md, 2026-08-02), an owner decision not a
# code requirement (IRC R327 permits an ESS in an ordinary utility closet; that's why
# `advisory.ess_enclosure`, not the code check, grades it): steel studs (no combustible
# framing around the 14 kWh lithium pack), 5/8" Type X both faces (R302.6-style fire
# membrane, both directions — the fire may start *inside* this closet). No cavity fill on
# purpose: heat should reach AL-B-ESS-HEAT outside, not be insulated away from it.
# The "INT" tag token is load-bearing: `mn_energy._is_interior_assembly` and the IFC
# emitter's IsExternal both key off it to keep this out of the R-21 exterior-wall table.
INT_ESS_CLOSET_STEEL = Assembly(
    tag="INT_ESS_CLOSET_STEEL",
    layers=(
        _PAINT_FINISH_A,
        Layer(name="gwb-x-a", material_ref="gwb-x", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="steel-stud", material_ref="steel-stud", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x4", spacing=inch(16))),
        Layer(name="gwb-x-b", material_ref="gwb-x", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        _PAINT_FINISH_B,
    ),
    source="owner ESS-closet standard, 2026-08-02: 25 ga. steel C-stud at 16 in. o.c. with 5/8 in. Type X both faces (notes/backup_power.md). Not a code-required rated assembly and not claimed as one — no tested assembly number is cited.",
)

# --- sauna ---------------------------------------------------------------------
# The hot side of a sauna is its own wall type, not a lining override on a partition:
# the foil-faced polyiso is the vapour/air control layer and the T&G liner is a
# low-conductivity species chosen so the boards stay touchable at löyly temperatures.
# Per notes/sauna_basement_wall_detail.md.
_SAUNA_LINER = (
    Layer(name="tg-liner", material_ref="sauna-tg", thickness=inch(1.0),
          function=LayerFunction.FINISH),
    Layer(name="liner-furring", material_ref="struct-1-plywood", thickness=inch(0.5),
          function=LayerFunction.FURRING,
          framing=FramingSpec(member="1x4", direction="horizontal")),
    Layer(name="foil-polyiso", material_ref="polyiso-foil", thickness=inch(2.0),
          function=LayerFunction.INSULATION,
          control={ControlLayer.THERMAL, ControlLayer.VAPOR, ControlLayer.AIR}),
)

# Sauna partition: hot side liner, 2x4 framing, gwb on the cold side.
SAUNA_2X4 = Assembly(
    tag="SAUNA_2X4",
    layers=(
        *_SAUNA_LINER,
        Layer(name="stud", material_ref="spf", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x4"),
              cavity=CavityFill(material_ref="mineral-wool")),
        Layer(name="gwb-cold", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
    ),
    interfaces=(_STUD_BEARING,),
    source="catlin-house sauna_basement_wall_detail.py + notes/sauna_basement_wall_detail.md",
)

# Where the sauna's hot side lands on the center concrete wall there is no framing to
# fill — the liner stack applies directly to the concrete.
SAUNA_LINER_ON_CONCRETE = Assembly(
    tag="SAUNA_LINER_ON_CONCRETE",
    layers=(
        *_SAUNA_LINER,
        Layer(name="concrete", material_ref="concrete", thickness=inch(12.0),
              function=LayerFunction.STRUCTURE),
    ),
    interfaces=(_CONCRETE_BEARING,),
    source="catlin-house sauna_basement_wall_detail.py (liner on the center bearing wall)",
)

# W-B-S2 only: the sauna's south side is a segment of the sunken-garden foundation wall,
# whose every non-structural layer sits *outboard* of the pour — so without this variant the
# room's fourth face is bare concrete while the other three carry the liner. Same liner, same
# order, on concrete instead of studs: the furring is fastened to the pour, not to framing.
#
# The three liner layers are restated here rather than splatted from _SAUNA_LINER because
# they carry a vertical extent that is specific to this wall and must not leak onto the
# partitions: the sauna's ceiling is at 7'-6" (W-B-SA-W/-N are `top=ft(7, 6)`) while the
# foundation wall runs the full 9'-4" from bottom_elevation=ft(-9, -4) to top_elevation=ft(0).
# Bounding the liner below the wall top keeps the takeoff from billing basswood T&G, furring
# and foil-faced polyiso over the concrete above the sauna's ceiling. The offset is 6", not
# the 1'-6" it was until 2026-08-23: the pour used to run to 0'-0" and stops on the bearing
# seat at -13 7/16" now, so the same 7'-6" ceiling is 6" down from the top of the wall
# instead of eighteen. The number to keep true is the *ceiling*, not the offset — if the
# seat moves again, this moves with it.
# PROVISIONAL: if the basement ever goes to a joist ceiling running the full width, the liner
# would run the wall's whole height and this extent should come back off.
_SAUNA_CEILING_EXTENT = LayerExtent(
    top=LayerBound(datum=LayerDatum.WALL_TOP, offset=inch(-6.0)))

SAUNA_LINER_ON_BASEMENT_8_GARDEN = Assembly(
    tag="SAUNA_LINER_ON_BASEMENT_8_GARDEN",
    layers=(
        Layer(name="tg-liner", material_ref="sauna-tg", thickness=inch(1.0),
              function=LayerFunction.FINISH, extent=_SAUNA_CEILING_EXTENT),
        Layer(name="liner-furring", material_ref="struct-1-plywood", thickness=inch(0.5),
              function=LayerFunction.FURRING,
              framing=FramingSpec(member="1x4", direction="horizontal"),
              extent=_SAUNA_CEILING_EXTENT),
        Layer(name="foil-polyiso", material_ref="polyiso-foil", thickness=inch(2.0),
              function=LayerFunction.INSULATION,
              control={ControlLayer.THERMAL, ControlLayer.VAPOR, ControlLayer.AIR},
              extent=_SAUNA_CEILING_EXTENT),
        *FOUNDATION_WALL_8_XPS4_CORE,
        _GARDEN_PARGE,
    ),
    interfaces=(_CONCRETE_BEARING,),
    source="catlin-house sauna_basement_wall_detail.py + CATLIN_BASEMENT_8_GARDEN (liner on the sunken-garden foundation wall)",
)

# --- mudroom exposed-stud wall ---------------------------------------------------
# W-M-STRW only. No default_lining, deliberately (like SAUNA_2X4): the mudroom face is a
# finished face made of the framing itself, not drywall left off. The open 2x6 bays are the
# coat nooks, so no cavity fill either — insulating them would fill the nooks, and both
# sides are conditioned anyway. Stair side closes with 3/4" cabinet plywood: stair finish
# and screw-anywhere hook backing at once. "INT" in the tag is load-bearing (see
# FOUNDATION_WALL_12_INT, INT_2X6_PLUMBING, _is_interior_assembly in mn_energy.py) — without it
# the uninsulated bays would fail as an exterior wall against R-21.
# `layout_origin="line"`: W-M-STRW/STRW2 are the main storey of the stair line, standing on
# W-B-STR/STR2/STR3 below. The exposed studs are the ones you can see from the mudroom, so
# they were always the ones a broken module showed up on.
CATLIN_MUDROOM_INT_2X6_EXPOSED = Assembly(
    tag="CATLIN_MUDROOM_INT_2X6_EXPOSED",
    layers=(
        Layer(name="stud", material_ref="df-select-s4s", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x6", layout_origin="line")),
        Layer(name="ply-stair", material_ref="cabinet-plywood", thickness=inch(0.75),
              function=LayerFunction.FINISH),
    ),
    interfaces=(_STUD_BEARING,),
    source="plans/TODO.md — mudroom coat wall: exposed Select Structural S4S 2x6 DF studs on the mudroom face (open bays = coat nooks), 3/4\" cabinet-grade plywood on the stair face",
)

# --- basement stair-shaft bearing walls -------------------------------------------
# W-B-STR3 / W-B-STR, the last two 12" interior pours on the x=10' line, framed instead
# (2026-08-24). They carry no earth; what they carry is FS-M-MECH/FS-M-STAIR's short
# joists and the W-M-STRW/W-M-STRW2 stack above, which is a stud-wall job on a footing.
# Both continue CATLIN_MUDROOM_INT_2X6_EXPOSED's plywood plane on the stair face, so the
# well's west face is one plywood surface from the basement floor to the main-storey
# ceiling — but with plain `spf` studs: nothing down here is exposed to a finished room.
# The "INT" token is load-bearing exactly as it is there (`_is_interior_assembly` in
# mn_energy.py keeps an uninsulated bay out of the R-21 exterior table).
CATLIN_STAIRWALL_INT_2X6_BRG = Assembly(
    tag="CATLIN_STAIRWALL_INT_2X6_BRG",
    layers=(
        Layer(name="stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x6", spacing=inch(16),
                                  sill_gasket=inch(0.0625),
                                  layout_origin="line")),
        Layer(name="ply-stair", material_ref="cabinet-plywood", thickness=inch(0.75),
              function=LayerFunction.FINISH),
    ),
    interfaces=(_STUD_BEARING,),
    source="catlin basement stair wall (W-B-STR3): 2x6 spf bearing studs at 16 in. o.c. on a PT sill, 3/4 in. plywood on the stair face continuing CATLIN_MUDROOM_INT_2X6_EXPOSED",
)

# The same wall where it forms RM-B-ESS's west side: one 5/8" Type X leaf on the closet
# face, which is what `advisory.ess_enclosure` sums for now that the mass of 12" of
# concrete is no longer there to satisfy it. Same `gwb-x` material as INT_ESS_CLOSET_STEEL.
CATLIN_STAIRWALL_INT_2X6_BRG_TYPEX = Assembly(
    tag="CATLIN_STAIRWALL_INT_2X6_BRG_TYPEX",
    layers=(
        Layer(name="gwb-x", material_ref="gwb-x", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x6", spacing=inch(16),
                                  sill_gasket=inch(0.0625),
                                  layout_origin="line")),
        Layer(name="ply-stair", material_ref="cabinet-plywood", thickness=inch(0.75),
              function=LayerFunction.FINISH),
    ),
    interfaces=(_STUD_BEARING,),
    source="catlin basement stair wall (W-B-STR) where it is also RM-B-ESS's west enclosure: CATLIN_STAIRWALL_INT_2X6_BRG with a 5/8 in. Type X leaf on the closet face (notes/backup_power.md)",
)

MATERIALS = [
    *STARTER_MATERIALS,
    # The EPS stay-in-place deck form (CATLIN_DECK_EPS_INT). Deliberately *not* `icf-eps`,
    # whose R-4.0/inch is the bead EPS on its own: this section is ribbed, and the concrete
    # that fills the ribs bridges it. BuildDeck publishes R-25 for the 8" section as
    # installed, which is R-3.125/inch through the finished deck — the number that belongs
    # in a thermal model of this floor, and 22% below the bare-foam figure.
    Material(tag="eps-deck-form", name="EPS stay-in-place deck form", r_per_inch=3.125,
             perm_rating=3.9, hatch="rigid", color="#f0f0e6", foam_plastic=True,
             source="BuildDeck brochure: R-25 at the 8\" base section as installed (ribs bridged by the pour), i.e. R-3.125/inch; permeance from ASHRAE UAF 'Expanded polystyrene, bead' 2.0-5.8 perm-in, midpoint, as `icf-eps`"),
    # --- accent wall paint -------------------------------------------------------
    # The house's one interior accent: deep spruce green-blue on RM-S-BED1's feature wall
    # (storeys/second.py). Physically identical to `latex-paint` (same film, same Class III
    # ~5 perm retarder, coating=True) — only the colour differs, so building science is
    # unchanged. Authored dark on purpose: the viewer's lighting lifts a dark albedo well
    # above itself (see metal-dark-exterior below for the same effect).
    Material(tag="latex-paint-accent", name="Interior latex paint, spruce accent",
             r_per_inch=0.0, vapor_permeance_perms=5.0, color="#2e4a44",
             finish="matte-latex", coating=True,
             source="same film as latex-paint (IRC R702.7.1 Class III over gypsum); only the colour differs — a second Material tag is how a wall says it is a different colour, since Layer has no colour slot"),
    # The roof's DECK vapour barrier (CATLIN_ROOF), over the taped ZIP and under the foam.
    # This is the layer that makes the roof a "perfect wall": all four control layers land
    # outboard of the structure, so the interior is paint and nothing else.
    #
    # The taped ZIP alone is not enough, and the reason is worth writing down. ZIP is an air
    # and water barrier, but 2 perm is IRC Class III — it is not a vapour barrier. That was
    # survivable while the layer outboard of the foam was a 54-perm membrane, because
    # whatever crossed the ZIP left again. It stopped being survivable when the nailbase
    # deck went on: 5/8" OSB is 0.64 perm, THREE TIMES TIGHTER than the ZIP under it. The
    # stack was inverted — vapour entered the foam more easily than it could leave — and it
    # piled up on the foam's cold face at 127% of saturation. Thinning the OSB does not fix
    # it (7/16" only reaches 1.21, and APA's own data has 1/2" at 0.70 perm against 5/8" at
    # 0.72, so the thickness lever is nearly flat in reality too). Making the sheathing-plane
    # control layer a real Class I barrier does: 0.89, with the interior left as paint.
    Material(tag="roof-deck-vapor-barrier", name="Self-adhered roof deck vapour barrier",
             r_per_inch=0.0, vapor_permeance_perms=0.04, hatch="membrane", color="#4a4a4a",
             source="published SBS self-adhered deck vapour barriers (Soprema Sopravap'r, Carlisle VapAir Seal 725TR) ASTM E96 permeance 0.03-0.05 perm; midpoint of the published range — a sheet rating, not perm-in"),
    # The ventilated underlayment mat under the standing seam. NOT a furring strip: a ~1/4"
    # nylon-matrix mat rolled over the underlayment, which the panel clips screw straight
    # through into the top deck below. It is the assembly's only outward drying path, and
    # without it the walk runs to the standing seam itself — which is rated 0 perm, so every
    # plane inboard of it sits at interior vapour pressure and NO unvented stack under a
    # metal roof can pass the gate at all, at any foam thickness. Metal manufacturers now
    # ask for one over self-adhered underlayment for this exact reason.
    Material(tag="roof-vent-mat", name="Ventilated underlayment mat (nylon matrix)",
             r_per_inch=0.0, perm_rating=120.0, hatch="membrane", color="#8a8f94",
             source="the vapour path through an open nylon-matrix mat is the air in it, so it is rated as `resilient-channel` above is: UAF 'Air, still' 120 perm-in"),
    # --- mudroom exposed-stud wall ---------------------------------------------
    # Appearance-grade framing, because in W-M-STRW the studs ARE the finish. Select
    # Structural S4S with eased corners: the grade buys straightness and a clean face, the
    # eased arris keeps a hand running along an exposed edge off a sharp corner. Douglas
    # fir-larch rather than SPF: it is the denser species (~32 pcf vs SPF's ~29), which is
    # why its R/inch is *lower* than spf's 1.24 — conductivity tracks density in wood.
    Material(tag="df-select-s4s", name="Douglas fir Select Structural S4S, eased corners",
             r_per_inch=1.00, density=530.0, perm_rating=2.9, hatch="lumber",
             color="#d9b077", finish="clear-satin-hardwax-oil",
             source="plans/TODO.md — exposed mudroom studs; DF-L R ~0.99-1.06/in (vs SPF 1.24-1.25) per the softwood density series, permeability shares the softwood midpoint used for spf"),
    # The stair face. 3/4" rather than the 1/2" a plain panel finish would take, because
    # this panel is structural backing: coat hooks and the closet rail screw straight into
    # it anywhere along the wall, with no blocking behind and no stud to hunt for.
    Material(tag="cabinet-plywood", name="Cabinet-grade hardwood plywood (3/4\")",
             r_per_inch=1.25, density=610.0, perm_rating=0.30, hatch="lumber",
             color="#c8a97a", finish="clear-satin-hardwax-oil",
             source="plans/TODO.md — mudroom wall's stair face; 3/4\" is structural backing so coat hooks screw directly into it (a 1/2\" panel would need blocking); permeability per the plywood series used for struct-1-plywood"),
    # FS-ATTIC's deck sheet, and only FS-ATTIC's (2026-08-27). The two unfinished lofts
    # RM-A-WEST-UNFIN / RM-A-EAST-UNFIN take no floor covering at all, so this panel IS the
    # walking surface — it is walked on, swept and stacked on with nothing over it. A
    # subfloor sheet is not specified to be walked on: it is specified to be covered, and
    # what is stocked as "3/4 subfloor" on a Minnesota job is OSB as often as plywood.
    # Naming the panel here is what stops that substitution at the lumberyard, and it is
    # why this is a separate tag from `plywood-subfloor` rather than a comment on it: every
    # other deck in the house gets a covering and does not care.
    #
    # 23/32" Performance Category is the trade designation for what the model carries as
    # 3/4"; the Span Rating of 24 oc is well inside FS-ATTIC's 16" I-joist spacing. The
    # numbers are the plywood series' (r_per_inch, permeability) — it is the same veneer
    # panel as `plywood-subfloor`, sanded on one face and plugged, so nothing thermal or
    # hygric moves. Only the grade, the price and the drawing do.
    Material(tag="plywood-underlayment-sanded",
             name="23/32\" sanded-face underlayment plywood, T&G (Sturd-I-Floor 24 oc)",
             r_per_inch=1.25, density=600.0, perm_rating=0.30, hatch="osb",
             color="#dcc79a",
             source="APA Underlayment/Subfloor (apawood.org/underlayment-subfloor): \"Underlayment C-C Plugged or veneer-faced Sturd-I-Floor with sanded face\" is the grade specified where the panel takes resilient flooring or is left exposed; 23/32 Performance Category = 24 oc Span Rating (APA RATED STURD-I-FLOOR datasheet). Thermal/vapour fields per the plywood series used for plywood-subfloor and struct-1-plywood"),
    Material(tag="sauna-tg", name="Basswood/aspen T&G sauna liner (5/4)", r_per_inch=1.3,
             perm_rating=20.0, hatch="lumber", color="#e6d4ae",
             species="basswood", stock_bf_per_sqft=1.25,
             source="notes/sauna_basement_wall_detail.md — low-conductivity species (American basswood, Canadian poplar, aspen); 5/4 stock = 1.25 bf/sf"),
    # --- species wood finishes (plans/TODO.md §Hardwood, 2026-08-02) -----------
    # RM-M-STUDY wainscot to 36". 4/4 stock: board feet = square feet.
    Material(tag="walnut-tg", name="Black walnut T&G wainscot (4/4)", r_per_inch=1.1,
             density=610.0, hatch="lumber", color="#5d4433",
             finish="clear-satin-hardwax-oil", species="walnut", stock_bf_per_sqft=1.0,
             source="plans/TODO.md — first-floor study walnut paneling to 36\""),
    # The suite's four 6-1/8\" square tudor posts, ordered as 10' sections and cut down.
    Material(tag="elm-timber", name="Elm timber 6-1/8\" square, S4S", r_per_inch=1.1,
             density=560.0, hatch="lumber", color="#b08d5e",
             finish="clear-satin-hardwax-oil", species="elm",
             source="plans/TODO.md — suite bedroom tudor posts, 10' sections cut to fit"),
    # --- the metal skins (2026-08-20; a fifth added 2026-08-26) ------------------
    # The house is clad in metal in FIVE specifications. They are all the same white PVDF
    # steel to look at; what separates them is SEAM PROFILE and GAUGE, and both are labour
    # and material facts rather than architectural ones. Splitting them into four tags is
    # what lets `prices.toml` bill each at its own rate — before this date a single tag
    # carried all 6,300 SF at the dearest of the four, which overstated the biggest line in
    # the house by roughly $5,000-18,000.
    #
    #   `standing-seam` (library/materials.py) — 24 ga, MECHANICALLY FIELD-SEAMED.
    #       CATLIN_ROOF and nothing else. Every seam takes a separate powered-seamer pass:
    #       +$1.50-3.00/SF of labour and ~50% more crew-hours than a hand-closed profile,
    #       plus a seamer rental. It is on the main house roof on purpose — this is the roof
    #       that carries the PV array, sheds onto occupied ground, and must not be re-roofed
    #       in 25 years.
    #   `standing-seam-snaplock` — 24 ga, SNAP-LOCK. Concealed floating clips like the
    #       seamed roof, but the male and female legs engage under hand pressure, so there
    #       is no seaming pass. Roughly $2-4/SF cheaper installed than mechanical seam.
    #       It clad the house walls until 2026-08-26 and is now taken by nothing but
    #       CATLIN_EXT_2X6_SWINBURNE, the revert wall — which is exactly what keeps the
    #       swap back to it a one-line `material_ref` change.
    #   `standing-seam-nailstrip` — 24 ga, NAIL-STRIP. GARAGE_ROOF only. Nail strip has NO
    #       concealed clips at all: an integral flange is face-fastened to the deck and the
    #       next panel's leg snaps over it, dropping both the clip material and the
    #       clip-setting labour. The trade-off is that face-fastening restricts thermal
    #       movement, so it wants SHORT runs — which is exactly what a garage is, and is why
    #       it stops at the garage and does not come onto the house.
    #   `standing-seam-nailstrip-26` — 26 ga, nail strip, same white paint.
    #       GARAGE_WALL_2X6 only. One gauge thinner (0.0179" vs 0.0239" base metal, ~25%
    #       less steel) for 20-35% less material. It oil-cans more visibly than 24 ga on a
    #       flat wall, which is acceptable on a detached garage and would not be on the
    #       house; specify a striated pan rather than a flat one.
    #
    # Every building-science number on all five is `standing-seam`'s verbatim — continuous
    # sheet steel is vapour-impermeable and carries no R whatever its gauge or seam — so
    # nothing here changes an energy or a Glaser result. Keep them in step by hand.
    #
    # The FIRST FOUR tags keep the substring "seam" ON PURPOSE:
    # `ui/src/three/materials.isStandingSeam` and `nordic/palette.familyOf` both key the
    # ribbed metal finish off it, and a tag like "nail-strip-steel" would render this
    # house's walls as flat grey. `pbr-panel-26` deliberately does NOT play that game — it
    # declares `finish="ribbed-panel"` and the renderers dispatch on the declaration, which
    # is what the substring fallback was always standing in for.
    Material(tag="standing-seam-snaplock", name="Snap-lock standing-seam steel, 24 ga.",
             r_per_inch=0.0, density=7800.0, vapor_permeance_perms=0.0, hatch="metal",
             color="#6b7076",
             skin_family="standing-seam",
             source="same 24 ga. PVDF-coated steel as library `standing-seam`, snap-lock seam profile (concealed floating clips, seam engaged by hand); continuous sheet steel is vapour-impermeable and is installed over a vented rainscreen"),
    Material(tag="standing-seam-nailstrip", name="Nail-strip standing-seam steel, 24 ga.",
             r_per_inch=0.0, density=7800.0, vapor_permeance_perms=0.0, hatch="metal",
             color="#6b7076",
             skin_family="standing-seam",
             source="same 24 ga. PVDF-coated steel, nail-strip seam profile (integral face-fastened flange, no concealed clips); short runs only, since face-fastening restricts thermal movement"),
    Material(tag="standing-seam-nailstrip-26", name="Nail-strip standing-seam steel, 26 ga.",
             r_per_inch=0.0, density=7800.0, vapor_permeance_perms=0.0, hatch="metal",
             color="#6b7076",
             skin_family="standing-seam",
             source="26 ga. PVDF-coated steel, nail-strip seam profile — the detached garage's wall spec; same white as the house, one gauge thinner"),
    # `standing-seam-nailstrip-26-green` (2026-08-26) — the same 26 ga. nail-strip panel as
    # the rest of the garage, in Western States Metal Roofing "Classic Green"
    # (westernstatesmetalroofing.com/classic-green) instead of white, on W-G-E only (the
    # overhead-door wall) via that wall's own `layer_materials=` override — no second
    # assembly, because nothing but the paint differs. The manufacturer publishes no
    # hex/RGB for the colour (page disclaimer: screen colour may differ from the physical
    # panel — order a sample), so this is an approximate PVDF forest-green swatch, not a
    # spec'd value; keeps `skin_family="standing-seam"` so the wall still reads as one
    # continuous skin with the garage roof at the closure edge.
    Material(tag="standing-seam-nailstrip-26-green", name="Nail-strip standing-seam steel, 26 ga., Classic Green",
             r_per_inch=0.0, density=7800.0, vapor_permeance_perms=0.0, hatch="metal",
             color="#2f5233", finish="classic-green-seam",
             skin_family="standing-seam",
             source="26 ga. PVDF-coated steel, nail-strip seam profile, Western States Metal Roofing \"Classic Green\" (westernstatesmetalroofing.com/classic-green) — an accent colourway for the garage's overhead-door (east) wall only; every other garage wall stays standing-seam-nailstrip-26 white"),
    # `pbr-panel-26` (2026-08-26) — 26 ga, EXPOSED-FASTENER PBR. The house walls,
    # CATLIN_EXT_2X6 and PLANT_EXT_2X6_HUMID, taking over from `standing-seam-snaplock`.
    # The fifth metal skin and the only one that is not a concealed-fixing product: 36" net
    # coverage with 1-1/4" major ribs at 12" o.c., screwed through its face into the girts.
    #
    # It is here because the 2026-08-26 truss-girt work built the substrate for it — flat
    # horizontal 2x4 girts at 24" o.c. are exactly what a PBR panel wants and are the
    # reason this stops at the house: GARAGE_WALL_2X6 has no furring at all (cladding
    # straight on Zip-R), so PBR there would need a whole new girt layer, and that cost
    # cancels the saving over 631 SF. The garage stays on `standing-seam-nailstrip-26`.
    #
    # `exposed_fastener=True` is not decoration: it is what lets `takeoff.fasteners` bill
    # the panel screws as a counted part. On the four skins above the fixings ride inside
    # the $/SF rate and counting them again would double-bill them.
    #
    # `skin_family="standing-seam"` is load-bearing for the ROOF EDGE, not the appearance:
    # `resolve.roof_edge_geometry.continuous_skin_cladding` returns True only when every
    # wall under a roof reads as one skin with the roofing, and without it the flush
    # zero-overhang edge silently reverts to a fascia-and-drip-edge detail nobody drew.
    # This is precisely the case that field's docstring describes — one white steel skin,
    # several specifications.
    Material(tag="pbr-panel-26", name="PBR exposed-fastener steel panel, 26 ga.",
             r_per_inch=0.0, density=7800.0, vapor_permeance_perms=0.0, hatch="metal",
             color="#6b7076", finish="ribbed-panel",
             skin_family="standing-seam", exposed_fastener=True,
             source="26 ga. PVDF-coated steel PBR (purlin-bearing rib) wall panel, 36\" net coverage, 1-1/4\" major ribs at 12\" o.c., face-fastened with gasketed screws; same white paint and the same vapour-impermeable sheet steel as the four skins above"),
    Material(tag="polyiso-foil", name="Foil-faced polyisocyanurate", r_per_inch=6.0,
             perm_rating=0.03, hatch="rigid", color="#d9d2a8", foam_plastic=True,
             source="foil facer is the sauna's vapour retarder as well as its CI"),
    # Loose-fill for the garage attic (GARAGE_ROOF). A separate tag from `fiberglass`
    # because blown wool is installed at roughly half batt density and rates R-2.5/in
    # rather than R-3.7 — reusing the batt tag would overstate the ceiling by ~48%.
    # House-local rather than library: only this roof uses it, so it stays here until a
    # second house wants it (CONTRIBUTING §Promotion flow).
    Material(tag="blown-fiberglass", name="Blown (loose-fill) fiberglass", r_per_inch=2.5,
             perm_rating=116.0, hatch="batt", color="#f6d9e1",
             source="NAIMA/manufacturer published loose-fill glass wool R-2.2-2.7 per inch at attic settled density; midpoint. Permeance as `fiberglass` above — loose-fill glass wool is air-permeable at any density"),
    # The roof cavity batt (CATLIN_ROOF). A separate tag from `fiberglass` because the
    # library's 3.7/in is a HIGH-DENSITY value — right for an R-21 batt squeezed into 5.5",
    # wrong for a standard R-19 that reaches R-19 only by lofting to 6.25". Reusing the
    # library tag at 6.25" would read R-23 and overstate this roof by R-4. House-local until
    # a second house wants it (CONTRIBUTING §Promotion flow).
    Material(tag="fiberglass-r19", name="Fiberglass batt, R-19 (6-1/4\")", r_per_inch=3.04,
             perm_rating=116.0, hatch="batt", color="#f3c6d0",
             source="R-19 nominal over the 6.25\" lofted thickness the rating is declared at = 3.04/in. Permeance as library `fiberglass` — glass wool is air-permeable at any density"),
    # The roof's field underlayment (CATLIN_ROOF), over the nailbase top deck.
    #
    # **Vapour-PERMEABLE synthetic, and that is not a preference.** High-temp peel-and-stick
    # over the whole field is the obvious choice under metal and it fails the condensation
    # gate outright (1.50 against 1.00): at 0.05 perm it is as tight as the deck vapour
    # barrier under the foam, so the polyiso and the OSB deck end up sealed on BOTH faces
    # with no way to dry in either direction. The synthetic is what turns the vent mat above
    # it into an actual drying path — with it the same stack runs at 0.80.
    #
    # The eaves and valleys still get the self-adhered ice barrier code requires; that is an
    # edge band a couple of feet wide, not a field layer, so it is priced as an allowance
    # (`roof-ice-and-water-barrier-code-minimum` in prices.toml) rather than modelled here.
    # It is small enough that sealing it does not close the field's drying path.
    Material(tag="roof-underlayment-synthetic",
             name="Vapour-permeable synthetic roof underlayment",
             r_per_inch=0.0, vapor_permeance_perms=20.0, hatch="membrane", color="#3b3b3b",
             source="published vapour-permeable synthetic roof underlayments (VaproShield SlopeShield, Cosella-Dorken DELTA-MAXX) ASTM E96 permeance 15-50 perm; low end of the published range — a sheet rating, not perm-in"),
    # The plant room's three materials — `pvc-panel`, `humid-room-membrane` and
    # `vinyl-sheet` — were authored here first and promoted to `library/materials.py`
    # (CONTRIBUTING §Promotion flow) on 2026-08-18: none of them carries a project
    # coordinate, an owner choice or a house-specific dimension, all three are ordinary
    # catalog products with stable tags, and `takeoff/finishes.py::_WASTE` (engine code)
    # names `vinyl-sheet` — an engine table may not depend on a material only one house
    # defines. They arrive through `STARTER_MATERIALS` above. See notes/plant_room.md for
    # why the panel deliberately carries no permeance and the membrane carries a
    # specification value.
    Material(tag="brick", name="Face brick", r_per_inch=0.20, density=1920.0,
             perm_rating=1.0, hatch="concrete", color="#9c5a4a", finish="brick",
             source="red face brick — the catalog default wythe"),
    # White (whitewashed / white-fired) face brick laid with a grey mortar joint. Same clay
    # unit and R-value as the red brick; only the finish differs, and `finish` names the
    # recipe explicitly so no renderer has to infer "white" from the tag spelling.
    Material(tag="white-brick", name="White face brick (grey mortar)", r_per_inch=0.20,
             density=1920.0, perm_rating=1.0, hatch="concrete", color="#e9e6df",
             finish="white-brick",
             source="porch railing outer wythe — white brick, grey mortar (brief.md)"),
    # Glazed (fired-glaze) face brick in forest green — the sunken garden's south wall
    # veneer. Same clay unit, R-value and density as the red/white brick; only the finish
    # differs. Named explicitly so no renderer has to infer "green" from the tag: the glaze
    # is a ceramic coat, which is why it reads uniform and low-jitter like the white brick
    # rather than variegated like the red.
    #
    # RETIRED as the veneer's field on 2026-08-20, when BASEMENT_BRICK_VENEER became the
    # Ishtar scheme below, and kept alive here on purpose: the colour was liked, it just did
    # not sit with a house of white standing seam and #1c1f24 trim. Nothing references it, so
    # restoring the wall to one flat forest-green field is a one-word `material_ref` swap in
    # BASEMENT_BRICK_VENEER — the Material, its MasonryStyle and its _FINISH_BASE entry are
    # all still there. Do not delete it to tidy up.
    Material(tag="glazed-green-brick", name="Glazed forest-green face brick",
             r_per_inch=0.20, density=1920.0, perm_rating=1.0, hatch="concrete",
             color="#1b4332", finish="glazed-green-brick",
             source="basement south veneer over the sunken garden until 2026-08-20 — glazed brick, 1\" airgap off the existing concrete wall; kept in the catalog as the revert target for the Ishtar scheme"),
    # --- the Ishtar scheme (2026-08-20) ------------------------------------------------
    # Three faces on one wythe, banded by Layer.slot in BASEMENT_BRICK_VENEER: a lapis field
    # with golden-yellow registers over an unglazed brown plinth, after the Ishtar Gate of
    # Babylon. Same clay unit, R-value, density and permeance as every other brick here —
    # a brick is a brick and only the face differs, which is the whole reason `finish` and
    # `color` are separate fields from the physics.
    #
    # All three hexes are authored a step DARKER than their reference colour, deliberately.
    # An authored colour is an albedo, and the viewer lights with 0.8 hemisphere + 0.9 key +
    # 0.6 IBL over unit irradiance, so a saturated surface arrives on screen well above what
    # is written here — the same lesson #1c1f24 records below. Author under the tone you
    # want to see, and re-check against `haus render --view elevation`.
    Material(tag="glazed-lapis-brick", name="Glazed lapis-blue face brick",
             r_per_inch=0.20, density=1920.0, perm_rating=1.0, hatch="concrete",
             color="#10386a", finish="glazed-lapis-brick",
             source="basement south veneer, the Ishtar field (2026-08-20) — glazed brick, 1\" airgap off the existing concrete wall"),
    # The registers. Same glaze technology as the lapis and so the same low jitter, but it is
    # a SECOND colour on the same job: its own special-order pallet, its own lead time, and a
    # mason laying two colours to a line rather than one. That is a price fact, not a
    # rendering one — see [wall_structure] in prices.toml.
    Material(tag="glazed-gold-brick", name="Glazed golden-yellow face brick",
             r_per_inch=0.20, density=1920.0, perm_rating=1.0, hatch="concrete",
             color="#c08a12", finish="glazed-gold-brick",
             source="basement south veneer, the Ishtar register bands (2026-08-20) — glazed brick, 1\" airgap off the existing concrete wall"),
    # The plinth: ordinary unglazed brown face brick, the cheapest brick on the wall and the
    # only one a Twin Cities yard carries off the shelf. Specify it as a SINGLE light body,
    # not a blend (2026-08-21). It was first authored dark and at the red brick's full
    # variegation, on the argument that an unglazed body beside a fired glaze is what makes
    # the glaze read as a glaze; on the wall that came out as a plinth laid from mixed
    # pallets with near-black units through it, which is a different building. One light
    # brown reads as one brick, and the glaze contrast is carried by sheen and joint colour
    # instead — see BROWN_BRICK_STYLE in ui/src/three/materials.ts, kept in step by hand.
    Material(tag="brown-brick", name="Brown face brick (unglazed)",
             r_per_inch=0.20, density=1920.0, perm_rating=1.0, hatch="concrete",
             color="#a07c5c", finish="brown-brick",
             source="basement south veneer, the Ishtar plinth (2026-08-20) — standard unglazed face brick, no special order"),
    # Glen-Gery "Columbia Roman Maximus" for the garage wainscot (2026-08-26), replacing
    # the black colourway of the same unit (which itself replaced an earlier light-buff
    # stock spec). Same clay physics as every other brick here — a brick is a brick and
    # only the face differs, which is the whole reason `finish` and `color` are separate
    # fields from `r_per_inch`/`density`. The unit itself is 3 5/8" x 1 5/8" x 23 5/8"
    # (glengery.com/brick-catalog/columbia-roman-maximus): the bed depth matches a modular
    # unit exactly (this material drops into the same 3 5/8" `brick` layer unchanged), but
    # it is a handmade Type FBA unit — coursing runs on its 1 5/8" + 3/8" joint = 2" module,
    # not modular's 2 2/3", and the 23 5/8" length reads as long, widely-spaced vertical
    # joints rather than a standard running bond. See GARAGE_BRICK_LEDGE_RISE above for the
    # recomputed coursing this drives — unchanged by this colour swap.
    #
    # `finish` stays "roman-maximus-brick": that key names the UNIT GEOMETRY recipe (the
    # 23 5/8" elongated unit and its coursing), not a colourway, so the black-to-Columbia
    # swap only touches `color`/`source` here and the style's `base` colour in
    # ui/src/three/materials.ts / emit/gltf/palette.py — nothing about the masonry recipe
    # itself changes.
    Material(tag="off-white-brick", name="Columbia Roman Maximus face brick (ASTM C216 Grade SW)",
             r_per_inch=0.20, density=1920.0, perm_rating=1.0, hatch="concrete",
             color="#e4ddc9", finish="roman-maximus-brick",
             source="garage wainscot — Glen-Gery Columbia Roman Maximus, ASTM C216 Grade SW Type FBA (severe weathering; Type FBA rather than FBS because the handmade process gives it intentional dimensional variation), an off-white/ivory through-body colour, a SINGLE body and not a blend: a chip or a trimmer scar exposes the same colour rather than a red core, and Grade SW is not optional at 40+ freeze-thaw cycles a year"),
    # cmu, grout (porch railing wythe/balcony post bases) were promoted to
    # library/materials.py on 2026-08-22 (CONTRIBUTING §Promotion flow); they arrive here
    # through STARTER_MATERIALS above.
    # The house's one exterior dark (2026-08-01): every dark metal element on the
    # envelope — rake/eave/ridge trim coil, opening casings, guards — shares this value.
    # #1c1f24, not the #3a3d40 it started at: colour here is an albedo, and the viewer's
    # lighting (0.8 hemisphere + 0.9 key + 0.6 IBL) lifts a dark surface well above its
    # albedo — #3a3d40 arrived near #525252 (generic grey). Not pure black either: zero
    # albedo kills the shading that makes folds/posts read as solids.
    # Deliberately not named "*seam*" — renderers key the ribbed standing-seam finish off
    # that substring and this is flat brake-formed stock.
    Material(tag="metal-dark-exterior", name="Near-black painted metal (exterior)",
             r_per_inch=0.0, density=7850.0, perm_rating=0.0, hatch="metal",
             color="#1c1f24",
             source="RF-HOUSE rake/eave/ridge trim coil, opening casings, exterior guards"),
    # The garage's accent coil (2026-08-26, settled 2026-08-27). Brake-formed PVDF-coated
    # stock in the same family as `metal-dark-exterior` above, sharing its reasoning: colour
    # is an albedo, so it is authored a step darker than the chip reads in hand, and it is
    # NOT named "*seam*" — renderers key the ribbed standing-seam finish off that substring
    # and this is flat formed trim. It is keyed into the two renderer palettes BY TAG
    # (`_FINISH_BASE` in emit/gltf/palette.py, `FINISH_BASE` in ui/src/nordic/palette.ts,
    # kept in step by hand) rather than by a declared `finish`, because a fascia and a ridge
    # cap are framed MEMBERS: `memberColor` is handed the palette and no catalog, so a
    # material's authored `color` is invisible to it and only the tag lookup reaches. That is
    # the same reason `metal-dark-exterior` above is tag-keyed.
    #
    # `metal-copper-penny` — the garage's ONE accent coil, carrying both the vented ridge cap
    # and all six fascia pieces (2026-08-27). Two members, one coil, one order: the fascia is
    # named on the `FasciaBoard` in `_GARAGE_EAVE_TRIM` and the cap through
    # `Roof.edge_trim_material` on RF-GARAGE, and the two paths landing on one material is
    # the point — a cap in a different colour from the fascia under it reads as a mistake
    # rather than as a choice. The fascia wore Western States "Regal Blue" for part of
    # 2026-08-26 (see `metal-fascia-regal-blue` below, kept and unreferenced).
    #
    # THE FASCIA'S SUBSTRATE CHANGED WITH ITS COLOUR, and that is the durable half of this.
    # The weather face was 5/4 cellular PVC; a PVDF metallic is a metal coil finish PVC
    # cannot be ordered in, and a dark trim colour on cellular PVC is the classic failure —
    # PVC's thermal movement is high enough that trim makers require a solar-reflective
    # vinyl-safe coating for dark colours and cap the LRV outright. Formed metal over the
    # existing 2x6 spf sub-fascia nailer has neither problem and is the ordinary detail on a
    # metal-roofed building. The SOFFIT stays cellular PVC: it is vented, out of the weather,
    # and white under an overhang is what keeps a soffit from reading as a shadow.
    #
    # A metallic PVDF is a two-coat mica/pearl system, so it reads differently by viewing
    # angle in a way a flat albedo cannot express — this is the mid-tone of that range.
    Material(tag="metal-copper-penny", name="Copper Penny PVDF-coated formed metal trim",
             r_per_inch=0.0, density=7850.0, perm_rating=0.0, hatch="metal",
             color="#8a4f2a",
             source="RF-GARAGE vented ridge cap + the six garage eave/rake fascia pieces — \"Copper Penny\" PVDF/Kynar metallic (mica) coil over 24 ga. steel, the standard trade colour for a copper look without copper's cost or its runoff staining; brake-formed, and on the fascia lapped over a 2x6 spf sub-fascia nailer. A metallic is angle-dependent and this hex is the mid-tone, so a physical chip governs"),
    # `metal-fascia-regal-blue` — Western States "Regal Blue"
    # (westernstatesmetalroofing.com/regal-blue), PVDF. **Referenced by nothing**: the garage
    # fascia wore it for part of 2026-08-26 and went to the copper penny above on 2026-08-27.
    # Kept the way `glazed-green-brick` and `standing-seam-nailstrip-26-green` are kept — a
    # solid-colour PVDF is the same product on the same substrate as the metallic, so going
    # blue again is a one-word `material=` swap on the FasciaBoard rather than a
    # re-derivation. The substrate argument above is what must NOT be reverted with it.
    Material(tag="metal-fascia-regal-blue", name="Regal Blue PVDF-coated formed metal fascia",
             r_per_inch=0.0, density=7850.0, perm_rating=0.0, hatch="metal",
             color="#1e3a5c",
             source="garage eave + rake fascia weather face, 2026-08-26 only — Western States Metal Roofing \"Regal Blue\", PVDF/Kynar over 24 ga. steel; the manufacturer publishes no hex (its own page warns the on-screen swatch differs from the panel), so this value is an approximation and a physical chip governs"),
    # The above-grade foundation band on CATLIN_BASEMENT_8/_12 (2026-08-18). Aluminium-faced
    # rigid protection panel — the trade product for exactly this, and what
    # notes/basement_to_framed_wall_detail.md already called for in prose ("rigid metal/PVC
    # trim") and what the detail sheet has always drawn here in "metal-dark". 1/2" so it
    # matches ``FOUNDATION_FACE.protection_board_in`` and the drawing needs no change; the
    # house's one exterior dark (#1c1f24) so the band reads with the rake trim and the
    # opening casings above it rather than as a grey skirt under them.
    Material(tag="foundation-protection-panel",
             name="Aluminium-faced foundation protection panel (1/2\")",
             r_per_inch=0.0, density=1100.0, perm_rating=0.0, hatch="metal",
             color="#1c1f24",
             source="above-grade band over basement exterior XPS, N/E/W (CATLIN_BASEMENT_8, CATLIN_BASEMENT_12)"),
    # stucco (porch railing CMU back face + basement parge coat), composite-deck (porch
    # floor) and aluminum-deck (balcony plank) were promoted to library/materials.py on
    # 2026-08-22 (CONTRIBUTING §Promotion flow); they arrive here through
    # STARTER_MATERIALS above.
    Material(tag="post-paint-white", name="White-painted PT lumber", r_per_inch=1.24,
             density=500.0, perm_rating=1.0, hatch="lumber", color="#f4f2ee",
             source="balcony 6x6 pillars, exterior white paint; painted softwood ~1 perm-in"),
    # retaining-block (raised garden outer face), polycarbonate-multiwall (breezeway
    # glazing) and aluminum-extrusion (breezeway glazing trim) were promoted to
    # library/materials.py on 2026-08-22 (CONTRIBUTING §Promotion flow); they arrive here
    # through STARTER_MATERIALS above.
]

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
# CATLIN_EXT_2X6 verbatim, restated rather than composed because the editable dialect has
# no way to splice one assembly's layers into another. Keep the two in step by hand.
#
# CATLIN_EXT_2X6 needs no re-engineering for this room and deliberately gets none, and the
# 2026-08-23 truss wall does not change that reading: 4" of 2 lb ccSPF at 1.6 perm-in runs
# about 0.4 perm — the SAME Class II the polyiso+EPS stack it replaced read, slow but real
# outward drying. The warning the CI stack carried (never foil-faced polyiso, which at 0.03
# perm would sandwich the stud bay between two vapour barriers with wet-prone wood at 25 F
# in between) is moot now that there is no board in the stack at all; it is left here as the
# reason the foam's permeance is a spec line and not an incidental.
PLANT_EXT_2X6_HUMID = Assembly(
    tag="PLANT_EXT_2X6_HUMID",
    layers=(
        *_HUMID_LINER,
        Layer(name="stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x6", sill_gasket=inch(0.0625),
                                  layout_origin="line", corner_style="4-stud"),
              cavity=CavityFill(material_ref="mineral-wool")),
        Layer(name="sheathing", material_ref="struct-1-plywood", thickness=inch(0.5),
              function=LayerFunction.SHEATHING),
        # BAND A, 0 - 1.5" off the sheathing. Continuous ccSPF, crossed only by the
        # block-1s the pass frames on the stud module. There is no WRB above it because
        # there is nothing left for one to do — ccSPF is air, water, vapour and thermal in
        # one bonded, seamless application. Sprayed FIRST, flush to the block-1 faces and
        # before the inner girts go on: a flat girt lying 1.5" off the sheathing shadows the
        # pocket behind it and the foam would void there otherwise.
        Layer(name="spray-foam", material_ref="closed-cell-spray-foam", thickness=inch(1.5),
              function=LayerFunction.INSULATION,
              control={ControlLayer.AIR, ControlLayer.WATER,
                       ControlLayer.VAPOR, ControlLayer.THERMAL}),
        # BAND B, 1.5 - 3.0". The INNER GIRT: plain SPF 2x4 laid flat, horizontal, 24" o.c.,
        # buried in the second foam lift and never wet. One 5" SDWS per block-1 through
        # girt + block + sheathing into the stud. `standoff="block"` is the whole selector
        # for `resolve/framing/truss_girts.py`; `layout_origin="line"` puts its blocks on
        # the same unified stud module the facade's studs and windows already sit on.
        #
        # Wood and foam here are a PARALLEL path, which is the whole reason the 4" of foam
        # is authored as three bands rather than one layer: a single 4" layer would credit
        # foam over 100% of the area and hide both girt tiers entirely. Split,
        # `analysis._layer_rsi` parallel-paths each band exactly as it already does a stud
        # bay, and the take-off bills the fills as `insulation (cavity)`.
        # ff 0.146 is 3.5" of flat girt per 24" course. The band A/C BLOCKS (3.2% each) are
        # modelled by the pass and are deliberately NOT authored as a fill — a plain
        # INSULATION layer carries no framing factor — so the card reads a little high and
        # notes/catlin_truss_engineering.md states the honest number.
        Layer(name="inner-girt", material_ref="spf", thickness=inch(1.5),
              function=LayerFunction.FURRING,
              framing=FramingSpec(member="2x4", direction="horizontal", laid="flat",
                                  spacing=inch(24), layout_origin="line",
                                  standoff="block"),
              cavity=CavityFill(material_ref="closed-cell-spray-foam",
                                thickness=inch(1.5), framing_factor=0.146,
                                control={ControlLayer.AIR, ControlLayer.WATER,
                                         ControlLayer.VAPOR, ControlLayer.THERMAL})),
        # BAND C, 3.0 - 4.5", authored as its two halves. The last 1" of the 4" foam total,
        # then the 1/2" vented gap the block-2s stand in. The applicator shaves this lift to
        # a gauge — inner girt face + 1" — because 1/2" is inside ccSPF surface tolerance;
        # the alternative margins are a 2" block-2 (1" gap) or 3-3/4" of foam. See the
        # engineering note's Risks.
        Layer(name="foam-vent", material_ref="closed-cell-spray-foam", thickness=inch(1.0),
              function=LayerFunction.INSULATION,
              control={ControlLayer.AIR, ControlLayer.WATER,
                       ControlLayer.VAPOR, ControlLayer.THERMAL}),
        Layer(name="vent-gap", material_ref="air-barrier", thickness=inch(0.5),
              function=LayerFunction.AIRGAP),
        # BAND D, 4.5 - 6.0". The OUTER GIRT: the cladding nailer, the window mount plane,
        # and the one treated layer in the wall — block-2 inherits its material, which is
        # what puts the two block tiers on two BOM rows. Same 24" courses at the SAME
        # elevations as the inner girt; one 5" SDWS per block-2 into the inner girt. It is
        # a 3-1/2"-deep horizontal ledge behind the cladding that will wet-cycle for the
        # life of the wall, which is why KDAT and not the vent alone carries it. No fill:
        # the gap behind it is the drainage plane and it vents.
        Layer(name="outer-girt", material_ref="kdat", thickness=inch(1.5),
              function=LayerFunction.FURRING,
              framing=FramingSpec(member="2x4", direction="horizontal", laid="flat",
                                  spacing=inch(24), layout_origin="line",
                                  standoff="block")),
        Layer(name="cladding", material_ref="pbr-panel-26", thickness=inch(1.25),
              function=LayerFunction.CLADDING),
    ),
    interfaces=(_STUD_BEARING,),
    source="notes/plant_room.md — CATLIN_EXT_2X6 outboard of a sealed PVC/membrane liner; the sheathing datum does not move (decision #43), the liner grows inward",
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
PLANT_INT_2X6_BRG_HUMID = Assembly(
    tag="PLANT_INT_2X6_BRG_HUMID",
    layers=(
        *_HUMID_LINER,
        Layer(name="stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x6", layout_origin="line"),
              cavity=CavityFill(material_ref="mineral-wool")),
        Layer(name="gwb-cold", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        _PAINT_FINISH_B,
    ),
    interfaces=(_STUD_BEARING,),
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
        _PAINT_FINISH_B,
    ),
    interfaces=(_STUD_BEARING,),
    source="notes/plant_room.md — plant room north partitions; humid liner one face, painted gypsum the other",
)

# --- construction rules: pre-resolve returns at mixed-assembly junctions (#45) ----------
# Typed declarations of the physical returns the junction solver leaves for framing/takeoff
# (documented via a Transition overlay, never drawn; none mutate construction geometry):
# a PT sill where framed walls land on concrete, the sauna liner wrapping the center wall,
# foundation foam turning the corner, the masonry guard's corner return.
#
# ``wall:framed_on_concrete`` means what it says and not "on a concrete wall": since
# 2026-08-21 it also finds a framed wall standing on a concrete *slab*, which is every
# basement partition in this house and is the same IRC R317.1 detail — treated plate, sill
# gasket, capillary break. It used to find only wall-on-wall, so the sauna, ESS-closet and
# bathroom partitions ordered no treated plate at all, and the five walls the deck overhaul
# framed on the slab would have joined them.
CONSTRUCTION_RULES = [
    ConstructionRule(
        tag="CR-CONC-TO-FRAMED-SILL",
        applies_to="wall:framed_on_concrete",
        kind="bearing_plate",
        dimension=inch(1.5),
        takeoff_category="pt-sill-plate",
    ),
    ConstructionRule(
        tag="CR-SAUNA-LINER-RETURN",
        applies_to="wall:sauna_liner_return",
        kind="blocking",
        dimension=inch(3.5),
        takeoff_category="sauna-liner-return",
    ),
    ConstructionRule(
        tag="CR-FOUNDATION-FOAM-RETURN",
        applies_to="wall:foundation_foam_return",
        kind="blocking",
        dimension=inch(24.0),
        takeoff_category="foundation-foam-return",
    ),
    # Named for the porch parapet it was written for, but that was never its only host: it
    # binds every masonry-to-masonry corner, and with the porch parapet retired (2026-08-18)
    # its eight remaining returns are all on the raised garden's dry-stacked SRW block
    # corners (N-RG-NE/NW/SE/SW). Kept under the old tag on purpose — the returns are stable
    # GlobalIds, and renaming the rule would reissue every one of them.
    ConstructionRule(
        tag="CR-PORCH-MASONRY-RETURN",
        applies_to="wall:porch_masonry_return",
        kind="blocking",
        dimension=inch(7.625),
        takeoff_category="masonry-corner-return",
    ),
    # The plant room's rim bands (2026-08-18). FS-S-WEST (the truss half since 2026-08-21)
    # and FS-ATTIC both run their joists in x, so their ends bear on W-S-W4 and a parallel
    # rim bay sits against W-S-S1 — two
    # direct paths from a floor cavity into the coldest part of an exterior wall, and neither
    # can take a sheet membrane, because there is no continuous plane to lap one onto between
    # joist ends. Closed-cell foam is the only product that is the insulation, the air
    # barrier and the vapour retarder at once in a cavity that shape.
    #
    # It is a ConstructionRule and not just a Transition because a Transition documents and
    # cannot bill (#45): TR-CATLIN-PLANT-RIM draws the detail, this puts the foam in the
    # takeoff. 3" is the specified depth — deep enough to be the retarder (about 0.53 perm)
    # rather than only the air seal.
    #
    # `scope_ref` because which rooms are run wet is a room decision, not a property of the
    # deck or the wall type — the same reasoning CR-LIVING-CEIL-RC's scope carries.
    ConstructionRule(
        tag="CR-PLANT-RIM-FOAM",
        applies_to="wall:rim_cavity_foam",
        kind="blocking",
        dimension=inch(3.0),
        takeoff_category="rim-spray-foam",
        scope_ref="RM-S-PLANT",
    ),
    # Resilient channel under the living room only: bedrooms sit directly over it, and 5/8"
    # gypsum screwed straight to the I-joists would carry footfall as impact noise. Scoped to
    # RM-M-LIVING (a room decision, not FS-S-EAST's, the half above it since 2026-08-21) —
    # the rest of that ceiling is screwed direct. A full layered-ceiling assembly is
    # deliberately deferred; this just bills the channel (gypsum comes via FS-S-EAST's
    # `ceiling_below`).
    # (That gap closed on 2026-08-18: `construction_returns` is a priced section. The
    # channel itself is PRICED — prices.toml [construction_returns] `resilient-channel`,
    # 522.2 LF at $1.35-2.25/LF installed. This comment said it was "still left unpriced on
    # purpose" until 2026-08-22 and had been wrong since the rate was authored; the sill
    # plate is the row that is deliberately blank, because a PT sill is lumber [framing]
    # already bought. Channel is not — nothing else in the file buys it.)
    ConstructionRule(
        tag="CR-LIVING-CEIL-RC",
        applies_to="floor:ceiling_channel",
        kind="furring",
        dimension=inch(16),
        takeoff_category="resilient-channel",
        scope_ref="RM-M-LIVING",
    ),
]

ASSEMBLIES = [
    CATLIN_EXT_2X6,
    CATLIN_EXT_2X6_SWINBURNE,
    CATLIN_ROOF,
    CATLIN_BASEMENT_12,
    CATLIN_BASEMENT_8,
    CATLIN_BASEMENT_8_GARDEN,
    CATLIN_SLAB_FLOOR,
    CATLIN_DECK_EPS_INT,
    FOUNDATION_WALL_12_INT,
    SUNKEN_GARDEN_WALL,
    SUNKEN_GARDEN_COLUMN_16,
    BASEMENT_BRICK_VENEER,
    RETAINING_BLOCK_12,
    PORCH_DECK_COMPOSITE,
    BREEZEWAY_ROOF_GLAZING,
    BREEZEWAY_GLAZED_WALL,
    BALCONY_DECK_ALUMINUM,
    POST_WHITE_PAINT,
    ELM_TIMBER,
    BEAM_LVL,
    BEAM_KDAT,
    POST_KDAT,
    PIER_CONCRETE_12,
    RAILING_DARK_METAL,
    GARAGE_ICF_6,
    GARAGE_ICF_6_BRICKLEDGE,
    GARAGE_BRICK_WAINSCOT,
    GARAGE_WALL_2X6,
    GARAGE_SLAB_ON_GRADE,
    SG_FROST_WING_XPS1,
    SG_FROST_WING_XPS2,
    FOOTING_FPSF_20,
    GARAGE_ROOF,
    CATLIN_INT_2X6_BRG,
    CATLIN_INT_2X4_BOOKCASE_12,
    INT_2X6_PLUMBING,
    INT_2X6_STAGGERED_PLUMBING,
    INT_2X4_PARTITION,
    INT_2X4_STAGGERED_DOUBLE_GWB,
    INT_ESS_CLOSET_STEEL,
    SAUNA_2X4,
    SAUNA_LINER_ON_CONCRETE,
    SAUNA_LINER_ON_BASEMENT_8_GARDEN,
    PLANT_EXT_2X6_HUMID,
    PLANT_INT_2X6_BRG_HUMID,
    PLANT_INT_2X4_HUMID,
    CATLIN_MUDROOM_INT_2X6_EXPOSED,
    CATLIN_STAIRWALL_INT_2X6_BRG,
    CATLIN_STAIRWALL_INT_2X6_BRG_TYPEX,
]
