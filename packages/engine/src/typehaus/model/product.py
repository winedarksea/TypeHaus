"""Product — the manufactured thing a material or a type *is*, by name and number (#28).

Identity only. A ``Product`` says which box arrives on site: brand, the manufacturer's own
designation, the marketing name, a distributor number where that is what you order by. It
carries **no price, vendor rate, or availability data, ever** — dollars belong to the house
(``prices.toml`` / ``costs.toml``), never to the engine (``plans/01-decisions.md`` #28).
``library/hardware.py`` has been following that split unstated since the connector catalog
landed; this is the same record generalized to everything else a house chooses.

Why a shared catalog record rather than three fields on eight classes: one place for the
costs join to read, and one product can serve several materials or types (the same coil
stock clads a wall and a roof; the same fixture family hangs in four rooms).
"""

from __future__ import annotations

from typehaus.model.base import HausModel
from typehaus.model.registry import register_constructor


class Product(HausModel):
    """A chosen product, referenced by tag from a ``Material`` or a ``*Type``."""

    tag: str
    # The manufacturer or the brand it is sold under — "LG", "Frigidaire", "Rheem".
    brand: str
    # The manufacturer's own designation — "WKHC252HBA". Empty where a brand has been
    # chosen and a model has not, which is a real and honest state.
    model: str = ""
    # The marketing name, if it differs usefully from the model number. Deliberately not
    # the referring object's ``name``: a type's name is what the schedules print, and this
    # record must be able to change without churning every schedule that names it.
    name: str = ""
    # A distributor/retailer number, where *that* is what an order is placed against
    # rather than the manufacturer's model (an accessory kit, a coil stock colour).
    sku: str = ""
    url: str | None = None
    # Where the choice and its numbers were read (#46) — the same freeform provenance
    # every other catalog record carries.
    source: str | None = None


register_constructor("Product", Product)
