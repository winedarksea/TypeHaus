"""The N-S chord force and the end-strap couple of a canopy that delivers across a joint.

The double envelope grades the screen at 100% of the across-joint shear ``V``. That is in
equilibrium only if the joint's straps hand back a COUPLE: ``V`` acts through the deck's
resultant, the screen resists it on its own line, and the offset between the two is a moment
the end straps carry as a pair of opposite N-S forces ``F = V (x_V - x_screen) / L_strap``.
The same load makes the deck a deep beam spanning the strap line with the first and last
truss as its chords, ``T = V L_strap / (8 d)`` with ``d`` the CHORDS' own separation (the
drawing's, not the deck's depth). ``T`` is printed for the truss order and not graded: a
truss chord's capacity is the fabricator's chart.

* **End straps** — ``F`` plus the open front's E-W chord force, added linearly, against the
  strap's installed rating (the E-W twin is ``open_front``'s "chord force + across share").
* **Receiving walls** — the couple ``V (x_V - x_screen)`` over the far lines' spacing, on
  each line's surplus, the N-S twin of ``open_front._far_lines``.

**Oracle.** ``houses/catlin/notes/north_entry_canopy_lateral.md`` §8b.
"""

from __future__ import annotations

from typing import Any

from typehaus.engineering import delivery_working as DW
from typehaus.engineering.canopy_service import DRY_UNDER_ROOFING
from typehaus.engineering.item import LimitState, Quantity

_M_PER_FT = 0.3048


def chord_rows(ctx: Any, rows: Any, element: Any, resolved_roof: Any, joints: list[Any],
               along: str, resultant_across_ft: float | None, far: list[tuple[Any, Any]],
               readings: dict) -> None:
    """Append the chord-force input, the end-strap couple row and the far-wall couple rows."""
    from typehaus.engineering.lateral_lines import panel_runs_along, panels_under

    across = "y" if along == "x" else "x"
    v = next((q.value for q in rows.inputs if q.name == f"delivered_shear_{across}"), 0.0)
    along_i, across_i = (0, 1) if along == "x" else (1, 0)
    stations = sorted(j.position.xy_m[along_i] / _M_PER_FT for j in joints)
    strap_line = stations[-1] - stations[0]
    truss_at = sorted({m.p0[across_i] / _M_PER_FT for m in resolved_roof.members
                       if m.category == "roof_truss"})
    if v <= 0.0 or strap_line <= 0.0:
        return
    if len(truss_at) < 2:
        rows.missing.append(f"two trusses on {element.tag} to be the deck's chords: the "
                            f"{across.upper()}-wind chord force is V L / (8 d) over their spacing")
        return
    spacing = truss_at[-1] - truss_at[0]
    chord = v * strap_line / (8.0 * spacing)
    rows.inputs.append(Quantity(f"chord_force_{across}", chord, "lb", 1.0))
    rows.notes.append(
        f"N-S CHORD FORCE FOR THE TRUSS ORDER: the first and last canopy truss (y "
        f"{truss_at[0]:.3f}' and {truss_at[-1]:.3f}', {spacing:.3f}' apart) are the deck's "
        f"chords, T = V L / (8 d) = {v:,.1f} x {strap_line:.3f} / (8 x {spacing:.3f}) = "
        f"{chord:,.1f} lb, tension in one chord and compression in the other, on top of the "
        f"gravity case, with the peak splice carrying it in tension. It is on EVERY canopy "
        f"truss so no mark can be the wrong one; nothing here grades a truss chord.")

    screens = [w for w in panels_under(ctx, resolved_roof) if panel_runs_along(ctx, w, across)]
    if len(screens) != 1 or resultant_across_ft is None:
        return
    ends = [ctx.plan.by_tag(getattr(screens[0], n)) for n in ("start_node", "end_node")]
    screen_at = sum(e.position.xy_m[along_i] for e in ends) / 2.0 / _M_PER_FT
    lever = abs(resultant_across_ft - screen_at)
    couple = v * lever
    pair = couple / strap_line
    rows.inputs.append(Quantity("joint_couple_ns_lb_ft", couple, "lb-ft", 1.0))
    capacity = rows.strap_capacity_lb
    chord_ew = next((q.value for q in rows.inputs if q.name == "chord_force_open_front_lb"), 0.0)
    centre = sum(stations) / len(stations)
    second = sum((x - centre) ** 2 for x in stations)
    linear = couple * max(abs(x - centre) for x in stations) / second if second else pair
    if capacity:
        ends_j = sorted(joints, key=lambda j: j.position.xy_m[along_i])
        rows.states.append(LimitState(
            f"{joints[0].size} end straps, N-S couple + chord", pair + chord_ew, capacity, "lb",
            f"{screens[0].tag} at 100% of the N-S {v:,.1f} lb stands {lever:.3f}' off the "
            f"deck's resultant, M = {couple:,.1f} lb-ft closed by a pair of N-S forces over "
            f"the {strap_line:.3f}' strap line, F = {pair:,.1f} lb at {ends_j[0].tag} and "
            f"{ends_j[-1].tag}, plus the E-W chord force {chord_ew:,.1f} lb added LINEARLY "
            f"(a conservative combination of the separate wind cases); reduced installed "
            f"nail schedule. A CONSERVATIVE BOUND: an elastic distribution of the couple over "
            f"all {len(stations)} straps puts {linear:,.1f} lb on an end strap "
            f"({(linear + chord_ew) / capacity:.2f} with the chord force); the end-strap pair "
            f"is kept because it needs no stiffness judgement across the joint. The straps are "
            f"{DRY_UNDER_ROOFING} (C_M 1.0); read at wet service (0.70) this row is "
            f"{(pair + chord_ew) / (capacity * 0.70):.2f}", **DW.cw(DW.WIND_ASD),
            working=DW.end_strap_couple(v, lever, couple, strap_line, pair, chord_ew, capacity,
                                        element.diaphragm.delivers_to, rows.strap_rated_lb)))
    placed = []
    for wall, line in far:
        e = [ctx.plan.by_tag(getattr(wall, n)) for n in ("start_node", "end_node")]
        placed.append((sum(p.position.xy_m[along_i] for p in e) / 2.0 / _M_PER_FT, wall, line))
    placed.sort(key=lambda row: row[0])
    if len(placed) < 2 or not all(panel_runs_along(ctx, w, across) for _x, w, _l in placed):
        return
    spacing_far = placed[-1][0] - placed[0][0]
    if spacing_far <= 0.0:
        return
    force = couple / spacing_far
    for _x, _wall, line in (placed[0], placed[-1]):
        reading = readings.get(line.wall)
        if reading is None:
            continue
        surplus = reading[1] - reading[2]
        rows.states.append(LimitState(
            f"{line.wall} joint couple, N-S case", force / surplus, line.unit_shear_asd_plf,
            "plf", f"{line.source}; M / d = {couple:,.1f} / {spacing_far:.3f}' = "
                   f"{force:,.1f} lb on the {surplus:.3f}' surplus — the screen-at-100% "
                   f"case's couple, which the joint hands on rather than closes",
            **DW.cw(DW.WIND_ASD),
            working=DW.couple_line(couple, spacing_far, force, reading[1], reading[2], surplus,
                                   force / surplus, line.unit_shear_asd_plf, line.wall,
                                   "N-S")))
