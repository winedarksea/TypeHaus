"""Every layer a sheet emits must be styled by both writers.

An unstyled layer does not fail loudly — it silently falls back to the writer's default
pen, so a drawing exports with the wrong lineweight and colour and nobody notices until
someone reads the sheet. That is exactly how ``A-STAIR``, ``A-FURN``, ``M-EQPT`` and
``E-POWR`` came to draw as generic strokes, and how ``"alarm"`` came to draw as a window
glass bar. This test walks the real permit set and holds both tables to what it finds, so
adding a layer without styling it fails here instead of on paper.
"""

from __future__ import annotations

import pytest

from typehaus.emit.draw.dxf_writer import _LAYER_STYLE as DXF_LAYER_STYLE
from typehaus.emit.draw.pdf_writer import _LAYER_STYLE as PDF_LAYER_STYLE
from typehaus.emit.draw.sheets import build_sheet_index


def _layers_emitted_by_the_permit_set(model) -> set[str]:
    """Layer names on every node of every IR-backed sheet in the emitted set."""
    layers: set[str] = set()
    for spec in build_sheet_index(model):
        if spec.scene is None:  # cover/schedule pages compose matplotlib tables directly
            continue
        for node in spec.scene(model).nodes:
            layer = getattr(node, "layer", None)
            if layer:
                layers.add(layer)
    return layers


@pytest.fixture(scope="module")
def catlin_sheet_layers(catlin_model) -> set[str]:
    return _layers_emitted_by_the_permit_set(catlin_model)


def test_pdf_writer_styles_every_emitted_layer(catlin_sheet_layers):
    unstyled = sorted(catlin_sheet_layers - set(PDF_LAYER_STYLE))
    assert not unstyled, f"layers emitted but unstyled in pdf_writer: {unstyled}"


def test_dxf_writer_styles_every_emitted_layer(catlin_sheet_layers):
    unstyled = sorted(catlin_sheet_layers - set(DXF_LAYER_STYLE))
    assert not unstyled, f"layers emitted but unstyled in dxf_writer: {unstyled}"


def test_the_two_writer_tables_cover_the_same_layers():
    """A layer styled for print but not for CAD exports wrong, and vice versa."""
    assert sorted(set(PDF_LAYER_STYLE) - set(DXF_LAYER_STYLE)) == []
    assert sorted(set(DXF_LAYER_STYLE) - set(PDF_LAYER_STYLE)) == []
