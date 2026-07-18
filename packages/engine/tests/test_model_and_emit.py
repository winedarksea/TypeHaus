"""WP1.3/1.7 tests — registry completeness, frozen-ness, card renders for every assembly."""

from __future__ import annotations

import pytest

from typehaus.model import Library, element_kinds
from typehaus.model.registry import constructor_names


def test_registry_populated() -> None:
    assert len(element_kinds()) >= 20
    # Every element kind is exposed as a dialect constructor.
    ctors = constructor_names()
    for name in element_kinds():
        assert name in ctors, f"{name} not registered as a constructor"


def test_elements_are_frozen(project) -> None:
    from typehaus.model import Node, pt, ft

    n = Node(uid="AAAAAAAAAA", tag="N-1", position=pt(ft(0), ft(0)))
    with pytest.raises(Exception):
        n.tag = "N-2"  # type: ignore[misc]


def test_card_renders_for_every_library_assembly() -> None:
    from library import STARTER_MATERIALS
    from library.assemblies import ALL_ASSEMBLIES
    from typehaus.emit.draw import render_card_svg

    lib = Library(materials=STARTER_MATERIALS, assemblies=ALL_ASSEMBLIES)
    for asm in ALL_ASSEMBLIES:
        svg = render_card_svg(lib.resolve_assembly(asm.tag), lib)
        assert svg.startswith("<svg") and svg.endswith("</svg>")
        assert asm.tag in svg


def test_variant_resolves_against_base() -> None:
    from typehaus.model import (
        Assembly,
        Layer,
        LayerFunction,
        Material,
        Substitution,
        inch,
        outside_of,
    )

    base = Assembly(tag="B", layers=(
        Layer(name="stud", material_ref="spf", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE),
        Layer(name="wrb", material_ref="m", thickness=inch(0.02),
              function=LayerFunction.MEMBRANE),
    ))
    variant = Assembly(tag="B-BRICK", variant_of="B", substitute=(
        Substitution(span=outside_of("wrb"), replacement=(
            Layer(name="brick", material_ref="brick", thickness=inch(3.625),
                  function=LayerFunction.CLADDING),)),))
    lib = Library(materials=(Material(tag="spf", name="s"),), assemblies=(base, variant))
    resolved = lib.resolve_assembly("B-BRICK")
    names = [layer.name for layer in resolved.layers]
    assert names == ["stud", "wrb", "brick"]
