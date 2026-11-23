"""Every delivery into one garage wall line, summed (integrated load-path review M9).

``diaphragm_delivery`` grades each delivery to a garage wall on its own row: the roof's
lever-rule share, the open front's couples, the screen-at-100% couple. The landing ties
deliver into the same walls (the collector strap along W-G-W, the HL angles into W-G-S) and
sat in no wall row. This module adds, per wall, the in-plane force of

* the canopy deck: the receiving share (lever rule, or the E-W share on the boundary wall),
  the E-W couple and the N-S couple over the far lines' spacing;
* the landing's ties: ``deck_tie``'s exported worst force along each wall (and across it,
  which the roof carries on to the perpendicular walls);

and grades the sum as a unit shear on the wall's surplus and as an end tension at its
hold-down. One wind direction at a time (the worst); within it the garage-100% and
screen-100% canopy cases never act together either, and every delivery is added: a bound.
"""

from __future__ import annotations

from typing import Any

from typehaus.engineering.item import LimitState, Quantity

_M_PER_FT = 0.3048


def landing_deliveries(ctx: Any) -> tuple[dict[str, float], dict[str, float], dict[str, float]]:
    """``(along, across, x_ft)`` per tied wall: ``deck_tie``'s exported worst force the ties put
    along and across it (``delivered_along_<wall>`` / ``delivered_across_<wall>``), and the
    mean plan x of the joints on it (where an across force enters the roof)."""
    from typehaus.engineering import deck_tie
    from typehaus.engineering.deck_tie_basis import wall_ties

    along: dict[str, float] = {}
    across: dict[str, float] = {}
    at: dict[str, float] = {}
    for deck in deck_tie._tied_decks(ctx):
        for joint in wall_ties(ctx, deck):
            at.setdefault(joint.wall, joint.x_ft)
    for record in deck_tie.compute(ctx):
        for q in record.inputs:
            for prefix, into in (("delivered_along_", along), ("delivered_across_", across)):
                if q.name.startswith(prefix):
                    into[q.name.removeprefix(prefix)] = q.value
    return along, across, at


def wall_sum_rows(ctx: Any, rows: Any, lines: tuple, far_walls: list[Any], along: str) -> None:
    """The summed delivered shear and end tension for every receiving wall."""
    from typehaus.engineering.diaphragm_delivery import _overturning, _surplus

    land_along, land_across, land_x = landing_deliveries(ctx)
    index = 0 if along == "x" else 1
    spacing = None
    if len(far_walls) >= 2:
        at = sorted(sum(ctx.plan.by_tag(getattr(w, n)).position.xy_m[index]
                        for n in ("start_node", "end_node")) / 2.0 / _M_PER_FT
                    for w in far_walls)
        spacing = at[-1] - at[0]
    inputs = {q.name: q.value for q in rows.inputs}
    far_tags = {w.tag for w in far_walls}
    far_x = {w.tag: sum(ctx.plan.by_tag(getattr(w, n)).position.xy_m[index]
                        for n in ("start_node", "end_node")) / 2.0 / _M_PER_FT
             for w in far_walls}
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
        # An across force at a tied wall enters the garage roof and leaves by the walls
        # perpendicular to it: a N-S force on an E-W wall splits to the far N-S walls by the
        # lever rule on where it entered; an E-W force on a N-S wall goes to the boundary wall.
        to_far = 0.0
        if on_far and len(far_walls) >= 2:
            xs = sorted(far_x.values())
            for tag, force in land_across.items():
                if tag not in far_tags and tag in land_x and xs[-1] > xs[0]:
                    toward = xs[-1] - land_x[tag] if far_x[line.wall] == xs[0] else (
                        land_x[tag] - xs[0])
                    to_far += force * max(0.0, min(1.0, toward / (xs[-1] - xs[0])))
        to_boundary = (0.0 if on_far else sum(f for t, f in land_across.items() if t in far_tags))
        cases = {
            "N-S wind": {"canopy deck share": receiving if on_far else 0.0,
                         "N-S couple": (inputs.get("joint_couple_ns_lb_ft", 0.0) / spacing
                                        if on_far and spacing else 0.0),
                         "landing ties along": land_along.get(line.wall, 0.0),
                         "landing ties across the E-W wall, by the roof": to_far},
            "E-W wind": {"canopy deck share": 0.0 if on_far else receiving,
                         "E-W couple": (inputs.get("joint_couple_lb_ft", 0.0) / spacing
                                        if on_far and spacing else 0.0),
                         "landing ties along": land_along.get(line.wall, 0.0),
                         "landing ties across the N-S walls, by the roof": to_boundary},
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
