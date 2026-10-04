"""Blocking stock references are validated on resolved assembly variants."""

from types import SimpleNamespace

import pytest

from typehaus.checks.integrity.catalog_tags import blocking_material_ref
from typehaus.model import Assembly, FramingSpec, Layer, LayerFunction, Material
from typehaus.model.plan import Library
from typehaus.quantities import inch


@pytest.mark.parametrize("ref", [None, "matching-wood", "misspelled-wood"])
def test_blocking_stock_reference_including_inherited_variants(ref):
    assembly = Assembly(
        tag="BASE",
        layers=(Layer(name="stud", material_ref="matching-wood", thickness=inch(5.5),
                      function=LayerFunction.STRUCTURE,
                      framing=FramingSpec(member="2x6", blocking_heights=(inch(48),),
                                          blocking_material_ref=ref)),),
    )
    library = Library(
        materials=(Material(tag="matching-wood", name="Matching wood"),),
        assemblies=(assembly, Assembly(tag="VARIANT", variant_of="BASE")),
    )
    findings = blocking_material_ref(SimpleNamespace(plan=SimpleNamespace(library=library)))
    if ref != "misspelled-wood":
        assert findings == []
    else:
        assert {finding.element_tags for finding in findings} == {("BASE",), ("VARIANT",)}
        assert all(finding.severity.value == "error" for finding in findings)
        assert all(ref in finding.message for finding in findings)
