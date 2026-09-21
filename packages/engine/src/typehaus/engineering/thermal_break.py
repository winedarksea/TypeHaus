"""Bars tying two pours across an insulating break — graded as a RESERVE, never a design.

``thermal_break_transfer/<Dowel tag>``. **The design shear across the break is zero by
construction**: the court holds its own thrust (``retaining_system``) and the board exists to
keep the house out of that free body. A ``demand = 0`` row would print d/c 0.00 and read as a
design, so the independence argument is a note, and what is graded is what the tie and the
board would have to survive:

* fresh-concrete pressure on the board — ACI 347R-14, capped at full liquid head ``w·h``;
* board flotation — Archimedes on the board, against the bars' bearing on the foam;
* thermal movement the board takes — ``α_c`` × (site hot − the concrete's set temperature,
  bounded below by ACI 306R's 50 °F) over the court's full run, against the closure at the
  long-term allowable stress, ``t · (foam_psi / 3) / foam_modulus_psi`` (any board: XPS or
  mineral wool, on the rated stress and modulus its sheet publishes);
* dowel shear reserve — ``retaining_system``'s governing per-footing shortfall at 1.6H, shared
  by bar count across every break reaching that court, against
  ``min(0.75 V_bar, 0.55 T_u d / 4t)`` per bar (shear, or rupture in double curvature over
  the gap);
* differential settlement — the court stem's own bearing over ``SubgradeModulus.k_v_pci``
  (measured or a presumed published row), against the bars' rupture drift over the gap,
  ``φ (T_u d / 8) t² / 6EI``.

A row over its capacity makes the item OVER even while an input is still missing, as on
the other kinds: an INCOMPLETE would hide a graded shortfall behind an open question.

Oracle: ``houses/catlin/notes/sunken_garden_court_free_body.md`` §11, worked by hand first.
"""

from __future__ import annotations

import math

from typehaus.engineering.item import (
    EngineeringRecord,
    LimitState,
    Oracle,
    Quantity,
    Status,
    item_id,
)
from typehaus.engineering.registry import EngineeringContext, calc, keys, oracled_by
from typehaus.engineering.retaining_basis import EARTH_PRESSURE_LOAD_FACTOR
from typehaus.engineering.retaining_system import footing_shortfalls

KIND = "thermal_break_transfer"
BASIS = "ACI 347R-14 (fresh-concrete pressure); ACI 440.11-22 (GFRP bar); IRC R404.4 loop"
#: Bumped whenever the arithmetic below changes — it rides in the fingerprint.
BASIS_VERSION = "3"

#: ACI 347R-14 unit weight of fresh concrete, pcf — the ``w`` in ``p = w·h``.
CONCRETE_PCF = 150.0
#: Coefficient of thermal expansion, normal-weight concrete, per °F (PCA average).
ALPHA_C_PER_F = 5.5e-6
#: ACI 440.11-22 strength reduction: shear, and FRP rupture (tension-controlled).
PHI_SHEAR = 0.75
PHI_RUPTURE = 0.55
#: ACI 306R-16 Table 3.1: minimum as-placed concrete temperature, 12"-36" section, °F — the
#: lowest set temperature, so the largest closing range.
MIN_SET_TEMP_F = 50.0
#: Sustained-stress factor against creep: a board held closed for a season may take a third
#: of its short-term rating (the XPS maker's "3:1 for static loads"). Kept for mineral wool,
#: whose sheets publish no creep figure at all (free body §11c).
FOAM_CREEP_FACTOR = 3.0

SETTLEMENT_MISSING = (
    "`Site.lateral_subgrade_modulus.k_v_pci` — a vertical subgrade modulus "
    "(SubgradeModulus.k_v_pci, a strip footing at its real width), measured or a presumed "
    "published row; differential settlement across the break has no demand without it")

_IN_PER_M = 1.0 / 0.0254

oracled_by(KIND, Oracle(note="sunken_garden_court_free_body.md", section="§11",
                        test="tests/test_thermal_break.py"))


def _dowels(ctx: EngineeringContext) -> list:
    from typehaus.model.structure import Dowel

    return sorted((d for d in ctx.plan.all_elements()
                   if isinstance(d, Dowel) and d.foam_thickness is not None),
                  key=lambda d: d.tag)


@keys(KIND)
def enumerate_breaks(ctx: EngineeringContext) -> list[str]:
    """Every ``Dowel`` carrying a foam block — a structural tie across a deliberate break.

    A dowel with no block is an ordinary pour-joint tie within one structure and needs no
    item; one with a block holds two structures together THROUGH an insulator put there to
    keep them apart.
    """
    return [d.tag for d in _dowels(ctx)]


def _structure(ctx: EngineeringContext, tag: str) -> set[str]:
    """Tags of the cast walls and beams node-connected to ``tag`` (a Footing reads through
    ``under``) — one structure, which is what a break separates."""
    from typehaus.model.structure import Footing, FoundationWall
    from typehaus.resolve.assembly_material import is_cast_beam

    start = ctx.plan.by_tag(tag)
    if isinstance(start, Footing):
        start = ctx.plan.by_tag(start.under)
    if start is None or not getattr(start, "start_node", None):
        return set()
    pool = [e for e in ctx.plan.all_elements()
            if (isinstance(e, FoundationWall) or is_cast_beam(ctx.plan, e))
            and e.start_node and e.end_node]
    seen, nodes, grew = {start.tag}, {start.start_node, start.end_node}, True
    while grew:
        grew = False
        for e in pool:
            if e.tag not in seen and ({e.start_node, e.end_node} & nodes):
                seen.add(e.tag)
                nodes |= {e.start_node, e.end_node}
                grew = True
    return seen


def _board(ctx: EngineeringContext, dowel):
    """The resolved foam block: ``(t_in, h_in, length_in, bottom_in, top_in, bbox)``."""
    solid = next((s for s in ctx.model.solids
                  if s.tag == f"{dowel.tag}-FOAM" and s.category == "thermal_break"), None)
    if solid is None:
        return None
    xs = [p[0] for p in solid.outline]
    ys = [p[1] for p in solid.outline]
    dx, dy = (max(xs) - min(xs)) * _IN_PER_M, (max(ys) - min(ys)) * _IN_PER_M
    t_in, length_in = (dy, dx) if dowel.axis == "y" else (dx, dy)
    return (t_in, (solid.z1_m - solid.z0_m) * _IN_PER_M, length_in,
            solid.z0_m * _IN_PER_M, solid.z1_m * _IN_PER_M,
            (min(xs), min(ys), max(xs), max(ys)))


def _stacked_on(ctx: EngineeringContext, dowel, board) -> str | None:
    """The break block this board stands on, if any — then no face of it is under the pour."""
    *_, bottom_in, _top, (x0, y0, x1, y1) = board
    for other in _dowels(ctx):
        if other.tag == dowel.tag:
            continue
        below = _board(ctx, other)
        if below is None or abs(below[4] - bottom_in) > 1e-3:
            continue
        bx0, by0, bx1, by1 = below[5]
        if bx0 < x1 and x0 < bx1 and by0 < y1 and y0 < by1:
            return other.tag
    return None


def _court_side(ctx, dowel, loops) -> tuple[str, set[str]] | None:
    """``(loop ref, that side's structure)`` — the side of the break a retaining loop is on."""
    for tag in dowel.connects:
        structure = _structure(ctx, tag)
        for ref, by_pcf in loops.items():
            members = set(next(iter(by_pcf.values()), {}))
            if structure & (members | {ref}):
                return ref, structure
    return None


def _run_in(ctx: EngineeringContext, dowel, structure: set[str]) -> float:
    """The court's run along the bar axis, from the break to its farthest wall axis point."""
    ax = 1 if dowel.axis == "y" else 0
    origin = dowel.position.xy_m[ax]
    far = max((abs(p[ax] - origin) for w in ctx.model.walls if w.tag in structure
               for p in w.axis), default=0.0)
    return far * _IN_PER_M


def _top_in(ctx: EngineeringContext, dowel) -> float | None:
    tops = [e.top_elevation.inches for tag in dowel.connects
            for e in map(ctx.plan.by_tag, _structure(ctx, tag))
            if getattr(e, "top_elevation", None) is not None]
    return max(tops) if tops else None


@calc(KIND)
def compute(ctx: EngineeringContext) -> list[EngineeringRecord]:
    loops = footing_shortfalls(ctx)
    breaks = _dowels(ctx)
    # Every break reaching a court shares its reserve by bar count: identical bars across one
    # gap carry equal shares. Keyed by loop ref.
    bars_on: dict[str, int] = {}
    sides = {}
    for dowel in breaks:
        sides[dowel.tag] = _court_side(ctx, dowel, loops)
        if sides[dowel.tag] is not None:
            ref = sides[dowel.tag][0]
            bars_on[ref] = bars_on.get(ref, 0) + dowel.count
    return [_one(ctx, d, loops, sides[d.tag], bars_on) for d in breaks]


def _one(ctx, dowel, loops, side, bars_on) -> EngineeringRecord:  # noqa: C901
    tags = tuple(dict.fromkeys((dowel.tag, *dowel.connects)))
    states: list[LimitState] = []
    missing: list[str] = []
    notes: list[str] = [
        "THE DESIGN SHEAR ACROSS THIS BREAK IS ZERO BY CONSTRUCTION, and no row grades it: "
        "the court closes its own free body (`retaining_system`) and the board keeps the "
        "house out of it. Every row below is a RESERVE or the board's own survival.",
    ]
    inputs = [Quantity("count", dowel.count, "", None),
              Quantity("diameter", dowel.diameter.inches, "in", 0.001),
              Quantity("foam_psi", dowel.foam_psi, "psi", 0.1)]
    board = _board(ctx, dowel)
    if board is None:
        missing.append(f"a resolved foam block on {dowel.tag}")
        return _record(dowel, tags, states, missing, notes, inputs)
    t_in, h_in, length_in, bottom_in, _top, _bbox = board
    inputs += [Quantity("board_t", t_in, "in", 0.01), Quantity("board_h", h_in, "in", 0.01),
               Quantity("board_L", length_in, "in", 0.01)]

    # 11a — fresh-concrete pressure, capped at w·h from the highest pour top it touches.
    top_in = _top_in(ctx, dowel)
    if top_in is None:
        missing.append(f"a top elevation on the structures {dowel.tag} connects")
    else:
        head_ft = (top_in - bottom_in) / 12.0
        pressure_psi = CONCRETE_PCF * head_ft / 144.0
        inputs.append(Quantity("pour_head", head_ft, "ft", 0.01))
        states.append(LimitState(
            "fresh-concrete pressure", pressure_psi, dowel.foam_psi, "psi",
            f"ACI 347R-14 lateral pressure capped at wh — {CONCRETE_PCF:.0f} pcf x "
            f"{head_ft:.3f}' of head, monolithic to the top; vs the board's rated "
            f"{dowel.foam_psi:.0f} psi"))

    # 11b — flotation; a board standing on another block has no face under the pour.
    below = _stacked_on(ctx, dowel, board)
    if below is not None:
        notes.append(f"NO FLOTATION ROW: this board stands on {below}'s, so no face of it is "
                     f"under the pour. The row is omitted rather than graded at zero.")
    else:
        buoyancy_lb = CONCRETE_PCF * t_in * h_in * length_in / 1728.0
        bearing_lb = dowel.foam_psi * dowel.diameter.inches * t_in
        states.append(LimitState(
            "board flotation", buoyancy_lb, dowel.count * bearing_lb, "lb",
            f"Archimedes at {CONCRETE_PCF:.0f} pcf, foam weight neglected; restraint "
            f"{dowel.count} bars x {bearing_lb:.0f} lb foam bearing "
            f"({dowel.foam_psi:.0f} psi x {dowel.diameter.inches:.3f}\" x {t_in:.2f}\")"))

    # 11c/11d need the court side of the break.
    if side is None:
        missing.append("a verified retaining loop (`base_restraint_ref`) on one side of the "
                       "break — the movement row's run and the reserve row's shortfall are "
                       "both read off it")
    else:
        ref, structure = side
        _movement(ctx, dowel, structure, t_in, states, missing, inputs)
        _reserve(dowel, ref, loops[ref], bars_on[ref], t_in, states, missing, inputs, notes)
        _settlement(ctx, dowel, structure, t_in, states, missing, inputs, notes)
    notes.append(
        "NOT GRADED: joint OPENING under contraction (bonded bars cannot stretch the "
        "movement over the gap — they debond, rupture or drag the court); placement impact "
        "and racking of the board; friction on the cured face, which would help; ACI "
        "440.11's environmental reduction on the bar values; the bars' development into "
        "either pour; the board's continuity along the joint; and the bracing that holds "
        "the board in position during the pour. What the structural engineer of record "
        "still owes, on the GFRP maker's published bond and modulus data (the deferral's "
        "deliverable): a stated design shear across each break, the differential "
        "settlement on a report's k_v in place of a presumed one, "
        "the bar size, count and embedment that carry them, and that bracing — for S-100's "
        "thermal-break detail and the pour-sequence hold point it depends on.")
    return _record(dowel, tags, states, missing, notes, inputs)


def _movement(ctx, dowel, structure, t_in, states, missing, inputs) -> None:
    site = ctx.plan.project.site
    hot, cold = site.design_temp_cooling, site.design_temp_heating
    if hot is None or cold is None:
        missing.append("Site.design_temp_cooling and Site.design_temp_heating — the "
                       "movement row's temperature range")
        return
    # The board closes only as the court warms past its SET temperature; contraction opens it.
    set_f = max(cold.fahrenheit, MIN_SET_TEMP_F)
    delta_t = hot.fahrenheit - set_f
    # Full run: the retained soil behind the far wall is far stiffer than the board, so the
    # court grows toward the break (free body §11c).
    run_in = _run_in(ctx, dowel, structure)
    movement_in = ALPHA_C_PER_F * delta_t * run_in
    inputs += [Quantity("delta_T", delta_t, "F", 0.1),
               Quantity("court_run", run_in, "in", 0.1)]
    names = [f"Dowel.{f}" for f in ("foam_modulus_psi", "foam_source")
             if getattr(dowel, f) is None]
    if names:
        missing.append(f"{', '.join(names)} on {dowel.tag} — the board's compressive "
                       f"modulus off a named datasheet; {movement_in:.3f}\" of movement "
                       f"({delta_t:.0f} F over {run_in / 12:.2f}') waits on it")
        return
    long_term_psi = dowel.foam_psi / FOAM_CREEP_FACTOR
    inputs.append(Quantity("foam_modulus", dowel.foam_modulus_psi, "psi", 1.0))
    states.append(LimitState(
        "thermal movement", movement_in, t_in * long_term_psi / dowel.foam_modulus_psi, "in",
        f"{ALPHA_C_PER_F:g}/F x ({hot.fahrenheit:.0f} - {set_f:.0f} F set, ACI 306R-16 "
        f"Table 3.1) x {run_in:.1f}\" of court run toward the break; vs {t_in:.2f}\" x "
        f"{long_term_psi:.2f} psi (1/{FOAM_CREEP_FACTOR:g} of {dowel.foam_psi:.0f}, creep) / "
        f"E {dowel.foam_modulus_psi:,.0f} psi — {dowel.foam_source}"))


def _court_stem(ctx, dowel, structure: set[str]):
    """``(wall tag, stem plf, footing width in)`` — the court wall at this joint and the
    strip under it, or None. A connect is a wall, or a footing read through ``under``."""
    from typehaus.model.enums import LayerFunction
    from typehaus.model.structure import Footing

    for tag in dowel.connects:
        el = ctx.plan.by_tag(tag)
        wall = ctx.plan.by_tag(el.under) if isinstance(el, Footing) else el
        if wall is None or wall.tag not in structure:
            continue
        footing = el if isinstance(el, Footing) else next(
            (f for f in ctx.plan.all_elements()
             if isinstance(f, Footing) and f.under == wall.tag), None)
        assembly = ctx.plan.library.resolve_assembly(getattr(wall, "assembly", "") or "")
        thick = sum(ly.thickness.inches for ly in getattr(assembly, "layers", ())
                    if ly.function is LayerFunction.STRUCTURE)
        top, bot = getattr(wall, "top_elevation", None), getattr(wall, "bottom_elevation", None)
        if footing is None or not thick or top is None or bot is None:
            return None
        plf = CONCRETE_PCF * (thick / 12.0) * (top.inches - bot.inches) / 12.0
        return wall.tag, plf, footing.width.inches
    return None


def _settlement(ctx, dowel, structure, t_in, states, missing, inputs, notes) -> None:
    """The court stem's bearing over k_v, against the bars' rupture drift over the gap.

    The stem is placement 2, cast after the footing that holds these bars has set, so its
    whole weight settles the court side against a house cured and surveyed first (free body
    §11e). It is a LOWER bound on the court's added bearing (porch, soil and snow add to it),
    and the house is credited no settlement of its own — the bound's two halves are stated.
    """
    report = getattr(ctx.plan.project.site, "lateral_subgrade_modulus", None)
    k_v = getattr(report, "k_v_pci", None)
    if k_v is None:
        missing.append(SETTLEMENT_MISSING)
        return
    presumed = getattr(report, "provenance", "measured") == "presumed"
    inputs += [Quantity("k_v", k_v, "pci", 0.1),
               Quantity("k_v_presumed", 1.0 if presumed else 0.0, "-", 0.5)]
    stem = _court_stem(ctx, dowel, structure)
    if stem is None:
        missing.append(f"the court wall {dowel.tag} ties, with a STRUCTURE layer, top and "
                       f"bottom elevations and a Footing under it — the settlement demand")
        return
    if dowel.bar_tensile_lb is None or dowel.bar_modulus_psi is None:
        return  # the reserve row already names the missing bar values
    wall_tag, plf, width_in = stem
    q_psi = plf / (width_in / 12.0) / 144.0
    d_in = dowel.diameter.inches
    ei = dowel.bar_modulus_psi * math.pi * d_in ** 4 / 64.0
    m_cap = PHI_RUPTURE * dowel.bar_tensile_lb * d_in / 8.0
    drift_cap = m_cap * t_in ** 2 / (6.0 * ei)
    inputs.append(Quantity("stem_bearing", q_psi * 144.0, "psf", 0.1))
    label = "PRESUMED" if presumed else "measured"
    states.append(LimitState(
        "differential settlement", q_psi / k_v, drift_cap, "in",
        f"{wall_tag}'s stem {plf:,.0f} plf over {width_in / 12:.2f}' of footing = "
        f"{q_psi * 144:.1f} psf / k_v {k_v:g} pci ({label}: {report.source}); vs the bar's "
        f"rupture drift fixed-fixed over {t_in:.2f}\", 0.55 x T_u d/8 x t^2 / 6EI"))
    notes.append(
        f"SETTLEMENT, BOUNDED: the stem alone is a LOWER bound on the court's added bearing and "
        f"the house is credited none of its own; the bars tolerate "
        f"{k_v * drift_cap * 144.0:.0f} psf of bearing mismatch at this k_v."
        + (" k_v IS PRESUMED, a published table row and not a report on this parcel — a "
           "geotechnical report confirms or replaces it." if presumed else ""))


def _reserve(dowel, ref, by_pcf, total_bars, t_in, states, missing, inputs, notes) -> None:
    pcf, source, shortfall = max(((p, tag, lb) for p, row in by_pcf.items()
                                  for tag, lb in row.items()), key=lambda r: r[2])
    share = dowel.count / total_bars
    demand = EARTH_PRESSURE_LOAD_FACTOR * shortfall * share
    inputs += [Quantity("loop_shortfall", shortfall, "lb", 1.0),
               Quantity("bar_share", share, "", 0.0001)]
    names = [f"Dowel.{f}" for f in ("bar_shear_lb", "bar_tensile_lb", "bar_modulus_psi",
                                    "bar_source") if getattr(dowel, f) is None]
    if names:
        missing.append(f"{', '.join(names)} on {dowel.tag} — the GFRP bar's published "
                       f"values (ASTM D7957 datasheet); the reserve demand is "
                       f"{demand:,.0f} lb")
        return
    d_in = dowel.diameter.inches
    shear_lb = PHI_SHEAR * dowel.bar_shear_lb
    bend_lb = PHI_RUPTURE * dowel.bar_tensile_lb * d_in / (4.0 * t_in)
    per_bar = min(shear_lb, bend_lb)
    inputs += [Quantity("bar_shear", dowel.bar_shear_lb, "lb", 1.0),
               Quantity("bar_tensile", dowel.bar_tensile_lb, "lb", 1.0),
               Quantity("bar_modulus", dowel.bar_modulus_psi, "psi", 1000.0)]
    states.append(LimitState(
        "dowel shear reserve", demand, dowel.count * per_bar, "lb",
        f"1.6 x {shortfall:,.0f} lb ({source} at {pcf:.0f} pcf, loop {ref}) x "
        f"{dowel.count}/{total_bars} bars; per bar min(0.75 x {dowel.bar_shear_lb:,.0f}, "
        f"0.55 x T_u d/4t = {bend_lb:,.0f}) lb — {dowel.bar_source}",
        combination="1.6H", combination_factors=(("H", EARTH_PRESSURE_LOAD_FACTOR),)))
    inertia = 3.141592653589793 * d_in ** 4 / 64.0
    slip = (shortfall * share / dowel.count) * t_in ** 3 / (12.0 * dowel.bar_modulus_psi
                                                            * inertia)
    notes.append(f"Slip across the gap at the service reserve share: {slip:.4f}\" "
                 f"(fixed-fixed bar over {t_in:.2f}\").")


def _record(dowel, tags, states, missing, notes, inputs) -> EngineeringRecord:
    # OVER outranks INCOMPLETE, as on the other kinds: a graded shortfall is the finding.
    over = [s for s in states if not s.ok]
    status = Status.OVER if over else (Status.INCOMPLETE if missing else Status.OK)
    graded = ", ".join(f"{s.name} {s.ratio:.2f}" for s in states) or "nothing"
    summary = f"{dowel.tag}: graded as a reserve — {graded}"
    if over:
        summary += " — OVER on " + ", ".join(s.name for s in over)
    if missing:
        summary += f"; open: {len(missing)} item(s)"
    return EngineeringRecord(
        item_id=item_id(KIND, dowel.tag), kind=KIND, key=dowel.tag,
        basis_version=BASIS_VERSION, basis=BASIS, status=status, summary=summary,
        inputs=tuple(inputs), limit_states=tuple(states),
        missing=tuple(dict.fromkeys(missing)), notes=tuple(notes), element_tags=tags)
