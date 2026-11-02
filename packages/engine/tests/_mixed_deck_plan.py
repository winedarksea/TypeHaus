"""A mixed main floor in miniature: a joisted bay beside a suspended EPS-formed pour.

Catlin's ``SL-M-DECK`` retired 2026-11-01 (decision #112); this keeps its numbers so the
features it exercised still have a case. One 18'-0" bay between two 12" pours (x 0 and 18'),
closed by two more (y 0 and 30'). The wood bay is y 0..12', the deck y 12'..30', both
spanning x — so they meet along a line no wall stands under, and the one basement room
straddles them.

Section, as catlin authored it: 11 7/8" TJI on a 1 1/2" mudsill + 1/16" gasket, so the seat
is -13 7/16"; the deck is a 10" EPS form under a 4 3/16" cap, its top pinned at the 3/4"
subfloor top, so its soffit lands on the same seat.
"""

from __future__ import annotations

import uuid
from functools import lru_cache

from typehaus.model import (
    Assembly,
    Building,
    ConcreteSpec,
    DeckLayer,
    FloorSystem,
    FoundationWall,
    JoistSpec,
    Layer,
    LayerFunction,
    Library,
    Material,
    Node,
    Occupancy,
    PipeRun,
    PipeSystem,
    PlanModel,
    Project,
    PublishedSpan,
    Room,
    Site,
    Slab,
    Storey,
    degF,
    ft,
    inch,
    pt,
)

SEAT_IN = -13.4375
DECK_DEPTH_IN = 14.1875  # 10" form + 4 3/16" cap
DECK_TOP_IN = 0.75  # = the subfloor top
SPAN_FT = 18.0
SPLIT_Y_FT = 12.0
LENGTH_FT = 30.0
DECK = "SL-DECK"
WOOD = "FS-WOOD"
ROOM = "RM-B"
#: How ``checks/structural/slab_span._model_member`` spells the DECK_EPS section.
MEMBER = '10" BuildDeck EPS deck form under a 4 3/16" cast cap'

_GWB = (Layer(name="gwb-ceil", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),)
_MIX = ConcreteSpec(fc_psi=4000.0, bar_coating="black")


def _rect(x0, y0, x1, y1):
    return (pt(ft(x0), ft(y0)), pt(ft(x1), ft(y0)), pt(ft(x1), ft(y1)), pt(ft(x0), ft(y1)))


def published_row(**update) -> PublishedSpan:
    row = PublishedSpan(
        source="BuildDeck Design, Engineering and Installation Manual (BuildBlock, 2022)",
        table="10\" deck, 4\" cap, 2-#5 beam bars, 20'-0\" span, 62 psf live load",
        member=MEMBER, span=ft(20), load_psf=62.0,
        condition="f'c 4,000 psi, fy 60 ksi, deflection < L/480")
    return row.model_copy(update=update)


def deck(**update) -> Slab:
    slab = Slab(
        uid="SLDECK0001", tag=DECK, kind="pour", outline=_rect(0, SPLIT_Y_FT, SPAN_FT, LENGTH_FT),
        thickness=inch(DECK_DEPTH_IN), assembly="DECK_EPS", top_elevation=inch(DECK_TOP_IN),
        ceiling_below=_GWB, published_span=published_row())
    return slab.model_copy(update=update)


def mixed_deck_plan(*, slab: Slab | None = None, wall_tops_in: dict[str, float] | None = None
                    ) -> PlanModel:
    """``slab`` replaces the deck; ``wall_tops_in`` re-tops named pours (inches)."""
    library = Library(
        materials=(
            Material(tag="concrete", name="Concrete", r_per_inch=0.08, perm_rating=3.2),
            Material(tag="eps-deck-form", name="BuildDeck EPS deck form", r_per_inch=4.0),
            Material(tag="gwb", name="Gypsum", r_per_inch=0.9),
            Material(tag="plywood", name="Plywood", r_per_inch=1.25),
        ),
        assemblies=(
            Assembly(tag="CONC12", layers=(
                Layer(name="concrete", material_ref="concrete", thickness=inch(12),
                      function=LayerFunction.STRUCTURE),)),
            Assembly(tag="DECK_EPS", layers=(
                Layer(name="concrete-cap", material_ref="concrete", thickness=inch(4.1875),
                      function=LayerFunction.STRUCTURE, concrete=_MIX),
                Layer(name="eps-form", material_ref="eps-deck-form", thickness=inch(10),
                      function=LayerFunction.INSULATION))),
        ))
    project = Project(
        name="MixedDeck", project_uuid=uuid.UUID("00000000-0000-4000-8000-0000000000e1"),
        site=Site(lat=44.9, lon=-93.2, elevation=ft(830), design_temp_heating=degF(-15),
                  design_temp_cooling=degF(90)), building=Building(name="MixedDeck"))
    base_in = SEAT_IN - 96.0
    basement = Storey(uid="STBASE00e1", tag="basement", elevation=inch(base_in),
                      default_ceiling_height=ft(8))
    main = Storey(uid="STMAIN00e1", tag="main", elevation=ft(0), default_ceiling_height=ft(9))
    corners = ((0, 0), (SPAN_FT, 0), (SPAN_FT, LENGTH_FT), (0, LENGTH_FT))
    nodes = tuple(Node(uid=f"NB{i:08d}", tag=f"N-B{i}", position=pt(ft(x), ft(y)))
                  for i, (x, y) in enumerate(corners, 1))
    tops = wall_tops_in or {}
    walls = tuple(
        FoundationWall(uid=f"FWB{i:07d}", tag=tag, start_node=f"N-B{a}", end_node=f"N-B{b}",
                       assembly="CONC12", top_elevation=inch(tops.get(tag, SEAT_IN)),
                       bottom_elevation=inch(base_in))
        for i, (tag, a, b) in enumerate((("W-S", 1, 2), ("W-E", 2, 3), ("W-N", 3, 4),
                                         ("W-W", 4, 1)), 1))
    room = Room(uid="RMB00000e1", tag=ROOM, seed=pt(ft(9), ft(15)),
                occupancy=Occupancy.LIVING, conditioned=True)
    wood = FloorSystem(
        uid="FSWOOD00e1", tag=WOOD, outline=_rect(0, 0, SPAN_FT, SPLIT_Y_FT),
        joists=JoistSpec(member="11.875 TJI 230", spacing=inch(16), direction="x",
                         bearing_refs=("W-W", "W-E")),
        subfloor=DeckLayer(material_ref="plywood", thickness=inch(0.75)),
        ceiling_below=_GWB)
    plan = PlanModel(project=project, library=library, storeys=(basement, main))
    return (plan.with_elements("basement", (*nodes, *walls, room))
            .with_elements("main", (wood, slab if slab is not None else deck())))


def drain(uid: str, tag: str, path, elevations_in) -> PipeRun:
    """A 2" PVC drain on the basement storey; ``path`` in feet, elevations storey-relative.
    The deck's cap spans 106..110 3/16" and its foam 96..106" over the basement floor."""
    return PipeRun(uid=uid, tag=tag, system=PipeSystem.DRAIN,
                   path=tuple(pt(ft(x), ft(y)) for x, y in path), diameter=inch(2),
                   material="pvc", elevations=tuple(inch(z) for z in elevations_in))


def resolved_with(basement=(), main=()):
    """The default plan plus extra basement/main elements, resolved."""
    from typehaus.resolve import resolve

    plan = mixed_deck_plan()
    plan = (plan.with_elements("basement", (*plan.elements["basement"], *basement))
            .with_elements("main", (*plan.elements["main"], *main)))
    model, _findings = resolve(plan)
    return model


@lru_cache(maxsize=1)
def mixed_deck_model():
    """The resolved default plan. Shared — read it, never mutate it."""
    from typehaus.resolve import resolve

    model, _findings = resolve(mixed_deck_plan())
    return model
