"""Corner packs and small-opening framing (plans/TODO.md §Framing follow-ups).

- unit: an L corner produces a three-stud pack — two studs in the owner wall plus the
  butting wall's end stud — none of which overlap in plan.
- unit: a 14" opening at 16" o.c. gets no header *and* keeps the two studs flanking it.
- unit: the stud-interruption analysis every consumer shares.
- integration: catlin's real corners and its four 14" bathroom windows.
"""

from __future__ import annotations

import math
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

from typehaus.model import (
    Assembly, Building, Library, Material, Node, PlanModel, Project, Site, Storey, Wall,
    degF, ft, pt,
)
from typehaus.model.assembly import FramingSpec, Layer
from typehaus.model.enums import LayerFunction
from typehaus.quantities import inch
from typehaus.resolve import resolve
from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.framing.openings import frame_opening
from typehaus.resolve.framing.solver import _framing_axis, frame_wall
from typehaus.resolve.framing.stud_module import opening_stud_module
from typehaus.resolve.geometry import sub, unit
from typehaus.resolve.model import ResolvedLayer, ResolvedWall
from typehaus.source import load_plan
from _helpers import CATLIN as CATLIN_DIR


_STUD_THICKNESS = inch(1.5).meters
_STUD_DEPTH = inch(3.5).meters
_MODULE = inch(16).meters
_VERTICAL_CATEGORIES = ("stud", "corner", "king", "jack")


def _mitred_wall(length_m: float, neighbour_band_m: float, at_start: bool) -> ResolvedWall:
    """A wall whose structure polygon is mitred at one end, as the junction solver leaves it.

    The mitre spans the shared corner square: projected onto the axis it runs from the far
    face of the neighbour's band to its near face, which is what the corner rule reads.
    """
    half = _STUD_DEPTH / 2.0
    if at_start:
        polygon = ((0.0, -half), (neighbour_band_m, half),
                   (length_m, half), (length_m, -half))
    else:
        polygon = ((0.0, -half), (0.0, half),
                   (length_m - neighbour_band_m, half), (length_m, -half))
    layer = ResolvedLayer(name="stud", material_ref="spf", function="structure",
                          thickness_m=_STUD_DEPTH, polygon=polygon)
    return ResolvedWall(uid="W1", tag="W-TEST", storey="MAIN", assembly="TEST_ASM",
                        axis=((0.0, 0.0), (length_m, 0.0)), layers=(layer,),
                        z0_m=0.0, z1_m=2.5)


def _plan_double(corner_style: str = "3-stud"):
    layer = Layer(name="stud", material_ref="spf", thickness=inch(3.5),
                  function=LayerFunction.STRUCTURE,
                  framing=FramingSpec(member="2x4", corner_style=corner_style))
    return SimpleNamespace(
        library=SimpleNamespace(resolve_assembly=lambda tag: SimpleNamespace(layers=(layer,)))
    )


def _stations(members, direction=(1.0, 0.0)) -> dict:
    return {m.child_key: m.p0[0] * direction[0] + m.p0[1] * direction[1]
            for m in members if m.p0 == m.p1}


# ------------------------------------------------------------------ corner unit tests
def test_owner_wall_end_stud_stops_at_the_far_face_of_the_corner_square():
    band = inch(5.5).meters
    rw = _mitred_wall(4.0, band, at_start=True)
    members = frame_wall(_plan_double(), rw, openings=[], corner_start=True)
    stations = _stations(members)
    # Flush with the far face of the neighbour's band: half a stud inboard of it.
    assert stations["stud-000"] == pytest.approx(_STUD_THICKNESS / 2.0, abs=1e-9)
    # The supplemental corner stud packs face-to-face inboard of it — three studs total at
    # the corner once the neighbour's own end stud butts the other side.
    assert stations["corner-start"] == pytest.approx(_STUD_THICKNESS * 1.5, abs=1e-9)


def test_butting_wall_end_stud_stops_at_the_near_face_of_the_corner_square():
    band = inch(5.5).meters
    rw = _mitred_wall(4.0, band, at_start=True)
    members = frame_wall(_plan_double(), rw, openings=[], butting_start=True)
    stations = _stations(members)
    assert stations["stud-000"] == pytest.approx(band + _STUD_THICKNESS / 2.0, abs=1e-9)
    assert not [m for m in members if m.category == "corner"]


def test_corner_plates_lap_opposite_ways_so_they_never_double_in_the_corner():
    band = inch(5.5).meters
    rw = _mitred_wall(4.0, band, at_start=True)
    members = frame_wall(_plan_double(), rw, openings=[], corner_start=True)
    plates = {m.child_key: m for m in members if m.category == "plate"}
    # Bottom + lower top plate run through the corner square the wall owns; the cap plate
    # laps back so the neighbour's cap can run over it.
    assert plates["plate-bottom"].p0[0] == pytest.approx(0.0, abs=1e-9)
    assert plates["plate-top-0"].p0[0] == pytest.approx(0.0, abs=1e-9)
    assert plates["plate-top-1"].p0[0] == pytest.approx(band, abs=1e-9)


# ---------------------------------------------------------- small-opening unit tests
def _fourteen_inch_window_wall():
    """A 4 m wall with a 14" window centred on the bay between the 4th and 5th studs."""
    rw = _mitred_wall(4.0, 0.0, at_start=True)
    center = 4.5 * _MODULE
    opening = SimpleNamespace(center_m=center, width_m=inch(14).meters,
                              height_m=inch(36).meters, sill_m=inch(24).meters,
                              is_door=False, operation=None)
    members = frame_wall(_plan_double(), rw, openings=[opening])
    return center, members


def test_fourteen_inch_window_gets_no_header_but_keeps_both_flanking_studs():
    center, members = _fourteen_inch_window_wall()
    assert not [m for m in members if m.category in ("header", "king", "jack")]
    half = inch(7).meters
    stations = sorted(m.p0[0] for m in members if m.category == "stud")
    left = [s for s in stations if s <= center - half + 1e-9]
    right = [s for s in stations if s >= center + half - 1e-9]
    assert left and right, "the bay's bounding studs must survive a header-free opening"
    assert max(left) == pytest.approx(4 * _MODULE, abs=1e-9)
    assert min(right) == pytest.approx(5 * _MODULE, abs=1e-9)


def test_header_free_sill_and_head_bear_on_the_flanking_studs():
    _center, members = _fourteen_inch_window_wall()
    sill = next(m for m in members if m.category == "sill")
    head = next(m for m in members if m.child_key.startswith("roughhead-"))
    clear_bay = _MODULE - _STUD_THICKNESS
    for member in (sill, head):
        assert member.length_m == pytest.approx(clear_bay, abs=1e-9)
        assert member.p0[0] == pytest.approx(4 * _MODULE + _STUD_THICKNESS / 2, abs=1e-9)


def _thirty_inch_window_wall():
    """A 4 m wall with a 30" window on a stud line: the header/jack/king path."""
    rw = _mitred_wall(4.0, 0.0, at_start=True)
    center = 4 * _MODULE
    opening = SimpleNamespace(center_m=center, width_m=inch(30).meters,
                              height_m=inch(36).meters, sill_m=inch(24).meters,
                              is_door=False, operation=None, header_spec=None,
                              pocket_run_m=0.0, pocket_sign=0)
    return rw, frame_wall(_plan_double(), rw, openings=[opening])


def test_opening_pack_is_framed_from_the_wall_base_not_the_stud_bearing_line():
    """A sill height is measured from ``base_ref_z_m``; a jack bears a plate above it.

    The solver hands ``frame_opening`` one elevation for both jobs, and reading it as the
    sill datum framed every opening in a house 1 1/2" above the hole every other emitter
    cut — the wall body, the buck, the furring, the IFC void. On top of that the rough
    sill was emitted upward from the sill line rather than hanging under it, another
    1 1/2", which is what left a 2x6 lying across the glass of each window.
    """
    rw, members = _thirty_inch_window_wall()
    plate_h = inch(1.5).meters
    sill_line = rw.base_ref_z_m + inch(24).meters
    head_line = sill_line + inch(36).meters

    sill = next(m for m in members if m.category == "sill")
    assert sill.z1_m == pytest.approx(sill_line, abs=1e-9), "the sill's TOP is the RO"
    assert sill.z0_m == pytest.approx(sill_line - plate_h, abs=1e-9)

    header = next(m for m in members if m.category == "header")
    assert header.z0_m == pytest.approx(head_line, abs=1e-9), "the header bears ON the head"

    # …and the members that genuinely stand on the bottom plate did not move with it.
    for category in ("jack", "king"):
        member = next(m for m in members if m.category == category)
        assert member.z0_m == pytest.approx(rw.base_ref_z_m + plate_h, abs=1e-9)
    cripple = next(m for m in members if m.child_key.startswith("cripple-sill-"))
    assert cripple.z0_m == pytest.approx(rw.base_ref_z_m + plate_h, abs=1e-9)
    assert cripple.z1_m == pytest.approx(sill.z0_m, abs=1e-9), "cripples carry the sill"


def test_header_free_opening_registers_on_the_same_lines():
    """The bay path frames the same two elevations — and it is the only framing in the
    hole, so a misplaced sill there is the whole of what a small window shows."""
    rw = _mitred_wall(4.0, 0.0, at_start=True)
    _center, members = _fourteen_inch_window_wall()
    plate_h = inch(1.5).meters
    sill_line = rw.base_ref_z_m + inch(24).meters

    sill = next(m for m in members if m.category == "sill")
    assert sill.z1_m == pytest.approx(sill_line, abs=1e-9)
    assert sill.z0_m == pytest.approx(sill_line - plate_h, abs=1e-9)
    # The head nailer is the mirror image: it sits ON the head, backing it from above.
    head = next(m for m in members if m.child_key.startswith("roughhead-"))
    assert head.z0_m == pytest.approx(sill_line + inch(36).meters, abs=1e-9)


def test_an_opening_that_reaches_the_floor_gets_no_rough_sill():
    """A cased opening with ``sill_m == 0`` has the bottom plate as its sill. Emitting a
    member anyway laid a 2x4 across the threshold, an inch and a half off the floor."""
    rw = _mitred_wall(4.0, 0.0, at_start=True)
    opening = SimpleNamespace(center_m=2.5 * _MODULE, width_m=inch(30).meters,
                              height_m=inch(80).meters, sill_m=0.0,
                              is_door=False, operation=None, header_spec=None,
                              pocket_run_m=0.0, pocket_sign=0)
    members = frame_wall(_plan_double(), rw, openings=[opening])
    assert not [m for m in members if m.category == "sill"]
    header = next(m for m in members if m.category == "header")
    assert header.z0_m == pytest.approx(rw.base_ref_z_m + inch(80).meters, abs=1e-9)


def test_header_free_opening_with_no_bounding_studs_adds_its_own_pair():
    # The bay's studs can be missing — a neighbouring opening's jamb pack takes them, or the
    # opening sits past the last module station. The sill and head nailer bear on them, so
    # the header-free path adds the pair itself rather than leaving them floating.
    rw = _mitred_wall(4.0, 0.0, at_start=True)
    opening = SimpleNamespace(center_m=2.5 * _MODULE, width_m=inch(14).meters,
                              height_m=inch(36).meters, sill_m=inch(24).meters,
                              is_door=False, operation=None)
    out = frame_opening(rw, (1.0, 0.0), (0.0, 0.0), opening, "2x4", 0.0,
                        lambda _station: 2.4, 0, _MODULE, stud_stations=())
    flanking = [m for m in out if m.child_key.startswith("flank-")]
    assert len(flanking) == 2
    assert not [m for m in out if m.category == "header"]
    assert all(m.category == "stud" for m in flanking)


# --------------------------------------------------------- stud-module analysis tests
@pytest.mark.parametrize(
    "width_in, center_in, expected_interrupted, expected_minimum",
    [
        (14, 8, 0, 0),     # fits inside one bay
        (14, 0, 1, 0),     # same window on a stud line: cuts the stud it straddles
        (15, 8, 2, 1),     # 15" > the 14.5" clear bay: cuts 1/4" into each flanking stud
        (30, 0, 1, 1),     # centred on a stud line, as intended
        (30, 8, 2, 1),     # off-centre: one stud more than its width requires
    ],
)
def test_stud_interruption_counts(width_in, center_in, expected_interrupted,
                                  expected_minimum):
    module = opening_stud_module(inch(center_in).meters, inch(width_in).meters,
                                 _MODULE, _STUD_THICKNESS)
    assert module.interrupted == expected_interrupted
    assert module.minimum_interrupted == expected_minimum
    assert module.straddles_awkwardly is (expected_interrupted > expected_minimum)


def test_stud_module_describes_the_awkward_case_with_its_offset():
    module = opening_stud_module(inch(8).meters, inch(30).meters, _MODULE, _STUD_THICKNESS)
    text = module.describe()
    assert "interrupts 2 studs at 16\" o.c." in text
    assert "instead of 1" in text
    assert module.ideal_label == "stud line"


# --------------------------------------------------- per-end corner-style integration
def _box_plan(**wall_fields) -> PlanModel:
    """A bare 20x14 box of framed walls — four L corners, ``wall_fields`` on every wall."""
    ext = Assembly(tag="EXT", layers=(
        Layer(name="stud", material_ref="wood", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6")),
    ))
    project = Project(
        name="Corners", project_uuid=uuid.UUID("00000000-0000-4000-8000-0000000000c4"),
        site=Site(lat=44.9, lon=-93.2, elevation=ft(830), design_temp_heating=degF(-15),
                  design_temp_cooling=degF(90)), building=Building(name="Corners"))
    main = Storey(uid="STMAIN00C4", tag="main", elevation=ft(0),
                  default_ceiling_height=ft(9))
    nodes = tuple(
        Node(uid=f"NC4{i:07d}", tag=f"N-{i}", position=position)
        for i, position in enumerate((
            pt(ft(0), ft(0)), pt(ft(20), ft(0)), pt(ft(20), ft(14)), pt(ft(0), ft(14)),
        ), 1))
    walls = tuple(
        Wall(uid=f"WC4{i:07d}", tag=f"W-{i}", start_node=f"N-{start}",
             end_node=f"N-{end}", assembly="EXT", top=ft(9), **wall_fields)
        for i, (start, end) in enumerate(((1, 2), (2, 3), (3, 4), (4, 1)), 1))
    plan = PlanModel(project=project, library=Library(
        materials=(Material(tag="wood", name="Wood", r_per_inch=1.25),),
        assemblies=(ext,)), storeys=(main,))
    return plan.with_elements("main", (*nodes, *walls))


def test_authored_per_end_corner_style_reaches_the_framing_solver():
    """The 4-stud override authored on ``Wall.corner_style_start/end`` doubles every
    supplemental corner stud the box's owned ends emit, end for end."""
    def corner_keys(model):
        return sorted((wall.tag, member.child_key) for wall in model.walls
                      for member in wall.members if member.category == "corner")

    base, _ = resolve(_box_plan())
    boxed, _ = resolve(_box_plan(corner_style_start="4-stud", corner_style_end="4-stud"))
    base_keys = corner_keys(base)
    boxed_keys = corner_keys(boxed)
    assert base_keys, "the box must own some L corners"
    assert not [key for _tag, key in base_keys if key.endswith("-2")]
    # Same owned ends, one extra stud at each of them, nothing else moved.
    assert [key for key in boxed_keys if not key[1].endswith("-2")] == base_keys
    assert len(boxed_keys) == 2 * len(base_keys)


def test_end_only_corner_style_override_reaches_its_owner():
    """``corner_style_end="4-stud"`` authored ALONE (no matching ``corner_style_start``).

    On a CCW box every wall's ``end`` butts the next wall's ``start`` — the shape catlin's
    real exterior loop is authored in, and four-for-four the reason a 4-stud override
    authored only on ``corner_style_end`` used to take effect nowhere: the wall that
    authors it never owns that corner (``topology.py`` gives L ownership to the wall that
    *starts* there), so the style has to travel to the neighbour that owns it instead of
    being read off the owning wall's own fields.
    """
    def corner_keys(model):
        return sorted((wall.tag, member.child_key) for wall in model.walls
                      for member in wall.members if member.category == "corner")

    base, _ = resolve(_box_plan())
    boxed, _ = resolve(_box_plan(corner_style_end="4-stud"))
    base_keys = corner_keys(base)
    boxed_keys = corner_keys(boxed)
    assert base_keys, "the box must own some L corners"
    assert [key for key in boxed_keys if not key[1].endswith("-2")] == base_keys
    assert len(boxed_keys) == 2 * len(base_keys)


# ------------------------------------------------------------------- catlin integration
@pytest.fixture(scope="module")
def catlin_resolved():
    model, findings = resolve(load_plan(CATLIN_DIR).plan)
    assert not [f for f in findings if f.severity.value == "error"]
    return model


def _corner_pack(model, junction, radius_m):
    """Vertical members of the junction's own walls within ``radius_m`` of the node.

    Scoped to the incident walls on purpose: walls of other storeys stack at the same plan
    coordinates, and their studs are not part of this corner's pack.
    """
    incident = {item.wall_tag for item in junction.incidents}
    out = []
    for wall in model.walls:
        if wall.tag not in incident:
            continue
        for member in wall.members:
            if member.category not in _VERTICAL_CATEGORIES:
                continue
            if math.hypot(member.p0[0] - junction.point[0],
                          member.p0[1] - junction.point[1]) <= radius_m:
                out.append((wall.tag, member))
    return out


def test_every_framed_catlin_corner_carries_a_three_stud_pack(catlin_resolved):
    from shapely.geometry import Polygon

    framed = {wall.tag for wall in catlin_resolved.walls if wall.members}
    corners = [j for j in catlin_resolved.junctions
               if j.kind == "l" and {i.wall_tag for i in j.incidents} <= framed and framed]
    assert corners, "catlin must still have framed L corners to check"
    for junction in corners:
        pack = _corner_pack(catlin_resolved, junction, inch(10).meters)
        assert len(pack) >= 3, (junction.node_tag, [m.child_key for _t, m in pack])
        # The studs of a corner pack touch; they must never share plan area.
        polygons = [Polygon(member_footprint(member)[0]) for _tag, member in pack]
        for i, a in enumerate(polygons):
            for b in polygons[i + 1:]:
                assert a.intersection(b).area < 1e-5, junction.node_tag


def test_catlin_small_windows_have_no_header_and_keep_their_flanking_studs(catlin_resolved):
    walls = {wall.tag: wall for wall in catlin_resolved.walls}
    small = [o for o in catlin_resolved.openings
             if not o.is_door and o.width_m <= inch(14).meters + 1e-9]
    # This is a stud-framing rule, so it only applies to windows in framed walls. A 14" RO
    # in a poured wall has no bay to fit between and no stud to avoid breaking: WIN-B-SAUNA
    # took WT-1424 on 2026-07-30 for its *size*, and its host W-B-S2 is 12" concrete.
    # The split is on *stud-bearing* members, not on having any member at all: since
    # 2026-08-18 W-B-S2 carries the sauna liner's horizontal 1x4 furring strapping, which is
    # fastened to the pour and frames nothing — a wall can have members and still have no bay
    # to fit a window between. Split rather than filtered so a framed wall can never quietly
    # drop out of the checks below by losing its framing.
    def _is_framed(wall):
        return any(member.category in _VERTICAL_CATEGORIES for member in wall.members)

    concrete = [o for o in small if not _is_framed(walls[o.host_wall])]
    framed = [o for o in small if _is_framed(walls[o.host_wall])]
    # AO-B-BRICK-WIN joined it on 2026-08-03: the reveal through the glazed-brick veneer in
    # front of WIN-B-SAUNA. Same 14", same reason — a single brick wythe has no members
    # either, so there is no bay to fit between and no stud to break.
    assert [o.tag for o in concrete] == ["WIN-B-SAUNA", "AO-B-BRICK-WIN"], \
        [o.tag for o in concrete]
    # The original 5 became 15 as the 14" family took over the places where a bigger unit
    # never fit, then 13 when the 2026-08-01 gable pass retired the south gable's corner
    # pair (WIN-A-S1/S4), then 12 when the 2026-08-15 west facade pass retyped WIN-M-BATH2
    # up to a 27" WT-2736-T. That one is the family's limit rather than a counterexample:
    # a 14" RO centres on a *bay centre* and a 27" one on a *stud line*, 8" apart, so a 14"
    # unit can never stack in a column with a 27" one — and BATH2 had to join a column.
    # What is left on 14": the garage pair (WIN-G-N1/S1), the two
    # surviving gable flankers (WIN-A-S2/S3, now WT-1448 — 48" tall but still a 14" RO, so
    # still headerless and still counted here), and the four 5' knee-wall windows
    # (WIN-A-W-S/W-N, WIN-A-E-S/E-N). Every one of them still passes the per-window checks
    # below — which is the whole reason the facade work could use this size so freely, and
    # why growing the flankers 24" taller cost the framing nothing.
    # 13 since 2026-08-24: WIN-M-KIT-E, the kitchen's second small window, on the east
    # wall at y=34'-0" over FURN-M-KIT-N4's counter. Its presence in THIS list rather than
    # the header list is the whole point of choosing 34'-0" — 408" off N-M-SE is 8" mod 16",
    # a bay centre on the merged W-M-E1's own grid, so a 14" RO drops into the bay whole.
    # 15 after the west-facade recomposition: WIN-M-BATH1-W and WIN-S-VANITY-W form the
    # exact y=24'-4" service-window column, each wholly inside the corresponding clear bay.
    assert len(framed) == 15, [o.tag for o in framed]
    for opening in framed:
        wall = walls[opening.host_wall]
        start, end = _framing_axis(wall)
        direction = unit(sub(end, start))
        def station(point, start=start, direction=direction) -> float:
            return ((point[0] - start[0]) * direction[0]
                    + (point[1] - start[1]) * direction[1])

        stations = [station(member.p0) for member in wall.members
                    if member.category in _VERTICAL_CATEGORIES]
        low = opening.center_along_m - opening.width_m / 2
        high = opening.center_along_m + opening.width_m / 2
        assert [s for s in stations if s <= low + 1e-9], opening.tag
        assert [s for s in stations if s >= high - 1e-9], opening.tag
        # PROJECT the header onto the wall axis before comparing it to `center_along_m`,
        # which is a distance ALONG the wall. This used to read `(m.p0[0] + m.p1[0]) / 2`
        # — a raw x — which is only comparable to a station on an EAST-WEST wall that
        # starts at x=0. On a north-south wall it compares an x against a y: W-M-E1's
        # members all sit at x=36'-0" (10.97 m), so every header on that wall matched every
        # opening within 1 m of 10.97, and WIN-M-KIT-E (station 10.36 m) was reported as
        # headered by WIN-M-EAST-MID's header 16 feet away. It has no header — its stud
        # stations at 33'-4" and 34'-8" are both intact, which is the assertion above.
        headers = [m for m in wall.members if m.category == "header"
                   and abs((station(m.p0) + station(m.p1)) / 2
                           - opening.center_along_m) < 1.0]
        assert not headers, opening.tag
