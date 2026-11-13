"""``with_product_refs``: a house names a Product on a library row without touching the library."""

import pytest
from _helpers import CATLIN

from typehaus import Material
from typehaus.library import with_product_refs
from typehaus.source import load_plan
from typehaus.takeoff.product_labels import product_labels


def _mat(tag):
    return Material(tag=tag, name=tag, r_per_inch=1.0)


def test_with_product_refs_copies_matching_rows():
    a, b = _mat("a"), _mat("b")
    out = with_product_refs([a, b], {"b": "PROD-X"})
    assert [m.tag for m in out] == ["a", "b"]
    assert out[0] is a and out[1].product_ref == "PROD-X"
    assert b.product_ref is None  # the original is untouched


def test_with_product_refs_raises_on_unmatched_tag():
    with pytest.raises(ValueError, match="nope"):
        with_product_refs([_mat("a")], {"nope": "PROD-X"})


def test_catlin_waterproofing_names_bituthene():
    plan = load_plan(CATLIN).plan
    label = product_labels(plan)[("envelope_layers", "waterproofing")]
    assert "Bituthene 3000" in label
