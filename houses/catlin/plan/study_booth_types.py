# haus: editable
# RM-M-STUDY's fitted booth; fabrication basis in notes/study_booth.md.
from typehaus import BuiltInBenchSpec, FurnitureType, inch

STUDY_BENCH = FurnitureType(
    tag="FT-STUDY-BENCH", name="Study upholstered booth bench, walnut-faced plywood",
    footprint=(inch(48.625), inch(20.819858)), height=inch(36),
    storage=False, work_surface=False,
    built_in_bench=BuiltInBenchSpec(
        width=inch(48.625), effective_seat_depth=inch(17), deck_height=inch(17.5),
        back_height=inch(36), panel_thickness=inch(.75), seat_cushion_thickness=inch(3),
        back_pad_thickness=inch(1), lumbar_projection=inch(.5),
        lumbar_height_above_seat=inch(7), occupied_seat_height=inch(19.5),
        back_angle_degrees=100, toe_height=inch(2), toe_recess=inch(2),
        cap_thickness=inch(.75), carcass_material_ref="study-birch-ply",
        front_material_ref="study-walnut-ply", trim_material_ref="walnut-trim-4q",
        upholstery_material_ref="study-upholstery", internal_partition_count=2,
        seat_foam_density_lb_ft3=2.5, seat_foam_ifd_min_lbf=35, seat_foam_ifd_max_lbf=45,
        lumbar_adjustment_min=inch(6), lumbar_adjustment_max=inch(9),
        front_roundover_radius=inch(.25), cushion_front_radius=inch(1)),
    source="Floor-standing A-1 veneer-core plywood bench with walnut A-1 front and solid walnut trim. Two internal seat partitions; four triangular back gussets support 100-degree back without fasteners into W-M-HS4's pocket-door cavity. 17.5 inch deck plus 3 inch HR seat; occupied target 19-20 inch requires mock-up. Matching warm gray seat/back, removable lumbar insert 6-9 inch above occupied seat, nominal 7 inch. No storage. See notes/study_booth.md for cut/fit and fabrication acceptance.",
)

STUDY_DESK = FurnitureType(
    tag="FT-STUDY-DESK", name='Study fixed walnut desk, 29" x 16"',
    footprint=(inch(29), inch(16)), height=inch(29.5),
    storage=False, work_surface=True, plan_symbol="wall-desk",
    wood_material_ref="walnut-shelf-5q",
    source="Fixed 1 inch walnut top on cleats into south wall study-face framing, with open knee space. West and south edges scribed 1/16 inch from finished wainscot. 16 inch depth retains bench-to-desk clearance with reclined upholstered back. No keyboard tray: laptop keyboard directly on desktop; screen/keyboard coupling remains an ergonomic limitation.",
)

FOLD_LEAF = FurnitureType(
    tag="FT-STUDY-DESK-LEAF", name='Study walnut fold-down leaf, 19 5/8" x 16"',
    footprint=(inch(19.625), inch(16)), height=inch(29.5),
    storage=False, work_surface=True, plan_symbol="wall-desk",
    wood_material_ref="walnut-shelf-5q",
    source="1 inch walnut leaf, same flitch/grain as fixed top, modeled deployed. Continuous piano hinge and ledger attached to let-in study-face blocking in W-M-CLN2, with bullet catches at fixed top. Pair of Sugatsune EB-303/EP-BL folding brackets, 307 mm (12.087 inch) projection, 165 mm height, supplier P1/P2 capacities 150/75 kgf depending on load position; verify installation and actual front-edge load rather than adding ratings. Continuous hinge/ledger and bullet catches retain lateral restraint. Original 18 7/8 inch Hebgo brackets do NOT fit. Stowed panel hangs approximately 12.5-28.5 inch AFF. Manufacturer installation and wall/blocking connection verification required before fabrication; no through bolts bridging staggered wall leaves.",
)

STUDY_FOOTREST = FurnitureType(
    tag="FT-STUDY-FOOTREST", name="Study removable adjustable footrest",
    footprint=(inch(18), inch(12)), height=inch(3),
    storage=False, work_surface=False, plan_symbol="footrest",
    source="Purchased stable non-slip footrest, approximately 18 x 12 inch; independent height adjustment 1-6 inch and tilt 0-20 degrees. Modeled nominal 3 inch high at 10 degrees. Set separately for each user's supported feet, no knee pressure. Removable for taller users. Included in booth upholstery/fit allowance; no custom-milling quantity.",
)
