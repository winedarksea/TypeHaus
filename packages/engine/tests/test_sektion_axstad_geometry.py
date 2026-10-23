"""Product dimensions, visible relief and front operating configurations."""

import math

import pytest

from typehaus.model.placeable_symbols import model_parts
from typehaus.model.placeable_symbols._sektion_fronts import (
    axstad_front,
    bagganas_knob,
    bagganas_pull,
)

INCH = 0.0254
PREFIX = "sektion-axstad-kitchen-"


def _bounds(parts, axis):
    return (
        min(p["center"][axis] - p["size"][axis] / 2 for p in parts),
        max(p["center"][axis] + p["size"][axis] / 2 for p in parts),
    )


def test_bagganas_published_dimensions_and_round_stock():
    knob = bagganas_knob(0, 0, 0)
    assert _bounds(knob, 0) == pytest.approx((-13 / 32 * INCH, 13 / 32 * INCH))
    assert _bounds(knob, 1) == pytest.approx((-15 / 16 * INCH, 0))
    pull = bagganas_pull(0, 0, 0)
    assert _bounds(pull, 0) == pytest.approx((-5.625 / 2 * INCH, 5.625 / 2 * INCH))
    assert _bounds(pull, 1) == pytest.approx((-1.25 * INCH, 0))
    washers = [p for p in pull if p["size"][1] == pytest.approx(INCH / 16)]
    assert len(washers) == 2
    assert washers[1]["center"][0] - washers[0]["center"][0] == pytest.approx(5.0625 * INCH)
    assert all(p["shape"] == "mesh" and p["color"] == "metal-black" for p in knob + pull)


def test_axstad_has_stock_envelope_softened_profile_and_closed_outward_faces():
    front = axstad_front(14.875 * INCH, 0, 0.75 * INCH, 0, 29.875 * INCH)[0]
    assert front["size"] == pytest.approx((14.875 * INCH, 0.75 * INCH, 29.875 * INCH))
    vertices = front["mesh"]["positions"]
    panel_points = [
        p
        for p in vertices
        if abs(p[0]) <= 5.4375 * INCH + 1e-9 and 2 * INCH - 1e-9 <= p[2] <= 27.875 * INCH + 1e-9
    ]
    assert min(p[1] for p in panel_points) == pytest.approx(0.25 * INCH)
    assert len({round(p[1], 8) for p in vertices}) >= 6
    # A closed solid with consistent winding has positive signed volume.
    volume = 0.0
    for a, b, c in front["mesh"]["triangles"]:
        p, q, r = vertices[a], vertices[b], vertices[c]
        volume += (
            p[0] * (q[1] * r[2] - q[2] * r[1])
            + p[1] * (q[2] * r[0] - q[0] * r[2])
            + p[2] * (q[0] * r[1] - q[1] * r[0])
        ) / 6
    assert volume > 0


@pytest.mark.parametrize(
    ("symbol", "width", "height", "count"),
    [
        ("base-door", 12, 36, 1),
        ("sink", 36, 36, 2),
        ("drawers", 24, 36, 3),
        ("wall", 24, 30, 1),
        ("wall", 30, 20, 2),
        ("tall", 18, 83.5, 2),
        ("lift", 24, 15, 1),
    ],
)
def test_configured_stock_front_sizes_and_actual_projection(symbol, width, height, count):
    parts = model_parts(PREFIX + symbol, width * INCH, 24 * INCH, height * INCH)
    fronts = [p for p in parts if p["color"] == "appliance-white" and p["shape"] == "mesh"]
    assert len(fronts) == count
    assert _bounds(fronts, 1) == pytest.approx((-12.75 * INCH, -12 * INCH))
    if symbol == "drawers":
        assert [p["size"][2] / INCH for p in fronts] == pytest.approx([9.875] * 3)
        assert [p["center"][2] / INCH for p in fronts] == pytest.approx([8.5, 18.5, 28.5])
    elif symbol == "tall":
        assert [p["size"][2] / INCH for p in fronts] == pytest.approx([49.875, 29.875])
    elif symbol == "wall" and width == 30:
        assert [p["size"][0] / INCH for p in fronts] == pytest.approx([14.875, 14.875])


def test_handing_moves_knob_to_opening_edge_and_wall_knobs_are_low():
    def hardware(symbol):
        return [
            p
            for p in model_parts(PREFIX + symbol, 24 * INCH, 24 * INCH, 36 * INCH)
            if p["color"] == "metal-black"
        ]

    assert all(p["center"][0] > 0 for p in hardware("base-door"))
    assert all(p["center"][0] < 0 for p in hardware("base-door-right"))
    assert all(p["center"][2] < 3 * INCH for p in hardware("wall"))


def test_corner_leaf_orientations_and_single_bifold_knob():
    parts = model_parts(PREFIX + "corner-base", 38 * INCH, 38 * INCH, 36 * INCH)
    faces = [p for p in parts if p["shape"] == "mesh" and p["color"] == "appliance-white"]
    assert len(faces) == 2
    assert faces[0]["size"][1] == pytest.approx(0.75 * INCH)
    assert faces[1]["size"][0] == pytest.approx(0.75 * INCH)
    assert len([p for p in parts if p["color"] == "metal-black"]) == 2  # head + stem
    diagonal = model_parts(PREFIX + "corner-wall", 26 * INCH, 26 * INCH, 30 * INCH)
    face = next(p for p in diagonal if p["shape"] == "mesh" and p["color"] == "appliance-white")
    assert face["size"][0] == pytest.approx(face["size"][1])
    assert all(math.isfinite(v) for p in diagonal for v in (*p["center"], *p["size"]))
