"""The sheathing sheet layout (decision #146): a synthetic wall, the check, and catlin's oracle."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from typehaus.checks.code.mn_residential.profile import MN_2020
from typehaus.checks.registry import CheckContext, Preferences
from typehaus.checks.structural.sheathing_edge_support import _grade, sheathing_edge_support
from typehaus.findings import Result
from typehaus.resolve.sheet_layout import lay_run, layout_params
from typehaus.resolve.sheet_layout_runs import Face, build_runs

IN = 0.0254


def _stud(s_in, z0_in, z1_in, key):
    p = (s_in * IN, 2.75 * IN)
    return SimpleNamespace(p0=p, p1=p, z0_m=z0_in * IN, z1_m=z1_in * IN, profile="2x6",
                           orient=(1.0, 0.0), child_key=key, category="stud",
                           plan_width_m=None, z0_end_m=None, z1_end_m=None)


def _flat(s0_in, s1_in, z0_in, z1_in, key):
    return SimpleNamespace(p0=(s0_in * IN, 2.75 * IN), p1=(s1_in * IN, 2.75 * IN), z0_m=z0_in * IN,
                           z1_m=z1_in * IN, profile="2x6", orient=None, child_key=key,
                           category="plate", plan_width_m=None, z0_end_m=None, z1_end_m=None)


def _wall(length_in, studs_in, band_in=108.0, blocks_in=(), openings=()):
    """A wall along +x, sheathing on its -y face (y -0.5" to 0), studs y 0 to 5.5"."""
    top = band_in
    members = [_stud(s, 1.5, top - 3.0, f"stud-{i:03d}") for i, s in enumerate(studs_in)]
    members += [_flat(0, length_in, 0, 1.5, "plate-bottom"),
                _flat(0, length_in, top - 3.0, top - 1.5, "plate-top-1"),
                _flat(0, length_in, top - 1.5, top, "plate-top-0")]
    members += [_flat(0, length_in, z - 0.75, z + 0.75, f"block-{i}")
                for i, z in enumerate(blocks_in)]
    L = length_in * IN
    sheathing = SimpleNamespace(name="sheathing", material_ref="ply", thickness_m=0.5 * IN,
                                polygon=((0, -0.5 * IN), (L, -0.5 * IN), (L, 0), (0, 0)),
                                run_span_m=None, function="sheathing", is_cavity=False)
    stud_layer = SimpleNamespace(polygon=((0, 0), (L, 0), (L, 5.5 * IN), (0, 5.5 * IN)),
                                 thickness_m=5.5 * IN, function="structure", is_cavity=False)
    wall = SimpleNamespace(tag="W-T", axis=((0.0, 0.0), (L, 0.0)), members=members,
                           layers=(stud_layer, sheathing), base_ref_z_m=0.0, z0_m=0.0,
                           z1_m=top * IN, top_z0_m=None, top_z1_m=None, head_caps=())
    model = SimpleNamespace(floors=[], solids=[], junctions=[], openings=list(openings),
                            walls=[wall], wall=lambda tag: wall)
    face = Face(wall, sheathing, stud_layer, 96 * IN, 0.0, top * IN)
    return model, wall, face


def _lay(model, face, **overrides):
    params = layout_params(None)
    for key, value in overrides.items():
        setattr(params, key, value)
    run = build_runs([face])[0]
    return lay_run(model, run, params)


def _opening(tag, centre_in, width_in, sill_in, height_in):
    return SimpleNamespace(tag=tag, host_wall="W-T", center_along_m=centre_in * IN,
                           width_m=width_in * IN, sill_m=sill_in * IN, height_m=height_in * IN,
                           depth_m=None)


def test_breaks_snap_back_to_a_stud_and_an_opening_cuts_its_piece():
    studs = [0.75, 8, 24, 40, 56, 72, 88, 99.25]  # 16" o.c. off an 8" layout origin
    window = _opening("WIN", 64.0, 24.0, 30.0, 40.0)
    model, _wall_, face = _wall(100, studs, band_in=96, openings=[window])
    layout = _lay(model, face)
    assert [round(b.at / IN, 3) for b in layout.vertical_breaks] == [40.0, 88.0]
    assert all(b.backed for b in layout.vertical_breaks)
    kinds = [(round(p.s0 / IN), p.kind, p.opening_cuts) for p in layout.pieces]
    assert kinds == [(0, "rip", ()), (40, "cut", ("WIN",)), (88, "rip", ())]


def test_a_short_last_piece_pulls_the_previous_break_back():
    studs = [0.75, 8, 24, 40, 56, 72, 88, 91.25]
    model, _w, face = _wall(92, studs, band_in=96)
    layout = _lay(model, face)
    # 40 then 88 would leave a 4" sliver: the second break comes back to 72.
    assert [round(b.at / IN) for b in layout.vertical_breaks] == [40, 72]


def test_courses_alternate_their_anchor_so_horizontal_joints_stagger():
    studs = [0.75, 16, 32, 48, 64, 80, 95.25]
    model, _w, face = _wall(96, studs, band_in=108, blocks_in=(12.0, 96.0))
    layout = _lay(model, face)
    joints = [round(b.at / IN, 2) for b in layout.horizontal_breaks]
    assert joints == [96.0, 12.0]
    assert all(b.backed for b in layout.horizontal_breaks)


def test_a_joint_off_framing_fails_the_check():
    model, _w, face = _wall(120, [0.75, 60, 119.25], band_in=96)  # studs 60" apart
    layout = _lay(model, face)
    assert not all(b.backed for b in layout.vertical_breaks)
    finding = _grade(model, layout, "")
    assert finding.result is Result.FAIL and "off framing" in finding.message


def test_catlin_garage_south_matches_the_oracle(catlin_model_ro):
    """houses/catlin/notes/sheet_layout_oracle.md, worked by hand."""
    layout = next(lay for lay in catlin_model_ro.sheet_layouts if lay.wall_tag == "W-G-S")
    assert layout.start_end == "start" and layout.hi / IN == pytest.approx(287.5625, abs=1e-3)
    assert [round(b.at / IN, 2) for b in layout.vertical_breaks] == [
        46.75, 72.0, 120.0, 168.0, 216.0, 264.0]
    assert not layout.horizontal_breaks and all(b.backed for b in layout.vertical_breaks)
    assert [p.kind for p in layout.pieces] == ["cut", "rip", "full", "full", "full", "full",
                                               "rip"]
    assert layout.pieces[0].opening_cuts == ("D-G-SERVICE",)
    from typehaus.takeoff.sheet_goods import layout_standard, pack_layouts

    assert pack_layouts([layout], layout_standard(catlin_model_ro.plan)).sheets == 7


def test_the_wall_below_backs_the_sheathing_over_the_floor_band(catlin_model_ro):
    """W-M-S1/S2 stand over the framed court walls W-B-S2-FR/S3-FR (x 118..314): their double
    top plate, now landed on the joists (z -13 3/8"..-11 7/8"), backs the five vertical joints
    that were bare for 1 9/16" there. Without the plate the band is air (review D §2.2)."""
    plan_tops = {w.tag: w.z1_m for w in catlin_model_ro.walls if w.tag.endswith("-FR")}
    assert plan_tops["W-B-S2-FR"] == pytest.approx(plan_tops["W-B-S3-FR"])
    assert plan_tops["W-B-S2-FR"] == pytest.approx(-11.875 * 0.0254, abs=1e-4)
    lay = next(lay for lay in catlin_model_ro.sheet_layouts if "W-M-S2" in lay.wall_tags)
    court = [b for b in lay.vertical_breaks if 118 * 0.0254 < b.at < 314 * 0.0254]
    assert court and all(b.backed for b in court)


def test_an_unstated_sheet_length_is_unknown(catlin_model_ro, monkeypatch):
    """Catlin states every sheet_length and grades clean; unstate one and it is UNKNOWN."""
    import typehaus.checks.structural.sheathing_edge_support as module

    ctx = CheckContext(plan=catlin_model_ro.plan, model=catlin_model_ro,
                       preferences=Preferences(), profile=MN_2020)
    findings = sheathing_edge_support(ctx)
    assert not [f for f in findings if f.result is Result.FAIL or "sheet_length" in f.message]
    real = module.wall_sheathing
    monkeypatch.setattr(module, "wall_sheathing", lambda plan, wall: [
        (name, None if wall.tag == "W-B-S2-FR" else length)
        for name, length in real(plan, wall)])
    assert any(f.result is Result.UNKNOWN and "W-B-S2-FR" in f.element_tags
               and "sheet_length" in f.message for f in sheathing_edge_support(ctx))


def _clad_wall(length_in, band_in, courses_in, nailers):
    """A cladding over flat horizontal girts (y 0 to 1.5", courses ``courses_in`` up)."""
    from typehaus.resolve.sheet_layout_nailers import NailerSpec

    L = length_in * IN
    girts = [SimpleNamespace(p0=(0.0, 0.75 * IN), p1=(L, 0.75 * IN), z0_m=z * IN,
                             z1_m=(z + 3.5) * IN, profile="2x4", orient=None,
                             child_key=f"strapping-girt-{i:03d}", category="strapping",
                             plan_width_m=None, z0_end_m=None, z1_end_m=None)
             for i, z in enumerate(courses_in)]
    clad = SimpleNamespace(name="cladding", material_ref="panel", thickness_m=0.375 * IN,
                           polygon=((0, -0.375 * IN), (L, -0.375 * IN), (L, 0), (0, 0)),
                           run_span_m=None, function="cladding", is_cavity=False)
    girt = SimpleNamespace(name="girt", polygon=((0, 0), (L, 0), (L, 1.5 * IN), (0, 1.5 * IN)),
                           thickness_m=1.5 * IN, function="furring", is_cavity=False)
    wall = SimpleNamespace(tag="W-T", uid="W-T-UID", axis=((0.0, 0.0), (L, 0.0)),
                           members=girts, layers=(girt, clad), base_ref_z_m=0.0, z0_m=0.0,
                           z1_m=band_in * IN, top_z0_m=None, top_z1_m=None, head_caps=())
    model = SimpleNamespace(floors=[], solids=[], junctions=[], openings=[], walls=[wall],
                            wall=lambda tag: wall)
    spec = NailerSpec("girt", "2x4", "kdat", 3.5 * IN, 1.5 * IN) if nailers else None
    return model, Face(wall, clad, girt, 96 * IN, 0.0, band_in * IN, nailer=spec)


def test_panel_cladding_on_girts_takes_a_nailer_at_each_joint_or_fails():
    model, face = _clad_wall(100, 90, (2.0, 26.0, 50.0, 74.0), nailers=True)
    found: dict[str, list] = {}
    layout = lay_run(model, build_runs([face])[0], layout_params(None), found)
    # The bare module from the start, the 4" tail pulling the second joint back to 88.
    assert [round(b.at / IN, 3) for b in layout.vertical_breaks] == [48.0, 88.0]
    assert all(b.backed for b in layout.vertical_breaks)
    # Five pieces a joint: under the first course, three bays, over the top one.
    spans = [(round(m.z0_m / IN, 2), round(m.z1_m / IN, 2)) for m in found["W-T"][:5]]
    assert spans == [(0.0, 2.0), (5.5, 26.0), (29.5, 50.0), (53.5, 74.0), (77.5, 90.0)]
    assert _grade(model, layout, "").result is Result.PASS
    model, face = _clad_wall(100, 90, (2.0, 26.0, 50.0, 74.0), nailers=False)
    bare = _lay(model, face)
    finding = _grade(model, bare, "")
    assert finding.result is Result.FAIL and "R703" in str(finding.code_ref)


def test_catlin_court_face_matches_the_lp_panel_oracle(catlin_model_ro):
    """houses/catlin/notes/court_face_lp_panel.md, "Sheet layout and joint battens"."""
    from typehaus.takeoff.cladding_trim import cladding_trim_takeoff
    from typehaus.takeoff.sheet_goods import sheet_goods_takeoff

    lay = next(lay for lay in catlin_model_ro.sheet_layouts if lay.function == "cladding")
    assert lay.wall_tags == ("W-B-S2-FR", "W-B-S3-FR") and not lay.horizontal_breaks
    # Centred (centre_cladding): 26" end columns, no joint through WIN-B-SAUNA.
    assert lay.start_end == "centre"
    assert [round(b.at / IN, 2) for b in lay.vertical_breaks] == [26.0, 74.0, 122.0, 170.0]
    # Backed by girts and nailers, bar the 1.22" panel foot under the lifted starter course;
    # s 170 sits on D-B-SUNKEN's jamb post from the wall base.
    assert [round(b.unbacked_m / IN, 2) for b in lay.vertical_breaks] == [1.22, 1.22, 0.0, 0.0]
    assert _grade(catlin_model_ro, lay, "").result is Result.UNKNOWN
    assert len(lay.nailers) == 10
    assert sum(m.length_m for m in lay.nailers) / IN == pytest.approx(145.5, abs=0.01)
    row = next(r for r in sheet_goods_takeoff(catlin_model_ro) if r["scope"] == "cladding panel")
    assert (row["sheets"], row["net_area_sqft"]) == (5, 81.8)
    battens = next(r for r in cladding_trim_takeoff(catlin_model_ro)
                   if r["part"] == "LP_440_BATTEN_3_5")
    # s 26 and 74 full height; the door's trim takes s 122 (head) and s 170 (casing).
    assert len(battens["tags"]) == 2 and battens["count"] == 1
    assert battens["length_ft"] == pytest.approx(2 * 87.718 / 12, abs=0.01)


def test_centred_walk_keeps_equal_end_columns_over_the_rip():
    from typehaus.resolve.sheet_layout_walk import walk_centred

    def lay(length):
        return walk_centred(0.0, length, 48.0, [], 0.4375, lambda _x: 0.0, 12.0, 0.125)

    assert lay(196.0) == [26.0, 74.0, 122.0, 170.0]  # 2" ends under the rip: a module wider
    assert lay(216.0) == [12.0, 60.0, 108.0, 156.0, 204.0]  # 12" ends are a rip
    assert lay(192.0) == [48.0, 96.0, 144.0] and lay(40.0) == []
