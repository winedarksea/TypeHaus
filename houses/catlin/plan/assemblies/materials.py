# haus: editable
# Catlin assemblies — the house's materials (the list the assembly editor adds to).
# Split out of plan/assemblies.py verbatim.
from typehaus import (
    Material,
)
from library import (
    ALL_MATERIALS,
)
from .materials_ishtar import MATERIALS_ISHTAR
from .materials_metal import MATERIALS_METAL
from .materials_flooring import MATERIALS_FLOORING
from .materials_entry_screen import MATERIALS_ENTRY_SCREEN
from .materials_titanium import MATERIALS_TITANIUM
from .materials_hardwood import MATERIALS_HARDWOOD
from .materials_study_booth import MATERIALS_STUDY_BOOTH


MATERIALS = [
    # Exterior darks are authored at the maker's own chip value, never pre-darkened
    # (2026-10-30). Graphite Gray is a MID grey on AZEK's chip, not the charcoal #41464a it
    # carried; the near Captivate options are Dark Shale #5c5b5e and Midnight Black #20201f.
    Material(tag="captivate-graphite-sheet", name="AZEK Captivate Graphite Gray 3/4 inch sheet trim",
             color="#848581", product_ref="PROD-AZEK-CAPTIVATE-GRAPHITE-SHEET",
             source="AZEK 2026 product guide AS03448096, 3/4 x 48 x 96 smooth sheet; Captivate Graphite Gray factory finish. Field-rip returns/casing; two sheets for both doors. Colour sampled from AZEK's captivate_swatch_graphitegray.png (2025 swatch set, read 2026-10-30); AZEK says screen colour is approximate, so a physical sample governs."),
    # Window frames, by product (`WindowType.frame_material_ref`).
    Material(tag="drutex-alucover-ral9005", name="Drutex Alucover aluminium cap, RAL 9005 jet black matt",
             hatch="metal", color="#131516",
             source="Drutex IGLO Energy Alucover exterior cap, RAL 9005 matt powder coat (plan/opening_products.py). Colour is RAL's own sRGB for RAL 9005 (ral-farben.de colour list, read 2026-10-30). The grey route on the same cap is RAL 7016 anthracite #3b4044 or RAL 7021 black grey #323537."),
    Material(tag="andersen-400-black", name="Andersen 400 Series Black exterior (Perma-Shield vinyl)",
             color="#323433",
             source="Andersen 400 casement, Black exterior. Colour sampled from Andersen's black-exterior swatch (andersenwindows.com, read 2026-10-30). The 400 Series offers no grey: White, Sandtone, Canvas, Terratone, Forest Green, Dark Bronze and Black only (Andersen help centre), so the nine escape units stay black whichever way the house goes."),
    # The overhead door's leaf (`DT-EXT-OVERHEAD192.leaf_material_ref`).
    Material(tag="clopay-charcoal", name="Clopay Classic Steel factory paint, Charcoal",
             hatch="metal", color="#535353",
             source="Clopay Classic Steel GDU293, Charcoal. Colour sampled from Clopay's paint-color-charcoal chip (clopaydoor.com, read 2026-10-30). Clopay offers Black in this line only at R-6.5 (GDU266)."),
    Material(tag="pvc-opening-flashing", name="SureSill PVC opening flashing",
             color="#eeeeee", source="SureSill stock HeadFlash/sloped sill pan; catalog coordination envelopes."),
    Material(tag="silicone-transition", name="Proglaze ETA standard silicone transition",
             color="#bbbbbb", source="Tremco ETA System 1 standard 6 inch extrusion and molded corners; project application unconfirmed."),
    Material(tag="composite-door-frame", name="Therma-Tru composite exterior frame and trim",
             color="#41464a", source="2026 Comp 6.4/6.46; composite profiles, finish per Therma-Tru. No exposed wood."),
    Material(tag="impermeable-door-flashing", name="Impermeable door pan/apron membrane",
             color="#444444", source="opening_flashing_spec.md hybrid; exact PVC-pan bond remains unconfirmed."),
    Material(tag="door-paint-black", name="Black exterior door field paint", coating=True,
             color="#181818", finish="paint", source="Site-applied coating approved for fiberglass/composite frame; factory black quote alternate."),
    Material(tag="door-paint-white", name="White interior door field paint", coating=True,
             color="#f4f3ee", finish="paint", source="Site-applied interior face finish; seal all leaf edges per manufacturer."),
    *ALL_MATERIALS,
    Material(tag="pax-frame-white", name="White PAX frame and shelf panels",
             color="#f0f0ed",
             source="Owner selection 2026-10-02: BED1-3 PAX frames are white."),
    # `polyiso-foil-thermax` (the sauna liner's board) is a library row since 2026-09-24.
    # --- THE 2026-09-06 INTERIOR SELECTIONS PASS -----------------------------------------
    #
    # ** THE FIRST MATERIALS IN THIS REPO TO CARRY A ``product_ref``. ** The field has existed
    # on ``Material`` since it was added for every other catalog and no material has used it,
    # because a stud is a stud. A slab and a tile are different: they are BOUGHT, by model,
    # finish and lot, and the whole point of ``plan/products_interior.py`` is that "what did we
    # actually buy" should be readable by the estimate rather than parsed out of prose.
    # ``takeoff/product_labels.py`` already joins ``envelope_layers`` and ``floor_finishes``
    # to product labels, so these reach the bill with no engine change.

    # ** COUNTERTOPS DID NOT EXIST IN THIS MODEL AT ALL. ** Until now the only statement about
    # them anywhere in the repo was one docstring line in library/placeables/casework.py:
    # "continuous 1-inch white countertop" — no element, no material, no price row, i.e.
    # unpriced scope. This tag is the material half of the fix; the price row is keyed to it
    # in prices.toml and driven off casework lineal feet, because a countertop is still not a
    # modelled ELEMENT and this pass deliberately does not invent one (see plans/TODO.md).
    #
    # 3 cm, no debate: 2 cm's saving evaporates into a plywood subtop plus a laminated edge,
    # and it cannot do a good mitre. Eased edge is included in the fabrication; a 2-3" mitred
    # apron on the exposed run is the most visible upgrade available in a minimalist kitchen,
    # and a WATERFALL is $700-1,200 to kill the knee space at one end of a three-stool run.
    #
    # ** SILICA: CONVENTIONAL QUARTZ, CHOSEN ON PRICE (owner, 2026-10-22). ** The 2026-09-06
    # pick was Silestone HybriQ (<=40% crystalline silica) because the low-silica slab was
    # also the cheaper one. MSI Q Quartz is a conventional formulation, typically ~90% silica,
    # and no MSI silica figure was found publicly: the SDS is the gate. What protects the
    # fabricator is vetting the SHOP, not the showroom — wet cutting on every operation
    # including hand edge-work, respirators on faces, and OSHA silica exposure monitoring on
    # file. That is the strongest argument against the big-box route, which subs the cut to an
    # undisclosed shop you can neither inspect nor hold to a cantilevered overhang.
    Material(tag="quartz-counter", name="Engineered quartz countertop, 3 cm",
             density=2400.0, hatch="masonry", color="#f2efe9", finish="polished",
             product_ref="PROD-MSI-Q-QUARTZ-SPECKLED-WHITE", engineered_stone=True,
             # MSI quartz slabs run ~120 x 55 in. (slabwise.com MSI guide, read 2026-10-30;
             # MSI's own sheet publishes none for Frost White). Confirm the lot at order.
             slab_size_in=(120.0, 55.0),
             source="MSI Q Quartz Frost White (pencilled 2026-10-22; confirm at order), speckled white, Group 1, 3 cm, standard polished, standard eased edge (owner selection 2026-10-22; replaces Silestone Et Calacatta Gold of 2026-09-06). Kitchen perimeter and sink run, the 48\" and 51\" vanity tops, and the peninsula's one-piece top, its 15\" seating overhang on hidden steel bars. ** NEVER CLEAN IT WITH ANYTHING HIGH-pH: ** bleach, ammonia, glass cleaner, degreasers, scouring powder and melamine sponges are the #1 cause of light quartz yellowing across every brand — not UV. #2 is heat scorch, which is irreversible; induction helps (no flame spill, no hot grate) but a 400 F pan is still a 400 F pan. Put that in the owner's manual."),
    # RM-M-BED desk top (CT-M-BED-DESK), over two SEKTION drawer bases and the knee ledger.
    Material(tag="walnut-counter", name='Black walnut top, 1", 5/4 S4S',
             r_per_inch=1.0, density=610.0, hatch="lumber", color="#80634f",
             finish="clear-satin-hardwax-oil", species="walnut", nominal_quarters=5,
             milling_profile="S4S", requires_custom_milling=True, max_board_width_in=8.0,
             source="One 61 1/2\" x 24 7/8\" x 1\" desk top, an edge-glued panel of bought 5/4 walnut, oversailing 7/8\" past the drawer fronts. Finish all six faces; fix on figure-8s to the cabinets and through slots to the ledger."),
    # The east wall's living-room slab (CT-M-LIV-E-N; one since 2026-10-20), ash to match the
    # dining table's ash-6q top. Priced in [countertops], cut-listed by `haus millwork`.
    # Same logs as the table, so the same ~11" widest board: the 25" slab is three boards.
    Material(tag="ash-counter-6q", name='White ash counter slab, 1 1/4", 6/4 S4S',
             r_per_inch=1.0, density=670.0, hatch="lumber", color="#d9cbb0",
             finish="oak-board",  # the 3D recipe; the coat is waterborne urethane
             species="ash", nominal_quarters=6, milling_profile="eased",
             requires_custom_milling=True, max_board_width_in=11.0,
             source="Two slabs on the living-room SEKTION banks, 1 1/4\" finished off 6/4 (sawn full, ~1 5/8\" green), 16 1/2\" deep, straight eased front edge. Each is an edge-glued panel of two ~8 1/4\" boards (Type II PVA), the glue line straight on the front edge; the 160 5/8\" slab needs a 14'+ ash log. Back edge scribed to the gwb, where the ash stools meet it in one plane. Fix on slotted brackets; waterborne urethane on all six faces, matching the stools: flat-sawn ash still moves."),
    # Legacy 2026-09-06 selection, retained for existing non-room references only.
    # Bathroom floors now use materials_flooring.py's product-specific epoxy-grouted stacks.
    Material(tag="tile-floor-24", name='Porcelain floor tile, 24x24 matte rectified',
             hatch="masonry", color="#e8e4dc",
             product_ref="PROD-MARAZZI-MF01",
             source="Marazzi Modern Formation Peak White MF01, 24x24 matte rectified, DCOF >=0.42, absorption <0.5%, USA made (owner selection 2026-09-06). A warm limestone-look white sits right next to the bleached red oak where a cool 'pure white' porcelain fights it and reads clinical. The MUDROOM takes the same tile in TEXTURED for a higher wet DCOF against snowmelt, salt and grit. ** V3 HIGH SHADE VARIATION: lay out eight pieces from a full box before committing. ** Grout is PERMACOLOR Select in a warm light-to-mid grey, one to one-and-a-half shades darker than the tile -- NOT bright white (MN road salt blooms white over black grime, and a rectified arris micro-abrades and lays a PERMANENT grey shadow along every joint by year three) and NOT charcoal, which merely inverts the problem: hard water, soap film and dried cleaner all dry to a WHITE haze. Make a grouted sample board at the real joint width and look at it dry, at 72 hours, lying flat, under the actual fixtures."),
    # The wall tile. A flat quiet white with NO veining, because the oak is the thing in the
    # room that should have figure. 12x24 rather than 24x24 on a wall: the same 1/8"
    # rectified joint, half the sheet weight to hang, and it modules better against a niche.
    #
    # ** THE SHOWER PAN IS A DELIBERATE HEDGE. ** Schluter's own copy notes that a
    # single-plane slope to KERDI-LINE lets large format run into the pan, which would cut
    # grout from ~12.8 lf/sf to 1.5. Take the linear drain and the single-slope pan, but
    # still take the tile down to 2x2 in the pan itself: DCOF >=0.42 is an ANSI A326.3
    # threshold for LEVEL surfaces, and a sloped soapy floor is past what it contemplates.
    # The pan is 12-16 sf, so the grout accepted is trivial and the traction is not.
    #
    # Shower walls retain their epoxy specification. The four room floors also use epoxy
    # under the owner's 2026-10-22 selection; the earlier cement-floor preference is superseded.
    Material(tag="tile-wall-1224", name='Porcelain wall tile, 12x24 matte rectified',
             hatch="masonry", color="#f0eeea",
             product_ref="PROD-TILEBAR-BRONX-WHITE",
             source="TileBar Bronx White 12x24 matte rectified, DCOF 0.5 (owner selection 2026-09-06). Smooth matte deliberately: a DEEPLY textured matte holds soap film and a gloss glaze shows every drip. Grout is SPECTRALOCK PRO epoxy on the walls and in the pan. ** COLOUR-MATCHED 100% SILICONE AT EVERY CHANGE OF PLANE (TCNA EJ171), 5-6 tubes from one lot: ** grouting a perimeter hard defeats the uncoupling membrane you paid for, and sanded ACRYLIC caulk sits right beside the grout in matching colours and is not a movement joint. ** TRIMLESS EDGES, WITH THREE EXCEPTIONS: ** profile on the shower CURB only (the most abused edge in the house -- never mitre a curb); mitre the shower outside corner if the setter has a portfolio of them; and no profile where the wall tile stops -- use a drywall shadow-gap reveal, because a horizontal bead at eye level is a visible ledge and a dust-catcher. Return field tile into the niche rather than trimming it, size the niche to the 12x24 module so the back is full pieces, and SLOPE THE SILL: a flat niche sill is a permanent puddle and the most common niche failure."),
    # The EPS stay-in-place deck form (DECK_EPS_INT). Deliberately *not* `icf-eps`,
    # whose R-4.0/inch is the bead EPS on its own: this section is ribbed, and the concrete
    # that fills the ribs bridges it. BuildDeck publishes the R as installed per section,
    # and this deck is the 10" one at R-29 — R-2.9/inch through the finished deck. Name the
    # SECTION, not a per-inch constant carried over from another depth.
    # --- the sunken-garden court's field build-up ---------------------------------
    # Five house-local materials, all specific to `GARDEN_PUTTING_GREEN`. None appears in any
    # other assembly, so retiring the turf field retires them with it. Every one of them is
    # a USGA *specification*, not a product: the gravel's bridging factor is computed against
    # the actual sand purchased, and the rootzone is qualified by an A2LA lab against USGA
    # Tables 3 and 4. An assembly can record the specification; it cannot record the test.
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
    # The roof's DECK vapour barrier (ROOF), over the taped ZIP and under the foam.
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
    # The ventilated underlayment mat under the standing seam. NOT a furring strip: a ~1/4"
    # nylon-matrix mat rolled over the underlayment, which the panel clips screw straight
    # through into the top deck below. It is the assembly's only outward drying path, and
    # without it the walk runs to the standing seam itself — which is rated 0 perm, so every
    # plane inboard of it sits at interior vapour pressure and NO unvented stack under a
    # metal roof can pass the gate at all, at any foam thickness. Metal manufacturers now
    # ask for one over self-adhered underlayment for this exact reason.
    # **The membrane that replaced all three of them** — the deck vapour barrier above,
    # the vent mat above it and the permeable synthetic below are all UNREFERENCED, kept
    # here so the nine-layer stack is a revert and not a re-derivation (see ROOF).
    #
    # High-temp self-adhered BUTYL, rated >= 240 F, over the whole deck rather than as an
    # eave band (GRACE ULTRA basis; Henry PE200HT is SBS, not butyl). Both chemistries
    # have fastener-sealing products; the house retains butyl. Product confirmation for
    # the unvented full-coverage application remains open (roof_sheathing_and_membranes.md).
    # Sealing around fasteners matters because
    # ~1,160 standing-seam nail-flange screws through the field are this roof's actual water risk —
    # not pipes, not curbs, and not the 48 non-penetrating S-5! PV clamps.
    #
    # Its 0.05 perm is NOT a hedge to be argued with. Under a 0-perm metal panel there is no
    # outward drying path at any permeance, which is exactly why the assembly takes the
    # R806.5 item 5.1.3 route instead of a drying one; a vapour-open self-adhered sheet (SIGA
    # Majvest SA, Pro Clima SOLITEX MENTO 3000 Connect, ~34-38 perms) would give permeability
    # with nowhere to go, and would give up the self-sealing that is the point. Named here so
    # the option is on the record and was rejected on purpose.
    # --- mudroom exposed-stud wall ---------------------------------------------
    # Appearance-grade framing, because in W-M-STRW the studs ARE the finish. Select
    # Structural S4S with eased corners: the grade buys straightness and a clean face, the
    # eased arris keeps a hand running along an exposed edge off a sharp corner. Douglas
    # fir-larch rather than SPF: it is the denser species (~32 pcf vs SPF's ~29), which is
    # why its R/inch is *lower* than spf's 1.24 — conductivity tracks density in wood.
    # The bays' flat courses (bench support, 6' shelf, 7' cap) and the bench board are red
    # oak (`oak-8q`; it was `white-oak-8-4` until the pile turned out to be red oak).
    Material(tag="oak-8q", name='Red oak 8/4, custom-milled S4S to 1 1/2"',
             hatch="lumber", color="#d6c9b3", finish="oak-board", species="red-oak",
             nominal_quarters=8, milling_profile="S4S", requires_custom_milling=True,
             source="Owner-milled red oak, 8/4 dressed to 1 1/2\" so a flat course sits flush with the 2x6 studs it spans between. The house red-oak system: A/B bleach, Bona NordicSeal, waterborne topcoat."),
    # The stair face. 3/4" rather than the 1/2" a plain panel finish would take, because
    # this panel is structural backing: coat hooks and the closet rail screw straight into
    # it anywhere along the wall, with no blocking behind and no stud to hunt for.
    # GARAGE_WALL_2X6's sheathing, replacing the 1.5" Zip-R.
    #
    # A SEPARATE TAG FROM `struct-1-plywood`, and deliberately. Structural 1 is a premium
    # shear-rated grade — a specific veneer layup ordered where a braced-wall line is being
    # engineered for it — and the garage is not that wall. Billing this sheet at Structural
    # 1's rate would overstate the sheathing on every square foot of a 24'x24' building and
    # would quietly re-spec what the yard delivers. CDX is the ordinary sheathing panel:
    # C-face, D-back, exterior glue.
    #
    # 5/8" and not 1/2": the studs are at 24" o.c. here, and 5/8" is the panel
    # that spans it comfortably and takes a face-fastened screw without dishing between the
    # crowns of the corrugated skin over it.
    #
    # Thermal/vapour numbers are the plywood series' — this is the same veneer panel as
    # `struct-1-plywood` and `plywood-subfloor`, and nothing hygric moves with the grade.
    # It carries NO `control` set in the assembly: the ccSPF in the bays behind it is the
    # air/water plane now, exactly as EXT_2X6 does it, and a bare CDX sheet is not
    # a WRB and must not be authored as one.
    # `ENTRY_SCREEN_WALL`'s EAST ply, and only that. One panel does two jobs there: it is a
    # rated wood structural panel (SDPWS Table 4.3B publishes shear values for Rated Siding
    # exactly as for Rated Sheathing) AND it is the finished, paint-ready face of the screen
    # under the canopy. That is why it is not `cdx-plywood`: a CDX C/D face is a sheathing
    # face, and nothing on this wall covers it.
    #
    # MDO (medium density overlay): a resin-treated fibre overlay bonded to the face, which
    # is the standard paint substrate and what stops the veneer's grain telegraphing through
    # a coating. Exterior bond, because the wall is outdoors even where it is sheltered.
    # Thermal/vapour numbers are the plywood series' (cdx-plywood, struct-1-plywood,
    # plywood-subfloor) — the overlay is not modelled as a separate retarder, which is
    # conservative for drying to the east and is the only side that can dry here.
    # FS-ATTIC's deck sheet, and only FS-ATTIC's. The two unfinished lofts
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
    # SHIPLAP, not T&G — a profile change and nothing else. The SPECIES
    # does not move and must not: American basswood / Canadian poplar / aspen is a BURN-SAFETY
    # spec (low thermal conductivity, a bench you can sit on at 190 F), not a finish choice.
    # Shiplap because a rabbeted lap is a simpler knife grind than a tongue and groove and
    # dries and moves more forgivingly in a room that cycles 60 F to 190 F; the board still
    # reads as a board.
    #
    # `stock_bf_per_sqft` is thickness x (face width / coverage width): the lap loses face.
    # --- species wood finishes (plans/TODO.md §Hardwood) -----------------------
    # RM-M-STUDY wainscot to 36". Shiplap since 2026-10-07: a
    # rabbet is two passes on a table saw, a tongue and groove is a moulder job. 4/4 stock,
    # 5 1/2" face over 5" coverage: 1.1 bf per SF.
    Material(tag="walnut-shiplap", name="Black walnut shiplap wainscot (4/4)", r_per_inch=1.1,
             density=610.0, hatch="lumber", color="#80634f",
             finish="clear-satin-hardwax-oil", species="walnut", stock_bf_per_sqft=1.1,
             nominal_quarters=4, milling_profile="shiplap", requires_custom_milling=True,
             source="plans/TODO.md — first-floor study walnut paneling to 36\"; owner-milled shiplap"),
    # RM-M-MUDROOM's three east-facing walls (WP-M-MUDROOM-SHIPLAP): owner-milled red oak
    # shiplap, painted white. For wear and fasten-anywhere hooks, not looks.
    Material(tag="oak-shiplap-painted", name="Red oak shiplap, 4/4, painted white",
             r_per_inch=1.1, density=700.0, hatch="lumber", color="#f2f0ea",
             finish="shiplap", species="red-oak", wood_surface="painted", stock_bf_per_sqft=1.1,
             nominal_quarters=4, milling_profile="shiplap", requires_custom_milling=True,
             source="Owner-milled red oak, 5 1/2\" face over 5\" coverage, blind-nailed to studs and the gypsum behind. Red oak's open grain telegraphs through enamel: grain-fill it or accept the texture. Prime all faces with a shellac-based primer (oak tannin bleeds through latex), then two coats of white enamel."),
    # ** TOMBSTONE: `walnut-floor` (added and removed 2026-09-05). ** For a few hours the
    # suite and its walk-in were a 181.7 SF field of site-milled walnut strip flooring under
    # its own tag (a separate tag from `walnut-shiplap` so 182 SF would not bill in both
    # [floor_finishes] and [wood_surfaces]). It lost on three counts, all in
    # plan/storeys/second.py at RM-S-SUITE: walnut photo-LIGHTENS under the west windows'
    # UV, it is soft underfoot (~1010 Janka vs oak's ~1360), and flooring is the most
    # demanding cut off a family log pile for the least-seen surface. The floor is `oak`;
    # the band is WP-S-SUITE-HEADBOARD, a 6'-0" band on W-S-SN1/SN2 (now painted MDF and poplar).
    # If it ever comes back it needs its own tag again, `finish="strip-floor"`, and a
    # `STRIP_FLOOR_REFS` needle in ui/src/three/plankMaterial.ts.
    # The desk and leaf remain bought solid walnut; the upholstered bench is now
    # appearance-grade plywood with walnut facing/trim (materials_study_booth.py).
    # The desk top and its leaf: 5/4, dressing to 1" (2026-10-16, was 6/4). Short spans, and
    # 5/4 is the cheaper, easier bought thickness; the bench's 47" seat still wants 8/4.
    Material(tag="walnut-shelf-5q", name="Black walnut shelving, 5/4 S4S", hatch="lumber",
             density=610.0, color="#80634f", finish="clear-satin-hardwax-oil",
             species="walnut", nominal_quarters=5, milling_profile="S4S",
             requires_custom_milling=True,
             source="RM-M-STUDY call booth desk top and fold-down leaf; 5/4 dressed to 1\" over a 30-5/8\" span, one flitch for both"),
    # RM-M-LIVING's fireplace mantel, SB-M-FIRE-MANTEL. Same species, same finish and same
    # bought-not-milled accounting as the walnut above; ** 12/4 AND NOT 8/4, WHICH IS THE
    # WHOLE REASON IT IS A SEPARATE MATERIAL. ** The mantel finishes 2 1/4" — one brick bed
    # height, so it reads as a course pulled out of the wythe — and 8/4 dresses to 1 1/2".
    # `takeoff/hardwood.py` catches exactly that ("2.25\" finished cannot come out of 8/4"),
    # which is how this tag came to exist: the board was authored on `walnut-shelf-8q` first
    # and `haus millwork` refused to pretend. 12/4 dresses to 2 1/2", so 2 1/4" comes off it
    # with a skim to spare.
    #
    # No `stock_bf_per_sqft`, like the walnut above: this is a PIECE good cut to a finished
    # T x W x L, not a coverage good. Its dollars are NOT here and not in `haus millwork`
    # either — see `finish-fireplace-mantel-walnut` in prices.toml [allowances], and the
    # note on SB-M-FIRE-MANTEL for why a wall-hosted ShelfBank has no host row to carry them.
    Material(tag="elm-mantel-12q", name="American elm mantel shelf, 12/4 S4S", hatch="lumber",
             density=560.0, color="#bd9975", finish="clear-satin-hardwax-oil",
             species="elm", nominal_quarters=12, milling_profile="S4S",
             requires_custom_milling=True,
             source="RM-M-LIVING fireplace mantel (elm since 2026-10-16, walnut before). 12/4 because the shelf finishes 2 1/4\" — one modular brick bed height, so it reads as a single course pulled proud of the wythe — and 8/4 dresses to 1 1/2\". Matches the elm slat partition."),
    # Slats and visible plates share 5/4 rough stock, dressed to 1" (2026-10-20).
    Material(tag="elm-slat-5q", name='American elm slats and plates, 1" x 2 1/2", from 5/4 rough',
             hatch="lumber", density=560.0, color="#bd9975", finish="oak-board",
             species="elm", nominal_quarters=5, milling_profile="S4S",
             requires_custom_milling=True,
             source="5/4 rough elm dressed to 1\" and ripped to 2 1/2\", one piece per slat or plate. Kiln-dried to 6-8% MC; rift sticks off the board edges, no pith; rip oversize, rest indoors a week or two, then dress; mill ~25% extra and reject any stick that moves. Hardwax oil all faces."),
    # The booth's acoustic felt, band 36" to 9'-0" on the south and north walls
    # of RM-M-STUDY. ** NO `species`. ** That one field is the gate on `haus millwork`
    # (takeoff/hardwood.py — "a milling schedule is only about wood"); set it and PET felt is
    # scheduled as lumber. ** NO `stock_bf_per_sqft` either: ** it is the only input to
    # `paneling._band_thickness_m`, and leaving it unset draws the band at the 1/2" default,
    # which is exactly the panel thickness. Bills into prices.toml `[wood_surfaces]` on the
    # material tag, the same join WP-B-SAUNA-SPLASH's tile takes.
    # The suite's two 6-1/4\" square tudor posts, ordered as 10' sections and cut down.
    # `nominal_quarters=8` is not decoration: a clear 6\" elm timber would check badly
    # drying, so these are GLUED UP from 8/4 board stock (prices.toml records the same
    # thing in prose). Five laminations of a 1-1/2\" dressed board make the 6-1/4\" face,
    # and `takeoff/hardwood.py` derives that count from this field rather than scheduling
    # two timbers nobody can saw.
    # NO `nominal_quarters`: this is a SAWN TIMBER, cut 6-5/8" square out of an elm log and
    # dressed back to 6-1/4", not a stack of board stock. Authoring 8/4 here would read as
    # "five laminations of 1-1/2"" on the milling schedule, which is a real way to make a
    # post and is not how these two are made.
    Material(tag="elm-timber", name="Elm timber 6-1/4\" square, S4S, sawn to section",
             r_per_inch=1.1,
             density=560.0, hatch="lumber", color="#bd9975",
             finish="clear-satin-hardwax-oil", species="elm",
             milling_profile="S4S", requires_custom_milling=True,
             source="plans/TODO.md — suite bedroom tudor posts, 10' sections cut to fit"),
    # Bought interior trim (plan/millwork.py TRIM-STANDARD), painted the walls' latex-paint
    # white. No species: none of it reaches `haus millwork`; prices.toml bills it by the LF.
    Material(tag="pine-fj-base", name='Finger-jointed pine base, 3/4" x 3 1/2" S4S',
             hatch="lumber", color="#f0ede6", finish="satin-enamel", milling_profile="S4S",
             product_ref="PROD-STOCK-PINE-FJ-1X4",
             source="Primed finger-jointed pine 1x4 from the yard, painted in the wall colour."),
    Material(tag="poplar-skirt-paint", name='Poplar skirt board, 1x12 S4S, paint grade',
             hatch="lumber", color="#f0ede6", finish="satin-enamel", species="poplar",
             milling_profile="S4S",
             source='Stock 3/4" x 11 1/4" poplar 1x12 from the yard, primed and painted the wall white. The stair skirts, set before the treads and risers.'),
    Material(tag="mdf-casing", name='MDF door casing, 3/4" x 3 1/2" S4S',
             hatch="lumber", color="#f0ede6", finish="satin-enamel", milling_profile="S4S",
             product_ref="PROD-STOCK-MDF-1X4",
             source="Primed MDF 1x4, painted in the wall colour. Kept out of the wet rooms: MDF swells at a cut edge."),
    Material(tag="pvc-trim", name='Cellular PVC trim, 3/4" x 3 1/2" S4S',
             hatch="lumber", color="#f0ede6", finish="satin-enamel", milling_profile="S4S",
             product_ref="PROD-STOCK-PVC-1X4",
             source="White cellular PVC 1x4 (Azek/Versatex class), painted with the walls. The bathrooms and the 70% RH plant room. In the tile baths it goes in after tile: stainless trim nails + PVC adhesive, sitting on the tile."),
    Material(tag="mdf-panel-painted", name='Paint-grade MDF backing, 1/4", white enamel',
             color="#f0ede6", finish="satin-enamel",
             source="Bought 1/4 inch MDF sheets over continuous gypsum. Prime faces and cut edges; white enamel matching trim. Includes field painting in the paneling rate."),
    Material(tag="poplar-batten-painted", name="Tulip poplar S4S rails and battens, warm white enamel",
             hatch="lumber", color="#e7e2d8", finish="satin-enamel", species="poplar",
             wood_surface="painted", milling_profile="S4S", requires_custom_milling=False,
             source="Bought S4S tulip poplar: 1x3 battens and 1x4 top rail, actual 3/4 inch thick. Prime and warm white satin enamel (#e7e2d8), subtly contrasting the MDF field (#f0ede6); installation/painting priced by LF, not owner milling."),
    # W-M-STRW's stair-face leaf, which is also the back of the mudroom coat nooks. Overlay on
    # both faces because both are painted. Plywood-series thermal/vapour numbers.
    Material(tag="mdo-plywood-interior", name='1/2" MDO plywood, two-sided overlay, painted white',
             r_per_inch=1.25, density=610.0, perm_rating=0.30, hatch="lumber", color="#f2f0ea",
             finish="satin-enamel",
             source="1/2 in. medium density overlay plywood, overlay both faces (MDO 2S), interior paint grade. Resin-fibre face takes paint without grain telegraphing and holds hook screws. Seal edges, prime and paint both faces with the same white scrubbable enamel as the mudroom shiplap (#f2f0ea) before hanging."),
    *MATERIALS_ENTRY_SCREEN,
    *MATERIALS_HARDWOOD,
    *MATERIALS_STUDY_BOOTH,
    *MATERIALS_METAL,
    *MATERIALS_ISHTAR,
    *MATERIALS_FLOORING,
    *MATERIALS_TITANIUM,
]
