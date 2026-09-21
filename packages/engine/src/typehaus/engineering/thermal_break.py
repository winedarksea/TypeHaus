"""Two pours held apart by an insulating board — every row the board, its bars and the
house behind it have to survive. ``thermal_break_transfer/<tag>``.

**The design shear across the break is zero by construction**: the court holds its own
thrust (``retaining_system``) and the board keeps the house out of that free body. What is
graded is everything else, free body §11 (basis 4), hand-worked first:

* the board — fresh-concrete pressure on the AUTHORED placement (ACI 347R-14, capped at wh),
  flotation, and closing movement against its recoverable strain ``σ_y / E``;
* the thrust it then passes, ``min(E·δ/t, σ_y) × A`` — into the house wall (flexure, shear,
  the floor line, the house's own insulation) or the house strip (sliding, bearing), and
  back into the court (sliding under the sum of every board on the loop);
* the GFRP bars on ACI 440.11-22 design values (C_E 0.85) over the CLEAR gap between the
  concretes — shear reserve, settlement and racking drift, joint opening at the §24.6.2
  sustained stress, and development.

Temperatures come from ``Site.concrete_service_temperature`` (a cited concrete range and a
specified set floor), never design air. A cast beam in the loop whose assembly carries an
insulating layer is a break too (catlin's veneer beam): board rows only, no bars. A row over
its capacity makes the item OVER even while an input is still missing.
"""

from __future__ import annotations

from typehaus.engineering import thermal_break_bars as bars
from typehaus.engineering import thermal_break_board as brd
from typehaus.engineering import thermal_break_geometry as geo
from typehaus.engineering import thermal_break_house as house
from typehaus.engineering.item import EngineeringRecord, Oracle, Quantity, Status, item_id
from typehaus.engineering.registry import EngineeringContext, calc, keys, oracled_by
from typehaus.engineering.retaining_system import footing_shortfalls, loop_free_bodies
from typehaus.engineering.thermal_break_bars import SETTLEMENT_MISSING  # noqa: F401
from typehaus.engineering.thermal_break_board import ALPHA_C_PER_F  # noqa: F401

KIND = "thermal_break_transfer"
BASIS = ("ACI 347R-14 (fresh-concrete pressure); ACI CODE-440.11-22 (GFRP bar, C_E 0.85); "
         "ACI 318-19 (house wall); IBC 1806.2 (sliding); IRC R404.4 loop")
#: Bumped whenever the arithmetic below changes — it rides in the fingerprint.
BASIS_VERSION = "4"

oracled_by(KIND, Oracle(note="sunken_garden_court_free_body.md", section="§11",
                        test="tests/test_thermal_break.py"))


def _boards(ctx: EngineeringContext, loops: dict) -> list[geo.Board]:
    out = [b for d in geo.dowels(ctx) if (b := geo.dowel_board(ctx, d, loops)) is not None]
    return out + geo.layer_boards(ctx, loops)


@keys(KIND)
def enumerate_breaks(ctx: EngineeringContext) -> list[str]:
    """Every ``Dowel`` with a foam block, and every cast beam in a retaining loop whose
    assembly carries an insulating layer."""
    loops = footing_shortfalls(ctx)
    return sorted({d.tag for d in geo.dowels(ctx)}
                  | {b.tag for b in geo.layer_boards(ctx, loops)})


def _gap(ctx, board) -> float | None:
    face = geo.house_concrete_face(ctx, board)
    return None if face is None else abs(face - board.court_face_in)


@calc(KIND)
def compute(ctx: EngineeringContext) -> list[EngineeringRecord]:
    loops = footing_shortfalls(ctx)
    boards = _boards(ctx, loops)
    temps = brd.temps(ctx)
    products = {b.tag: brd.product_of(b.dowel) for b in boards if b.dowel is not None}
    # The beam's board names no product of its own (a Layer has no compressive field); it is
    # the product the same court's closure boards name — `test_catlin_contract_m3` pins that.
    for b in boards:
        if b.dowel is None:
            products[b.tag] = next((products[o.tag] for o in boards if o.dowel is not None
                                    and o.loop_ref == b.loop_ref and products[o.tag]), None)
    sigma = {}
    for b in boards:
        p = products[b.tag]
        if p is not None and temps is not None:
            delta = ALPHA_C_PER_F * temps.closing * geo.court_run_in(ctx, b)
            sigma[b.tag] = min(p.modulus_psi * delta / b.t_in, p.psi)
    thrust = {b.tag: sigma[b.tag] * b.area_in2 for b in boards if b.tag in sigma}
    patches = {b.tag: house.wall_patch(ctx, b, sigma[b.tag]) for b in boards
               if b.tag in sigma and b.dowel is not None
               and geo.z_extent(ctx, b.house_tag or "") is not None
               and ctx.plan.by_tag(b.house_tag).__class__.__name__ == "FoundationWall"}
    bars_on: dict[str, int] = {}
    for b in boards:
        if b.dowel is not None and b.loop_ref is not None:
            bars_on[b.loop_ref] = bars_on.get(b.loop_ref, 0) + b.dowel.count
    shared = dict(loops=loops, boards=boards, temps=temps, products=products, sigma=sigma,
                  thrust=thrust, patches=patches, bars_on=bars_on,
                  free_bodies=loop_free_bodies(ctx))
    return [_one(ctx, b, shared) for b in sorted(boards, key=lambda b: b.tag)]


def _one(ctx, board, sh) -> EngineeringRecord:  # noqa: C901
    d = board.dowel
    tags = tuple(dict.fromkeys((board.tag, *(d.connects if d is not None else ()))))
    states, missing = [], []
    notes = ["THE DESIGN SHEAR ACROSS THIS BREAK IS ZERO BY CONSTRUCTION, and no row grades "
             "it: the court closes its own free body (`retaining_system`). Every row below is "
             "the board's own survival, the thrust it passes, or a reserve of the bars."]
    inputs = [Quantity("board_t", board.t_in, "in", 0.01),
              Quantity("board_h", board.h_in, "in", 0.01),
              Quantity("board_L", board.length_in, "in", 0.01)]
    if d is not None:
        inputs += [Quantity("count", d.count, "", None),
                   Quantity("diameter", d.diameter.inches, "in", 0.001)]
    product, temps = sh["products"].get(board.tag), sh["temps"]
    if product is None:
        missing.append(f"Dowel.foam_psi, foam_modulus_psi and foam_source for {board.tag}'s "
                       f"board — the rating, modulus and datasheet every board row reads")
        return _record(board, tags, states, missing, notes, inputs)
    inputs.append(Quantity("foam_psi", product.psi, "psi", 0.1))
    pour = brd.pressure(ctx, board, product, states, missing, inputs)
    below = geo.stacked_on(ctx, board, sh["boards"])
    if d is None:
        notes.append("NO FLOTATION ROW: a layer board's bottom edge bears on the bedding and "
                     "its far face on backfill — no face is under the pour; it is held by the "
                     "formwork. NO BAR ROWS: it has no bars.")
    elif below is not None:
        notes.append(f"NO FLOTATION ROW: this board stands on {below}'s, so no face of it is "
                     f"under the pour.")
    else:
        brd.flotation(board, product, states)
    if temps is None:
        missing.append(brd.TEMPERATURE_MISSING)
    else:
        brd.movement(ctx, board, product, temps, states, inputs)
    if board.tag in sh["sigma"]:
        _thrust_rows(ctx, board, sh, pour, states, missing, inputs)
    if d is not None:
        _bar_rows(ctx, board, sh, states, missing, inputs, notes)
    return _record(board, tags, states, missing, notes, inputs)


def _thrust_rows(ctx, board, sh, pour, states, missing, inputs) -> None:
    sigma = sh["sigma"][board.tag]
    inputs += [Quantity("board_stress", sigma, "psi", 0.01),
               Quantity("board_thrust", sh["thrust"][board.tag], "lb", 1.0)]
    patch = sh["patches"].get(board.tag)
    if patch is not None:
        brd.house_insulation_row(board, geo.house_insulation(ctx, board), sigma, pour,
                                 states, missing)
        house.house_wall_rows(ctx, board, patch, states, missing, inputs)
    else:
        facing = geo.facing_footings(ctx, board)
        base = min((geo.z_extent(ctx, t)[0] for t in facing), default=board.bottom_in)
        loads = [(sh["thrust"][board.tag], (board.bottom_in + board.top_in) / 2 - base,
                  f"{board.tag} board")]
        for other in sh["boards"]:
            p = sh["patches"].get(other.tag)
            under = getattr(ctx.plan.by_tag(other.house_tag or ""), "tag", None)
            feet = {t for t in facing if ctx.plan.by_tag(t).under == under}
            if p is not None and feet and board.dowel is not None:
                loads.append((p["bottom_reaction"], geo.z_extent(ctx, other.house_tag)[0] - base,
                              f"{other.house_tag} base under {other.tag}"))
        house.footing_rows(ctx, board, facing, loads, states, missing, inputs)
    if board.loop_ref is not None:
        total = sum(sh["thrust"].get(b.tag, 0.0) for b in sh["boards"]
                    if b.loop_ref == board.loop_ref)
        house.court_sliding(ctx, board.loop_ref, total, sh["free_bodies"], states, missing)


def _bar_rows(ctx, board, sh, states, missing, inputs, notes) -> None:
    d = board.dowel
    names = [f"Dowel.{f}" for f in ("bar_shear_lb", "bar_tensile_lb", "bar_modulus_psi",
                                    "bar_source") if getattr(d, f) is None]
    gap = _gap(ctx, board)
    if names or gap is None or board.loop_ref is None:
        missing.append(f"{', '.join(names) or 'the house element and a verified loop'} on "
                       f"{board.tag} — the GFRP bar's published values (ASTM D7957 "
                       f"datasheet), its clear gap and the loop it reserves")
        return
    inputs += [Quantity("clear_gap", gap, "in", 0.001),
               Quantity("bar_tensile", d.bar_tensile_lb, "lb", 1.0),
               Quantity("bar_modulus", d.bar_modulus_psi, "psi", 1000.0)]
    bars.reserve(d, board.loop_ref, sh["loops"][board.loop_ref], sh["bars_on"][board.loop_ref],
                 gap, states, inputs, notes)
    settle = bars.settlement(ctx, board, gap, states, missing, inputs, notes)
    temps = sh["temps"]
    centre = geo.court_centre_along(ctx, board)
    if temps is None or centre is None:
        return
    offset = abs((board.along[0] + board.along[1]) / 2.0 - centre)
    bars.racking(d, gap, offset, temps.opening, settle, states, inputs)
    from typehaus.resolve.concrete import concrete_spec_for, fc_psi

    fcs = [fc_psi(concrete_spec_for(ctx.plan, ctx.plan.by_tag(t))) for t in d.connects]
    z_bar = geo.bar_centre_z(ctx, d)
    z_court = geo.z_extent(ctx, board.court_tag)
    if None in fcs or z_bar is None or z_court is None:
        missing.append(f"both pours' f'c and the resolved bar row on {board.tag} — opening "
                       f"and development")
        return
    ends = ((d.count - 1) * d.spacing.inches if d.spacing else 0.0)
    c_b = min(d.spacing.inches / 2.0 if d.spacing else 99.0, (board.length_in - ends) / 2.0,
              z_bar - z_court[0], z_court[1] - z_bar)
    delta_open = ALPHA_C_PER_F * temps.opening * geo.court_run_in(ctx, board)
    bars.opening(d, gap, delta_open, min(fcs), c_b, z_bar - z_court[0], states, inputs)
    half = d.length.inches / 2.0
    face = geo.house_concrete_face(ctx, board)
    court_embed = half - abs(board.court_face_in - board.mid_in)
    house_embed = half - abs(face - board.mid_in)
    post = ctx.plan.by_tag(board.house_tag).__class__.__name__ == "FoundationWall"
    bars.development(d, court_embed, house_embed, post, states)


def _record(board, tags, states, missing, notes, inputs) -> EngineeringRecord:
    # OVER outranks INCOMPLETE, as on the other kinds: a graded shortfall is the finding.
    over = [s for s in states if not s.ok]
    status = Status.OVER if over else (Status.INCOMPLETE if missing else Status.OK)
    graded = ", ".join(f"{s.name} {s.ratio:.2f}" for s in states) or "nothing"
    summary = f"{board.tag}: {graded}"
    if over:
        summary += " — OVER on " + ", ".join(s.name for s in over)
    if missing:
        summary += f"; open: {len(missing)} item(s)"
    return EngineeringRecord(
        item_id=item_id(KIND, board.tag), kind=KIND, key=board.tag,
        basis_version=BASIS_VERSION, basis=BASIS, status=status, summary=summary,
        inputs=tuple(inputs), limit_states=tuple(states),
        missing=tuple(dict.fromkeys(missing)), notes=tuple(notes), element_tags=tags)
