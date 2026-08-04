"""Masonry appearance + cladding orientation (B5).

Two regressions are locked here:

* a material's authored appearance (``Material.color`` / ``Material.finish``) survives into
  ``model.json`` and into the glTF export, so white brick renders white instead of falling
  through to the masonry family's red; and
* a clad wall authored end-to-start builds its layer stack inside out, and
  ``advisory.cladding_side_mismatch`` says so.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from typehaus.checks import run
from typehaus.model import (
    Assembly,
    FoundationWall,
    Layer,
    LayerFunction,
    Library,
    Material,
    Node,
    PlanModel,
    Storey,
    ft,
    inch,
    pt,
)
from typehaus.resolve import resolve
from typehaus.source import load_plan

CATLIN = Path(__file__).resolve().parents[3] / "houses" / "catlin"

# The porch railing's brick wythe must land on the outboard face of each of the three walls:
# the front wall faces the garden (south, -y) and the side walls face away from the porch
# (west / east). Compared against the wall's own interior finish so the test is independent
# of where the porch happens to sit in plan.
_RAILING_OUTBOARD = {
    "W-SG-RAIL-F": (0.0, -1.0),
    "W-SG-RAIL-W": (-1.0, 0.0),
    "W-SG-RAIL-E": (1.0, 0.0),
}


def _centroid(polygon):
    return (sum(p[0] for p in polygon) / len(polygon),
            sum(p[1] for p in polygon) / len(polygon))


@pytest.mark.parametrize("wall_tag", sorted(_RAILING_OUTBOARD))
def test_porch_railing_brick_faces_outboard(catlin_model, wall_tag) -> None:
    wall = catlin_model.wall(wall_tag)
    assert wall is not None, f"{wall_tag} missing from the resolved model"
    layers = wall.depth_layers()
    brick = next(ly for ly in layers if ly.function == "cladding")
    assert brick.material_ref == "white-brick"
    inner, outer = _centroid(layers[0].polygon), _centroid(brick.polygon)
    direction = _RAILING_OUTBOARD[wall_tag]
    outboard = ((outer[0] - inner[0]) * direction[0] + (outer[1] - inner[1]) * direction[1])
    assert outboard > 0.0, (
        f"{wall_tag}: brick sits on the porch side, not the exterior "
        f"(interior {inner} -> cladding {outer})"
    )


def test_catlin_has_no_cladding_side_mismatch() -> None:
    report = run(load_plan(CATLIN).plan)
    mismatches = [f for f in report.findings
                  if f.check_id == "advisory.cladding_side_mismatch"]
    assert not mismatches, [f.message for f in mismatches]


def test_white_brick_material_ships_its_appearance() -> None:
    from typehaus.server.model_json import model_to_dict

    model, _ = resolve(load_plan(CATLIN).plan)
    materials = {m["tag"]: m for m in model_to_dict(model)["catalog"]["materials"]}
    assert materials["white-brick"]["finish"] == "white-brick"
    assert materials["white-brick"]["color"] == "#e9e6df"
    # The red default still reads red, so the finish is a real distinction, not a rename.
    assert materials["brick"]["color"] != materials["white-brick"]["color"]


def test_gltf_colors_white_brick_whitewashed() -> None:
    from typehaus.emit.draw.palette import material_family_color
    from typehaus.emit.gltf.emitter import _hex_rgba, _material_finish_color

    white = _material_finish_color("white-brick", "cladding")
    assert white == _hex_rgba("#e9e6df")
    assert white != _hex_rgba(material_family_color("brick")), "white brick must not read red"
    assert _material_finish_color("brick", "cladding") == _hex_rgba(
        material_family_color("brick"))


def test_glazed_green_brick_material_ships_its_appearance() -> None:
    """The basement's south veneer (2026-08-03) — same pattern as the white brick above.

    A third brick had to be distinguishable from the other two or the sunken garden's most
    visible wall would render as the masonry family's red, which is the porch's brick, not
    this one.
    """
    from typehaus.server.model_json import model_to_dict

    model, _ = resolve(load_plan(CATLIN).plan)
    materials = {m["tag"]: m for m in model_to_dict(model)["catalog"]["materials"]}
    assert materials["glazed-green-brick"]["finish"] == "glazed-green-brick"
    assert materials["glazed-green-brick"]["color"] == "#1b4332"
    # Three bricks, three colours: the finish is a real distinction on both counts.
    assert len({materials[tag]["color"]
                for tag in ("brick", "white-brick", "glazed-green-brick")}) == 3


def test_gltf_colors_glazed_green_brick_green() -> None:
    from typehaus.emit.draw.palette import material_family_color
    from typehaus.emit.gltf.emitter import _hex_rgba, _material_finish_color

    # STRUCTURE, not "cladding": the veneer is a single self-supporting wythe, so its brick
    # is the assembly's structure layer (BASEMENT_BRICK_VENEER). The finish must win either
    # way — colour comes from the material, never from what the layer is doing.
    green = _material_finish_color("glazed-green-brick", "structure")
    assert green == _hex_rgba("#1b4332")
    assert green == _material_finish_color("glazed-green-brick", "cladding")
    assert green != _hex_rgba(material_family_color("brick")), "glazed brick must not read red"
    assert green != _material_finish_color("white-brick", "cladding")


def test_basement_veneer_brick_faces_the_garden() -> None:
    """W-B-BRICK is authored east->west on purpose — see the note in plan/storeys/basement.py.

    It is its own wall-graph component (two open ends, no loop), so it gets the fallback
    outward sign rather than the house perimeter's, and at the house's own winding the wythe
    built *north*, back through the XPS into the concrete. This pins the direction: the brick
    must end up south of the air gap, in the sunken garden.
    """
    model, _ = resolve(load_plan(CATLIN).plan)
    wall = model.wall("W-B-BRICK")
    assert wall is not None, "W-B-BRICK missing from the resolved model"
    layers = {ly.name: ly for ly in wall.depth_layers()}
    assert set(layers) == {"air-gap", "brick"}
    gap_y = _centroid(layers["air-gap"].polygon)[1]
    brick_y = _centroid(layers["brick"].polygon)[1]
    assert brick_y < gap_y, "the brick must sit outboard (south) of the cavity"
    # And clear of the wall it faces: CATLIN_BASEMENT_12's parge ends at -4.55".
    assert max(p[1] for p in layers["brick"].polygon) <= inch(-4.55).meters + 1e-9


# --- the guard itself, on a minimal two-wall corner -----------------------------------

_CLAD = Assembly(tag="CLAD", layers=(
    Layer(name="gwb", material_ref="gwb", thickness=inch(0.5), function=LayerFunction.FINISH),
    Layer(name="cmu", material_ref="cmu", thickness=inch(8), function=LayerFunction.STRUCTURE),
    Layer(name="brick", material_ref="white-brick", thickness=inch(3.625),
          function=LayerFunction.CLADDING),
))


def _corner_plan(project, east_reversed: bool) -> PlanModel:
    """An L of two clad walls. ``east_reversed`` authors the second leg end-to-start, the
    exact mistake that flipped W-SG-RAIL-E's brick onto the porch."""
    library = Library(
        materials=(Material(tag="gwb", name="GWB", r_per_inch=0.9),
                   Material(tag="cmu", name="CMU", r_per_inch=0.11),
                   Material(tag="white-brick", name="White brick", r_per_inch=0.2,
                            color="#e9e6df", finish="white-brick")),
        assemblies=(_CLAD,),
    )
    storey = Storey(uid="ST00000001", tag="s1", elevation=ft(0),
                    default_ceiling_height=ft(9))
    nodes = [
        Node(uid="N000000001", tag="N-W", position=pt(ft(0), ft(0))),
        Node(uid="N000000002", tag="N-C", position=pt(ft(20), ft(0))),
        Node(uid="N000000003", tag="N-E", position=pt(ft(20), ft(14))),
    ]
    east = (("N-E", "N-C") if east_reversed else ("N-C", "N-E"))
    walls = [
        FoundationWall(uid="W000000001", tag="W-S", start_node="N-W", end_node="N-C",
                       assembly="CLAD", top_elevation=ft(3), bottom_elevation=ft(0)),
        FoundationWall(uid="W000000002", tag="W-E", start_node=east[0], end_node=east[1],
                       assembly="CLAD", top_elevation=ft(3), bottom_elevation=ft(0)),
    ]
    return (PlanModel(project=project, library=library, storeys=(storey,))
            .with_elements("s1", [*nodes, *walls]))


def _mismatches(plan: PlanModel) -> list[str]:
    return [f.message for f in run(plan).findings
            if f.check_id == "advisory.cladding_side_mismatch"]


def test_cladding_side_mismatch_flags_a_reversed_leg(project) -> None:
    assert len(_mismatches(_corner_plan(project, east_reversed=True))) == 1


def test_cladding_side_mismatch_silent_when_windings_agree(project) -> None:
    assert _mismatches(_corner_plan(project, east_reversed=False)) == []
