"""A ceiling exports as an ``IfcCovering`` CEILING, contained in its room's storey.

The resolved solid is filed under the deck that hangs it (so the viewer hides it with that
level); IFC keeps its own convention and contains the covering where the room is.
"""

from __future__ import annotations

import pytest


@pytest.fixture(scope="module")
def ifc_file(catlin_ifc_path):
    import ifcopenshell

    return ifcopenshell.open(str(catlin_ifc_path))


def test_a_ceiling_is_a_ceiling_covering_in_its_rooms_storey(ifc_file) -> None:
    from ifcopenshell.util.element import get_container

    living = next(item for item in ifc_file.by_type("IfcCovering")
                  if item.Name == "CEIL-RM-M-LIVING")
    assert living.PredefinedType == "CEILING"
    assert get_container(living).Name == "main"
    assert not any(item.Name.startswith("CEIL-") for item in ifc_file.by_type("IfcFooting"))
