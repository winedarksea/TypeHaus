"""The parts BETWEEN the deck and the lines that resist it — and the torsion nobody carried.

``lateral_system`` grades the deck and the panels. What stood between them, named and
ungraded, was the load path: the collector along each support line, the CONNECTION at each
end of it, the concrete under the hold-down, and the torsional term a rigid split leaves over.
This module computes those rows and hands them back; the record they land on is still one
item per roof, because they are one design (``lateral_system``'s own doctrine).

** A COLLECTOR'S MEMBER IS NEVER THE QUESTION. ** A 3-ply 2x12 dragging a few hundred pounds
of axial force is 0.007 ksi. The joint at its end is where a collector fails, so what is
graded here is the connection: the published interaction of the tie that holds it, at the
line reaction the deck actually delivers — with the torsional increment in it.

**Oracle.** ``houses/catlin/notes/north_entry_canopy_lateral.md`` §8c-§8g;
``tests/test_lateral_system_calcs.py`` reproduces it.
"""

from __future__ import annotations

from typing import Any

from typehaus.engineering.diaphragm_basis import Line
from typehaus.engineering.item import LimitState, Quantity
from typehaus.engineering.roof_moment import FrameCase
from typehaus.engineering.torsion import Torsion, load_resultant_ft, torsional_distribution

_M_PER_FT = 0.3048


def _lines(ctx: Any, case: FrameCase) -> list[Line]:
    """This case's lines, at the GROSS-column distribution the case's shares came from."""
    from typehaus.engineering.lateral_lines import column_lines, panel_line

    posts = {tag: ctx.plan.by_tag(tag) for tag in case.column_tags}
    lines: list[Line] = column_lines(ctx, posts, list(case.column_tags), case.axis, cracked=False)
    for wall_tag in case.panel_tags:
        wall = ctx.plan.by_tag(wall_tag)
        share = case.columns_governing.shares.get(wall_tag)
        if wall is None or share is None:
            continue
        line = panel_line(ctx, wall, case.axis, share * case.diaphragm_shear_lb)
        if line is not None:
            lines.append(line)
    return lines


def _footprint_centre_ft(roof: Any, axis: str) -> float | None:
    index = 0 if axis == "y" else 1
    values = [p[index] / _M_PER_FT for p in roof.footprint]
    return (min(values) + max(values)) / 2.0 if values else None


def torsion_for(ctx: Any, roof: Any, case: FrameCase,
                cases: list[FrameCase]) -> Torsion | None:
    """One case's torsional distribution, with the OTHER axis's lines in ``J``."""
    along = _lines(ctx, case)
    across = [line for other in cases if other.axis != case.axis
              for line in _lines(ctx, other)]
    centre = _footprint_centre_ft(roof, case.axis)
    if centre is None:
        return None
    stations = {line.tag: value for line in along
                if (value := (line.x_ft if case.axis == "y" else line.y_ft)) is not None}
    resultant = load_resultant_ft(case.top_shear_lb, centre, case.head_reactions, stations)
    if resultant is None:
        return None
    return torsional_distribution(case.axis, case.diaphragm_shear_lb, resultant,
                                  along, across)


def line_force_lb(torsion: Torsion | None, tag: str, fallback: float) -> float:
    """The line's graded force: its direct share plus a torsional INCREMENT, never a relief."""
    if torsion is None or tag not in torsion.direct_lb:
        return fallback
    return torsion.direct_lb[tag] + max(torsion.torsional_lb.get(tag, 0.0), 0.0)


def torsion_rows(torsions: dict[str, Torsion]) -> tuple[list[LimitState], list[Quantity],
                                                        list[str]]:
    """The stability row, the inputs and the note. Magnitudes ride on the collector rows."""
    states: list[LimitState] = []
    inputs: list[Quantity] = []
    notes: list[str] = []
    for axis, torsion in sorted(torsions.items()):
        direction = "N-S" if axis == "y" else "E-W"
        inputs += [Quantity(f"torsion_eccentricity_{axis}", torsion.eccentricity_ft, "ft",
                            0.01),
                   Quantity(f"torsion_moment_{axis}", torsion.moment_lb_ft, "lb-ft", 1.0)]
        states.append(LimitState(
            f"torsional stability, {direction}", 0.0 if torsion.stable else 1.0, 1.0, "",
            f"IBC 2018 §1604.4 with the moment term kept: {torsion.how}",
            is_detailing=True))
        worst = max(torsion.multipliers.values(), default=1.0)
        notes.append(
            f"TORSION, {direction}: {torsion.how} Each line's direct share is multiplied by "
            + ", ".join(f"{tag} {torsion.multipliers[tag]:.2f}x"
                        for tag in sorted(torsion.multipliers))
            + f" (worst {worst:.2f}x), and the lines running the other way take "
            + ", ".join(f"{tag} {abs(force):,.0f} lb"
                        for tag, force in sorted(torsion.across_lb.items()))
            + " as the couple that closes the free body.")
    return states, inputs, notes


def collector_rows(ctx: Any, roof: Any, cases: list[FrameCase],
                   torsions: dict[str, Torsion],
                   states: list[LimitState], notes: list[str],
                   inputs: list[Quantity]) -> None:
    """Every collector row this roof owes: the panel lines, the column heads, the strap line."""
    for case in cases:
        torsion = torsions.get(case.axis)
        for wall_tag in case.panel_tags:
            _panel_collector(ctx, roof, case, wall_tag, states)
        for column_tag in case.column_tags:
            _head_collector(ctx, case, torsion, column_tag, states, notes, inputs)
    _strap_line(ctx, roof, cases, torsions, states, notes, inputs)


def _panel_collector(ctx: Any, roof: Any, case: FrameCase, wall_tag: str,
                     states: list[LimitState]) -> None:
    """A panel that spans the deck's whole depth needs no drag strut, and this says so."""
    from typehaus.engineering.lateral_lines import _ends_ft

    wall = ctx.plan.by_tag(wall_tag)
    share = case.columns_governing.shares.get(wall_tag)
    ends = _ends_ft(ctx, wall) if wall is not None else None
    if ends is None or share is None or case.depth_ft <= 0.0:
        return
    index = 1 if case.axis == "y" else 0
    lo, hi = sorted((ends[0][index], ends[1][index]))
    roof_values = [p[index] / _M_PER_FT for p in roof.footprint]
    overlap = max(0.0, min(hi, max(roof_values)) - max(lo, min(roof_values)))
    drag_length = max(0.0, case.depth_ft - overlap)
    unit_shear = share * case.diaphragm_shear_lb / case.depth_ft
    states.append(LimitState(
        f"{wall_tag} collector (drag into the line)", case.depth_ft, max(overlap, 1e-9),
        "ft",
        f"the deck's {case.depth_ft:.3f}' of boundary on this line against "
        f"{overlap:.3f}' of panel under it, so the drag length is {drag_length:.3f}' and "
        f"the drag force {unit_shear:.1f} plf x {drag_length:.3f}' = "
        f"{unit_shear * drag_length:,.0f} lb — the panel's own top plate is the collector "
        f"over the length it covers",
        is_detailing=True))


def _head_collector(ctx: Any, case: FrameCase, torsion: Torsion | None, column_tag: str,
                    states: list[LimitState], notes: list[str],
                    inputs: list[Quantity]) -> None:
    """The collector's END CONNECTION at a cast column: the head tie's published interaction."""
    from typehaus.engineering.column_head_joint import _net_uplift
    from typehaus.engineering.pier_basis import cast_piers

    post = ctx.plan.by_tag(column_tag)
    connector = getattr(post, "head_connector", None)
    if connector is None or connector.lateral_lb is None or connector.uplift_lb is None:
        return
    rule = getattr(connector, "interaction_rule", None)
    if not rule:
        return
    direct = case.columns_governing.shares.get(column_tag, 0.0) * case.diaphragm_shear_lb
    force = line_force_lb(torsion, column_tag, direct)
    across = abs(torsion.across_lb.get(column_tag, 0.0)) if torsion is not None else 0.0
    pier = next((p for p in cast_piers(ctx) if p.tag == column_tag), None)
    if pier is None:
        return
    uplift = _net_uplift(ctx, pier, notes=[])
    if uplift is None:
        return
    share = 1 if connector.set_rated else connector.tie_count
    perpendicular = getattr(connector, "lateral_f2_lb", None) or connector.lateral_lb
    unity = (max(uplift, 0.0) / share / connector.uplift_lb
             + force / connector.lateral_lb + across / perpendicular)
    direction = "N-S" if case.axis == "y" else "E-W"
    inputs.append(Quantity(f"collector_reaction_{column_tag}_{case.axis}", force, "lb", 1.0))
    states.append(LimitState(
        f"{column_tag} collector end connection, {direction}", unity, 1.0, "",
        f"{rule}; {connector.tie} x{connector.tie_count}"
        f"{' (the rated set)' if connector.set_rated else ''}: uplift "
        f"{uplift:,.0f}/{share} / {connector.uplift_lb:,.0f} + in-plane {force:,.0f} / "
        f"{connector.lateral_lb:,.0f} + the torsional couple's {across:,.0f} / "
        f"{perpendicular:,.0f}. The in-plane force is this line's direct share "
        f"({direct:,.0f} lb) WITH its torsional increment; 0.6D + 0.6W"))


def _strap_line(ctx: Any, roof: Any, cases: list[FrameCase], torsions: dict[str, Torsion],
                states: list[LimitState], notes: list[str],
                inputs: list[Quantity]) -> None:
    """A support line with no member on it, collected by a tie line into a NEIGHBOURING roof.

    The canopy's north line is the case: the fourth truss was dropped, so nothing of this
    roof stands on the line its E-W reaction is delivered along, and what carries that force
    is the strap line tying this deck to the next roof's own gable frame. That crossing is a
    fact about the building and is printed, not hidden inside a passing row.
    """
    from typehaus.hardware.catalog import allowable_for_model
    from typehaus.model.enums import ConnectorKind

    ties = [e for e in ctx.plan.all_elements()
            if getattr(e, "kind", None) is ConnectorKind.TENSION_TIE
            and roof.tag in (getattr(e, "connects", ()) or ())
            and len(getattr(e, "connects", ()) or ()) > 1]
    if not ties:
        return
    allowable = allowable_for_model(ties[0].size or "")
    capacity = allowable.uplift_lb if allowable is not None else None
    xs = [t.position.xy_m[0] / _M_PER_FT for t in ties]
    ys = [t.position.xy_m[1] / _M_PER_FT for t in ties]
    length_ft = max(xs) - min(xs)
    line_y = sum(ys) / len(ys)
    case = next((c for c in cases if c.axis == "x"), None)
    if case is None or length_ft <= 0.0:
        return
    torsion = torsions.get("x")
    nearest = min(case.column_tags,
                  key=lambda tag: abs(_column_station(ctx, tag) - line_y),
                  default=None)
    if nearest is None:
        return
    direct = case.columns_governing.shares.get(nearest, 0.0) * case.diaphragm_shear_lb
    force = line_force_lb(torsion, nearest, direct)
    per_strap = force / len(ties)
    others = sorted({t for tie in ties for t in tie.connects if t != roof.tag})
    inputs.append(Quantity("collector_strap_line_lb", force, "lb", 1.0))
    if allowable is None or capacity is None:
        notes.append(
            f"THE E-W COLLECTOR AT THE {ties[0].tag.rsplit('-', 1)[0]} LINE IS NOT GRADED: "
            f"`{ties[0].size}` has no published allowable in this catalog.")
        return
    states.append(LimitState(
        f"{ties[0].size} strap line collector ({len(ties)} ties)", per_strap, capacity, "lb",
        f"{allowable.citation.split(':')[0]}; {force:,.0f} lb of E-W line reaction over "
        f"{length_ft:.1f}' = {force / length_ft:.1f} plf, {per_strap:.1f} lb per tie. "
        f"THE FORCE RUNS ALONG THE JOINT, not across it: the tabulated value is the STEEL "
        f"strength and the nail group behind it is direction-independent for a fastener "
        f"under 1/4in (NDS 12.3). {allowable.fasteners}"))
    notes.append(
        f"THE E-W COLLECTOR AT THIS LINE CROSSES INTO {', '.join(others)}. No member of "
        f"{roof.tag} stands on it, so the line reaction is collected by the "
        f"{len(ties)} {ties[0].size} tie(s) into the neighbouring roof's own frame — which "
        f"is the one direction in which this roof is not freestanding. Gravity still crosses "
        f"nowhere.")


def _column_station(ctx: Any, tag: str) -> float:
    post = ctx.plan.by_tag(tag)
    return post.position.xy_m[1] / _M_PER_FT if post is not None else 0.0
