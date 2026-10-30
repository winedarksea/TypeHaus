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
