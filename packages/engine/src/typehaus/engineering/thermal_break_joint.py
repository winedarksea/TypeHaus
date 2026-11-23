"""The court-to-house joint: a conservative bound on the court's movement against the joint
as drawn (decision 29, free body §11r).

The boards are graded AT their compliant layer's published cap only while the layer stays
inside the strain its sheet publishes that cap at. What closes the joint:

* thermal closure — the whole run growing toward the house (``compliant layer strain``);
* the court's sliding movement toward the house — the friction its resultant mobilises
  times the ground motion at which a presumptive allowable is taken as mobilised. Friction
  is a lateral resistance, so the motion is the lateral anchor of
  ``soil.MOTION_AT_ALLOWABLE_BAND_IN`` (IBC §1806.3.4 pairs twice the tabular lateral value
  with 1/2", the tabular value with 1/4"); the band's top is printed as a sensitivity.

**Boards set after backfill** (owner, 2026-11-23): where the boards' placement annotation
says they go in after the retained sides are backfilled, the backfill's own sliding is spent
before the joint exists and only the increment to the worst graded service case counts, and
the boards are cut to the as-built slot (no construction pre-closure). Otherwise the whole
mobilisation counts and the slot tolerance is an open input. The veneer ties go in with the
boards and must take the same bound; that is graded on the tie's own record.

Capacity: the compliant layer's thickness x the strain its cap is published at. The foam
board in series compresses too; no published modulus bounds that from below, so it is
printed (off the C578 rating, linear to 10%) and not credited.
"""

from __future__ import annotations

import re

from typehaus.engineering.item import LimitState, Quantity
from typehaus.engineering.soil import MOTION_AT_ALLOWABLE_BAND_IN

NAME = "court-to-house joint closure"
#: The rating strain ASTM C578 reads a board's compressive strength at ("at yield or 10%").
RATING_STRAIN = 0.10
_AFTER_BACKFILL = re.compile(r"\bafter\b[^.]*\bbackfill", re.IGNORECASE)


def set_after_backfill(ctx, boards) -> bool:  # type: ignore[no-untyped-def]
    """Every authored board's placement annotation says it goes in after backfill."""
    refs = {b.element.placement_sequence_ref for b in boards if b.element is not None}
    if not refs or None in refs:
        return False
    texts = [getattr(ctx.plan.by_tag(r), "text", "") or "" for r in refs]
    return all("BOARD" in t.upper() and _AFTER_BACKFILL.search(t) for t in texts)


def joint_row(ctx, boards, products, temps, runs: dict, mobilised: dict | None):  # type: ignore[no-untyped-def]
    """``(LimitState | None, missing, inputs)`` for one loop's boards."""
    from typehaus.engineering.thermal_break_board import ALPHA_C_PER_F

    missing: list[str] = []
    capped = [(b, products[b.tag]) for b in boards
              if products.get(b.tag) is not None and products[b.tag].compliant is not None]
    if not capped or temps is None or not mobilised:
        return None, missing, []
    capacity = min(p.compliant.at_strain * p.compliant.thickness.inches for _, p in capped)
    thermal = max(ALPHA_C_PER_F * temps.closing * runs[b.tag] for b, _ in capped)
    squeeze = max(RATING_STRAIN * min(p.cap_psi, p.psi) / p.psi * b.t_in for b, p in capped)
    after = set_after_backfill(ctx, boards)
    moved, pcf = max(((wet - back if after else wet), float(k))
                     for k, (back, wet) in mobilised.items())
    low, high = MOTION_AT_ALLOWABLE_BAND_IN
    slide = moved * low
    demand = thermal + slide
    if not after:
        missing.append("the stripped slot's construction tolerance against the board (the "
                       "joint's as-built closure before any movement), stated on the model")
    inputs = [Quantity("joint_thermal", thermal, "in", 0.0001),
              Quantity("joint_board_squeeze", squeeze, "in", 0.0001),
              Quantity("joint_slide", slide, "in", 0.0001)]
    which = ("boards set after backfill: only the increment from the backfilled court to "
             "the worst graded service case" if after else "the whole mobilisation")
    return LimitState(
        NAME, demand, capacity, "in",
        f"thermal {thermal:.4f}\" + sliding {slide:.4f}\" ({which}: {moved:.3f} of the "
        f"friction at {pcf:.0f} pcf x {low:g}\", the lateral anchor; {moved * high:.3f}\" at "
        f"{high:g}\") against the compliant layer's {capacity:.3f}\" at its capped strain"
        + (". Boards cut to the as-built slot: no pre-closure" if after else "")
        + f". The ties go in with the boards and take the same {demand:.3f}\". The foam "
        f"board's own squeeze at the cap, up to {squeeze:.4f}\" off its rating, is not "
        f"credited"), missing, inputs
