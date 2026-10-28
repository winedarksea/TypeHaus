"""The authoring catalog and the variant catalog — what the house *could* be.

The rest of model.json describes the resolved house; this describes the palette the editor
draws from (window/door products, occupancies, materials, every resolved assembly) and the
named alternatives ``variants.toml`` declares. Split out because the two answer the same
question at different scales and neither is derived from resolved geometry: both are read
straight off the plan's library, so they change when the *library* changes, not when the
house does.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from typehaus.model.canvas import canvas_object_types
from typehaus.resolve.model import ResolvedModel
from typehaus.server.model_json_mesh import mesh_json
from typehaus.server.model_json_shared import _enum_value, _provenance
from typehaus.source.provenance import Provenance

if TYPE_CHECKING:
    from collections.abc import Sequence

    from typehaus.diff.variants import VariantSpec


def load_variant_catalog(house_dir: Path | str | None) -> tuple[VariantSpec, ...]:
    """The declared variant specs for ``house_dir`` — the graceful model.json entry point.

    A house without a ``variants.toml`` simply declares no variants, and a *malformed*
    catalog must degrade the same way here rather than take down model.json emission (the
    server's GET /model and the offline PWA both ride through this): ``haus variants list``
    is the surface that reports catalog errors loudly.
    """
    if house_dir is None:
        return ()
    from typehaus.diff.variants import load_variants

    try:
        return load_variants(Path(house_dir))
    except Exception:  # noqa: BLE001 — degrade to "no catalog", never break the payload
        return ()


def _catalog(model: ResolvedModel, provenance: Provenance | None) -> dict[str, Any]:
    """The authoring palette the UI's placement + assembly tools draw from (→ 21b).

    Everything the editor can *add* — window/door product types, the occupancy vocabulary,
    every library + project assembly with its resolved layer stack, and the material list —
    surfaced from the plan's :class:`~typehaus.model.plan.Library` so the client never has to
    hard-code a catalog. ``editable`` flags assemblies authored in the house's ``plan/``
    (provenance-tracked, so a layer edit can write back) versus shared ``library/`` presets
    the editor must duplicate before tweaking.
    """
    from typehaus.model.enums import Occupancy

    lib = model.plan.library
    assemblies: list[dict[str, Any]] = []
    for asm in lib.assemblies:
        resolved = lib.resolve_assembly(asm.tag)
        if resolved is None:
            continue
        prov = _provenance(provenance, asm.tag)
        assemblies.append({
            "tag": asm.tag,
            "editable": bool(prov and prov["editable"]),
            "provenance": prov,
            "stc": resolved.stc,
            "variant_of": asm.variant_of,
            "layers": [
                {"name": ly.name, "material": ly.material_ref,
                 "function": _enum_value(ly.function), "thickness_m": ly.thickness.meters}
                for ly in resolved.layers
            ],
        })
    return {
        "window_types": [
            {"tag": wt.tag, "width_m": wt.width.meters, "height_m": wt.height.meters,
             "operation": wt.operation, "product_ref": wt.product_ref}
            for wt in lib.window_types
        ],
        "door_types": [
            {"tag": dt.tag, "width_m": dt.width.meters, "height_m": dt.height.meters,
             "hardware": [dict(role=item.role, product_ref=item.product_ref,
                               quantity=item.quantity,
                               height_m=item.height.meters if item.height else None,
                               installation=item.installation) for item in dt.hardware],
             "jamb_framing": dt.jamb_framing.model_dump() if dt.jamb_framing else None,
             "field_finish": dt.field_finish,
             "operation": dt.operation, "exterior": dt.exterior, "glazed": dt.glazed,
             "frame_material_ref": dt.frame_material_ref, "leaf_material_ref": dt.leaf_material_ref,
             "catalog_dimensions": ({
                 "nominal_width_m": dt.catalog_dimensions.nominal_width.meters,
                 "nominal_height_m": dt.catalog_dimensions.nominal_height.meters,
                 "unit_width_m": dt.catalog_dimensions.unit_width.meters,
                 "unit_height_m": dt.catalog_dimensions.unit_height.meters,
                 "source_url": dt.catalog_dimensions.source_url,
                 "source_drawing": dt.catalog_dimensions.source_drawing,
                 "assembly_confirmed": dt.catalog_dimensions.assembly_confirmed,
             } if dt.catalog_dimensions else None),
             "trimless": dt.trimless, "leaf_set": dt.leaf_set, "product_ref": dt.product_ref,
             "bookcase_door": (None if dt.bookcase_door is None else {
                 "nominal_width_m": dt.bookcase_door.nominal_width.meters,
                 "nominal_height_m": dt.bookcase_door.nominal_height.meters,
                 "body_width_m": dt.bookcase_door.body_width.meters,
                 "body_height_m": dt.bookcase_door.body_height.meters,
                 "body_depth_m": dt.bookcase_door.body_depth.meters,
                 "casing_overall_width_m": dt.bookcase_door.casing_overall_width.meters,
                 "clear_passage_width_m": dt.bookcase_door.clear_passage_width.meters,
                 "hinge_side_clearance_m": dt.bookcase_door.hinge_side_clearance.meters,
                 "casing_lap_m": dt.bookcase_door.casing_lap.meters,
                 "clearance_envelope": {
                     "kind": "published_installation_clearance",
                     "hinge_side_m": dt.bookcase_door.hinge_side_clearance.meters,
                     "calculated_pivot_sweep": False,
                 },
                 "mounting_face": dt.bookcase_door.mounting_face,
                 "material_ref": dt.bookcase_door.material_ref,
                 "source": dt.bookcase_door.source,
             })}
            for dt in lib.door_types
        ],
        # The chosen-product catalog (model/product.py): identity only, and deliberately
        # no price — dollars reach the UI through the BOM, never through the palette. The
        # referring entries below carry ``product_ref``; this is what a ref resolves to.
        "products": [
            {"tag": pr.tag, "brand": pr.brand, "model": pr.model, "name": pr.name,
             "sku": pr.sku, "url": pr.url, "source": pr.source}
            for pr in lib.products
        ],
        "occupancies": [o.value for o in Occupancy],
        # ``color``/``finish`` are the authored *appearance* of a material. Without them the
        # viewer can only guess a material's look from substrings in its tag (nordic/palette
        # familyOf), which cannot distinguish white brick from red — so they ship with the
        # catalog and take precedence there. ``hatch`` deliberately stays out: it is the 2D
        # cut-pattern key and already disagrees with the 3D family (face brick hatches as
        # "concrete"), so feeding it to the viewer would mis-classify masonry.
        # Both vapour fields cross the boundary, and they are not interchangeable:
        # ``perm_rating`` is perm-*inch* (permeability, scales with depth) while
        # ``vapor_permeance_perms`` is the finished product's ASTM E96 permeance and takes
        # precedence. A consumer that saw only the first would divide a whole-sheet rating by a
        # thickness and invent a number nobody measured — so the resolution rule travels with
        # them (Material.vapor_permeance_at, mirrored in ui/src/model/vapor.ts). ``source`` rides
        # along because an unsourced permeance and a sourced one are not equally actionable.
        "materials": [
            {"tag": mat.tag, "name": mat.name, "r_per_inch": mat.r_per_inch,
             "perm_rating": mat.perm_rating,
             "vapor_permeance_perms": mat.vapor_permeance_perms,
             "density": mat.density, "source": mat.source,
             "color": mat.color, "finish": mat.finish, "coating": mat.coating,
             "species": mat.species, "wood_surface": mat.wood_surface,
             "panel_face_grade": mat.panel_face_grade, "panel_core": mat.panel_core,
             "panel_veneer_species": mat.panel_veneer_species,
             "panel_nominal_thickness_in": mat.panel_nominal_thickness_in,
             "finish_thickness_in": mat.finish_thickness_in,
             "product_ref": mat.product_ref}
            for mat in lib.materials
        ],
        "assemblies": assemblies,
    }


def catalog_json(
    model: ResolvedModel,
    provenance: Provenance | None,
    variants: Sequence[VariantSpec] | None,
) -> dict[str, Any]:
    """The payload's catalog tail: the declared variants plus the authoring palette."""
    return {
        # The declared variant catalog (variants.toml, → 21b §Variant compare): what named
        # alternatives this house can build, so the UI's variant picker never shells out.
        # Always present — an empty list *is* the absent-catalog story.
        "variants": [spec.as_dict() for spec in (variants or ())],
        "catalog": {**_catalog(model, provenance), **_placed_types(model)},
    }


def _placed_types(model: ResolvedModel) -> dict[str, Any]:
    """Every product type, with 3D parts only where something places it.

    A part's mesh moves to the shared ``meshes`` table and the part keeps its
    ``mesh_index``: the same bowl or rod recurs across types, and an unplaced type's massing
    was megabytes nothing drew. Plan strokes and metadata stay on every type.
    """
    placed = {item.type_ref for item in model.canvas_objects}
    meshes: list[dict[str, Any]] = []
    indices: dict[tuple, int] = {}
    types = canvas_object_types(model.plan)
    for item in types:
        if item["tag"] not in placed:
            item.pop("model_parts", None)
            continue
        for part in item.get("model_parts", ()):
            mesh = part.pop("mesh", None)
            if mesh is None:
                continue
            encoded = mesh_json(mesh["positions"], mesh["triangles"], mesh.get("normals"))
            key = (tuple(encoded["positions"]), tuple(encoded["triangles"]),
                   tuple(encoded.get("normals", ())))
            if key not in indices:
                indices[key] = len(meshes)
                meshes.append(encoded)
            part["mesh_index"] = indices[key]
    return {"canvas_object_types": types, "meshes": meshes}
