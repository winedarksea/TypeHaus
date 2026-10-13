"""A hung seat's load path below its joist line: the saddle bolted through it, the swivel or
shackle under it.

Named by ``SuspensionAnchor.hardware`` and graded by ``structural.suspension_anchor``.
"""

from __future__ import annotations

from typehaus.hardware.catalog import (
    ROLE_SUSPENSION_SADDLE,
    ROLE_SUSPENSION_SHACKLE,
    ROLE_SUSPENSION_SWIVEL,
    AllowableLoads,
    StructuralHardware,
)

CROSBY_3_S_5_SWIVEL = StructuralHardware(
    tag="crosby-3-s-5-swivel",
    name="Eye & eye thrust-bearing swivel, 3 t (rotates under load)",
    role=ROLE_SUSPENSION_SWIVEL,
    manufacturer="Kito Crosby",
    model="3-S-5",
    source="Crosby S-5 eye & eye swivel, stock no. 297057 (kitocrosby.com/product/"
           "crosby-s-5-eye-eye, read 2026-10-05): tapered roller thrust bearing, 'suitable "
           "for frequent rotation under load', 239 mm (9.4 in) overall, 3.86 kg (8.5 lb)",
    weight_lb=8.5,
    allowable=AllowableLoads(
        wll_lb=6614.0,
        # A steel rigging rating: no NDS duration factor applies; 1.0 so nothing scales it.
        load_duration_factor=1.0,
        fasteners="in-line tension eye to eye: the top eye on the saddle's shackle, the "
                  "bottom eye on the seat's ring",
        citation="Kito Crosby S-5 Eye & Eye product page, 3-S-5 row, read 2026-10-05: "
                 "working load limit 3 t (metric, = 6,614 lb), design factor 5:1, "
                 "individually proof tested to 2 x WLL",
    ),
)

FABRICATED_JOIST_SADDLE = StructuralHardware(
    tag="fabricated-joist-saddle-58",
    name="Steel U-saddle on a 3 1/2 in joist line, two 5/8 in through-bolts",
    role=ROLE_SUSPENSION_SADDLE,
    manufacturer="fabricated",
    model="SADDLE-3.5-2x58",
    source="Shop-fabricated, no stock part fits a 3 1/2 in LVL hidden above a ceiling: "
           "ASTM A36 1/4 x 3 in strap bent to a U around the joist (9 in legs, 3 9/16 in "
           "inside), a welded 1/2 in plate padeye under it for the swivel, and two 5/8 in "
           "ASTM A307 through-bolts at 4 in centres at the joist's MID-DEPTH (not lower: "
           "NDS 3.4.3.3). ~6 lb with bolts (16.5 in3 of plate at 0.284 lb/in3 + 1.2 lb). "
           "Its capacity is graded through the bolts and the joist; the weld and padeye "
           "are the fabricator's, proof-loaded to 2 x the anchor's factored demand",
    weight_lb=6.0,
)

FABRICATED_JOIST_SADDLE_HDG = StructuralHardware(
    tag="fabricated-joist-saddle-58-hdg",
    name="HDG steel U-saddle on a 4 1/2 in (3-ply 2x) joist line, two 5/8 in through-bolts",
    role=ROLE_SUSPENSION_SADDLE,
    manufacturer="fabricated",
    model="SADDLE-4.5-2x58-HDG",
    source="Shop-fabricated, exterior: ASTM A36 1/4 x 2 1/2 in strap bent to a U around a "
           "3-ply 2x12 (10 3/4 in legs, 4 9/16 in inside), a welded 1/2 in plate padeye under "
           "it for the shackle, hot-dip galvanized after fabrication (ASTM A123), and two "
           "5/8 in ASTM A307 bolts HDG to ASTM A153 at 4 in centres, the row 2 1/2 in below "
           "the line's top (the anchor's bolt_top_distance; NDS 3.4.3.3). ~7 lb with bolts "
           "(18.4 in3 of plate at 0.284 lb/in3 + 1.6 lb of bolts, nuts and washers). "
           "Galvanized, not stainless, so it sits on the galvanized "
           "shackle with no dissimilar pair. Graded through the bolts and the line; the weld "
           "and padeye are the fabricator's, proof-loaded to 2 x the anchor's demand",
    weight_lb=7.0,
)

CROSBY_G_209_SHACKLE_12 = StructuralHardware(
    tag="crosby-g-209-shackle-12",
    name="Screw-pin anchor shackle, 1/2 in, galvanized, 2 t (no swivel: a bed must not spin)",
    role=ROLE_SUSPENSION_SHACKLE,
    manufacturer="Kito Crosby",
    model="G-209-1/2",
    source="Crosby G-209 screw-pin anchor shackle, 1/2 in, stock no. 1018455, hot-dip "
           "galvanized forged carbon steel with an alloy pin, 0.7 lb (distributor listings, "
           "read 2026-10-13). Moused pin. A 4-rope bed hangs on a shackle, never a swivel",
    weight_lb=0.7,
    allowable=AllowableLoads(
        wll_lb=4409.0,
        load_duration_factor=1.0,
        fasteners="in-line through the saddle's padeye and the rope's thimble eye",
        citation="Crosby G-209 1/2 in row (stock no. 1018455), read 2026-10-13 from "
                 "distributor listings of the Crosby catalog: working load limit 2 t "
                 "(4,409 lb), meets ASME B30.26; confirm against the Crosby catalog page "
                 "when ordering",
    ),
)

SUSPENSION_HARDWARE = (CROSBY_3_S_5_SWIVEL, FABRICATED_JOIST_SADDLE,
                       FABRICATED_JOIST_SADDLE_HDG, CROSBY_G_209_SHACKLE_12)
