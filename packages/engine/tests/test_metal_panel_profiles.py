"""The exposed PBR and 7/8 inch corrugated wall skins follow their section drawings."""

import math
from dataclasses import replace

import pytest

from typehaus.resolve.board_batten import (
    BBD75_PROFILE,
    CORRUGATED_PROFILE,
    PBR_PROFILE,
    profile_mesh,
)
from typehaus.resolve.model import ResolvedLayer, ResolvedOpening, ResolvedWall


def panel_wall(profile):
    length = max(3 * profile.pitch_m, 1.2)
    support_y = -0.1
    inner = ResolvedLayer(
        "stud", "spf", "structure", 0.1, [(0, 0), (length, 0), (length, support_y), (0, support_y)]
    )
    skin = ResolvedLayer(
        "cladding",
        profile.key,
        "cladding",
        profile.depth_m,
        [
            (0, support_y - profile.depth_m),
            (length, support_y - profile.depth_m),
            (length, support_y),
            (0, support_y),
        ],
    )
    return ResolvedWall(
        "wall", "W-PANEL", "main", profile.key, ((0, 0), (length, 0)), (inner, skin), 0.0, 3.0
    )


def panel_mesh(wall, profile, **kwargs):
    return profile_mesh(
        wall,
        wall.layers[-1].polygon,
        0.0,
        3.0,
        ((0, 0), (1, 0)),
        layer_name="cladding",
        profile=profile,
        **kwargs,
    )


def triangle_normal(a, b, c):
    ab = [b[index] - a[index] for index in range(3)]
    ac = [c[index] - a[index] for index in range(3)]
    return (
        ab[1] * ac[2] - ab[2] * ac[1],
        ab[2] * ac[0] - ab[0] * ac[2],
        ab[0] * ac[1] - ab[1] * ac[0],
    )


@pytest.mark.parametrize(
    ("profile", "pitch", "depth"),
    [
        (BBD75_PROFILE, 12.0, 0.75),
        (PBR_PROFILE, 12.0, 1.25),
        (CORRUGATED_PROFILE, 8 / 3, 7 / 8),
    ],
)
def test_section_rhythm_and_installed_depth(profile, pitch, depth):
    xs = [point[0] for point in profile.section_points_m]
    heights = [point[1] for point in profile.section_points_m]
    assert max(xs) - min(xs) == pytest.approx(pitch * 0.0254)
    assert max(heights) == pytest.approx(depth * 0.0254)
    assert min(heights) == pytest.approx(profile.sheet_thickness_m)
    assert all(a <= b for a, b in zip(xs, xs[1:], strict=False))


@pytest.mark.parametrize("profile", [PBR_PROFILE, CORRUGATED_PROFILE])
def test_profiled_skin_is_thin_closed_mesh_with_outward_facing_surfaces(profile):
    wall = panel_wall(profile)
    mesh = panel_mesh(wall, profile)
    assert mesh.triangles
    assert min(point[1] for point in mesh.positions) == pytest.approx(-0.1 - profile.depth_m)
    assert any(normal[1] < -0.99 for normal in mesh.normals)
    assert all(math.isfinite(value) for point in mesh.positions for value in point)
    for triangle in mesh.triangles:
        a, b, c = (mesh.positions[index] for index in triangle)
        cross = triangle_normal(a, b, c)
        assert sum(value * value for value in cross) > 1e-24
        normal = mesh.normals[triangle[0]]
        assert sum(value * direction for value, direction in zip(cross, normal, strict=True)) > 0
        assert sum(value * value for value in normal) == pytest.approx(1.0)


@pytest.mark.parametrize("profile", [PBR_PROFILE, CORRUGATED_PROFILE])
def test_profile_phase_survives_reversed_axis_and_partial_wall(profile):
    wall = panel_wall(profile)
    full = panel_mesh(wall, profile)
    reversed_wall = replace(wall, axis=tuple(reversed(wall.axis)))
    assert panel_mesh(reversed_wall, profile) == full
    skin = wall.layers[-1]
    partial = replace(
        wall,
        layers=(
            *wall.layers[:-1],
            replace(
                skin,
                polygon=[
                    (0.173, skin.polygon[0][1]),
                    skin.polygon[1],
                    skin.polygon[2],
                    (0.173, skin.polygon[3][1]),
                ],
            ),
        ),
    )
    cut = panel_mesh(partial, profile)
    assert cut.triangles
    assert min(point[0] for point in cut.positions) == pytest.approx(0.173)
    assert max(point[0] for point in cut.positions) == pytest.approx(wall.axis[1][0])


@pytest.mark.parametrize("profile", [PBR_PROFILE, CORRUGATED_PROFILE])
@pytest.mark.parametrize("arch_rise", [0.0, 0.25])
def test_rectangular_and_arched_openings_cut_the_folded_skin(profile, arch_rise):
    wall = panel_wall(profile)
    opening = ResolvedOpening(
        "op", "O", wall.tag, None, 0.5, 1.0, 0.8, 0.61, "window", False, arch_rise_m=arch_rise
    )
    mesh = panel_mesh(wall, profile, openings=[opening])
    centers = [
        tuple(sum(mesh.positions[index][axis] for index in triangle) / 3 for axis in range(3))
        for triangle in mesh.triangles
    ]
    upper_jamb = 1.549 if arch_rise else 1.799
    assert not any(0.361 < x < 0.859 and 0.801 < z < upper_jamb for x, _, z in centers)
    if arch_rise:
        assert not any(0.59 < x < 0.63 and 1.601 < z < 1.799
                       for x, _, z in centers)
        assert any(0.361 < x < 0.43 and 1.56 < z < 1.76
                   for x, _, z in centers)
    assert any(z > 1.801 for _, _, z in centers)


def test_pbr_has_major_rib_and_two_minor_ribs_per_12_in_module():
    section = PBR_PROFILE.section_points_m
    high = max(height for _, height in section)
    major_crown_x = [x for x, height in section if height == high]
    assert max(major_crown_x) - min(major_crown_x) == pytest.approx(1.0 * 0.0254)
    minor_height = 0.00060706 + 0.25 * 0.0254
    minor_crown_x = [x for x, height in section if height == pytest.approx(minor_height)]
    assert len(minor_crown_x) == 4
    assert (minor_crown_x[2] - minor_crown_x[0]) == pytest.approx(8 * 0.0254)


def test_corrugated_section_is_a_sampled_sine_with_exact_wall_pitch():
    section = CORRUGATED_PROFILE.section_points_m
    assert len(section) == 25
    assert section[0][1] == pytest.approx(section[-1][1])
    assert section[12][1] == pytest.approx(CORRUGATED_PROFILE.depth_m)
    assert section[6][1] == pytest.approx(
        (CORRUGATED_PROFILE.depth_m + CORRUGATED_PROFILE.sheet_thickness_m) / 2,
    )


@pytest.mark.parametrize("profile", [BBD75_PROFILE, PBR_PROFILE, CORRUGATED_PROFILE])
def test_seated_folds_clear_concealed_laps_and_keep_the_nominal_crown(profile):
    wall = panel_wall(profile)
    clearance = 0.0013208  # .032 inch metal plus .020 inch strip-in membrane
    mesh = panel_mesh(wall, profile, support_clearance_m=clearance)
    assert min(y for _, y, _ in mesh.positions) == pytest.approx(-0.1 - profile.depth_m)
    # A curved valley's miter can leave its rear face slightly farther out than the seat.
    assert max(y for _, y, _ in mesh.positions) <= -0.1 - clearance + 1e-9
    assert max(y for _, y, _ in mesh.positions) > -0.1 - clearance - profile.sheet_thickness_m
    front = [y for (_, y, _), n in zip(mesh.positions, mesh.normals, strict=True) if n[1] < 0]
    assert max(front) == pytest.approx(-0.1 - clearance - profile.sheet_thickness_m)


def test_concealed_lap_cannot_consume_the_entire_profile_depth():
    profile = CORRUGATED_PROFILE
    with pytest.raises(ValueError, match="concealed flashing exceeds"):
        panel_mesh(panel_wall(profile), profile, support_clearance_m=profile.depth_m)
