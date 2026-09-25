# haus: editable
# Catlin assemblies — the house, garage and canopy roofs.
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
    PAINT_FINISH,
)


# --- hot roof (unvented; flash-and-batt in the bay — → 30 §WP3.11) ------------
#
# Four layers: the bay, one deck, one membrane, the panel. It replaced a nine-layer roof
# (an R-19 batt loose in an 11 7/8" bay, 1/2" taped ZIP, a 0.04-perm self-adhered deck
# vapour barrier, TWO staggered 3" polyiso courses, a 5/8" OSB nailbase screwed through the
# foam on 539 x 10" SDWH screws, a permeable synthetic underlayment and a 1/4" nylon vent
# mat under the metal — R-55.1 at 19.9" deep, against a code minimum of R-49).
#
# The move is flash-and-batt — 5" of closed-cell foam sprayed against the deck underside
# with an R-30C batt compressed in front of it — and the three things that make it work are
# each recorded where they are decided, not here:
#
#   1. **It is legal with zero above-deck foam.** IRC/MSRC R806.5 item 5.1.3: air-impermeable
#      insulation in direct contact with the sheathing underside at the Table R806.5 minimum
#      (R-25 in zone 6, R-30 in zone 7), with the air-permeable insulation directly under it.
#      5" of ccSPF is R-32.5 and clears BOTH rows, so the zone reading cannot go wrong.
#      Item 2's other condition is already met and is why the lining below is paint and
#      nothing else: NO INTERIOR CLASS I VAPOUR RETARDER, ever, on this ceiling.
#      `checks/code/unvented_roof.py` grades all of it.
#   2. **The condensation gate had to change, not be dodged.** No unvented stack under a
#      0-perm metal panel can pass a steady-state Glaser walk at any foam thickness — with
#      no outward flux the method equilibrates every plane to interior vapour pressure by
#      construction. The old stack bought its margin by leaving 5.6" of the bay deliberately
#      UNFILLED as a drying path; this one fills the bay, and the honest answer is that the
#      criterion changed: R806.5 item 5.1.3 makes the foam's own outer face the condensing
#      surface and holds it warm, and outward drying is not required.
#      `checks/building_science/condensation.py::_r806_5_deferral` says so in the report.
#   3. **The air barrier moved from tape to foam.** The taped ZIP was the air/water control
#      plane; the ccSPF is now the air and vapour plane (bonded, seamless, ~0.32 perm at 5"
#      = Class II) and the adhered membrane is the water plane. That is a more reliable
#      pair than a taped panel, and it is what R806.5 item 5.1.3 contemplates.
#
# **The vent mat and the permeable underlayment went together, because they were one
# decision.** Above the underlayment sits an impermeable metal panel: the only thing a
# 20-perm underlayment can dry into is the vented gap the mat made. Delete the mat and the
# permeable sheet is drying into a sealed panel underside — it buys nothing while still
# being a mechanically-fastened, non-self-sealing water layer under ~1,160 clip screws. So
# it is mat + permeable sheet, or adhered membrane + nothing. The second wins on labour, on
# oil canning, and on water control, and the membrane's butyl self-seals around every one of
# those screws — which is the actual water risk on a roof with no field penetrations
# (the 48 PV mounts are non-penetrating S-5! seam clamps).
#
# **5/8" CDX plywood, not 1/2" ZIP and not a grooved panel.** Smooth (the best bed an
# adhered membrane and an oil-canning-prone pan can have), span-rated 40/20 so 24" o.c. is
# well inside it, holds clip screws uniformly, and dries several times faster than OSB while
# recovering strength after wetting. **It oversails the last joist at each eave, spanning the
# wall girts** — which is why the deck, the membrane and the panel bill on the roof's sloped
# `surface_area_m2` (1,547.9 SF) while the bay fills bill on `roof_ceiling_area_m2`
# (1,449.0 SF); those are two different planes and `takeoff/envelope.py` keeps them apart.
# That cantilever is not graded by anything in the engine and belongs in the PE scope.
#
# **24" o.c. forces the heavier joist, and that is the deal.** At 16" a TJI 110 carries the
# 17'-9 3/4" HORIZONTAL run at Ps = 35 psf (Pg 50, Ramsey); at 24" it does not, and the 230
# is the first series that does. ** THE ALLOWABLE IS 18'-4", NOT THE 19'-3" THIS COMMENT USED
# TO CARRY: ** that figure was an interpolation between two published rows to 35 psf, which
# is a move `checks/structural/snow.py` refuses for its own table and which must not be made
# for a manufacturer's either. The honest read of TJ-4000's published row is 18'-4" — the
# margin is 6-1/4", not 15". Net of the upcharge the framing still comes down, and the better
# half is thermal: the framing factor falls from 0.07 to 0.05 at no cost.
#
# `structural.rafter_span` now grades this roof PRESCRIPTIVELY against that published row,
# authored as `Roof.published_span` on RF-HOUSE (2026-09-11; it was UNKNOWN/engineered at
# both spacings before). What the engine still will NOT tell you: no sheathing-span or
# gypsum-ceiling rule reads the spacing at all — fine here, 5/8" board is rated for a 24"
# o.c. ceiling where 1/2" is not, and neither is verified. And the printed table assumes
# BEARING at the high end where these joists HANG off the ridge on LSSR hangers: confirm in
# ForteWEB, and see notes/roof_rafter_span_read.md §3, which is the open item.
#
# The metal itself is unchanged: 24 ga mechanically field-seamed, hidden floating clips.
ROOF = Assembly(
    tag="ROOF",
    layers=(
        Layer(name="rafter", material_ref="spf", thickness=inch(11.875),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="11.875 TJI 230", spacing=inch(24)),
              # ~R-53 whole-assembly on a 0.05 framing factor, and every point of it now
              # lives INSIDE the joist depth. The bay is authored interior -> exterior, the
              # way the layer list is: the batt first, the foam that touches the deck last.
              # `Layer.cavity_fills` is what reads it — the two are in SERIES with each other
              # and in PARALLEL with the joist, which runs past both.
              #
              # The batt is an R-30C cathedral batt (8 1/4" nominal) COMPRESSED into the
              # 6 7/8" the foam leaves, which is why it is authored at 6.875" against a
              # material whose R/inch is the compressed value — it arrives oversized on
              # purpose, friction-fits the flange pockets and is held tight by the drywall,
              # so there is no sag void over a 20' run of 6:12 slope.
              cavity=(
                  CavityFill(material_ref="fiberglass-r30c", thickness=inch(6.875),
                             framing_factor=0.05),
                  CavityFill(material_ref="closed-cell-spray-foam", thickness=inch(5.0),
                             framing_factor=0.05,
                             control={ControlLayer.AIR, ControlLayer.VAPOR,
                                      ControlLayer.THERMAL}),
              )),
        # 5/8" CDX. The structural deck, the clip substrate and the oil-canning bed, in one
        # panel — and no longer any part of the air barrier: that moved to the foam under it.
        Layer(name="sheathing", material_ref="struct-1-plywood", thickness=inch(0.625),
              function=LayerFunction.SHEATHING),
        # High-temp self-adhered butyl over the WHOLE deck, not an eave band. This is also
        # the strongest form of the FORTIFIED sealed-roof-deck requirement, and it retires
        # the open "screwed nailbase vs RSRS-01" item in notes/fortified_roof_cert.md §4.2.2
        # by deleting the nailbase that raised it.
        Layer(name="membrane", material_ref="roof-adhered-butyl-ht", thickness=inch(0.04),
              function=LayerFunction.MEMBRANE,
              control={ControlLayer.AIR, ControlLayer.WATER}),
        # `standing-seam-linen-white`, not the library's generic `standing-seam`: identical
        # in every building-science number, and it carries the published SR this roof's
        # SOL-AIR cooling term reads (notes/solar_gain_basis.md section 6).
        Layer(name="roofing", material_ref="standing-seam-linen-white", thickness=inch(0.5),
              function=LayerFunction.CLADDING),
    ),
    default_lining=(
        PAINT_FINISH,
        Layer(name="gwb-ceil", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
    ),
    source="catlin-house ifcplot/assemblies.py HOUSE_ROOF (hot roof); the screwed nailbase over two 3\" polyiso courses (2026-08-20) deleted 2026-08-31 for 5\" ccSPF flash-and-batt in the bay under an adhered butyl membrane, IRC R806.5 item 5.1.3",
)

# The garage service step-down, SL-G-STEP-1..4, is a real `Stair` (ST-G-SERVICE in
# plan/storeys/garage.py) in pressure-treated KDAT. SL-G-STEP-0 survives as the 3'-0"
# landing at the threshold, pours with the slab, and names no assembly of its own.

GARAGE_ROOF = Assembly(
    tag="GARAGE_ROOF",
    layers=(
        # Raised-heel trusses (2x4 chords + webs) with a 9.25" energy heel so full
        # insulation depth carries over the top plate; the truss carries the ridge, so no
        # ridge beam is required. `haus` frames the chords/webs/heel as first-class members.
        #
        # The fill is loose-fill fiberglass blown onto the ceiling plane, 14.5" settled —
        # R-38 nominal (owner). The 9.25" energy heel is the FLOOR of that
        # depth, not the ceiling: the heel is what guarantees full depth survives over the
        # top plate instead of pinching to nothing at the eave, and the blow runs deeper
        # than the heel across the field, tapering into it at the last bay. That is why
        # 14.5" is thicker than this layer's own 11.875" — the fill lies on the bottom
        # chord in a vented attic void that is far deeper than 14.5" anywhere but the very
        # eave, so it is not bounded by the structural depth the way a stud-bay batt is.
        # Nothing moves geometrically: a CavityFill adds no thickness to the stack
        # (→ CavityFill), it is a parallel thermal path with the chords, not a series one.
        # The attic above it is the vent void the PVC soffit feeds (ROOFS in
        # storeys/garage.py). framing_factor is the 2x4 bottom chord at this assembly's
        # authored 24" o.c. (1.5/24); the blow buries the chords, so this is the
        # conservative reading of the bridge.
        #
        # ** 24" o.c., AND ff MUST STAY 0.0625 WITH IT. ** A 24'-span 2x4 fink is an
        # essentially unchanged truss at either spacing, so this buys ~33% fewer trusses of
        # the same design. The two numbers have to move together: 0.0625 is 1.5/24, and
        # 0.09 (the 16" o.c. figure) would silently under-credit the R-38 blow by crediting
        # bottom chord over 9% of a ceiling that is only 6.25% chord.
        Layer(name="truss", material_ref="spf", thickness=inch(11.875),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x4", roof_frame="truss",
                                  spacing=inch(24),
                                  heel_height=inch(9.25),
                                  chord_member="2x4", web_member="2x4"),
              cavity=CavityFill(material_ref="blown-fiberglass", thickness=inch(14.5),
                                framing_factor=0.0625)),
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
    # PRIMER, NOT PAINT, and that is a decision rather than an omission (owner): the
    # ceiling is taped and primed, not finished. GARAGE_WALL_2X6 keeps its paint, so the
    # garage is board-and-paint on the walls and board-and-primer overhead. The primer is
    # authored so the board is not bare: bare gypsum facing a room is billed paint
    # (takeoff/derived_paint.py).
    default_lining=(
        Layer(name="primer", material_ref="gwb-primer", thickness=inch(0.01),
              function=LayerFunction.FINISH),
        Layer(name="gwb-ceil", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),
    ),
    source="catlin-house detached garage roof (vented 4:12 truss attic); gypsum ceiling + 9.25\" blown fiberglass added 2026-08-20",
)

# The north entry canopy, over the open passage between the house and the garage.
#
# ** STRUCTURALLY IDENTICAL TO GARAGE_ROOF, AND THAT IS THE POINT. ** Same 2x4 fink at
# 24" o.c., same 9.25" heel, same deck/membrane/roofing. RF-BW-CANOPY bears at +7'-4" on
# BM-BW-RW/RE, which are southward extensions of the garage's own two truss bearing lines,
# so the two roof planes are ONE plane: change this layer's depth, spacing or heel and the
# canopy steps off the garage roof at the joint. The sheathing runs continuous across the
# garage south wall line even though the `Roof` elements are separate — that continuity is
# the canopy's whole lateral system (AN-BW-ROOF says so, and so must the drawings).
#
# ** WHAT IS DELETED IS THE WHOLE REASON IT IS A SEPARATE ASSEMBLY. ** No `cavity` and no
# `default_lining`. `roof_ceiling_area_m2` bills off the BEARING footprint, so extending
# RF-GARAGE over the passage instead would have ordered R-38 blown fiberglass and a 5/8"
# gypsum ceiling over 144 sf of open outdoor bay — about $350-700 of material, and an
# insulated ceiling with no conditioned space under it is building-science nonsense besides.
# An open canopy has no thermal boundary to hold, so it carries none.
CANOPY_ROOF = Assembly(
    tag="CANOPY_ROOF",
    layers=(
        Layer(name="truss", material_ref="spf", thickness=inch(11.875),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member="2x4", roof_frame="truss",
                                  spacing=inch(24),
                                  heel_height=inch(9.25),
                                  chord_member="2x4", web_member="2x4")),
        Layer(name="deck", material_ref="struct-1-plywood", thickness=inch(0.75),
              function=LayerFunction.SHEATHING),
        Layer(name="membrane", material_ref="air-barrier", thickness=inch(0.02),
              function=LayerFunction.MEMBRANE,
              control={ControlLayer.AIR, ControlLayer.WATER}),
        Layer(name="roofing", material_ref="standing-seam-nailstrip", thickness=inch(0.5),
              function=LayerFunction.CLADDING),
    ),
    source="north entry canopy over the open passage; GARAGE_ROOF's structure with no insulation and no ceiling (2026-09-10)",
)
