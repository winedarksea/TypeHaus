"""Starter materials ported/adapted from ifcplot/assemblies.py (→ 02 migration table).

Water-vapour ratings follow the two-field split on ``Material``: ``perm_rating`` is
permeability in US perm-inch for bulk substances, ``vapor_permeance_perms`` is the
thickness-independent ASTM E96 permeance of a finished sheet. Every value below cites the
published test or manufacturer datasheet it came from, per CONTRIBUTING §3. Where the
source publishes a *range* rather than a point value, the midpoint of that published range
is used and the range is quoted in ``source`` so the reader can see the spread; nothing
here is estimated from first principles. A material with no locatable source leaves the
field unset so the Glaser walk reports UNKNOWN naming it (#32) instead of guessing.
"""

from __future__ import annotations

from typehaus.model import Material

# Recurring citations, spelled once so the per-material `source` strings stay readable.
_UAF = ("UAF Cooperative Extension EEM-00259 Table 3 (Carlson compilation, "
        "ASTM E96/C355), 'Water Vapor Permeance of Construction Materials'")
_APA = "APA/Performance Panels published ASTM E96 dry-cup panel permeance data"

STARTER_MATERIALS: tuple[Material, ...] = (
    Material(tag="spf", name="SPF framing lumber", r_per_inch=1.25, density=460.0,
             perm_rating=2.9, hatch="lumber", color="#d8c9a6",
             source=f"{_UAF}: 'Wood, sugar pine' permeability 0.4-5.4 perm-in "
                    "(the table's softwood entry); midpoint of the published range"),
    # No published permeance/permeability located for laminated strand lumber; the field is
    # deliberately unset so an assembly that puts LSL in the vapour path reports UNKNOWN.
    Material(tag="lsl", name="Laminated strand lumber", r_per_inch=1.25, density=650.0,
             hatch="lumber", color="#cbb98e",
             source="R-value per ifcplot port; no published ASTM E96 rating located, so "
                    "the vapour fields stay unset (Glaser reports UNKNOWN, never a guess)"),
    Material(tag="osb", name="OSB sheathing", r_per_inch=1.25, density=650.0,
             perm_rating=0.4, hatch="osb", color="#c9a86a",
             source=f"{_APA}: OSB 7/16\" 0.91, 15/32-1/2\" 0.70, 19/32-5/8\" 0.72, "
                    "23/32-3/4\" 0.49 perm — 0.35-0.45 perm-in across those four thicknesses"),
    Material(tag="struct-1-plywood", name="Structural 1 plywood", r_per_inch=1.25,
             density=600.0, perm_rating=0.30, hatch="osb", color="#c9a86a",
             source=f"{_APA}: 0.8 perm for 3/8\" Exterior-type plywood (species-weighted "
                    "from a 0.45-1.43 perm dry-cup series) = 0.30 perm-in"),
    # ZIP-R is a bonded WRB/OSB/polyiso/facer sandwich, not a depth of one substance, so its
    # rating is authored as a panel permeance.
    Material(tag="zip-r", name="ZIP System R-sheathing", r_per_inch=4.0,
             vapor_permeance_perms=0.95, hatch="osb", color="#3f6d3a",
             source="Huber ZIP System R-sheathing published ASTM E96 Procedure B (wet cup) "
                    "assembly permeance 0.8-1.1 perm; midpoint of the published range"),
    Material(tag="polyiso", name="Polyisocyanurate CI", r_per_inch=5.6, perm_rating=1.0,
             hatch="rigid", color="#e8d64f",
             source=f"{_UAF}: 'Expanded polyurethane, R-11, board stock' 0.4-1.6 perm-in; "
                    "midpoint of the published range"),
    Material(tag="fiberglass", name="Fiberglass batt", r_per_inch=3.7, perm_rating=116.0,
             hatch="batt", color="#f3c6d0",
             source="AHFC Alaska Building Manual Appendix 2: 100 mm (4 in.) glass fibre "
                    "wool 28.97 perm = 116 perm-in"),
    Material(tag="mineral-wool", name="Mineral wool batt", r_per_inch=4.2,
             perm_rating=116.0, hatch="batt", color="#c7c2bd",
             source=f"{_UAF}: 'Mineral wool, unprotected' 116 perm-in; AHFC Appendix 2 "
                    "gives 28.97 perm at 100 mm (4 in.), the same 116 perm-in"),
    Material(tag="gwb", name="5/8\" gypsum board", r_per_inch=0.9, perm_rating=18.8,
             gypsum_type="regular", hatch="gypsum", color="#efeae2",
             source=f"{_UAF}: 'Gypsum wall board, plain' 50 perm at 0.375\" = 18.8 perm-in "
                    "(≈30 perm at 5/8\", consistent with USG's 34.2 perm at 1/2\")"),
    # Type X differs from regular board in its glass-fibre core, not in any property this
    # engine calculates with — same R per inch, same permeance. It exists as a separate
    # material precisely so an assembly can *say* which board it uses, which is the whole
    # question R302.6 asks about a garage ceiling with habitable space over it.
    Material(tag="gwb-x", name="5/8\" Type X gypsum board", r_per_inch=0.9,
             perm_rating=18.8, gypsum_type="type-x", hatch="gypsum", color="#efeae2",
             source="thermal and vapour properties as 'gwb' above; the Type X core changes "
                    "fire performance, not conductivity or permeance"),
    # A hat channel is a spaced 25 ga. section, not a continuous metal skin: vapour crosses
    # the still-air space between channels, so the layer is rated as that air space.
    Material(tag="resilient-channel", name="1/2\" resilient channel", r_per_inch=0.0,
             density=7850.0, perm_rating=120.0, hatch="metal", color="#91979d",
             source=f"{_UAF}: 'Air, still' 120 perm-in — the vapour path through a spaced "
                    "hat channel is the air between the channels, not the steel"),
    Material(tag="air-barrier", name="Air/weather-resistive barrier", r_per_inch=0.0,
             vapor_permeance_perms=54.0, hatch="membrane", color="#4a4a4a",
             source="DuPont Tyvek HomeWrap physical-properties data sheet: 54 perm by "
                    "ASTM E96-05 Method B (56 perm Method A) — a sheet rating, not perm-in"),
    # No published ASTM E96 rating located for modern fibre-cement lap siding; the closest
    # published entry is asbestos-cement board, a different binder/fibre system, so the
    # field is left unset rather than substituted.
    Material(tag="fiber-cement", name="Fiber-cement lap siding", r_per_inch=0.15,
             density=1700.0, hatch="siding", color="#b8bcc0",
             source="no published ASTM E96 rating located for fibre-cement lap siding; "
                    "vapour fields unset so the Glaser walk reports UNKNOWN"),
    # Light-gauge steel framing (25 ga. C-stud). Like the resilient channel above it is a
    # spaced section, not a skin, so the vapour path through the layer is the still air
    # between studs — the same 120 perm-in the channel carries, and for the same reason.
    # R per inch is zero: a steel stud is a thermal bridge, not an insulator, and stating
    # any positive number here would credit the wall for the worst part of it.
    Material(tag="steel-stud", name="25 ga. steel C-stud", r_per_inch=0.0,
             density=7850.0, perm_rating=120.0, hatch="metal", color="#91979d",
             source=f"{_UAF}: 'Air, still' 120 perm-in — the vapour path through a spaced "
                    "metal section is the air between the sections, not the steel"),
    Material(tag="standing-seam", name="Standing-seam steel", r_per_inch=0.0,
             density=7800.0, vapor_permeance_perms=0.0, hatch="metal", color="#6b7076",
             source=f"{_UAF}: metal foil at 0.001\" reads 0 perm; continuous sheet steel is "
                    "vapour-impermeable. Normally installed over a vented rainscreen, which "
                    "truncates the Glaser walk before it"),
    # The vent strip that closes a rainscreen cavity's base: a corrugated polypropylene
    # section whose flutes run *across* the cavity, so the cavity keeps draining and
    # venting while nothing insect-sized gets in. It is a spaced section, not a skin — the
    # vapour path through it is the open air in its flutes, exactly like the resilient
    # channel above.
    Material(tag="corrugated-vent-strip", name="Corrugated rainscreen vent/insect strip",
             r_per_inch=0.0, density=910.0, perm_rating=120.0, hatch="rigid",
             color="#3c4045",
             source=f"{_UAF}: 'Air, still' 120 perm-in — the vapour path through a "
                    "corrugated vent strip is the open flute, not the polypropylene; "
                    "density is the published bulk density of polypropylene. No ASTM E96 "
                    "test is published for the strip itself"),
    Material(tag="concrete", name="Cast-in-place concrete", r_per_inch=0.08,
             density=2400.0, perm_rating=3.2, hatch="concrete", color="#a9a9a9",
             source=f"{_UAF}: 'Concrete, 1:2:4 mix' 3.2 perm-in (1.25 perm at 4\")"),
    Material(tag="icf-eps", name="ICF EPS form", r_per_inch=4.0, perm_rating=3.9,
             hatch="rigid", color="#f0f0e6",
             source=f"{_UAF}: 'Expanded polystyrene, bead' 2.0-5.8 perm-in; midpoint of "
                    "the published range"),
    Material(tag="plywood-subfloor", name="3/4\" plywood subfloor", r_per_inch=1.25,
             density=600.0, perm_rating=0.30, hatch="osb", color="#c9a86a",
             source=f"{_APA}: 0.8 perm for 3/8\" Exterior-type plywood = 0.30 perm-in"),
    Material(tag="eps", name="EPS rigid insulation", r_per_inch=4.0, perm_rating=3.9,
             hatch="rigid", color="#eef0f2",
             source=f"{_UAF}: 'Expanded polystyrene, bead' 2.0-5.8 perm-in (midpoint); "
                    "Type II datasheets publish 5.0 perm at 1\", inside that band"),
    Material(tag="xps", name="XPS rigid insulation", r_per_inch=5.0, perm_rating=1.2,
             hatch="rigid", color="#f2b8c6",
             source=f"{_UAF}: 'Expanded polystyrene, extruded' 1.2 perm-in; Owens Corning "
                    "FOAMULAR publishes 1.1 perm max at 1\" by ASTM E96"),
    Material(tag="cedar-tg", name="Cedar T&G paneling", r_per_inch=1.0, perm_rating=2.9,
             hatch="lumber", color="#c98d5f",
             source=f"{_UAF}: 'Wood, sugar pine' permeability 0.4-5.4 perm-in (the table's "
                    "softwood entry); midpoint of the published range"),

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
    Material(tag="latex-paint", name="Interior latex paint (primer + 2 coats)",
             r_per_inch=0.0, vapor_permeance_perms=5.0, color="#f0ede6",
             finish="matte-latex", coating=True,
             source="IRC R702.7.1 vapour-retarder classes: Class III is 1.0-10 perm by ASTM "
                    "E96 dry cup, and R702.7 names latex paint over gypsum board as the "
                    "canonical Class III retarder. Published permeances for a two-coat latex "
                    "film on gypsum spread over roughly 3-10 perm with coats and sheen; 5.0 "
                    "is a mid-band value biased to the tight end of that spread, quoted as a "
                    "band midpoint rather than as a single published test result"),

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
    Material(tag="oak", name="3/4\" white-oak strip flooring", hatch="lumber", color="#c69c6d",
             species="oak",
             source="finish covering, not an assembly layer: thermal/vapour fields unset "
                    "(no published rating located, and nothing consumes them here)"),
    Material(tag="lvp", name="Luxury vinyl plank, click-lock", hatch="lumber", color="#a08a72",
             source="finish covering over its own underlayment; thermal/vapour fields unset "
                    "for the same reason as the other floor finishes"),
    Material(tag="lvp-underlayment", name="LVP acoustic underlayment", hatch="membrane",
             color="#d8d3c8",
             source="companion layer under `lvp` — carried so a takeoff can order it with "
                    "the plank rather than leaving it off the schedule"),
    Material(tag="carpet", name="Cut-pile carpet", hatch="batt", color="#9c8f80",
             source="finish covering, not an assembly layer; thermal/vapour fields unset"),
    Material(tag="carpet-pad", name="Bonded-urethane carpet pad", hatch="batt",
             color="#c8b7a0",
             source="companion layer under `carpet` — carried so a takeoff can order it with "
                    "the carpet rather than leaving it off the schedule"),
    Material(tag="tile", name="Porcelain floor tile", hatch="masonry", color="#dfe3e5",
             source="finish covering, not an assembly layer; thermal/vapour fields unset"),
    Material(tag="sealed-concrete", name="Sealed concrete slab finish", hatch="concrete",
             color="#b3b1ad", coating=True,
             source="a sealer on the slab rather than a covering over it — it adds no "
                    "thickness, so it is billed by area and carries no thermal fields"),
    Material(tag="rubber", name="Rolled rubber athletic flooring", hatch="membrane",
             color="#54585c",
             source="finish covering, not an assembly layer; thermal/vapour fields unset"),
)
