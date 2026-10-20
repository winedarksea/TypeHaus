# haus: editable
# Birch plywood carcass, solid walnut face/trim and coordinated booth upholstery.
from typehaus import Material

MATERIALS_STUDY_BOOTH = [
    Material(tag="study-walnut-front-4q", name='Black walnut bench front, 4/4 edge-glued',
             color="#80634f", finish="clear-satin-hardwax-oil", species="walnut",
             nominal_quarters=4, milling_profile="S4S", requires_custom_milling=True,
             max_board_width_in=10,
             source="One finished edge-glued front panel from 4/4 walnut dressed to 3/4 inch; plan around rough boards up to 10 inches wide rather than a single wide slab. Select matched heartwood and horizontal grain to coordinate with desk and trim. Clear satin hardwax oil on all faces. Allow cross-grain movement in height with slotted fixings and edge clearance; no rigid glue joint to plywood carcass."),
    Material(tag="study-birch-ply", name='Birch veneer-core plywood, 3/4", A-1',
             color="#dfcba7", finish="clear-satin-sealer",
             panel_face_grade="A-1", panel_core="veneer core", panel_veneer_species="birch",
             panel_nominal_thickness_in=0.75,
             source="A-1 birch, maple substitution permitted with same grade/core. No significant core voids at joints or fasteners. Sand and seal all faces/edges beneath cushions. Measure supplied thickness before cutting joinery; no MDF or particleboard substitution."),
    Material(tag="walnut-trim-4q", name='Black walnut booth edging and cap, 4/4 S4S',
             color="#80634f", finish="clear-satin-hardwax-oil", species="walnut",
             nominal_quarters=4, milling_profile="eased", requires_custom_milling=True,
             source="3/4 inch finished edging and cap; same heartwood tone as desktop and solid front. Eased edges; cap attached through slots for movement."),
    Material(tag="study-upholstery", name="Warm gray performance fabric, booth seat and back",
             color="#a39a90", finish="woven-fabric",
             source="Removable zippered seat cover, thin polyester wrap, concealed non-slip retention. Back pad with removable contoured lumbar insert and concealed height adjustment. Seat HR foam 3 inch, >=2.5 lb/ft3, supplier 25% IFD 35-45 lbf with test conditions. Occupied height verified by mock-up, not inferred from density."),
]
