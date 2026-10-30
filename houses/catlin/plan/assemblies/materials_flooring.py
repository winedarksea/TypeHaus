"""Catlin floor assemblies whose installed height is coordinated at interior doors.

Depths include all layers above the 3/4-inch framed subfloor (the gym's mats sit on
the slab). The tile mortar beds are design allowances; verify the installed planes
with the selected tile and setter.
"""

from typehaus import Material

# The tile baths' base is the painted PVC board (owner 2026-10-29), not a cut-tile base.
_TOE = ("Floor tile stops 1/4 inch off the wall; the PVC base sits on the tile over the gap, "
        "silicone at its toe, never grout.")
_LARGE_FORMAT = ("Large format: substrate flat to 1/8 inch in 10 ft (ANSI A108.02), "
                 "large-and-heavy-tile mortar, lippage control. ")

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
    Material(tag="catlin-tile-opera-blue",
             name="Selene Opera Blue 24x48 polished, platinum epoxy grout",
             hatch="masonry", color="#c5c6cc", finish="tile-onyx-opera-blue-grid",
             finish_thickness_in=0.75, floor_waste_fraction=0.20,
             base_joint_ref="catlin-base-toe-silicone",
             floor_companion_refs=("catlin-ditra-heat",),
             product_ref="PROD-IVY-SELENE-OPERA-BLUE",
             source='RM-M-BATH2: 24 x 48-inch polished onyx-look porcelain, 1/16-inch '
                    'rectified joints, platinum epoxy grout. 1/4-inch DITRA-HEAT + '
                    '~0.40-inch tile + ~0.10-inch mortar = 3/4 inch. ' + _LARGE_FORMAT + _TOE),
    Material(tag="catlin-tile-kaleo-brick", name="Kaleo Brick terracotta, cream epoxy grout",
             hatch="masonry", color="#bc7658", finish="tile-kaleo-running-bond",
             finish_thickness_in=0.75, floor_waste_fraction=0.15,
             base_joint_ref="catlin-base-toe-silicone",
             floor_companion_refs=("catlin-ditra-xl",), product_ref="PROD-IVY-KALEO-BRICK",
             source='RM-S-SUITEBATH: 7.08 x 14.17-inch matte rectangles, half-offset '
                    'running bond, warm cream slightly yellow epoxy grout. 5/16-inch '
                    'DITRA-XL + provisional 5/16-inch tile + 1/8-inch combined mortar '
                    '= 3/4 inch. Confirm tile thickness and beds before installation. ' + _TOE),
    Material(tag="catlin-tile-agua-linda",
             name="Agua Linda 24x48 polished, platinum epoxy grout",
             hatch="masonry", color="#c7d5e2", finish="tile-onyx-agua-linda-grid",
             finish_thickness_in=0.75, floor_waste_fraction=0.20,
             base_joint_ref="catlin-base-toe-silicone",
             floor_companion_refs=("tile-uncoupling-membrane",),
             product_ref="PROD-MSI-AGUA-LINDA",
             source='RM-S-VANITY: 24 x 48-inch polished blue onyx-look porcelain, 1/16-inch '
                    'rectified joints, platinum epoxy grout. 1/8-inch uncoupling membrane + '
                    '0.40-inch tile + ~0.225-inch combined mortar = 3/4 inch (DITRA-XL '
                    'would leave under 1/16 inch of mortar). Listing DCOF <0.42, dry '
                    'areas; accepted for a sinks-only room. ' + _LARGE_FORMAT + _TOE),
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
