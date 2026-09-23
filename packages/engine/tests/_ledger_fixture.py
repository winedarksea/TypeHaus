"""A 17'-6" court: two cast walls, a treated 2x12 ledger on each inner face, joists hung
between them. Shared by ``test_deck_ledger.py``."""

from __future__ import annotations

from typehaus.model import (
    Assembly,
    Beam,
    Building,
    Connector,
    ConnectorKind,
    DeckLayer,
    FloorSystem,
    FoundationWall,
    JoistSpec,
    Layer,
    LayerFunction,
    Library,
    Material,
    Node,
    PlanModel,
    Project,
    Site,
    Storey,
    Wall,
    degF,
    ft,
    inch,
    pt,
)

WALL_IN = 12.0
X_W, X_E = 0.0, 18.5          # wall axes; inner faces at 0'-6" and 18'-0"
LENGTH_FT = 10.0
LEDGER = "2x12:kdat"
LEDGER_W_IN = 1.5
DECK_TOP_FT = 0.0

_CONCRETE = Material(tag="concrete", name="Concrete", r_per_inch=0.08, perm_rating=3.2)
_KDAT = Material(tag="kdat", name="KDAT SYP", r_per_inch=1.25, perm_rating=2.9,
                 preservative_treated=True)
_SPF = Material(tag="spf", name="SPF", r_per_inch=1.25, perm_rating=2.9)
_WALL = Assembly(tag="CONC12", layers=(
    Layer(name="concrete", material_ref="concrete", thickness=inch(WALL_IN),
          function=LayerFunction.STRUCTURE),))
_BEAM_KDAT = Assembly(tag="BEAM_KDAT", layers=(
    Layer(name="kdat", material_ref="kdat", thickness=inch(1.5),
          function=LayerFunction.STRUCTURE),))
_WOOD = Assembly(tag="WOOD12", layers=(
    Layer(name="band", material_ref="spf", thickness=inch(WALL_IN),
          function=LayerFunction.STRUCTURE),))
_BEAM_SPF = Assembly(tag="BEAM_SPF", layers=(
    Layer(name="spf", material_ref="spf", thickness=inch(1.5),
          function=LayerFunction.STRUCTURE),))


def ledger_x_ft(side: str, gap_in: float = 0.0) -> float:
    half = WALL_IN / 2.0 + gap_in + LEDGER_W_IN / 2.0
    return X_W + half / 12.0 if side == "W" else X_E - half / 12.0


def anchors(tag: str, x_ft: float, spacing_in: float, wall: str,
            uid_prefix: str, size: str) -> tuple[Connector, ...]:
    count = int(LENGTH_FT * 12.0 // spacing_in)
    return tuple(
        Connector(uid=f"{uid_prefix}{i:04d}", tag=f"CN-{tag}-{i}",
                  kind=ConnectorKind.ANCHOR_BOLT, size=size,
                  position=pt(ft(x_ft), inch(6 + i * spacing_in)),
                  elevation=ft(DECK_TOP_FT) - inch(5.625), connects=(tag, wall))
        for i in range(count))


def plan(*, gap_in: float = 0.0, assembly: str = "BEAM_KDAT", spacing_in: float | None = 16.0,
         ledger_on_w: str = "W-W", wood: bool = False,
         fastener: str = "1/2 adhesive anchor", ledger: str = LEDGER) -> PlanModel:
    library = Library(materials=(_CONCRETE, _KDAT, _SPF),
                      assemblies=(_WALL, _WOOD, _BEAM_KDAT, _BEAM_SPF))
    project = Project(name="LDG", project_uuid="00000000-0000-4000-8000-0000000000d7",
                      site=Site(lat=44.9, lon=-93.2, elevation=ft(830), grade=ft(-8),
                                design_temp_heating=degF(-15), design_temp_cooling=degF(90)),
                      building=Building(name="LDG"))
    storey = Storey(uid="ST000000d7", tag="main", elevation=ft(DECK_TOP_FT),
                    default_ceiling_height=ft(9))
    xw, xe = ledger_x_ft("W", gap_in), ledger_x_ft("E", gap_in)
    nodes = (
        Node(uid="N000000d01", tag="N-WS", position=pt(ft(X_W), ft(0)), open_end=True),
        Node(uid="N000000d02", tag="N-WN", position=pt(ft(X_W), ft(LENGTH_FT)), open_end=True),
        Node(uid="N000000d03", tag="N-ES", position=pt(ft(X_E), ft(0)), open_end=True),
        Node(uid="N000000d04", tag="N-EN", position=pt(ft(X_E), ft(LENGTH_FT)), open_end=True),
        Node(uid="N000000d05", tag="N-LWS", position=pt(ft(xw), ft(0)), open_end=True),
        Node(uid="N000000d06", tag="N-LWN", position=pt(ft(xw), ft(LENGTH_FT)),
             open_end=True),
        Node(uid="N000000d07", tag="N-LES", position=pt(ft(xe), ft(0)), open_end=True),
        Node(uid="N000000d08", tag="N-LEN", position=pt(ft(xe), ft(LENGTH_FT)),
             open_end=True),
    )
    if wood:
        walls = (
            Wall(uid="F000000d01", tag="W-W", start_node="N-WS", end_node="N-WN",
                 assembly="WOOD12", top=ft(3.5)),
            Wall(uid="F000000d02", tag="W-E", start_node="N-ES", end_node="N-EN",
                 assembly="WOOD12", top=ft(3.5)),
        )
    else:
        walls = (
            FoundationWall(uid="F000000d01", tag="W-W", start_node="N-WS", end_node="N-WN",
                           assembly="CONC12", top_elevation=ft(3.5), bottom_elevation=ft(-8)),
            FoundationWall(uid="F000000d02", tag="W-E", start_node="N-ES", end_node="N-EN",
                           assembly="CONC12", top_elevation=ft(3.5), bottom_elevation=ft(-8)),
        )
    ledgers = (
        Beam(uid="B000000d01", tag="BM-LW", start_node="N-LWS", end_node="N-LWN",
             size=ledger, assembly=assembly, top_elevation=ft(DECK_TOP_FT),
             ledger_on=ledger_on_w),
        Beam(uid="B000000d02", tag="BM-LE", start_node="N-LES", end_node="N-LEN",
             size=ledger, assembly=assembly, top_elevation=ft(DECK_TOP_FT),
             ledger_on="W-E"),
    )
    deck = FloorSystem(
        uid="FS000000d7", tag="FS-D",
        joists=JoistSpec(member="2x12:kdat", spacing=inch(12), direction="x",
                         bearing_refs=("BM-LW", "BM-LE"), species="southern_pine"),
        outline=(pt(ft(xw), ft(0)), pt(ft(xe), ft(0)), pt(ft(xe), ft(LENGTH_FT)),
                 pt(ft(xw), ft(LENGTH_FT))),
        subfloor=DeckLayer(material_ref="spf", thickness=inch(1.0)),
        service="deck",
    )
    bolts = ()
    if spacing_in is not None:
        bolts = (*anchors("BM-LW", xw, spacing_in, "W-W", "A0000W", fastener),
                 *anchors("BM-LE", xe, spacing_in, "W-E", "A0000E", fastener))
    return plan_with(project, library, storey, (*nodes, *walls, *ledgers, deck, *bolts))


def plan_with(project, library, storey, elements) -> PlanModel:
    return PlanModel(project=project, library=library,
                     storeys=(storey,)).with_elements("main", elements)
