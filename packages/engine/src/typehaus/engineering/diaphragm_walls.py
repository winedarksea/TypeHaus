"""Every delivery into one garage wall line, summed (integrated load-path review M9).

``diaphragm_delivery`` grades each delivery to a garage wall on its own row: the roof's
lever-rule share, the open front's couples, the screen-at-100% couple. The landing ties
deliver into the same walls (the collector strap along W-G-W, the HL angles into W-G-S) and
sat in no wall row. This module adds, per wall, the in-plane force of

* the canopy deck: the receiving share (lever rule, or the E-W share on the boundary wall),
  the E-W couple and the N-S couple over the far lines' spacing;
* the landing's ties: ``deck_tie``'s own distribution of its wind cases onto the joints at
  that wall, the along-wall component of each, worst sense, per wind direction;

and grades the sum as a unit shear on the wall's surplus and as an end tension at its
hold-down. One wind direction at a time (the worst); within it the garage-100% and
screen-100% canopy cases never act together either, and every delivery is added: a bound.
"""

from __future__ import annotations

from typing import Any

from typehaus.engineering.item import LimitState, Quantity

_M_PER_FT = 0.3048


def landing_in_plane(ctx: Any) -> dict[str, dict[str, float]]:
    """``wind axis -> {wall tag: lb}`` along that wall from every tied deck's joints, worst
    sense per wind axis."""
    from typehaus.engineering.deck_tie import (
        Capacity,
        _bearing_posts,
        _split,
        _tied_decks,
        capacity,
        carries_of,
        distribute,
    )
    from typehaus.engineering.deck_tie_basis import deck_wind, loads_on, wall_ties

    out: dict[str, dict[str, float]] = {}
    for deck in _tied_decks(ctx):
        joints = wall_ties(ctx, deck)
        caps = [capacity(j) for j in joints]
        if not joints or not all(isinstance(c, Capacity) for c in caps):
            continue
        anchors = [ctx.plan.by_tag(t) for t in sorted(_bearing_posts(ctx, deck))]
        wind = deck_wind(ctx, deck, anchors) if anchors else None
        if wind is None:
            continue
        cases, _guards = loads_on(ctx, deck, wind)
        for axis, loads in cases.items():
            worst: dict[str, float] = {}
            for sign in (1.0, -1.0):
                forces = distribute(joints, loads, sign, carries_of(joints, caps))
                for joint, force in zip(joints, forces, strict=False):
                    along, _across = (abs(v) for v in _split(joint, force))
                    worst[joint.wall] = worst.get(joint.wall, 0.0) + along
                if sign == 1.0:
                    first, worst = worst, {}
            here = out.setdefault(axis, {})
            for wall in set(first) | set(worst):
                here[wall] = here.get(wall, 0.0) + max(first.get(wall, 0.0),
                                                       worst.get(wall, 0.0))
    return out


def wall_sum_rows(ctx: Any, rows: Any, lines: tuple, far_walls: list[Any], along: str) -> None:
    """The summed delivered shear and end tension for every receiving wall."""
    from typehaus.engineering.diaphragm_delivery import _overturning, _surplus

    landing = landing_in_plane(ctx)
    index = 0 if along == "x" else 1
    spacing = None
    if len(far_walls) >= 2:
        at = sorted(sum(ctx.plan.by_tag(getattr(w, n)).position.xy_m[index]
                        for n in ("start_node", "end_node")) / 2.0 / _M_PER_FT
                    for w in far_walls)
        spacing = at[-1] - at[0]
    inputs = {q.name: q.value for q in rows.inputs}
    far_tags = {w.tag for w in far_walls}
    for line in lines:
        wall = ctx.plan.by_tag(line.wall)
        reading = _surplus(ctx, rows, line.wall)
        if wall is None or reading is None:
            continue
        _tag, provided, required = reading
        surplus = provided - required
        receiving = inputs.get(f"receiving_{line.wall}_lb", 0.0)
        on_far = line.wall in far_tags
        # One wind direction at a time: N-S wind loads the N-S walls with the deck's lever-rule
        # share, the screen-at-100% couple and the landing's N-S case; E-W wind loads the
        # boundary wall with the deck's E-W share and the far walls with the E-W couple. Each
        # case adds every delivery in it; the worst case is graded.
        cases = {
            "N-S wind": {"canopy deck share": receiving if on_far else 0.0,
                         "N-S couple": (inputs.get("joint_couple_ns_lb_ft", 0.0) / spacing
                                        if on_far and spacing else 0.0),
                         "landing ties": landing.get("y", {}).get(line.wall, 0.0)},
            "E-W wind": {"canopy deck share": 0.0 if on_far else receiving,
                         "E-W couple": (inputs.get("joint_couple_lb_ft", 0.0) / spacing
                                        if on_far and spacing else 0.0),
                         "landing ties": landing.get("x", {}).get(line.wall, 0.0)},
        }
        name, parts = max(cases.items(), key=lambda kv: sum(kv[1].values()))
        total = sum(parts.values())
        if total <= 0.0 or surplus <= 0.0:
            continue
        text = f"{name}: " + " + ".join(f"{k} {v:,.1f}" for k, v in parts.items() if v)
        rows.inputs.append(Quantity(f"summed_{line.wall}_lb", total, "lb", 1.0))
        rows.states.append(LimitState(
            f"{line.wall} delivered shear, all deliveries summed", total / surplus,
            line.unit_shear_asd_plf, "plf",
            f"{line.source}; {text} = {total:,.1f} lb in plane on the {surplus:.3f}' of "
            f"surplus; the worst wind direction, every delivery in it added (the garage-100% and "
            f"screen-100% canopy cases too): a conservative bound"))
        _overturning(ctx, rows, wall, total, provided, "all deliveries summed", required=False)
