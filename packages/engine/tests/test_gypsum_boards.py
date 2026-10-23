"""Gypsum board materials, the 1/2" partition presets, and the readers that find gypsum."""

from __future__ import annotations

from types import SimpleNamespace

from typehaus.checks.structural.bracing_eval import _panels_without_gypsum
from typehaus.library.assemblies import HALF_PARTITIONS
from typehaus.library.materials import ALL_MATERIALS
from typehaus.model.assembly import Assembly, Layer
from typehaus.model.enums import LayerFunction
from typehaus.model.plan import Library
from typehaus.quantities import inch

_BY_TAG = {m.tag: m for m in ALL_MATERIALS}


def test_upgrade_boards_resolve_and_author_their_look():
    for tag, upgrade in (("gwb-ar", "abuse-resistant"), ("gwb-mr", "mold-resistant")):
        board = _BY_TAG[tag]
        assert board.gypsum_facer == "paper" and upgrade in board.gypsum_upgrades
        assert board.hatch == "gypsum" and board.color and board.source
    assert _BY_TAG["gwb-c"].gypsum_type == "type-c"
    assert len({_BY_TAG[t].color for t in ("gwb", "gwb-c", "gwb-ar", "gwb-mr")}) == 4


def test_half_presets_are_half_inch_and_cite_any_stc():
    for asm in HALF_PARTITIONS:
        for layer in asm.layers:
            if layer.name.startswith("gwb"):
                assert abs(layer.thickness.inches - 0.5) < 1e-9, asm.tag
        if asm.stc is not None:
            assert "TL-" in (asm.source or ""), asm.tag


def test_bracing_reads_any_gypsum_grade():
    library = SimpleNamespace(material=_BY_TAG.get)
    walls = [SimpleNamespace(tag=f"W-{tag}", storey="main", layers=[
        SimpleNamespace(material_ref=tag, function="finish")])
        for tag in ("gwb", "gwb-ar", "gwb-x", "cedar-tg")]
    model = SimpleNamespace(walls=walls, plan=SimpleNamespace(library=library))
    line = SimpleNamespace(storey="main")
    panels = [SimpleNamespace(wall_tags=[w.tag for w in walls])]
    assert _panels_without_gypsum(model, line, panels) == ["W-cedar-tg"]


def test_variant_does_not_inherit_stc():
    base = Assembly(tag="B", stc=48, layers=(
        Layer(name="gwb-a", material_ref="gwb", thickness=inch(0.625),
              function=LayerFunction.FINISH),))
    variant = Assembly(tag="V", variant_of="B")
    library = Library(assemblies=[base, variant])
    assert library.resolve_assembly("V").stc is None
