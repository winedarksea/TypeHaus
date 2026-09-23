"""Three structural interference blind spots, each on a small synthetic model.

1. a plate/stud inside a rafter is a birdsmouth only where the seat holds
   (``checks/structural/_rafter_seat.py``, IRC R802.7.1 / NDS 4.4.3);
2. framing buried in a concrete or masonry wall layer
   (``structural.member_in_masonry``);
3. framing in the standoff space of an authored post base
   (``structural.post_base_interference``).
"""

from __future__ import annotations

from types import SimpleNamespace

from typehaus.checks.structural.interference import member_interference
from typehaus.checks.structural.masonry_interference import member_in_masonry
from typehaus.checks.structural.post_base_interference import post_base_interference
from typehaus.findings import Result
from typehaus.model.assembly import Assembly, Layer
from typehaus.model.enums import ConnectorKind, LayerFunction
from typehaus.model.materials import Material
from typehaus.model.structure import Beam, Connector, Post
from typehaus.quantities import inch
from typehaus.quantities import pt as point
from typehaus.resolve.model import FramedMember, ResolvedLayer, ResolvedSolid, ResolvedWall

_PREFS = SimpleNamespace(framing=SimpleNamespace(interference_tolerance_in=0.25))
IN = inch(1).meters


def _ctx(members=(), solids=(), walls=(), elements=(), library=None):
    elements = list(elements)
    plan = SimpleNamespace(all_elements=lambda: elements, library=library,
                           by_tag=lambda t: next((e for e in elements if e.tag == t), None))
    model = SimpleNamespace(all_members=lambda: list(members), solids=list(solids),
                            walls=list(walls), junctions=(), plan=plan)
    return SimpleNamespace(model=model, preferences=_PREFS, plan=plan)


def _fails(findings):
    return [f for f in findings if f.result is Result.FAIL]


# --------------------------------------------------------------- 1. the rafter seat
def _rafter(bottom_at_outer_face: float) -> FramedMember:
    """A 2x10 rafter at 3:12 running +x, its underside at ``bottom_at_outer_face`` over
    x = 0.130 (the plate's outer face)."""
    plumb = 9.25 * IN / 0.9701  # the 2x10's depth read plumb at 3:12
    z0 = bottom_at_outer_face - 0.25 * 0.130
    return FramedMember("RF-1", "rafter-000", "rafter", "2x10", (0.0, 0.0), (3.0, 0.0),
                        z0_m=z0, z1_m=z0 + plumb, length_m=3.1,
                        z0_end_m=z0 + 0.75, z1_end_m=z0 + 0.75 + plumb)


def _plate(top: float, parent: str = "W-1") -> FramedMember:
    """A flat 2x6 top plate crossing the rafter, 5 1/2" wide centred on x = 0.2."""
    return FramedMember(parent, "plate-top-1", "plate", "2x6", (0.2, -1.0), (0.2, 1.0),
                        z0_m=top - 1.5 * IN, z1_m=top, length_m=2.0)


def test_a_true_birdsmouth_seat_is_not_a_clash():
    """A 1.17" notch over the plate, underside above the plate's underside: a seat."""
    ctx = _ctx(members=[_rafter(2.40 - 1.17 * IN), _plate(2.40)])
    assert not _fails(member_interference(ctx))


def test_a_plate_inside_the_rafter_fails_with_its_citation():
    """The attic-partition case: the plate stands inside the rafter's depth, not under it."""
    ctx = _ctx(members=[_rafter(2.40 - 1.17 * IN), _plate(2.52)])
    [finding] = _fails(member_interference(ctx))
    assert finding.code_ref == "IRC R802.7.1; NDS 4.4.3"
    assert "inside the rafter" in finding.message
    assert finding.element_tags[:2] == ("RF-1", "W-1")


def _stud_under_rafter(poke_in: float):
    """A 2x10 rafter laid flat over a stud whose top pokes ``poke_in`` into it."""
    rafter = FramedMember("RF-1", "rafter-000", "rafter", "2x10", (-1.0, 0.0), (1.0, 0.0),
                          z0_m=2.4 - poke_in * IN, z1_m=2.4 - poke_in * IN + 9.25 * IN,
                          length_m=2.0)
    stud = FramedMember("W-1", "stud-000", "stud", "2x6", (0.0, 0.0), (0.0, 0.0),
                        z0_m=0.0, z1_m=2.4, length_m=2.4, orient=(0.0, 1.0))
    return _ctx(members=[rafter, stud])


def test_the_seat_is_capped_at_a_quarter_of_the_rafter_depth():
    """2" into a 9 1/4" rafter is a seat (limit 2.31"); 3" is not."""
    assert not _fails(member_interference(_stud_under_rafter(2.0)))
    [finding] = _fails(member_interference(_stud_under_rafter(3.0)))
    assert "exceeds 1/4" in finding.message


def _ridge_and_plate(plate_p0, plate_p1):
    ridge = FramedMember("RB-1", "ridge-beam", "ridge_beam", "2-1.75x16 LVL",
                         (0.0, 0.0), (3.0, 0.0), z0_m=2.5, z1_m=2.9, length_m=3.0)
    plate = FramedMember("W-G", "plate-top-1", "plate", "2x6", plate_p0, plate_p1,
                         z0_m=2.6, z1_m=2.6 + 1.5 * IN, length_m=1.0)
    return _ctx(members=[ridge, plate])


def test_a_ridge_pocketed_in_a_gable_wall_is_cleared():
    assert not _fails(member_interference(_ridge_and_plate((2.95, -1.0), (2.95, 1.0))))


def test_a_ridge_sunk_into_a_partition_under_it_fails():
    """Runs ALONG the wall: no end in it, so no pocket and no seat."""
    [finding] = _fails(member_interference(_ridge_and_plate((0.5, 0.0), (2.5, 0.0))))
    assert "no end pocketed" in finding.message


# ------------------------------------------------------ 2. framing in masonry/concrete
_BRICK = Material(tag="brick", name="Face brick", hatch="concrete")
_WASH = Material(tag="wash", name="Silicate wash", hatch="concrete", coating=True)
_WYTHE = Assembly(tag="WYTHE", layers=(
    Layer(name="brick", material_ref="brick", thickness=inch(3.625),
          function=LayerFunction.STRUCTURE),
    Layer(name="wash", material_ref="wash", thickness=inch(0.01),
          function=LayerFunction.FINISH),
))
_LIBRARY = SimpleNamespace(materials=(_BRICK, _WASH),
                           resolve_assembly=lambda t: _WYTHE if t == "WYTHE" else None)
_HALF = 3.625 * IN / 2.0


def _wythe(z0=0.0, z1=2.4, tag="W-BRICK") -> ResolvedWall:
    """A brick wythe running along y, centred on x = 0."""
    ring = [(-_HALF, -2.0), (_HALF, -2.0), (_HALF, 2.0), (-_HALF, 2.0)]
    layers = (ResolvedLayer("brick", "brick", "structure", 3.625 * IN, ring),
              ResolvedLayer("wash", "wash", "finish", 0.01 * IN, ring))
    return ResolvedWall(uid=f"{tag}-uid", tag=tag, storey="S", assembly="WYTHE",
                        axis=((0.0, -2.0), (0.0, 2.0)), layers=layers, z0_m=z0, z1_m=z1)


def _joist(x0, x1, z0=1.0, category="joist"):
    return FramedMember("FS-1", f"{category}-000", category, "2x10", (x0, 0.0), (x1, 0.0),
                        z0_m=z0, z1_m=z0 + 9.25 * IN, length_m=abs(x1 - x0))


def test_a_joist_through_a_brick_wythe_fails():
    """The porch-joist defect: framing run through a masonry layer."""
    ctx = _ctx(members=[_joist(-1.0, 1.0)], walls=[_wythe()], library=_LIBRARY)
    [finding] = _fails(member_in_masonry(ctx))
    assert finding.element_tags[:2] == ("FS-1", "W-BRICK")
    assert "brick (WYTHE)" in finding.message


def test_a_ledger_on_the_wall_face_and_a_joist_bearing_on_top_pass():
    """A legitimate ledger stops AT the face; a joist bearing on the wall top shares no
    height. Neither may FAIL, and the clean report says so."""
    ledger = FramedMember("FS-1", "rim-0", "rim", "2x10", (_HALF + 0.75 * IN, -1.0),
                          (_HALF + 0.75 * IN, 1.0), z0_m=1.0, z1_m=1.0 + 9.25 * IN,
                          length_m=2.0)
    bearing = _joist(-1.0, 1.0, z0=2.4)
    ctx = _ctx(members=[ledger, bearing, _joist(_HALF, 1.0)], walls=[_wythe()],
               library=_LIBRARY)
    findings = member_in_masonry(ctx)
    assert not _fails(findings)
    assert [f.result for f in findings] == [Result.PASS]


def _beam_solid(x0, x1, z0, z1, tag="BM-1"):
    return ResolvedSolid(uid=tag, tag=tag, storey="S", category="beam",
                         outline=[(x0, -0.04), (x1, -0.04), (x1, 0.04), (x0, 0.04)],
                         z0_m=z0, z1_m=z1)


def test_a_lintel_the_wythe_is_bedded_on_passes():
    """A steel angle in the bed joints: the masonry band starts at the beam's soffit."""
    wall = _wythe(z0=1.2, z1=1.6)
    lintel = ResolvedSolid(uid="BM-L", tag="BM-L", storey="S", category="beam",
                           outline=[(-0.02, -1.0), (0.02, -1.0), (0.02, 1.0), (-0.02, 1.0)],
                           z0_m=1.2, z1_m=1.2 + 3.5 * IN)
    assert not _fails(member_in_masonry(_ctx(solids=[lintel], walls=[wall],
                                             library=_LIBRARY)))


def test_a_beam_pocket_is_cleared_only_when_the_beam_names_the_wall():
    wall = _wythe()
    beam = _beam_solid(-0.03, 2.0, 1.0, 1.3)
    named = Beam(uid="BM1AAAAAAA", tag="BM-1", start_node="A", end_node="B",
                 bearing_refs=("W-BRICK",))
    unnamed = Beam(uid="BM1AAAAAAA", tag="BM-1", start_node="A", end_node="B")
    assert not _fails(member_in_masonry(_ctx(solids=[beam], walls=[wall], elements=[named],
                                             library=_LIBRARY)))
    assert _fails(member_in_masonry(_ctx(solids=[beam], walls=[wall], elements=[unnamed],
                                         library=_LIBRARY)))


def test_no_masonry_or_concrete_wall_is_an_earned_not_applicable():
    [finding] = member_in_masonry(_ctx(members=[_joist(-1.0, 1.0)], library=_LIBRARY))
    assert finding.result is Result.NOT_APPLICABLE


# ------------------------------------------------------------- 3. the post base space
def _post_base_ctx(beam_x0: float):
    """A 6x6 on an ABU66SS over a pier top at z = 0, and a seat beam on the same top."""
    post = Post(uid="PT1AAAAAAA", tag="PT-C", position=point(0.0, 0.0), size="6x6",
                supported_by="PT-PIER")
    base = Connector(uid="CN1AAAAAAA", tag="CN-BASE", kind=ConnectorKind.POST_BASE,
                     position=point(0.0, 0.0), elevation=inch(0), size="ABU66SS",
                     connects=("PT-C", "PT-PIER"))
    standoff = (1.0 + 0.1793) * IN
    column = ResolvedSolid(uid="PT1", tag="PT-C", storey="S", category="column",
                           outline=[(-0.07, -0.07), (0.07, -0.07), (0.07, 0.07),
                                    (-0.07, 0.07)], z0_m=standoff, z1_m=2.4)
    beam = _beam_solid(beam_x0, 1.0, 0.0, 7.25 * IN, tag="BM-SEAT")
    return _ctx(solids=[column, beam], elements=[post, base])


def test_a_beam_end_in_the_post_base_standoff_fails():
    """The PT-BW-W/-GW condition: the seat beam's end sits on the pier top inside the
    footprint of the post the ABU stands."""
    [finding] = _fails(post_base_interference(_post_base_ctx(-0.02)))
    assert finding.element_tags == ("BM-SEAT", "CN-BASE", "PT-C")
    assert "1.18\" standoff" in finding.message


def test_a_beam_stopped_at_the_post_face_passes():
    findings = post_base_interference(_post_base_ctx(0.08))
    assert not _fails(findings)
    assert [f.result for f in findings] == [Result.PASS]


# ------------------------------------------------------------------ catlin, pinned
def test_catlin_roof_seat_fails_are_the_attic_partitions_and_gable_end_rafters(catlin_ctx):
    """Sixteen (roof element, wall) pairs, all real at the time of writing:

    * RF-HOUSE's rafters and RB-HOUSE's ridge beam stand 11"-16" INTO the five attic
      partitions W-A-C1/-C1B/-C2/-C2B/-C2M (walls too tall; TODO "plate inside a rafter");
    * the gable end rafters lap 1.81" of their 2.31" flange into the six gable walls
      W-A-S1/-S2/-S3/-N1/-N2/-N2B with the raked plates inside the rafter depth.

    A count moving is information about the attic, not a threshold to raise."""
    seats = [f for f in member_interference(catlin_ctx) if f.code_ref is not None]
    pairs = sorted(f.element_tags[:2] for f in seats)
    partitions = ("W-A-C1", "W-A-C1B", "W-A-C2", "W-A-C2B", "W-A-C2M")
    gables = ("W-A-N1", "W-A-N2", "W-A-N2B", "W-A-S1", "W-A-S2", "W-A-S3")
    assert pairs == sorted([("RB-HOUSE", w) for w in partitions]
                           + [("RF-HOUSE", w) for w in (*partitions, *gables)])


def test_catlin_framing_in_concrete_is_the_walkout_end_studs_and_one_stair(catlin_ctx):
    """W-B-S2-FR/-S3-FR's end studs stand 2 3/4" inside W-B-S1/-S4 (their own node chain
    meets the pour with no junction to mitre them), and ST-B2M's lower stringer and
    landing rim sit in W-B-CN (the stair-to-wall-axis offset, TODO D3). The brick fireplace
    lintel, the backing blocks at concrete tees and every pier are cleared."""
    fails = _fails(member_in_masonry(catlin_ctx))
    assert sorted(f.element_tags[:2] for f in fails) == [
        ("ST-B2M", "W-B-CN"), ("ST-B2M", "W-B-CN"),
        ("W-B-S2-FR", "W-B-S1"), ("W-B-S3-FR", "W-B-S4")]


def test_catlin_post_base_clash_is_the_two_west_seat_beams(catlin_ctx):
    """PT-BW-W/-GW: each seat beam's end sits on the pier top inside the footprint of the
    6x6 the ABU66SS stands, over the full 1 3/16" standoff. The owner's design call."""
    findings = post_base_interference(catlin_ctx)
    assert sorted(f.element_tags for f in _fails(findings)) == [
        ("BM-BW-GARAGE-SEAT", "CN-BW-BASE-NW", "PT-BW-CNW"),
        ("BM-BW-HOUSE-SEAT", "CN-BW-BASE-W", "PT-BW-CW")]
