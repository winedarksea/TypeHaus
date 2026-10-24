"""The bonded bowl remains visible through the deck and above the floating cabinet."""

import pytest
from shapely.geometry import Point, Polygon

from typehaus.model.placeable_symbols import model_parts


def test_bonded_bowl_has_an_open_deck_and_curved_five_inch_recess():
    inch = 0.0254
    parts = model_parts("solid-surface-vanity", 48 * inch, 18 * inch, 41.5 * inch)
    deck = 41.5 * inch - 0.14
    basin_y = -1.125 * inch
    shell = next(part for part in parts if part["shape"] == "mesh")
    vertices = shell["mesh"]["positions"]
    assert max(p[2] for p in vertices) == pytest.approx(deck)
    assert min(p[2] for p in vertices) == pytest.approx(deck - 5 * inch, abs=0.0002)
    assert len({round(p[2], 5) for p in vertices}) > 10
    assert {part["color"] for part in parts} == {"porcelain", "appliance-white", "metal", "faucet"}
    for part in parts:
        if part["shape"] != "box":
            continue
        (x, y, z), (w, d, h) = part["center"], part["size"]
        if z + h / 2 >= deck - 1e-9 and z - h / 2 < deck:
            outline = Polygon(((x-w/2, y-d/2), (x+w/2, y-d/2),
                               (x+w/2, y+d/2), (x-w/2, y+d/2)))
            assert not outline.contains(Point(0, basin_y))
    cabinet = [part for part in parts if part["color"] == "appliance-white"]
    assert min(p["center"][2] - p["size"][2] / 2 for p in cabinet) == pytest.approx(
        5.5 * inch, abs=0.0002)


@pytest.mark.parametrize("symbol,width", [("sektion-vanity", 24), ("sektion-vanity", 30),
                                          ("drawer-vanity", 37)])
def test_selected_vanities_keep_a_useful_bowl_and_separate_faucet_material(symbol, width):
    parts = model_parts(symbol, width * .0254, 18 * .0254, 41.5 * .0254,
                        material_refs={"faucet": "faucet-brushed-nickel"})
    bowl = next(part for part in parts if part["shape"] == "mesh")
    xs = [point[0] for point in bowl["mesh"]["positions"]]
    assert max(xs) - min(xs) == pytest.approx(16.375 * .0254)
    assert all(part.get("material_ref") == "faucet-brushed-nickel"
               for part in parts if part["color"] == "faucet")
    assert all("material_ref" not in part for part in parts if part["color"] != "faucet")


def test_two_bowls_have_independent_full_size_mouths():
    from typehaus.model.placeable_symbols._solid_surface_vanity import solid_surface_vanity

    _, parts = solid_surface_vanity(60 * .0254, 18 * .0254, 41.5 * .0254,
                                    fronts=(.5, .5), bowl_count=2)
    bowls = [part for part in parts if part["shape"] == "mesh" and part["color"] == "porcelain"]
    assert len(bowls) == 2
    centers = []
    for bowl in bowls:
        xs = [v[0] for v in bowl["mesh"]["positions"]]
        assert max(xs) - min(xs) == pytest.approx(16.375 * .0254)
        centers.append((max(xs) + min(xs)) / 2)
    assert centers[1] - centers[0] == pytest.approx(30 * .0254)


def test_genta_fits_between_bowl_mouth_and_wall():
    parts = model_parts("solid-surface-vanity", 48*.0254, 18*.0254, 41.5*.0254)
    bowl = next(part for part in parts if part["shape"] == "mesh" and part["color"] == "porcelain")
    rear_lip = max(p[1] for p in bowl["mesh"]["positions"])
    shaft = max((part for part in parts if part["color"] == "faucet"),
                key=lambda part: part["size"][2])
    center_y = shaft["center"][1]
    assert 9*.0254 - center_y >= 2.5*.0254 - 1e-9
    assert center_y - rear_lip >= 1.125*.0254 - 1e-9
