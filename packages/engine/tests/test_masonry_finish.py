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


def _centroid(polygon):
    return (sum(p[0] for p in polygon) / len(polygon),
            sum(p[1] for p in polygon) / len(polygon))


# The catlin case this file was written for — the porch railing's three W-SG-RAIL-* walls,
# whose white-brick wythe had to land outboard on each — was retired with the masonry guard
# itself. The house-wide mismatch sweep below still covers every clad wall it has, and the
# L-corner fixtures further down reproduce the winding mistake that flipped W-SG-RAIL-E's
# brick onto the porch, synthetically and in both directions.


def test_catlin_has_no_cladding_side_mismatch(catlin_plan) -> None:
    # `run(plan)` with NO house_dir, and not `catlin_check_report()`: an absent directory
    # means an empty `Preferences`, so a different suppression set and a different
    # jurisdiction. Two different reports, not one cheaper one.
    report = run(catlin_plan)
    mismatches = [f for f in report.findings
                  if f.check_id == "advisory.cladding_side_mismatch"]
    assert not mismatches, [f.message for f in mismatches]


def test_white_brick_material_ships_its_appearance(catlin_model_ro) -> None:
    from typehaus.server.model_json import model_to_dict

    model = catlin_model_ro
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


def test_glazed_green_brick_material_ships_its_appearance(catlin_model_ro) -> None:
    """The basement's south veneer — same pattern as the white brick above.

    A third brick had to be distinguishable from the other two or the sunken garden's most
    visible wall would render as the masonry family's red, which is the porch's brick, not
    this one.
    """
    from typehaus.server.model_json import model_to_dict

    model = catlin_model_ro
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


def test_basement_veneer_brick_faces_the_garden(catlin_model_ro) -> None:
    """W-B-BRICK is authored east->west on purpose — see the note in plan/storeys/basement.py.

    It is its own wall-graph component (two open ends, no loop), so it gets the fallback
    outward sign rather than the house perimeter's, and at the house's own winding the wythe
    built *north*, back through the XPS into the concrete. This pins the direction: the brick
    must end up south of the air gap, in the sunken garden.
    """
    model = catlin_model_ro
    wall = model.wall("W-B-BRICK")
    assert wall is not None, "W-B-BRICK missing from the resolved model"
    # One flat wythe since 2026-09-04. It was five `Layer.slot` regions of the Ishtar scheme,
    # and this loop checked every one of them because a slot that resolved its regions to
    # different strips would have built the plinth into the concrete and the field into the
    # garden. The loop is kept over whatever brick layers the wall has, so it comes back on
    # its own if a banded scheme ever returns.
    depth = {ly.name: ly for ly in wall.depth_layers()}
    assert set(depth) == {"air-gap", "brick"}
    gap_y = _centroid(depth["air-gap"].polygon)[1]
    bricks = [ly for ly in wall.layers if ly.name.startswith("brick")]
    assert len(bricks) == 1, "one flat unglazed field"
    for brick in bricks:
        assert _centroid(brick.polygon)[1] < gap_y, \
            f"{brick.name} must sit outboard (south) of the cavity"
        # And clear of the wall it faces: BASEMENT_12's parge ends at -4.55".
        assert max(p[1] for p in brick.polygon) <= inch(-4.55).meters + 1e-9



def test_fireplace_wash_faces_the_room(catlin_model_ro) -> None:
    """The five W-M-FIRE-* walls carry the wash on RM-M-LIVING's side, not against the studs.

    ``FIREPLACE_BRICK_WYTHE`` is ``layers=(brick, wash)`` and the ORDER is the whole point.
    ``resolve/topology.py`` places layer 0 on the ``-outward_sign * normal(start->end)`` side —
    the left normal ``(-dy, dx)``. Each of these walls is its own ``open_end`` node pair, finds
    no closed walk and so takes ``UNRECOVERABLE_WINDING_OUTWARD_SIGN = +1.0``; they are authored
    S->N, so ``normal`` points WEST and layer 0 lands EAST, against W-M-E1's studs. The room face
    is therefore the LAST layer, and the wash has to be it.

    ** THIS TEST IS THE ONLY GUARD. ** ``advisory.cladding_side_mismatch`` inspects CLADDING
    layers and this assembly deliberately has none (CLADDING would drag a brick panel standing
    inside a conditioned room into the Glaser scope — see the assembly's own note). So a wash
    authored at index 0 would silently paint the BACK of the panel, invisible from the room, at
    0 FAIL. Compare ``test_basement_veneer_brick_faces_the_garden`` above, which pins the same
    class of bug on the one wall that does have a cladding layer.
    """
    model = catlin_model_ro
    # DERIVED, not hard-coded. The panel was one wall, then five, then seven (the buried stub
    # became three piers with two joist pockets between them on 2026-09-19), and a list spelled
    # out here would have to be edited every time — which is how a test about layer ORDER ends
    # up silently grading fewer walls than the house has.
    tags = sorted(w.tag for w in model.walls
                  if getattr(model.plan.by_tag(w.tag), "assembly", None)
                  == "FIREPLACE_BRICK_WYTHE")
    assert len(tags) == 7, tags
    for tag in tags:
        wall = model.wall(tag)
        assert wall is not None, f"{tag} missing from the resolved model"
        depth = {ly.name: ly for ly in wall.depth_layers()}
        assert set(depth) == {"brick", "wash"}, f"{tag}: {sorted(depth)}"
        brick_x = _centroid(depth["brick"].polygon)[0]
        wash_x = _centroid(depth["wash"].polygon)[0]
        # West is -x and the living room is west of the panel; W-M-E1's studs are east.
        assert wash_x < brick_x, (
            f"{tag}: the wash must sit WEST of the brick (toward RM-M-LIVING), not against "
            f"W-M-E1's studs — wash x={wash_x:.5f} vs brick x={brick_x:.5f}")
        # And it is a film, not a wythe. The centroids sit half of each layer's own thickness
        # either side of the shared face, so the gap is (brick + wash) / 2 — derived from the
        # resolved layers rather than hardcoded, because `_WASH_FILM` is a render decision that
        # has already moved once (0.01" -> 1/8") and what this assertion is about is the ORDER,
        # not the value. What it pins is that the wash is a thin film in front of a 3 5/8" wythe
        # and not a second wythe of its own.
        brick_t = depth["brick"].thickness_m
        wash_t = depth["wash"].thickness_m
        assert brick_t == pytest.approx(inch(3.625).meters, abs=1e-9)
        assert wash_t < inch(0.5).meters, "the wash is a coating, not a wythe"
        assert brick_x - wash_x == pytest.approx((brick_t + wash_t) / 2.0, abs=1e-6)


def test_court_wash_faces_the_court(catlin_plan, catlin_model_ro) -> None:
    """All five SUNKEN_GARDEN_WALL walls carry the wash on the COURT face, at layer 0.

    The court is a light well and the wash is what makes it one, so the face is the design.
    ``params/sunken_garden.py`` used to claim this component had lost its only closed loop and
    fell back to ``UNRECOVERABLE_WINDING_OUTWARD_SIGN`` (+1); it has not — ``W-SG-ARCH`` supplies
    the N-SG-MW/N-SG-ME leg, the walk ME->SE->SW->MW->ME closes, and the component resolves to
    **-1.0**, which is what puts layer 0 on the court side for all five.

    Deleting W-SG-ARCH, or renaming either of those nodes, would drop the sign to +1 and bury the
    wash on the outboard face of all five walls silently: no check grades a FINISH layer's side.
    That is what this test is for.
    """
    from typehaus.resolve.orientation import resolve_storey_windings

    plan = catlin_plan
    windings = resolve_storey_windings(plan, "court-low")
    model = catlin_model_ro
    # The court walls and the direction the court lies in from each one's own axis.
    court_side = {
        "W-SG-W1": ("x", +1),   # NW->MW, court is east
        "W-SG-E1": ("x", -1),   # ME->NE, court is west
        "W-SG-W2": ("x", +1),   # MW->SW, court is east
        "W-SG-E2": ("x", -1),   # SE->ME, court is west
        "W-SG-S": ("y", +1),    # SW->SE, court is north
    }
    for tag, (axis, sign) in court_side.items():
        wall = model.wall(tag)
        assert wall is not None, f"{tag} missing from the resolved model"
        assert windings.sign_for_wall(plan.by_tag(tag)) == -1.0, (
            f"{tag}: the N-SG-* component must resolve to -1.0; a +1 here means the closed walk "
            "through W-SG-ARCH was lost and every wash face is now on the wrong side")
        depth = {ly.name: ly for ly in wall.depth_layers()}
        # All five carry dimpleboard outboard (2026-09-16): full height on the buried
        # retaining U, below grade only on W-SG-W1/E1 (checked below).
        assert set(depth) == {"wash", "concrete", "dimple-board"}, f"{tag}: {sorted(depth)}"
        board = depth["dimple-board"]
        if tag in {"W-SG-W1", "W-SG-E1"}:
            assert board.z1_m is not None and board.z1_m < wall.z1_m - 0.5, (
                f"{tag}: the board must stop at grade, below the exposed face's devices")
        else:
            assert board.z1_m is None, f"{tag}: the retained face is drained full height"
        i = 0 if axis == "x" else 1
        wash = _centroid(depth["wash"].polygon)[i]
        concrete = _centroid(depth["concrete"].polygon)[i]
        assert (wash - concrete) * sign > 0, (
            f"{tag}: the wash must sit on the COURT side of the pour along {axis} "
            f"(expected sign {sign:+d}), got wash={wash:.5f} concrete={concrete:.5f}")
        # ** AND THE TWO NEW ONES ARE ON THE OTHER SIDE, WHICH IS THE WHOLE POINT. ** A
        # drainage plane on the court face would be a dimpled sheet in a light well; a wash
        # on the retained face would be paint under nine feet of soil. Both are silent
        # errors — nothing grades which side a layer lands on — and the outward sign that
        # decides it is the same one this test exists to pin.
        for name in ("dimple-board",):
            buried = _centroid(depth[name].polygon)[i]
            assert (buried - concrete) * sign < 0, (
                f"{tag}: {name} must sit on the RETAINED side of the pour along {axis} "
                f"(expected sign {-sign:+d}), got {buried:.5f} concrete={concrete:.5f}")
        # ** THE POUR IS STILL ON THE GRID. ** This is the assertion the alignment re-strike
        # exists for: a layer outboard re-centres the stack, and an unrevised
        # `_COURT_AXIS_SHIFT` slides the 12" concrete off its node line — silently, at
        # 0 FAIL. The axis coordinate is 8.0 / 28.0 ft on the x-axis walls.
        axis_coord = wall.axis[0][i]
        assert concrete == pytest.approx(axis_coord, abs=1e-6), (
            f"{tag}: the pour's centre is {concrete:.5f} and its node line is "
            f"{axis_coord:.5f} — the alignment did not follow the stack")


def test_raised_garden_wash_faces_the_yard_on_the_perimeter_legs_only(catlin_plan, catlin_model_ro) -> None:
    """Only the three perimeter legs are washed, and their wash faces the lawn.

    The RG graph is an open chain (``WB-NW-SW-SE-NE-EB``, no north wall), so ``_closed_walks``
    finds nothing and the sign genuinely IS ``UNRECOVERABLE_WINDING_OUTWARD_SIGN = +1.0``. That
    is not a bug here: with +1, layer 0 lands on the ``-normal`` side, which for these three legs
    is exactly the yard. The two balcony returns are excluded because they have no lawn-facing
    face at all — layer 0 on them would land in the terrace fill.
    """
    from typehaus.resolve.orientation import (
        UNRECOVERABLE_WINDING_OUTWARD_SIGN,
        resolve_storey_windings,
    )

    plan = catlin_plan
    windings = resolve_storey_windings(plan, "yard-low")
    model = catlin_model_ro
    yard_side = {
        "W-RG-BLOCK": ("y", -1),   # SW->SE, yard is south
        "W-RG-WEST": ("x", -1),    # NW->SW, yard is west
        "W-RG-EAST": ("x", +1),    # SE->NE, yard is east
    }
    for tag, (axis, sign) in yard_side.items():
        wall = model.wall(tag)
        assert wall is not None, f"{tag} missing from the resolved model"
        assert windings.sign_for_wall(plan.by_tag(tag)) == UNRECOVERABLE_WINDING_OUTWARD_SIGN
        depth = {ly.name: ly for ly in wall.depth_layers()}
        assert set(depth) == {"wash", "srw-block"}, f"{tag}: {sorted(depth)}"
        i = 0 if axis == "x" else 1
        wash = _centroid(depth["wash"].polygon)[i]
        block = _centroid(depth["srw-block"].polygon)[i]
        assert (wash - block) * sign > 0, (
            f"{tag}: the wash must sit on the YARD side of the block along {axis} "
            f"(expected sign {sign:+d}), got wash={wash:.5f} block={block:.5f}")
        # Banded to the exposed 3'-4" off WALL_BASE, NOT to the global site grade (-2'-10").
        assert wall.z0_m == pytest.approx(ft(-4).meters, abs=1e-6)
        assert depth["wash"].z0_m == pytest.approx(ft(-4).meters + inch(8).meters, abs=1e-6)
    for tag in ("W-RG-WEST-BALCONY", "W-RG-EAST-BALCONY"):
        wall = model.wall(tag)
        assert wall is not None
        assert {ly.name for ly in wall.depth_layers()} == {"srw-block"}, (
            f"{tag} returns terrace fill to the south and the balcony underside to the north — "
            "it has no lawn-facing face and must stay bare")

# --- the guard itself, on a minimal two-wall corner -----------------------------------

_CLAD = Assembly(tag="CLAD", layers=(
    Layer(name="gwb", material_ref="gwb", thickness=inch(0.5), function=LayerFunction.FINISH),
    Layer(name="cmu", material_ref="cmu", thickness=inch(8), function=LayerFunction.STRUCTURE),
    Layer(name="brick", material_ref="white-brick", thickness=inch(3.625),
          function=LayerFunction.CLADDING),
))


def _corner_plan(project, east_reversed: bool) -> PlanModel:
    """An L of two clad walls. ``east_reversed`` authors the second leg end-to-start, the
    exact mistake that once flipped the porch parapet's brick onto the porch (W-SG-RAIL-E,
    now retired — this synthetic pair is what keeps the lesson)."""
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
