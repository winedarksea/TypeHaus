"""R302.11 chase fireblocks: holes derived from the runs, graded by ``code.fireblock_chase``."""

from __future__ import annotations

import math

import pytest

from typehaus.findings import Result
from typehaus.quantities import ft, inch

_IN = 0.0254
# The stacked chase, 12" x 16", at the same plan spot on both decks.
_CHASE = ((ft(2), ft(4)), (ft(3), ft(4)), (ft(3), ft(5, 4)), (ft(2), ft(5, 4)))


def _plan(*, fireblock=True, wool=False, sealant="firestop-sealant", stacked=True):
    import uuid

    from typehaus.model import (
        Assembly,
        Building,
        DeckLayer,
        FloorOpening,
        FloorOpeningPurpose,
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

    stud = Assembly(tag="EXT", layers=(
        Layer(name="stud", material_ref="wood", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6")),))
    project = Project(
        name="Chase", project_uuid=uuid.UUID("00000000-0000-4000-8000-0000000000c1"),
        site=Site(lat=44.9, lon=-93.2, elevation=ft(830), design_temp_heating=degF(-15),
                  design_temp_cooling=degF(90)), building=Building(name="Chase"))
    storeys = tuple(Storey(uid=f"ST{tag.upper():0<8}"[:10], tag=tag, elevation=ft(9 * i),
                           default_ceiling_height=ft(9))
                    for i, tag in enumerate(("main", "second", "third")))
    layers = (Layer(name="sheet", material_ref="plywood", thickness=inch(0.75),
                    function=LayerFunction.SHEATHING),)
    if wool:
        layers += (Layer(name="wool", material_ref="wool", thickness=inch(3.5),
                         function=LayerFunction.INSULATION),)
    plan = PlanModel(project=project, library=Library(
        materials=(Material(tag="wood", name="Wood", r_per_inch=1.25),
                   Material(tag="plywood", name="Plywood", r_per_inch=1.25),
                   Material(tag="wool", name="Mineral wool", r_per_inch=4.2),
                   Material(tag="firestop-sealant", name="Firestop sealant")),
        assemblies=(stud,)), storeys=storeys)

    def walls(storey: str) -> tuple:
        out = []
        for i, x in enumerate((0, 12)):
            s, n = f"N-{storey}-{i}S", f"N-{storey}-{i}N"
            out += [Node(uid=f"N{storey[:2]}{i:06d}S", tag=s, position=pt(ft(x), ft(0)),
                         open_end=True),
                    Node(uid=f"N{storey[:2]}{i:06d}N", tag=n, position=pt(ft(x), ft(12)),
                         open_end=True),
                    Wall(uid=f"W{storey[:2]}{i:07d}", tag=f"W-{storey}-{x}", start_node=s,
                         end_node=n, assembly="EXT", top=ft(9))]
        return tuple(out)

    def deck(storey: str, below: str, chase: bool) -> tuple:
        k = storey[:2].upper()
        opening = FloorOpening(
            uid=f"FO{k}000001", tag=f"FO-{k}-CHASE", purpose=FloorOpeningPurpose.CHASE,
            outline=tuple(pt(x, y) for x, y in _CHASE),
            fireblock=layers if fireblock else (),
            fireblock_sealant=sealant if fireblock else None)
        system = FloorSystem(
            uid=f"FS{k}000001", tag=f"FS-{k}", openings=(opening.tag,) if chase else (),
            subfloor=DeckLayer(material_ref="plywood", thickness=inch(0.75)),
            joists=JoistSpec(member="2x10", spacing=inch(16), direction="x",
                             bearing_refs=(f"W-{below}-0", f"W-{below}-12")))
        return (opening, system) if chase else (system,)

    plan = plan.with_elements("main", walls("main"))
    plan = plan.with_elements("second", (*walls("second"), *deck("second", "main", True)))
    return plan.with_elements("third", deck("third", "second", stacked))


def _riser(model, tag: str, x_in: float, y_in: float, diameter_in: float = 3.0) -> None:
    from typehaus.resolve.model import ResolvedPipeRun

    xy = (x_in * _IN, y_in * _IN)
    model.pipe_runs.append(ResolvedPipeRun(
        uid=tag, tag=tag, storey="main", system="vent", path=[xy, xy],
        diameter_m=diameter_in * _IN, z_start_m=0.0, z_end_m=ft(25).meters,
        length_m=ft(25).meters, z_m=(0.0, ft(25).meters)))


def _model(risers=((30.0, 56.0),), **fields):
    """Resolve, add the risers, and re-derive the fireblocks against them."""
    from typehaus.resolve import resolve
    from typehaus.resolve.opening_fireblock import resolve_fireblocks

    model, findings = resolve(_plan(**fields))
    assert not [f for f in findings if f.severity.value == "error"], findings
    for i, (x, y) in enumerate(risers):
        _riser(model, f"PR-{i}", x, y)
    model.solids[:] = [s for s in model.solids if s.category != "fireblock"]
    model.fireblocks.clear()
    resolve_fireblocks(model)
    return model


def _findings(model):
    from typehaus.checks.code.mn_residential.fireblocking import fireblock_chase
    from typehaus.checks.run import build_context_from_model

    return fireblock_chase(build_context_from_model(model, []))


def _solids(model):
    return [s for s in model.solids if s.category == "fireblock"]


def test_one_void_per_layer_per_riser_and_it_follows_the_riser():
    model = _model(wool=True)
    solids = _solids(model)
    assert len(solids) == 4  # two decks x (sheet + wool)
    assert all(len(s.voids) == 1 for s in solids)
    sheet = next(s for s in solids if s.tag == "FO-SE-CHASE-fireblock-sheet")
    cx = sum(p[0] for p in sheet.voids[0]) / len(sheet.voids[0]) / _IN
    assert cx == pytest.approx(30.0, abs=0.05)
    # Reroute the riser: no plan edit, and the hole moves with it.
    moved = _solids(_model(risers=((33.0, 52.0),)))
    void = next(s for s in moved if s.tag == "FO-SE-CHASE-fireblock-sheet").voids[0]
    assert sum(p[0] for p in void) / len(void) / _IN == pytest.approx(33.0, abs=0.05)
    # The sheet sits flush with the subfloor top.
    deck = next(f for f in model.floors if f.tag == "FS-SE")
    assert sheet.z1_m == pytest.approx(deck.deck_z1_m)


def test_check_fails_without_a_fireblock_and_passes_with_one():
    fails = _findings(_model(fireblock=False))
    assert {f.result for f in fails} == {Result.FAIL}
    assert len(fails) == 2 and "fireblock=(Layer(" in fails[0].message
    passes = _findings(_model())
    assert {f.result for f in passes} == {Result.PASS}
    assert "PR-0" in passes[0].message


def test_no_stack_is_not_applicable_and_a_lone_chase_is_not_graded():
    findings = _findings(_model(stacked=False, fireblock=False))
    assert [f.result for f in findings] == [Result.NOT_APPLICABLE]


def test_a_missing_sealant_fails_when_runs_pass_through():
    findings = _findings(_model(sealant=None))
    assert all(f.result is Result.FAIL and "fireblock_sealant" in f.message for f in findings)


def test_risers_closer_than_the_min_web_need_mineral_wool():
    # Two 3" DWV risers (3.5" OD, 4" cut) 4.5" apart: a 1/2" web between the holes.
    close = ((30.0, 53.0), (30.0, 57.5))
    sliver = _findings(_model(risers=close))
    assert all(f.result is Result.FAIL and "mineral-wool" in f.message for f in sliver)
    assert {f.result for f in _findings(_model(risers=close, wool=True))} == {Result.PASS}


def test_takeoff_sheet_area_is_net_of_holes_and_sealant_is_the_perimeters():
    from typehaus.takeoff.fireblocking import fireblock_sealant_takeoff
    from typehaus.takeoff.sheet_goods import sheet_goods_takeoff

    model = _model()
    block = model.fireblocks[0]
    gross = (12 * 16) * _IN ** 2
    area = block.layers[0][2]
    assert area < gross
    hole = gross - area
    # The riser's real OD plus the annulus, all round.
    radius = math.sqrt(hole / math.pi)
    assert block.penetrations[0][1] == pytest.approx(2 * math.pi * radius, rel=0.01)
    row = next(r for r in sheet_goods_takeoff(model) if r["scope"] == "fireblock")
    assert row["net_area_sqft"] == pytest.approx(2 * area * 10.7639, abs=0.1)
    (sealant,) = fireblock_sealant_takeoff(model)
    total = sum(p for b in model.fireblocks for _, p in b.penetrations)
    assert sealant["count"] == 2
    assert sealant["length_ft"] == pytest.approx(total / 0.3048, abs=0.05)


@pytest.mark.slow
def test_catlin_nw_chase_is_fireblocked_at_all_three_decks(catlin_ctx):
    tags = {"FO-M-ERV-OA", "FO-S-ERV-CHASE", "FO-A-ERV-CHASE"}
    sheets = {s.tag for s in catlin_ctx.model.solids if s.category == "fireblock"
              and s.tag.endswith("-fireblock-sheet")}
    assert sheets == {f"{t}-fireblock-sheet" for t in tags}
    findings = _findings(catlin_ctx.model)
    assert {f.result for f in findings} == {Result.PASS}
    assert {f.message.split()[0] for f in findings} == tags
