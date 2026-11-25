"""The one trim catalog a ``product`` key is looked up in: Metal Sales' parts, LP SmartSide
boards and the generic shop-brake profiles no single maker's kit supplies (``generic.py``)."""

from typehaus.library.trim import generic, lp_smartside, metal_sales

PROFILES = {**metal_sales.PROFILES, **lp_smartside.PROFILES, **generic.PROFILES}
SUPPLIES = metal_sales.SUPPLIES
