"""The court-to-house joint: a conservative bound on the court's movement against the joint
as drawn (decision 29, free body §11r).

The boards are graded AT their compliant layer's published cap only while the layer stays
inside the strain its sheet publishes that cap at. Everything that closes the joint counts:

* thermal closure — the whole run growing toward the house (``compliant layer strain``);
* the court's sliding movement toward the house — the friction its resultant mobilises
  (dry body, the adverse band end) times the ground motion at which a presumptive allowable
  is taken as mobilised (``soil.MOTION_AT_ALLOWABLE_BAND_IN``), graded at the band's top;
* construction tolerance on the slot, and the veneer ties' travel — read from the model
  where it states them, otherwise named as missing.

Capacity: the compliant layer's thickness x the strain its cap is published at. The foam
board in series with it compresses too, which would add room; no published modulus bounds
that from below, so it is printed (off the C578 rating, linear to 10%) and not credited.
"""

from __future__ import annotations

from typehaus.engineering.item import LimitState, Quantity
from typehaus.engineering.soil import MOTION_AT_ALLOWABLE_BAND_IN

NAME = "court-to-house joint closure"
#: The rating strain ASTM C578 reads a board's compressive strength at ("at yield or 10%").
RATING_STRAIN = 0.10


def joint_row(boards, products, temps, runs: dict, body: dict | None):  # type: ignore[no-untyped-def]
    """``(LimitState | None, missing, inputs)`` for one loop's boards."""
    from typehaus.engineering.thermal_break_board import ALPHA_C_PER_F

    missing: list[str] = []
    capped = [(b, products[b.tag]) for b in boards
              if products.get(b.tag) is not None and products[b.tag].compliant is not None]
    if not capped or temps is None or not body:
        return None, missing, []
    capacity = min(p.compliant.at_strain * p.compliant.thickness.inches for _, p in capped)
    thermal = max(ALPHA_C_PER_F * temps.closing * runs[b.tag] for b, _ in capped)
    squeeze = max(RATING_STRAIN * min(p.cap_psi, p.psi) / p.psi * b.t_in for b, p in capped)
    fraction, pcf = max(((push / friction, float(k)) for k, (push, friction) in body.items()
                         if friction), default=(0.0, 0.0))
    low, high = MOTION_AT_ALLOWABLE_BAND_IN
    slide = fraction * high
    demand = thermal + slide
    missing += [
        "the stripped slot's construction tolerance against the board (the joint's "
        "as-built closure before any movement), stated on the model",
        "the veneer ties' published travel across the joint, from the tie product the "
        "model names (decision 29: the ties must follow the bounded court movement)"]
    inputs = [Quantity("joint_thermal", thermal, "in", 0.0001),
              Quantity("joint_board_squeeze", squeeze, "in", 0.0001),
              Quantity("joint_slide", slide, "in", 0.0001)]
    return LimitState(
        NAME, demand, capacity, "in",
        f"thermal {thermal:.4f}\" + sliding {slide:.3f}\" (the court body mobilises "
        f"{fraction:.2f} of its friction at {pcf:.0f} pcf, x {high:g}\" at full mobilisation; "
        f"{fraction * low:.3f}\" at {low:g}\") against the compliant layer's "
        f"{capacity:.3f}\" at its capped strain; as drawn {capacity - thermal:.3f}\" is left "
        f"after thermal closure. The foam board's own squeeze at the cap, up to "
        f"{squeeze:.4f}\" off its rating, is not credited"), missing, inputs
