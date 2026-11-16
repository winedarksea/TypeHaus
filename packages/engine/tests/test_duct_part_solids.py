"""Every derived duct part and hanger is one drawn, closed product solid (decision #114)."""

from __future__ import annotations

import pytest

m3d = pytest.importorskip("manifold3d")

from typehaus.resolve.duct_part_solids import neck_drawn, parse_section  # noqa: E402
from typehaus.resolve.solid_categories import solid_category  # noqa: E402
from typehaus.solids3d.convert import mesh_manifold  # noqa: E402

_CATEGORIES = ("duct_fitting", "duct_damper", "duct_connector", "duct_support")


def test_sections_parse_as_ordered():
    assert parse_section("4in").is_round
    rect = parse_section("18x8")
    assert (round(rect.width / 0.0254), round(rect.depth / 0.0254)) == (18, 8)
    assert parse_section("none") is None and parse_section(None) is None


def test_one_closed_solid_per_non_integral_part_and_hanger(catlin_model_ro):
    model = catlin_model_ro
    drawn = [s for s in model.solids if s.category in _CATEGORIES]
    necked = neck_drawn(model)
    parts = [p for p in model.duct_parts if not p.integral
             and not (p.kind == "boot" and p.other in necked)]
    expected = len(parts) + len(model.duct_supports)
    assert expected and len(drawn) == expected
    assert all(s.derived and s.body_mesh is not None and s.host_ref for s in drawn)
    assert len({s.uid for s in drawn}) == len(drawn)
    assert {solid_category(c).collision for c in _CATEGORIES} == {None}
    bad = []
    for solid in drawn:
        manifold = mesh_manifold(solid.body_mesh.positions, solid.body_mesh.triangles)
        if manifold.status() != m3d.Error.NoError or manifold.volume() <= 0:
            bad.append(solid.tag)
    assert not bad, bad[:10]
    named = {p.product_ref for p in parts if p.product_ref}
    assert named <= {s.product for s in drawn}


def test_turned_reducer_is_the_small_runs_stub_not_drawn_back_over_the_big_run():
    from types import SimpleNamespace as NS

    from typehaus.resolve.duct_part_solids import _part_mesh
    from typehaus.resolve.model_ducts import ResolvedDuctPart

    i = 0.0254

    def run(tag, path, w, d):
        return NS(tag=tag, path=[(x * i, y * i) for x, y in path], z_m=[0.0] * len(path),
                  width_m=w * i, depth_m=d * i, diameter_m=None)

    trunk, leg = run("T", [(0, 100), (0, 0)], 8, 4), run("L", [(0, 0), (30, 0)], 3.25, 8)
    part = ResolvedDuctPart(kind="reducer", run_tag="T", storey="s", size="8x4", branch="3.25x8",
                            point=(0.0, 0.0, 0.0), axis=(0.0, 1.0, 0.0), other="L")
    xs, ys, _ = zip(*_part_mesh(NS(ducts=[trunk, leg]), part, []).positions, strict=True)
    assert min(xs) >= -1e-9 and max(ys) <= 3.25 / 2 * i + 1e-9 and min(ys) >= -3.25 / 2 * i - 1e-9


def test_offset_reducer_joins_and_is_flat_bottomed():
    """An 18x8 cap into a 10x6 8" west and 18" on, bottoms flush: one joint, one flat loft."""
    from types import SimpleNamespace as NS

    from typehaus.resolve.duct_part_solids import _part_mesh
    from typehaus.resolve.mep_soffit import eccentric_end_joint
    from typehaus.resolve.model_ducts import ResolvedDuctPart

    i = 0.0254

    def run(tag, path, w, d, z):
        return NS(tag=tag, path=[(x * i, y * i) for x, y in path], z_m=[z * i] * len(path),
                  width_m=w * i, depth_m=d * i, diameter_m=None)

    trunk = run("T", [(0, 100), (0, 18)], 18, 8, 4)
    branch = run("S", [(-8, 0), (-8, -80)], 10, 6, 3)
    assert eccentric_end_joint(branch, branch.path[0], branch.z_m[0], trunk)
    assert eccentric_end_joint(trunk, trunk.path[-1], trunk.z_m[-1], branch)
    part = ResolvedDuctPart(kind="reducer", run_tag="T", storey="s", size="18x8",
                            branch="10x6", point=(-8 * i, 0.0, 3 * i), axis=(0.0, -1.0, 0.0),
                            other="S", length_m=18 * i)
    xs, ys, zs = zip(*_part_mesh(NS(ducts=[trunk, branch]), part, []).positions, strict=True)
    assert min(zs) == pytest.approx(0.0, abs=1e-9)  # flush with both bottoms
    assert (min(ys), max(ys)) == pytest.approx((0.0, 18 * i))  # fills the gap, no more
    assert (min(xs), max(xs)) == pytest.approx((-13 * i, 9 * i))


def test_a_separate_boot_neck_draws_its_boot_to_the_neck_back(catlin_model_ro):
    from shapely.geometry import Polygon

    model = catlin_model_ro
    necks = {s.host_ref: s for s in model.solids if s.category == "terminal_neck"}
    for run, register in (("DU-S-HP-STUDY2", "REG-S-HP-STUDY2"),
                          ("DU-S-HP-STUDY2-S", "REG-S-HP-STUDY2-S"),
                          ("DU-S-HP-STUDY-BOOT", "REG-A-HP-STUDY")):
        boot = next(s for s in model.solids if s.tag == f"{run}-BOOT-1")
        neck = necks[register]
        # Touches the neck's back face and does not overlap the damper box.
        a, b = Polygon(boot.outline), Polygon(neck.outline)
        overlap_z = min(boot.z1_m, neck.z1_m) - max(boot.z0_m, neck.z0_m)
        assert a.distance(b) < 1e-6
        assert a.intersection(b).area < 1e-6 or overlap_z < 1e-6, run


def test_a_collar_past_its_mains_end_or_over_a_sibling_fails():
    from types import SimpleNamespace as NS

    from typehaus.checks.mep.takeoff_collars import takeoff_collar_fit
    from typehaus.resolve.model_ducts import ResolvedDuctPart

    i = 0.0254
    main = NS(tag="M", path=[(0.0, 0.0), (0.0, 40 * i)], z_m=[0.0, 0.0],
              width_m=10 * i, depth_m=6 * i, diameter_m=None)

    def collar(other, y):
        return ResolvedDuctPart(kind="takeoff", run_tag="M", storey="s", size="10x6",
                                branch="6in", point=(0.0, y * i, 0.0), axis=(1.0, 0.0, 0.0),
                                other=other)

    def results(*parts):
        ctx = NS(model=NS(ducts=[main], duct_parts=list(parts)))
        return [f.result.value for f in takeoff_collar_fit(ctx)]

    assert results(collar("A", 20)) == ["pass"]
    assert results(collar("A", 2)) == ["fail"]  # 3" + 1/2" flange past the end
    assert results(collar("A", 20), collar("B", 26.25)) == ["fail"]  # 6 1/4" c-c
