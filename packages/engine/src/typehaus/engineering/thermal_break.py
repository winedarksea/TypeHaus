"""A compressible board between two separately founded pours — a pure isolation joint.
``thermal_break_transfer/<board tag>``.

**Nothing crosses the break, and no row grades a shear across it**: the court holds its own
thrust (``retaining_system``) and the board keeps the house out of that free body. What is
graded is what the board and the house behind it must survive — free body §11 (basis 5),
hand-worked first:

* the board — fresh-concrete pressure on the AUTHORED placement (ACI 347R-14, capped at wh)
  and closing movement against its recoverable strain ``σ_y / E``;
* the thrust it then passes, ``min(E·δ/t, σ_y) × A`` — into the house wall (flexure, shear,
  the floor line, the house's own insulation) or the house strip (sliding, bearing), and
  back into the court (sliding under the sum of every board on the loop).

Temperatures come from ``Site.concrete_service_temperature`` (a cited concrete range and a
specified set floor), never design air. Boards are ``IsolationBoard`` elements and cast walls
or beams in a retaining loop whose assembly carries an insulating layer facing a house
footing. A row over its capacity makes the item OVER even while an input is still missing.
"""

from __future__ import annotations

from typehaus.engineering import thermal_break_board as brd
from typehaus.engineering import thermal_break_geometry as geo
from typehaus.engineering import thermal_break_house as house
from typehaus.engineering.item import EngineeringRecord, Oracle, Quantity, Status, item_id
from typehaus.engineering.registry import EngineeringContext, calc, keys, oracled_by
from typehaus.engineering.retaining_system import footing_shortfalls, loop_free_bodies
from typehaus.engineering.thermal_break_board import ALPHA_C_PER_F

KIND = "thermal_break_transfer"
BASIS = ("ACI 347R-14 (fresh-concrete pressure); ACI 318-19 (house wall); IBC 1806.2 "
         "(sliding); IRC R404.4 loop")
#: Bumped whenever the arithmetic below changes — it rides in the fingerprint.
BASIS_VERSION = "5"

oracled_by(KIND, Oracle(note="sunken_garden_court_free_body.md", section="§11",
                        test="tests/test_thermal_break.py"))


def _boards(ctx: EngineeringContext, loops: dict) -> list[geo.Board]:
    out = [b for e in geo.isolation_boards(ctx)
           if (b := geo.authored_board(ctx, e, loops)) is not None]
    return out + geo.layer_boards(ctx, loops)


@keys(KIND)
def enumerate_breaks(ctx: EngineeringContext) -> list[str]:
    """Every ``IsolationBoard``, and every cast wall or beam in a retaining loop whose
    assembly carries an insulating layer facing a house footing."""
    loops = footing_shortfalls(ctx)
    return sorted({e.tag for e in geo.isolation_boards(ctx)}
                  | {b.tag for b in geo.layer_boards(ctx, loops)})


@calc(KIND)
def compute(ctx: EngineeringContext) -> list[EngineeringRecord]:
    loops = footing_shortfalls(ctx)
    boards = _boards(ctx, loops)
    temps = brd.temps(ctx)
    products = {b.tag: brd.product_of(b.element) for b in boards if b.element is not None}
    # A layer board names no product of its own (a Layer has no compressive field); it is the
    # product the same court's authored boards name — `test_catlin_contract_m3` pins that.
    for b in boards:
        if b.element is None:
            products[b.tag] = next((products[o.tag] for o in boards if o.element is not None
                                    and o.loop_ref == b.loop_ref and products[o.tag]), None)
    sigma = {}
    for b in boards:
        p = products[b.tag]
        if p is not None and temps is not None:
            delta = ALPHA_C_PER_F * temps.closing * geo.court_run_in(ctx, b)
            sigma[b.tag] = min(p.modulus_psi * delta / b.t_in, p.psi)
    thrust = {b.tag: sigma[b.tag] * b.area_in2 for b in boards if b.tag in sigma}
    patches = {b.tag: house.wall_patch(ctx, b, sigma[b.tag]) for b in boards
               if b.tag in sigma and b.element is not None and b.house_tag
               and ctx.plan.by_tag(b.house_tag).__class__.__name__ == "FoundationWall"}
    shared = dict(boards=boards, temps=temps, products=products, sigma=sigma, thrust=thrust,
                  patches=patches, free_bodies=loop_free_bodies(ctx))
    return [_one(ctx, b, shared) for b in sorted(boards, key=lambda b: b.tag)]


def _one(ctx, board, sh) -> EngineeringRecord:
    element = board.element
    tags = tuple(dict.fromkeys((board.tag, *(element.connects if element else ()))))
    states, missing = [], []
    notes = ["A PURE ISOLATION JOINT: nothing crosses it and no row grades a shear across it. "
             "The court closes its own free body (`retaining_system`); every row below is the "
             "board's own survival or the thrust it passes.",
             "RETIRED WITH THE BARS (free body §11e): shear reserve, differential settlement, "
             "racking drift, joint opening and development — there is no tie to grade.",
             "NO FLOTATION ROW: nothing restrains a board with no bars, so it is held by the "
             "work — adhered or pinned to the cured house face and braced (sequencing trap 2)."]
    inputs = [Quantity("board_t", board.t_in, "in", 0.01),
              Quantity("board_h", board.h_in, "in", 0.01),
              Quantity("board_L", board.length_in, "in", 0.01)]
    product, temps = sh["products"].get(board.tag), sh["temps"]
    if product is None:
        missing.append(f"IsolationBoard.psi, modulus_psi and source for {board.tag} — the "
                       f"rating, modulus and datasheet every board row reads")
        return _record(board, tags, states, missing, notes, inputs)
    inputs.append(Quantity("foam_psi", product.psi, "psi", 0.1))
    pour = brd.pressure(ctx, board, product, states, missing, inputs)
    if temps is None:
        missing.append(brd.TEMPERATURE_MISSING)
    else:
        brd.movement(ctx, board, product, temps, states, inputs)
    if board.tag in sh["sigma"]:
        _thrust_rows(ctx, board, sh, pour, states, missing, inputs)
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
        # The wall-end board above an authored footing board lands its wall's base reaction
        # on the same strip.
        for other in sh["boards"]:
            p = sh["patches"].get(other.tag)
            if p is None or board.element is None:
                continue
            if {t for t in facing if ctx.plan.by_tag(t).under == other.house_tag}:
                loads.append((p["bottom_reaction"], geo.z_extent(ctx, other.house_tag)[0] - base,
                              f"{other.house_tag} base under {other.tag}"))
        house.footing_rows(ctx, board, facing, loads, states, missing, inputs)
    if board.loop_ref is not None:
        total = sum(sh["thrust"].get(b.tag, 0.0) for b in sh["boards"]
                    if b.loop_ref == board.loop_ref)
        house.court_sliding(ctx, board.loop_ref, total, sh["free_bodies"], states, missing)


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
