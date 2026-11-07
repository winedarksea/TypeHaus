"""What a duct turn costs in straight duct: the elbow's take-off, and the port kit's lead.

**Take-off.** A turn of angle theta takes ``R tan(theta/2)`` of straight from each leg, R
the elbow's 90-degree centre-to-face. Two consecutive turns need the sum of theirs between
them; a turn beside a run end (collar, port, tee, terminal) owes only its own. The elbow is
the one ``resolve/duct_standard.elbow_for_turn`` buys (decision #114) — the same reading
``mep.fitting_pattern`` grades and the take-off bills — so router, check and bill cannot
disagree about the part. Its R is the row's ``center_to_face`` where read, else the
catalogued gored radius (1.5 D, SMACNA), the stand-in the check uses for an unpublished
stamped elbow. A round turn no row makes is a gored elbow FABRICATED to the angle, and a
rectangular turn always is: no throat radius is read for one, so its take-off is unknown
(0 here) and it is priced as a last resort instead.

**Lead.** A ``PortKit`` (Broan: 6-to-8 transition where the duct is not the port's size,
then 12" of flex) stands between a port and the first rigid fitting. The flex is a straight
lead that never bends — no minimum bend radius is on file — so the search starts at its
far end. An unread transition length counts 0 and says so.

``houses/catlin/notes/mep_duct_routing_basis.md`` §7 (take-off) and §8 (lead) are the
oracle.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from typehaus.quantities import M_PER_IN
from typehaus.resolve.duct_standard import elbow_for_turn
from typehaus.resolve.mep_fittings import KIND_ELBOW, SERVICE_DUCT, fitting_for

#: A shop-made elbow's price on top of a stock one's, inches of equivalent travel: a stated
#: weight (a fabricated fitting is a last resort), not a datasheet value.
FABRICATED_ELBOW_IN = 48.0
#: The pair a short jog is offset with, steepest first (the shorter slide): a stamped 45,
#: and the 30 catlin authors its FS-S-WEST tier changes with (§7.4).
OFFSET_ANGLES: tuple[float, ...] = (45.0, 30.0)


@dataclass(frozen=True)
class Elbow:
    """The part a turn is made with. ``radius_m`` is its 90-degree centre-to-face, or None
    where nothing reads one (a rectangular throat)."""

    radius_m: float | None
    basis: str  # "bought" | "stand-in" | "fabricated"

    @property
    def fabricated(self) -> bool:
        return self.basis == "fabricated"

    def takeoff_m(self, angle_deg: float) -> float:
        return takeoff_m(self.radius_m or 0.0, angle_deg)


def takeoff_m(radius_m: float, angle_deg: float) -> float:
    """``R tan(theta/2)``: the straight one turn takes from each of its legs."""
    return radius_m * math.tan(math.radians(angle_deg) / 2.0)


def floor_takeoff_m(diameter_m: float, angle_deg: float) -> float:
    """The take-off at R = D/2, the tightest throat any round elbow is made with."""
    return takeoff_m(diameter_m / 2.0, angle_deg)


def min_straight_m(*takeoffs: float) -> float:
    """The straight two consecutive turns (or a turn and a run end, at 0) need between them."""
    return sum(takeoffs)


def stand_in_radius_m(diameter_m: float) -> float | None:
    """The catalogued gored elbow's centreline radius at this size, or None off-catalog."""
    spec = fitting_for(SERVICE_DUCT, KIND_ELBOW, 90.0, round(diameter_m / M_PER_IN, 3))
    radius = getattr(spec, "bend_radius_in", None)
    return radius * M_PER_IN if radius else None


def elbow(standard: Any, angle_deg: float, *, diameter_m: float | None = None) -> Elbow:
    """The elbow a turn of ``angle_deg`` is made with, at ``diameter_m`` (None: rectangular)."""
    if not diameter_m:
        return Elbow(None, "fabricated")
    hit = elbow_for_turn(standard, diameter_m, angle_deg) if standard is not None else None
    if hit is not None and hit[0].center_to_face is not None:
        return Elbow(hit[0].center_to_face.meters, "bought")
    return Elbow(stand_in_radius_m(diameter_m) or 1.5 * diameter_m,
                 "stand-in" if hit is not None else "fabricated")


@dataclass(frozen=True)
class KitLead:
    """The straight a port kit puts between a port face and the first rigid fitting."""

    length_m: float
    #: What the length leaves out because nothing on file reads it.
    unread: tuple[str, ...] = ()

    @property
    def inches(self) -> float:
        return self.length_m / M_PER_IN


def kit_lead(kit: Any, *, needs_transition: bool) -> KitLead | None:
    """Transition (where the duct is not the port's size) + flex, or None without a kit."""
    if kit is None:
        return None
    length, unread = 0.0, []
    if kit.transition_product_ref and needs_transition:
        if kit.transition_length is None:
            unread.append(f"{kit.transition_product_ref}'s length is unread, counted 0")
        else:
            length += kit.transition_length.meters
    if kit.flex_length is not None:
        length += kit.flex_length.meters
    elif kit.flex_product_ref:
        unread.append(f"{kit.flex_product_ref}'s length is unread, counted 0")
    return KitLead(length, tuple(unread))


def lead_shortfall_m(points: list[tuple[float, float, float]], lead_m: float) -> float:
    """How far the first straight of ``points`` (port first) falls short of the kit lead,
    or 0: the flex has to be laid straight before anything rigid turns."""
    straight, heading = 0.0, None
    for a, b in zip(points, points[1:], strict=False):
        length = math.dist(a, b)
        if length < 1e-9:
            continue
        unit = tuple((q - p) / length for p, q in zip(a, b, strict=True))
        if heading is not None and sum(u * h for u, h in zip(unit, heading, strict=True)) \
                < 1.0 - 1e-9:
            break  # the first turn
        heading, straight = unit, straight + length
    return max(0.0, lead_m - straight)
