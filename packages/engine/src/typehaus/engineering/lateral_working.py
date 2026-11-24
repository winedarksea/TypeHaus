"""The working for ``lateral_system``'s deck and panel rows (calc-sheet pattern).

Each function returns the :class:`~typehaus.engineering.item.Step` chain one limit state
prints; the numbers are the caller's, the very ones the state is built from. A repeated
group (the same chain for every nailer, every receiving wall) uses one function, so one chain
of steps serves every member of the group and the sheet prints it once.
"""

from __future__ import annotations

from typehaus.engineering.item import Step, num

#: Load combinations, named in words with the standard's letters.
WIND_ASD = ("0.6W, ASD wind (ASCE 7-16 §2.4.1(7) wind term)", (("W", 0.6),))
WIND_NO_DEAD = ("0.6W, ASD wind, no dead load credited (a bound; §2.4.1(7) would take 0.6D "
                "off the uplift)", (("W", 0.6),))
NET_UPLIFT = ("ASCE 7-16 §2.4.1(7) 0.6D + 0.6W", (("D", 0.6), ("W", 0.6)))
GEOMETRY = ("none: a geometry limit, no load", ())


def cw(combo: tuple[str, tuple[tuple[str, float], ...]]) -> dict:
    """``LimitState`` keywords for one combination constant."""
    return {"combination": combo[0], "combination_factors": combo[1]}


_DECK_V = ("the roof's design wind (0.6 q G Cf on its projected band, ASD) resolved to the "
           "deck's lines; see the Independent check note")


def deck_aspect(span_ft: float, depth_ft: float, limit: float, blocked: bool) -> tuple[Step, ...]:
    return (Step("L", "span of the deck between its resisting lines", span_ft, "ft"),
            Step("W", "depth of the deck across the wind", depth_ft, "ft"),
            Step("L/W", "span-to-depth ratio", span_ft / depth_ft, "", "L / W",
                 f"{num(span_ft)} / {num(depth_ft)}"),
            Step("(L/W)_max", f"largest ratio allowed, {'blocked' if blocked else 'unblocked'} "
                 "wood structural panel deck", limit, "", source="SDPWS Table 4.2.4"))


def deck_unit_shear(share: float, shear_lb: float, depth_ft: float, v_allow: float
                    ) -> tuple[Step, ...]:
    return (Step("V", "wind shear on the deck, worst direction", shear_lb, "lb",
                 source=_DECK_V),
            Step("s", "share of it the larger line reaction takes", share, ""),
            Step("v", "deck boundary unit shear", share * shear_lb / depth_ft, "plf",
                 "s V / W", f"{num(share)} x {num(shear_lb)} / {num(depth_ft)}"),
            Step("v_allow", "allowable unit shear of the deck's sheathing and nailing", v_allow,
                 "plf", source="the deck's authored SDPWS Table 4.2A/4.2C row, see References"))


def panel_unit_shear(worst: float, length_ft: float, v_allow: float, direction: str
                     ) -> tuple[Step, ...]:
    return (Step("V", f"wind shear the deck hands this wall ({direction}, the worse way)", worst,
                 "lb", source=_DECK_V),
            Step("L", "length of the shear panel along its wall", length_ft, "ft"),
            Step("v", "unit shear in the panel", worst / length_ft, "plf", "V / L",
                 f"{num(worst)} / {num(length_ft)}"),
            Step("v_allow", "allowable unit shear of the panel's sheathing and nailing", v_allow,
                 "plf", source="the wall's authored SDPWS Table 4.3A row, see References"))


def panel_aspect(height_ft: float, length_ft: float, limit: float) -> tuple[Step, ...]:
    return (Step("h", "height of the shear panel", height_ft, "ft"),
            Step("L", "length of the shear panel along its wall", length_ft, "ft"),
            Step("h/L", "height-to-length ratio", height_ft / length_ft, "", "h / L",
                 f"{num(height_ft)} / {num(length_ft)}"),
            Step("(h/L)_max", "largest ratio allowed for the sheathing", limit, "",
                 source="SDPWS Table 4.3.4"))


def panel_holdown(worst: float, height_ft: float, length_ft: float, capacity: float,
                  holdown: str) -> tuple[Step, ...]:
    tension = worst * height_ft / length_ft
    return (Step("V", "wind shear on the panel", worst, "lb", source=_DECK_V),
            Step("T", "tension in the end post from overturning, no dead load credited",
                 tension, "lb", "V h / L", f"{num(worst)} x {num(height_ft)} / {num(length_ft)}"),
            Step("T_allow", f"{holdown} published allowable uplift", capacity, "lb",
                 source="the hold-down's published table, see References"))


def boundary(share_lb: float, edge_ft: float, v_allow: float, wall: str, direction: str
             ) -> tuple[Step, ...]:
    return (Step("V_w", f"wind shear delivered to {wall} at 100% ({direction})", share_lb, "lb",
                 source=_DECK_V),
            Step("d", "length of deck boundary the shear enters along", edge_ft, "ft"),
            Step("v", "deck unit shear along that boundary", share_lb / edge_ft, "plf",
                 "V_w / d", f"{num(share_lb)} / {num(edge_ft)}"),
            Step("v_allow", "allowable unit shear of the deck's sheathing and nailing", v_allow,
                 "plf", source="the deck's authored SDPWS Table 4.2A row, see References"))


def open_front_depth(depth: float, limit: float) -> tuple[Step, ...]:
    return (Step("L'", "deck dimension normal to its open side", depth, "ft",
                 source="deck footprint"),
            Step("L'_max", "largest allowed for an open front", limit, "ft",
                 source="SDPWS-2015 §4.2.5.2"))


def open_front_aspect(depth: float, width: float, limit: float) -> tuple[Step, ...]:
    return (Step("L'", "deck dimension normal to its open side", depth, "ft",
                 source="deck footprint"),
            Step("W'", "deck dimension along its open side", width, "ft",
                 source="deck footprint"),
            Step("L'/W'", "open-front ratio", depth / width, "", "L' / W'",
                 f"{num(depth)} / {num(width)}"),
            Step("(L'/W')_max", "largest allowed, one-story structure", limit, "",
                 source="SDPWS-2015 §4.2.5.2"))


def joint_nailing(v_along: float, joint_len: float, v_allow: float, direction: str
                  ) -> tuple[Step, ...]:
    return (Step("V_a", f"wind shear along the joint ({direction})", v_along, "lb",
                 source=_DECK_V),
            Step("l_j", "length of the joint the last bay lands on the neighbour's frame",
                 joint_len, "ft", source="the joint straps' extent"),
            Step("v", "unit shear in the joint's boundary nailing", v_along / joint_len, "plf",
                 "V_a / l_j", f"{num(v_along)} / {num(joint_len)}"),
            Step("v_allow", "allowable unit shear of the deck's sheathing and nailing", v_allow,
                 "plf", source="the deck's authored SDPWS Table 4.2A row, see References"))
