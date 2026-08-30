"""The *specified* product behind an estimate line — a label, never a number.

``costs.toml`` has always had a free-text ``product`` field: the estimator types what was
actually bought into ``BomView`` and nothing in the model can check it, because until
``Product`` (model/product.py) the model had no idea what was *specified*. That is the
disconnected-document problem in its smallest form — two records of the same fact, one of
them unreadable.

This module closes exactly that half of it, and no more. It derives, per estimate
``(section, key)``, the brand + model the plan specifies, so the BOM row can show it and the
estimator only has to write down what *differed*. It is presentation: it never enters a
price, a quantity or any arithmetic, which is what keeps decision #28 intact — a ``Product``
carries no dollars, and this carries no dollars either.

Dollars stay where they were: ``prices.toml`` for the rate, ``costs.toml`` for what was
paid, both house-owned and both outside the undo journal (paying a bill is not a plan edit).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from typehaus.model.plan import PlanModel

#: Estimate sections whose price key is a tag a ``product_ref`` hangs off, mapped to the
#: ``Library`` catalogs that resolve it. Every name here must be a real section in
#: ``cli.prices.ESTIMATE_PLANS`` (``tests/test_products.py`` proves it) and every key field
#: must be the one that plan declares — this is a second reading of the *same* join, not a
#: parallel one.
#:
#: Sections absent from this map are absent on purpose. ``framing`` is keyed on a profile
#: string, ``concrete`` on a solid category, ``hardware`` on a part number that already
#: carries its manufacturer on the BOM row itself — none of them is a catalog tag, and
#: inventing a product for one would be guessing.
PRODUCT_REF_SOURCES: dict[str, tuple[str, ...]] = {
    "placeables": ("furniture_types", "fixture_types", "appliance_types", "equipment_types",
                   "register_types", "electrical_device_types"),
    # The same BOM table as ``placeables``, priced into the furnishings split.
    "furnishings": ("furniture_types", "fixture_types", "appliance_types", "equipment_types",
                    "register_types", "electrical_device_types"),
    "openings": ("door_types", "window_types"),
    "railings": ("railing_types",),
    "envelope_layers": ("materials",),
    "sheet_goods": ("materials",),
    "wood_surfaces": ("materials",),
    "floor_finishes": ("materials",),
}


def product_label(product: Any) -> str:
    """"LG WKHC252HBA" — brand and the manufacturer's designation, in that order.

    Falls back to the brand alone (a choice made only as far as the maker) and then to the
    marketing name, so the label is never a lone brand where a name would say more.
    """
    parts = [product.brand, product.model]
    label = " ".join(part for part in parts if part)
    return label or product.name or product.tag


def product_labels(plan: PlanModel) -> dict[tuple[str, str], str]:
    """``{(estimate section, price key): "Brand Model"}`` for everything the plan specifies.

    Keyed by ``(section, key)`` — the identical pair ``costs.toml`` files an entry under and
    ``estimate_csv`` sorts on — rather than by bare tag: a material tag and a type tag live
    in different namespaces and nothing forbids them colliding.
    """
    library = plan.library
    labels: dict[tuple[str, str], str] = {}
    for section, catalogs in PRODUCT_REF_SOURCES.items():
        for catalog in catalogs:
            for entry in getattr(library, catalog, ()) or ():
                product = library.product(getattr(entry, "product_ref", None) or "")
                if product is None:
                    continue
                labels[(section, entry.tag)] = product_label(product)
    return labels


def hardware_product(row: Mapping[str, Any]) -> str | None:
    """The specified product for a ``hardware`` row, read off the row rather than a catalog.

    ``StructuralHardware`` is where product identity in this engine started, and a hardware
    BOM line already carries ``manufacturer`` + ``part_number`` (takeoff/hardware_catalog.py
    ``hardware_row``). So the join is already done — there is nothing to look up, and a
    ``Product`` record for the connector catalog would only be a second copy of it. Folding
    hardware into ``Product`` is a later move; its length-keyed ``part_number_by_length_in``
    does not fit that shape yet.
    """
    manufacturer = row.get("manufacturer")
    part_number = row.get("part_number")
    parts = [str(p) for p in (manufacturer, part_number) if p]
    return " ".join(parts) or None


def specified_product(section: str, key: str, row: Mapping[str, Any],
                      products: Mapping[tuple[str, str], str] | None) -> str | None:
    """The specified brand + model for one priced estimate row, or None for no product.

    Hardware reads off the BOM row (see :func:`hardware_product`); everything else comes out
    of the caller's ``(section, key)`` map. A QUALIFIED key (``"slab:BALCONY_DECK_ALUMINUM"``
    — a house pricing one assembly at its own rate) falls back to its bare tag, so naming a
    rate does not cost the line its product identity.
    """
    if section == "hardware":
        return hardware_product(row)
    if not products:
        return None
    return products.get((section, key)) or products.get((section, key.split(":", 1)[0]))
