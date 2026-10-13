"""Small three-bearing decks for opening framing and connection tests."""

from typehaus.quantities import ft, inch


def _deck_plan(*, east_edge=None, opening_bearing=(), member="11.875 I-joist", lining=False,
               support_spans=()):
    import uuid

    from typehaus.model import (
        Assembly,
        Building,
        FloorOpening,
        FloorSystem,
        FramingSpec,
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
    )
    from typehaus.quantities import degF, pt

    east_edge = east_edge or ft(20)
    stud = Assembly(tag="EXT", layers=(
        Layer(name="stud", material_ref="wood", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6")),))
    project = Project(
        name="Deck", project_uuid=uuid.UUID("00000000-0000-4000-8000-0000000000b1"),
        site=Site(lat=44.9, lon=-93.2, elevation=ft(830), design_temp_heating=degF(-15),
                  design_temp_cooling=degF(90)), building=Building(name="Deck"))
    main = Storey(uid="STMAIN0001", tag="main", elevation=ft(0), default_ceiling_height=ft(9))
    second = Storey(uid="STSEC00001", tag="second", elevation=ft(9),
                    default_ceiling_height=ft(9))
    nodes, walls = [], []
    for index, x in enumerate((0, 12, 24)):
        south, north = f"N-{index}S", f"N-{index}N"
        nodes += [Node(uid=f"N{index:08d}S", tag=south, position=pt(ft(x), ft(0)), open_end=True),
                  Node(uid=f"N{index:08d}N", tag=north, position=pt(ft(x), ft(12)), open_end=True)]
        walls.append(Wall(uid=f"W{index:09d}", tag=f"W-{x}", start_node=south,
                          end_node=north, assembly="EXT", top=ft(9)))
    for index, (start_in, end_in) in enumerate(support_spans):
        south, north = f"N-SUPPORT{index}S", f"N-SUPPORT{index}N"
        nodes += [Node(uid=f"NS{index:07d}S", tag=south,
                       position=pt(inch(165.25), inch(start_in)), open_end=True),
                  Node(uid=f"NS{index:07d}N", tag=north,
                       position=pt(inch(165.25), inch(end_in)), open_end=True)]
        walls.append(Wall(uid=f"WS{index:08d}", tag=f"W-SUPPORT{index}", start_node=south,
                          end_node=north, assembly="EXT", top=ft(9)))
    opening_bearing = (*opening_bearing, *(f"W-SUPPORT{i}" for i in range(len(support_spans))))
    plan = PlanModel(project=project, library=Library(
        materials=(Material(tag="wood", name="Wood", r_per_inch=1.25),
                   Material(tag="gwb", name="Gypsum", r_per_inch=0.9)),
        assemblies=(stud,)), storeys=(main, second))
    deck = (
        FloorOpening(uid="FO00000001", tag="FO-1", bearing_refs=opening_bearing, outline=(
            pt(ft(14), ft(4)), pt(east_edge, ft(4)), pt(east_edge, ft(7, 4)),
            pt(ft(14), ft(7, 4))), lining=(
                Layer(name="gwb-well", material_ref="gwb", thickness=inch(0.625),
                      function=LayerFunction.FINISH),) if lining else ()),
        FloorSystem(uid="FS00000001", tag="FS-1", openings=("FO-1",), joists=JoistSpec(
            member=member, spacing=inch(16), direction="x",
            bearing_refs=("W-0", "W-12", "W-24"))),
    )
    return plan.with_elements("main", (*nodes, *walls)).with_elements("second", deck)


def _deck(**fields):
    from typehaus.resolve import resolve

    model, findings = resolve(_deck_plan(**fields))
    assert not [f for f in findings if f.severity.value == "error"], findings
    return model, {member.child_key: member for member in model.floors[0].members}

