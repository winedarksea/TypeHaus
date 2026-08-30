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
             "operation": dt.operation, "exterior": dt.exterior, "glazed": dt.glazed,
             "trimless": dt.trimless, "product_ref": dt.product_ref}
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
        "catalog": {**_catalog(model, provenance),
                    "canvas_object_types": canvas_object_types(model.plan)},
    }
