"""A retailer order list: every bought item of one brand, in packs, with who uses it.

A view of the ``placeables`` BOM rows, never an addition to the estimate: a frame row
joins its type's ``product_ref``, a part row (``FurnitureType``/``FixtureType.parts``)
is already keyed by product. A ``LightRun`` whose type names a product is bought by the
piece (``_add_light_runs``). Units become packs by ``Product.pack_quantity``. What would
leave the list silently short — a SEKTION-family type with no product, a product with no
article number — is reported as ``unresolved`` rather than dropped. A sheet product's
pieces nest onto whole sheets (``takeoff/sheet_nesting.py``): its packs are sheets, and
``cuts`` says which piece comes off which.
"""

from __future__ import annotations

import math
from typing import Any

from typehaus.model.electrical import luminaire_types
from typehaus.resolve.model import ResolvedModel
from typehaus.takeoff.placeables import _placeable_types, placeables_takeoff
from typehaus.takeoff.sheet_nesting import cut_list, nest, sheet_pieces

ORDER_COLUMNS = ("brand", "article", "name", "roles", "units", "pack_quantity", "packs",
                 "length_ft", "unit_price", "used_by", "cuts", "note")
_FAMILY_WORDS = ("sektion", "förbättra")


def _sektion_family(entry: object) -> bool:
    """A SEKTION-line type: by glyph, or by name. A cover-panel glyph alone is not enough —
    a site-cut scribe draws as one and is shop stock."""
    symbol = str(getattr(entry, "plan_symbol", "") or "")
    name = str(getattr(entry, "name", "") or "").lower()
    return ((symbol.startswith("sektion") and symbol != "sektion-cover-panel")
            or any(word in name for word in _FAMILY_WORDS))


def order_list(model: ResolvedModel,
               brand: str | None = None) -> dict[str, list[dict[str, Any]]]:
    """``{"items": [...], "unresolved": [...]}`` for ``brand`` (case-insensitive).

    Without a brand, every brand that supplies at least one part row is listed. Each item's
    ``price_keys`` are the ``[placeables]`` keys a caller may price it by, product first.
    """
    library = model.plan.library
    types = _placeable_types(model)
    rows = placeables_takeoff(model)
    part_brands = {str(row.get("brand") or "").lower() for row in rows if "roles" in row}
    wanted = {brand.lower()} if brand else part_brands
    items: dict[str, dict[str, Any]] = {}
    unresolved: list[dict[str, Any]] = []
    for row in rows:
        if "roles" in row:
            product_tag, roles = str(row["type"]), list(row["roles"])
            price_keys = [product_tag]
        else:
            entry = types.get(str(row["type"]))
            product_tag = getattr(entry, "product_ref", None)
            if product_tag is None:
                if (_sektion_family(entry) and not getattr(entry, "parts", ())
                        and (brand is None or brand.lower() == "ikea")):
                    unresolved.append({"item": row["type"], "reason": "no product_ref",
                                       "used_by": ", ".join(row["tags"])})
                continue
            symbol = str(getattr(entry, "plan_symbol", "") or "")
            roles = ["cover_panel" if symbol == "sektion-cover-panel" else "frame"]
            price_keys = [str(row["type"])]
        product = library.product(product_tag)
        if product is None or product.brand.lower() not in wanted:
            continue
        item = _item(items, product_tag, product)
        item["units"] += int(row["count"])
        item["roles"] += [role for role in roles if role not in item["roles"]]
        item["price_keys"] += [key for key in price_keys if key not in item["price_keys"]]
        item["used_by"].update(row["tags"])
        if row.get("length_ft") is not None:
            item["length_ft"] = round((item["length_ft"] or 0) + float(row["length_ft"]), 2)
    _add_light_runs(model, items, wanted)
    pieces = sheet_pieces(model)
    listed = []
    for tag in sorted(items, key=lambda t: (items[t]["brand"], items[t]["roles"][0],
                                            str(items[t]["name"]))):
        item = items[tag]
        if not item["article"]:
            unresolved.append({"item": tag, "reason": "no article number (sku)",
                               "used_by": ", ".join(sorted(item["used_by"]))})
        packs, cuts = math.ceil(item["units"] / item["pack_quantity"]), ""
        product = library.product(tag)
        if tag in pieces:
            sheets, oversize = nest(pieces[tag], product.stock_width.meters,
                                    product.stock_length.meters)
            packs = math.ceil((len(sheets) + len(oversize)) / item["pack_quantity"])
            cuts = cut_list(sheets)
            unresolved += [{"item": tag, "reason": f"{piece.label()} is larger than the sheet",
                            "used_by": piece.tag} for piece in oversize]
        listed.append({**item, "roles": ", ".join(item["roles"]), "packs": packs,
                       "unit_price": "", "used_by": ", ".join(sorted(item["used_by"])),
                       "cuts": cuts})
    return {"items": listed, "unresolved": unresolved}


def _item(items: dict[str, dict[str, Any]], tag: str, product) -> dict[str, Any]:
    if tag not in items:
        items[tag] = {
            "brand": product.brand, "article": product.sku, "product": tag,
            "name": product.name or product.model, "url": product.url, "roles": [],
            "units": 0, "pack_quantity": product.pack_quantity, "length_ft": None,
            "price_keys": [tag], "used_by": set(), "note": ""}
    return items[tag]


def _add_light_runs(model: ResolvedModel, items: dict[str, dict[str, Any]],
                    wanted: set[str]) -> None:
    """Finished strips by the piece: whole ``stock_length`` pieces per run, or, where the
    product states none, one piece per run — and the line says that is assumed."""
    library = model.plan.library
    types = luminaire_types(library)
    for run in model.light_runs:
        tag = getattr(types.get(run.type_ref), "product_ref", None)
        product = library.product(tag) if tag else None
        if product is None or product.brand.lower() not in wanted:
            continue
        item = _item(items, tag, product)
        stock = product.stock_length
        item["units"] += math.ceil(run.length_m / stock.meters - 1e-9) if stock else 1
        if stock is None:
            item["note"] = "1 piece per run assumed: product states no stock_length"
        if "light_run" not in item["roles"]:
            item["roles"].append("light_run")
        item["used_by"].add(run.tag)
        item["length_ft"] = round((item["length_ft"] or 0) + run.length_m / 0.3048, 2)
