# haus: editable
# Catlin house assemblies — ported from catlin-house ifcplot (WP3.1).
# Layer order is interior → exterior. The exterior wall family is one 2x6 stack on every
# framed storey (sheathing / WRB / 2" polyiso / 2" EPS / furring / standing seam), so the
# sheathing plane and every control layer are continuous with no stud-depth jog.
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
from library import INT_2X4_PARTITION, STARTER_MATERIALS

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
CATLIN_EXT_2X6 = Assembly(
    tag="CATLIN_EXT_2X6",
    layers=(
        Layer(name="stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x6", sill_gasket=inch(0.25)),
              cavity=CavityFill(material_ref="mineral-wool")),
        Layer(name="sheathing", material_ref="struct-1-plywood", thickness=inch(0.5),
              function=LayerFunction.SHEATHING),
        Layer(name="wrb", material_ref="air-barrier", thickness=inch(0.02),
              function=LayerFunction.MEMBRANE,
              control={ControlLayer.AIR, ControlLayer.WATER}),
        Layer(name="polyiso", material_ref="polyiso", thickness=inch(2.0),
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
        Layer(name="eps", material_ref="eps", thickness=inch(2.0),
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
        Layer(name="furring", material_ref="spf", thickness=inch(0.5),
              function=LayerFunction.FURRING,
              framing=FramingSpec(member="1x4", direction="vertical")),
        Layer(name="cladding", material_ref="standing-seam-snaplock", thickness=inch(0.5),
              function=LayerFunction.CLADDING),
    ),
    interfaces=(_STUD_BEARING,),
    default_lining=_GWB_LINING,
    source="catlin-house ifcplot/catlin_house.py wall siding stack; main-storey studs are LSL, second/attic standard dimensional 2x6",
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
# **Two basement assemblies, because the north/east/west walls and the south wall are two
# genuinely different conditions.** Both are the same 12" pour with the same damp-proofing
# and the same 4" of exterior XPS; they differ only in what covers that foam, and they
# differ because what exposes it is different.
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
# the full-height parge coat, and keeps CATLIN_BASEMENT_12_GARDEN to say so.
#
# Both carry the same 4.55" outboard of the concrete face (damp-proof + 2x XPS + a 1/2"
# outer skin), which is what N-B-BRICK-W/-E's inch(-4.55) stand-off is measured from — the
# panel is deliberately the same 1/2" as the parge it replaces so that number never moves.
CATLIN_BASEMENT_12 = Assembly(
    tag="CATLIN_BASEMENT_12",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(12.0),
              function=LayerFunction.STRUCTURE),
        Layer(name="damp-proof", material_ref="air-barrier", thickness=inch(0.05),
              function=LayerFunction.MEMBRANE,
              control={ControlLayer.AIR, ControlLayer.WATER}),
        Layer(name="xps-a", material_ref="xps", thickness=inch(2.0),
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
        Layer(name="xps-b", material_ref="xps", thickness=inch(2.0),
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
        # The exposed-foundation band (2026-08-18, deeper since 2026-08-21). Runs from 6"
        # *below* grade — so no foam edge shows at the soil line, and so the panel is what
        # the shovel hits rather than the XPS — up to the top of the wall at 0'-0", where
        # its head tucks under the rainscreen's Z-flashing with the bug screen above it. It
        # replaces the full-height parge this wall used to claim over nine feet of buried
        # foam: the parge was added 2026-08-01 for the *south* wall's exposure and applied
        # to all four sides because a layer had no way to say "only here".
        Layer(name="protection-panel", material_ref="foundation-protection-panel",
              thickness=inch(0.5), function=LayerFunction.CLADDING,
              extent=LayerExtent(
                  bottom=LayerBound(datum=LayerDatum.GRADE, offset=inch(-6)))),
    ),
    interfaces=(_CONCRETE_BEARING,),
    source="catlin-house basement N/E/W: 12\" wall + 2x2\" exterior XPS + above-grade protection panel",
)

# The south wall's stack, hoisted so the bare garden wall and the sauna-liner variant of it
# (SAUNA_LINER_ON_BASEMENT_12_GARDEN, below) share one source of truth rather than two
# hand-kept copies — the shape _SAUNA_LINER / _HUMID_LINER already use. Interior→exterior,
# starting at the concrete: whatever is inboard of the pour is the variant's business.
_GARDEN_CONCRETE_STACK = (
    Layer(name="concrete", material_ref="concrete", thickness=inch(12.0),
          function=LayerFunction.STRUCTURE),
    Layer(name="damp-proof", material_ref="air-barrier", thickness=inch(0.05),
          function=LayerFunction.MEMBRANE,
          control={ControlLayer.AIR, ControlLayer.WATER}),
    Layer(name="xps-a", material_ref="xps", thickness=inch(2.0),
          function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
    Layer(name="xps-b", material_ref="xps", thickness=inch(2.0),
          function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
    # Parge coat over mesh (2026-08-01): exposed XPS degrades under UV/impact, and here
    # the exposure runs the full south wall from the sunken garden floor to the
    # main-storey siding — bare pink foam was reading as the wall's finish. Reuses the
    # porch railing's Portland-cement stucco; rides outboard of everything so the
    # concrete face (the footings/damp-proofing/drain-tile datum) is untouched. Full
    # height and staying that way: this face has no grade line on it to band against.
    Layer(name="parge", material_ref="stucco", thickness=inch(0.5),
          function=LayerFunction.FINISH),
)

# The south wall, which the sunken garden opens to the air over its whole 9'.
CATLIN_BASEMENT_12_GARDEN = Assembly(
    tag="CATLIN_BASEMENT_12_GARDEN",
    layers=(
        *_GARDEN_CONCRETE_STACK,
    ),
    interfaces=(_CONCRETE_BEARING,),
    source="catlin-house basement south: 12\" wall + 2x2\" exterior XPS + full-height parge over the sunken garden",
)

# Basement slab-on-grade: 3" XPS below the slab (R-15 @ 40 psi compressive — rated for
# slab loading, not the lighter foundation-wall grade) breaks direct slab-to-clay contact.
CATLIN_SLAB_FLOOR = Assembly(
    tag="CATLIN_SLAB_FLOOR",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(3.5),
              function=LayerFunction.STRUCTURE),
        Layer(name="xps-below", material_ref="xps", thickness=inch(3.0),
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
    ),
    source="catlin-house basement slab: 3\" below-slab XPS, R-15 @ 40 psi compressive",
)

# Main-floor structural deck: an EPS stay-in-place form with a cast concrete cap, over the
# (conditioned) basement — so it is an interior floor, not an envelope slab. The "INT" tag
# token is the codebase's signal for that (see CATLIN_CONC_12_INT, INT_2X6_PLUMBING) — it
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
# The depth is the whole point. 4 5/8" cap + 8" form = 12 5/8", which is exactly
# FS-SECOND's 11 7/8" I-joist plus its 3/4" plywood subfloor: same soffit plane, same
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
        Layer(name="concrete-cap", material_ref="concrete", thickness=inch(4.625),
              function=LayerFunction.STRUCTURE),
        Layer(name="eps-form", material_ref="eps-deck-form", thickness=inch(8.0),
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
    source="catlin-house main-floor deck — BuildDeck/LiteDeck 8\" EPS stay-in-place form with a 4 5/8\" cast cap (12 5/8\" total, matching FS-SECOND's joist + subfloor), steel furring rib and a 5/8\" gypsum R316.4 thermal barrier under it; replaced CATLIN_DECK_9_INT 2026-08-21",
)

CATLIN_CONC_12_INT = Assembly(
    tag="CATLIN_CONC_12_INT",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(12.0),
              function=LayerFunction.STRUCTURE),
    ),
    interfaces=(_CONCRETE_BEARING,),
)

CATLIN_CONC_8_INT = Assembly(
    tag="CATLIN_CONC_8_INT",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(8.0),
              function=LayerFunction.STRUCTURE),
    ),
    interfaces=(_CONCRETE_BEARING,),
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
# There is no CMU backer wythe here, because the existing CATLIN_BASEMENT_12 concrete
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
# the opening rather than floating above it. The brick reveal AO-B-BRICK-DOOR crowns 4" under
# that band (2026-08-21): it was first cut to 88" so the band sprang straight off the crown,
# and with no course between them the arch read as sawn off. The lower register caps the
# plinth and crosses the door's foot. AO-B-BRICK-WIN (sill 29", head 55") sits wholly inside
# `brick-field-lo` and is untouched by any band edge.
#
# STRUCTURE, not CLADDING, on every region: this wythe has nothing behind it in this
# assembly (the backer is a *different wall*), so it has to be the structure layer or
# integrity.assembly_layers finds none. Same precedent as RETAINING_BLOCK_12.
_VENEER_WYTHE = inch(3.625)
BASEMENT_BRICK_VENEER = Assembly(
    tag="BASEMENT_BRICK_VENEER",
    layers=(
        Layer(name="air-gap", material_ref="air-barrier", thickness=inch(1.0),
              function=LayerFunction.AIRGAP),
        # 9 courses of ordinary unglazed brown brick — the cheapest face on the wall, and
        # the one the wall stands out of the ground on.
        Layer(name="brick-plinth", material_ref="brown-brick", thickness=_VENEER_WYTHE,
              function=LayerFunction.STRUCTURE, slot="wythe",
              extent=LayerExtent(
                  bottom=LayerBound(datum=LayerDatum.WALL_BASE, offset=inch(0.0)),
                  top=LayerBound(datum=LayerDatum.WALL_BASE, offset=inch(24.0)))),
        # 2 courses of gold capping the plinth.
        Layer(name="brick-band-lo", material_ref="glazed-gold-brick", thickness=_VENEER_WYTHE,
              function=LayerFunction.STRUCTURE, slot="wythe",
              extent=LayerExtent(
                  bottom=LayerBound(datum=LayerDatum.WALL_BASE, offset=inch(24.0)),
                  top=LayerBound(datum=LayerDatum.WALL_BASE, offset=inch(29.333)))),
        # The field: 22 courses of lapis, plinth cap to door head.
        Layer(name="brick-field-lo", material_ref="glazed-lapis-brick",
              thickness=_VENEER_WYTHE,
              function=LayerFunction.STRUCTURE, slot="wythe",
              extent=LayerExtent(
                  bottom=LayerBound(datum=LayerDatum.WALL_BASE, offset=inch(29.333)),
                  top=LayerBound(datum=LayerDatum.WALL_BASE, offset=inch(88.0)))),
        # 2 courses of gold on the door head line, springing off the arch crown.
        Layer(name="brick-band-hi", material_ref="glazed-gold-brick", thickness=_VENEER_WYTHE,
              function=LayerFunction.STRUCTURE, slot="wythe",
              extent=LayerExtent(
                  bottom=LayerBound(datum=LayerDatum.WALL_BASE, offset=inch(88.0)),
                  top=LayerBound(datum=LayerDatum.WALL_BASE, offset=inch(93.333)))),
        # The lapis cap above the upper register. Open top on purpose: `top=None` is the
        # wall's own top, which is the only way to say "run it out" without writing this
        # wall's 8'-9" into an assembly type that any wall may use.
        Layer(name="brick-field-hi", material_ref="glazed-lapis-brick",
              thickness=_VENEER_WYTHE,
              function=LayerFunction.STRUCTURE, slot="wythe",
              extent=LayerExtent(
                  bottom=LayerBound(datum=LayerDatum.WALL_BASE, offset=inch(93.333)))),
    ),
    source="basement south veneer over the sunken garden — the Ishtar scheme (2026-08-20): lapis glazed field with golden-yellow register bands over an unglazed brown plinth, one 3 5/8\" wythe banded by Layer.slot, 1\" airgap, corrugated masonry ties back to the existing CATLIN_BASEMENT_12 wall (no CMU backer: the basement concrete is the backer). Was one flat field of glazed-green-brick, which is still in the catalog for a one-word revert",
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
GARAGE_ICF_EPS = inch(2.5)
GARAGE_ICF_CORE = inch(6.0)

GARAGE_ICF_6 = Assembly(
    tag="GARAGE_ICF_6",
    layers=(
        Layer(name="eps-int", material_ref="icf-eps", thickness=GARAGE_ICF_EPS,
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
        Layer(name="concrete", material_ref="concrete", thickness=GARAGE_ICF_CORE,
              function=LayerFunction.STRUCTURE,
              masonry=MasonrySpec(unit_size="ICF-6", core_fill=True,
                                  rebar_spacing=inch(16))),
        Layer(name="eps-ext", material_ref="icf-eps", thickness=GARAGE_ICF_EPS,
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
    ),
    source="catlin-house ifcplot/assemblies.py GARAGE_ICF (6\" core)",
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
              framing=FramingSpec(member="2x6", sill_gasket=inch(0.25))),
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
    ),
    source="catlin-house detached garage floor — 3\" below-slab XPS on compacted base",
)

# The step-down inside the garage service door (ST-G-STEPS in params/foundations.py). The
# door threshold stayed at 0'-0" with the breezeway deck when grade dropped 2'-6" on
# 2026-08-18, and the slab stayed at grade, so five 6" risers now stand between them. Plain
# 6" concrete on compacted base: no below-slab XPS, because these bear on the fill inside
# the stem's own thermal break rather than on the ground plane the slab insulates.
GARAGE_STEP_CONCRETE = Assembly(
    tag="GARAGE_STEP_CONCRETE",
    layers=(
        Layer(name="concrete", material_ref="concrete", thickness=inch(6.0),
              function=LayerFunction.STRUCTURE),
    ),
    source="catlin-house garage service-door step-down — 6\" concrete on compacted base",
)

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
CATLIN_INT_2X6_BRG = Assembly(
    tag="CATLIN_INT_2X6_BRG",
    layers=(
        _PAINT_FINISH_A,
        Layer(name="gwb-a", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6")),
        Layer(name="gwb-b", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        _PAINT_FINISH_B,
    ),
    interfaces=(_STUD_BEARING,),
    source="catlin-house centerline bearing wall (2x6)",
)

INT_2X6_PLUMBING = Assembly(
    tag="INT_2X6_PLUMBING",
    layers=(
        _PAINT_FINISH_A,
        Layer(name="gwb-a", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6")),
        Layer(name="gwb-b", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        _PAINT_FINISH_B,
    ),
    interfaces=(_STUD_BEARING,),
    source="wet wall — depth for 3\" stacks",
)

# Non-bearing wet walls: 2x4 studs staggered on 2x6 plates — same 5.5" pipe cavity as
# INT_2X6_PLUMBING (which stays for any *bearing* wet wall, needing continuous studs),
# but the staggered studs decouple the two faces for noise and leave a continuous
# cavity that never needs a stud bored on the way through.
INT_2X6_STAGGERED_PLUMBING = Assembly(
    tag="INT_2X6_STAGGERED_PLUMBING",
    layers=(
        _PAINT_FINISH_A,
        Layer(name="gwb-a", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        Layer(name="staggered-studs", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x4", plate_member="2x6", spacing=inch(16),
                                  layout=PartitionLayout.STAGGERED,
                                  stagger_gap=inch(1.5)),
              cavity=CavityFill(material_ref="fiberglass", thickness=inch(3.5))),
        Layer(name="gwb-b", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
        _PAINT_FINISH_B,
    ),
    interfaces=(_STUD_BEARING,),
    source="wet wall, non-bearing — 2x4 staggered on 2x6 plates per USG/GA WP 5530 (16\" o.c. per face, 8\" combined), 3.5\" fiberglass sound batt",
)

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
# Bounding the liner at WALL_TOP - 1'-6" keeps the takeoff from billing basswood T&G, furring
# and foil-faced polyiso over the 1'-6" of concrete above the sauna's ceiling.
# PROVISIONAL: if the basement ever goes to a joist ceiling running the full width, the liner
# would run the wall's whole height and this extent should come back off.
_SAUNA_CEILING_EXTENT = LayerExtent(
    top=LayerBound(datum=LayerDatum.WALL_TOP, offset=inch(-18.0)))

SAUNA_LINER_ON_BASEMENT_12_GARDEN = Assembly(
    tag="SAUNA_LINER_ON_BASEMENT_12_GARDEN",
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
        *_GARDEN_CONCRETE_STACK,
    ),
    interfaces=(_CONCRETE_BEARING,),
    source="catlin-house sauna_basement_wall_detail.py + CATLIN_BASEMENT_12_GARDEN (liner on the sunken-garden foundation wall)",
)

# --- mudroom exposed-stud wall ---------------------------------------------------
# W-M-STRW only. No default_lining, deliberately (like SAUNA_2X4): the mudroom face is a
# finished face made of the framing itself, not drywall left off. The open 2x6 bays are the
# coat nooks, so no cavity fill either — insulating them would fill the nooks, and both
# sides are conditioned anyway. Stair side closes with 3/4" cabinet plywood: stair finish
# and screw-anywhere hook backing at once. "INT" in the tag is load-bearing (see
# CATLIN_CONC_12_INT, INT_2X6_PLUMBING, _is_interior_assembly in mn_energy.py) — without it
# the uninsulated bays would fail as an exterior wall against R-21.
CATLIN_MUDROOM_INT_2X6_EXPOSED = Assembly(
    tag="CATLIN_MUDROOM_INT_2X6_EXPOSED",
    layers=(
        Layer(name="stud", material_ref="df-select-s4s", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6")),
        Layer(name="ply-stair", material_ref="cabinet-plywood", thickness=inch(0.75),
              function=LayerFunction.FINISH),
    ),
    interfaces=(_STUD_BEARING,),
    source="plans/TODO.md — mudroom coat wall: exposed Select Structural S4S 2x6 DF studs on the mudroom face (open bays = coat nooks), 3/4\" cabinet-grade plywood on the stair face",
)

MATERIALS = [
    *STARTER_MATERIALS,
    # The EPS stay-in-place deck form (CATLIN_DECK_EPS_INT). Deliberately *not* `icf-eps`,
    # whose R-4.0/inch is the bead EPS on its own: this section is ribbed, and the concrete
    # that fills the ribs bridges it. BuildDeck publishes R-25 for the 8" section as
    # installed, which is R-3.125/inch through the finished deck — the number that belongs
    # in a thermal model of this floor, and 22% below the bare-foam figure.
    Material(tag="eps-deck-form", name="EPS stay-in-place deck form", r_per_inch=3.125,
             perm_rating=3.9, hatch="rigid", color="#f0f0e6",
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
    # --- the four metal skins (2026-08-20) --------------------------------------
    # The house is clad in metal in FOUR specifications. They are all the same white PVDF
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
    #   `standing-seam-snaplock` — 24 ga, SNAP-LOCK. The house walls, CATLIN_EXT_2X6 and
    #       PLANT_EXT_2X6_HUMID. Concealed floating clips like the seamed roof, but the male
    #       and female legs engage under hand pressure, so there is no seaming pass. Roughly
    #       $2-4/SF cheaper installed than mechanical seam.
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
    # Every building-science number on all four is `standing-seam`'s verbatim — continuous
    # sheet steel is vapour-impermeable and carries no R whatever its gauge or seam — so
    # nothing here changes an energy or a Glaser result. Keep them in step by hand.
    #
    # The tags keep the substring "seam" ON PURPOSE: `ui/src/three/materials.isStandingSeam`
    # and `nordic/palette.familyOf` both key the ribbed metal finish off it, and a tag like
    # "nail-strip-steel" would render this house's walls as flat grey.
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
    Material(tag="polyiso-foil", name="Foil-faced polyisocyanurate", r_per_inch=6.0,
             perm_rating=0.03, hatch="rigid", color="#d9d2a8",
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
    Material(tag="cmu", name="Grouted CMU (8\")", r_per_inch=0.11, density=2000.0,
             perm_rating=2.5, hatch="concrete", color="#b8b3ab", finish="cmu",
             source="porch railing inner wythe (grouted cores); concrete masonry ~2-3 perm-in"),
    Material(tag="grout", name="Masonry grout", r_per_inch=0.08, density=2240.0,
             perm_rating=2.5, hatch="concrete", color="#9a958c",
             source="fills the CMU cores for balcony post bases; cementitious grout ~2-3 perm-in"),
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
    # The above-grade foundation band on CATLIN_BASEMENT_12 (2026-08-18). Aluminium-faced
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
             source="above-grade band over basement exterior XPS, N/E/W (CATLIN_BASEMENT_12)"),
    Material(tag="stucco", name="Portland-cement stucco", r_per_inch=0.20, density=1900.0,
             perm_rating=10.0, hatch="concrete", color="#d9d2c4",
             # Two jobs, one product: the porch railing's CMU back-face finish, and the
             # basement wall's parge coat over its exterior XPS (CATLIN_BASEMENT_12).
             source="porch railing CMU back face; basement exterior-XPS parge coat"),
    Material(tag="composite-deck", name="Composite decking (capped PVC/wood)",
             r_per_inch=1.0, density=1000.0, perm_rating=0.5, hatch="lumber", color="#8a7f70",
             source="porch floor walking surface; PVC-capped composite ~0.5 perm-in (low)"),
    Material(tag="aluminum-deck", name="Aluminum deck board (Wahoo AridDeck-style)",
             r_per_inch=0.0, density=2700.0, perm_rating=0.05, hatch="metal", color="#b9bcc0",
             source="balcony waterproof aluminum plank; metal is effectively vapor-impermeable"),
    Material(tag="post-paint-white", name="White-painted PT lumber", r_per_inch=1.24,
             density=500.0, perm_rating=1.0, hatch="lumber", color="#f4f2ee",
             source="balcony 6x6 pillars, exterior white paint; painted softwood ~1 perm-in"),
    # --- raised garden ---------------------------------------------------------
    # Dry-stacked segmental retaining-wall (SRW) block. A precast concrete masonry unit, so
    # it renders on the existing "cmu" finish recipe rather than inventing a new one; the
    # split-face grey is a shade darker than the porch railing's grouted CMU.
    Material(tag="retaining-block", name="Segmental concrete retaining-wall block",
             r_per_inch=0.08, density=2200.0, perm_rating=2.5, hatch="concrete",
             color="#a8a49c", finish="cmu",
             source="raised garden outer face — dry-stacked SRW units, no mortar"),
    # --- breezeway glazing -----------------------------------------------------
    # 16mm five-wall polycarbonate. `color` is authored, not inferred: the palette's
    # substring-ordered family inference matches ("poly","rigid") first and would render this
    # as bright-yellow rigid foam otherwise. The alpha byte is what reads as glazing rather
    # than a solid panel (alphaMode BLEND below 1.0 in emit/gltf/scene.py).
    # Permeance ~0.012 perms, from EN 16153's 3.8e-5 mg/(m·h·Pa) converted and stored as
    # product permeance across the 16mm sheet (not divided again by thickness) — Class I.
    Material(tag="polycarbonate-multiwall", name="Multiwall polycarbonate glazing (16mm)",
             r_per_inch=1.54, density=1200.0, vapor_permeance_perms=0.012,
             hatch="glass", color="#cfe3e8b0",
             finish="polycarbonate",
             source="SABIC LEXAN THERMOCLEAR multiwall declaration EN 16153:2013+A1:2015 https://ff.sabic.eu/uploads/resources/DoP%20LT2UV329X38%20-%202023.pdf"),
    # Mill-finish extruded aluminium: the U/H/F channels, the glazing bars, and the panel
    # fasteners' washers. "alum" matches no needle in the family inference at all, so this
    # colour is authored for the same reason the polycarbonate's is.
    Material(tag="aluminum-extrusion", name="Extruded aluminium glazing bar / channel",
             r_per_inch=0.0007, density=2700.0, perm_rating=0.0, hatch="metal",
             color="#b6bac0",
             source="breezeway glazing trim — mill-finish 6063-T5 extrusion"),
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
# CATLIN_EXT_2X6 needs no re-engineering for this room and deliberately gets none: the
# model's `polyiso` is 1.0 perm-in and `eps` 3.9, so the exterior CI stack runs about
# 0.4 perm — Class II, slow but real outward drying. THE POLYISO MUST BE GLASS-FACED OR
# UNFACED, NEVER FOIL-FACED. Foil-faced (the house's own `polyiso-foil`, 0.03 perm) would
# sandwich the stud bay between two vapour barriers with wet-prone wood at 25 F in between,
# and the model would not catch it because it carries the permeable number.
PLANT_EXT_2X6_HUMID = Assembly(
    tag="PLANT_EXT_2X6_HUMID",
    layers=(
        *_HUMID_LINER,
        Layer(name="stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x6", sill_gasket=inch(0.25)),
              cavity=CavityFill(material_ref="mineral-wool")),
        Layer(name="sheathing", material_ref="struct-1-plywood", thickness=inch(0.5),
              function=LayerFunction.SHEATHING),
        Layer(name="wrb", material_ref="air-barrier", thickness=inch(0.02),
              function=LayerFunction.MEMBRANE,
              control={ControlLayer.AIR, ControlLayer.WATER}),
        Layer(name="polyiso", material_ref="polyiso", thickness=inch(2.0),
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
        Layer(name="eps", material_ref="eps", thickness=inch(2.0),
              function=LayerFunction.INSULATION, control={ControlLayer.THERMAL}),
        Layer(name="furring", material_ref="spf", thickness=inch(0.5),
              function=LayerFunction.FURRING,
              framing=FramingSpec(member="1x4", direction="vertical")),
        Layer(name="cladding", material_ref="standing-seam-snaplock", thickness=inch(0.5),
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
PLANT_INT_2X6_BRG_HUMID = Assembly(
    tag="PLANT_INT_2X6_BRG_HUMID",
    layers=(
        *_HUMID_LINER,
        Layer(name="stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6"),
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
    # The plant room's rim bands (2026-08-18). FS-SECOND and FS-ATTIC both run their joists
    # in x, so their ends bear on W-S-W4 and a parallel rim bay sits against W-S-S1 — two
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
    # RM-M-LIVING (a room decision, not FS-SECOND's) — the rest of that ceiling is screwed
    # direct. A full layered-ceiling assembly is deliberately deferred; this just bills the
    # channel (gypsum comes via FS-SECOND's `ceiling_below`).
    # (That gap is closed as of 2026-08-18: `construction_returns` is a priced section now.
    # This rule's own channel is still left unpriced in houses/catlin/prices.toml, on purpose
    # and with the reason written there — it is the same "is this a second count of material
    # another table already bought" question the sill plate raises.)
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
    CATLIN_ROOF,
    CATLIN_BASEMENT_12,
    CATLIN_BASEMENT_12_GARDEN,
    CATLIN_SLAB_FLOOR,
    CATLIN_DECK_EPS_INT,
    CATLIN_CONC_12_INT,
    CATLIN_CONC_8_INT,
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
    RAILING_DARK_METAL,
    GARAGE_ICF_6,
    GARAGE_WALL_2X6,
    GARAGE_SLAB_ON_GRADE,
    GARAGE_STEP_CONCRETE,
    GARAGE_ROOF,
    CATLIN_INT_2X6_BRG,
    INT_2X6_PLUMBING,
    INT_2X6_STAGGERED_PLUMBING,
    INT_2X4_PARTITION,
    INT_ESS_CLOSET_STEEL,
    SAUNA_2X4,
    SAUNA_LINER_ON_CONCRETE,
    SAUNA_LINER_ON_BASEMENT_12_GARDEN,
    PLANT_EXT_2X6_HUMID,
    PLANT_INT_2X6_BRG_HUMID,
    PLANT_INT_2X4_HUMID,
    CATLIN_MUDROOM_INT_2X6_EXPOSED,
]
