# haus: editable
# Catlin assemblies — the metal skins.
# Split out of plan/assemblies.py verbatim.
from typehaus import (
    Material,
    PublishedCladdingLoad,
    inch,
)


MATERIALS_METAL = [
    # --- the metal skins --------------------------------------------------------
    # The house is clad in metal in FIVE specifications. They are all the same white PVDF
    # steel to look at; what separates them is SEAM PROFILE and GAUGE, and both are labour
    # and material facts rather than architectural ones. Splitting them into separate tags
    # is what lets `prices.toml` bill each at its own rate — one tag carrying all 6,300 SF
    # at the dearest of the four would overstate the biggest line in the house by roughly
    # $5,000-18,000.
    #
    #   `standing-seam` (library/materials/) — 24 ga, MECHANICALLY FIELD-SEAMED.
    #       ROOF and nothing else. Every seam takes a separate powered-seamer pass:
    #       +$1.50-3.00/SF of labour and ~50% more crew-hours than a hand-closed profile,
    #       plus a seamer rental. It is on the main house roof on purpose — this is the roof
    #       that carries the PV array, sheds onto occupied ground, and must not be re-roofed
    #       in 25 years.
    #   `standing-seam-snaplock` — 24 ga, SNAP-LOCK. Concealed floating clips like the
    #       seamed roof, but the male and female legs engage under hand pressure, so there
    #       is no seaming pass. Roughly $2-4/SF cheaper installed than mechanical seam.
    #       It clad the house walls before the truss girts and is now taken by nothing but
    #       EXT_2X6_SWINBURNE, the revert wall — which is exactly what keeps the
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
    # house's walls as flat grey. The two PBR rows deliberately do NOT play that game — they
    # declare `finish="ribbed-panel"` and the renderers dispatch on the declaration, which
    # is what the substring fallback was always standing in for.
    # `standing-seam-nailstrip-26-green` — the same 26 ga. nail-strip panel as
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
    # `pbr-panel-26` — 26 ga, EXPOSED-FASTENER PBR. ** RETIRED 2026-09-14 and kept at 0 SF
    # as the documented revert ** — the house's east and west walls are `pbr-panel-24`
    # below, the same profile a gauge heavier in a named colour, because "26 ga PVDF" is
    # probably not a purchasable combination at Metal Sales (26 ga there is SMP). It took
    # EXT_2X6 and PLANT_EXT_2X6_HUMID over from `standing-seam-snaplock`. The fifth metal skin
    # and the only one that is not a concealed-fixing product: 36" net coverage with
    # 1-1/4" major ribs at 12" o.c., screwed through its face into the girts.
    #
    # It is here because the truss-girt work built the substrate for it — flat horizontal
    # 2x4 girts (32" o.c.) are what a PBR panel wants and are the reason this stops at the
    # house: GARAGE_WALL_2X6 has no furring at all (cladding
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
    # `pbr-panel-24` — the SAME PBR profile as `pbr-panel-26` above, one gauge heavier and
    # a named colour, on the house's EAST AND WEST walls (EXT_2X6 and PLANT_EXT_2X6_HUMID).
    # A new tag rather than an edit to the 26 ga row, because the tag reads the GAUGE: a row
    # spelled `pbr-panel-26` carrying 24 ga steel would lie to `prices.toml`, to
    # `emit/draw/palette.py` and to every reader. The 26 ga row stays above at 0 SF as the
    # documented revert, the way the nail-strip rows are kept.
    #
    # Three reasons for the gauge step, in order of weight:
    #   - At Metal Sales, PVDF IS a 24 ga product. The 24 ga colour guide is the PVDF
    #     palette; the 26 ga guides are MS Colorfast45, which is SMP (45-yr film / 30-yr
    #     chalk-fade, ~10-15 years of field data). The authored "26 ga PVDF" was probably
    #     not a purchasable combination from this supplier at all.
    #   - Hail. The Twin Cities are a hail corridor and insurers exclude cosmetic denting;
    #     24 ga dents and oil-cans visibly less. Gauge has ZERO effect on corrosion — that
    #     is the paint and the Galvalume — so this is an appearance-and-claims argument,
    #     not a durability one, and it is worth saying so.
    #   - Colour match. Linen White (81) on every face of the property, which also
    #     neutralises St Paul §63.110's advisory that street-facing sides use materials
    #     "similar to those used on principal facades".
    # Load is not the reason and never was: PBR at 24 ga is 318 psf outward at 2'-0" (PBR
    # CTR 1/2026) and at 26 ga 236 psf, both an order of magnitude over the -18.3 psf ASD
    # corner-zone demand. This wall stays PRESCRIPTIVE — `exposed_fastener=True` keeps it
    # out of `engineering/wall_panel.py`'s enumeration, which is the correct scope: a
    # face-fastened panel's wall capacity is published.
    # `standing-seam-linen-white` — the ROOF panel, and it exists for exactly one field the
    # library's generic `standing-seam` cannot carry for every house: `solar_absorptance`.
    #
    # ** IT IS A DIFFERENT PANEL FROM THE WALLS AND THE SAME COLOUR. ** The walls are
    # `pbr-panel-24`, an exposed-fastener PBR profile; this is a concealed-clip standing seam.
    # Both are 24 ga PVDF steel in Metal Sales Linen White (81), SR 0.73 / TE 0.86 / SRI 89,
    # which is where the absorptance comes from: alpha = 1 - SR = 0.27.
    #
    # ** WHY THE NUMBER MATTERS, AND WHY `color` COULD NOT STAND IN. ** A roof is
    # solar-dominated and nearly delta-T-independent: at the cooling peak hour this roof's
    # SOL-AIR temperature is 101 F against a 90 F design day, a 26 F CTD where the plain air
    # delta-T is 15 (notes/solar_gain_basis.md section 6). At alpha 0.90 — a black roof — it
    # would be 144 F and a 69 F CTD, five times the air delta-T. `color` is an sRGB
    # presentation triple and says nothing about the near-infrared, where most of the energy
    # is; only a published SR answers it.
    #
    # HOUSE-LOCAL rather than an edit to `library/materials/`: a colour is this house's
    # choice and the library's `standing-seam-snaplock` is the shared, reviewed catalog
    # entry (CONTRIBUTING section Promotion flow). Every other building-
    # science number is `standing-seam`'s verbatim — continuous sheet steel carries no R and
    # no vapour permeance whatever its colour — so nothing but the cooling load moves.
    Material(tag="standing-seam-linen-white",
             name="Standing-seam steel, 24 ga., PVDF Linen White (81)",
             r_per_inch=0.0, density=7800.0, vapor_permeance_perms=0.0, hatch="metal",
             color="#6b7076",
             skin_family="standing-seam",
             solar_absorptance=0.27,
             source="Metal Sales 24 ga. PVDF-coated steel standing seam, concealed-clip snap-lock profile, in PVDF Linen White (81) — the same colour as `pbr-panel-24` on the walls and `corrugated-panel-24` on the garage, on a different profile. SR 0.73 / TE 0.86 / SRI 89 from the Metal Sales PVDF colour guide, so solar_absorptance = 1 - 0.73 = 0.27. Caveat carried from the wall panel's own record: SRI is NIR-weighted, no visible LRV is published, and it is NOT a low-gloss colour."),
    # `corrugated-panel-24` (a library row since 2026-09-24, as are `pbr-panel-24/-26` and
    # the three seam profiles) — `corrugated-panel-26` one gauge heavier, ordered here in
    # Linen White, on GARAGE_WALL_2X6 and both ENTRY_SCREEN faces. Same gauge reasoning as
    # `pbr-panel-24` above, and the entry screen moves WITH the garage
    # because CLAUDE.md records that its west face must stay in the same plane and the same
    # reading as the garage panel.
    #
    # ** 34-2/3" wall coverage, not the library row's 32". ** The Metal Sales 7/8"
    # Corrugated WALL CTR (1/2024) reads "34 2/3\" panel coverage"; 32" is the ROOF figure,
    # one more corrugation of side lap. The library's prose and
    # `emit/draw/elevation_finish.py::_CORRUGATED_LAP_M` both carried 32", which drew a side
    # lap where no joint is on every garage elevation; the constant is fixed and the library
    # row's prose is a separate correction. The TAKEOFF still counts screws off
    # `takeoff/hardware_config.py`'s global PBR 12"/36" proxy — a known approximation,
    # unchanged by this work and unaffected by gauge.
    #
    # `areal_density_kg_m2` is the one number that actually moves with the gauge: 24 ga is
    # 0.0239" of steel = 4.7 kg/m2 flat, and the corrugation's developed length runs about
    # 10% over its coverage, so 5.2. The 7/8" layer `thickness` is the PROFILE DEPTH, not
    # the steel, which is why a dead load taken off it would read a sheet of solid steel.
    # `board-batten-24` — Metal Sales BBD75-1212, 24 ga CONCEALED-FASTENER board & batten
    # at 12" net coverage, on the NORTH AND SOUTH elevations only. The sixth metal skin. The
    # east and west walls are `pbr-panel-24` above, a different profile in the same colour
    # and gauge: this is a per-wall `layer_materials=` swap on twenty walls, not an
    # assembly change.
    #
    # ** BB75-1111 is the CLIP-fastened panel; BBD75-1212 is the DIRECT-fastened one, and
    # this row named the wrong one until 2026-09-14. ** The two guides' cover pages say so
    # outright — "Concealed Clip-Fastened BB75-1111" against "Concealed Direct-Fastened
    # BBD75-1010 / BBD75-1212" — and the difference is visible in the wall-base details:
    # BB75's (guide p.20) reads "PANEL CLIP (SEE PAGE 17), CLIP FASTENERS (B), 2 PER CLIP"
    # (clip P/N 4934600 G90 / 49346F01 stainless), BBD75's (p.22) reads "PANEL FASTENER (B),
    # AT NAIL STRIP". The engineering item's withdrawal model — ONE screw per panel per
    # girt — has always described the direct-fastened panel, so naming BBD75 makes the
    # existing calculation true rather than adding a new one to it.
    #
    # Structurally the two are the same product: both guides (10/2025) publish 43 psf
    # inward / 58 psf outward at 2'-0" fastener spacing, the same note 2, the same "Lumber
    # - 1x or thicker" support list, 24 ga only, 5'-20' lengths. What BBD75-1212 buys is
    # cheaper INSTALLATION — 12" coverage instead of 11" (~9% fewer panels, laps and screw
    # lines) and one nail-strip screw per girt instead of a clip plus two screws (~840
    # screws and no clips on the N+S faces, against ~2,000 screws and ~1,000 clips). What
    # it gives up is the Florida approval (FL47647.1, which is scoped "over Sheathing" and
    # reaches this wall for neither panel) and the clip's thermal-movement slip, which at
    # an 11.1 ft storey band is immaterial.
    #
    # 24 ga, not 26: at Metal Sales PVDF *is* a 24 ga product. The 24 ga colour guide is the
    # PVDF palette; the 26 ga guides are MS Colorfast45, which is SMP. "26 ga PVDF" is
    # probably not a purchasable combination from this supplier at all, which is why every
    # metal face on this house is now 24 ga (see `pbr-panel-24` above and
    # `corrugated-panel-24` below).
    #
    # ** PVDF Linen White (81), and the colour is a decision. ** 24 ga colour guide 9/2026:
    # SR 0.73 / TE 0.86 / SRI 89 — the highest SRI in the whole Metal Sales line (Snowdrift
    # White W81 is 78, the 26 ga SMP "White (30)" is 79). The point is bouncing daylight
    # into tree-shaded rear gardens. Two caveats worth keeping: SRI is NIR-weighted and
    # Metal Sales publishes no visible LRV (peer whites run ~74-75), and Linen White is a
    # standard no-upcharge colour but is NOT marked Low Gloss and "not all colours stocked
    # at all branches" — treat it as a made-to-order coil run and ask Rogers MN for lead
    # time. There is no matte white in this palette.
    #
    # 12" net coverage is the PRODUCT'S, not a choice. The row was authored at 20" against
    # no named panel; the survey in notes/board_batten_girt_span.md §7 found no
    # 24"-coverage batten panel on the market at all, and published coverages run 10", 11",
    # 12" and 16". At 12" against PBR's 36" this is 3.0x the panel count, which is why the
    # prices.toml labour band sits near the top of its researched range.
    #
    # ** The girts constrain the SUPPLIER, and that had to survive a substitution. **
    # Board & batten is not a purlin-bearing profile, and it appears in no evaluation
    # report. That is why the product is NAMED rather than assumed: Metal Sales BBD75-1212,
    # whose own install guide (2025-10-16, p.7) says the panel is "designed to be installed
    # over open framing and/or directly over a wood substrate" and whose p.12 Support
    # Materials list reads "Lumber - 1x or thicker" and "Steel Framing - 18 gauge or
    # thicker" — neither of which is a solid substrate. This wall's 1-1/2" KDAT girts at
    # 24" o.c. are on-label under that sentence, which is the whole reason the switch was
    # made away from an unnamed Western States panel that publishes no load data at all.
    #
    # ** And the question is closed by the CODE, not by a letter. ** IRC R703.1.2 asks for
    # a wind-load path by test or by analysis and says nothing about a solid substrate;
    # BBD75-1212 lists an ASTM E 330 Load Test on its own design page, which is R703.1.2's
    # first path named on the product; and the allowable table is indexed on FASTENER
    # SPACING from 2'-0" (the NARROWEST column, 43/58 psf) out to 6'-0" (22/13), so a table
    # built on fastener spacing across five spans is a spanning-between-supports table by
    # construction and this 24" girt sits at its strong end. The 07/2026 CTR carries a
    # summary badge that reads as sheathing-only; it is a copy artifact — the same sheet's
    # own icon row says `10" & 12" COVERAGE` while showing ONE panel at 11", because the
    # 12/2024 single-sheet CTR was split in two and the row copied verbatim onto both. No
    # Tech Services letter is needed.
    #
    # ** A MANUFACTURER READ SINCE 2026-09-22, AND `wall_panel/W-A-N1` LEFT THE REGISTER. **
    # `structural.cladding_wind` grades the zone-5 demand against the guide's own row in
    # BOTH directions: 18.27 psf ASD suction vs 58 outward (d/c 0.315) and 13.64 psf ASD
    # push vs 43 inward (d/c 0.317 — inward governs, by a hair). The fastener is the
    # guide's own named screw at its own spacing, a CONDITION of the read; the NDS 2018
    # section 12.2 withdrawal (0.182) and AISI S100 pull-through (0.118) the retired item
    # graded stay as the `structural.cladding_fastener` advisory. See
    # houses/catlin/notes/board_batten_girt_span.md §8.
    #
    # ** The row stays 58 even though a newer sheet publishes 75; a switch to 75 is a
    # re-author with a new source, not an edit to a number. ** The
    # Condensed Technical Reference 07/2026 re-publishes this panel at 42 psf inward /
    # 75 outward at 2'-0", off a LOWER section (Ixx 0.0156-0.0181 against the guide's
    # 0.0442). A lower section modulus with a higher allowable is not reconcilable in
    # either limit state — scaling 58 by the section ratio gives ~25-29 psf, not 75 — so
    # one of the two tables is wrong and 58 is the conservative half. Recorded, not
    # adopted; it is a question for the Rogers branch when quoting, not a gate.
    #
    # ** The screw is a #10-12 x 1-1/2" (owner, 2026-09-22): the guide's named 1", longer. **
    # The published read accepts it — its length guard is increase-only, because the row
    # excludes fasteners by footnote. Metal Sales stocks only the 1" (8243100, plated); the
    # 1-1/2" is bought with the 316 SS / A153-D coating the KDAT needs, as the 1" had to be.
    # History: this row carried a #10-12 x 2" for three days on one argument: Metal Sales' detail
    # asks that "fasteners should extend 1/2" or more past the inside face of the support",
    # and in a 1-1/2" girt nothing shorter than 2" can. That argument does not hold, for
    # three reasons, and the note's §6 now works all three:
    #   - The GIRT is the support, and the protrusion buys nothing. Behind it is the 1/2"
    #     vent gap and then the ccSPF. A tip emerging into that plane adds no withdrawal,
    #     no bearing and no redundancy.
    #   - The rule cannot be a wood-engagement criterion, because on the guide's OWN
    #     thinnest listed supports it yields almost none: the same 1" screw gives 0.034" of
    #     thread in 7/16" OSB and 0.096" in 1/2" plywood, against 0.596" in this 1-1/2"
    #     girt — ~18x the manufacturer's thinnest listed case. It is a sheathing-era "make
    #     sure you went all the way through" proxy, not a design criterion.
    #   - And it is not the governing document. The load table footnotes fasteners and
    #     support material out BY NAME, which is exactly why `wall_panel` is an ENGINEERED
    #     record; IRC R703.1.2's design-analysis path is the one this wall is on, and NDS
    #     2018 §12.2 is the analysis. Every candidate length passes it, the 1" included.
    # At 1-1/2" the thread engagement is 1.096" and d/c is 0.182 (0.334 at the stocked 1")
    # on an allowable that already carries NDS's own 5:1; the tip stays inside the girt.
    # ** 2" is affirmatively REJECTED: ** its tip stands 0.476" into a 0.500" vent gap,
    # 0.024" off the ccSPF face, so a thin girt or one overdriven screw puts ~840 tips in
    # the foam. Nothing longer than 1-1/2" should ever be specified here.
    # It must still be a wood-point (Type 17) screw — a self-drilling point reams its own
    # thread out of a 1-1/2" nailer — and the 316 SS / A153-D coating call is unchanged
    # (KDAT contact; see prices.toml).
    #
    # ** `panel_fastener_head_dia_in=0.40` is not decoration either. ** IRC R703.1.2 names
    # three failure modes a design analysis must reach — "bending rupture of siding,
    # fastener withdrawal and fastener head pull-through" — and this field is the third
    # one's only input the model does not already hold. A pancake head is the smallest head
    # sold, which is why the mode is graded rather than assumed away; it passes at ~0.12.
    #
    # ** 12" coverage, not 20" and not 11". ** That is the product's real net coverage, and
    # it is not cosmetic — panel count and the labour band both move with it (see the
    # `board-batten-24` row in prices.toml), and fastener tributary area moves with it in
    # the withdrawal calculation above, which is how the governing limit state came to
    # FLIP twice: at 11" coverage with the rejected 2" screw withdrawal was 0.12 against
    # bending's 0.315; at 12" with the 1" screw it was 0.334 and governed; with the 1-1/2"
    # it is 0.182 and the panel's own row (0.317 inward) governs again.
    #
    # ** PVDF Linen White and not the wood-grain print: ** "white wood" is CERAM-A-STAR
    # SMP, a different coating system and warranty from the PVDF on the rest of the
    # envelope, costs about as much again as the switch itself, and is not quoted below a
    # $3,000 job minimum.
    #
    # ** The tag stays `board-batten-24`. ** It reads as the GAUGE, which is unchanged at
    # 24 ga; renaming it would touch twenty layer_materials overrides, the prices.toml key
    # and three unrelated tests for nothing. (The E/W and garage tags DID have to move —
    # `pbr-panel-26` -> `pbr-panel-24`, `corrugated-panel-26` -> `corrugated-panel-24` —
    # because those read the gauge that changed, and a tag that reads 26 ga would lie.)
    #
    # ** `exposed_fastener` is deliberately ABSENT (defaults False). ** A concealed-leg
    # panel's pancake screws are inside the $/SF rate, and leaving the flag on would bill
    # them a second time as a counted part. This is what drops the house's face-screw count
    # to the garage's corrugated share plus the E/W walls'.
    #
    # ** `skin_family="standing-seam"` is load-bearing for the ROOF EDGE, exactly as it is
    # on `pbr-panel-26`. ** `resolve.roof_edge_geometry.continuous_skin_cladding` returns
    # True only when every wall under a roof reads as ONE skin, and in the mixed case that
    # is precisely what this field buys: two materials both declaring it collapse to
    # {"standing-seam"} and the flush zero-overhang edge survives on all four edges. Omit it
    # and the edge silently reverts to fascia-and-drip-edge, including on the PBR walls.
    #
    # ** Thickness stays 1-1/4", and that is not a rounding. ** The cladding face is
    # hand-transcribed into house constants that feed the north/south faces this material
    # lands on: `params/roof_trim.py` `_WALL_OUTBOARD_IN`, `params/breezeway.py`
    # `HOUSE_CLADDING_Y_FT`, `params/sunken_garden.py` `gap_to_house_in`, and the exterior
    # devices in `plan/electrical.py`. The roof footprint re-derives from the bearing walls'
    # outermost layer polygons and those constants do not, so any thickness change makes
    # derived geometry and authored constants silently disagree at the rake ends. The
    # BBD75-1212 rib is 3/4" and the panel plus batten sits inside 1-1/4".
    Material(tag="board-batten-24", name="Metal Sales BBD75-1212 board & batten panel, 12\" coverage, 24 ga., PVDF Linen White (81)",
             r_per_inch=0.0, density=7800.0, vapor_permeance_perms=0.0, hatch="metal",
             color="#6b7076", finish="board-and-batten",
             skin_family="standing-seam",
             published_cladding=PublishedCladdingLoad(
                 source="Metal Sales BBD75 Install Guide 10/2025 p.13",
                 table="Allowable uniform loads, 24 ga, 12\" coverage, 2'-0\" fastener spacing",
                 member="BBD75-1212",
                 allowable_outward_psf=58.0,
                 allowable_inward_psf=43.0,
                 fastener_spacing=inch(24),
                 condition="AISI 2016, three or more equal spans, L/180, no 1/3 stress increase, ASTM E330; the spacing is measured along the panel, so on this vertically-run panel it is the girt course",
                 gauge=24,
                 coverage=inch(12),
                 panel_fastener="#10-12 x 1\" Pancake Head Wood Screw",
                 support_material="Lumber - 1x or thicker",
                 min_support_thickness=inch(0.75),
                 deflection_limit="L/180",
                 stress_increase=False,
                 span_condition="3 or more equal spans",
                 excludes="note 2: the allowable \"does not address web crippling, fasteners, support material or load testing\"",
                 demand_psf=18.27,
                 wind_speed_mph=115.0,
                 exposure="B"),
             open_framing_source="Metal Sales BBD75 Board & Batten (Concealed Direct-Fastened) install guide, 2025-10-16, p.7: the panel is \"designed to be installed over open framing and/or directly over a wood substrate\", and p.12's Support Materials list reads \"Lumber - 1x or thicker\" and \"Steel Framing - 18 gauge or thicker\" (neither is a solid substrate). The Spec Data Sheet says the same in its own words: \"Designed for application over solid sheathing or open framing\", typical assembly \"Wood framing with moisture barrier\"",
             panel_fastener="#10-12 x 1-1/2\" pancake head wood screw, Type 17 point, 316 stainless or ASTM A153 Class D HDG",
             panel_fastener_diameter_in=0.190,
             panel_fastener_length_in=1.5,
             panel_fastener_head_dia_in=0.40,
             fastener_coverage_in=12.0,
             source="Metal Sales BBD75-1212 (product nos. 2520741 ACG / 25207XX PVDF): 24 ga. PVDF-coated steel board & batten wall panel, 12\" net coverage, 3/4\" rib, concealed DIRECT-fastened at the nail strip over open framing; allowable 58 psf outward / 43 psf inward at 2'-0\" fastener spacing (AISI 2016, 3+ equal spans, L/180, no 1/3 stress increase, and by its own note 2 it does not address web crippling, fasteners, support material); PVDF Linen White (81), SR 0.73 / TE 0.86 / SRI 89 per ASTM C1549 / C1371 / E1980, CRRC-listed steep and low slope, 45-yr film / 35-yr chalk-fade warranty; same vapour-impermeable sheet steel as the five skins above"),
    # Loose-fill for the garage attic (GARAGE_ROOF). A separate tag from `fiberglass`
    # because blown wool is installed at roughly half batt density and rates R-2.5/in
    # rather than R-3.7 — reusing the batt tag would overstate the ceiling by ~48%.
    # House-local rather than library: only this roof uses it, so it stays here until a
    # second house wants it (CONTRIBUTING §Promotion flow).
    # The roof cavity batt (ROOF). A separate tag from `fiberglass` because the
    # library's 3.7/in is a HIGH-DENSITY value — right for an R-21 batt squeezed into 5.5",
    # wrong for a standard R-19 that reaches R-19 only by lofting to 6.25". Reusing the
    # library tag at 6.25" would read R-23 and overstate this roof by R-4. House-local until
    # a second house wants it (CONTRIBUTING §Promotion flow).
    # The roof cavity batt, in front of the 5" ccSPF flash. An R-30C
    # CATHEDRAL batt — 8 1/4" nominal, the unfaced high-density product made for a rafter bay
    # — deliberately COMPRESSED into the 6 7/8" the foam leaves.
    #
    # **The R/inch here is the compressed value and not the label's.** Compressing glass wool
    # raises its density and lowers its R per inch while raising the R per *bay*: R-30 at
    # 8.25" is 3.64/in, and the same batt squeezed to 6.875" delivers about R-26, i.e.
    # 3.78/in. Reusing the label's number over the shorter depth would read R-25 and
    # understate it; reusing the `fiberglass` library tag's 3.7/in — a high-density value for
    # an R-21 in 5.5" — would read R-25.4 for a different reason. Neither is this product at
    # this depth, which is why the tag is its own. House-local until a second house wants it
    # (CONTRIBUTING §Promotion flow).
    #
    # Not air-impermeable, at any density: it is the *air-permeable* half of R806.5 item 5.1.3,
    # and the ccSPF outboard of it is the half the table governs.
    # The roof's field underlayment (ROOF), over the nailbase top deck.
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
    # The plant room's three materials — `pvc-panel`, `humid-room-membrane` and
    # `vinyl-sheet` — were authored here first and promoted to `library/materials/`
    # (CONTRIBUTING §Promotion flow): none of them carries a project
    # coordinate, an owner choice or a house-specific dimension, all three are ordinary
    # catalog products with stable tags, and `takeoff/finishes.py::_WASTE` (engine code)
    # names `vinyl-sheet` — an engine table may not depend on a material only one house
    # defines. They arrive through `ALL_MATERIALS` above. See notes/plant_room.md for
    # why the panel deliberately carries no permeance and the membrane carries a
    # specification value.
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
    # RETIRED as the veneer's field when BASEMENT_BRICK_VENEER became the
    # Ishtar scheme below, and kept alive here on purpose: the colour was liked, it just did
    # not sit with a house of white standing seam and #1c1f24 trim. Nothing references it, so
    # restoring the wall to one flat forest-green field is a one-word `material_ref` swap in
    # BASEMENT_BRICK_VENEER — the Material, its MasonryStyle and its _FINISH_BASE entry are
    # all still there. Do not delete it to tidy up.
    Material(tag="glazed-green-brick", name="Glazed forest-green face brick",
             r_per_inch=0.20, density=1920.0, perm_rating=1.0, hatch="concrete",
             color="#1b4332", finish="glazed-green-brick",
             source="basement south veneer over the sunken garden until 2026-08-20 — glazed brick, 1\" airgap off the existing concrete wall; kept in the catalog as the revert target for the Ishtar scheme"),
]
