"""Winding is per structure, not per storey (→ resolve/orientation).

A storey key names a floor level, not a building. Catlin's ``basement`` carries the house
basement, the garage foundation, the retaining garden and the sunken garden — four
independent wall loops, each free to be authored with its own winding. Deriving one scalar
from the largest loop forced the other three to inherit its answer, which built them
inside-out; ``advisory.cladding_side_mismatch`` could only detect that after the fact.
"""

from __future__ import annotations

from typehaus.model import (
    Building,
    Library,
    Node,
    PlanModel,
    Project,
    Site,
    Storey,
    Wall,
    m,
    pt,
)
from typehaus.resolve.orientation import (UNRECOVERABLE_WINDING_OUTWARD_SIGN,
                                          resolve_storey_windings, storey_outward_sign)

_ASSEMBLY_REF = "A-WALL"


def _square_loop(prefix: str, x0: float, y0: float, side: float, *, counter_clockwise: bool):
    """Four nodes and four walls closing a square, authored in the requested direction."""
    corners = [(x0, y0), (x0 + side, y0), (x0 + side, y0 + side), (x0, y0 + side)]
    if not counter_clockwise:
        corners.reverse()
    nodes = tuple(
        Node(uid=f"{prefix}-node-{index}", tag=f"{prefix}-N{index}", position=pt(m(x), m(y)))
        for index, (x, y) in enumerate(corners)
    )
    walls = tuple(
        Wall(uid=f"{prefix}-wall-{index}", tag=f"{prefix}-W{index}",
             start_node=nodes[index].tag, end_node=nodes[(index + 1) % len(nodes)].tag,
             assembly=_ASSEMBLY_REF)
        for index in range(len(nodes))
    )
    return nodes + walls


def _plan(*elements) -> PlanModel:
    return PlanModel(
        project=Project(name="test", project_uuid="00000000-0000-0000-0000-000000000099",
                        building=Building(name="test"),
                        site=Site(lat=0, lon=0, elevation=m(0))),
        storeys=(Storey(tag="ground", elevation=m(0), default_ceiling_height=m(3)),),
        library=Library(),
        elements={"ground": elements},
    )


def test_two_disjoint_loops_on_one_storey_resolve_opposite_windings() -> None:
    """The bug class: a smaller structure used to inherit the largest loop's sign."""
    plan = _plan(
        # The larger structure, authored counter-clockwise.
        *_square_loop("BIG", 0.0, 0.0, 10.0, counter_clockwise=True),
        # A separate structure well clear of it, authored the other way round.
        *_square_loop("SMALL", 40.0, 40.0, 4.0, counter_clockwise=False),
    )

    windings = resolve_storey_windings(plan, "ground")
    assert len(windings.sign_by_component_key) == 2
    big_sign = windings.sign_for_wall(next(e for e in plan.storey_elements("ground")
                                           if e.tag == "BIG-W0"))
    small_sign = windings.sign_for_wall(next(e for e in plan.storey_elements("ground")
                                             if e.tag == "SMALL-W0"))
    assert big_sign == -1.0
    assert small_sign == 1.0
    # The legacy whole-storey answer is the largest structure's, which is exactly what the
    # smaller one must no longer inherit.
    assert storey_outward_sign(plan, "ground") == big_sign


def test_both_loops_agree_when_both_are_authored_the_same_way() -> None:
    plan = _plan(
        *_square_loop("BIG", 0.0, 0.0, 10.0, counter_clockwise=True),
        *_square_loop("SMALL", 40.0, 40.0, 4.0, counter_clockwise=True),
    )

    windings = resolve_storey_windings(plan, "ground")
    assert set(windings.sign_by_component_key.values()) == {-1.0}


def test_a_component_with_no_closed_loop_keeps_its_authored_geometry() -> None:
    """A freestanding run has no inside to point away from, so nothing may flip it."""
    plan = _plan(
        *_square_loop("BIG", 0.0, 0.0, 10.0, counter_clockwise=True),
        Node(uid="free-a", tag="FREE-NA", position=pt(m(40), m(40))),
        Node(uid="free-b", tag="FREE-NB", position=pt(m(46), m(40))),
        Wall(uid="free-w", tag="FREE-W", start_node="FREE-NA", end_node="FREE-NB",
             assembly=_ASSEMBLY_REF),
    )

    windings = resolve_storey_windings(plan, "ground")
    free_wall = next(e for e in plan.storey_elements("ground") if e.tag == "FREE-W")
    assert windings.sign_for_wall(free_wall) == UNRECOVERABLE_WINDING_OUTWARD_SIGN
    assert windings.sign_for_wall(next(e for e in plan.storey_elements("ground")
                                       if e.tag == "BIG-W0")) == -1.0


def test_catlin_basement_structures_resolve_independently(catlin_model) -> None:
    """Four structures share the ``basement`` key; each must answer for itself."""
    windings = resolve_storey_windings(catlin_model.plan, "basement")

    # The house basement, the garage foundation, the retaining garden, the sunken garden.
    assert len(windings.sign_by_component_key) == 4
    basement_walls = [e for e in catlin_model.plan.storey_elements("basement")
                      if e.element_kind in ("Wall", "FoundationWall")]
    sunken_garden = next(w for w in basement_walls if w.start_node.startswith("N-SG-"))
    house = next(w for w in basement_walls if w.start_node.startswith("N-B-"))
    assert (windings.component_key_for_wall(sunken_garden)
            != windings.component_key_for_wall(house))
    # Catlin authors both clockwise-in-plan today; the point is that each was traced on its
    # own outer loop rather than one borrowing the other's scalar.
    assert windings.sign_for_wall(sunken_garden) == -1.0
    assert windings.sign_for_wall(house) == -1.0
