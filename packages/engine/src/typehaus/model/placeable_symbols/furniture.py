"""The furniture half of the symbol registry — a table, not a pile of bespoke functions.

Each entry names a family from ``_families`` and the two or three parameters that make this
piece of furniture that piece of furniture. Adding a catalog size (a 72" sofa beside the 84")
needs no entry here at all: the same symbol renders at whatever W×D×H the type declares.
"""

from __future__ import annotations

from typehaus.model.placeable_symbols._families import (Builder, bed, case, pedestal_seat,
                                                        round_slab, screen, seating,
                                                        sectional, sectional_points, shelving,
                                                        slab)

__all__ = ["FURNITURE_SYMBOLS", "sectional_points"]

FURNITURE_SYMBOLS: dict[str, Builder] = {
    # Seating. Seat count is what separates a sofa from a loveseat from an armchair.
    "sofa": seating(arms=True, seats=3),
    "loveseat": seating(arms=True, seats=2),
    "armchair": seating(arms=True, seats=1),
    "sectional": sectional(),
    # A dining chair has no arms and a slim back; its "seats" count is the single pad.
    "dining-chair": seating(arms=False, seats=1, back_depth_m=0.10),
    "office-chair": pedestal_seat(),
    # Tables and desks. The apron is what stops a dining table reading as a coffee table in
    # elevation, and the coffee/end tables deliberately skip it — they are open underneath.
    "dining-table": slab(leg_inset_m=0.09, apron=True),
    "round-table": round_slab(pedestal=True),
    "coffee-table": slab(leg_inset_m=0.05, apron=False),
    "end-table": slab(leg_inset_m=0.04, apron=False),
    "desk": slab(leg_inset_m=0.06, apron=True, modesty_panel=True),
    # Casegoods, distinguished by their drawer grid.
    "dresser": case(rows=3, cols=2),
    "chest": case(rows=5, cols=1),
    "nightstand": case(rows=2, cols=1),
    "media-console": case(rows=2, cols=3, pulls=False),
    "bookcase": shelving(shelves=5),
    "bed": bed(pillows=2, headboard=True),
    "tv": screen(stand=True),
}
