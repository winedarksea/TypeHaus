"""Seats hung from the framing overhead (``HangingSeatType``), one SuspensionAnchor per
hang point."""

from __future__ import annotations

from typehaus.library.placeables._zones import swing_zone
from typehaus.model import HangingSeatType, Mount, MountKind, inch, pt

# A medium spreader-bar hammock chair, sized off the La Siesta Habana Comfort (lasiesta.com,
# read 2026-10-05: 110 cm bar, 160 cm overall, 2.6 kg, 130 kg / 285 lb). The RATING is the
# two-occupant basis this type answers, which that product does not meet: buy one rated at
# 360 lb or more. Hung from a SuspensionAnchor (model/suspension.py).
HAMMOCK_CHAIR_MEDIUM = HangingSeatType(
    tag="FURN-HAMMOCK-CHAIR-MEDIUM", name="Hammock chair, medium, 43\" spreader, 360 lb",
    footprint=(inch(43.3), inch(34)), height=inch(63), plan_symbol="hammock-chair",
    mount=Mount(kind=MountKind.CEILING, elevation=inch(12)),
    rated_load_lb=360.0,
    rated_load_source="Design basis, two occupants (catlin owner, 2026-10-05). The size "
                      "reference, La Siesta Habana Comfort, is rated 130 kg / 285 lb and "
                      "does not meet it; the purchased chair must state 360 lb or more",
    weight_lb=5.7, wall_clearance=inch(35.5), ground_clearance=inch(12),
    suspension_range=(inch(6), inch(48)),
    source="La Siesta Habana Comfort geometry (lasiesta.com, read 2026-10-05): spreader "
           "110 cm, overall ring to seat 160 cm, minimum hanging height 210 cm, 2.6 kg; "
           "35.5 in wall clearance and 12 in ground clearance per the maker's hanging "
           "guide. Suspension range is a planning figure for an adjustable rope kit",
    clearances=(swing_zone(inch(43.3), inch(34), inch(8), "fore-and-aft swing"),),
)

# A twin rope-hung daybed, sized off the Atlantic Swing Co. Simon (theporchswingcompany.com,
# read 2026-10-13: 80 x 43 x 29 in, 100 lb, 2- or 4-point 1 in rope kit for ceilings to 9').
# No rating is published; 500 lb is the owner's design basis and the bed bought must state it.
# Four ropes on the arms, no swivel. They hang plumb: each hang point is its anchor's
# station overhead, 76 x 36 in, inside the frame.
HANGING_DAYBED_TWIN = HangingSeatType(
    tag="FURN-HANGING-DAYBED-TWIN", name="Hanging daybed, twin, 4-rope, 500 lb",
    footprint=(inch(80), inch(43)), height=inch(29), plan_symbol="hanging-daybed",
    mount=Mount(kind=MountKind.CEILING, elevation=inch(18)),
    rated_load_lb=500.0,
    rated_load_source="Design basis, owner 2026-10-13: 500 lb. The size reference, the "
                      "Atlantic Swing Co. Simon, publishes no rating; the bed bought must "
                      "state 500 lb or more",
    weight_lb=125.0, wall_clearance=inch(12), ground_clearance=inch(18),
    suspension_range=(inch(24), inch(84)),
    hang_points=(pt(inch(-38), inch(-18)), pt(inch(38), inch(-18)),
                 pt(inch(38), inch(18)), pt(inch(-38), inch(18))),
    source="Atlantic Swing Co. Simon kiln-dried pine daybed swing, twin (theporchswingcompany"
           ".com, read 2026-10-13): 80 W x 43 D x 29 H in, 100 lb, 75 x 39 in cushion sold "
           "separately (~25 lb, a planning figure), 4-point 1 in synthetic rope kit for "
           "ceilings to 9 ft. Hang points on the arms, 2 in in from the ends and 3 1/2 in "
           "in from the front and back (76 x 36 in); 12 in wall "
           "clearance is the sway past the frame, measured from the rope. Suspension range "
           "is a planning figure for that kit",
    clearances=(swing_zone(inch(80), inch(43), inch(12), "sway"),),
)
