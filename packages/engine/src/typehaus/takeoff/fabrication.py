"""The fabrication schedule: what a *made-to-order* member has to be built to.

Every other framing row is stock cut from a pile, where the length is an ordering unit. A
floor truss is engineered, plated and shipped to one length, and what goes on the order is
its **overall length** — not the span line it was cut at, not the stock ladder it prices
against. Wrong by 3/4" and it either will not drop in or lands short of its own seat.

So, per deck and per distinct length: overall length, clear span (face of support to face of
support, what the truss is designed for), the seat at each end, and the clear chord-to-chord
opening — on this house the reason the member was specified at all. All read off the
resolved members and ``ResolvedFloor.ends``, so schedule and geometry cannot disagree.
"""

from __future__ import annotations

from collections import defaultdict

from typehaus.model.floors import FloorSystem
from typehaus.quantities import M_PER_IN
from typehaus.resolve.floor_ends import FloorEnds
from typehaus.resolve.framing.profiles import cross_section, open_web_opening_m
from typehaus.resolve.model import ResolvedModel

#: Shapes bought fabricated to length rather than cut from stock. Mirrors the fabricated
#: branch of ``takeoff/framing.py::_order_length_ft`` — the two read the same shape name.
FABRICATED_SHAPES = frozenset({"floor_truss"})
#: Lengths within this of each other are the same piece. A hundredth of an inch: the model
#: works in metres and a shared bearing line reaches the same tip by two float paths.
_LENGTH_TOL_M = 0.01 * M_PER_IN


def _feet_inches(metres: float) -> str:
    """``17'-11"`` — the form a fabricator's order is written in, to 1/16"."""
    total = metres / M_PER_IN
    feet, inches = divmod(round(total * 16) / 16, 12)
    return f"{int(feet)}'-{inches:g}\""


def fabricated_member_schedule(model: ResolvedModel) -> list[dict[str, object]]:
    """One row per (deck, member, overall length) for every fabricated framing member."""
    rows: list[dict[str, object]] = []
    for floor in model.floors:
        system = model.plan.by_tag(floor.tag)
        if not isinstance(system, FloorSystem):
            continue
        section = cross_section(system.joists.member)
        if section.shape not in FABRICATED_SHAPES:
            continue
        groups: dict[str, list[float]] = defaultdict(list)
        for member in floor.members:
            if cross_section(member.profile).shape not in FABRICATED_SHAPES:
                continue
            groups[member.category].append(member.length_m)
        ends = floor.ends
        opening = open_web_opening_m(section)
        spacing = system.joists.spacing
        for category, lengths in sorted(groups.items()):
            for length, count in _bucket(lengths):
                # Seats belong to full-length members only: a piece clipped by a floor
                # opening lands on a header, and would name a plate it never reaches.
                full = (ends if ends is not None
                        and abs(length - (ends.tip_hi - ends.tip_lo)) <= _LENGTH_TOL_M
                        else None)
                seat_lo = None if full is None or full.seat_lo is None else full.seat_lo
                seat_hi = None if full is None or full.seat_hi is None else full.seat_hi
                rows.append({
                    "floor": floor.tag,
                    "storey": floor.storey,
                    "category": category,
                    "profile": system.joists.member,
                    "pieces": count,
                    "overall_length_ft_in": _feet_inches(length),
                    "overall_length_in": round(length / M_PER_IN, 4),
                    "depth_in": round(section.depth_m / M_PER_IN, 4),
                    "spacing_in": None if spacing is None else round(spacing.inches, 4),
                    "clear_span_ft_in": (None if full is None
                                         else _feet_inches(_clear_span(full, length))),
                    "bearing_low_in": (None if seat_lo is None
                                       else round(seat_lo / M_PER_IN, 4)),
                    "bearing_high_in": (None if seat_hi is None
                                        else round(seat_hi / M_PER_IN, 4)),
                    "chord_clear_opening_in": (None if opening is None
                                               else round(opening / M_PER_IN, 4)),
                })
    return rows


def _clear_span(ends: FloorEnds, length_m: float) -> float:
    """Face of support to face of support: the overall length less both seats."""
    return length_m - (ends.seat_lo or 0.0) - (ends.seat_hi or 0.0)


def _bucket(lengths: list[float]) -> list[tuple[float, int]]:
    """``(length, count)`` longest first, lengths within a hundredth of an inch merged."""
    out: list[list[float | int]] = []
    for length in sorted(lengths, reverse=True):
        if out and abs(out[-1][0] - length) <= _LENGTH_TOL_M:
            out[-1][1] += 1
            continue
        out.append([length, 1])
    return [(float(length), int(count)) for length, count in out]
