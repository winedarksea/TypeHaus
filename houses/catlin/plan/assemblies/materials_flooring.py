"""Catlin floor assemblies whose installed height is coordinated at interior doors.

Depths include all layers above the 3/4-inch framed subfloor. The tile mortar beds
are design allowances; verify the installed planes with the selected tile and setter.
"""

from typehaus import Material

# The tile baths' base is the painted PVC board (owner 2026-10-29), not a cut-tile base.
_TOE = ("Floor tile stops 1/4 inch off the wall; the PVC base sits on the tile over the gap, "
        "silicone at its toe, never grout.")

MATERIALS_FLOORING = [
    Material(tag="catlin-plant-vinyl-raised", name="Plant-room sheet vinyl over SurePly",
             hatch="membrane", color="#f2ede6", finish="veined-marble",
             finish_thickness_in=0.370, floor_waste_fraction=0.12,
             floor_companion_refs=("catlin-plant-sureply",), base_detail="resilient_base",
             base_joint_ref="catlin-base-toe-silicone",
             source='Tarkett First Class 0.120" fully adhered sheet over one nominal '
                    '1/4" SurePly resilient-flooring underlayment panel. The combined '
                    'height is provisional until the installed stack is measured. '
                    'Perimeter: 4" Johnsonite rubber cove base, silicone at its toe '
                    '(owner 2026-10-22, no flash cove; notes/plant_room.md).'),
    Material(tag="catlin-plant-sureply", name='SurePly plywood underlayment, nominal 1/4"',
             hatch="lumber", color="#d5c4a6",
             source="Patriot Timber SurePly, nominal 1/4 in, exterior-glue, "
                    "sanded resilient-flooring underlayment. Interior weather-protected "
                    "use only; fasten per Patriot instructions over the existing subfloor."),
    Material(tag="catlin-carpet-raised", name="Sweet Spot I Romano bedroom carpet (provisional)",
             hatch="batt", color="#e5dccb", finish="carpet-pile",
             finish_thickness_in=0.75,
             floor_companion_refs=("catlin-bedroom-carpet-pad", "catlin-carpet-underlayment"),
             product_ref="PROD-STAINMASTER-SWEET-SPOT-I-ROMANO",
             source='Provisional owner selection 2026-10-23: textured nylon, warm ivory/cream; '
                    'light warm greige alternative. Color is a schematic approximation. '
                    'The retained 3/4-inch modeled depth is a coordination allowance, '
                    'not the selected installed stack: its former 1/4-inch plywood + '
                    '1/4-inch pad + 1/4-inch carpet assumption is superseded. '
                    'Measure carpet including backing, cushion and compressed doorway '
                    'edges before resolving plywood, transitions, door clearances and '
                    'affected elevations together; notes/bedroom_carpet.md.'),
    Material(tag="catlin-bedroom-carpet-pad",
             name='Provisional bedroom rebond cushion, 8 lb/ft3, 7/16 inch',
             hatch="batt", color="#c8b7a0",
             product_ref="PROD-FUTURE-FOAM-150553488-33",
             source='Companion to catlin-carpet-raised only; installation is included '
                    'once in carpet labor. Confirm manufacturer acceptance and warranty '
                    'requirements. Manufacturer-approved 3/8-inch, 8 lb/ft3 cushion is '
                    'the height-coordination alternative; notes/bedroom_carpet.md.'),
    Material(tag="catlin-tile-calacatta-gold", name="Calacatta Gold hex mosaic, white epoxy grout",
             hatch="masonry", color="#f2efe8", finish="tile-calacatta-gold-hex",
             finish_thickness_in=0.75, floor_waste_fraction=0.15,
             base_joint_ref="catlin-base-toe-silicone",
             floor_companion_refs=("catlin-ditra-heat",),
             product_ref="PROD-QUBE-BODE-CALACATTA-HEX",
             source='RM-M-BATH2: nominal 3-inch matte hex (actual 2.86-inch chips), '
                    'white epoxy grout. '
                    '1/4-inch DITRA-HEAT + 0.26-inch tile + '
                    '0.24-inch combined bedding/approved leveling '
                    '= 3/4 inch. Beds provisional; verify installed stack. '
                    'Larger chips replace nominal MSI 2-inch hex to clear the membrane '
                    'minimum. ' + _TOE),
    Material(tag="catlin-tile-kaleo-brick", name="Kaleo Brick terracotta, cream epoxy grout",
             hatch="masonry", color="#bc7658", finish="tile-kaleo-running-bond",
             finish_thickness_in=0.75, floor_waste_fraction=0.15,
             base_joint_ref="catlin-base-toe-silicone",
             floor_companion_refs=("catlin-ditra-xl",), product_ref="PROD-IVY-KALEO-BRICK",
             source='RM-S-SUITEBATH: 7.08 x 14.17-inch matte rectangles, half-offset '
                    'running bond, warm cream slightly yellow epoxy grout. 5/16-inch '
                    'DITRA-XL + provisional 5/16-inch tile + 1/8-inch combined mortar '
                    '= 3/4 inch. Confirm tile thickness and beds before installation. ' + _TOE),
    Material(tag="catlin-tile-flower-blue", name="Flower Blue mosaic, light gray epoxy grout",
             hatch="masonry", color="#c7d9e2", finish="tile-flower-blue",
             finish_thickness_in=0.75, floor_waste_fraction=0.15,
             base_joint_ref="catlin-base-toe-silicone",
             floor_companion_refs=("catlin-mosaic-backer",),
             product_ref="PROD-SUNWINGS-FLOWER-BLUE",
             source='RM-S-VANITY: glossy glass petal mosaic, white base/white mortar, '
                    'light gray epoxy grout. 1/4-inch cement backer + 6 mm tile + '
                    '0.264-inch combined bedding/approved leveling allowance = 3/4 inch. '
                    'Provisional: select backer-compatible leveling system, not thick thinset. '
                    'Small chips are not placed directly over DITRA-XL. ' + _TOE),
    Material(tag="catlin-tile-carrara", name="Budget Carrara matte 12x24, white epoxy grout",
             hatch="masonry", color="#e9edf0", finish="tile-carrara-grid",
             finish_thickness_in=0.75, floor_waste_fraction=0.15,
             base_joint_ref="catlin-base-toe-silicone",
             floor_companion_refs=("catlin-ditra-heat",),
             product_ref="PROD-FLORIDA-CARRARA-MATTE",
             source='RM-S-BATH1: budget 12 x 24-inch matte porcelain, straight grid, 1/8-inch '
                    'white epoxy grout joints. 1/4-inch DITRA-HEAT + nominal 9 mm tile + '
                    '0.146-inch combined mortar = 3/4 inch. Verify thickness and beds; '
                    'matte selected '
                    'instead of requested polished HDC for published wet DCOF >=0.42. ' + _TOE),
    Material(tag="catlin-mosaic-backer", name="Continuous cement backer for glass mosaic, 1/4 inch",
             hatch="cement", color="#aaa69c",
             source='Nonheated RM-S-VANITY; fastened cement backer bedded in mortar. '
                    'Include approved height leveling in this assembly allowance. '
                    'Use white glass-compatible setting mortar above; '
                    'no DITRA minimum chip restriction.'),
    Material(tag="catlin-carpet-underlayment",
             name='Provisional rigid plywood carpet underlayment allowance, 1/4"',
             hatch="lumber", color="#bfae91",
             source="Provisional rigid buildup and takeoff allowance; cushion is separate. "
                    "The selected carpet/pad has not been measured. Reconcile whether "
                    "plywood is needed and its thickness with transitions, door clearances "
                    "and affected elevations before construction; notes/bedroom_carpet.md."),
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
]
