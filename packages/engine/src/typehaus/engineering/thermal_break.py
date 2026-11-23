"""Compressible boards between two separately founded pours — an isolation joint.
``thermal_break_transfer/<the loop's cross-member>``: ONE item per court loop, every board in
it (decision 13, 2026-11-22). The loop-level rows (the thrust into the house, its lateral path,
the near line, the court's winter tension) are graded once; each board's own rows carry its
tag. A board on no loop is its own item.

**No structural member crosses the break.** The masonry ties of a veneer founded on the court
and the boards' own compliance do, and both are named and bounded (free body §11r): the court
holds its own thrust (``retaining_system``) and the board keeps the house out of that free
body. What is graded is what the boards and the house behind them must survive — free body
§11j-§11l (basis 9), hand-worked first:

* the board — fresh-concrete pressure on the AUTHORED placement (ACI 347R-14, capped at wh)
  where it is a form face, and its summer strain, any locked-in pour plus the closing at the
  neutral point; a board set into a stripped blockout (``formed_and_stripped``) takes no pour;
* the thrust, ``k_i ε_i x`` at the neutral point plus any locked-in pour
  (:mod:`thermal_break_demand`), into the house wall (flexure, shear, the floor line, the
  house's own insulation), along the house's near footing line in plan
  (:mod:`thermal_break_line`) and lateral path (:mod:`thermal_break_path`), and back into
  the court;
* winter, the joint open: the court's own contraction on its base (:mod:`thermal_break_winter`).

Temperatures come from ``Site.concrete_service_temperature`` (a cited concrete range and a
specified set floor), never design air. A row over its capacity makes the item OVER even
while an input is still missing. An ESTIMATED modulus adds a sensitivity note on E.
"""

from __future__ import annotations

import dataclasses

from typehaus.engineering import thermal_break_board as brd
from typehaus.engineering import thermal_break_demand as dem
from typehaus.engineering import thermal_break_geometry as geo
from typehaus.engineering import thermal_break_house as house
from typehaus.engineering import thermal_break_line as line
from typehaus.engineering import thermal_break_path as path
from typehaus.engineering import thermal_break_winter as winter
from typehaus.engineering.item import (
    EngineeringRecord,
    LimitState,
    Oracle,
    Quantity,
    Status,
    item_id,
)
from typehaus.engineering.registry import EngineeringContext, calc, keys, oracled_by
from typehaus.engineering.retaining_system import (
    footing_shortfalls,
    loop_free_bodies,
    loop_mobilisation,
)
from typehaus.engineering.thermal_break_joint import NAME as JOINT
from typehaus.engineering.thermal_break_joint import joint_row
from typehaus.resolve.slab_clip import floor_outline

KIND = "thermal_break_transfer"
BASIS = ("ACI 347R-14 (fresh-concrete pressure); ACI 209R-92 (stem shrinkage); ACI 318-19 "
         "(house wall, slab strut); IBC 1610.1/1806.2 (house sliding, soil); IRC R404.4 loop")
#: Bumped whenever the arithmetic below changes — it rides in the fingerprint.
#: ``"11"``: one record per loop; the court body is ``retaining_system``'s (2026-11-22).
BASIS_VERSION = "11"
#: Multiples of an ESTIMATED modulus the sensitivity note re-grades at (free body §11i).
E_SENSITIVITY = (2.0 / 3.0, 1.5, 2.0)

oracled_by(KIND, Oracle(note="sunken_garden_court_free_body.md", section="§11l, §11m",
                        test="tests/test_thermal_break.py"))

_NOTES = (
    "AN ISOLATION JOINT: no structural member crosses it and no row grades a shear across "
    "it. The court closes its own free body (`retaining_system`); every row below is a "
    "board's own survival or the thrust the boards pass. What does cross is named and "
    "bounded: the veneer's ties (tie travel) and the boards' compliance (the joint "
    "movement row).",
    "RETIRED WITH THE BARS (free body §11e): shear reserve, racking drift and development — "
    "there is no bar to grade. Differential movement and joint closure are the joint "
    "movement row's.",
    "RETIRED WITH THE STRIP (free body §11i): sliding and bearing of one isolated house strip "
    "— replaced by the house's lateral path through its slab on grade.",
    "NO FLOTATION ROW: nothing restrains a board with no bars. A form-face board is held by "
    "the work (adhered or pinned to the cured house face, and braced); a stripped one is set "
    "into its slot after the pour and never meets fresh concrete (sequencing trap 2).")


def _compliant_note(board, product) -> str:
    cap = product.cap_psi
    return (f"STRESS-CAPPED (free body §11l): {board.tag}'s {product.compliant.material} "
            f"layer publishes a MAXIMUM {cap:g} psi at {product.compliant.at_strain:.0%}; the "
            f"court's largest closure strains it less, so the board is graded AT the cap, "
            f"{cap:g} x {board.area_in2:,.1f} in² = {cap * board.area_in2:,.0f} lb — independent "
            f"of the foam's modulus, the neutral point and the stems' shrinkage.")


def _boards(ctx: EngineeringContext, loops: dict) -> list[geo.Board]:
    out = [b for e in geo.isolation_boards(ctx)
           if (b := geo.authored_board(ctx, e, loops)) is not None]
    return out + geo.layer_boards(ctx, loops)


@keys(KIND)
def enumerate_breaks(ctx: EngineeringContext) -> list[str]:
    """One key per court loop with a board on it, and one per board on no loop."""
    loops = footing_shortfalls(ctx)
    return sorted({b.loop_ref or b.tag for b in _boards(ctx, loops)})


@calc(KIND)
def compute(ctx: EngineeringContext) -> list[EngineeringRecord]:
    loops = footing_shortfalls(ctx)
    boards = _boards(ctx, loops)
    products = {b.tag: brd.product_of(b.element) for b in boards if b.element is not None}
    # A layer board names no product and no sequence of its own (a Layer has neither field);
    # it is the product the same court's authored boards name — `test_catlin_contract_m3` pins
    # that — and it is stripped when they all are (free body §11j: the beam's blockout).
    for b in boards:
        if b.element is None:
            mine = [o for o in boards if o.element is not None and o.loop_ref == b.loop_ref]
            products[b.tag] = next((products[o.tag] for o in mine if products[o.tag]), None)
            b.formed_and_stripped = bool(mine) and all(o.formed_and_stripped for o in mine)
    bodies = loop_free_bodies(ctx)
    graded = _grade(ctx, boards, products, bodies, 1.0)
    if any(p is not None and p.estimated for p in products.values()):
        sens = {k: _grade(ctx, boards, products, bodies, k) for k in E_SENSITIVITY}
        for tag, (states, _missing, _inputs, notes) in graded.items():
            if states:
                notes.append(_sensitivity(tag, states, sens))
    groups: dict[str, list] = {}
    for b in sorted(boards, key=lambda b: b.tag):
        groups.setdefault(b.loop_ref or b.tag, []).append(b)
    temps = brd.temps(ctx)
    mobilised = loop_mobilisation(ctx)
    out = []
    for key, mine in sorted(groups.items()):
        joint = None
        if mine[0].loop_ref is not None:
            runs = {b.tag: geo.court_run_in(ctx, b) for b in mine}
            joint = joint_row(ctx, mine, products, temps, runs,
                              mobilised.get(mine[0].loop_ref))
        out.append(_record(key, mine, graded, joint))
    return out


def _sensitivity(tag, states, sens) -> str:
    rows = []
    for state in states:
        alt = [next((s.ratio for s in sens[k][tag][0] if s.name == state.name), None)
               for k in E_SENSITIVITY]
        if any(a is not None and abs(a - state.ratio) > 0.005 for a in alt):
            rows.append(f"{state.name} {state.ratio:.3f} -> "
                        + " / ".join("-" if a is None else f"{a:.3f}" for a in alt))
    scales = " / ".join(f"x{k:.2f}" for k in E_SENSITIVITY)
    return (f"SENSITIVITY ON E (the modulus is ESTIMATED; ratio at {scales}): "
            + ("; ".join(rows) or "no row moves"))


def _grade(ctx, boards, products, bodies, e_scale) -> dict:
    """``{tag: (states, missing, inputs, notes)}`` at ``e_scale`` x each product's modulus."""
    temps = brd.temps(ctx)
    npt = dem.neutral_point(ctx, boards, products, temps, bodies, e_scale) if temps else {}
    sigma, closure = {}, {}
    for b in boards:
        p = products.get(b.tag)
        if p is not None and b.loop_ref in npt and p.cap_psi is not None:
            # §11l: graded AT the compliant layer's published cap, never off E or x.
            sigma[b.tag] = min(p.cap_psi, p.psi)
            closure[b.tag] = sigma[b.tag] * b.t_in / (p.modulus_psi * e_scale)
        elif p is not None and b.loop_ref in npt:
            closure[b.tag] = dem.closing_strain(ctx, b, temps) * npt[b.loop_ref][0]
            sigma[b.tag] = min(p.modulus_psi * e_scale * closure[b.tag] / b.t_in, p.psi)
    lock = {b.tag: dem.lock_in_force(ctx, b) for b in boards}
    thrust = {b.tag: sigma[b.tag] * b.area_in2 + lock[b.tag] for b in boards if b.tag in sigma}
    patches = {}
    for b in boards:
        if b.tag in sigma and b.element is not None and b.house_tag and \
                ctx.plan.by_tag(b.house_tag).__class__.__name__ == "FoundationWall":
            pour = dem.pressure_at(ctx, b) or (lambda _z: 0.0)
            patches[b.tag] = house.wall_patch(
                ctx, b, lambda z, s=sigma[b.tag], f=pour: s + f(z))
    sh = dict(boards=boards, temps=temps, products=products, sigma=sigma, thrust=thrust,
              closure=closure, npt=npt, patches=patches, free_bodies=bodies, e_scale=e_scale,
              lock=lock)
    sh["lines"] = {ref: _near_line(ctx, [b for b in boards if b.loop_ref == ref], sh)
                   for ref in {b.loop_ref for b in boards if b.tag in sigma}}
    return {b.tag: _one(ctx, b, sh) for b in boards}


def _one(ctx, board, sh):
    states: list[LimitState] = []
    missing: list[str] = []
    notes = list(_NOTES)
    inputs = [Quantity("board_t", board.t_in, "in", 0.01),
              Quantity("board_h", board.h_in, "in", 0.01),
              Quantity("board_L", board.length_in, "in", 0.01)]
    product, temps = sh["products"].get(board.tag), sh["temps"]
    if product is None:
        missing.append(f"IsolationBoard.psi, modulus_psi and source for {board.tag} — the "
                       f"rating, modulus and datasheet every board row reads")
        return states, missing, inputs, notes
    inputs.append(Quantity("foam_psi", product.psi, "psi", 0.1))
    if product.estimated:
        notes.append(f"ESTIMATED MODULUS: {product.modulus_psi:,.0f} psi is not published — "
                     f"{product.source}." + (" No verdict reads it: the thrust is graded at "
                                             "the compliant layer's cap." if product.compliant
                                             else ""))
    pour = None
    if board.formed_and_stripped:
        notes.append(dem.FORMED_AND_STRIPPED_NOTE)
        if board.element is not None and not board.element.placement_sequence_ref:
            missing.append(f"IsolationBoard.placement_sequence_ref for {board.tag} — the "
                           f"annotation that puts the stripped blockout on the drawing")
    else:
        pour = brd.pressure(ctx, board, product, states, missing, inputs)
    if temps is None:
        missing.append(brd.TEMPERATURE_MISSING)
    elif board.tag in sh["closure"] and product.compliant is not None:
        notes.append(_compliant_note(board, product))
        if not board.formed_and_stripped:
            notes.append(dem.LOCK_IN_FLAG)
        brd.compliant_row(board, product, temps, geo.court_run_in(ctx, board), states, inputs)
        brd.movement(board, product, temps, geo.court_run_in(ctx, board),
                     sh["closure"][board.tag], pour, states, inputs, sh["e_scale"])
    elif board.tag in sh["closure"]:
        inputs.append(Quantity("neutral_point", sh["npt"][board.loop_ref][0], "in", 0.01))
        notes.append(dem.NEUTRAL_POINT_FLAG)
        if not board.formed_and_stripped:
            notes.append(dem.LOCK_IN_FLAG)
        if dem.dries(ctx, board):
            notes.append(dem.shrinkage_flag(dem.stem_shrinkage()))
        brd.movement(board, product, temps, geo.court_run_in(ctx, board),
                     sh["closure"][board.tag], pour, states, inputs, sh["e_scale"])
    if board.tag in sh["sigma"]:
        _thrust_rows(ctx, board, sh, pour, states, missing, inputs, notes)
    return states, missing, inputs, notes


def _thrust_rows(ctx, board, sh, pour, states, missing, inputs, notes) -> None:
    sigma = sh["sigma"][board.tag]
    inputs += [Quantity("board_stress", sigma, "psi", 0.001),
               Quantity("board_lock_in", sh["lock"][board.tag], "lb", 1.0),
               Quantity("board_thrust", sh["thrust"][board.tag], "lb", 1.0)]
    patch = sh["patches"].get(board.tag)
    if patch is not None:
        brd.house_insulation_row(board, geo.house_insulation(ctx, board), sigma, pour,
                                 states, missing)
        house.house_wall_rows(ctx, board, patch, states, missing, inputs)
    mine = [b for b in sh["boards"] if b.loop_ref == board.loop_ref]
    total = sum(sh["thrust"].get(b.tag, 0.0) for b in mine)
    floor = sum(p["top_reaction"] + p["band"] for b in mine
                if (p := sh["patches"].get(b.tag)) is not None)
    inputs.append(Quantity("house_thrust", total, "lb", 1.0))
    path.path_rows(ctx, mine, total, floor, states, missing, notes, inputs)
    if board.loop_ref is not None:
        house.court_sliding(ctx, board.loop_ref, total, sh["free_bodies"], states, missing)
    found = sh["lines"].get(board.loop_ref)
    if found is not None:
        line.line_rows(*found, states=states, inputs=inputs)
    from typehaus.engineering.soil import presumptive

    soil = presumptive(getattr(ctx, "soil_class", None),
                       basis=getattr(ctx, "soil_basis", None))
    winter.winter_rows(ctx, board, sh["free_bodies"], soil, states, missing, inputs, notes)


def _near_line(ctx, mine, sh):
    """The loop's near footing line solved under its boards' loads (free body §11m.1):
    each board's thrust along its own stretch, less what a house wall sends to its floor
    line. ``(result, break, E, estimated, (cap psi, how))`` or None."""
    mine = [b for b in mine if b.tag in sh["thrust"]]
    if not mine:
        return None
    facing = sorted({t for b in mine for t in geo.facing_footings(ctx, b)})
    found = line.near_line(ctx, facing, mine[0].ax, mine[0].toward_house) if facing else None
    slab = path.house_slab(ctx, facing) if found else None
    brk = slab[0].perimeter_thermal_break if slab else None
    grade = brk and brk_rating(brk)
    if found is None or grade is None:
        return None
    loads = []
    for b in mine:
        patch = sh["patches"].get(b.tag)
        force = patch["bottom_reaction"] if patch else sh["thrust"][b.tag]
        loads.append((*b.along, force / (b.along[1] - b.along[0])))
    estimated = brk.modulus_psi is None
    e = grade[0] * line.E_PER_PSI_ESTIMATE if estimated else brk.modulus_psi
    depth = brk.depth.inches if brk.depth is not None else slab[0].thickness.inches
    lo, hi = path._span(floor_outline(ctx.model, slab[1]), 1 - mine[0].ax)
    result = line.share(ctx, found, loads, e * depth / brk.thickness.inches, (lo, hi))
    result["edge_depth"] = depth
    frac = brk.sustained_load_fraction
    cap = ((frac * brk.psi, f"the sheet's sustained-load rule, {frac:.3g} x {brk.psi:.0f} psi")
           if frac and brk.psi is not None else (grade[0], grade[1]))
    return result, brk, e, estimated, cap


def brk_rating(brk):
    from typehaus.engineering.thermal_break_board import rated

    return rated(brk.material_ref, brk.psi, brk.source)


def _merge(mine, graded):
    """One record's rows from its boards': a row every board grades identically is the
    loop's and appears once; a row that differs is the board's and carries its tag."""
    lists = [graded[b.tag] for b in mine]
    key = lambda st: (st.name, round(st.demand, 6), round(st.capacity, 6))  # noqa: E731
    shared = set.intersection(*({key(st) for st in states} for states, *_ in lists)) \
        if len(lists) > 1 else set()
    states, inputs, notes, missing, seen = [], [], [], [], set()
    for b, (b_states, b_missing, b_inputs, b_notes) in zip(mine, lists, strict=True):
        for st in b_states:
            if key(st) in shared:
                if key(st) not in seen:
                    seen.add(key(st))
                    states.append(st)
                continue
            states.append(st if len(mine) == 1 else
                          dataclasses.replace(st, name=f"{b.tag}: {st.name}"))
        for q in b_inputs:
            inputs.append(q if len(mine) == 1 else
                          dataclasses.replace(q, name=f"{b.tag}:{q.name}"))
        notes.extend(n for n in b_notes if n not in notes)
        missing.extend(m for m in b_missing if m not in missing)
    return states, missing, inputs, notes


def _record(key, mine, graded, joint=None) -> EngineeringRecord:
    states, missing, inputs, notes = _merge(mine, graded)
    pending = []
    if joint is not None and joint[0] is not None:
        row, gaps, more = joint
        states.append(row)
        inputs += more
        missing += [g for g in gaps if g not in missing]
        if not row.ok:
            # Decision 29 is open: the detail has to take the bounded movement, and how
            # (thicker layer, set after backfill, wider joint) is the owner's choice.
            pending.append(f"a joint detail that takes the bounded court movement "
                           f"({row.demand:.3f}\" against {row.capacity:.3f}\")")
            states_over = [s for s in states if not s.ok and s is not row]
            if not states_over:
                missing += pending
    tags = tuple(dict.fromkeys(t for b in mine for t in (
        b.tag, *(b.element.connects if b.element else ()))))
    # OVER outranks INCOMPLETE, as on the other kinds: a graded shortfall is the finding.
    over = [s for s in states if not s.ok and not (pending and s.name == JOINT)]
    status = Status.OVER if over else (Status.INCOMPLETE if missing else Status.OK)
    governing = max(states, key=lambda s: s.ratio, default=None)
    boards = ", ".join(b.tag for b in mine)
    summary = (f"{key}: {len(mine)} board(s) ({boards}); "
               + (f"{governing.name} governs at {governing.ratio:.2f}" if governing
                  else "nothing graded"))
    if over:
        summary += " — OVER on " + ", ".join(s.name for s in over)
    if missing:
        summary += f"; open: {len(missing)} item(s)"
    return EngineeringRecord(
        item_id=item_id(KIND, key), kind=KIND, key=key,
        basis_version=BASIS_VERSION, basis=BASIS, status=status, summary=summary,
        inputs=tuple(inputs), limit_states=tuple(states),
        missing=tuple(missing), notes=tuple(notes), element_tags=tags)
