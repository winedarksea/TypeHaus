"""Catlin's SEKTION part choices, by role: what ``sektion_parts`` orders for each frame.

Tags only; the records are in products_ikea.py and the rooms' own type files. Counts are the
library's rules (notes/ikea_sektion_order.md). NOT editable: no element lives here.
"""

from __future__ import annotations

from typehaus.library.placeables.sektion_parts import SektionHardware

_SHELVES = {(w, d): f"PROD-IKEA-UTRUSTA-SHELF-{w}-{d}"
            for w, d in ((12, 24), (18, 24), (24, 24), (36, 24), (12, 15), (30, 15), (36, 15))}
_COMMON = {"hinge": "PROD-IKEA-UTRUSTA-HINGE-110",
           "lift_hinge": "PROD-IKEA-UTRUSTA-HINGE-HORIZONTAL",
           "leg": "PROD-IKEA-SEKTION-LEG", "toe_kick": "PROD-IKEA-FORBATTRA-TOEKICK-84",
           "rail": "PROD-IKEA-SEKTION-RAIL-84"}

# Kitchen, living north run and the bed desk: AXSTAD matte white, BAGGANÄS black.
AXSTAD_HARDWARE = SektionHardware(
    fronts={
        **{("door", w, h): f"PROD-IKEA-AXSTAD-DOOR-{w}-{h}"
           for w, h in ((12, 30), (15, 20), (15, 30), (18, 20), (18, 30), (18, 40), (24, 30),
                        (24, 50))},
        **{("drawer", w, 10): f"PROD-IKEA-AXSTAD-DRAWER-{w}-10" for w in (18, 24, 36)},
        ("drawer", 15, 10): "PROD-IKEA-AXSTAD-MATTE-15-10",
        ("lift", 24, 15): "PROD-IKEA-AXSTAD-DRAWER-24-15",
    },
    drawers={**{(w, 10): f"PROD-IKEA-MAXIMERA-MEDIUM-{w}-24" for w in (18, 24, 36)},
             (15, 10): "PROD-IKEA-MAXIMERA-MEDIUM-15-24"},
    shelves=_SHELVES, knob="PROD-IKEA-BAGGANAS-KNOB-BLACK",
    pull="PROD-IKEA-BAGGANAS-PULL-BLACK", **_COMMON,
)

# Hall bath and study nook: VOXTORP matte white, no loose hardware (owner, 2026-10-02).
VOXTORP_HARDWARE = SektionHardware(
    fronts={("door", 24, 30): "PROD-IKEA-VOXTORP-DOOR-24-30",
            ("door", 24, 20): "PROD-IKEA-VOXTORP-DOOR-24-20",
            ("door", 18, 30): "PROD-IKEA-VOXTORP-DOOR-18-30",
            ("door", 18, 20): "PROD-IKEA-VOXTORP-DOOR-18-20",
            ("drawer", 24, 10): "PROD-IKEA-VOXTORP-DRAWER-24-10",
            ("drawer", 18, 10): "PROD-IKEA-VOXTORP-DRAWER-18-10",
            ("drawer", 18, 15): "PROD-IKEA-VOXTORP-DRAWER-18-15",
            ("lift", 24, 15): "PROD-IKEA-VOXTORP-DOOR-24-15"},
    drawers={(24, 10): "PROD-IKEA-MAXIMERA-MEDIUM-24-24",
             (18, 10): "PROD-IKEA-MAXIMERA-MEDIUM-18-24",
             (18, 15): "PROD-IKEA-MAXIMERA-HIGH-18-24"},
    shelves=_SHELVES, **_COMMON,
)
