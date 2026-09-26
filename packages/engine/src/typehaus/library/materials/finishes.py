"""Interior linings, coatings and floor finishes."""

from __future__ import annotations

from typehaus.library.materials._common import _UAF
from typehaus.model import Material

MATERIALS: tuple[Material, ...] = (
    Material(
        tag="gwb",
        name='5/8" gypsum board',
        r_per_inch=0.9,
        perm_rating=18.8,
        gypsum_type="regular",
        hatch="gypsum",
        color="#efeae2",
        source=f"{_UAF}: 'Gypsum wall board, plain' 50 perm at 0.375\" = 18.8 perm-in "
        '(≈30 perm at 5/8", consistent with USG\'s 34.2 perm at 1/2")',
    ),
    # Type X differs from regular board in its glass-fibre core, not in any property this
    # engine calculates with — same R per inch, same permeance. It exists as a separate
    # material precisely so an assembly can *say* which board it uses, which is the whole
    # question R302.6 asks about a garage ceiling with habitable space over it.
    Material(
        tag="gwb-x",
        name='5/8" Type X gypsum board',
        r_per_inch=0.9,
        perm_rating=18.8,
        gypsum_type="type-x",
        hatch="gypsum",
        color="#efeae2",
        source="thermal and vapour properties as 'gwb' above; the Type X core changes "
        "fire performance, not conductivity or permeance",
    ),
    # A hat channel is a spaced 25 ga. section, not a continuous metal skin: vapour crosses
    # the still-air space between channels, so the layer is rated as that air space.
    Material(
        tag="resilient-channel",
        name='1/2" resilient channel',
        r_per_inch=0.0,
        density=7850.0,
        perm_rating=120.0,
        hatch="metal",
        color="#91979d",
        source=f"{_UAF}: 'Air, still' 120 perm-in — the vapour path through a spaced "
        "hat channel is the air between the channels, not the steel",
    ),
    # --- interior paint ---------------------------------------------------------------------
    #
    # Latex paint on gypsum board is not decoration the model can skip: IRC R702.7 counts it as
    # the assembly's warm-side vapour retarder, and R702.7.1 puts it in Class III. Leaving it
    # out models every painted wall as bare gypsum (~30 perms at 5/8"), which is a wall with no
    # vapour retarder at all — a different wall from the one that gets built.
    #
    # The rating is authored as a *permeance*, not a permeability, for the same reason housewrap
    # and foil facers are: what ASTM E96 measures here is a finished two-coat film, not a depth
    # of substance. Dividing a film rating by the 0.01" the layer carries would report 500 perms
    # and invent a number no test measured. ``coating=True`` says the rest out loud — this is a
    # covering with no plane of its own, billed by coverage area, and the renderers must not
    # draw it as a second wall face.
    Material(
        tag="latex-paint",
        name="Interior latex paint (primer + 2 coats)",
        r_per_inch=0.0,
        vapor_permeance_perms=5.0,
        color="#f0ede6",
        finish="matte-latex",
        coating=True,
        source="IRC R702.7.1 vapour-retarder classes: Class III is 1.0-10 perm by ASTM "
        "E96 dry cup, and R702.7 names latex paint over gypsum board as the "
        "canonical Class III retarder. Published permeances for a two-coat latex "
        "film on gypsum spread over roughly 3-10 perm with coats and sheen; 5.0 "
        "is a mid-band value biased to the tight end of that spread, quoted as a "
        "band midpoint rather than as a single published test result",
    ),
    # A board that is taped and primed but not finished. Authoring it is what says so: an
    # exposed gypsum face with no coating is billed paint by ``takeoff/derived_paint.py``.
    # No vapour fields: nobody has sourced one coat's permeance, so a conditioned assembly
    # carrying it grades UNKNOWN rather than on an invented number.
    Material(
        tag="gwb-primer",
        name="Drywall primer (1 coat)",
        r_per_inch=0.0,
        color="#efeae2",
        coating=True,
        source="one coat of drywall primer over taped gypsum board; a coating, so it "
        "adds no plane of its own and bills by area",
    ),
    # --- mineral silicate coatings -----------------------------------------------------------
    #
    # An untinted white potassium-silicate ("mineral") wash, for bare mineral substrates that
    # want a high diffuse reflectance: a light well whose job is to bounce daylight into the
    # rooms that look at it, and a retaining wall meant to throw light back onto a lawn.
    #
    # ** IT IS A COATING, NOT A COVERING, AND ALSO NOT A SEALER. ** ``coating=True`` says the
    # first half — no measurable thickness, billed by coverage area with no waste allowance.
    # The second half is what separates it from the silane/siloxane repellent it REPLACES on
    # this house's exposed pours: a silane makes concrete hydrophobic and non-absorbent, which
    # is precisely the one condition a potassium silicate cannot bond to. The two are
    # alternatives, never a stack, and a wash is itself vapour-open weather protection.
    #
    # ** THE PERMEANCE IS A PUBLISHED ASTM E96 FIGURE, AND IT IS AUTHORED AS A PERMEANCE. **
    # ``vapor_permeance_perms`` for `latex-paint`'s reason: what is rated here is a finished
    # two-coat film, and dividing a film rating by the 1/16" a layer carries would invent a
    # number no test measured. The value is 80.0 — the midpoint of the **75-85 perms** the
    # Beeckosil and Beecko-SOL technical data sheets publish by ASTM E96 — which is this file's
    # own convention (see the module docstring): the published test, at its range midpoint.
    #
    # ** IT WAS NEARLY AUTHORED AS A CONVERTED CLASS THRESHOLD, AND THE CROSS-CHECK IS WHY THAT
    # WOULD HAVE BEEN WRONG BY 3x. ** EN 1062-1 class **V1** ("high") is s_d < 0.14 m, and that
    # threshold converts to only ~25 perms:
    #
    #     W = delta_air / s_d = 2e-10 kg/(m.s.Pa) / 0.14 m = 1.43e-9 kg/(m^2.s.Pa),
    #     and at 1 US perm = 5.72e-11 kg/(m^2.s.Pa) that is  W ~ 25 perms.
    #
    # 25 is the FLOOR of the class, not this product. Both TDS in fact give s_d 0.01-0.02 m
    # (ISO 7783-2) — an order below the class limit — so the real film sits far inside V1 rather
    # than at its edge. Those two published numbers do NOT reconcile with each other (s_d
    # 0.01-0.02 m would compute to ~175-350 perms against an ASTM E96 75-85), because they are
    # different methods and cup conditions; that discrepancy is recorded in ``source`` rather
    # than averaged away, and the ASTM figure is the one authored because it is the test this
    # field's unit is defined by. For scale: this now becomes the most vapour-open entry in the
    # library — `air-barrier` is 54 perms and `latex-paint` is 5.0 — which is the correct
    # ordering for a non-film-forming mineral coating.
    #
    # ** NO ControlLayer.VAPOR ON ANY LAYER THAT USES THIS. ** It is the opposite of a
    # retarder, and `_PAINT_FINISH`'s Class III film is the reason that needs saying out loud.
    #
    # ** THE TAG AVOIDS THREE SUBSTRING MATCHERS ON PURPOSE. ** `mineral` maps to the BATT
    # family in `emit/draw/palette.py::_FAMILY_NEEDLES` and `ui/src/nordic/palette.ts`, so
    # "mineral-silicate-wash" would hatch and colour as mineral wool; `limewash`/`whitewash`
    # are matched by `_is_white_brick` / `isWhiteBrickRef` and would hand it brick COURSING.
    # The declared `finish` is what carries appearance here, which is why the tag does not
    # have to.
    Material(
        tag="silicate-wash-white",
        name="Mineral silicate wash, untinted white (2 coats)",
        r_per_inch=0.0,
        vapor_permeance_perms=80.0,
        color="#e9e6df",
        finish="silicate-wash",
        hatch="concrete",
        coating=True,
        source="untinted white mineral silicate (potassium-silicate) wash, 2 coats, on raw "
        "absorbent mineral substrate. Product of record BEECK Beeckosil C-102 White: "
        "LRV 90 (Beeck colour page, 'Bright White'; C-101 Off-White is LRV 60 for "
        "comparison), single-component silicate paint manufactured to VOB/C DIN 18363 "
        "group 2.4.1 on pure potassium water glass, non-film-forming, bonds by "
        "silicification with free lime in the substrate, inorganic pigments only "
        "(colourfastness A1, BFS 26), 'extreme flat mineral matte finish' and dull "
        "matte at 85 deg per EN ISO 2813. Coverage 200-275 sf/gal/coat on CMU, poured "
        "and cast concrete of average texture, 150-200 on split-face or heavily "
        "textured masonry (Beeck product page; the TDS's own headline 300-350 is for "
        "SMOOTH normally-absorbent substrate and does not describe as-cast or SRW). NO "
        "PRIMER on a raw mineral substrate, which is the binding constraint on this "
        "material and the reason the silane/siloxane repellent it replaces cannot "
        "coexist with it; previously painted or non-absorbent surfaces need a BEECK "
        "Bonding Coat, highly absorbent ones a Fixative thin. VAPOUR: authored as the "
        "PUBLISHED ASTM E96 permeance, 75-85 perms, midpoint 80.0, per the Beeckosil "
        "and Beecko-SOL TDS - the library convention (see this file's header) is the "
        "published test at its range midpoint, so this supersedes a conversion. "
        "Cross-check, and the reason the number is credible rather than merely quoted: "
        "both TDS give s_d 0.01-0.02 m (ISO 7783-2) and EN 1062-1 class V1 'high' is "
        "s_d < 0.14 m, whose threshold converts to only ~25 perms (W = delta_air/s_d = "
        "2e-10/0.14 = 1.43e-9 kg/(m2.s.Pa), at 1 US perm = 5.72e-11) - so 80 perms sits"
        " far INSIDE the class this product family markets into rather than at its "
        "floor. The two figures do not reconcile exactly (s_d 0.01-0.02 m would compute"
        " to ~175-350 perms) because they are different methods and cup conditions; the"
        " ASTM number is the one authored because it is the test this field's unit is "
        "defined by. Either way the material is vapour-OPEN and must never carry "
        "ControlLayer.VAPOR. Alternates considered: Romabio Masonry Flat (D-SILICATE "
        "modified with an organic dispersion, NOT unmodified 2.4.1, and MicroGrip "
        "primer is REQUIRED on concrete and concrete block, so it does not clear the "
        "no-primer constraint; no LRV published). COLOUR IS DERIVED, NOT PUBLISHED: no "
        "measured sRGB or spectral value exists for any of these whites. LRV 90 is "
        "Y=0.90 = #f3f3f3 as an ideal full-hiding chip; a photographed two-coat white "
        "silicate over as-cast grey loses 5-15% to mottle, thin-spot substrate bleed "
        "and matte micro-shadowing, landing near #ebe8e1 and reading very slightly "
        "warm. #e9e6df is authored UNDER that, per houses/catlin/CLAUDE.md's rule that "
        "the viewer's ambient lifts an albedo, and is deliberately the same hex as "
        "WHITE_BRICK_STYLE's base - this house already tuned that value for a "
        "whitewashed masonry face in this renderer",
    ),
    # The SAME PRODUCT on dry-stacked segmental retaining block, split off solely so the
    # renderers can tell the two apart. A silicate wash is a thin, slightly translucent film:
    # over as-cast concrete it reads as one flat chalky plane, and over SRW units it does NOT
    # — the open dry-stacked joints and the unit module telegraph straight through it. That is
    # an appearance difference between two faces of one order, and `Material.finish` is the
    # field that declares appearance, so it takes two tags rather than one.
    #
    # The tag carries "block" deliberately: `family_of` reads it as MASONRY, which is the gate
    # `ui/src/three/builders/walls.ts` gives the coursing path (`isMasonry`). Everything else
    # is identical to `silicate-wash-white` above, INCLUDING the price — one pail, one crew,
    # one rate over both substrates; see prices.toml [envelope_layers].
    Material(
        tag="silicate-wash-white-block",
        name="Mineral silicate wash, untinted white (2 coats) on SRW block",
        r_per_inch=0.0,
        vapor_permeance_perms=80.0,
        color="#e9e6df",
        finish="silicate-wash-block",
        hatch="concrete",
        coating=True,
        source="untinted white mineral silicate (potassium-silicate) wash, 2 coats, on raw "
        "absorbent mineral substrate. Product of record BEECK Beeckosil C-102 White: "
        "LRV 90 (Beeck colour page, 'Bright White'; C-101 Off-White is LRV 60 for "
        "comparison), single-component silicate paint manufactured to VOB/C DIN 18363 "
        "group 2.4.1 on pure potassium water glass, non-film-forming, bonds by "
        "silicification with free lime in the substrate, inorganic pigments only "
        "(colourfastness A1, BFS 26), 'extreme flat mineral matte finish' and dull "
        "matte at 85 deg per EN ISO 2813. Coverage 200-275 sf/gal/coat on CMU, poured "
        "and cast concrete of average texture, 150-200 on split-face or heavily "
        "textured masonry (Beeck product page; the TDS's own headline 300-350 is for "
        "SMOOTH normally-absorbent substrate and does not describe as-cast or SRW). NO "
        "PRIMER on a raw mineral substrate, which is the binding constraint on this "
        "material and the reason the silane/siloxane repellent it replaces cannot "
        "coexist with it; previously painted or non-absorbent surfaces need a BEECK "
        "Bonding Coat, highly absorbent ones a Fixative thin. VAPOUR: authored as the "
        "PUBLISHED ASTM E96 permeance, 75-85 perms, midpoint 80.0, per the Beeckosil "
        "and Beecko-SOL TDS - the library convention (see this file's header) is the "
        "published test at its range midpoint, so this supersedes a conversion. "
        "Cross-check, and the reason the number is credible rather than merely quoted: "
        "both TDS give s_d 0.01-0.02 m (ISO 7783-2) and EN 1062-1 class V1 'high' is "
        "s_d < 0.14 m, whose threshold converts to only ~25 perms (W = delta_air/s_d = "
        "2e-10/0.14 = 1.43e-9 kg/(m2.s.Pa), at 1 US perm = 5.72e-11) - so 80 perms sits"
        " far INSIDE the class this product family markets into rather than at its "
        "floor. The two figures do not reconcile exactly (s_d 0.01-0.02 m would compute"
        " to ~175-350 perms) because they are different methods and cup conditions; the"
        " ASTM number is the one authored because it is the test this field's unit is "
        "defined by. Either way the material is vapour-OPEN and must never carry "
        "ControlLayer.VAPOR. Alternates considered: Romabio Masonry Flat (D-SILICATE "
        "modified with an organic dispersion, NOT unmodified 2.4.1, and MicroGrip "
        "primer is REQUIRED on concrete and concrete block, so it does not clear the "
        "no-primer constraint; no LRV published). COLOUR IS DERIVED, NOT PUBLISHED: no "
        "measured sRGB or spectral value exists for any of these whites. LRV 90 is "
        "Y=0.90 = #f3f3f3 as an ideal full-hiding chip; a photographed two-coat white "
        "silicate over as-cast grey loses 5-15% to mottle, thin-spot substrate bleed "
        "and matte micro-shadowing, landing near #ebe8e1 and reading very slightly "
        "warm. #e9e6df is authored UNDER that, per houses/catlin/CLAUDE.md's rule that "
        "the viewer's ambient lifts an albedo, and is deliberately the same hex as "
        "WHITE_BRICK_STYLE's base - this house already tuned that value for a "
        "whitewashed masonry face in this renderer. THIS TAG IS THE SRW-BLOCK VARIANT "
        "and differs from `silicate-wash-white` in appearance only - same product, same"
        " pail, same crew, same price. It also carries the SUBSTRATE WARNING that made "
        "a separate record worth having: dry-cast integrally-coloured SRW units are far"
        " less absorbent than cast-in-place and frequently carry an INTEGRAL WATER "
        "REPELLENT, and NCMA/CMHA TEK 19-7 says of such units that 'the most important "
        "characteristic of the unit may be its compatibility with the type of coating "
        "used [...] some coatings may not be able to bridge open pores or fill all "
        "surface irregularities'. Beeckosil additionally asks for Quartz Filler or a "
        "Bonding Coat over the WHOLE face as a CMU pretreatment. The answer on this "
        "substrate is BEECK Beecko-SOL, a silica-sol modified silicate emulsion (still "
        "VOB/C DIN 18363 2.4.1, <5% organic) whose TDS claims 'perfect adhesion and "
        "silicification, even on critical, semi-water repellent and synthetic-resin "
        "coated facades' and lists partially water-repellent substrates as suitable - "
        "noting the manufacturer goes no further than SEMI-repellent, so a fully "
        "IWR-dosed unit is outside what anyone publishes. A TEST PANEL ON A SPARE BLOCK"
        " IS MANDATORY AND IS THE MANUFACTURER'S OWN INSTRUCTION ('the only way to "
        "precisely predict application rates is with a trial application'), not a "
        "precaution added here",
    ),
    # The SAME PRODUCT a third time, on laid face brick (the fireplace surround). Split off for
    # the SRW variant's reason: the brick module and its tooled joints telegraph through a
    # non-film-forming wash, so the flat concrete mottle made the surround read as a pour.
    # "brick" in the tag makes `family_of` MASONRY, which opens the coursing path.
    Material(
        tag="silicate-wash-white-brick",
        name="Mineral silicate wash, untinted white (2 coats) on face brick",
        r_per_inch=0.0,
        vapor_permeance_perms=80.0,
        color="#e9e6df",
        finish="silicate-wash-brick",
        hatch="concrete",
        coating=True,
        source="BEECK Beeckosil C-102 White, 2 coats, no primer on raw absorbent clay brick. "
        "Identical in product, vapour permeance, colour and rate to `silicate-wash-white`, "
        "whose record carries the full citation; this tag differs in appearance only",
    ),
    # --- floor finishes -------------------------------------------------------------------
    #
    # `Room.floor_finish` was a free-form string with nothing behind it: the viewer could not
    # colour it, the .glb painted every room the same flat grey, and a takeoff had nothing to
    # bill against. These are the materials those strings name, so all three surfaces key off
    # one definition — the tag *is* the finish string, which is what makes the lookup exact
    # rather than substring guesswork.
    #
    # A finish is a covering laid on a floor deck, not a layer in a rated assembly: none of
    # them appears in an `Assembly`, so the Glaser walk and the R-value rollup never see them
    # and their thermal/vapour fields stay unset rather than being filled with numbers no
    # published test measured. `color` and `hatch` are what these entries exist to carry.
    # `finish` picks the 3D board recipe: strip flooring is 2 1/4" boards with staggered butt
    # joints, not the 3 1/2" tongue-and-groove paneling the `*-tg` refs infer by default.
    # That inference is a TAG reading, so a profile change that renames the tag escapes it —
    # the sauna liner's T&G -> shiplap retag is why `sauna-shiplap` authors
    # `finish="shiplap"` outright rather than relying on it (ui/src/three/plankMaterial.ts).
    # This is a factory-sourced floor product. Its species and strip-floor recipe remain
    # useful for reporting and rendering, but it carries no rough-stock declaration: a
    # house only sends flooring to the custom mill when it opts in locally.
    Material(
        tag="oak",
        name='3/4" white-oak strip flooring',
        hatch="lumber",
        color="#c69c6d",
        species="oak",
        finish="strip-floor",
        finish_thickness_in=0.75,
        source="factory-sourced finish covering, not an assembly layer: thermal/vapour fields "
        "unset "
        "(no published rating located, and nothing consumes them here). "
        "`finish_thickness_in` is the 3/4\" this product's own name states; "
        "the rosin paper or felt slip sheet under a nailed strip floor is not "
        "a thickness",
    ),
    Material(
        tag="lvp",
        name="Luxury vinyl plank, click-lock",
        hatch="lumber",
        color="#a08a72",
        finish_thickness_in=0.2362,
        source="finish covering over its own underlayment; thermal/vapour fields unset "
        "for the same reason as the other floor finishes. "
        "`finish_thickness_in` is 6 mm nominal — the mainstream click-lock "
        "plank, 5 mm rigid core plus a 1 mm attached IXPE pad. A separate "
        "compressible acoustic mat laid under it is NOT counted: it crushes "
        "under load, so the plane underfoot stays the plank's own (the basis "
        "houses/catlin/params/main_deck.py works its flush-joint case from). "
        "A house on a thicker plank has to say so",
    ),
    Material(
        tag="lvp-underlayment",
        name="LVP acoustic underlayment",
        hatch="membrane",
        color="#d8d3c8",
        source="companion layer under `lvp` — carried so a takeoff can order it with "
        "the plank rather than leaving it off the schedule",
    ),
    Material(
        tag="carpet",
        name="Cut-pile carpet",
        hatch="batt",
        color="#9c8f80",
        finish_thickness_in=0.5,
        source="finish covering, not an assembly layer; thermal/vapour fields unset. "
        '`finish_thickness_in` is the carpet AND its pad, 1/4" of '
        'commercial-weight cut pile over a 1/4" high-density rebond cushion. '
        "The pad is the half that is a judgement: carpet-council guidance caps "
        'stair cushion at 3/8" because a thicker one rolls the nosing '
        'underfoot, and 1/4" is the safe end of that. Selected 2026-09-11 '
        "for catlin's ST-B2M and taken as the house default",
    ),
    Material(
        tag="carpet-pad",
        name="Bonded-urethane carpet pad",
        hatch="batt",
        color="#c8b7a0",
        source="companion layer under `carpet` — carried so a takeoff can order it with "
        "the carpet rather than leaving it off the schedule",
    ),
    Material(
        tag="tile",
        name="Porcelain floor tile",
        hatch="masonry",
        color="#dfe3e5",
        finish_thickness_in=0.5,
        source="finish covering, not an assembly layer; thermal/vapour fields unset. "
        "`finish_thickness_in` is the whole tray over the subfloor — tile, its "
        'thinset beds and the 1/8" uncoupling membrane under it — because a '
        "room names only the tile. 1/2\" is what catlin's own mudroom "
        'arithmetic resolves to (params/main_deck.py puts that floor ~5/16" '
        'proud of a concrete cap standing +15/16" over a +3/4" subfloor), '
        "and it is an ordinary porcelain-over-DITRA build",
    ),
    Material(
        tag="sealed-concrete",
        name="Sealed concrete slab finish",
        hatch="concrete",
        color="#b3b1ad",
        coating=True,
        source="a sealer on the slab rather than a covering over it — it adds no "
        "thickness, so it is billed by area and carries no thermal fields",
    ),
    Material(
        tag="polished-concrete",
        name="Polished concrete floor",
        hatch="concrete",
        color="#c2c0bb",
        coating=True,
        source="a mechanical grind (4-6 passes) plus densifier and guard on the cast "
        "cap itself, not a covering over it — no thickness, so no thermal or "
        "vapour fields; distinct from `sealed-concrete`, which is a roll-on "
        "sealer over a trowel finish at roughly half the rate",
    ),
    # The third way to finish a cast cap, and the one with a film on it. A polish and a
    # sealer both leave the concrete as the wearing surface; this leaves a coating as the
    # wearing surface, and that is a different set of requirements: every coating TDS found
    # (Tnemec 201, Sikafloor-1620/217, Dur-A-Flex, Sherwin-Williams) asks for ICRI CSP 2-4,
    # which is a GRIND, not a polish — a hard-troweled cream reads below CSP 2 and a hone to
    # 200 grit moves further away from profile, not toward it. ``coating=True`` and no
    # thickness, like `latex-paint`: a film has no plane of its own and is billed by
    # coverage area.
    #
    # ** THE RISK THIS FINISH CARRIES IS MOISTURE, AND NOTHING IN THE ENGINE GRADES IT. **
    # A floor_finish is not a ``Layer``, so no vapour check sees a near-vapour-tight film
    # over a cap that can only dry upward (EPS below it). Primer ceilings run 80% RH
    # (Tnemec 201) to 85% (Sikafloor-217); only a moisture-mitigating class tolerates 100%.
    # ASTM F2170 in-situ RH at 40% of depth is the gate, and it belongs in the house's own
    # note, not here. Confirm the product class against its current TDS before ordering:
    # published RH limits disagree between a manufacturer's web page and its PDS.
    Material(
        tag="coated-concrete",
        name="Coated concrete floor (2K PU over primer)",
        hatch="concrete",
        color="#bfbdb6",
        coating=True,
        finish="matte-2k-pu",
        source="a resinous floor on the cast cap itself: diamond grind to ICRI CSP "
        "2-3, a moisture-mitigating primer, and a matte two-component "
        "aliphatic polyurethane topcoat, roller-applied. No thickness, so no "
        "thermal or vapour fields; distinct from `polished-concrete`, which "
        "leaves the concrete itself as the wearing surface, and from "
        "`sealed-concrete`, which is a roll-on sealer over a trowel finish",
    ),
    Material(
        tag="rubber",
        name="Rolled rubber athletic flooring",
        hatch="membrane",
        color="#54585c",
        finish_thickness_in=0.3125,
        source="finish covering, not an assembly layer; thermal/vapour fields unset. "
        "`finish_thickness_in` is 8 mm, the stock roll thickness this class of "
        'flooring is sold in for a home gym; 3/8" and 1/2" rolls exist for '
        "free-weight platforms and a house laying one has to say so",
    ),
    # Residential luxury sheet vinyl on 12' rolls — the wet-room floor. A room no wider
    # than the roll takes one seamless sheet; the floor–wall joint is turned up as a flash
    # cove where the maker allows it (houses/catlin/notes/plant_room.md). Nothing
    # impermeable goes *under* the sheet (a second Class I layer there sandwiches the
    # subfloor with no drying path either way). No ASTM E96 number is published, and none is
    # needed: a floor finish is never a layer in a rated assembly.
    Material(
        tag="vinyl-sheet",
        name="Luxury sheet vinyl, 12' roll, glue-down",
        hatch="membrane",
        color="#f0ede7",
        finish="veined-marble",
        finish_thickness_in=0.120,
        source="finish covering, not an assembly layer; thermal/vapour fields unset. "
        "Tarkett Home First Class, Monaco Calacatta (TK1387071) or equal: 120 mil "
        "total, 16 mil urethane wear layer, 12' wide rolls, glue-down or loose-lay. "
        "A continuous white Calacatta marble print with no tile or grout lines, "
        "which the viewer draws as the `veined-marble` recipe",
    ),
)
