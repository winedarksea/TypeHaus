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
    # Laminated VENEER lumber, the sibling of ``lsl`` and a different product: rotary-peeled
    # veneers laid parallel and glued, rather than stranded flakes. It is authored here and
    # not left to the ``solid_material_ref`` fallback (which calls every non-round beam
    # "spf") because an LVL beam costs three to five times a sawn one by the foot, and a
    # takeoff that cannot tell them apart cannot price either.
    # Same discipline as ``lsl`` on vapour: no published ASTM E96 rating located, so both
    # fields stay unset and the Glaser walk names this material in an UNKNOWN.
    Material(tag="lvl", name="Laminated veneer lumber", r_per_inch=1.25, density=670.0,
             hatch="lumber", color="#c2ab7c",
             source="R-value shares the engineered-lumber value used for lsl; density is "
                    "the midpoint of the 640-720 kg/m3 (40-45 pcf) band published for "
                    "softwood LVL; no ASTM E96 rating located, so the vapour fields "
                    "stay unset (Glaser reports UNKNOWN, never a guess)"),
    # Kiln-dried-after-treatment southern yellow pine — the exterior framing species. KDAT
    # rather than plain PT is a real distinction and not a label: the treatment leaves the
    # stick soaked, and drying it *after* is what stops a deck frame shrinking, cupping and
    # backing its fasteners out over its first season. It is a separate tag from ``spf``
    # because it is a denser species, costs more by the foot, and must not be substituted
    # into an interior wall by a takeoff that only knows "lumber".
    Material(tag="kdat", name="KDAT southern yellow pine (treated exterior framing)",
             r_per_inch=0.95, density=600.0, perm_rating=2.9, hatch="lumber",
             color="#bfa06a",
             source="SYP is the densest of the framing softwoods (SG ~0.55 green vs SPF "
                    "~0.42), and R/inch falls as density rises, so it sits below the "
                    "df-select-s4s 0.99-1.06 band already authored in catlin; "
                    f"permeability shares the softwood midpoint used for spf ({_UAF})"),
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
    # Plain ZIP — OSB with a bonded WRB facer, no foam. Unlike ZIP-R it *is* a depth of one
    # substance (the facer is a film), so it carries an R per inch like the OSB it is, and
    # its rating is authored as a panel permeance because the facer, not the wood, governs.
    # The taped seams are what make it the air barrier; the panel is the vapour retarder.
    Material(tag="zip-sheathing", name="ZIP System sheathing", r_per_inch=1.25,
             density=650.0, vapor_permeance_perms=2.0, hatch="osb", color="#3f6d3a",
             source="Huber ZIP System sheathing published ASTM E96 Procedure A (dry cup) "
                    "panel permeance 2-3 perm at 7/16-1/2\"; low end of the published range"),
    Material(tag="polyiso", name="Polyisocyanurate CI", r_per_inch=5.6, perm_rating=1.0,
             hatch="rigid", color="#e8d64f", foam_plastic=True,
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
    # Closed-cell (2 lb) spray polyurethane foam — what fills a rim cavity that no sheet
    # membrane can reach. It is the insulation, the air barrier AND the vapour retarder in
    # one bonded, seamless application, which is exactly why it is specified where a floor
    # band interrupts a wall's control layers: 3" runs about 0.53 perm, a Class II retarder,
    # with no seam to fail. `resolve/construction_rim.py` bills it by the lineal foot of rim.
    Material(tag="closed-cell-spray-foam", name="Closed-cell spray polyurethane foam (2 lb)",
             r_per_inch=6.5, density=32.0, perm_rating=1.6, hatch="batt", color="#e8d9b5",
             foam_plastic=True,
             source="published ccSPF range R-5.9 to R-7.0 per inch and ASTM E96 permeance "
                    "1.2-2.0 perm at 1 in.; midpoints of the published ranges, per this "
                    "file's convention"),
    # The wet/humid-room air+vapour barrier: the layer a room run at 55-70% RH depends on,
    # and the one `building_science.humid_room_liner` keys on. Authored as a
    # **specification**, not a datasheet reading — 0.05 perm is the loosest a submitted
    # product may test at and still be IRC R702.7.1 Class I (<= 0.1 perm) with margin. That
    # is a different kind of number from the rest of this file and the `source` says so;
    # replace it with the selected product's own ASTM E96 result when one is chosen.
    #
    # It exists as a separate material from `air-barrier` (54 perm) precisely because those
    # two are opposites: one is a vapour-open weather barrier for the cold side, this is a
    # vapour-closed barrier for the warm side, and confusing them is the classic way to
    # build a wall that cannot dry in either direction.
    # Under-slab vapour retarder. There was no polyethylene in this catalog at all — the only
    # hit for the word was the radon sump basin — which is why the layer below every slab in
    # every house was simply absent, and why ``sheet.foundation.vapour_retarder`` fired
    # UNKNOWN on the permit sheet and nowhere else.
    #
    # 10 mil, Class A per ASTM E1745. The class is the specification that matters: E1745
    # grades a sheet on water-vapour transmission (0.01 perms or less after conditioning),
    # tensile strength and puncture resistance together, and Class A is the tier that
    # survives being walked on and having rebar chairs set on it. A 6-mil builder's poly is
    # the same polymer and none of the same product.
    Material(tag="polyethylene", name="Under-slab vapour retarder (10 mil, ASTM E1745 Class A)",
             r_per_inch=0.0, density=940.0, vapor_permeance_perms=0.01, hatch="membrane",
             color="#2e3d34",
             source="ASTM E1745 Class A: <=0.01 perms by ASTM E96 after the standard's "
                    "conditioning, >=45 lbf/in tensile (E154), >=2,200 g puncture (D1709). "
                    "IRC R506.2.3 requires a vapour retarder in contact with a slab's base "
                    "course; ACI 302.2R and E1745 are what specify which one"),
    # The capillary break under it: open-graded crushed stone, compacted, no fines. The
    # break is the *absence* of small pores — water cannot wick up through voids this large —
    # so "4 inches of clean stone" is the specification and a well-graded base course, which
    # compacts better, is the wrong material for the job.
    Material(tag="capillary-break-stone",
             name="Compacted open-graded stone (capillary break, #57)",
             r_per_inch=0.0, density=1600.0, hatch="concrete", color="#8f8d88",
             source="IRC R506.2.2: a 4\" base course of clean graded sand, gravel or crushed "
                    "stone passing a 2\" sieve under a slab-on-ground. #57 is the open-graded "
                    "stone ACI 302.2R names for the capillary break; the point is the absence "
                    "of fines, not the compaction"),
    Material(tag="humid-room-membrane",
             name="Self-adhered air/vapour barrier membrane (Class I)",
             r_per_inch=0.0, density=1000.0, vapor_permeance_perms=0.05, hatch="membrane",
             color="#3f4a52",
             source="specification, not a product datasheet: a fully-adhered sheet "
                    "air/vapour barrier tested to ASTM E96 desiccant method at 0.05 perm "
                    "or tighter, i.e. Class I per IRC R702.7.1 with margin"),
    # Solid PVC tongue-and-groove wall/ceiling panel (Trusscore-class): concealed screw
    # flange, mounts direct to furring, no cellulose substrate anywhere in it, third-party
    # mould-tested to ISO 846. The lining of choice for a room that is deliberately wet.
    #
    # `vapor_permeance_perms` is deliberately UNSET and that is the finding, not a gap: no
    # manufacturer in this product class — Crane, Marlite, Nudo, Trusscore, Extrutech —
    # publishes an ASTM E96 number, so an assembly using it reports UNKNOWN naming this
    # material rather than crediting a panel nobody measured as vapour control. The barrier
    # is `humid-room-membrane` above, behind it.
    #
    # Chosen over FRP, which is disqualified rather than merely worse: FRP's own published
    # product limitations require 60-75 F and 35-55% RH and forbid installing it over studs,
    # and non-compliance voids the warranty.
    Material(tag="pvc-panel", name="Solid PVC T&G wall/ceiling panel (1/2\")",
             r_per_inch=1.0, density=700.0, hatch="rigid", color="#f2f4f3",
             source="Trusscore-class 1/2\" T&G interlocking PVC panel, concealed screw "
                    "flange, ISO 846 mould-tested; no ASTM E96 permeance published in "
                    "this product class, so none is authored"),
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
             skin_family="standing-seam",
             source=f"{_UAF}: metal foil at 0.001\" reads 0 perm; continuous sheet steel is "
                    "vapour-impermeable. Normally installed over a vented rainscreen, which "
                    "truncates the Glaser walk before it"),
    # 7/8" corrugated, the third profile in the site's one white steel skin (2026-08-31),
    # and the detached garage's wall panel — GARAGE_WALL_2X6 over 5/8" CDX, replacing the
    # 26 ga. concealed nail-strip over Zip-R. A sinusoidal exposed-fastener sheet: 7/8"
    # deep on a 2-2/3" pitch, 32" net coverage, screwed through the crowns into the studs.
    #
    # `finish="corrugated"` is the whole dispatch. `isStandingSeam` (ui materials.ts) and
    # `_is_standing_seam` (emit/gltf/palette.py) are substring tests, and this tag carries
    # neither "seam" nor "standing" — so the metal treatment is reached ONLY through the
    # authored finish, exactly as `pbr-panel-26` does it. That is the documented design,
    # not a workaround; a material that says what it is beats a tag that hints at it.
    #
    # `skin_family="standing-seam"` keeps the garage's wall and its nail-strip roof reading
    # as one continuous skin at the flush roof edge (`continuous_skin_cladding`), which is
    # the one thing tag equality gets wrong about a building wearing one white in three
    # specifications. It changes no quantity and no building-science number.
    #
    # `exposed_fastener=True` is the double-billing guard: it is what lets
    # `takeoff.fasteners` bill the panel screws as a counted part instead of leaving them
    # inside a $/SF rate. Without it the screws simply vanish from the bill.
    Material(tag="corrugated-panel-26", name="7/8\" corrugated exposed-fastener steel panel, 26 ga.",
             r_per_inch=0.0, density=7800.0, vapor_permeance_perms=0.0, hatch="metal",
             color="#6b7076", finish="corrugated",
             skin_family="standing-seam", exposed_fastener=True,
             source=f"{_UAF}: continuous sheet steel is vapour-impermeable, as `standing-seam` "
                    "above. 26 ga. PVDF-coated steel, 7/8\" corrugation depth on a 2-2/3\" "
                    "pitch, 32\" net coverage, face-fastened with gasketed screws through the "
                    "crowns. TWO KNOWN APPROXIMATIONS, recorded here rather than fixed: "
                    "takeoff/hardware_config.py::ExposedFastenerCladdingRules is one frozen "
                    "dataclass with PBR geometry hard-coded (12\" rib pitch, 36\" coverage), so "
                    "the field screw count is a fair proxy but the sidelap count runs slightly "
                    "low on 36\" vs this panel's 32\"; and its support_embedment_in=1.4\" is "
                    "satisfied by no sheathing thickness at all — the rule presumes penetration "
                    "into framing, which is what these screws do"),
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
             hatch="rigid", color="#f0f0e6", foam_plastic=True,
             source=f"{_UAF}: 'Expanded polystyrene, bead' 2.0-5.8 perm-in; midpoint of "
                    "the published range"),
    Material(tag="plywood-subfloor", name="3/4\" plywood subfloor", r_per_inch=1.25,
             density=600.0, perm_rating=0.30, hatch="osb", color="#c9a86a",
             source=f"{_APA}: 0.8 perm for 3/8\" Exterior-type plywood = 0.30 perm-in"),
    Material(tag="eps", name="EPS rigid insulation", r_per_inch=4.0, perm_rating=3.9,
             hatch="rigid", color="#eef0f2", foam_plastic=True,
             source=f"{_UAF}: 'Expanded polystyrene, bead' 2.0-5.8 perm-in (midpoint); "
                    "Type II datasheets publish 5.0 perm at 1\", inside that band"),
    Material(tag="xps", name="XPS rigid insulation", r_per_inch=5.0, perm_rating=1.2,
             hatch="rigid", color="#f2b8c6", foam_plastic=True,
             source=f"{_UAF}: 'Expanded polystyrene, extruded' 1.2 perm-in; Owens Corning "
                    "FOAMULAR publishes 1.1 perm max at 1\" by ASTM E96"),
    Material(tag="cedar-tg", name="Cedar T&G paneling", r_per_inch=1.0, perm_rating=2.9,
             hatch="lumber", color="#c98d5f",
             source=f"{_UAF}: 'Wood, sugar pine' permeability 0.4-5.4 perm-in (the table's "
                    "softwood entry); midpoint of the published range"),

    # --- masonry and concrete commodities ------------------------------------------------
    Material(tag="cmu", name="Grouted CMU (8\")", r_per_inch=0.11, density=2000.0,
             perm_rating=2.5, hatch="concrete", color="#b8b3ab", finish="cmu",
             source="grouted 8 in. concrete masonry unit wythe; concrete masonry ~2-3 perm-in"),
    Material(tag="grout", name="Masonry grout", r_per_inch=0.08, density=2240.0,
             perm_rating=2.5, hatch="concrete", color="#9a958c",
             source="fills CMU cores; cementitious grout ~2-3 perm-in"),
    Material(tag="stucco", name="Portland-cement stucco", r_per_inch=0.20, density=1900.0,
             perm_rating=10.0, hatch="concrete", color="#d9d2c4",
             source="Portland-cement stucco / parge coat over mesh, a standard exterior "
                    "masonry finish"),
    Material(tag="retaining-block", name="Segmental concrete retaining-wall block",
             r_per_inch=0.08, density=2200.0, perm_rating=2.5, hatch="concrete",
             color="#a8a49c", finish="cmu",
             source="dry-stacked segmental retaining-wall (SRW) unit, no mortar"),
    Material(tag="composite-deck", name="Composite decking (capped PVC/wood)",
             r_per_inch=1.0, density=1000.0, perm_rating=0.5, hatch="lumber", color="#8a7f70",
             source="capped composite decking walking surface; PVC-capped composite "
                    "~0.5 perm-in (low)"),
    Material(tag="aluminum-deck", name="Aluminum deck board (Wahoo AridDeck-style)",
             r_per_inch=0.0, density=2700.0, perm_rating=0.05, hatch="metal", color="#b9bcc0",
             source="waterproof aluminum plank decking; metal is effectively "
                    "vapor-impermeable"),
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
             source="SABIC LEXAN THERMOCLEAR multiwall declaration EN 16153:2013+A1:2015 "
                    "https://ff.sabic.eu/uploads/resources/DoP%20LT2UV329X38%20-%202023.pdf"),
    # Mill-finish extruded aluminium: U/H/F channels, glazing bars, panel fasteners' washers.
    # "alum" matches no needle in the family inference at all, so this colour is authored
    # for the same reason the polycarbonate's is.
    Material(tag="aluminum-extrusion", name="Extruded aluminium glazing bar / channel",
             r_per_inch=0.0007, density=2700.0, perm_rating=0.0, hatch="metal",
             color="#b6bac0",
             source="mill-finish 6063-T5 extruded aluminium glazing trim"),

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
    # `finish` picks the 3D board recipe: strip flooring is 2 1/4" boards with staggered butt
    # joints, not the 3 1/2" tongue-and-groove paneling the `*-tg` refs infer by default.
    # That inference is a TAG reading, so a profile change that renames the tag escapes it —
    # the sauna liner's 2026-08-28 T&G -> shiplap retag is why `sauna-shiplap` authors
    # `finish="shiplap"` outright rather than relying on it (ui/src/three/plankMaterial.ts).
    # `stock_bf_per_sqft` 1.0: 3/4" finished strip flooring is 4/4 stock, so a square foot
    # of floor is a board foot of order. It was unset until 2026-08-28, which is why the
    # oak floor was the one `wood_surfaces` row printing no board feet at all — the section
    # omits the column rather than inventing a thickness (#32), and here the thickness was
    # never in doubt. `milling_profile` is T&G because strip flooring is: the tongue is face
    # width the mill saws and the floor never sees.
    Material(tag="oak", name="3/4\" white-oak strip flooring", hatch="lumber", color="#c69c6d",
             species="oak", finish="strip-floor", stock_bf_per_sqft=1.0,
             nominal_quarters=4, milling_profile="T&G",
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
    Material(tag="polished-concrete", name="Polished concrete floor", hatch="concrete",
             color="#c2c0bb", coating=True,
             source="a mechanical grind (4-6 passes) plus densifier and guard on the cast "
                    "cap itself, not a covering over it — no thickness, so no thermal or "
                    "vapour fields; distinct from `sealed-concrete`, which is a roll-on "
                    "sealer over a trowel finish at roughly half the rate"),
    Material(tag="rubber", name="Rolled rubber athletic flooring", hatch="membrane",
             color="#54585c",
             source="finish covering, not an assembly layer; thermal/vapour fields unset"),
    # Homogeneous sheet vinyl with heat-welded seams — the wet-room floor. Ordered with a
    # 6" integral flash cove where it laps up the wall, which is what makes floor and wall
    # one tray with no base joint; the cove is the waterproofing, so nothing impermeable
    # goes *under* the sheet (a second Class I layer there sandwiches the subfloor with no
    # drying path either way). Like the PVC panel above, no maker in this class publishes an
    # ASTM E96 number — and unlike the panel, nothing needs one, because a floor finish is
    # never a layer in a rated assembly.
    Material(tag="vinyl-sheet", name="Heat-welded sheet vinyl, integral flash cove",
             hatch="membrane", color="#8a9a86",
             source="finish covering, not an assembly layer; thermal/vapour fields unset. "
                    "Heat-welded seams and a 6\" integral flash cove lapped behind the wall "
                    "membrane — see houses/catlin/notes/plant_room.md for why the cove "
                    "replaces a separate waterproofing layer"),
)
