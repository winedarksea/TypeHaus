"""The room owns its paint (``resolve/room_paint.py``, decision #104)."""

from __future__ import annotations

from shapely.geometry import Polygon

from typehaus.model.assembly import Layer
from typehaus.model.enums import LayerFunction
from typehaus.quantities import inch
from typehaus.resolve.room_paint import PaintRoom, paint_stack_end
from typehaus.takeoff.envelope import envelope_layer_takeoff


def _materials(model, tag: str) -> list[str]:
    wall = next(w for w in model.walls if w.tag == tag)
    return [layer.material_ref for layer in wall.layers if not layer.is_cavity]


def test_an_unpainted_room_strips_its_face_only(catlin_model_ro) -> None:
    """RM-M-MECH's partition face is bare; the mudroom face keeps its latex."""
    assert _materials(catlin_model_ro, "W-M-MECH-S") == ["gwb", "spf", "gwb-ar", "latex-paint"]


def test_an_envelope_wall_in_an_unpainted_room_keeps_its_paint(catlin_model_ro) -> None:
    """The exterior wall's room-face paint is its vapour retarder (RM-M-MECH's north wall)."""
    assert _materials(catlin_model_ro, "W-M-N3B")[0] == "latex-paint"


def test_an_stc_preset_is_painted_by_its_rooms(catlin_model_ro) -> None:
    """The tested core carries no paint; both faces bound used rooms and gain it."""
    assembly = catlin_model_ro.plan.library.resolve_assembly("INT_2X4_RC")
    assert all(layer.material_ref != "latex-paint" for layer in assembly.layers)
    materials = _materials(catlin_model_ro, "W-S-BD1")
    assert materials[0] == materials[-1] == "latex-paint"


def test_rooms_that_disagree_paint_the_face_and_say_so(catlin_plan) -> None:
    face = Polygon([(0, 0), (1, 0), (1, 1)])
    rooms = [PaintRoom(tag, face, None, 0.0, 3.0, True, unpainted, None)
             for tag, unpainted in (("RM-A", True), ("RM-B", False))]
    board = Layer(name="gwb", material_ref="gwb", thickness=inch(0.5),
                  function=LayerFunction.FINISH)
    stack, conflict = paint_stack_end([board], 0, rooms, catlin_plan.library, False)
    assert conflict
    assert [layer.material_ref for layer in stack] == ["latex-paint", "gwb"]


def test_catlin_latex_paint_total(catlin_model_ro) -> None:
    """A band, not a figure: about 13,300 SF once the five rooms opt out."""
    rows = envelope_layer_takeoff(catlin_model_ro)
    total = sum(r["net_area_sqft"] for r in rows if r["material"] == "latex-paint")
    assert 12_500 < total < 14_000
    assert not any("(derived)" in str(r["scope"]) for r in rows if "paint" in r["material"])


def test_a_roof_ceiling_no_room_claims_keeps_its_authored_coat(catlin_model_ro) -> None:
    """The attic stair hall (FO-A-HALL) has no Room, so RF-HOUSE's latex stays as authored."""
    from typehaus.takeoff.coating_areas import _ceiling_area_m2, ceiling_coating_areas

    rooms = sum(_ceiling_area_m2(catlin_model_ro, c) for c in catlin_model_ro.ceilings
                if c.layers and c.layers[0].material_ref == "latex-paint")
    unroomed = ceiling_coating_areas(catlin_model_ro)[("ceiling", "latex-paint")] - rooms
    assert 9.0 < unroomed < 11.0  # m², ~109 SF of sloped hall ceiling


def test_a_coating_in_a_roof_stack_takes_no_depth(catlin_plan) -> None:
    """``assembly_layer_spans`` is the roof walk; a coat there must not push the roofing out."""
    from typehaus.model.assembly import Assembly
    from typehaus.resolve.roof_layer_setbacks import assembly_layer_spans, structure_datum_m

    stack = Assembly(tag="COATED_ROOF", layers=(
        Layer(name="primer", material_ref="latex-paint", thickness=inch(0.01),
              function=LayerFunction.FINISH),
        Layer(name="deck", material_ref="spf", thickness=inch(0.75),
              function=LayerFunction.STRUCTURE),
        Layer(name="sealer", material_ref="latex-paint", thickness=inch(0.01),
              function=LayerFunction.FINISH)))
    spans = assembly_layer_spans(stack, catlin_plan.library)
    assert [round((c1 - c0) / 0.0254, 3) for _layer, c0, c1 in spans] == [0.0, 0.75, 0.0]
    assert structure_datum_m(stack, catlin_plan.library) == inch(0.75).meters
