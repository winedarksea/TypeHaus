"""Authored drainage elements, and the checks that hold their references to real things.

Drainage claims made only in prose are unenforced: two of the Catlin gutters sloped "to the
east downspout" while no such leader existed anywhere in the plan, and the pit outside the
garage was a deepened footing bedding whose excavation perimeter billed as drain tile that
is not there. This file covers the real elements and the two advisory checks that catch
that class of mistake.
"""

from __future__ import annotations


import pytest

from _helpers import check_context

from typehaus.checks.mep.drainage import discharge_consistency, downspout_ref
from typehaus.checks.registry import CheckContext
from typehaus.findings import Result
from typehaus.model.structure import Drywell, FrenchDrain
from typehaus.model.trim import Downspout, Gutter
from typehaus.quantities import ft, inch, pt
from typehaus.resolve import resolve

_M_TO_FT = 3.280839895



def _context(plan, model) -> CheckContext:
    return check_context(plan, model)


def _failures(findings) -> list:
    return [f for f in findings if f.result is Result.FAIL]


# --- the elements -------------------------------------------------------------------------

def test_every_authored_gutter_falls_to_a_leader_that_exists(catlin_plan, catlin_model):
    """The regression the whole phase is for. TR-RF-GUTTER-W/E, the garage eave gutter and
    TR-SG-GUTTER all named a downspout in prose; two of those leaders were never authored."""
    findings = downspout_ref(_context(catlin_plan, catlin_model))
    assert not _failures(findings), [f.message for f in _failures(findings)]

    leaders = {element.tag for storey in catlin_plan.storeys
               for element in catlin_plan.storey_elements(storey.tag)
               if isinstance(element, Downspout)}
    assert {"TR-RF-LEADER-W", "TR-RF-LEADER-E",
            "TR-G-LEADER-E", "TR-G-LEADER-W", "TR-SG-LEADER-SE"} <= leaders


def test_the_garage_leaders_take_their_water_from_the_resolved_troughs(catlin_model):
    """Each garage leader's elevation is pinned rather than derived, because the EaveGutter
    above it deliberately is not: the raised-heel truss lifts the deck plane during the
    envelope stage. This is the tie that catches a pin drifting off the channel it drains.

    ** TWO LEADERS SINCE 2026-09-07. ** The ridge turned north-south with the overhead door,
    so the eaves are EAST and WEST and both carry a trough. `EaveGutter.downspout_ref` names
    both; what binds a leader to its trough is `Downspout.gutter_ref`, which both carry — so
    this test walks the pair and matches each leader to the trough on ITS OWN side.
    """
    roof = next(r for r in catlin_model.roofs if r.tag == "RF-GARAGE")
    floors = [m for m in roof.members
              if m.category == "gutter" and m.child_key.endswith("-bottom")]
    assert len(floors) == 2, "one trough per eave, east and west"
    grade_m = catlin_model.plan.project.site.grade.meters
    for tag in ("TR-G-LEADER-E", "TR-G-LEADER-W"):
        leader = next(s for s in catlin_model.solids if s.tag == tag)
        # The OUTLET is what sits in the trough; the east drop goosenecks back to the wall.
        element = catlin_model.plan.by_tag(tag)
        leader_x = (element.outlet or element.position).xy_m[0]
        floor = min(floors, key=lambda m: abs(m.p0[0] - leader_x))
        assert abs(floor.p0[0] - leader_x) < 0.3, \
            f"{tag} must sit on its own eave's trough, not the one across the roof"
        assert floor.z0_m <= leader.z1_m <= floor.z1_m, \
            f"{tag}'s outlet must sit in the trough floor, not above or below it"
        assert grade_m < leader.z0_m < grade_m + 0.5, \
            "and stop just above grade, where the riser to its rain garden takes over — "\
            "measured from grade, which the garage stands on"


def _x0(solid) -> float:
    return min(point[0] for point in solid.outline)


def _x1(solid) -> float:
    return max(point[0] for point in solid.outline)


def test_the_balcony_leader_hangs_outside_the_east_retaining_wall(catlin_model):
    """The leader hangs outboard of the 6x6 pillar PT-SG-BF3 and the 12" band of W-SG-E1, so
    it discharges to the raised terrace (level with the retaining top) instead of nine feet
    down into the garden."""
    leader = next(s for s in catlin_model.solids if s.tag == "TR-SG-LEADER-SE")
    gutter_bands = [s for s in catlin_model.solids
                    if s.tag.startswith("TR-SG-GUTTER-") and s.category == "gutter"]
    assert gutter_bands
    assert leader.z1_m <= min(band.z1_m for band in gutter_bands)
    # The outlet still sits under the trough it drains. The run oversails the deck edge
    # precisely so it can, so this is the tie that catches the two drifting apart.
    assert _x1(leader) <= max(_x1(band) for band in gutter_bands)

    pillar = next(s for s in catlin_model.solids if s.tag == "PT-SG-BF3")
    assert _x0(leader) >= _x1(pillar), "the pipe is east of the column, not inside it"
    # The deck's east edge is flush with W-SG-E1's *outer* face by construction (the joists
    # cantilever 6" off the axis and the wall is 12" thick), so clearing the deck is the
    # same statement as clearing the wall the whole drop would otherwise pass through.
    deck = next(f for f in catlin_model.floors if f.tag == "FS-SG-DECK")
    assert _x0(leader) >= max(point[0] for point in deck.deck_outline)

    terrace_m = next(w for w in catlin_model.walls if w.tag == "W-SG-E2").z1_m
    assert terrace_m < leader.z0_m < terrace_m + 0.3, \
        "and it stops just above the terrace, whose surface is level with the retaining top"


def test_the_balcony_leader_runs_east_to_a_basin_in_the_yard(catlin_model):
    """TR-SG-LEADER-SE drops into TR-SG-RUNNEL on W-RG-EAST-BALCONY's top, whose spout lets
    go past W-RG-EAST into FURN-SG-SPLASH-BASIN — never onto the terrace (the court's
    soakaway) and clear of SL-SG-STAIRPAD (no icy walkway). Nothing in `haus check` grades a
    runnel or a basin, so this is the guard."""
    ft_m = 0.3048
    plan_leader = catlin_model.plan.by_tag("TR-SG-LEADER-SE")
    assert plan_leader.discharge_ref == "daylight"

    leader = next(s for s in catlin_model.solids if s.tag == "TR-SG-LEADER-SE")
    runnel = [s for s in catlin_model.solids
              if s.tag.startswith("TR-SG-RUNNEL-") and s.category == "gutter"]
    assert runnel
    ret = next(w for w in catlin_model.walls if w.tag == "W-RG-EAST-BALCONY")
    assert min(s.z0_m for s in runnel) == pytest.approx(ret.z1_m, abs=1e-6), \
        "the channel sits on the return's top course, in place of its cap"
    rim = max(s.z1_m for s in runnel)
    assert rim < leader.z0_m <= rim + 0.05, "the leader lets go just over the channel"

    spout = catlin_model.plan.by_tag("TR-SG-RUNNEL").path[-1].xy_m
    east = next(w for w in catlin_model.walls if w.tag == "W-RG-EAST")
    east_face = east.axis[0][0] + east.thickness_m / 2
    assert spout[0] > east_face, "the spout clears W-RG-EAST's yard face"

    basin = next(c for c in catlin_model.canvas_objects if c.tag == "FURN-SG-SPLASH-BASIN")
    xs = [p[0] for p in basin.footprint]
    ys = [p[1] for p in basin.footprint]
    assert min(xs) <= spout[0] <= max(xs) and min(ys) <= spout[1] <= max(ys), \
        "the spout lands in the basin"
    assert min(xs) > east_face, "the basin stands clear of the SRW face"
    pad = next(s for s in catlin_model.solids if s.tag == "SL-SG-STAIRPAD")
    assert min(p[1] for p in pad.outline) - max(ys) >= 2.0 * ft_m - 1e-6, \
        "the basin stays 2'-0\" off the stair pad"
    assert basin.z_m == pytest.approx(-40 * 0.0254, abs=1e-6), "set on the yard at -3'-4\""


def test_the_hydrant_pit_is_a_drywell_and_no_longer_bills_phantom_tile(catlin_model):
    """As a FootingBedding the pit's perimeter counted as perimeter drain tile — tile that
    is not there and that nobody installs around a soakaway."""
    well = next(s for s in catlin_model.solids if s.tag == "DRW-G-HYDRANT")
    assert well.category == "drywell"
    assert not [b for b in catlin_model.footing_beddings if "HYDRANT" in b.tag]
    assert not [s for s in catlin_model.solids
                if s.category == "drain_tile" and "HYDRANT" in s.tag]


def test_the_soakaway_is_a_course_below_the_drained_section(catlin_model):
    """The 42" under the court's footings is a *bearing* course that happens to drain; the
    soakaway is a 12" course of the same stone BELOW it, under W2/E2/S/ARCH only — it floods,
    and it is never frost section. There is no separate well any more (retired 2026-09-22).

    W1/E1 abut the house footings and stop on the drained plane, so the dig steps 12" at the
    grade-beam line and flood water stays ~10' off the basement."""
    assert catlin_model.plan.by_tag("DRW-SG-MAIN") is None
    beds = {b.tag: b for b in catlin_model.footing_beddings if b.tag.startswith("FB-SG-")}
    drained = {round(b.z0_m / 0.0254, 4) for b in beds.values()}
    assert drained == {-163.4375}, "every drained section bottoms on one plane"
    soak = {t for t, b in beds.items() if b.soakaway_z0_m is not None}
    assert soak == {"FB-SG-W2", "FB-SG-E2", "FB-SG-S", "FB-SG-ARCH"}
    for tag in soak:
        assert beds[tag].stone_z0_m / 0.0254 == pytest.approx(-175.4375)
        assert beds[tag].void_ratio == 0.40 and beds[tag].infiltration_in_per_hr == 0.06
    for tag in ("FB-SG-W1", "FB-SG-E1"):
        assert beds[tag].stone_z0_m == beds[tag].z0_m, "the house-side beds stay drained-only"
    # No court bed runs a pipe (2026-09-23): the stone lets go into the course, never to a
    # daylight it does not have. W1/E1, with no course, name the bed their stone abuts.
    assert not any(b.drain_tile for b in beds.values())
    assert {b.tag: b.discharge_ref for b in beds.values() if b.discharge_ref} == {
        "FB-SG-W1": "FB-SG-W2", "FB-SG-E1": "FB-SG-E2"}
    # The balcony leader is NOT an inlet: it hangs outside the east wall.
    arch = catlin_model.plan.by_tag("FB-SG-ARCH")
    assert "TR-SG-LEADER-SE" not in arch.inlet_refs
    assert set(arch.inlet_refs) == {"FD-SG-FIELD", "AD-SG-COURT"}
    assert catlin_model.plan.by_tag("FB-SG-W1").inlet_refs == ("SM-B-RADON",)


def test_the_garden_field_has_a_real_underdrain_and_not_a_prose_one(catlin_model):
    """`GARDEN_PUTTING_GREEN` said "draining to DRW-SG-MAIN" in a `source=` string for as
    long as it existed, and until 2026-09-05 NO element implemented it — the exact failure
    `checks/mep/drainage.py`'s docstring is written about. This test is what stops it
    reverting to prose."""
    plan_drain = catlin_model.plan.by_tag("FD-SG-FIELD")
    assert plan_drain is not None, "the field's underdrain is an element, not a sentence"
    assert plan_drain.discharge_ref == "FB-SG-ARCH"

    # It lies in the blanket the field is built on: the trench floor is 8" below the
    # profile's underside, which is `field_depth_in` below the court plane.
    field = next(s for s in catlin_model.solids if s.tag == "SL-SG-FIELD")
    invert_ft = plan_drain.invert._m / 0.3048
    assert invert_ft == pytest.approx(field.z0_m / 0.3048 - 8.0 / 12.0, abs=0.01), \
        "the trench is cut INTO the subgrade below the gravel, not floating in it"

    # And it is clear of the grade beam, which is the court's only real strut: the trench
    # runs down the field's centreline, not USGA's perimeter "smile".
    xs = {round(point.x._m, 6) for point in plan_drain.path}
    assert len(xs) == 1, "one straight lateral on the centreline"

    # ** `sock=False`, which in this house means the two FrenchDrains in the sand profile —
    # this field lateral and `FD-SG-OVERFLOW`. ** (This comment said "the only tile in this
    # house" until 2026-09-14; the overflow has always carried it too.) USGA: "any piping
    # encased in geotextile sleeves are not recommended"; a sock in a sand profile clogs
    # with fines and seals the line. Every bearing bed in clay keeps its sock.
    assert plan_drain.tile is not None and plan_drain.tile.sock is False
    sockless = {drain.tag for drain in catlin_model.plan.all_elements()
                if getattr(drain, "element_kind", None) == "FrenchDrain"
                and getattr(drain, "tile", None) is not None and drain.tile.sock is False}
    assert sockless == {"FD-SG-FIELD", "FD-SG-OVERFLOW"}, sockless
    beds = [b for b in catlin_model.footing_beddings if b.drain_tile_spec is not None]
    assert beds and all(b.drain_tile_spec.sock for b in beds)

    # The bed knows about it, so `drainage.discharge_consistency` grades both ends.
    assert "FD-SG-FIELD" in catlin_model.plan.by_tag("FB-SG-ARCH").inlet_refs


def test_the_house_perimeter_tile_falls_to_the_sump_it_can_actually_reach(catlin_model):
    """All 30 house beddings claimed `discharge="daylight"` with an invert 7'-6 1/2" BELOW
    site grade. It passed silently because "daylight" names nothing and the check
    short-circuits it. There is no daylight available to this tile anywhere on the lot."""
    house = [b for b in catlin_model.footing_beddings if b.host.startswith("FT-B-")]
    assert house
    assert {b.drain_tile_spec.discharge for b in house} == {"SM-B-RADON"}
    assert catlin_model.plan.by_tag("SM-B-RADON") is not None
    # The garden's own beds are NOT redirected: their soakaway course is below them and takes
    # their water with no pump in the path — and since 2026-09-23 no pipe either.
    garden = [b for b in catlin_model.footing_beddings if b.host.startswith("FT-SG-")]
    assert garden and not any(b.drain_tile for b in garden)


def test_the_radon_sump_carries_its_pump(catlin_plan):
    sump = catlin_plan.by_tag("SM-B-RADON")
    assert sump.pump is not None
    assert sump.pump.circuit_ref == "CKT-SUMP"
    # The pump lifts into the west leader's extension (2026-09-22) by a modelled line with a
    # check valve and an ice guard; "daylight" had no pipe behind it.
    assert sump.pump.discharge == "TR-RF-LEADER-W"
    assert sump.pump.discharge_line_ref == "PR-B-SUMP-DISCH"
    assert sump.pump.check_valve and sump.pump.freeze_relief
    line = catlin_plan.by_tag("PR-B-SUMP-DISCH")
    assert line.system.value == "sump_discharge"


# --- the resolver, on elements the Catlin house does not author yet ------------------------

def _minimal_plan_with(catlin_plan, element, storey: str = "basement"):
    """The Catlin plan with one extra element spliced onto a storey.

    Cheaper and more honest than a synthetic plan: FrenchDrain and Drywell resolve against
    site grade and the storey table, and a hand-built two-wall fixture would not have either.
    """
    return catlin_plan.with_elements(
        storey, (*catlin_plan.storey_elements(storey), element))


def test_a_french_drain_resolves_a_trench_and_the_tile_inside_it(catlin_plan):
    from typehaus.model.structure import DrainTile

    run = FrenchDrain(
        uid="TSTFD00001", tag="FD-TEST", path=(pt(ft(60), ft(10)), pt(ft(60), ft(40))),
        invert=ft(-4), trench_width=inch(18), trench_depth=inch(24),
        tile=DrainTile(diameter=inch(4), discharge="daylight"))
    model, findings = resolve(_minimal_plan_with(catlin_plan, run))
    assert not [f for f in findings if f.severity.value == "error"]

    # Scoped to FD-TEST: the Catlin plan carries two real FrenchDrains of its own since
    # 2026-09-05 (FD-SG-FIELD, FD-SG-OVERFLOW), and this test is about the resolver.
    trench = [s for s in model.solids
              if s.category == "french_drain" and s.tag.startswith("FD-TEST")]
    assert len(trench) == 1
    assert (trench[0].z1_m - trench[0].z0_m) == pytest.approx(inch(24).meters)
    # The pipe is not the trench: it is the product inside it, billed and drawn separately.
    tile = [s for s in model.solids if s.tag.startswith("FD-TEST-DT-")]
    assert tile and all(s.category == "drain_tile" for s in tile)
    assert min(s.z0_m for s in tile) > trench[0].z0_m, "the tile floats on bedding stone"


def test_an_open_french_drain_run_does_not_close_back_on_itself(catlin_plan):
    """A bedding's ring closes; an interceptor run ends where it discharges. Closing it
    would bill a phantom segment straight back across the yard."""
    from typehaus.model.structure import DrainTile

    run = FrenchDrain(
        uid="TSTFD00002", tag="FD-OPEN",
        path=(pt(ft(60), ft(10)), pt(ft(70), ft(10)), pt(ft(70), ft(30))),
        invert=ft(-4), trench_width=inch(18), trench_depth=inch(24),
        tile=DrainTile(diameter=inch(4)))
    model, _ = resolve(_minimal_plan_with(catlin_plan, run))
    assert len([s for s in model.solids if s.tag.startswith("FD-OPEN-DT-")]) == 2


def test_a_drywell_is_dug_from_grade_not_from_its_storey_datum(catlin_plan):
    """Authored on the basement storey, a soakaway outside the building would otherwise
    start at the basement floor and hang in the excavation."""
    well = Drywell(uid="TSTDW00001", tag="DRW-TEST", position=pt(ft(70), ft(70)),
                   diameter=ft(4), depth=ft(4))
    model, _ = resolve(_minimal_plan_with(catlin_plan, well))
    solid = next(s for s in model.solids if s.tag == "DRW-TEST")
    grade = model.plan.project.site.grade.meters
    assert solid.z1_m == pytest.approx(grade)
    assert (solid.z1_m - solid.z0_m) == pytest.approx(ft(4).meters)


# --- the checks ----------------------------------------------------------------------------

def test_a_gutter_that_names_a_missing_leader_fails_the_check(catlin_plan, catlin_model):
    gutter = Gutter(
        uid="TSTGT00001", tag="TR-TEST-GUTTER",
        path=(pt(ft(60), ft(10)), pt(ft(70), ft(10))), top_elevation=ft(9),
        depth=inch(5), thickness=inch(5), material="aluminum",
        downspout_ref="TR-NO-SUCH-LEADER")
    plan = _minimal_plan_with(catlin_plan, gutter, storey="main")
    model, _ = resolve(plan)
    failures = _failures(downspout_ref(_context(plan, model)))
    assert [f for f in failures if "TR-TEST-GUTTER" in f.element_tags]


def test_a_slope_note_naming_a_downspout_with_no_ref_fails(catlin_plan):
    """The exact shape of the original bug: the claim lived in prose only."""
    gutter = Gutter(
        uid="TSTGT00002", tag="TR-PROSE-GUTTER",
        path=(pt(ft(60), ft(10)), pt(ft(70), ft(10))), top_elevation=ft(9),
        depth=inch(5), thickness=inch(5), material="aluminum",
        slope="1/16 in/ft to the east downspout")
    plan = _minimal_plan_with(catlin_plan, gutter, storey="main")
    model, _ = resolve(plan)
    failures = _failures(downspout_ref(_context(plan, model)))
    assert [f for f in failures if "TR-PROSE-GUTTER" in f.element_tags]


def test_catlin_discharges_all_resolve(catlin_plan, catlin_model):
    findings = discharge_consistency(_context(catlin_plan, catlin_model))
    assert not _failures(findings), [f.message for f in _failures(findings)]


def test_a_pump_on_a_circuit_the_panel_does_not_carry_fails(catlin_plan):
    from typehaus.model.mep import SumpPump

    sump = catlin_plan.by_tag("SM-B-RADON")
    patched = sump.model_copy(update={
        "pump": SumpPump(discharge="daylight", circuit_ref="CKT-NOT-A-CIRCUIT")})
    plan = catlin_plan.with_elements(
        "basement", (patched if e is sump else e
                     for e in catlin_plan.storey_elements("basement")))
    model, _ = resolve(plan)
    failures = _failures(discharge_consistency(_context(plan, model)))
    assert [f for f in failures if "CKT-NOT-A-CIRCUIT" in f.message]


def test_a_soakaway_is_stone_not_concrete(catlin_model):
    """``solid_material_ref``'s last-resort default is "concrete", which is right for a
    footing and wrong for a hole full of washed rock. A drywell that named no material at
    all hatched 4.35 cy of #57 stone as a pour in every section it was cut in, and told the
    estimate's material guard that the soakaway was ready-mix."""
    from typehaus.resolve.assembly_material import solid_material_ref

    wells = [s for s in catlin_model.solids if s.category == "drywell"]
    assert wells, "the house has soakaways to get wrong"
    for well in wells:
        assert solid_material_ref(catlin_model.plan, well) == "aggregate"


def test_the_radon_sump_is_a_basin_not_a_second_pour(catlin_model):
    """The pit interrupts the slab; it is not made of it."""
    from typehaus.resolve.assembly_material import solid_material_ref

    sumps = [s for s in catlin_model.solids if s.category == "sump"]
    assert sumps
    for sump in sumps:
        assert solid_material_ref(catlin_model.plan, sump) == "polyethylene"


def test_a_thermal_break_is_foam_not_the_concrete_it_breaks(catlin_model):
    """The one block whose whole job is to *not* be the pour on either side of it."""
    from typehaus.resolve.assembly_material import solid_material_ref

    blocks = [s for s in catlin_model.solids if s.category == "thermal_break"]
    assert blocks
    for block in blocks:
        assert solid_material_ref(catlin_model.plan, block) == "xps"


# --- the drainage NETWORK (2026-09-14) ----------------------------------------------------
#
# Everything above this line tests elements. These test the GRAPH between them, which did not
# exist until the outside review of the sunken garden asked where the water actually goes.


def _network(catlin_model):
    from typehaus.resolve.drainage_network import build_network

    return build_network(catlin_model.plan)


def test_every_drainage_source_reaches_something_that_disposes_of_water(catlin_model):
    """The walk, end to end, on the real house.

    Disposal is daylight, a soakaway (the soil takes it) or a pit with a pump. Before this
    existed a discharge was a string beside a string: ``FD-SG-FIELD`` named ``DRW-SG-MAIN``,
    the name resolved perfectly, and the trench ended 28 inches above the stone.
    """
    from typehaus.resolve.drainage_network import EdgeKind

    network = _network(catlin_model)
    assert network.unresolved == [], network.unresolved
    sources = set(network.sources())
    house_rings = {b.tag for b in catlin_model.footing_beddings if b.tag.startswith("FB-B-")}
    assert len(house_rings) == 19 and house_rings <= sources
    assert {"FD-SG-FIELD", "FD-SG-OVERFLOW", "AD-SG-COURT", "FB-SG-W1", "FB-SG-E1",
            "TR-RF-LEADER-W", "TR-G-LEADER-W"} <= sources
    # A soakaway bed DISPOSES; it is not a source.
    assert not {"FB-SG-W2", "FB-SG-E2", "FB-SG-S", "FB-SG-ARCH"} & sources
    for source in sorted(sources):
        reached, path, problem = network.reaches_disposal(
            source, first_hop=EdgeKind.PRIMARY)
        assert reached, f"{source}: {problem} (followed {path})"


def test_the_bridge_runs_both_ways_through_the_house_tile(catlin_model):
    """**Owner decision 6, as a graph rather than as a paragraph.**

    The sump and the court's soakaway each fall back to the other: deliberately a CYCLE, no
    valves, no high-water device, and the walk has to tolerate it rather than call it a fault.

    Since 2026-09-23 the court's end is FB-SG-W1, where FD-SG-OVERFLOW starts on the west
    heel. It is NOT one invert: the court spills at the field profile's underside, and the pit
    reaches the court only back through the house tile, so it relieves at its own inlet.
    Gravity still runs sump -> court free: W1's drained floor is below the pit's.
    """
    from typehaus.resolve.drainage_network import EdgeKind

    network = _network(catlin_model)
    reached, path, problem = network.reaches_disposal(
        "SM-B-RADON", first_hop=EdgeKind.OVERFLOW, not_being="SM-B-RADON")
    assert reached, problem
    assert path[:2] == ["SM-B-RADON", "FB-SG-W1"], path

    reached, path, problem = network.reaches_disposal(
        "FB-SG-W1", first_hop=EdgeKind.OVERFLOW, not_being="FB-SG-W1")
    assert reached, problem
    assert path == ["FB-SG-W1", "FD-SG-OVERFLOW", "SM-B-RADON"], path

    plan = catlin_model.plan
    for invert in (plan.by_tag("FB-SG-W1").overflow_invert,
                   plan.by_tag("FD-SG-OVERFLOW").invert):
        assert invert.inches == pytest.approx(-127.4375)
    sump = plan.by_tag("SM-B-RADON")
    assert sump.overflow_invert.inches == pytest.approx(sump.inlet_invert.inches)
    assert plan.by_tag("FB-SG-ARCH").overflow_ref is None
    # Downhill without a pump: the court's drained floor is below the pit's floor.
    pit_floor = next(s.z0_m for s in catlin_model.solids if s.tag == "SM-B-RADON")
    w1 = next(b for b in catlin_model.footing_beddings if b.tag == "FB-SG-W1")
    assert w1.z0_m < pit_floor


def test_the_overflow_runs_on_the_west_heel(catlin_model):
    """A short level leg from inside FB-SG-W1's stone to FB-B-S1's bedding: no trench down
    the court, and nothing crosses the grade beam (its sleeve and pipe are retired)."""
    run = catlin_model.plan.by_tag("FD-SG-OVERFLOW")
    xs = {round(p.x.inches, 3) for p in run.path}
    assert xs == {84.0}, "2 ft west of W-SG-W1's axis, on the footing's heel"
    assert run.end_invert is None, "level: it carries water both ways"
    w1 = next(b for b in catlin_model.footing_beddings if b.tag == "FB-SG-W1")
    s1 = next(b for b in catlin_model.footing_beddings if b.tag == "FB-B-S1")
    from shapely.geometry import Point, Polygon
    start, end = run.path[0].xy_m, run.path[-1].xy_m
    assert Polygon(w1.outline).contains(Point(start))
    assert Polygon(s1.outline).distance(Point(end)) < 1e-6
    for retired in ("SP-SG-ARCH-OVERFLOW", "PR-SG-ARCH-OVERFLOW"):
        assert catlin_model.plan.by_tag(retired) is None


def test_the_field_lateral_falls_into_the_stone_it_feeds(catlin_model):
    """**D1.** It once discharged 28" above the stone. It now falls 1" over 10' and ends on
    FB-SG-ARCH's south face with its invert inside that bed's stone band — and resolves as
    two bands, not the 28-step staircase its dive to the old well needed."""
    run = catlin_model.plan.by_tag("FD-SG-FIELD")
    arch = next(b for b in catlin_model.footing_beddings if b.tag == "FB-SG-ARCH")
    assert run.end_invert is not None and run.end_invert.meters < run.invert.meters
    assert arch.stone_z0_m < run.end_invert.meters < arch.z1_m, "it arrives in the stone"
    assert run.path[-1].y.meters == pytest.approx(min(p[1] for p in arch.outline))
    bands = [s for s in catlin_model.solids
             if s.tag.startswith("FD-SG-FIELD-") and s.category == "french_drain"]
    assert 1 <= len(bands) <= 2, len(bands)


def test_every_bedding_that_names_a_receiver_has_a_way_to_reach_it(catlin_model):
    """**D2, and the half of it that turned out to be false.**

    The review read the nineteen house perimeter rings as "19 independent loops with no
    lead". The RINGS are independent — ``resolve/drain_tile.py`` derives a closed loop per
    bedding and never a lead — but the STONE is not: all nineteen beds are one connected
    body, and that body abuts the radon pit. So the connection is real, and it is real in
    the same way the court's own authoring argues ``FB-SG-ARCH`` feeds the well through its
    side. What was genuinely orphaned was ``FB-SG-COL``, alone in a body of one, 8'-10" from
    the well with nothing between — which is why ``FD-SG-COL-LEAD`` existed.

    Both retired on 2026-09-22 with the court's centre support line (17'-0" court), so there
    is no orphan left: every bed in the house is in one of exactly two bodies.
    """
    from typehaus.resolve.drainage_network import stone_bodies

    bodies = stone_bodies(catlin_model)
    house = bodies["FB-B-W1"]
    assert len(house) == 19, sorted(house)
    court = bodies["FB-SG-W1"]
    assert court == {"FB-SG-ARCH", "FB-SG-E1", "FB-SG-E2", "FB-SG-S", "FB-SG-W1", "FB-SG-W2"}
    assert set(bodies) == set(house) | set(court), "a bed in a body of its own is orphaned"
    assert catlin_model.plan.by_tag("FB-SG-COL") is None
    assert catlin_model.plan.by_tag("FD-SG-COL-LEAD") is None


def test_the_sump_names_what_feeds_it(catlin_model):
    """A receiver that cannot say what feeds it can be claimed by anything.

    ``Drywell.inlet_refs`` has always carried this; ``Sump`` did not, so twenty runs named
    the pit and nothing named them back.
    """
    sump = catlin_model.plan.by_tag("SM-B-RADON")
    assert len(sump.inlet_refs) == 20, sump.inlet_refs
    assert "FD-SG-OVERFLOW" in sump.inlet_refs and "FD-B-SUMP-LEAD" not in sump.inlet_refs
    assert sum(1 for tag in sump.inlet_refs if tag.startswith("FB-B-")) == 19
    for tag in sump.inlet_refs:
        assert catlin_model.plan.by_tag(tag) is not None, tag
    assert sump.inlet_invert is not None, "a receiver with no level cannot be checked against"
