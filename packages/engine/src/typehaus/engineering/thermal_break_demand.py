"""The refined demand for ``thermal_break`` — free body §11i (basis 6).

Three assumptions, each flagged in every record that reads them:

* **the neutral point** — the court's base friction fully mobilised (rigid-plastic) and its
  at-rest soil hold it, so only the part north of ``x`` grows toward the house (the
  subgrade-drag idealisation of ACI 360R-92 §6.3):
  ``x = (H + μwL) / (Σ k_i ε_i + 2μw)``, ``k_i = E A_i / t_i``;
* **the stems' drying shrinkage** (ACI 209R-92), credited against their closure only — the
  footings and the beam are in wet soil;
* **the pour lock-in** — a board that is a form face keeps its fresh-concrete squeeze after
  the court sets; added in full to every force (early-age cooling is reversible about the set
  position, so nothing relieves it — §11i). A board set into a stripped blockout carries none
  (§11j, basis 7).
"""

from __future__ import annotations

import math

from typehaus.engineering.thermal_break_board import ALPHA_C_PER_F, CONCRETE_PCF, pour_head_in
from typehaus.engineering.thermal_break_geometry import Board, court_run_in

#: ACI 209R-92 Eq. 2-8 inputs for a moist-cured wall end: ultimate 780 με, the drying days to
#: the first summer, ambient RH and the one-face-drying v/s of a 12" wall (free body §11i).
SHU_MICROSTRAIN, DRYING_DAYS, AMBIENT_RH, VOLUME_SURFACE_IN = 780.0, 270.0, 70.0, 12.0
PSI_PER_IN_OF_HEAD = CONCRETE_PCF / 1728.0

NEUTRAL_POINT_FLAG = (
    "ASSUMPTION — NEUTRAL POINT (free body §11i): the court's base friction is taken fully "
    "mobilised (the subgrade-drag idealisation of ACI 360R-92 §6.3). Mobilising it needs "
    "0.1-0.2\" of slip against the ~0.03\" at stake, and passive stiffness would move the "
    "neutral point toward the house — an estimate, not a bound.")
LOCK_IN_FLAG = (
    "ASSUMPTION — POUR LOCK-IN, NOT RELIEVED: every board keeps its fresh-concrete squeeze "
    "and it is added in full. Early-age cooling after the hydration peak is reversible "
    "about the set position (ACI 207.2R-07; ACI 231R-10's zero-stress temperature needs "
    "restraint, and a soft board gives none). Pressure decay at set is not credited.")


def stem_shrinkage() -> float:
    """ACI 209R-92 drying shrinkage at the first summer, strain."""
    return (SHU_MICROSTRAIN * 1e-6 * DRYING_DAYS / (35.0 + DRYING_DAYS)
            * (1.40 - 0.010 * AMBIENT_RH) * 1.2 * math.exp(-0.12 * VOLUME_SURFACE_IN))


def shrinkage_flag(eps: float) -> str:
    return (f"ASSUMPTION — STEM SHRINKAGE: ACI 209R-92, moist-cured, {DRYING_DAYS:.0f} d to "
            f"the first summer, RH {AMBIENT_RH:.0f}%, v/s {VOLUME_SURFACE_IN:.0f}\" = "
            f"{eps * 1e6:.2f} microstrain against the stem's closure. A first-summer estimate; "
            f"the wall's base restraint by its footing shortens less than a free end.")


def dries(ctx, board: Board) -> bool:
    """A wall end cast against the board, drying from its court face — the stems."""
    from typehaus.model.structure import FoundationWall

    return board.element is not None and isinstance(
        ctx.plan.by_tag(board.court_tag or ""), FoundationWall)


def closing_strain(ctx, board: Board, temps) -> float:
    eps = ALPHA_C_PER_F * temps.closing
    return max(0.0, eps - stem_shrinkage()) if dries(ctx, board) else eps


def neutral_point(ctx, boards: list[Board], products: dict, temps, free_bodies: dict,
                  e_scale: float = 1.0) -> dict:
    """``{loop ref: (x in, soil pcf, H lb, friction lb, L in)}`` — the case with the largest
    ``x`` (the most thrust) over the unit-weight band."""
    out = {}
    for ref in {b.loop_ref for b in boards if b.loop_ref}:
        mine = [b for b in boards if b.loop_ref == ref and products.get(b.tag)]
        body = free_bodies.get(ref)
        if not mine or not body:
            continue
        run = max(court_run_in(ctx, b) for b in mine)
        stiff = sum(products[b.tag].modulus_psi * e_scale * b.area_in2 / b.t_in
                    * closing_strain(ctx, b, temps) for b in mine)
        cases = []
        for pcf, (soil, friction) in body.items():
            mu_w = friction / run
            x = min(run, (soil + mu_w * run) / (stiff + 2.0 * mu_w))
            cases.append((x, float(pcf), soil, friction, run))
        out[ref] = max(cases)
    return out


FORMED_AND_STRIPPED_NOTE = (
    "FORMED AND STRIPPED (free body §11j): the court face was cast against a stripped "
    "blockout of the board's thickness and the board set into the slot afterwards — no "
    "fresh-concrete pressure reaches it and nothing is locked in. A field sequence the model "
    "states and cannot enforce: the placement annotation carries it to site.")


def pressure_at(ctx, board: Board):
    """``p(z)`` psi, the locked-in fresh pressure at elevation ``z`` in — zero for a board set
    into a stripped blockout, ``None`` where no head can be read."""
    if board.formed_and_stripped:
        return lambda _z: 0.0
    head, _how = pour_head_in(ctx, board)
    if head is None:
        return None
    top = board.bottom_in + head
    return lambda z: PSI_PER_IN_OF_HEAD * max(0.0, top - z)


def integrate(p, lo: float, hi: float, n: int = 400) -> tuple[float, float]:
    """``(∫p dz, ∫p·(z − lo) dz)`` over ``[lo, hi]`` — force and first moment per inch."""
    if hi <= lo:
        return 0.0, 0.0
    dz = (hi - lo) / n
    zs = [lo + (i + 0.5) * dz for i in range(n)]
    return sum(p(z) for z in zs) * dz, sum(p(z) * (z - lo) for z in zs) * dz


def lock_in_force(ctx, board: Board) -> float:
    if board.formed_and_stripped:
        return 0.0
    p = pressure_at(ctx, board)
    return 0.0 if p is None else integrate(p, board.bottom_in, board.top_in)[0] * board.length_in
