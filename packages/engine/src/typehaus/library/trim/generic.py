"""Formed trim no one manufacturer's kit supplies: a sheet-metal shop's custom brake.

These sit in ``metal_sales.PROFILES`` beside the catalog parts, because that dict is the one
trim catalog every resolver, check and take-off looks a ``product`` up in.
"""

from typehaus.library.trim.profile import TrimProfile

#: The Z drip flashing over a window or door head on a non-metal rainscreen (fiber cement
#: over furring). Section = ``resolve/opening_flashing.head_flashing_section``: an upstand on
#: the water plane taped under the WRB above, a leg falling outward across the cavity, the
#: cladding and the head casing, a drip past the casing face; 3/4" end dams. Held to the
#: sheathing by the upstand under its tape, so no face fasteners are billed.
OPENING_HEAD_DRIP_FLASHING = TrimProfile(
    "Opening head drip flashing (Z), custom brake",
    stock_lengths_in=(120.0,),
    fastener_rows=0,
    custom=True,
    maker="custom brake",
    source="IRC R703.4 item 1 and R703.4.1 (flashing at exterior window and door openings, "
           "extending to the surface of the exterior wall finish); James Hardie HardiePlank "
           "Lap Siding Installation Requirements HS0920-P1/4 (10/10), Fig. 7",
)

#: James Hardie: "Maintain a 1/4" clearance between the bottom of James Hardie products and
#: horizontal flashing. Do not caulk gap." (HS0920-P1/4, Fig. 7). The cladding's bottom edge,
#: and the perforated strip under it that closes the cavity's foot, stand this far up.
HEAD_FLASHING_CLADDING_CLEARANCE_IN = 0.25
