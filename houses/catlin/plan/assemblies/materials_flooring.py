"""Catlin floor assemblies whose installed height is coordinated at interior doors.

Depths include all layers above the 3/4-inch framed subfloor. The tile mortar beds
are design allowances; verify the installed planes with the selected tile and setter.
"""

from typehaus import Material


MATERIALS_FLOORING = [
    Material(tag="catlin-plant-vinyl-raised", name="Plant-room sheet vinyl over SurePly",
             hatch="membrane", color="#f2ede6", finish="veined-marble",
             finish_thickness_in=0.370, floor_waste_fraction=0.12,
             floor_companion_refs=("catlin-plant-sureply",),
             source='Tarkett First Class 0.120" fully adhered sheet over one nominal '
                    '1/4" SurePly resilient-flooring underlayment panel. The combined '
                    'height is provisional until the installed stack is measured; '
                    'Tarkett must approve flash coving and 70% design RH in writing.'),
    Material(tag="catlin-plant-sureply", name='SurePly plywood underlayment, nominal 1/4"',
             hatch="lumber", color="#d5c4a6",
             source="Patriot Timber SurePly, nominal 1/4 in, exterior-glue, "
                    "sanded resilient-flooring underlayment. Interior weather-protected "
                    "use only; fasten per Patriot instructions over the existing subfloor."),
    Material(tag="catlin-carpet-raised", name="Cut-pile carpet over rigid underlayment",
             hatch="batt", color="#9d9080", finish="carpet-pile",
             finish_thickness_in=0.75,
             floor_companion_refs=("carpet-pad", "catlin-carpet-underlayment"),
             source='1/4" rigid plywood underlayment + 1/4" bonded cushion + 1/4" '
                    'nominal carpet. Verify compressed edge at oak and tile doors.'),
    Material(tag="catlin-tile-oak-height", name="Porcelain over DITRA-XL to oak height",
             hatch="masonry", color="#dfe2e5", finish="porcelain-tile",
             finish_thickness_in=0.75,
             floor_waste_fraction=0.15, floor_companion_refs=("catlin-ditra-xl",),
             product_ref="PROD-MARAZZI-MF01",
             source='5/16" DITRA-XL + 5/16" Marazzi MF01 24x24 matte porcelain + '
                    '1/8" combined mortar beds = 3/4" above subfloor. Verify beds.'),
    Material(tag="catlin-tile-heated", name="Porcelain over DITRA-HEAT to oak height",
             hatch="masonry", color="#dce0e3", finish="porcelain-tile",
             finish_thickness_in=0.75,
             floor_waste_fraction=0.15, floor_companion_refs=("catlin-ditra-heat",),
             product_ref="PROD-MARAZZI-MF01",
             source='1/4" DITRA-HEAT + 5/16" Marazzi MF01 24x24 matte porcelain + '
                    '3/16" combined mortar beds = 3/4"; cable occupies studs.'),
    Material(tag="catlin-carpet-underlayment", name='Rigid plywood carpet underlayment, 1/4"',
             hatch="lumber", color="#bfae91",
             source="Rigid height build-up under Catlin raised carpet; cushion is separate."),
    Material(tag="catlin-ditra-xl", name='DITRA-XL uncoupling membrane, 5/16"',
             hatch="membrane", color="#da7433",
             source="Nonheated tile membrane; seams and perimeters waterproofed where required."),
    Material(tag="catlin-ditra-heat", name='DITRA-HEAT cable-retaining membrane, 1/4"',
             hatch="membrane", color="#d47835",
             source="Whole heated bathroom floor, including the area outside cable loops."),
]
