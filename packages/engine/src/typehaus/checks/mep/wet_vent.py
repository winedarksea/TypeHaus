"""Wet-vent grading for ``mep.trap_arm_developed`` — MN 4714 (UPC) 908, pure of the model.

A child drain joining the arm's path that carries its own vent tee may end the arm only if
the wet vent is legal. The section is that child (tee to join) plus the parent from the join
downstream. Data and sources: ``takeoff.plumbing_calc.WET_VENT_*``;
``houses/catlin/notes/wet_vent_basis.md`` works a case by hand.

Plain data in: ``fx`` maps fixture tag -> ``(leaf drain run, DFU, plan symbol, storey)``;
``parents`` maps a run to ``(parent run, segment index, t)`` where its end stands.
"""

from __future__ import annotations

import math

from typehaus.quantities import M_PER_IN
from typehaus.takeoff.plumbing_calc import (
    BATHROOM_GROUP_SYMBOLS,
    DRAIN_BRANCH_CAPACITY_DFU,
    WET_VENT_HORIZONTAL_MIN_IN,
    WET_VENT_MIN_IN,
    WET_VENT_VERTICAL_MAX_FIXTURES,
    WET_VENT_VERTICAL_MAX_IN,
    WET_VENT_VERTICAL_UPPER_DFU_MAX,
    required_drain_diameter_in,
)

Fx = tuple[str, float, str, str]
Order = tuple[int, float]  # (segment, t) where a run enters another; (-1, 0) = starts there


def _entries(leaf: str, parents: dict[str, tuple]) -> dict[str, Order]:
    """Every run this fixture's waste crosses, with where it enters each."""
    out: dict[str, Order] = {leaf: (-1, 0.0)}
    run = leaf
    while run in parents and parents[run][0] not in out:
        tag, i, t = parents[run]
        out[tag] = (i, t)
        run = tag
    return out


def _is_vertical(pts: list) -> bool:
    """UPC "vertical": 45° or steeper overall, so rise ≥ plan run."""
    rise = sum(abs(b[2] - a[2]) for a, b in zip(pts, pts[1:], strict=False))
    plan = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:], strict=False))
    return rise > plan


def _length_in(pts: list) -> float:
    return sum(math.dist(a, b) for a, b in zip(pts, pts[1:], strict=False)) / M_PER_IN


def _next_size(size_in: float) -> float:
    return next((s for s, _ in DRAIN_BRANCH_CAPACITY_DFU if s > size_in + 1e-6), size_in)


def _size_in(radius_m: float) -> float:
    return round(2.0 * radius_m / M_PER_IN, 2)


def grade_wet_vent(child: str, parent: str, join: Order, drains: dict[str, list],
                   radii: dict[str, float], parents: dict[str, tuple],
                   fx: dict[str, Fx], arm_fx: str) -> tuple[bool, str]:
    """``(legal, why)`` for ``child`` wet-venting ``arm_fx`` where it joins ``parent``."""
    vertical = _is_vertical(drains[child])
    via_child: dict[str, Order] = {}
    via_parent: dict[str, Order] = {}
    for tag, (leaf, *_rest) in fx.items():
        ent = _entries(leaf, parents)
        if child in ent:
            via_child[tag] = ent[child]
        elif parent in ent:
            via_parent[tag] = ent[parent]
    members = {**via_child, **({} if vertical else via_parent)}
    dfu = sum(fx[t][1] for t in members)
    d_child, d_parent = _size_in(radii[child]), _size_in(radii[parent])
    bad: list[str] = []
    if vertical:
        sec = f"908.1 vertical, Ø{d_child:g}\" {_length_in(drains[child]):.0f}\" long"
        if arm_fx not in via_child:
            bad.append(f"{arm_fx} does not discharge into the vertical wet vent")
        if len(members) > WET_VENT_VERTICAL_MAX_FIXTURES:
            bad.append(f"{len(members)} fixtures vent through it (max "
                       f"{WET_VENT_VERTICAL_MAX_FIXTURES})")
        if len({fx[t][3] for t in members}) > 1:
            bad.append("fixtures on more than one storey")
        if _length_in(drains[child]) > WET_VENT_VERTICAL_MAX_IN:
            bad.append(f"developed {_length_in(drains[child]):.0f}\" over "
                       f"{WET_VENT_VERTICAL_MAX_IN:.0f}\"")
        lowest = max(members, key=lambda t: via_child[t], default=None)
        big = [t for t in members if t != lowest and fx[t][1] > WET_VENT_VERTICAL_UPPER_DFU_MAX]
        if big:
            bad.append(f"upper fixture {big[0]} is over {WET_VENT_VERTICAL_UPPER_DFU_MAX:g} DFU")
        # Min waste of the upper fixture: its own authored trap-arm run stands in for it.
        waste = max((_size_in(radii[fx[t][0]]) for t in members if t != lowest), default=0.0)
        need = max(_next_size(waste), _next_size(required_drain_diameter_in(dfu) or 0.0),
                   WET_VENT_MIN_IN)
        if d_child < need - 1e-6:
            bad.append(f"Ø{d_child:g}\" under the {need:g}\" 908.1 asks for {dfu:g} DFU")
    else:
        need = next(m for lim, m in WET_VENT_HORIZONTAL_MIN_IN if dfu <= lim + 1e-9)
        sec = f"908.2 horizontal, {dfu:g} DFU, Ø{min(d_child, d_parent):g}\""
        if arm_fx not in members:
            bad.append(f"{arm_fx} does not discharge into it")
        if min(d_child, d_parent) < need - 1e-6:
            bad.append(f"Ø{min(d_child, d_parent):g}\" under the {need:g}\" it needs for "
                       f"{dfu:g} DFU, whole length (PB0225)")
        off = sorted(t for t in members if fx[t][2] not in BATHROOM_GROUP_SYMBOLS)
        if off:
            bad.append(f"{off[0]} is not a bathroom-group fixture")
        if len({fx[t][3] for t in members}) > 1:
            bad.append("fixtures on more than one floor")
        upstream = [t for t in members if t not in via_child and via_parent[t] < join]
        if len(upstream) > 1:
            bad.append(f"{len(upstream)} wet-vented drains ({', '.join(sorted(upstream))}) "
                       "discharge upstream of the dry-vent connection (max 1)")
        at = {**dict.fromkeys(via_child, join), **via_parent}
        at = {t: o for t, o in at.items() if t in members}
        first = [t for t in at if fx[t][2].startswith("toilet")
                 and any(o > at[t] for o in at.values())]
        if first:
            bad.append(f"{first[0]} discharges before other connections; 908.2.4 puts a "
                       "water closet downstream of all")
    return (not bad), (f"{sec}: " + ("; ".join(bad) if bad else f"ok for {dfu:g} DFU"))
