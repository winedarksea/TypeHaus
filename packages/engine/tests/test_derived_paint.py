"""Paint billed on exposed gypsum no assembly paints (``takeoff/derived_paint.py``)."""

from __future__ import annotations

import dataclasses

import pytest
from shapely.geometry import Polygon

from typehaus.takeoff import derived_paint as dp
from typehaus.takeoff.envelope import envelope_layer_takeoff

_M2_TO_FT2 = 10.7639104


def _fractions(model, wall_tag: str) -> list[float]:
    """The facing fraction of each gypsum end of ``wall_tag``, in stack order."""
    wall = next(w for w in model.walls if w.tag == wall_tag)
    rooms = dp._used_rooms(model)
    layers = [layer for layer in wall.layers if not layer.is_cavity]
    return [dp._facing_fraction(wall, row, rooms) for row in dp._end_rows(layers)
            if any(dp._is_gypsum(model, layer.material_ref) for layer in row)]


def _derived(rows, scope: str) -> float:
    return sum(r["net_area_sqft"] for r in rows
               if r["scope"] == scope and r["material"] == dp.PAINT)


def test_a_partition_between_two_rooms_paints_both_faces(catlin_model_ro) -> None:
    """``INT_2X4_PARTITION`` is an STC preset and authors no paint; both faces are rooms."""
    assert _fractions(catlin_model_ro, "W-M-PAN-E") == [1.0, 1.0]


def test_a_face_into_a_chase_takes_no_paint(catlin_model_ro) -> None:
    """``W-S-CH-S`` closes the second-storey chase: one face is a room, one is the shaft."""
    assert sorted(_fractions(catlin_model_ro, "W-S-CH-S")) == [0.0, 1.0]


def test_an_authored_paint_layer_is_not_billed_again(catlin_model_ro) -> None:
    """``INT_2X6_BRG`` paints both faces itself, so neither end is bare gypsum."""
    wall = next(w for w in catlin_model_ro.walls if w.assembly == "INT_2X6_BRG")
    assert _fractions(catlin_model_ro, wall.tag) == []


def test_gypsum_below_the_floor_is_not_facing_a_room(catlin_model_ro) -> None:
    """The garage stem's board band stops at the slab, below any room."""
    assert _fractions(catlin_model_ro, "W-GF-N") == [0.0]


def test_bare_gypsum_ceilings_bill_their_area_and_a_primed_one_does_not(catlin_model_ro) -> None:
    rows = envelope_layer_takeoff(catlin_model_ro)
    bare = sum(abs(Polygon(c.outline).area) for c in catlin_model_ro.ceilings
               if c.layers and c.layers[0].material_ref == "gwb")
    assert _derived(rows, "ceiling (derived)") == pytest.approx(bare * _M2_TO_FT2, abs=0.1)
    garage = next(c for c in catlin_model_ro.ceilings if c.room_ref == "RM-GARAGE")
    assert garage.layers[0].material_ref == "gwb-primer"
    assert any(r["material"] == "gwb-primer" for r in rows)


def test_catlin_derived_paint_is_the_unpainted_gypsum(catlin_model_ro) -> None:
    """A band, not a figure: about 3,700 SF of partition faces and 3,300 of deck ceilings."""
    rows = envelope_layer_takeoff(catlin_model_ro)
    assert 3000 < _derived(rows, "wall (derived)") < 4500
    assert 2800 < _derived(rows, "ceiling (derived)") < 3800


def test_a_coating_is_not_ordered_as_sheets(catlin_model_ro) -> None:
    from typehaus.model.assembly import Layer
    from typehaus.model.enums import LayerFunction
    from typehaus.quantities import inch
    from typehaus.takeoff.sheet_goods import _sheets

    paint = Layer(name="paint", material_ref="latex-paint", thickness=inch(0.01),
                  function=LayerFunction.FINISH)
    board = Layer(name="gwb", material_ref="gwb", thickness=inch(0.625),
                  function=LayerFunction.FINISH)
    assert _sheets(catlin_model_ro, (paint, board)) == [board]


def test_an_unconditioned_room_takes_no_paint(catlin_model) -> None:
    """Mark the pantry unconditioned: its ceiling and its face of W-M-PAN-E drop out."""
    full = envelope_layer_takeoff(catlin_model)
    rooms = catlin_model.rooms
    try:
        catlin_model.rooms = [dataclasses.replace(r, occupancy="unconditioned")
                              if r.tag == "RM-M-PANTRY" else r for r in rooms]
        rows = envelope_layer_takeoff(catlin_model)
        assert _derived(rows, "ceiling (derived)") < _derived(full, "ceiling (derived)")
        assert sorted(_fractions(catlin_model, "W-M-PAN-E")) == [0.0, 1.0]
    finally:
        catlin_model.rooms = rooms
