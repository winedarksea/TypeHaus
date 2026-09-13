"""The centreline DXF RISA-3D imports: lines, points, section layers, and no timestamp."""

from __future__ import annotations

import dataclasses

import pytest
from analytical_fixtures import HEIGHT_M, SPAN_M, portal_frame

from typehaus.analytical.graph import Fixity, Support
from typehaus.emit.draw.dxf_structure import (
    LAYER_LABELS,
    LAYER_NODES,
    LAYER_NOTES,
    LAYER_SUPPORTS,
    write_structure_dxf,
)

_M_TO_IN = 1.0 / 0.0254
BEAM_LAYER = "3.5X11.875_GLULAM"
COLUMN_LAYER = "12_RD_CONCRETE"


@pytest.fixture(scope="module")
def doc(tmp_path_factory):
    import ezdxf

    path = write_structure_dxf(portal_frame(), tmp_path_factory.mktemp("dxf") / "c.dxf")
    return ezdxf.readfile(path)


def test_one_line_per_member_and_one_point_per_node(doc):
    msp = doc.modelspace()
    assert len(msp.query("LINE")) == 3
    assert len(msp.query("POINT")) == 4


def test_layers_include_the_section_sets_and_the_annotation_layers(doc):
    names = {layer.dxf.name for layer in doc.layers}
    assert {BEAM_LAYER, COLUMN_LAYER} <= names
    assert {LAYER_NODES, LAYER_LABELS, LAYER_SUPPORTS, LAYER_NOTES} <= names


def test_units_are_inches_and_coordinates_match_the_nodes(doc):
    assert doc.header["$INSUNITS"] == 1
    lines = {line.dxf.layer: line for line in doc.modelspace().query("LINE")}
    beam = lines[BEAM_LAYER]
    assert tuple(beam.dxf.start) == pytest.approx((0.0, 0.0, HEIGHT_M * _M_TO_IN))
    assert tuple(beam.dxf.end) == pytest.approx(
        (SPAN_M * _M_TO_IN, 0.0, HEIGHT_M * _M_TO_IN)
    )
    columns = [line for line in doc.modelspace().query("LINE")
               if line.dxf.layer == COLUMN_LAYER]
    assert len(columns) == 2
    for column in columns:
        assert column.dxf.start[2] == pytest.approx(0.0)
        assert column.dxf.end[2] == pytest.approx(HEIGHT_M * _M_TO_IN)


def test_labels_name_the_member_the_section_and_the_item(doc):
    labels = {text.dxf.text for text in doc.modelspace().query("TEXT")
              if text.dxf.layer == LAYER_LABELS}
    assert f"PT-W | {COLUMN_LAYER} | deck_post/PT-W" in labels
    assert f"BM-1 | {BEAM_LAYER} | (no engineering item)" in labels


def test_supports_are_labelled_and_notes_carry_the_conventions(doc):
    texts = {text.dxf.layer: [] for text in doc.modelspace().query("TEXT")}
    for text in doc.modelspace().query("TEXT"):
        texts[text.dxf.layer].append(text.dxf.text)
    assert texts[LAYER_SUPPORTS] == ["FIXED", "FIXED"]
    notes = " / ".join(texts[LAYER_NOTES])
    assert "INCHES" in notes and "Z UP" in notes
    assert "LOADS ARE NOT DRAWN" in notes
    assert "ASSUMPTION: fixture: beam bears on the column tops" in notes
    assert "deck_post/PT-E" in notes          # the scope line


def test_two_writes_are_byte_identical(tmp_path):
    model = portal_frame()
    first = write_structure_dxf(model, tmp_path / "a.dxf").read_bytes()
    second = write_structure_dxf(model, tmp_path / "b.dxf").read_bytes()
    assert first == second


def _rolled_pin(model):
    """The fixture with its two bases re-authored as beam-on-wall pins that cannot roll."""
    return dataclasses.replace(model, supports=tuple(
        Support(s.node, Fixity.PINNED, "bears on a wall", item_id=s.item_id,
                element_tag=s.element_tag, rotations=(True, False, False))
        for s in model.supports))


def test_support_text_names_a_restrained_rotation(tmp_path):
    import ezdxf

    path = write_structure_dxf(_rolled_pin(portal_frame()), tmp_path / "p.dxf")
    texts = [text.dxf.text for text in ezdxf.readfile(path).modelspace().query("TEXT")
             if text.dxf.layer == LAYER_SUPPORTS]
    assert texts == ["PINNED RX", "PINNED RX"]
