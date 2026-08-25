"""Layout lines: the derived wall-line chain, and the three things that hang off it.

``plans/11-m1-resolve.md`` §Vertical stacking (#43) asked for a "stacking matrix" and nobody
built one. This is it — aligned / width-change / setback / ambiguous-needs-a-tiebreaker,
plus the *horizontal* case the pairwise ``stack_edges`` model never had a shape for: two
collinear walls split at a tee are one line, and the second one's station on it is the
first one's length.

Then the consumers, each proving the property that made the line worth deriving:

* ``LayerDatum.LINE_BASE`` — a band measured from the line rather than from the wall, so
  brick coursing continues across a storey line instead of restarting at it.
* ``FramingSpec.layout_origin="line"`` — the stud module continues across a tee split and
  stacks floor to floor, *including* when the upper wall is authored reversed, which is the
  case ``direction_sign`` exists for.
* ``WallPaneling.layout_line`` — a facade band whose scope is the line, not a room.
"""

from __future__ import annotations

import hashlib
import math
import uuid

import pytest

from typehaus.model import (
    Assembly,
    Building,
    CavityFill,
    FramingSpec,
    Layer,
    LayerBound,
    LayerDatum,
    LayerExtent,
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
    face,
    ft,
    inch,
    pt,
)
from typehaus.resolve.layout_lines import lines_by_wall, resolve_layout_lines

_IN = 39.3700787
_UID = uuid.UUID("00000000-0000-4000-8000-0000000000cc")


def _assembly(tag: str, stud: str = "2x6", *, layout_origin: str = "wall-start",
              banded: bool = False) -> Assembly:
    layers = [
        Layer(name="stud", material_ref="spf",
              thickness=inch(5.5 if stud == "2x6" else 3.5),
              function=LayerFunction.STRUCTURE,
              framing=FramingSpec(member=stud, layout_origin=layout_origin),
              cavity=CavityFill(material_ref="spf")),
        Layer(name="sheathing", material_ref="spf", thickness=inch(0.5),
              function=LayerFunction.SHEATHING),
    ]
    if banded:
        # Two regions of one row tiling the whole LINE — the veneer-coursing shape.
        layers.append(Layer(
            name="plinth", material_ref="spf", thickness=inch(3.625),
            function=LayerFunction.CLADDING, slot="wythe",
            extent=LayerExtent(bottom=LayerBound(datum=LayerDatum.LINE_BASE),
                               top=LayerBound(datum=LayerDatum.LINE_BASE,
                                              offset=inch(32.0)))))
        layers.append(Layer(
            name="field", material_ref="spf", thickness=inch(3.625),
            function=LayerFunction.CLADDING, slot="wythe",
            extent=LayerExtent(bottom=LayerBound(datum=LayerDatum.LINE_BASE,
                                                 offset=inch(32.0)))))
    return Assembly(tag=tag, layers=tuple(layers))


def _plan(storeys, assemblies) -> PlanModel:
    project = Project(
        name="Lines", project_uuid=_UID,
        site=Site(lat=44.9, lon=-93.2, elevation=ft(830), design_temp_heating=degF(-15)),
        building=Building(name="Lines"),
    )
    return PlanModel(
        project=project,
        library=Library(materials=(Material(tag="spf", name="SPF", r_per_inch=1.25),),
                        assemblies=tuple(assemblies)),
        storeys=storeys,
    )


def _uid(prefix: str, tag: str) -> str:
    """A stable 10-character uid.

    ``hash()`` is salted per process and a colliding uid is a hard load-time error, so the
    fixture mints from the tag rather than from anything that varies run to run.
    """
    return prefix + hashlib.md5(tag.encode()).hexdigest()[:9].upper()


def _node(tag: str, x, y) -> Node:
    return Node(uid=_uid("N", tag), tag=tag, position=pt(x, y))


def _wall(tag: str, a: Node, b: Node, assembly: str = "EXT", **kwargs) -> Wall:
    # Aligned on the sheathing face, which is both what catlin does and what makes the
    # width-change case mean anything: two walls of different depth *centred* on one node
    # line genuinely do not share a sheathing face, and no datum can pretend they do.
    return Wall(uid=_uid("W", tag), tag=tag, start_node=a.tag, end_node=b.tag,
                assembly=assembly, alignment=face("sheathing-ext"), **kwargs)


#: Every fixture storey is this rectangle: 20' x 14', walked counter-clockwise from the
#: origin. A **closed loop**, deliberately — ``resolve.orientation`` derives a wall's
#: outward side from the loop it belongs to, and the vertical datum is a *face*, so a wall
#: with no loop has no settled outward side and two collinear walls can disagree about
#: which way their datum face lies. Real storeys are loops; the fixture is one too.
_CORNERS = ((ft(0), ft(0)), (ft(20), ft(0)), (ft(20), ft(14)), (ft(0), ft(14)))
_EDGES = ((0, 1), (1, 2), (2, 3), (3, 0))


def _rect_storey(prefix: str, top, assembly: str = "EXT", *,
                 clockwise: bool = False, y_offset=ft(0),
                 split_south: bool = False, split_at=None,
                 south_assembly: str | None = None):
    """The four walls of one storey's rectangle, and their nodes.

    ``clockwise`` walks the loop the other way, so every wall on it — the south wall
    included — is authored end-to-start relative to a counter-clockwise storey. That is the
    real shape of "authored reversed" and the case ``LayoutLineMember.direction_sign``
    exists for; reversing *one* wall inside a loop is a different thing entirely (it turns
    that wall's assembly inside out) and is not what this models.

    ``split_south`` cuts edge 0 in two at ``split_at`` — the tee-split shape, and, on an
    upper storey, the two-walls-over-one shape. The default 10' is deliberately *off* the
    16" module (120" is 8" out); pass a multiple of 16" for the other case, where the seam
    and a module station want the same stud.
    """
    positions = [(x, y + y_offset if index in (0, 1) else y)
                 for index, (x, y) in enumerate(_CORNERS)]
    nodes = [_node(f"N-{prefix}-{i}", x, y) for i, (x, y) in enumerate(positions)]
    walls, extra = [], []
    for index, (a, b) in enumerate(_EDGES):
        if index == 0 and split_south:
            mid = _node(f"N-{prefix}-MID",
                        ft(10) if split_at is None else split_at, positions[0][1])
            extra.append(mid)
            pairs = [(nodes[a], mid, f"W-{prefix}-0A"), (mid, nodes[b], f"W-{prefix}-0B")]
        else:
            pairs = [(nodes[a], nodes[b], f"W-{prefix}-{index}")]
        for start, end, tag in pairs:
            if clockwise:
                start, end = end, start
            walls.append(_wall(tag, start, end, top=top,
                               assembly=(south_assembly or assembly) if index == 0
                               else assembly))
    used = {w.start_node for w in walls} | {w.end_node for w in walls}
    return (*[n for n in (*nodes, *extra) if n.tag in used], *walls)


def _two_storey(assemblies=None, *, upper=None, lower=None, platform_band=None,
                **asm_kwargs) -> PlanModel:
    """Main (9') under second (8'), each a rectangle, each authored by the caller.

    ``platform_band`` lifts the upper storey by a floor thickness, so the lower wall tops
    out that far *below* the upper wall's base — real platform framing, and the shape every
    other fixture here quietly lacks: with second at exactly ``ft(9)`` the two walls touch,
    and a vertical-adjacency test can never be exercised. 13 3/8" is catlin's basement band
    (mudsill + 11 7/8" rim), the same number ``test_layer_extent._lift_plan`` uses.
    """
    main = Storey(uid="STMAIN00LL", tag="main", elevation=ft(0),
                  default_ceiling_height=ft(9))
    second = Storey(uid="STSEC000LL", tag="second",
                    elevation=ft(9) if platform_band is None else ft(9) + platform_band,
                    default_ceiling_height=ft(8))
    plan = _plan((main, second), assemblies or (_assembly("EXT", **asm_kwargs),))
    return (plan
            .with_elements("main", _rect_storey("M", ft(9), **(lower or {})))
            .with_elements("second", _rect_storey("S", ft(8), **(upper or {}))))


def _south_line(plan: PlanModel, wall_tag: str = "W-M-0"):
    return lines_by_wall(resolve_layout_lines(plan))[wall_tag]


# --- the stacking matrix -----------------------------------------------------------------


def test_an_aligned_stack_is_one_line_with_both_members():
    line = _south_line(_two_storey())
    assert {m.wall_tag for m in line.members} == {"W-M-0", "W-S-0"}
    assert {m.storey for m in line.members} == {"main", "second"}
    assert all(m.u_offset_m == pytest.approx(0.0) for m in line.members)
    assert all(m.direction_sign == 1 for m in line.members)
    assert line.base_z_m == pytest.approx(0.0)
    assert line.top_z_m == pytest.approx(ft(17).meters)


def test_a_width_change_still_stacks_on_the_shared_datum_face():
    """A 2x4 wall over a 2x6 one. Their centrelines are 1" apart, so a centreline read
    would call them two lines; the datum face (``Storey.vertical_datum``) is what #43 says
    to group on, and on the sheathing face they are one line."""
    assemblies = (_assembly("EXT"), _assembly("THIN", stud="2x4"))
    depths = {a.tag: sum(ly.thickness.meters for ly in a.layers) for a in assemblies}
    assert depths["EXT"] != depths["THIN"], "fixture: the two walls must differ in depth"

    plan = _two_storey(assemblies, upper={"south_assembly": "THIN"})
    line = _south_line(plan)
    assert {m.wall_tag for m in line.members} == {"W-M-0", "W-S-0"}


def test_a_platform_band_between_the_storeys_is_still_one_line():
    """The case every other fixture here misses, and the reason the interior never stacked.

    Platform framing puts a floor — 13 3/8" at catlin's basement, 12" above it — between a
    wall's top plate and the base of the wall over it, so the two are nowhere near touching.
    Grouping on *vertical adjacency* calls them two lines and quietly makes
    ``layout_origin="line"`` a no-op for every wall that is not authored ``stacks_on``.
    The question a layout line asks is the one ``stacking._axis_match`` asks — collinear,
    and overlapping by at least ``_MIN_OVERLAP`` — and nothing about the gap between them.
    """
    plan = _two_storey(platform_band=inch(13.375))
    by_wall = lines_by_wall(resolve_layout_lines(plan))
    assert by_wall["W-M-0"].tag == by_wall["W-S-0"].tag
    line = by_wall["W-M-0"]
    assert {m.wall_tag for m in line.members} == {"W-M-0", "W-S-0"}
    assert line.base_z_m == pytest.approx(0.0)
    assert line.top_z_m == pytest.approx((ft(9) + inch(13.375) + ft(8)).meters)


def test_a_setback_wall_over_a_platform_band_is_still_two_lines():
    """The band must not become a licence to weld anything vaguely above anything else:
    two feet inboard is still not the same wall line. The companion to
    ``test_a_setback_wall_is_a_line_of_its_own`` with the gap that test does not have."""
    plan = _two_storey(platform_band=inch(13.375), upper={"y_offset": ft(2)})
    by_wall = lines_by_wall(resolve_layout_lines(plan))
    assert by_wall["W-M-0"].tag != by_wall["W-S-0"].tag


def test_a_setback_wall_is_a_line_of_its_own():
    """Two feet inboard is not the same wall line, and must not be welded onto one."""
    plan = _two_storey(upper={"y_offset": ft(2)})
    by_wall = lines_by_wall(resolve_layout_lines(plan))
    assert by_wall["W-M-0"].tag != by_wall["W-S-0"].tag


def test_two_walls_over_one_both_join_its_line():
    """The case a single-chain model gets wrong. ``stacking.resolve_stacking`` collapses to
    ``candidates[:1]`` and reports ``integrity.stack_ambiguous``; a *line* has no reason to
    choose — a shared datum is shared by all three — so both uppers are members."""
    plan = _two_storey(upper={"split_south": True})
    line = _south_line(plan)
    assert {m.wall_tag for m in line.members} == {"W-M-0", "W-S-0A", "W-S-0B"}
    stations = {m.wall_tag: round(m.u_offset_m * _IN, 3) for m in line.members}
    assert stations["W-M-0"] == pytest.approx(0.0)
    assert stations["W-S-0A"] == pytest.approx(0.0)
    assert stations["W-S-0B"] == pytest.approx(120.0)


def test_an_upper_wall_authored_reversed_keeps_a_negative_direction_sign():
    line = _south_line(_two_storey(upper={"clockwise": True}))
    upper = line.member("W-S-0")
    assert upper is not None, "a reversed wall fell off its own line"
    assert upper.direction_sign == -1
    # Its own station 0 is at the far end of the line; the lower wall's is at the origin.
    assert upper.u_offset_m == pytest.approx(ft(20).meters)
    assert line.member("W-M-0").u_offset_m == pytest.approx(0.0)


# --- the horizontal case ------------------------------------------------------------------


def _tee_split_plan(split_at=None, **asm_kwargs) -> PlanModel:
    """One 20' south plane authored as two segments meeting at a mid node."""
    main = Storey(uid="STMAIN00TT", tag="main", elevation=ft(0),
                  default_ceiling_height=ft(9))
    plan = _plan((main,), (_assembly("EXT", **asm_kwargs),))
    return plan.with_elements("main", _rect_storey("M", ft(9), split_south=True,
                                                   split_at=split_at))


def test_two_segments_split_at_a_tee_are_one_line():
    line = _south_line(_tee_split_plan(), "W-M-0A")
    assert {m.wall_tag for m in line.members} == {"W-M-0A", "W-M-0B"}, \
        "only the two collinear segments belong; the returns are perpendicular"
    stations = {m.wall_tag: m.u_offset_m for m in line.members}
    assert stations["W-M-0A"] == pytest.approx(0.0)
    # The second member's station is the first one's length. That is the whole claim.
    assert stations["W-M-0B"] == pytest.approx(ft(10).meters)


def test_the_derived_line_does_not_depend_on_authoring_order():
    plan = _tee_split_plan()
    elements = list(plan.storey_elements("main"))
    shuffled = _plan(plan.storeys, plan.library.assemblies).with_elements(
        "main", tuple(reversed(elements)))

    def shape(lines):
        return [(line.tag, line.origin, line.direction,
                 tuple(sorted(m.wall_tag for m in line.members))) for line in lines]

    assert shape(resolve_layout_lines(plan)) == shape(resolve_layout_lines(shuffled))


# --- LINE_BASE ----------------------------------------------------------------------------


def test_a_line_banded_layer_continues_across_the_storey_line():
    """The point of the datum. The plinth is 32" from the *line's* base, so the wall above
    carries only the field — where WALL_BASE would have restarted the coursing on it."""
    from typehaus.resolve import resolve

    model, _findings = resolve(_two_storey(banded=True))
    lower, upper = model.wall("W-M-0"), model.wall("W-S-0")

    plinth = next(ly for ly in lower.layers if ly.name == "plinth")
    assert plinth.band(lower)[0] == pytest.approx(lower.z0_m)
    assert (plinth.band(lower)[1] - lower.z0_m) * _IN == pytest.approx(32.0, abs=1e-3)

    # The upper wall is wholly above the plinth's band, so the clamp drops the layer.
    assert "plinth" not in [ly.name for ly in upper.layers], \
        "the coursing restarted at the storey line"
    field = next(ly for ly in upper.layers if ly.name == "field")
    assert field.band(upper)[0] == pytest.approx(upper.z0_m)
    assert field.band(upper)[1] == pytest.approx(upper.z1_m)


# --- layout_origin="line" -------------------------------------------------------------------


def _line_stations(line, wall) -> list[float]:
    """Every stud of ``wall``, projected onto ``line`` — where they have to agree."""
    ox, oy = line.origin
    dx, dy = line.direction
    return sorted(round(((m.p0[0] - ox) * dx + (m.p0[1] - oy) * dy) * _IN, 4)
                  for m in wall.members if m.category == "stud")


def _on_module(stations: list[float]) -> list[float]:
    return [s for s in stations if min(s % 16.0, 16.0 - s % 16.0) < 1e-3]


def test_the_default_layout_origin_starts_the_module_at_the_wall():
    """The default is byte-for-byte the old behaviour: each segment counts from its own
    node, so W-M-0B's studs sit 10' — an exact multiple here — but measured from itself."""
    from typehaus.resolve import resolve

    model, _ = resolve(_tee_split_plan())
    for tag in ("W-M-0A", "W-M-0B"):
        wall = model.wall(tag)
        (x0, y0), (x1, y1) = wall.axis
        span = math.hypot(x1 - x0, y1 - y0)
        ux, uy = (x1 - x0) / span, (y1 - y0) / span
        local = sorted(round(((m.p0[0] - x0) * ux + (m.p0[1] - y0) * uy) * _IN, 4)
                       for m in wall.members if m.category == "stud")
        assert _on_module(local), f"{tag} did not lay out from its own station 0"


def test_a_tee_split_lays_out_as_one_module_when_the_line_is_the_origin():
    """Both segments' on-module studs land on one grid, with no doubled or missing bay
    where the two meet — which is what "the module continues across the split" means."""
    from typehaus.resolve import resolve

    model, _ = resolve(_tee_split_plan(layout_origin="line"))
    line = lines_by_wall(model.layout_lines)["W-M-0A"]
    stations = sorted({s for tag in ("W-M-0A", "W-M-0B")
                       for s in _on_module(_line_stations(line, model.wall(tag)))})
    assert len(stations) >= 8, f"almost no on-module studs: {stations}"
    gaps = {round(b - a, 3) for a, b in zip(stations, stations[1:], strict=False)}
    assert gaps <= {16.0}, f"the module broke at the tee: {sorted(gaps)}"


def _seam_stations(line, *walls, category: str = "stud") -> list[float]:
    """Every member of ``category`` on these walls, as a station on the line."""
    ox, oy = line.origin
    dx, dy = line.direction
    return sorted(round(((m.p0[0] - ox) * dx + (m.p0[1] - oy) * dy) * _IN, 4)
                  for wall in walls for m in wall.members if m.category == category)


def test_a_tee_split_frames_no_stud_at_an_off_module_seam():
    """The seam is where the *rooms* change, not where the wall does. Both halves used to
    plant an end stud on it — two sticks in the same 1-1/2", off the module, at a station
    the storey above splits somewhere else. Nothing stands there now; the module runs on."""
    from typehaus.resolve import resolve

    model, _ = resolve(_tee_split_plan(layout_origin="line"))
    line = lines_by_wall(model.layout_lines)["W-M-0A"]
    seam = 120.0  # the 10' split, 8" off the module
    stations = _seam_stations(line, model.wall("W-M-0A"), model.wall("W-M-0B"))
    assert not [s for s in stations if abs(s - seam) < 3.0], \
        f"a stud is still standing at the seam: {stations}"
    module = _on_module(stations)
    gaps = {round(b - a, 3) for a, b in zip(module, module[1:], strict=False)}
    assert gaps <= {16.0}, f"the module broke at the seam: {sorted(gaps)}"


def test_a_seam_on_the_module_is_framed_once_not_twice():
    """The one station the two halves both claim. Exactly one stud, not two stacked in the
    same place and not — the failure the first cut of this had — none at all."""
    from typehaus.resolve import resolve

    model, _ = resolve(_tee_split_plan(split_at=ft(16), layout_origin="line"))
    line = lines_by_wall(model.layout_lines)["W-M-0A"]
    seam = 192.0  # 16' — a whole number of modules from the line origin
    stations = _seam_stations(line, model.wall("W-M-0A"), model.wall("W-M-0B"))
    at_seam = [s for s in stations if abs(s - seam) < 0.75]
    assert len(at_seam) == 1, f"expected one stud on the seam, got {at_seam}"


def test_a_batten_band_runs_through_a_tee_split_too():
    """The battens are what a standing seam clips to, so a doubled pair at every seam is a
    doubled *panel line* — the defect you can see from the street, not just in the cut list.
    """
    from typehaus.resolve import resolve

    furred = Assembly(tag="EXT", layers=(
        _assembly("EXT", layout_origin="line").layers[0],
        _assembly("EXT").layers[1],
        Layer(name="batten", material_ref="spf", thickness=inch(0.75),
              function=LayerFunction.FURRING,
              framing=FramingSpec(member="1x4", direction="vertical",
                                  layout_origin="line")),
    ))
    main = Storey(uid="STMAIN00BB", tag="main", elevation=ft(0),
                  default_ceiling_height=ft(9))
    plan = _plan((main,), (furred,)).with_elements(
        "main", _rect_storey("M", ft(9), split_south=True))
    model, _ = resolve(plan)
    line = lines_by_wall(model.layout_lines)["W-M-0A"]
    battens = _seam_stations(line, model.wall("W-M-0A"), model.wall("W-M-0B"),
                             category="strapping")
    assert not [s for s in battens if abs(s - 120.0) < 3.0], \
        f"battens still double at the seam: {battens}"
    module = _on_module(battens)
    gaps = {round(b - a, 3) for a, b in zip(module, module[1:], strict=False)}
    assert gaps <= {16.0}, f"the batten module broke at the seam: {sorted(gaps)}"


def test_studs_stack_even_when_the_upper_wall_is_authored_reversed():
    """The case ``direction_sign`` exists for. Authoring the upper wall end-to-start
    reverses its own station axis; only the line can say the two grids are the same one."""
    from typehaus.resolve import resolve

    plan = _two_storey(upper={"clockwise": True}, layout_origin="line")
    model, _ = resolve(plan)
    line = lines_by_wall(model.layout_lines)["W-M-0"]
    assert line.member("W-S-0").direction_sign == -1

    below = set(_line_stations(line, model.wall("W-M-0")))
    above = _on_module(_line_stations(line, model.wall("W-S-0")))
    assert above, "the reversed wall framed no on-module stud at all"
    for station in above:
        assert any(abs(station - other) < 0.5 for other in below), \
            f"stud at {station}\" on the reversed upper wall stands over no stud below"


def test_the_battens_follow_the_studs_onto_the_line():
    """``furring._module_stations(module=True)`` exists to sit on the studs. Moving the
    studs and leaving the battens behind would be keeping that promise to nothing."""
    from typehaus.resolve import resolve

    furred = Assembly(tag="EXT", layers=(
        _assembly("EXT", layout_origin="line").layers[0],
        _assembly("EXT").layers[1],
        Layer(name="batten", material_ref="spf", thickness=inch(0.75),
              function=LayerFunction.FURRING,
              framing=FramingSpec(member="1x4", direction="vertical",
                                  layout_origin="line")),
    ))
    main = Storey(uid="STMAIN00FF", tag="main", elevation=ft(0),
                  default_ceiling_height=ft(9))
    plan = _plan((main,), (furred,)).with_elements(
        "main", _rect_storey("M", ft(9), split_south=True))
    model, _ = resolve(plan)
    line = lines_by_wall(model.layout_lines)["W-M-0B"]
    wall = model.wall("W-M-0B")
    ox, oy = line.origin
    dx, dy = line.direction
    battens = _on_module(sorted(
        round(((m.p0[0] - ox) * dx + (m.p0[1] - oy) * dy) * _IN, 4)
        for m in wall.members if m.category == "strapping"))
    studs = set(_on_module(_line_stations(line, wall)))
    assert battens, "no batten landed on the line's module"
    for station in battens:
        assert any(abs(station - s) < 0.5 for s in studs), \
            f"batten at {station}\" sits on no stud"


# --- WallPaneling.layout_line ---------------------------------------------------------------


def test_a_line_scoped_paneling_covers_every_storey_of_the_line():
    """A facade band, not a room band: one authored element, one record per member wall,
    and the band measured from the line's base rather than from each room's floor."""
    from typehaus.model.paneling import WallPaneling
    from typehaus.resolve import resolve

    plan = _two_storey()
    line = _south_line(plan)
    plan = plan.with_elements("main", (*plan.storey_elements("main"), WallPaneling(
        uid="PANEL00001", tag="WP-FACADE", layout_line=line.tag, material_ref="spf",
        offset=ft(2), height=ft(10))))

    model, findings = resolve(plan)
    assert not [f for f in findings if f.severity.value == "error"], findings
    records = {p.wall_tag: p for p in model.panelings if p.tag == "WP-FACADE"}
    assert set(records) == {"W-M-0", "W-S-0"}, "the band stopped at a storey"
    assert {p.layout_line for p in records.values()} == {line.tag}
    assert {p.room for p in records.values()} == {None}

    # 2' to 12' above the LINE's base: the lower wall carries 2'..9', the upper 9'..12',
    # and each record is stated in its own wall's frame.
    lower, upper = model.wall("W-M-0"), model.wall("W-S-0")
    assert records["W-M-0"].band_z0_m == pytest.approx(ft(2).meters)
    assert records["W-M-0"].band_z1_m == pytest.approx(lower.z1_m - lower.base_ref_z_m)
    assert records["W-S-0"].band_z0_m == pytest.approx(0.0)
    assert records["W-S-0"].band_z1_m + upper.base_ref_z_m == pytest.approx(
        line.base_z_m + ft(12).meters)


def test_a_paneling_naming_both_scopes_is_an_error():
    from typehaus.model.paneling import WallPaneling
    from typehaus.resolve import resolve

    plan = _two_storey()
    plan = plan.with_elements("main", (*plan.storey_elements("main"), WallPaneling(
        uid="PANEL00002", tag="WP-BOTH", room="RM-X", layout_line="LL-W-M-0",
        material_ref="spf")))
    _model, findings = resolve(plan)
    assert "integrity.paneling_ref" in [
        f.check_id for f in findings if f.severity.value == "error"]
