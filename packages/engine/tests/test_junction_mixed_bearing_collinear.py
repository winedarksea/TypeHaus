"""A collinear tier of two DIFFERENT bearing materials, side by side, is owned.

A stud wall meeting the end of a pour on one bearing line has no transfer to detail: each
wall's load goes down its own path, the deck that spans onto the line lands on both, and
nothing in IRC R404.1.7 / R602.10.8 / R403.1.6 asks for a connection between them (the
reasoning and the citations live on ``_independent_bearing``). Catlin's N-B-C1 is the real
instance.

These tests pin the two guards that keep the clause from becoming a mute button — a wall
bearing on its neighbour, and a wall with no bearing element at all, both still report
UNKNOWN — because either one going quiet would turn a real transfer into a silent PASS.

``classify_storey_junctions`` is called directly rather than through ``resolve``: the
classification is a plan-level decision, and going through the whole pipeline would grade
these deliberately-minimal fixtures against every check in the engine.
"""

from __future__ import annotations

from typehaus.model import (
    Assembly,
    Layer,
    LayerFunction,
    Library,
    Material,
    Node,
    PlanModel,
    Storey,
    Wall,
    ft,
    inch,
    pt,
)
from typehaus.resolve.topology import classify_storey_junctions

#: Two bearing materials that are not each other, plus a stack with no bearing element.
_FRAMED = Assembly(tag="FRAMED", layers=(
    Layer(name="stud", material_ref="spf", thickness=inch(5.5),
          function=LayerFunction.STRUCTURE),
))
_POUR = Assembly(tag="POUR", layers=(
    Layer(name="concrete", material_ref="concrete", thickness=inch(12),
          function=LayerFunction.STRUCTURE),
))
_FINISH_ONLY = Assembly(tag="FINISH_ONLY", layers=(
    Layer(name="gwb", material_ref="gwb", thickness=inch(0.625),
          function=LayerFunction.FINISH),
))


def _collinear(project, north_assembly: str, south_assembly: str,
               south_base=None) -> PlanModel:
    """Two walls leaving node ``C`` in opposite directions along y — one collinear tier.

    ``south_base`` lifts the south wall off the storey datum, which is what a wall bearing
    on its neighbour rather than beside it looks like to the tier splitter.
    """
    library = Library(
        materials=tuple(Material(tag=tag, name=tag)
                        for tag in ("spf", "concrete", "gwb")),
        assemblies=(_FRAMED, _POUR, _FINISH_ONLY),
    )
    storey = Storey(uid="STMIXBEAR", tag="main", elevation=ft(0),
                    default_ceiling_height=ft(9))
    nodes = [
        Node(uid="JNMIX0001", tag="N", position=pt(ft(0), ft(20)), open_end=True),
        Node(uid="JNMIX0002", tag="C", position=pt(ft(0), ft(10))),
        Node(uid="JNMIX0003", tag="S", position=pt(ft(0), ft(0)), open_end=True),
    ]
    walls = [
        Wall(uid="JWMIX0001", tag="W-N", start_node="C", end_node="N",
             assembly=north_assembly, top=ft(9)),
        Wall(uid="JWMIX0002", tag="W-S", start_node="C", end_node="S",
             assembly=south_assembly, top=ft(9), base_elevation=south_base),
    ]
    return PlanModel(project=project, library=library,
                     storeys=(storey,)).with_elements("main", [*nodes, *walls])


def _tier(plan: PlanModel):
    return next(item for item in classify_storey_junctions(plan, "main")
                if item.node_tag == "C")


def test_side_by_side_mixed_bearing_collinear_tier_is_owned(project) -> None:
    """Different bearing materials, same elevations: neither bears on the other."""
    tier = _tier(_collinear(project, "POUR", "FRAMED"))
    assert tier.kind == "collinear"
    assert tier.supported and tier.diagnostic is None


def test_same_bearing_material_is_still_owned_by_continuity(project) -> None:
    """The pre-existing ``_shared_bearing`` path is untouched by the new clause."""
    tier = _tier(_collinear(project, "FRAMED", "FRAMED"))
    assert tier.supported and tier.diagnostic is None


def test_a_wall_bearing_on_its_neighbour_still_reports_unknown(project) -> None:
    """NEGATIVE: lifted off the datum, the south wall sits partway up the north one — a
    ledge or pocket bearing, which is a real transfer and wants a real detail."""
    tier = _tier(_collinear(project, "POUR", "FRAMED", south_base=ft(2)))
    assert tier.kind == "collinear"
    assert not tier.supported
    assert tier.diagnostic == "mixed-assembly junction requires interface rules"


def test_a_side_with_no_bearing_element_still_reports_unknown(project) -> None:
    """NEGATIVE: nothing to bear on is a modelling gap, not a transition. Coincident
    elevations must not be enough on their own to close the finding."""
    tier = _tier(_collinear(project, "POUR", "FINISH_ONLY"))
    assert not tier.supported
    assert tier.diagnostic == "mixed-assembly junction requires interface rules"


def test_catlin_stud_wall_meeting_the_pour_end_is_owned(catlin_plan) -> None:
    """The real instance: W-B-CS3's 2x6 studs meet W-B-CS2's 12" pour end-on at N-B-C1,
    both spanning the same z. It is the only junction in the house this clause closes."""
    tier = next(item for item in classify_storey_junctions(catlin_plan, "basement")
                if item.node_tag == "N-B-C1")
    assert tier.kind == "collinear"
    assert {item.wall_tag for item in tier.incidents} == {"W-B-CS2", "W-B-CS3"}
    assert len({item.assembly for item in tier.incidents}) == 2
    assert tier.supported and tier.diagnostic is None


def test_no_junction_in_the_house_is_left_unowned(catlin_plan) -> None:
    """``integrity.junction_fallback`` is clean house-wide, so a future edit that reopens a
    junction fails here rather than only in the build's warning stream."""
    unowned = [item.node_tag
               for storey in catlin_plan.storeys
               for item in classify_storey_junctions(catlin_plan, storey.tag)
               if not item.supported]
    assert unowned == []
