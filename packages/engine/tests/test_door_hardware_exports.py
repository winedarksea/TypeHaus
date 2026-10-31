"""The IFC accessories and live viewer consume the same authored door parts."""
import ifcopenshell
import ifcopenshell.util.element
import pytest

from typehaus.server.model_json_door_hardware import authored_product_parts

# Measured: shared house + IFC setup 16.2 s (pytest --durations=10).
pytestmark = pytest.mark.slow


def test_authored_parts_include_two_finishes_and_viewer(catlin_model_ro):
    model = catlin_model_ro
    entry = next(opening for opening in model.openings if opening.tag == "D-M-ENTRY")
    parts = authored_product_parts(model, entry)
    assert {part["material_ref"] for part in parts if part["key"].startswith("leaf:")} == {
        "door-paint-exterior", "door-paint-white"}
    spec = next(spec for spec in model.plan.library.door_types if spec.tag == entry.type_ref)
    viewer_index = next(index for index, item in enumerate(spec.hardware) if item.role == "viewer")
    viewer = next(part for part in parts if part["key"] == f"hardware:{viewer_index}")
    leaf_bottom = entry.doorway.leaf_bottom_z_m
    assert all((solid["z0_m"] + solid["z1_m"])/2 == pytest.approx(leaf_bottom + 1.524)
               for solid in viewer["solids"])
    garage = next(opening for opening in model.openings if opening.tag == "D-G-SERVICE")
    assert authored_product_parts(model, garage) is None


def test_ifc_hardware_accessories_have_product_quantity_installation_and_geometry(catlin_ifc_path):
    model = ifcopenshell.open(str(catlin_ifc_path))
    hardware = []
    for accessory in model.by_type("IfcDiscreteAccessory"):
        spec = ifcopenshell.util.element.get_pset(accessory, "TypeHaus_DoorHardware")
        if spec:
            hardware.append((accessory, spec))
    assert len(hardware) == 33  # nine entry items plus eight for each French pair
    viewer = [(accessory, spec) for accessory, spec in hardware if spec["Role"] == "viewer"]
    assert len(viewer) == 1
    accessory, spec = viewer[0]
    assert spec["ProductRef"] == "PROD-DOORSCOPE-DS2000"
    assert spec["HeightAboveLeafBottom"] == pytest.approx(1.524)
    assert "caulk" in spec["Installation"]
    assert spec["Quantity"] == 1
    assert accessory.Representation
    assert accessory.Nests[0].RelatingObject.is_a("IfcDoor")
