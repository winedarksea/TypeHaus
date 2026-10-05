"""Seats hung from one point overhead (``HangingSeatType``), carried by a SuspensionAnchor."""

from __future__ import annotations

from typehaus.library.placeables._zones import swing_zone
from typehaus.model import HangingSeatType, Mount, MountKind, inch

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
