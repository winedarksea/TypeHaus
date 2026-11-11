"""Catlin floor assemblies whose installed height is coordinated at interior doors.

Depths include all layers above the 3/4-inch framed subfloor (the gym's mats sit on
the slab). The tile mortar beds are design allowances; verify the installed planes
with the selected tile and setter.
"""

from typehaus import Material, inch

# The tile baths' base is the painted PVC board (owner 2026-10-29), not a cut-tile base.
_TOE = ("Floor tile stops 1/4 inch off the wall; the PVC base sits on the tile over the gap, "
        "silicone at its toe, never grout.")
_LARGE_FORMAT = ("Large format: substrate flat to 1/8 inch in 10 ft (ANSI A108.02), "
                 "large-and-heavy-tile mortar, lippage control. ")

# Johnsonite Traditional rubber wall base DC-XX (coved), 4" x 0.125": Tarkett "Johnsonite
# Resilient Wall Base, Traditional Wall Base" product specification 070517, p.1 §1.3.2
# (thecornerguardstore.com/content/submittals/tk/DS_20170705_EN_TRADITIONAL_WALL_BASE.pdf).
_RUBBER_COVE_4 = inch(4)

MATERIALS_FLOORING = [
    Material(tag="catlin-plant-vinyl-raised", name="Plant-room sheet vinyl over SurePly",
             hatch="membrane", color="#e2e1e0", finish="tile-gatsby-grid",
             finish_thickness_in=0.370, floor_waste_fraction=0.12,
             floor_companion_refs=("catlin-plant-sureply",), base_detail="resilient_base",
             base_height=_RUBBER_COVE_4,
             base_joint_ref="catlin-base-toe-silicone",
             source='Tarkett First Class FiberFloor, Windsor Gatsby 87061, 12 ft (no seam), '
                    'fully adhered over one nominal 1/4" SurePly; the combined height is '
                    'provisional until measured. Perimeter: 4" Johnsonite rubber cove base, '
                    'silicone toe (owner 2026-10-22, reaffirmed 2026-11-03). Alternatives: '
                    'Beauflor Blacktex HD Canvas 109M; Mannington Platinum Tapestry 130451.'),
    Material(tag="catlin-vinyl-gatsby", name="Tarkett First Class Windsor Gatsby sheet vinyl",
             hatch="membrane", color="#e2e1e0", finish="tile-gatsby-grid",
             finish_thickness_in=0.120, base_detail="resilient_base",
             base_height=_RUBBER_COVE_4,
             base_joint_ref="catlin-base-toe-silicone",
             source='RM-A-STUDIO, RM-A-STUBATH, RM-B-BATH, owner 2026-11-03: Tarkett First Class '
                    'FiberFloor, Windsor Gatsby 87061, 12 ft, glue-down on the subfloor. 4" '
                    'Johnsonite rubber cove base, silicone toe, as the plant room. '
                    'Alternatives: Beauflor Blacktex HD Canvas 109M; Mannington Platinum '
                    'Tapestry 130451.'),
    Material(tag="catlin-plant-sureply", name='SurePly plywood underlayment, nominal 1/4"',
             hatch="lumber", color="#d5c4a6",
             source="Patriot Timber SurePly, nominal 1/4 in, exterior-glue, "
                    "sanded resilient-flooring underlayment. Interior weather-protected "
                    "use only; fasten per Patriot instructions over the existing subfloor."),
    Material(tag="catlin-carpet-raised", name="Sweet Spot I Romano bedroom carpet (provisional)",
             hatch="batt", color="#e5dccb", finish="carpet-pile",
             finish_thickness_in=1.0,
             floor_companion_refs=("catlin-bedroom-carpet-pad",),
             product_ref="PROD-STAINMASTER-SWEET-SPOT-I-ROMANO",
             source='Provisional owner selection 2026-10-23: textured nylon, warm ivory/cream; '
                    'light warm greige alternative. Color is a schematic approximation. '
                    'Owner 2026-11-01: no plywood. 1 inch over the subfloor = 0.56-inch '
                    'published pile + 1/16-inch backing allowance + 3/8-inch cushion, '
                    '1/4 inch over the 3/4-inch oak and tile it meets. Each bedroom doorway '
                    'tucks the carpet into a Z-bar flush with the hard floor '
                    '(plan/doorway_transitions.py). Measure the backing on the sample: '
                    'the Z-bar answer holds to 0.10 inch; notes/bedroom_carpet.md.'),
    Material(tag="catlin-theater-carpet",
             name="Emphatic II 30 Nightlife theater carpet (provisional)",
             hatch="batt", color="#1f1a21", finish="carpet-pile",
             finish_thickness_in=0.735,
             floor_companion_refs=("catlin-bedroom-carpet-pad",),
             product_ref="PROD-PHILA-EMPHATIC-II-30-NIGHTLIFE",
             source='RM-B-PLAY-N, owner 2026-11-01: dark cut pile for the theater. 0.36-inch '
                    'published total + 3/8-inch cushion, stretched in; flush with the gym '
                    'mats at D-B-PLAY (Z-bar). Dealer to confirm stretch-in; '
                    'notes/basement_carpet.md.'),
    Material(tag="catlin-stair-carpet", name="Refine Structural stair carpet (provisional)",
             hatch="batt", color="#415058", finish="carpet-refine-structural",
             finish_thickness_in=0.25,
             product_ref="PROD-PHILA-REFINE-STRUCTURAL",
             source='ST-B2M, owner 2026-11-01: dense multi-level loop glued to tread and '
                    'riser, no cushion. 0.237-inch published total + adhesive, 1/4 inch; '
                    'notes/basement_carpet.md.'),
    Material(tag="catlin-bedroom-carpet-pad",
             name='Bedroom and theater rebond cushion, 8 lb/ft3, 3/8 inch',
             hatch="batt", color="#c8b7a0",
             product_ref="PROD-FUTURE-FOAM-150553488-32",
             source='Companion to catlin-carpet-raised and catlin-theater-carpet; '
                    'meets Shaw stretch-in commercial minimum (8 lb, 3/8 in max); installation '
                    'is included once in carpet labor. 3/8 inch, not the 7/16 inch first '
                    'selected, so the carpet stands 1/4 inch over the oak (owner 2026-11-01). '
                    'Confirm carpet manufacturer acceptance and warranty; '
                    'notes/bedroom_carpet.md.'),
    Material(tag="catlin-tile-limestone",
             name="Lifeproof Limestone 12x24 matte, Biscuit grout",
             hatch="masonry", color="#cdbea9", finish="tile-limestone-grid",
             finish_thickness_in=0.75, floor_waste_fraction=0.15,
             base_joint_ref="catlin-base-toe-silicone",
             floor_companion_refs=("catlin-ditra-heat",),
             product_ref="PROD-LIFEPROOF-LIMESTONE",
             source='RM-M-BATH2, RM-S-BATH1: 12 x 24-inch matte porcelain, straight grid, long '
                    'axis along plan Y, 3/16-inch joints, MAPEI Ultracolor Plus FA #5014 Biscuit '
                    'grout (nearest warm shade to Haystack, no published cross-reference: confirm '
                    'on a cured sample on a tile; #5015 Bone is the paler fallback), Mapesil T '
                    'Plus #5014 silicone at changes of plane. Do not run the floor heat until '
                    'the grout has cured. 1/4-inch DITRA-HEAT + 8 mm tile + ~0.185-inch combined '
                    'mortar = 3/4 inch; verify thickness and beds. ' + _LARGE_FORMAT + _TOE),
    Material(tag="catlin-tile-kaleo-brick", name="Kaleo Brick terracotta, cream epoxy grout",
             hatch="masonry", color="#bc7658", finish="tile-kaleo-running-bond",
             finish_thickness_in=0.75, floor_waste_fraction=0.15,
             base_joint_ref="catlin-base-toe-silicone",
             floor_companion_refs=("catlin-ditra-xl",), product_ref="PROD-IVY-KALEO-BRICK",
             source='RM-S-SUITEBATH: 7.08 x 14.17-inch matte rectangles, half-offset '
                    'running bond, warm cream slightly yellow epoxy grout. 5/16-inch '
                    'DITRA-XL + provisional 5/16-inch tile + 1/8-inch combined mortar '
                    '= 3/4 inch. Confirm tile thickness and beds before installation. ' + _TOE),
    Material(tag="catlin-tile-jume-onyx-blue",
             name="Jume Onyx Blue 23.62x47.24 polished, platinum epoxy grout",
             hatch="masonry", color="#7894a9", finish="tile-onyx-jume-blue-grid",
             finish_thickness_in=0.75, floor_waste_fraction=0.20,
             base_joint_ref="catlin-base-toe-silicone",
             floor_companion_refs=("tile-uncoupling-membrane",),
             product_ref="PROD-IVY-JUME-ONYX-BLUE",
             source='RM-S-VANITY: Jume Onyx Blue 23.62 x 47.24-inch polished porcelain, 1/16-inch '
                    'rectified joints, platinum epoxy grout. 1/8-inch uncoupling membrane + '
                    '10.5 mm (~0.413-inch) tile + ~0.212-inch combined mortar = 3/4 inch. '
                    'Listing conflicts at 10/10.5 mm; verify thickness and beds. DCOF <0.42; '
                    'selected for the sinks-only room, no bathing. ' + _LARGE_FORMAT + _TOE),
    Material(tag="catlin-ditra-xl", name='DITRA-XL uncoupling membrane, 5/16"',
             hatch="membrane", color="#da7433",
             source="Nonheated tile membrane; seams and perimeters waterproofed where required."),
    Material(tag="catlin-base-toe-silicone", name="Silicone toe bead at the wall base, white",
             color="#f4f4f2", product_ref="PROD-GE-2812565",
             source="100% silicone kitchen & bath sealant over the floor's perimeter movement "
                    "joint, beaded at base install. ~1/4 inch bead."),
    Material(tag="catlin-ditra-heat", name='DITRA-HEAT cable-retaining membrane, 1/4"',
             hatch="membrane", color="#d47835",
             source="Whole heated bathroom floor, including the area outside cable loops."),
    Material(tag="catlin-rubber-stall-mat", name='Rubber stall mats, 4x6 ft x 3/4"',
             hatch="membrane", color="#26282a",
             finish_thickness_in=0.75, floor_waste_fraction=0.09,
             source='RM-B-GYM: 4 x 6 ft x 3/4-inch vulcanized recycled rubber stall mats '
                    '(Tractor Supply / Rural King), loose-laid, no adhesive; 13 mats '
                    '(312 SF) over ~287 SF. Before laying: slab moisture test (taped poly '
                    'sheet; 6-mil poly under the mats if damp), and air the mats out 1-2 '
                    'weeks. Reducers to the sealed concrete at D-B-GYM and D-B-SAUNA. '
                    'Echo-neutral; see notes/gym_acoustics.md.'),
]
