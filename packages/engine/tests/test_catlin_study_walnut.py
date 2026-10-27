"""The call booth's solid desktops uses the walnut stock specified for its boards."""

from types import SimpleNamespace

from typehaus.emit.gltf.canvas_objects import _add_canvas_parts
from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.emit.gltf.palette import _authored_material_color
from typehaus.library.wood_appearance import NATURAL_WOOD_COLORS
from typehaus.model.canvas import canvas_object_types
from typehaus.model.placeable_symbols import PART_COLORS


def test_study_boards_share_the_wainscot_walnut_in_viewer_and_glb(catlin_plan):
    materials = {material.tag: material for material in catlin_plan.library.materials}
    furniture_types = {item.tag: item for item in catlin_plan.library.furniture_types}
    viewer_types = {item["tag"]: item for item in canvas_object_types(catlin_plan)}
    elements = {item.tag: item for item in catlin_plan.all_elements()}
    walnut_color = NATURAL_WOOD_COLORS["walnut"]
    paneling = elements["WP-M-STUDY-WAINSCOT"]
    assert materials[paneling.material_ref].color == walnut_color

    for furniture_tag, bank_tag in (
        ("FT-STUDY-DESK", "SB-M-STUDY-DESK"),
        ("FT-STUDY-DESK-LEAF", "SB-M-STUDY-LEAF"),
    ):
        furniture = furniture_types[furniture_tag]
        stock_ref = elements[bank_tag].material_ref
        assert furniture.wood_material_ref == stock_ref
        stock = materials[stock_ref]
        assert stock.species == "walnut" and stock.color == walnut_color
        wood_parts = [part for part in viewer_types[furniture_tag]["model_parts"]
                      if part.get("material_ref")]
        assert wood_parts and all(part["color"] == walnut_color
                                  and part["material_ref"] == stock_ref for part in wood_parts)

        mesh = _MeshBuilder()
        placement = SimpleNamespace(position=(0.0, 0.0), rotation_degrees=0.0, z_m=0.0, mount=None)
        assert _add_canvas_parts(mesh, placement, furniture, materials)
        assert _authored_material_color(stock) in mesh._buckets
        for generic_role in ("wood", "sauna-wood", "sauna-wood-dark"):
            assert PART_COLORS[generic_role] not in mesh._buckets
