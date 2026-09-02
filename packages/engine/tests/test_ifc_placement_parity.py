"""The world-frame contract that lets the emitter author its own containment relations.

``lowlevel.assign_container`` and ``lowlevel.aggregate`` build ``IfcRelContainedInSpatial
Structure`` / ``IfcRelAggregates`` directly rather than calling ``ifcopenshell.api``. The
API versions do one extra thing: they re-derive each product's ``ObjectPlacement`` so it
becomes relative to its new parent. That is a no-op *here* — every represented product this
emitter writes carries an identity placement in the shared project frame, with the geometry
itself authored in world coordinates inside the swept solid — but it is not free: each
re-derivation ends in a ``remove_deep2`` whose ``file.remove()`` is O(file size), which cost
20.9 s of a 35.5 s catlin emit.

So the bypass is only sound while that premise holds. This module is the premise, asserted:
if some future emitter starts nesting placements, these tests go red and the direct
relations must be revisited (or the geometry re-based) rather than quietly shipping products
that land in the wrong place in Revit.
"""

from __future__ import annotations

import numpy as np
import pytest

ifcopenshell = pytest.importorskip("ifcopenshell")
import ifcopenshell.util.placement as placement_util  # noqa: E402

# The storeys are the deliberate exception: ``set_storey_elevation`` gives each one a
# placement at its datum, and ``diff/semantic.py`` reads exactly that. It re-bases nothing,
# because no element placement is relative to it.
_ELEVATED = "IfcBuildingStorey"


def _placed_products(ifc_file) -> list:
    return [p for p in ifc_file.by_type("IfcProduct") if p.ObjectPlacement is not None]


@pytest.fixture(scope="module")
def ifc_file(catlin_ifc_path):
    return ifcopenshell.open(str(catlin_ifc_path))


def test_every_product_but_a_storey_sits_at_the_world_origin(ifc_file):
    """The premise itself: composed placement == identity for everything with geometry.

    A non-identity matrix here means some product's coordinates are being interpreted
    relative to a parent, and the geometry — authored in world coordinates — would be drawn
    at double the offset.
    """
    offenders = [
        (product.is_a(), product.Name)
        for product in _placed_products(ifc_file)
        if product.is_a() != _ELEVATED
        and not np.allclose(placement_util.get_local_placement(product.ObjectPlacement),
                            np.eye(4), atol=1e-9)
    ]
    assert not offenders, offenders[:20]


def test_the_only_nested_placements_are_openings_onto_an_identity_host(ifc_file):
    """The structural form of the same claim, independent of the arithmetic above.

    ``PlacementRelTo`` is what an ifcopenshell api re-basing leaves behind. Exactly one
    still runs: ``add_opening`` goes through ``feature.add_feature``, which re-bases each
    ``IfcOpeningElement`` onto the wall it voids. That is harmless only because the host is
    itself at identity, so the chain composes back to identity — which is why the void lands
    in the wall rather than at twice its offset. Pin both halves: nothing *else* nests, and
    every nest is onto an identity parent.
    """
    nested = [p for p in _placed_products(ifc_file)
              if p.ObjectPlacement.PlacementRelTo is not None]
    assert nested, "the house has voided openings"
    wrong_class = {p.is_a() for p in nested} - {"IfcOpeningElement"}
    assert not wrong_class, wrong_class
    off_origin = [p.Name for p in nested
                  if not np.allclose(
                      placement_util.get_local_placement(p.ObjectPlacement.PlacementRelTo),
                      np.eye(4), atol=1e-9)]
    assert not off_origin, off_origin[:20]


def test_each_storey_placement_is_its_own_elevation(ifc_file):
    """``diff/semantic.py`` reads storey placements — the one real consumer of a datum."""
    storeys = ifc_file.by_type(_ELEVATED)
    assert storeys, "the catlin house has storeys"
    for storey in storeys:
        matrix = placement_util.get_local_placement(storey.ObjectPlacement)
        assert matrix[0][3] == pytest.approx(0.0, abs=1e-9)
        assert matrix[1][3] == pytest.approx(0.0, abs=1e-9)
        assert matrix[2][3] == pytest.approx(storey.Elevation, abs=1e-9)


def test_no_element_is_contained_in_two_places_at_once(ifc_file):
    """Appending to an existing relation, rather than calling the API, is what makes a
    double containment possible at all — the API removes the previous one. Nothing may be
    assigned to two containers, and nothing may be listed twice in the same one."""
    seen: dict[int, str] = {}
    for rel in ifc_file.by_type("IfcRelContainedInSpatialStructure"):
        container = rel.RelatingStructure.Name
        elements = rel.RelatedElements
        assert len(set(elements)) == len(elements), f"{container} lists an element twice"
        for element in elements:
            assert element.id() not in seen, (
                f"{element.Name} is in both {seen[element.id()]} and {container}")
            seen[element.id()] = container
    assert seen, "the spatial structure contains elements"


def test_no_object_is_aggregated_under_two_parents(ifc_file):
    """The same guard for ``aggregate`` — a part under two assemblies double-counts."""
    seen: dict[int, str] = {}
    for rel in ifc_file.by_type("IfcRelAggregates"):
        parent = rel.RelatingObject.Name
        children = rel.RelatedObjects
        assert len(set(children)) == len(children), f"{parent} lists a child twice"
        for child in children:
            assert child.id() not in seen, (
                f"{child.Name} is under both {seen[child.id()]} and {parent}")
            seen[child.id()] = parent
    assert seen, "the framed model aggregates members"


def test_one_containment_relation_per_container(ifc_file):
    """The batching the direct write buys: appending to one relation per container rather
    than minting a fresh ``IfcRelContainedInSpatialStructure`` per element. A file with one
    relation per *element* is legal IFC but is a much slower write."""
    containers = [rel.RelatingStructure.id()
                  for rel in ifc_file.by_type("IfcRelContainedInSpatialStructure")]
    assert len(containers) == len(set(containers))
