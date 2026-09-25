# haus: editable
# Catlin assemblies — the retired Ishtar scheme, still referenced.
# Split out of plan/assemblies.py verbatim.
from typehaus import (
    Material,
)


MATERIALS_ISHTAR = [
    # --- the Ishtar scheme, RETIRED 2026-09-04 -----------------------------------------
    # Three faces on one wythe, banded by Layer.slot in BASEMENT_BRICK_VENEER: a lapis field
    # with golden-yellow registers over an unglazed brown plinth, after the Ishtar Gate of
    # Babylon. Same clay unit, R-value, density and permeance as every other brick here —
    # a brick is a brick and only the face differs, which is the whole reason `finish` and
    # `color` are separate fields from the physics.
    #
    # BOTH GLAZES ARE NOW UNREFERENCED, and both stay, on the same convention as
    # `glazed-green-brick` above: the wall went to one flat unglazed buff/brown field on
    # 2026-09-04 and the Materials, their MasonryStyles and their _FINISH_BASE entries are
    # the whole cost of getting the scheme back. Do not delete them to tidy up. Their
    # prices.toml rows are commented out rather than removed for the same reason.
    #
    # All three hexes are authored a step DARKER than their reference colour, deliberately.
    # An authored colour is an albedo, and the viewer lights with 0.8 hemisphere + 0.9 key +
    # 0.6 IBL over unit irradiance, so a saturated surface arrives on screen well above what
    # is written here — the same lesson #1c1f24 records below. Author under the tone you
    # want to see, and re-check against `haus render --view elevation`.
    Material(tag="glazed-lapis-brick", name="Glazed lapis-blue face brick",
             r_per_inch=0.20, density=1920.0, perm_rating=1.0, hatch="concrete",
             color="#10386a", finish="glazed-lapis-brick",
             source="basement south veneer, the Ishtar field (2026-08-20 to 2026-09-04) — glazed brick, 1\" airgap off the existing concrete wall; RETIRED when the wall went to one flat unglazed field, kept in the catalog as the revert target"),
    # The registers. Same glaze technology as the lapis and so the same low jitter, but it is
    # a SECOND colour on the same job: its own special-order pallet, its own lead time, and a
    # mason laying two colours to a line rather than one. That is a price fact, not a
    # rendering one — see [wall_structure] in prices.toml.
    Material(tag="glazed-gold-brick", name="Glazed golden-yellow face brick",
             r_per_inch=0.20, density=1920.0, perm_rating=1.0, hatch="concrete",
             color="#c08a12", finish="glazed-gold-brick",
             source="basement south veneer, the Ishtar register bands (2026-08-20 to 2026-09-04) — glazed brick, 1\" airgap off the existing concrete wall; RETIRED with the lapis field, kept in the catalog as the revert target"),
    # THE WHOLE WALL since 2026-09-04, and unchanged as a Material: ordinary unglazed
    # buff/brown face brick, ASTM C216 Grade SW, the cheapest brick that was ever on this
    # wall and the only one a Twin Cities yard carries off the shelf. It was the Ishtar
    # plinth's 28 SF; it is now the full 129 SF field.
    #
    # Specify it as a SINGLE light body, not a blend. It was first authored dark and at the
    # red brick's full variegation, on the argument that an unglazed body beside a fired
    # glaze is what makes the glaze read as a glaze; on the wall that came out as a plinth
    # laid from mixed pallets with near-black units through it, which is a different
    # building. One light brown reads as one brick.
    #
    # #a07c5c is already authored a step under its target (the albedo lesson #1c1f24 records
    # below) — do NOT re-darken it. What DID have to move with the swap is the renderer's
    # variegation: BROWN_BRICK_STYLE's jitter was set near zero for a 28 SF plinth beside a
    # glaze, and at 129 SF with nothing to contrast against that reads as a printed sheet.
    # See ui/src/three/materials.ts, kept in step by hand.
    Material(tag="brown-brick", name="Brown face brick (unglazed)",
             r_per_inch=0.20, density=1920.0, perm_rating=1.0, hatch="concrete",
             color="#a07c5c", finish="brown-brick",
             source="basement south veneer over the sunken garden — the Ishtar plinth 2026-08-20, the whole field since 2026-09-04; standard unglazed ASTM C216 Grade SW face brick, no special order"),
    # cmu, grout (porch railing wythe/balcony post bases) were promoted to
    # library/materials/ (CONTRIBUTING §Promotion flow); they arrive here
    # through ALL_MATERIALS above.
    # The house's one exterior dark: every dark metal element on the
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
    # The SAME dark, on seamless K-style stock. It exists only because it is a different
    # PRODUCT, and prices.toml qualifies [drainage] on the material tag: the garage low eave
    # and the balcony run are roll-formed on site from prefinished coil off the truck, which
    # every manufacturer's colour card carries, while the house eaves are shop-brake-formed
    # box gutter at 3x the foot. Sharing `metal-dark-exterior` with those billed 47.8 LF of
    # colour-card stock as fabrication. Colour is deliberately identical — the eave line must
    # read continuous — so every palette entry for it points at the same ink.
    Material(tag="metal-dark-kstyle", name="Near-black prefinished K-style gutter coil",
             r_per_inch=0.0, density=2700.0, perm_rating=0.0, hatch="metal",
             color="#1c1f24",
             source="garage south eave + balcony gutter/leaders, prefinished aluminium coil"),
    # The garage's base skin, and since 2026-09-03 it is the ONLY thing on it: the 24" band
    # on the ICF stem, all four walls, plus the stem-top Z at the corrugated panel base.
    # The 4'-0" east wainscot this material also clad was deleted that day. Painted
    # aluminium flat sheet, 3105-H14 or 5005, 2-coat 70% PVDF (Kynar 500 / Hylar 5000),
    # 0.040" minimum and 0.050" preferred — NOT 0.019" trim coil, which takes a permanent
    # dimple from a shovel corner in exactly the zone this exists to survive.
    #
    # ** THE HEAVY GAUGE SURVIVED THE WAINSCOT, AND IT IS FREE. ** With only a ~24" band
    # left, 24" trim coil is the obvious buy and it is the WRONG one: stock 48" x 120"
    # architectural sheet rips into exactly TWO 24" bands with no waste, so the heavier
    # metal costs nothing per SF over coil and the dent argument above is unchanged. The
    # band is still the shovel/plow-splash zone; it just got shorter.
    #
    # SECOND BEST, IF A SUPPLIER CANNOT GET SHEET: 0.024" heavy-gauge aluminium trim coil in
    # a 24" width, the thickest the trim-coil product line reaches (0.027" in a few lines).
    # That is a REAL fallback and is why it is written down rather than left to the field.
    # 0.019" standard trim coil is NOT the fallback — it is the thing this note rejects.
    #
    # ALUMINIUM, WHERE EVERY OTHER PANEL ON THIS BUILDING IS STEEL, AND THAT IS THE POINT.
    # `corrugated-panel-24` above it is 24 ga PVDF-coated STEEL. The driveway apron is
    # plowed and salted, and chloride is what separates the two metals: aluminium's oxide
    # film re-forms in it and steel's does not. Two consequences that no check can see —
    # the Z-flash at the transition must be ALUMINIUM, not steel, and the two panels must
    # never lap metal-to-metal (sealant/EPDM separation, the aluminium's leg behind).
    #
    # No `finish` key, deliberately: a new one costs ~5 hand-kept renderer registrations
    # (materials.ts, palette.ts, gltf/palette.py, draw/palette.py, DetailCanvas.tsx), each
    # of which falls through SILENTLY if missed — the board-batten-24 precedent. An authored
    # `color` needs none of them: it reaches both renderers through the material catalog
    # (`authored_colors` in emit/gltf/palette.py, `materialColor` in ui/src/nordic/palette.ts),
    # which is what makes the colourway a one-word swap where a `finish` would not be.
    #
    # BLACK, THE WINDOW TRIM'S #1c1f24, SINCE 2026-09-23 (owner): the house's one exterior
    # dark. Order it as Western States "Matte Black" (SR 4.1%). It was "Charcoal Gray"
    # #383838 (SR 28.1%) from 2026-09-02; before that it was #1c1f24 too. That value renders
    # near-black in the viewer (NeutralToneMapping's black-point offset crushes it), which
    # is the point now. The tag stays: it names the METAL, and aluminium on the Z is what
    # keeps it off the steel panel.
    #
    # No `skin_family`: that field is the wall/roof continuous-skin reading at a
    # zero-overhang edge, and a base band is not skin (the `metal-copper-penny` reasoning
    # below). No `exposed_fastener`: the sheet is hung on hems and concealed cleats with
    # only a perimeter fixing, so the screws belong inside the $/SF rate — the same call
    # `board-batten-24` makes, and the flag is the double-billing guard, not a description.
    # Not named "*seam*": both renderers key the ribbed standing-seam finish off that
    # substring and this is flat brake-formed sheet.
    Material(tag="aluminum-flat-pvdf",
             name="PVDF-painted aluminium flat sheet (0.040-0.050\")",
             r_per_inch=0.0, density=2700.0, vapor_permeance_perms=0.0, hatch="metal",
             color="#1c1f24",
             source="garage ICF stem exterior protection band (all four walls) + the stem-top Z-flash at the corrugated panel base; 3105-H14 or 5005 painted aluminium flat sheet, 2-coat 70% PVDF in Matte Black (Kynar 500/Hylar 5000), 0.040\" min / 0.050\" preferred, stock 48\" x 120\" ripped into two 24\" bands with no waste (second best if sheet is unobtainable: 0.024\" heavy-gauge 24\" trim coil, never 0.019\"); fixed with #9 316 stainless gasketed screws (EPDM washer is the dielectric break) into KDAT furring, every exposed edge hemmed or folded; NEVER in contact with concrete or fresh mortar (alkali strips the oxide film) and never lapped metal-to-metal against the steel corrugated panel above"),
    # The basement's exposed-XPS band (`_PROTECTION_PANEL`), black to match the window trim
    # (owner, 2026-09-23). The library's `foundation-coating-acrylic` is the same product in
    # stock grey; a tag cannot be shadowed, so the colourway is its own house tag. Every
    # other property is the library row's, so the condensation verdict does not move.
    # ** HEAT OVER FOAM: ** a black skin in sun runs far hotter than grey, and XPS softens
    # near 165 F. Confirm the coating maker's LRV floor over XPS before ordering.
    Material(tag="foundation-coating-acrylic-black",
             name="Trowel-applied acrylic foundation coating over mesh (1/8\"), black",
             r_per_inch=0.0, density=1400.0, vapor_permeance_perms=5.0, coating=True,
             hatch="concrete", color="#1c1f24",
             source="basement exposed-XPS band, 6\" below grade to wall top; acrylic foundation coating over mesh (Tuff II class), finished black to match the window trim; confirm the black colourway and the maker's minimum LRV over foam before ordering"),
    # `metal-copper-penny` — the garage's accent coil from 2026-08-26 to 2026-09-08, carrying
    # both the vented ridge cap and all six fascia pieces. **Referenced by nothing now.** The
    # garage roof edge went to `metal-dark-exterior` above, so the garage no longer departs
    # from the house's ONE exterior dark, and the accent that made it its own building is now
    # the Classic Green door wall alone (the stem band went black 2026-09-23).
    #
    # Kept, unreferenced, the way `metal-fascia-regal-blue` below is: a metallic PVDF is the
    # same product on the same substrate as a solid colour, so coming back is a one-word
    # `material=` swap — but in TWO places, the `FasciaBoard` in `_GARAGE_EAVE_TRIM` and
    # `Roof.edge_trim_material` on RF-GARAGE, which is the whole trap. A cap in a different
    # colour from the fascia under it reads as a mistake rather than as a choice, and no
    # check catches the drift.
    #
    # THE FASCIA'S SUBSTRATE CHANGED WITH THIS COLOUR AND MUST NOT BE REVERTED WITH IT.
    # The weather face was 5/4 cellular PVC; a dark trim colour on cellular PVC is the
    # classic failure — PVC's thermal movement is high enough that trim makers require a
    # solar-reflective vinyl-safe coating for dark colours and cap the LRV outright, and the
    # near-black it wears now is further past that cap than the metallic was. Formed metal
    # over the existing 2x6 spf sub-fascia nailer has neither problem and is the ordinary
    # detail on a metal-roofed building. The SOFFIT stays cellular PVC: it is vented, out of
    # the weather, and white under an overhang is what keeps a soffit from reading as a
    # shadow.
    #
    # Both renderers reach this tone BY TAG (`_FINISH_BASE` in emit/gltf/palette.py,
    # `FINISH_BASE` in ui/src/nordic/palette.ts, kept in step by hand), not by a declared
    # `finish`: a fascia and a ridge cap are framed MEMBERS, and `memberColor` is handed the
    # palette and no catalog, so a material's authored `color` never reaches them. Those rows
    # stay while this material does. Not named "*seam*" — renderers key the ribbed
    # standing-seam finish off that substring and this is flat formed trim.
    #
    # A metallic PVDF is a two-coat mica/pearl system, so it reads differently by viewing
    # angle in a way a flat albedo cannot express — this hex is the mid-tone of that range.
    Material(tag="metal-copper-penny", name="Copper Penny PVDF-coated formed metal trim",
             r_per_inch=0.0, density=7850.0, perm_rating=0.0, hatch="metal",
             color="#8a4f2a",
             source="garage vented ridge cap + eave/rake fascia, 2026-08-26 to 2026-09-08 only — \"Copper Penny\" PVDF/Kynar metallic (mica) coil over 24 ga. steel, the standard trade colour for a copper look without copper's cost or its runoff staining; brake-formed, and on the fascia lapped over a 2x6 spf sub-fascia nailer. A metallic is angle-dependent and this hex is the mid-tone, so a physical chip governs"),
    # `metal-fascia-regal-blue` — Western States "Regal Blue"
    # (westernstatesmetalroofing.com/regal-blue), PVDF. **Referenced by nothing**: the garage
    # fascia wore it before going to the copper penny above.
    # Kept the way `glazed-green-brick` and `standing-seam-nailstrip-26-green` are kept — a
    # solid-colour PVDF is the same product on the same substrate as the metallic, so going
    # blue again is a one-word `material=` swap on the FasciaBoard rather than a
    # re-derivation. The substrate argument above is what must NOT be reverted with it.
    Material(tag="metal-fascia-regal-blue", name="Regal Blue PVDF-coated formed metal fascia",
             r_per_inch=0.0, density=7850.0, perm_rating=0.0, hatch="metal",
             color="#1e3a5c",
             source="garage eave + rake fascia weather face, 2026-08-26 only — Western States Metal Roofing \"Regal Blue\", PVDF/Kynar over 24 ga. steel; the manufacturer publishes no hex (its own page warns the on-screen swatch differs from the panel), so this value is an approximation and a physical chip governs"),
    # RM-M-BATH2's shower back: the 36" pan's two closed sides, WP-M-BATH2-SURR.
    #
    # **Not `pvc-panel`.** That tag is RM-S-PLANT's Trusscore liner and is priced over 445.8
    # SF; folding 47 SF of a different product into it would make both unseparable and would
    # price a bathroom surround at a greenhouse liner's rate. This is its own tag so the
    # owner's selection (see prices.toml) lands on one line.
    #
    # NO `species`, deliberately — that field is what gates `haus millwork`, and a cast
    # panel is not a board to be ripped out of stock. NO `stock_bf_per_sqft` either: unset,
    # `resolve/paneling.py` draws the band at its 1/2" default, which is this panel's actual
    # thickness. And NO vapour field, on the same reading `library/materials/` states for
    # `pvc-panel` and `fiber-cement` — a butted, adhered panel with sealed joints has no
    # published ASTM E96 number that means anything at an assembly scale, and declaring one
    # would be inventing it. It costs nothing here: the panel is in no *assembly*, only a
    # `WallPaneling`, so the Glaser walk never reaches it and it buys no new UNKNOWN.
    Material(tag="marble-look-panel",
             name="Marble-look cast shower wall panel (1/2\")",
             r_per_inch=0.0, density=1600.0, hatch="stone", color="#efece6",
             source="RM-M-BATH2 shower surround, 2026-09-02; \"marble-look\" spans cultured marble, cast solid surface and acrylic and the product family is an OPEN OWNER SELECTION — see prices.toml [wood_surfaces] for the price spread that collapses when it is made"),
    # The above-grade foundation band on BASEMENT_8/_12: a trowel-applied acrylic
    # coating over the exposed XPS, on the Styro Industries Tuff II product data
    # (styro.net / totalwall.com "Applying TUFF II Over Rigid Foam & ICF"). It is the option
    # notes/basement_to_framed_wall_detail.md named first and always has ("protect with
    # appropriate elastomeric coating or rigid metal/PVC trim per manufacturer").
    #
    # **The manufacturer's system is a lamina, not a paint job, and both halves are bought.**
    # Sticky Mesh HD over the ENTIRE foam face (the FAQ is explicit: "when coating foam, it is
    # necessary to use sticky mesh"), a 1/16" skim coat that embeds it, then a 1/16" texture
    # coat 2 hours later - 1/8" built, 80 SF per 5-gallon pail. The mesh is why the thickness
    # is authored at 1/8" and not at a paint film's mils, and it is priced with the coating in
    # one $/SF rate because no one buys the mesh separately for this.
    #
    # **The XPS is bonded, not anchored, and that is the manufacturer's own instruction** -
    # "secure the foam boards to the wall using TOTAL WALL Blue Mastic #11 Adhesive or TOTAL
    # WALL fasteners". Foam-compatible adhesive to the self-adhered waterproofing below,
    # captured by the rainscreen Z-flash above and 6" of bury at the bottom. Nothing is given
    # up against the board it replaces: that board's washered pins went into the XPS, never
    # through to concrete, so no version of this band has ever had a masonry anchor in it.
    # See prices.toml, and `what is deliberately not modelled` below.
    #
    # ** THE PERMEANCE IS A CLASS BAND, NOT A PRODUCT TEST, AND THE SOURCE SAYS SO. **
    # Styro publishes appearance, pH, wet density and chemistry and no ASTM E96 number - the
    # whole product class does not test for it. So this is authored the way `latex-paint` is
    # (library/materials/): a midpoint of a published band, quoted as a band. What makes
    # that honest HERE and dishonest for the protection board below is the joint. A butted
    # board's installed permeance is dominated by its unsealed seams and no band describes
    # it; a mesh-reinforced trowel lamina is monolithic and seamless by construction, which
    # is precisely the condition the published stucco/coating rows measure.
    #
    # **And the verdict does not turn on where in the band the number lands.** Swept 2.0 /
    # 3.0 / 5.0 / 10.0 perms, the January gate PASSes at every value and the tightest plane
    # stays `xps-b`: 40, 56, 69 and 100 Pa below saturation on _8 (48 / 62 / 73 / 102 on
    # _12). The coating is nowhere near the control layer — 4" of XPS at ~0.28 perms is —
    # so the band's WIDTH is what had to be defensible, not its midpoint. That is the whole
    # reason a class band is admissible here and a made-up product figure would not be.
    #
    # ``vapor_permeance_perms`` and NOT ``perm_rating``: ``Material.vapor_permeance_at``
    # divides a perm_rating by thickness, and at 1/8" that would invent a number no test
    # measured. ``perm_rating=0.0`` is worse than useless - it is inert, reads as "not
    # authored", and this is the opposite of a barrier.
    # **UNREFERENCED since 2026-09-04. The named alternate**, on the `glazed-green-brick`
    # convention: an aluminium-faced 1/2" rigid protection board, the other half of the
    # detail note's "rigid metal/PVC trim", fastened into the XPS with washered pins. Its
    # price row is kept live in prices.toml for the same reason. Going back to it is one
    # `material_ref`/`thickness` edit on `_PROTECTION_PANEL` above.
    #
    # ** AND IT IS WHY THE COATING WAS TAKEN. ** Both vapour fields are UNSET here, and that
    # was the finding rather than a gap - the same conclusion library/materials/ reached
    # for `pvc-panel` and `fiber-cement`. ``perm_rating=0.0`` is not usable: perm_rating is a
    # *permeability* (perms per inch), ``Material.vapor_permeance_at`` treats 0.0 there as
    # "not authored", so the field would be inert. The published ASHRAE aluminium-foil
    # permeance (0.05 perm, dry cup) is the wrong number too: it is the *facer sheet*'s
    # rating, and this is a rigid board over exterior XPS with butted, unsealed joints behind
    # trim - a butted board's installed permeance is dominated by those joints, not by its
    # face. Authoring the facer's rating as the assembly's would credit a continuous Class I
    # vapour barrier on the COLD side of a wall whose interior face is vapour-open, and the
    # Glaser walk would report dew point inside the XPS on January normals - an artifact of
    # the input. So the board reported UNKNOWN on both basement assemblies, and no
    # manufacturer in its class publishes the test that would answer it. **Choosing the
    # coating is what answers it**, because a seamless lamina is a shape a published band
    # actually describes.
    # stucco (no instance in this house), composite-deck (porch
    # floor) and aluminum-deck (balcony plank) were promoted to library/materials/
    # (CONTRIBUTING §Promotion flow); they arrive here through
    # ALL_MATERIALS above.
    # ``preservative_treated``: the paint is a finish over PT stock, which is what the name
    # has always said. It decides the COATING of any connector landing on a member wearing
    # this material (IRC R317.3.1 — copper preservative corrodes G90 zinc), and nothing else
    # reads it. The live case is BM-SG-FRW/FRE, the porch's two 3-ply KDAT 2x12 front beams:
    # sixteen derived hurricane ties land on them, and they billed as plain G90 until
    # 2026-09-12 because this assembly names the PAINT as its structure layer and the paint
    # said nothing about the wood under it.
    Material(tag="post-paint-white", name="White-painted PT lumber", r_per_inch=1.24,
             density=500.0, perm_rating=1.0, hatch="lumber", color="#f4f2ee",
             preservative_treated=True,
             source="balcony 6x6 pillars, exterior white paint; painted softwood ~1 perm-in"),
    # The two CENTRE balcony pillars only, and the species is the whole point of the tag.
    # Every Simpson cap and base in ICC-ES ESR-2604 is conditioned by §3.2.2 on wood of
    # specific gravity >= 0.50; SPF is 0.42, so while these pillars were SPF neither the
    # CCQ46SDS2.5 cap at their tops nor anything at their bases had a published value.
    # DF-L at 0.50 is the cheapest thing that fixes that, and it fixes both ends at once.
    # NOT `species=`: that field admits a material to the species-split `wood_surfaces`
    # takeoff (model/materials.py), which is a millwork road this structural post has no
    # business on. Denser and therefore slightly less insulating than the SPF it replaces,
    # which matters to nothing here — an open-air pillar is in no envelope assembly.
    Material(tag="post-df-paint-white", name="White-painted DF-L (SG 0.50)", r_per_inch=1.00,
             density=530.0, perm_rating=1.0, hatch="lumber", color="#f4f2ee",
             source="balcony centre 6x6 pillars PT-SG-BR2/BF2, exterior white paint over Douglas Fir-Larch specified at specific gravity 0.50 so the SG >= 0.50 clause is met at both ends — ESR-2604 §3.2.2 for the CCQ46SDS2.5 cap above, ESR-2105 §3.5.2 and ESR-3096 §3.2.2 for the MSTA12Z strap and L50Z angles at the base below; painted softwood ~1 perm-in"),
    # retaining-block (raised garden outer face), polycarbonate-multiwall (breezeway
    # glazing) and aluminum-extrusion (breezeway glazing trim) were promoted to
    # library/materials/ (CONTRIBUTING §Promotion flow); they arrive here
    # through ALL_MATERIALS above.
]
