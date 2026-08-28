"""Self-adhered membrane over framing tops, by the lineal foot.

Joist tape is bought and installed by the foot of member it covers, which is a quantity
nothing else in the BOM reports. ``framing`` counts sticks by (profile, category) across the
whole house, so "the two garden decks' joists" is not addressable there; ``structural_solids``
bills the standalone beams by the cubic yard. Neither can answer "how many feet of tape".

Two sources, both authored — this section derives nothing it was not told:

* :attr:`~typehaus.model.floors.FloorSystem.top_protection` — every joist, rim and blocking
  member the deck resolved, matched back to its floor system by ``parent_uid``.
* :attr:`~typehaus.model.structure.Beam.top_protection` — the beam's own axis length, taken
  off its two nodes exactly the way ``resolve/envelope.py::_resolve_beam`` takes it.

The row carries ``width_in`` because tape is sold in widths and the width is a decision, not
a constant: a 3-ply 2x12 is 4 1/2" across and the common 3 1/8" "double joist" roll does not
cover it. The width comes off the member's own cross-section, so a beam that gains a ply
orders wider tape instead of quietly under-covering.
"""

from __future__ import annotations

import math

from typehaus.model.floors import FloorSystem
from typehaus.model.structure import Beam
from typehaus.quantities import M_PER_IN
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import ResolvedModel

_M_TO_FT = 3.280839895013123

#: Member categories a deck's ``top_protection`` covers. A joist, the rim closing its ends
#: and the blocking between them all present an up-facing top the deck sheet sits on. Posts
#: and hangers do not, and a stud is not part of a floor system at all.
_TAPED_CATEGORIES = frozenset({"joist", "rim", "blocking"})


def _rounded_width_in(profile: str) -> float:
    """The member's actual cross-section width, in inches — the tape has to cover it."""
    try:
        return round(cross_section(profile).width_m / M_PER_IN, 3)
    except Exception:
        # An unknown profile must not lose the run: report the length with no width rather
        # than dropping the member, so the order is short a dimension and never short a foot.
        return 0.0


class _Rows:
    """Accumulator keyed on what makes two runs the same line on the order."""

    def __init__(self) -> None:
        self._rows: dict[tuple[str, str, float], dict[str, object]] = {}

    def add(self, material: str, scope: str, width_in: float, *, tag: str,
            length_m: float) -> None:
        key = (material, scope, width_in)
        row = self._rows.get(key)
        if row is None:
            row = self._rows[key] = {
                "material": material, "scope": scope, "width_in": width_in,
                "count": 0, "length_m": 0.0, "tags": set(),
            }
        row["count"] = int(row["count"]) + 1
        row["length_m"] = float(row["length_m"]) + length_m
        tags = row["tags"]
        assert isinstance(tags, set)
        tags.add(tag)

    def finish(self) -> list[dict[str, object]]:
        out: list[dict[str, object]] = []
        for key in sorted(self._rows, key=lambda k: (k[0], k[1], k[2])):
            row = self._rows[key]
            tags = row["tags"]
            assert isinstance(tags, set)
            out.append({
                "material": row["material"],
                "scope": row["scope"],
                "width_in": row["width_in"],
                "count": int(row["count"]),
                "length_ft": round(float(row["length_m"]) * _M_TO_FT, 1),
                "tags": sorted(tags),
            })
        return out


def member_protection_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Lineal feet of framing-top membrane, grouped by material, scope and tape width."""
    rows = _Rows()

    # --- decks: every taped member the floor system resolved ---------------------------
    decks = {el.uid: el for storey in model.plan.storeys
             for el in model.plan.storey_elements(storey.tag)
             if isinstance(el, FloorSystem) and el.top_protection}
    if decks:
        for member in model.all_members():
            deck = decks.get(member.parent_uid)
            if deck is None or member.category not in _TAPED_CATEGORIES:
                continue
            assert deck.top_protection is not None
            rows.add(deck.top_protection, "deck", _rounded_width_in(member.profile),
                     tag=deck.tag, length_m=member.length_m)

    # --- standalone beams: the axis length, off the same two nodes the resolver uses ----
    for storey in model.plan.storeys:
        elements = list(model.plan.storey_elements(storey.tag))
        nodes = {e.tag: e.position.xy_m for e in elements if e.element_kind == "Node"}
        for element in elements:
            if not isinstance(element, Beam) or not element.top_protection:
                continue
            p0, p1 = nodes.get(element.start_node), nodes.get(element.end_node)
            if p0 is None or p1 is None:
                continue
            rows.add(element.top_protection, "beam", _rounded_width_in(element.size),
                     tag=element.tag, length_m=math.dist(p0, p1))
    return rows.finish()
