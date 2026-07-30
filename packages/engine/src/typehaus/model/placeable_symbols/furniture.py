"""The furniture half of the symbol registry — a table, not a pile of bespoke functions.

Each entry names a family from ``_families`` and the two or three parameters that make this
piece of furniture that piece of furniture. Adding a catalog size (a 72" sofa beside the 84")
needs no entry here at all: the same symbol renders at whatever W×D×H the type declares.
"""

from __future__ import annotations

from typehaus.model.placeable_symbols._families import (Builder, bed, besta, case, counter_case,
                                                        pedestal_seat, potted_plant, round_slab,
                                                        sauna_bench, screen, seating,
                                                        sectional, sectional_points, shelving,
                                                        slab)

__all__ = ["FURNITURE_SYMBOLS", "sectional_points"]

# The painted-casework pair, named once so a change of kitchen colour is a one-line edit.
CABINET = "cabinet-cream"
CABINET_SHADE = "cabinet-cream-dark"

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
    # The one furnishing that is not joinery: a pot with leaves over it. Five blades is the
    # fewest that still reads as a canopy rather than as a star at plan scale.
    "potted-plant": potted_plant(leaves=5),
    # Fitted casework. A base cabinet is a carcass under a counter slab, so it is the one
    # family that draws its top rather than its doors; wall and tall units are cases whose
    # cell grid says how the front divides — two doors side by side, or one full-height
    # pull-out. The same three symbols cover every catalog width.
    #
    # Painted cream rather than the stained ``wood`` the casegoods wear: fitted millwork is
    # finished on site as one run, and the light cream is what puts the grey counter slab and
    # the stainless appliances in relief instead of losing them against a brown box.
    "base-cabinet": counter_case(body=CABINET, kick_color=CABINET_SHADE),
    # The one base that is drawn hollow: its counter is cut and its carcass is a shell, so the
    # sink dropped into it is visible rather than entombed. The hole is deliberately smaller
    # than the sink — a drop-in's flange laps *over* the counter — which is what leaves real
    # bearing all round instead of a hairline the two edges fight over.
    "sink-base": counter_case(body=CABINET, kick_color=CABINET_SHADE, cutout=(0.83, 0.78)),
    "wall-cabinet": case(rows=1, cols=2, pulls=True, color=CABINET, face_color=CABINET_SHADE),
    "tall-cabinet": case(rows=1, cols=1, pulls=True, color=CABINET, face_color=CABINET_SHADE),
    # Past about 24" a full-height door stops being a door — it racks on its own weight and
    # needs half its width of swing — so wide tall units carry a pair. Same carcass as
    # ``tall-cabinet``; the cell grid is the whole difference, which is what this registry
    # distinguishes symbols by.
    "tall-cabinet-double": case(rows=1, cols=2, pulls=True, color=CABINET,
                                face_color=CABINET_SHADE),
    # Three bays is where a tall unit stops being a cabinet and becomes a wall of storage:
    # 72" of carcass behind three 24" doors, which is the widest front that still divides on
    # the 24" module the doubles use.
    "tall-cabinet-triple": case(rows=1, cols=3, pulls=True, color=CABINET,
                                face_color=CABINET_SHADE),
    "besta": besta(),
    # Sauna joinery. Not casegoods and not tables: a bench is a platform on end supports, and
    # the two-tier version is the one piece of furniture whose *height* is a code-of-practice
    # number rather than an ergonomic average — see ``sauna_bench``.
    "sauna-bench": sauna_bench(tiers=1),
    "sauna-bench-tiered": sauna_bench(tiers=2),
}
