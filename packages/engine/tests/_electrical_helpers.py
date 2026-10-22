"""Small room fixture for electrical wall-spacing regressions."""

from typehaus.model import Library, PlanModel, Storey, pt


def room_plan(project, devices=()):
    """A 20'x14' LIVING room with four walls — the receptacle-spacing fixture."""
    from typehaus.model import (
        Assembly,
        FramingSpec,
        Layer,
        LayerFunction,
        Material,
        Node,
        Occupancy,
        Room,
        Wall,
        ft,
        inch,
    )

    lib = Library(
        materials=(Material(tag="spf", name="SPF", r_per_inch=1.25),
                   Material(tag="gwb", name="GWB", r_per_inch=0.9)),
        assemblies=(Assembly(tag="EXT", layers=(
            Layer(name="stud", material_ref="spf", thickness=inch(5.5),
                  function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6")),),
            default_lining=(Layer(name="gwb", material_ref="gwb", thickness=inch(0.625),
                                  function=LayerFunction.FINISH),)),),
    )
    storey = Storey(uid="ST00000001", tag="s1", elevation=ft(0), default_ceiling_height=ft(9))
    nodes = [Node(uid=f"N{i:09d}", tag=f"N-{i}", position=p) for i, p in enumerate(
        [pt(ft(0), ft(0)), pt(ft(20), ft(0)), pt(ft(20), ft(14)), pt(ft(0), ft(14))], 1)]
    walls = [Wall(uid=f"W{i:09d}", tag=f"W-{i}", start_node=f"N-{a}", end_node=f"N-{b}",
                  assembly="EXT", top=ft(9))
             for i, (a, b) in enumerate([(1, 2), (2, 3), (3, 4), (4, 1)], 1)]
    room = Room(uid="RM00000001", tag="RM-1", seed=pt(ft(10), ft(7)),
                occupancy=Occupancy.LIVING)
    return (PlanModel(project=project, library=lib, storeys=(storey,))
            .with_elements("s1", [*nodes, *walls, room, *devices]))


