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


MATERIALS = [
    *ALL_MATERIALS,
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
    # ** SILICA IS A REAL CONSIDERATION AND HERE IT IS ALSO FREE. ** Silestone is now HybriQ
    # at <=40% crystalline silica against 90-95% for conventional quartz including Cambria;
    # Cal/OSHA voted 2026-05-21 to initiate a prohibition on fabricating engineered stone over
    # 1% silica after 592 silicosis cases, 65 lung transplants and 31 deaths among California
    # fabricators since 2019, and Australia banned it outright. There is NO Minnesota or
    # federal ban and quartz buys with zero friction here — but the low-silica slab is also
    # the cheaper one, so the choice costs nothing. What it does NOT do is protect the
    # fabricator by itself: vet the SHOP, not the showroom — wet cutting on every operation
    # including hand edge-work, respirators on faces, and OSHA silica exposure monitoring on
    # file. That is the strongest argument against the big-box route, which subs the cut to an
    # undisclosed shop you can neither inspect nor hold to a cantilevered overhang.
    Material(tag="quartz-counter", name="Engineered quartz countertop, 3 cm",
             density=2400.0, hatch="masonry", color="#f2efe9", finish="polished",
             product_ref="PROD-SILESTONE-ET-CALACATTA-GOLD", engineered_stone=True,
             source="Silestone Et Calacatta Gold, 3 cm, eased edge (owner selection 2026-09-06). Kitchen perimeter and sink run, the 48\" and 51\" vanity tops, and the peninsula's 24\" work surface. ** NEVER CLEAN IT WITH ANYTHING HIGH-pH: ** bleach, ammonia, glass cleaner, degreasers, scouring powder and melamine sponges are the #1 cause of light quartz yellowing across every brand — not UV. #2 is heat scorch, which is irreversible; induction helps (no flame spill, no hot grate) but a 400 F pan is still a 400 F pan. Put that in the owner's manual."),
    # ** THE PENINSULA'S OVERHANG IS THE ONE PLACE THE STONE STOPS, AND IT IS AN ENGINEERING
    # LIMIT RATHER THAN A PREFERENCE. ** CASE-PENINSULA-120 is a 24" carcass carrying a 15"
    # knee (NKBA's figure for a 36" counter). Caesarstone's own rule for engineered quartz is
    # max overhang = 1/3 of depth and not more than 15", with up to 14" unsupported in 3 cm —
    # and 15" on a 24" carcass is 38% of depth, outside the rule and outside the warranty.
    # Steel plate would buy it back; so does putting a different material on the cantilever.
    #
    # The owner mills white oak off family land in southern Minnesota at ~$2/sf in 4/4 and
    # 8/4 up to 18" wide, and 1.5-1.75" of solid oak cantilevers 15" without an argument. So
    # the peninsula is quartz on the 24" work surface and oak on the 15" bar top, meeting at
    # the carcass face. That also deletes the jumbo-slab problem in the same move: a 120" x
    # 39" seamless quartz top needs a jumbo (a standard slab is 57" x 120", i.e. ZERO cutting
    # margin) and consumes 39" of a 65" slab for 35-45% waste on a slab paid for in full,
    # while a 24"-deep strip cuts out of a standard slab with ordinary yield.
    #
    # ** MILL IT TO 1 3/16" SO THE TWO TOPS ARE FLUSH ** — 3 cm is 1.181", and neither 4/4
    # (13/16" dressed) nor 8/4 (1 3/4") lands there on its own. Strips run the LONG way,
    # fastened with slotted screws or figure-8s because 39" of solid oak moves hard between a
    # Minnesota January and July, and ** finish all six faces equally including the underside
    # ** — that is the detail that fails on shop-built tops. The joint between stone and wood
    # is a colour-matched silicone MOVEMENT joint, never grout or hard caulk. The EAST 24" of
    # the peninsula is not overhang at all (FURN-M-KIT-MIXER-GARAGE stands full-depth on it),
    # so the oak top runs the western ~96" only.
    Material(tag="oak-counter", name='White oak bar top, 1 3/16", site-milled',
             r_per_inch=1.0, density=750.0, hatch="lumber", color="#c9a978",
             finish="hardwax-oil",
             source="Owner's own white oak, milled to match 3 cm quartz flush. The peninsula's 15\" seating overhang ONLY -- see the quartz-counter note above for why the stone stops at the carcass face. The 36\" kitchen sink base stays quartz: do not put water and wood together."),
    # ** THE FLOOR TILE, AND THE SELECTION IS ARITHMETIC BEFORE IT IS TASTE. ** Grout length
    # per square foot is 144 x (1/a + 1/b): a 24x24 gives 1.0 lineal ft/sf, a 3x12 subway
    # gives 5.0, a penny round gives 24+. Large-format is ~3x easier to keep clean than
    # subway and ~9x easier than mosaic, and THAT is the cleanability decision; grout colour
    # and grout chemistry come second and third.
    #
    # ** "RECTIFIED" IS THE HIGHEST-LEVERAGE WORD ON THE SPEC SHEET. ** ANSI A108.02 4.3.8.1:
    # tile with any side over 15" takes a 1/8" minimum joint if rectified and 3/16" if not —
    # so a non-rectified 24x24 gives the same look and three times the grout area. Confirm it
    # on the spec sheet and not in the sales copy. The price of rectified is that square
    # arrises show lippage: budget a levelling-clip system and a flat substrate.
    #
    # ** PATTERN IS STACK BOND, 0% OFFSET, AND A 50% RUNNING BOND IS OUT OF STANDARD HERE. **
    # There is no "TCNA 5% rule" — the governing text is ANSI A108.02 4.3.8.2: where the
    # offset side exceeds 15" nominal, only offsets of 33% or less shall be specified. So a
    # third is the MAXIMUM permitted and a half is not available without an owner-approved
    # mock-up (long tiles crown slightly, and a 50% offset lands the neighbour's edge at the
    # peak). Stack bond is simultaneously the lowest-lippage install, the easiest to mop and
    # the correct minimalist language. Align wall and floor joints at the base of the wall
    # where geometry allows; that single move is what makes a room read designed.
    Material(tag="tile-floor-24", name='Porcelain floor tile, 24x24 matte rectified',
             hatch="masonry", color="#e8e4dc",
             product_ref="PROD-MARAZZI-MF01",
             source="Marazzi Modern Formation Peak White MF01, 24x24 matte rectified, DCOF >=0.42, absorption <0.5%, USA made (owner selection 2026-09-06). A warm limestone-look white sits right next to white oak where a cool 'pure white' porcelain fights it and reads clinical. The MUDROOM takes the same tile in TEXTURED for a higher wet DCOF against snowmelt, salt and grit. ** V3 HIGH SHADE VARIATION: lay out eight pieces from a full box before committing. ** Grout is PERMACOLOR Select in a warm light-to-mid grey, one to one-and-a-half shades darker than the tile -- NOT bright white (MN road salt blooms white over black grime, and a rectified arris micro-abrades and lays a PERMANENT grey shadow along every joint by year three) and NOT charcoal, which merely inverts the problem: hard water, soap film and dried cleaner all dry to a WHITE haze. Make a grouted sample board at the real joint width and look at it dry, at 72 hours, lying flat, under the actual fixtures."),
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
    # ** EPOXY THE SHOWER, CEMENT THE FLOORS, AND NEVER EPOXY THE MUDROOM. ** At a 1/8" joint
    # on rectified 24x24 the grout is ~1% of the floor; epoxy's advantage is per unit of
    # grout SURFACE, matte warm-white porcelain is the worst possible haze substrate, and
    # PERMACOLOR needs no sealer ever. Epoxying the floors is a $1,200-1,800 decision to
    # improve 1% of the floor at ~2.5x the grouting labour.
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
    # eave band (Grace Ultra / Henry Blueskin PE200HT class). Butyl rather than SBS for one
    # reason that outranks every other property here: it self-seals around a fastener, and
    # ~1,160 standing-seam clip screws through the field are this roof's actual water risk —
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
    # `stock_bf_per_sqft` is RE-DERIVED, not carried over: it is thickness x (face width /
    # coverage width), and the lap loses more face than the tongue did. 5/4 stock on a
    # 5-1/2" face over a 5" coverage is 1.25 x 1.10 = 1.375 bf/sf, against 1.25 for the T&G
    # (which was authored as bare thickness, with no face allowance at all). The order goes
    # up; the wall area does not.
    # --- species wood finishes (plans/TODO.md §Hardwood) -----------------------
    # RM-M-STUDY wainscot to 36". 4/4 stock: board feet = square feet.
    Material(tag="walnut-tg", name="Black walnut T&G wainscot (4/4)", r_per_inch=1.1,
             density=610.0, hatch="lumber", color="#5d4433",
             finish="clear-satin-hardwax-oil", species="walnut", stock_bf_per_sqft=1.0,
             nominal_quarters=4, milling_profile="T&G", requires_custom_milling=True,
             source="plans/TODO.md — first-floor study walnut paneling to 36\""),
    # ** TOMBSTONE: `walnut-floor` (added and removed 2026-09-05). ** For a few hours the
    # suite and its walk-in were a 181.7 SF field of site-milled walnut strip flooring under
    # its own tag (a separate tag from `walnut-tg` so 182 SF would not bill in both
    # [floor_finishes] and [wood_surfaces]). It lost on three counts, all in
    # plan/storeys/second.py at RM-S-SUITE: walnut photo-LIGHTENS under the west windows'
    # UV, it is soft underfoot (~1010 Janka vs oak's ~1360), and flooring is the most
    # demanding cut off a family log pile for the least-seen surface. The floor is `oak`;
    # the walnut is WP-S-SUITE-HEADBOARD, a 6'-0" band on W-S-SN1/SN2 under `walnut-tg`.
    # If it ever comes back it needs its own tag again, `finish="strip-floor"`, and a
    # `STRIP_FLOOR_REFS` needle in ui/src/three/plankMaterial.ts.
    # The call booth's bench seat and desk top, the same walnut as the wainscot
    # they sit against. ** `nominal_quarters=8` IS REQUIRED, not decoration: ** both pieces
    # finish 1-1/2", 4/4 dresses to 3/4", and `takeoff/hardwood.py` flags a finished piece
    # that cannot come out of the stock it names.
    #
    # Deliberately no `stock_bf_per_sqft`: like the oak below, these are PIECE goods cut to a
    # finished T x W x L, not a coverage good. Unlike the oak below, this walnut is BOUGHT —
    # so it appears on `haus millwork` for the mill AND its dollars stay inside the
    # `[placeables]` rows for FT-STUDY-BENCH / FT-STUDY-DESK. See prices.toml; getting that
    # backwards puts the most expensive material in the room at $0.
    Material(tag="walnut-shelf-8q", name="Black walnut shelving, 8/4 S4S", hatch="lumber",
             density=610.0, color="#5d4433", finish="clear-satin-hardwax-oil",
             species="walnut", nominal_quarters=8, milling_profile="S4S",
             requires_custom_milling=True,
             source="plans/TODO.md — RM-M-STUDY call booth. 8/4 because both pieces are structural millwork on a 45-5/8\" and a 30-5/8\" span with no stiffener: a bench seat someone sits on and a fixed desk top someone leans on"),
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
    Material(tag="walnut-mantel-12q", name="Black walnut mantel shelf, 12/4 S4S", hatch="lumber",
             density=610.0, color="#5d4433", finish="clear-satin-hardwax-oil",
             species="walnut", nominal_quarters=12, milling_profile="S4S",
             requires_custom_milling=True,
             source="RM-M-LIVING fireplace mantel (2026-09-06). 12/4 because the shelf finishes 2 1/4\" — one modular brick bed height, so it reads as a single course pulled proud of the wythe — and 8/4 dresses to 1 1/2\". Bought walnut, not the family's oak stock"),
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
             density=560.0, hatch="lumber", color="#b08d5e",
             finish="clear-satin-hardwax-oil", species="elm",
             milling_profile="S4S", requires_custom_milling=True,
             source="plans/TODO.md — suite bedroom tudor posts, 10' sections cut to fit"),
    # --- owner-milled white-oak stock -------------------------------------------------
    #
    # White oak off family land in southern Minnesota, rough-milled: boards commonly 12\"+
    # wide and out to 18\", in 4/4 and 8/4. Owner-supplied stock wins on WIDTH and FLATNESS
    # — a one-piece stool, shelf or tread — and loses on PROFILE, where a knife grind plus a
    # molder setup cannot amortise over one house. That is why there is no oak baseboard or
    # casing tag here and `finish-interior-trim-and-baseboard` stays a lump.
    #
    # These are PIECE goods, not coverage goods: each one is cut to a finished T x W x L, so
    # they carry `nominal_quarters` (the stock a mill saws) and deliberately no
    # `stock_bf_per_sqft` (a coverage factor, which would be meaningless on a stool). They
    # appear in no assembly layer, no room finish and no paneling, so they enter no other
    # take-off section — `haus millwork` is where they are ordered from.
    Material(tag="oak-floor-custom", name='3/4" white-oak strip flooring, site-milled',
             hatch="lumber", color="#c69c6d", species="oak", finish="strip-floor",
             stock_bf_per_sqft=1.0, nominal_quarters=4, milling_profile="T&G",
             finish_thickness_in=0.75, requires_custom_milling=True,
             source="Catlin owner-milled white oak floor; local rather than the factory library product so only this house enters the custom milling schedule."),
    Material(tag="catlin-sauna-shiplap",
             name="Basswood/aspen shiplap sauna liner (5/4), site-milled",
             r_per_inch=1.3, perm_rating=20.0, hatch="lumber", color="#e6d4ae",
             finish="shiplap", species="basswood", stock_bf_per_sqft=1.375,
             nominal_quarters=5, milling_profile="shiplap", requires_custom_milling=True,
             source="Catlin site-milled sauna liner; local rather than the factory library product so this coverage reaches the custom milling schedule."),
    Material(tag="oak-stool", name="White oak window stool, 8/4 S4S", hatch="lumber",
             color="#c69c6d", finish="clear-satin-hardwax-oil", species="oak",
             nominal_quarters=8, milling_profile="eased", requires_custom_milling=True,
             source="owner-milled white oak, ~$2/sf rough. 8/4 because the interior return on an outie window runs most of a 13 7/8\" wall and a 3/4\" board that wide will cup; the front edge is eased, not moulded (see the profile note above)"),
    Material(tag="oak-shelf-8q", name="White oak shelving, 8/4 S4S", hatch="lumber",
             color="#c69c6d", finish="clear-satin-hardwax-oil", species="oak",
             nominal_quarters=8, milling_profile="S4S", requires_custom_milling=True,
             source="owner-milled white oak. 8/4 wherever the shelf is visible or LOADED: 1-1/2\" needs no stiffener and no edge banding at a 2'-6\" bay, and it is the thickness a climbable shelf wants (notes/pantry_climbable_shelving.md)"),
    Material(tag="oak-shelf-4q", name="White oak shelving, 4/4 S4S", hatch="lumber",
             color="#c69c6d", finish="clear-satin-hardwax-oil", species="oak",
             nominal_quarters=4, milling_profile="S4S", requires_custom_milling=True,
             source="owner-milled white oak. 4/4 for the light-duty cases — a 12\"-deep bookcase shelf and a bath alcove shelf carry books and towels, not people"),
    Material(tag="oak-tread", name="White oak stair tread, 8/4 bullnose", hatch="lumber",
             color="#c69c6d", finish="clear-satin-hardwax-oil", species="oak",
             nominal_quarters=8, milling_profile="bullnose", requires_custom_milling=True,
             source="owner-milled white oak. Tread and landing nosings share the bullnose setup; the landing nosing also gets a groove to meet the T&G field"),
    *MATERIALS_METAL,
    *MATERIALS_ISHTAR,
]
