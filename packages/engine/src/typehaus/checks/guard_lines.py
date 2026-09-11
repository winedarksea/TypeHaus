"""Everything that stands at a raised edge and stops a fall, as one population.

Every guard rule in ``checks/`` used to open with the same line —
``[e for e in plan.all_elements() if isinstance(e, Railing)]`` — which is not the question
those rules are asking. R312.1 governs a *guard*, and the IRC has nothing to say about which
class in this schema authored it. Three already leak past that line and each leaked
separately: a masonry parapet is a ``Wall`` with ``guard=True`` and ``structural.deck_guard``
grew its own branch for it; a stair throat is not a guard at all and
``edge_coverage._stair_throat_quads`` exists to say so.

A **slat screen** is the fourth, and it is the one that motivated this module. A screen of
on-edge 2x4s at a 1 1/2" clear gap, framed top and bottom into real cross rails that carry to
columns, is a guard by every test R312.1 applies: it stands at the edge, it is tall enough,
and a 4" sphere does not pass it. Modelled as a ``SlatScreen`` it was invisible to every rule
here, so a deck guarded by one read as a deck with no guard — and the workaround was to stand
a second, redundant ``Railing`` an inch away from it and bill an aluminium product nobody
buys. ``SlatScreen.role="guard"`` says the screen IS the guard, and this module is what makes
the rules see it.

The adapter is deliberately thin: it presents the fields the coverage derivation actually
reads and nothing else. A screen is NOT offered as a handrail — ``role`` here is the guard
question only, and R311.7.8 graspability is a different fixture with a different section.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.model.screens import SlatScreen
from typehaus.model.structure import Railing
from typehaus.quantities import Length

__all__ = ["GuardLine", "guard_lines"]


@dataclass(frozen=True)
class GuardLine:
    """The guard-shaped view of an element that guards an edge.

    Field for field what ``edge_coverage._uncovered_runs`` and ``structural.deck_guard``
    read off a ``Railing``. ``source`` keeps the authored element reachable for a rule that
    needs more than the common subset.
    """

    tag: str
    path: tuple
    height: Length
    base_elevation: Length
    infill: str | None
    baluster_spacing: Length | None
    source: object


def _from_railing(element: Railing) -> GuardLine:
    return GuardLine(tag=element.tag, path=tuple(element.path), height=element.height,
                     base_elevation=element.base_elevation, infill=element.infill,
                     baluster_spacing=element.baluster_spacing, source=element)


def _from_screen(element: SlatScreen) -> GuardLine:
    # A screen states its opening as ``clear_gap`` — the face-to-face gap between slats,
    # which is exactly the dimension R312.1.3 sphere-tests and exactly what
    # ``Railing.baluster_spacing`` means. ``infill="balusters"`` for the same reason: a
    # vertical member repeated at a clear gap is what that value describes, whatever the
    # member is made of.
    return GuardLine(tag=element.tag, path=(element.start, element.end),
                     height=element.height, base_elevation=element.base_elevation,
                     infill="balusters", baluster_spacing=element.clear_gap,
                     source=element)


def guard_lines(plan) -> list[GuardLine]:
    """Every authored line element that guards a raised edge, in authoring order.

    ``Railing`` in any role — a stair rail still covers the edge it runs along — plus every
    ``SlatScreen`` that declares ``role="guard"``. Guard *walls* are not here: a wall is a
    footprint rather than a path, and the coverage derivation already projects wall polygons
    on their own path.
    """
    out: list[GuardLine] = []
    for element in plan.all_elements():
        if isinstance(element, Railing):
            out.append(_from_railing(element))
        elif isinstance(element, SlatScreen) and element.role == "guard":
            out.append(_from_screen(element))
    return out
