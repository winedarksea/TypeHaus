"""The one trim catalog a ``product`` key is looked up in: Metal Sales' parts and the
generic shop-brake profiles no single maker's kit supplies (``generic.py``)."""

from typehaus.library.trim import generic, metal_sales

PROFILES = {**metal_sales.PROFILES, **generic.PROFILES}
SUPPLIES = metal_sales.SUPPLIES
